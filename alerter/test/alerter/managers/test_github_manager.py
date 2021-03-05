import json
import logging
import multiprocessing
import time
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerter_starters import start_github_alerter
from src.alerter.managers.github import (GithubAlerterManager)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (HEALTH_CHECK_EXCHANGE,
                                 GITHUB_MANAGER_INPUT_QUEUE,
                                 GITHUB_MANAGER_INPUT_ROUTING_KEY,
                                 GITHUB_ALERTER_NAME)
from src.utils.exceptions import PANICException
from test.utils.test_utils import infinite_fn


# Tests adapted from Monitors managers
class TestGithubAlertersManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.manager_name = 'test_github_alerters_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': self.manager_name,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.github_alerter_name = GITHUB_ALERTER_NAME
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = Process(target=infinite_fn, args=())
        self.dummy_process3.daemon = True

        self.test_rabbit_manager = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.test_manager = GithubAlerterManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)
        self.test_exception = PANICException('test_exception', 1)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_rabbit_manager.connect()
            self.test_manager.rabbitmq.connect()
            # Declare queues incase they haven't been declared already
            self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_declare(
                queue=GITHUB_MANAGER_INPUT_QUEUE, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_purge(self.test_queue_name)
            self.test_manager.rabbitmq.queue_purge(GITHUB_MANAGER_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(GITHUB_MANAGER_INPUT_QUEUE)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
            self.rabbitmq.disconnect()
            self.test_rabbit_manager.disconnect()
        except Exception as e:
            print("Test failed: {}".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.test_manager = None
        self.test_exception = None
        self.test_rabbit_manager = None

        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.__str__())

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        self.assertEqual(1, mock_start_consuming.call_count)

    @mock.patch.object(GithubAlerterManager, "_process_ping")
    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self, mock_process_ping) -> None:
        mock_process_ping.return_value = None
        try:
            self.test_rabbit_manager.connect()
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges and queues have not already been
            # declared
            self.test_manager.rabbitmq.connect()
            self.test_manager.rabbitmq.queue_delete(GITHUB_MANAGER_INPUT_QUEUE)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)

            self.test_manager._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_manager.rabbitmq.is_connected)
            self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_manager.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchanges and queues have been creating by
            # sending messages with the same routing keys as for the queues. We
            # will also check if the size of the queues is 0 to confirm that
            # basic_consume was called (it will store the msg in the component
            # memory immediately). If one of the exchanges or queues is not
            # created, then either an exception will be thrown or the queue size
            # would be 1. Note when deleting the exchanges in the beginning we
            # also released every binding, hence there are no other queue binded
            # with the same routing key to any exchange at this point.
            self.test_rabbit_manager.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=GITHUB_MANAGER_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_rabbit_manager.queue_declare(
                GITHUB_MANAGER_INPUT_QUEUE, False, True, False, False)
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_manager._initialise_rabbitmq()
            self.test_rabbit_manager.connect()

            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._send_heartbeat(self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_rabbit_manager.basic_get(
                self.test_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_alerter_process_creates_the_correct_process(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._start_alerters_processes()

        new_entry_process = self.test_manager.alerter_process_dict[
            GITHUB_ALERTER_NAME]

        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(0, len(new_entry_process._args))
        self.assertEqual(start_github_alerter, new_entry_process._target)

    @mock.patch("src.alerter.alerter_starters.create_logger")
    def test_start_alerters_process_starts_the_process(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger
        self.test_manager._start_alerters_processes()

        # We need to sleep to give some time for the alerter to be initialised,
        # otherwise the process would not terminate
        time.sleep(1)

        new_entry_process = self.test_manager.alerter_process_dict[
            GITHUB_ALERTER_NAME]
        self.assertTrue(new_entry_process.is_alive())

        new_entry_process.terminate()
        new_entry_process.join()

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerter_starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_process_is_alive(
            self, mock_ack, mock_create_logger) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_manager._initialise_rabbitmq()
            self.test_manager._start_alerters_processes()

            # Give time for the processes to start
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            properties = pika.spec.BasicProperties()
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)
            expected_output = {
                "component_name": self.manager_name,
                "dead_processes": [],
                "running_processes": [GITHUB_ALERTER_NAME],
                "timestamp": datetime(2012, 1, 1).timestamp()
            }
            # Check that the message received is a valid HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_manager.alerter_process_dict[
                GITHUB_ALERTER_NAME].terminate()
            self.test_manager.alerter_process_dict[GITHUB_ALERTER_NAME].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerter_starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_process_is_dead(
            self, mock_ack, mock_create_logger) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_manager._initialise_rabbitmq()
            self.test_manager._start_alerters_processes()

            # Give time for the processes to start
            time.sleep(1)

            self.test_manager.alerter_process_dict[
                GITHUB_ALERTER_NAME].terminate()
            self.test_manager.alerter_process_dict[GITHUB_ALERTER_NAME].join()

            # Time for processes to terminate
            time.sleep(1)

            self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            properties = pika.spec.BasicProperties()
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)
            expected_output = {
                "component_name": self.manager_name,
                "dead_processes": [GITHUB_ALERTER_NAME],
                "running_processes": [],
                "timestamp": datetime(2012, 1, 1).timestamp()
            }
            # Check that the message received is a valid HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_manager.alerter_process_dict[
                GITHUB_ALERTER_NAME].terminate()
            self.test_manager.alerter_process_dict[GITHUB_ALERTER_NAME].join()
            self.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch("src.alerter.alerter_starters.create_logger")
    @mock.patch.object(GithubAlerterManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes(
            self, send_hb_mock, mock_create_logger, mock_ack) -> None:
        send_hb_mock.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_manager._initialise_rabbitmq()
            self.test_manager._start_alerters_processes()

            # Give time for the processes to start
            time.sleep(1)

            # Automate the case when having all processes dead
            self.test_manager.alerter_process_dict[
                GITHUB_ALERTER_NAME].terminate()
            self.test_manager.alerter_process_dict[GITHUB_ALERTER_NAME].join()

            # Give time for the processes to terminate
            time.sleep(1)

            # Check that that the processes have terminated
            self.assertFalse(self.test_manager.alerter_process_dict[
                                 GITHUB_ALERTER_NAME].is_alive())

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            properties = pika.spec.BasicProperties()
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # Give time for the processes to start
            time.sleep(1)

            self.assertTrue(self.test_manager.alerter_process_dict[
                                GITHUB_ALERTER_NAME].is_alive())

            # Clean before test finishes
            self.test_manager.alerter_process_dict[
                GITHUB_ALERTER_NAME].terminate()
            self.test_manager.alerter_process_dict[GITHUB_ALERTER_NAME].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(multiprocessing.Process, "is_alive")
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, is_alive_mock) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat. In this test we will
        # check that no heartbeat is sent when mocking a raised exception.
        is_alive_mock.side_effect = self.test_exception
        try:
            self.test_manager._initialise_rabbitmq()
            self.test_manager._start_alerters_processes()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        try:
            self.test_manager._initialise_rabbitmq()
            self.test_manager._start_alerters_processes()

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("pika.exceptions.AMQPChannelError('test')",
         "pika.exceptions.AMQPChannelError"),
        ("self.test_exception", "PANICException"),
    ])
    @mock.patch.object(GithubAlerterManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_exceptions(
            self, param_input, param_expected, hb_mock) -> None:
        hb_mock.side_effect = eval(param_input)
        try:
            self.test_manager._initialise_rabbitmq()

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(eval(param_expected),
                              self.test_manager._process_ping,
                              blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
