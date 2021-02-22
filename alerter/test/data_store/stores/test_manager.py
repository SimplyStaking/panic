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

from src.data_store.stores.manager import StoreManager
from src.data_store.starters import (start_system_store, start_github_store,
                                     start_alert_store)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (HEALTH_CHECK_EXCHANGE, SYSTEM_STORE_NAME,
                                 GITHUB_STORE_NAME, ALERT_STORE_NAME,
                                 DATA_STORE_MAN_INPUT_QUEUE,
                                 DATA_STORE_MAN_INPUT_ROUTING_KEY)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  PANICException)
from src.utils.logging import log_and_print
from src.utils import env

from test.test_utils import (infinite_fn, connect_to_rabbit,
                             disconnect_from_rabbit,
                             delete_exchange_if_exists,
                             delete_queue_if_exists)


class TestStoreManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.test_rabbit_manager = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.manager_name = 'test_store_manager'
        self.routing_key = 'heartbeat.manager'
        self.test_queue_name = 'test queue'
        self.test_store_manager = StoreManager(self.dummy_logger,
                                               self.manager_name,
                                               self.rabbitmq)

        connect_to_rabbit(self.rabbitmq)
        connect_to_rabbit(self.test_rabbit_manager)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.rabbitmq.queue_declare(DATA_STORE_MAN_INPUT_QUEUE, False, True,
                                    False, False)
        self.test_rabbit_manager.queue_declare(self.test_queue_name, False,
                                               True, False, False)
        self.rabbitmq.queue_bind(DATA_STORE_MAN_INPUT_QUEUE,
                                 HEALTH_CHECK_EXCHANGE,
                                 DATA_STORE_MAN_INPUT_ROUTING_KEY)

        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': self.manager_name,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.test_exception = PANICException('test_exception', 1)

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, DATA_STORE_MAN_INPUT_QUEUE)
        delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        connect_to_rabbit(self.test_rabbit_manager)
        delete_queue_if_exists(self.test_rabbit_manager, self.test_queue_name)
        disconnect_from_rabbit(self.test_rabbit_manager)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_rabbit_manager = None

    def test__str__returns_name_correctly(self):
        self.assertEqual(self.manager_name, str(self.test_store_manager))

    def test_name_property_returns_name_correctly(self):
        self.assertEqual(self.manager_name, self.test_store_manager.name)

    def test_logger_property_returns_logger_correctly(self):
        self.assertEqual(self.dummy_logger, self.test_store_manager.logger)

    def test_rabbitmq_property_returns_rabbitmq_correctly(self):
        self.assertEqual(self.rabbitmq, self.test_store_manager.rabbitmq)

    def test_initialise_rabbitmq_initialises_everything_as_expected(self):
        try:
            # To make sure that the exchanges have not already been declared
            self.rabbitmq.connect()
            self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_store_manager._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_store_manager.rabbitmq.is_connected)
            self.assertTrue(self.test_store_manager.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_store_manager.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchange has been creating by sending messages
            # to it. If this fails an exception is raised, hence the test fails.
            self.test_store_manager.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE, routing_key=self.routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_store_manager._initialise_rabbitmq()
            self.test_rabbit_manager.connect()

            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_store_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=self.routing_key)
            self.test_store_manager._send_heartbeat(self.test_heartbeat)

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
    def test_start_stores_processes_starts_system_store_correctly(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_store_manager._start_stores_processes()

        time.sleep(1)

        new_entry_process = self.test_store_manager._store_process_dict[
            SYSTEM_STORE_NAME]

        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(0, len(new_entry_process._args))
        self.assertEqual(start_system_store, new_entry_process._target)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_stores_processes_starts_github_store_correctly(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_store_manager._start_stores_processes()

        time.sleep(1)

        new_entry_process = self.test_store_manager._store_process_dict[
            GITHUB_STORE_NAME]

        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(0, len(new_entry_process._args))
        self.assertEqual(start_github_store, new_entry_process._target)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_stores_processes_starts_alert_store_correctly(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_store_manager._start_stores_processes()

        time.sleep(1)

        new_entry_process = self.test_store_manager._store_process_dict[
            ALERT_STORE_NAME]

        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(0, len(new_entry_process._args))
        self.assertEqual(start_alert_store, new_entry_process._target)

    @mock.patch("src.data_store.starters.create_logger")
    def test_start_stores_processes_starts_the_processes_correctly(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger
        self.test_store_manager._start_stores_processes()

        # We need to sleep to give some time for the stores to be initialised,
        # otherwise the process would not terminate
        time.sleep(1)

        new_system_process = self.test_store_manager._store_process_dict[
            SYSTEM_STORE_NAME]
        self.assertTrue(new_system_process.is_alive())
        new_system_process.terminate()
        new_system_process.join()

        new_github_process = self.test_store_manager._store_process_dict[
            GITHUB_STORE_NAME]
        self.assertTrue(new_github_process.is_alive())
        new_github_process.terminate()
        new_github_process.join()

        new_alert_process = self.test_store_manager._store_process_dict[
            ALERT_STORE_NAME]
        self.assertTrue(new_alert_process.is_alive())
        new_alert_process.terminate()
        new_alert_process.join()

    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_process_is_alive(
            self, mock_ack, mock_create_logger) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_store_manager._initialise_rabbitmq()
            self.test_store_manager._start_stores_processes()

            # Give time for the processes to start
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_rabbit_manager.queue_delete(self.test_queue_name)

            # initialise
            blocking_channel = self.test_store_manager.rabbitmq.channel
            properties = pika.spec.BasicProperties()
            method_hb = pika.spec.Basic.Deliver(routing_key=self.routing_key)
            body = 'ping'
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_rabbit_manager.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=self.routing_key)
            self.test_store_manager._process_ping(blocking_channel, method_hb,
                                                  properties, body)

            time.sleep(1)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)
            expected_output = {
                "component_name": self.manager_name,
                "dead_processes": [],
                "running_processes": [SYSTEM_STORE_NAME, GITHUB_STORE_NAME,
                                      ALERT_STORE_NAME],
                "timestamp": datetime(2012, 1, 1).timestamp()
            }
            # Check that the message received is a valid HB
            _, _, body = self.test_rabbit_manager.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_all_processes_are_dead(
            self, mock_ack, mock_create_logger) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_store_manager._initialise_rabbitmq()
            self.test_store_manager._start_stores_processes()

            # Give time for the processes to start
            time.sleep(1)

            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].join()

            # Time for processes to terminate
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_rabbit_manager.queue_delete(self.test_queue_name)

            # initialise
            blocking_channel = self.test_store_manager.rabbitmq.channel
            properties = pika.spec.BasicProperties()
            method_hb = pika.spec.Basic.Deliver(routing_key=self.routing_key)
            body = 'ping'
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_rabbit_manager.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=self.routing_key)
            self.test_store_manager._process_ping(blocking_channel, method_hb,
                                                  properties, body)

            time.sleep(1)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)
            expected_output = {
                "component_name": self.manager_name,
                "dead_processes": [SYSTEM_STORE_NAME, GITHUB_STORE_NAME,
                                   ALERT_STORE_NAME],
                "running_processes": [],
                "timestamp": datetime(2012, 1, 1).timestamp()
            }
            # Check that the message received is a valid HB
            _, _, body = self.test_rabbit_manager.basic_get(
                self.test_queue_name)
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].join()
            self.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch("src.data_store.starters.create_logger")
    @mock.patch.object(StoreManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes(
            self, send_hb_mock, mock_create_logger, mock_ack) -> None:
        send_hb_mock.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_store_manager._initialise_rabbitmq()
            self.test_store_manager._start_stores_processes()

            # Give time for the processes to start
            time.sleep(1)

            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].join()

            # Give time for the processes to terminate
            time.sleep(1)

            # Check that that the processes have terminated
            self.assertFalse(self.test_store_manager._store_process_dict[
                                SYSTEM_STORE_NAME].is_alive())
            self.assertFalse(self.test_store_manager._store_process_dict[
                                GITHUB_STORE_NAME].is_alive())
            self.assertFalse(self.test_store_manager._store_process_dict[
                                ALERT_STORE_NAME].is_alive())

            # initialise
            blocking_channel = self.test_store_manager.rabbitmq.channel
            properties = pika.spec.BasicProperties()
            method_hb = pika.spec.Basic.Deliver(routing_key=self.routing_key)
            body = 'ping'
            self.test_store_manager._process_ping(blocking_channel, method_hb,
                                                  properties, body)

            # Give time for the processes to start
            time.sleep(1)

            self.assertTrue(self.test_store_manager._store_process_dict[
                                SYSTEM_STORE_NAME].is_alive())
            self.assertTrue(self.test_store_manager._store_process_dict[
                                GITHUB_STORE_NAME].is_alive())
            self.assertTrue(self.test_store_manager._store_process_dict[
                                ALERT_STORE_NAME].is_alive())

            # Clean before test finishes
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].terminate()
            self.test_store_manager._store_process_dict[
                SYSTEM_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                GITHUB_STORE_NAME].join()
            self.test_store_manager._store_process_dict[
                ALERT_STORE_NAME].join()
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
            self.test_store_manager._initialise_rabbitmq()
            self.test_store_manager._start_stores_processes()

            time.sleep(1)
            # Delete the queue before to avoid messages in the queue on error.
            self.test_rabbit_manager.queue_delete(self.test_queue_name)

            # initialise
            blocking_channel = self.test_store_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=self.routing_key)
            properties = pika.spec.BasicProperties()
            body = 'ping'
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_rabbit_manager.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=self.routing_key)
            self.test_store_manager._process_ping(blocking_channel, method,
                                                  properties, body)

            time.sleep(1)
            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        try:
            self.test_store_manager._initialise_rabbitmq()
            self.test_store_manager._start_stores_processes()

            time.sleep(1)

            # initialise
            blocking_channel = self.test_store_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.test_store_manager._process_ping(blocking_channel, method,
                                                  properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("pika.exceptions.AMQPChannelError('test')",
         "pika.exceptions.AMQPChannelError"),
        ("self.test_exception", "PANICException"),
    ])
    @mock.patch.object(StoreManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_exceptions(
            self, param_input, param_expected, hb_mock) -> None:
        hb_mock.side_effect = eval(param_input)
        try:
            self.test_store_manager._initialise_rabbitmq()

            # initialise
            blocking_channel = self.test_store_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=self.routing_key)
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(eval(param_expected),
                              self.test_store_manager._process_ping,
                              blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
