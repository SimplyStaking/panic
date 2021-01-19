import logging
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock

import pika

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.system import SystemMonitor
from src.utils.constants import RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import PANICException


class TestSystemMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger,
            connection_check_time_interval=self.connection_check_time_interval)
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.system_id = 'test_system_id'
        self.parent_id = 'test_parent_id'
        self.system_name = 'test_system'
        self.monitor_system = True
        self.node_exporter_url = 'test_url'
        self.routing_key = 'test_routing_key'
        self.test_data_str = 'test data'
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': datetime.now().timestamp()
        }
        self.test_queue_name = 'Test Queue'
        self.test_exception = PANICException('test_exception', 1)
        self.system_config = SystemConfig(self.system_id, self.parent_id,
                                          self.system_name, self.monitor_system,
                                          self.node_exporter_url)
        self.test_monitor = SystemMonitor(self.monitor_name, self.system_config,
                                          self.dummy_logger,
                                          self.monitoring_period, self.rabbitmq)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.test_exception = None
        self.system_config = None
        self.test_monitor = None

    def test_str_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.__str__())

    def test_get_monitor_period_returns_monitor_period(self) -> None:
        self.assertEqual(self.monitoring_period,
                         self.test_monitor.monitor_period)

    def test_get_monitor_name_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.monitor_name)

    def test_initialize_rabbitmq_initializes_everything_as_expected(
            self) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges have not already been declared
            self.rabbitmq.connect()
            self.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
            self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_monitor._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_monitor.rabbitmq.is_connected)
            self.assertTrue(self.test_monitor.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_monitor.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchange has been creating by sending messages
            # to it. If this fails an exception is raised hence the test fails.
            self.test_monitor.rabbitmq.basic_publish_confirm(
                exchange=RAW_DATA_EXCHANGE, routing_key=self.routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)
            self.test_monitor.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE, routing_key=self.routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)

            self.test_monitor.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitor, "_process_retrieved_data")
    @mock.patch.object(SystemMonitor, "_process_error")
    def test_process_data_calls_process_error_retrieval_error(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_error.return_value = self.test_data_dict

        self.test_monitor._process_data(self.test_data_dict, True,
                                        self.test_exception)

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        try:
            self.assertEqual(1, mock_process_error.call_count)
            self.assertEqual(0, mock_process_retrieved_data.call_count)
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitor, "_process_retrieved_data")
    @mock.patch.object(SystemMonitor, "_process_error")
    def test_process_data_calls_process_retrieved_data_on_retrieval_success(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_retrieved_data.return_value = self.test_data_dict

        self.test_monitor._process_data(self.test_data_dict, False, None)

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        try:
            self.assertEqual(0, mock_process_error.call_count)
            self.assertEqual(1, mock_process_retrieved_data.call_count)
        except AssertionError as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_monitor._initialise_rabbitmq()

            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_monitor.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.worker')
            self.test_monitor._send_heartbeat(self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_monitor.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Clean before test finishes
            self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)
            self.test_monitor.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))
