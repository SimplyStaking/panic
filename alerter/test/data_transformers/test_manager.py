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

from src.data_transformers.manager import (DataTransformersManager,
                                           DT_MAN_INPUT_QUEUE,
                                           DT_MAN_INPUT_ROUTING_KEY)
from src.data_transformers.starters import (start_system_data_transformer,
                                            start_github_data_transformer)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (SYSTEM_DATA_TRANSFORMER_NAME,
                                 GITHUB_DATA_TRANSFORMER_NAME,
                                 HEALTH_CHECK_EXCHANGE)
from src.utils.exceptions import PANICException
from test.test_utils import infinite_fn


class TestDataTransformersManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_data_transformers_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = Process(target=infinite_fn, args=())
        self.dummy_process3.daemon = True
        self.transformer_process_dict_example = {
            SYSTEM_DATA_TRANSFORMER_NAME: self.dummy_process1,
            GITHUB_DATA_TRANSFORMER_NAME: self.dummy_process2,
        }
        self.test_manager = DataTransformersManager(self.dummy_logger,
                                                    self.manager_name,
                                                    self.rabbitmq)
        self.test_exception = PANICException('test_exception', 1)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_manager.rabbitmq.connect()

            # Declare them before just in case there are tests which do not
            # use these queues and exchanges
            self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_declare(
                DT_MAN_INPUT_QUEUE, False, True, False, False)
            self.test_manager.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, 'topic', False, True, False, False)

            self.test_manager.rabbitmq.queue_purge(self.test_queue_name)
            self.test_manager.rabbitmq.queue_purge(DT_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(DT_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            print("Deletion of queues and exchanges failed: {}".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None
        self.test_manager = None
        self.test_exception = None
        self.transformer_process_dict_example = None

    def test_str_returns_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.__str__())

    def test_name_returns_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_transformer_process_dict_returns_transformer_process_dict(
            self) -> None:
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example
        self.assertEqual(self.transformer_process_dict_example,
                         self.test_manager.transformer_process_dict)

    def test_initialise_rabbitmq_initializes_everything_as_expected(
            self) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchange and queue have not already been
            # declared
            self.rabbitmq.connect()
            self.test_manager.rabbitmq.queue_delete(DT_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_manager._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_manager.rabbitmq.is_connected)
            self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_manager.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchange and queue have been creating by
            # sending messages with the same routing keys as for the queue. We
            # will also check if the size of the queue is 0 to confirm that
            # basic_consume was called (it will store the msg in the component
            # memory immediately). If one of the exchange or queue is not
            # created, then either an exception will be thrown or the queue size
            # would be 1. Note when deleting the exchange in the beginning we
            # also released every binding, hence there is no other queue binded
            # with the same routing key to any exchange at this point.
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=DT_MAN_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_manager.rabbitmq.queue_declare(
                DT_MAN_INPUT_QUEUE, False, True, False, False)
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        self.assertEqual(1, mock_start_consuming.call_count)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_manager._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_manager.rabbitmq.queue_declare(
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
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_transformers_processes_creates_correct_sys_proc_first_time(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._start_transformers_processes()

        system_data_trans_proc = self.test_manager.transformer_process_dict[
            SYSTEM_DATA_TRANSFORMER_NAME]
        self.assertTrue(system_data_trans_proc.daemon)
        self.assertEqual(0, len(system_data_trans_proc._args))
        self.assertEqual(start_system_data_transformer,
                         system_data_trans_proc._target)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_transformers_processes_creates_correct_sys_proc_if_not_alive(
            self, mock_start) -> None:
        mock_start.return_value = None

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example

        self.test_manager._start_transformers_processes()

        system_data_trans_proc = self.test_manager.transformer_process_dict[
            SYSTEM_DATA_TRANSFORMER_NAME]
        self.assertTrue(system_data_trans_proc.daemon)
        self.assertEqual(0, len(system_data_trans_proc._args))
        self.assertEqual(start_system_data_transformer,
                         system_data_trans_proc._target)

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, "Process")
    def test_start_transformers_processes_stores_sys_proc_correct_first_time(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process3

        self.test_manager._start_transformers_processes()

        expected_trans_proc_dict_without_gh = {
            SYSTEM_DATA_TRANSFORMER_NAME: self.dummy_process3,
        }
        actual_trans_proc_dict_without_gh = \
            self.test_manager._transformer_process_dict
        del actual_trans_proc_dict_without_gh[GITHUB_DATA_TRANSFORMER_NAME]

        self.assertEqual(expected_trans_proc_dict_without_gh,
                         actual_trans_proc_dict_without_gh)

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, "Process")
    def test_start_transformers_processes_stores_sys_proc_correct_if_not_alive(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process3

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example

        self.test_manager._start_transformers_processes()

        expected_trans_proc_dict_without_gh = {
            SYSTEM_DATA_TRANSFORMER_NAME: self.dummy_process3,
        }
        actual_trans_proc_dict_without_gh = \
            self.test_manager._transformer_process_dict
        del actual_trans_proc_dict_without_gh[GITHUB_DATA_TRANSFORMER_NAME]

        self.assertEqual(expected_trans_proc_dict_without_gh,
                         actual_trans_proc_dict_without_gh)

    @mock.patch("src.data_transformers.starters.create_logger")
    def test_start_transformers_processes_starts_system_process_if_first_time(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger
        self.test_manager._start_transformers_processes()

        # We need to sleep to give some time for the data transformer to be
        # initialized, otherwise the process would not terminate
        time.sleep(1)

        system_data_trans_process = self.test_manager.transformer_process_dict[
            SYSTEM_DATA_TRANSFORMER_NAME]
        github_data_trans_process = self.test_manager.transformer_process_dict[
            GITHUB_DATA_TRANSFORMER_NAME]
        self.assertTrue(system_data_trans_process.is_alive())

        system_data_trans_process.terminate()
        system_data_trans_process.join()
        github_data_trans_process.terminate()
        github_data_trans_process.join()

    @mock.patch("src.data_transformers.starters.create_logger")
    def test_start_transformers_processes_starts_system_process_if_not_alive(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example

        self.test_manager._start_transformers_processes()

        # We need to sleep to give some time for the data transformer to be
        # initialized, otherwise the process would not terminate
        time.sleep(1)

        system_data_trans_process = self.test_manager.transformer_process_dict[
            SYSTEM_DATA_TRANSFORMER_NAME]
        github_data_trans_process = self.test_manager.transformer_process_dict[
            GITHUB_DATA_TRANSFORMER_NAME]
        self.assertTrue(system_data_trans_process.is_alive())

        system_data_trans_process.terminate()
        system_data_trans_process.join()
        github_data_trans_process.terminate()
        github_data_trans_process.join()

    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_transformers_processes_creates_correct_git_proc_first_time(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._start_transformers_processes()

        github_data_trans_proc = self.test_manager.transformer_process_dict[
            GITHUB_DATA_TRANSFORMER_NAME]
        self.assertTrue(github_data_trans_proc.daemon)
        self.assertEqual(0, len(github_data_trans_proc._args))
        self.assertEqual(start_github_data_transformer,
                         github_data_trans_proc._target)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_transformers_processes_creates_correct_git_proc_if_not_alive(
            self, mock_start) -> None:
        mock_start.return_value = None

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example

        self.test_manager._start_transformers_processes()

        github_data_trans_proc = self.test_manager.transformer_process_dict[
            GITHUB_DATA_TRANSFORMER_NAME]
        self.assertTrue(github_data_trans_proc.daemon)
        self.assertEqual(0, len(github_data_trans_proc._args))
        self.assertEqual(start_github_data_transformer,
                         github_data_trans_proc._target)

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, "Process")
    def test_start_transformers_processes_stores_github_proc_correct_first_time(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process3

        self.test_manager._start_transformers_processes()

        expected_trans_proc_dict_without_sys = {
            GITHUB_DATA_TRANSFORMER_NAME: self.dummy_process3,
        }
        actual_trans_proc_dict_without_sys = \
            self.test_manager._transformer_process_dict
        del actual_trans_proc_dict_without_sys[SYSTEM_DATA_TRANSFORMER_NAME]

        self.assertEqual(expected_trans_proc_dict_without_sys,
                         actual_trans_proc_dict_without_sys)

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, "Process")
    def test_start_transformers_processes_stores_git_proc_correct_if_not_alive(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process3

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example

        self.test_manager._start_transformers_processes()

        expected_trans_proc_dict_without_sys = {
            GITHUB_DATA_TRANSFORMER_NAME: self.dummy_process3,
        }
        actual_trans_proc_dict_without_sys = \
            self.test_manager._transformer_process_dict
        del actual_trans_proc_dict_without_sys[SYSTEM_DATA_TRANSFORMER_NAME]

        self.assertEqual(expected_trans_proc_dict_without_sys,
                         actual_trans_proc_dict_without_sys)

    @mock.patch("src.data_transformers.starters.create_logger")
    def test_start_transformers_processes_starts_github_process_if_first_time(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger
        self.test_manager._start_transformers_processes()

        # We need to sleep to give some time for the data transformer to be
        # initialized, otherwise the process would not terminate
        time.sleep(1)

        system_data_trans_process = self.test_manager.transformer_process_dict[
            SYSTEM_DATA_TRANSFORMER_NAME]
        github_data_trans_process = self.test_manager.transformer_process_dict[
            GITHUB_DATA_TRANSFORMER_NAME]
        self.assertTrue(github_data_trans_process.is_alive())

        system_data_trans_process.terminate()
        system_data_trans_process.join()
        github_data_trans_process.terminate()
        github_data_trans_process.join()

    @mock.patch("src.data_transformers.starters.create_logger")
    def test_start_transformers_processes_starts_github_process_if_not_alive(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example

        self.test_manager._start_transformers_processes()

        # We need to sleep to give some time for the data transformer to be
        # initialized, otherwise the process would not terminate
        time.sleep(1)

        system_data_trans_process = self.test_manager.transformer_process_dict[
            SYSTEM_DATA_TRANSFORMER_NAME]
        github_data_trans_process = self.test_manager.transformer_process_dict[
            GITHUB_DATA_TRANSFORMER_NAME]
        self.assertTrue(github_data_trans_process.is_alive())

        system_data_trans_process.terminate()
        system_data_trans_process.join()
        github_data_trans_process.terminate()
        github_data_trans_process.join()

    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_start_transformers_processes_does_not_start_any_process_if_alive(
            self, mock_start, mock_is_alive) -> None:
        mock_start.return_value = None
        mock_is_alive.return_value = True

        # Make the state non-empty to mock the case when creation is not being
        # done for the first time
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example

        self.test_manager._start_transformers_processes()

        mock_start.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    def test_process_ping_sends_a_valid_hb_if_all_processes_are_alive(
            self, mock_is_alive, mock_send_hb) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat. The actual sending was already tested above. Note
        # we wil mock is_alive by setting it to always return true to avoid
        # creating processes
        mock_is_alive.return_value = True
        mock_send_hb.return_value = None
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to mock the fact that the processes were
            # already created
            self.test_manager._transformer_process_dict = \
                self.transformer_process_dict_example

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            expected_hb = {
                'component_name': self.test_manager.name,
                'running_processes': [SYSTEM_DATA_TRANSFORMER_NAME,
                                      GITHUB_DATA_TRANSFORMER_NAME],
                'dead_processes': [],
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    @mock.patch.object(DataTransformersManager, "_start_transformers_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_sends_a_valid_hb_if_some_processes_alive_some_dead(
            self, mock_join, mock_is_alive, mock_start_trans,
            mock_send_hb) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat as the actual sending was already tested above. Note
        # we wil mock is_alive by setting it to first return true and then
        # return false (note we only have two processes). By this we can avoid
        # creating processes.
        mock_is_alive.side_effect = [True, False]
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_trans.return_value = None
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to mock the fact that the processes were
            # already created
            self.test_manager._transformer_process_dict = \
                self.transformer_process_dict_example

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            expected_hb = {
                'component_name': self.test_manager.name,
                'running_processes': [SYSTEM_DATA_TRANSFORMER_NAME],
                'dead_processes': [GITHUB_DATA_TRANSFORMER_NAME],
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    @mock.patch.object(DataTransformersManager, "_start_transformers_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_sends_a_valid_hb_if_all_processes_dead(
            self, mock_join, mock_is_alive, mock_start_trans,
            mock_send_hb) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat as the actual sending was already tested above. Note
        # we wil mock is_alive by setting it to always return False. By this we
        # can avoid creating processes.
        mock_is_alive.return_value = False
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_trans.return_value = None
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to mock the fact that the processes were
            # already created
            self.test_manager._transformer_process_dict = \
                self.transformer_process_dict_example

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            expected_hb = {
                'component_name': self.test_manager.name,
                'running_processes': [],
                'dead_processes': [SYSTEM_DATA_TRANSFORMER_NAME,
                                   GITHUB_DATA_TRANSFORMER_NAME],
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    @mock.patch.object(DataTransformersManager, "_start_transformers_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_restarts_dead_processes_all_dead(
            self, mock_join, mock_is_alive, mock_start_trans,
            mock_send_hb) -> None:
        # We will perform this test by checking that
        # _start_transformers_processes is called, as the actual restarting
        # logic was already tested above. Note we wil mock is_alive by setting
        # it to always return False. By this we can avoid creating processes.
        mock_is_alive.return_value = False
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_trans.return_value = None
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to mock the fact that the processes were
            # already created
            self.test_manager._transformer_process_dict = \
                self.transformer_process_dict_example

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            mock_start_trans.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    @mock.patch.object(DataTransformersManager, "_start_transformers_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_restarts_dead_processes_some_alive_some_dead(
            self, mock_join, mock_is_alive, mock_start_trans,
            mock_send_hb) -> None:
        # We will perform this test by checking that
        # _start_transformers_processes is called, as the actual restarting
        # logic was already tested above. Note we wil mock is_alive by setting
        # it to first return False and then True. By this we can avoid creating
        # processes.
        mock_is_alive.side_effect = [False, True]
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_trans.return_value = None
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to mock the fact that the processes were
            # already created
            self.test_manager._transformer_process_dict = \
                self.transformer_process_dict_example

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            mock_start_trans.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    @mock.patch.object(DataTransformersManager, "_start_transformers_processes")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_ping_does_not_restart_dead_processes_if_all_alive(
            self, mock_join, mock_is_alive, mock_start_trans,
            mock_send_hb) -> None:
        # We will perform this test by checking that
        # _start_transformers_processes is called, as the actual restarting
        # logic was already tested above. Note we wil mock is_alive by setting
        # it to always return True. By this we can avoid creating processes.
        mock_is_alive.return_value = True
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_start_trans.return_value = None
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to mock the fact that the processes were
            # already created
            self.test_manager._transformer_process_dict = \
                self.transformer_process_dict_example

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            mock_start_trans.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_is_alive, mock_send_hb) -> None:
        # We will perform this test by checking that _send_heartbeat is not
        # called. Note we will generate an exception from is_alive
        mock_is_alive.side_effect = self.test_exception
        mock_send_hb.return_value = None
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to mock the fact that the processes were
            # already created
            self.test_manager._transformer_process_dict = \
                self.transformer_process_dict_example

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        # This test would fail if a msg not del excep is raised, as it is not
        # caught in the test.
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_connection_err_on_connection_err(
            self, mock_send_hb) -> None:
        mock_send_hb.side_effect = pika.exceptions.AMQPConnectionError('test')
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_channel_err_on_channel_err(
            self, mock_send_hb) -> None:
        mock_send_hb.side_effect = pika.exceptions.AMQPChannelError('test')
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(DataTransformersManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_exception_on_unexpected_exception(
            self, mock_send_hb) -> None:
        mock_send_hb.side_effect = self.test_exception
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=DT_MAN_INPUT_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.assertRaises(PANICException, self.test_manager._process_ping,
                              blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
