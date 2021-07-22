import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from http.client import IncompleteRead
from unittest import mock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.configs.nodes.geth import GethNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.node.geth import GethNodeMonitor
from src.utils import env
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          RAW_DATA_EXCHANGE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          GETH_NODE_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (PANICException, NodeIsDownException,
                                  DataReadingException, InvalidUrlException,
                                  MessageWasNotDeliveredException)
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit)


class TestGethNodeMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.node_id = 'test_node_id'
        self.parent_id = 'test_parent_id'
        self.node_name = 'test_node'
        self.monitor_node = True
        self.node_http_url = 'test_url'
        self.routing_key = 'test_routing_key'
        self.test_data_str = 'test data'
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.test_queue_name = 'Test Queue'
        self.retrieved_metrics_example = {
            'current_height': 2003024
        }
        self.test_exception = PANICException('test_exception', 1)
        self.node_config = GethNodeConfig(self.node_id, self.parent_id,
                                          self.node_name, self.monitor_node,
                                          self.node_http_url)
        self.test_monitor = GethNodeMonitor(self.monitor_name, self.node_config,
                                            self.dummy_logger,
                                            self.monitoring_period,
                                            self.rabbitmq)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_monitor.rabbitmq)
        delete_queue_if_exists(self.test_monitor.rabbitmq, self.test_queue_name)
        delete_exchange_if_exists(self.test_monitor.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_monitor.rabbitmq, RAW_DATA_EXCHANGE)
        disconnect_from_rabbit(self.test_monitor.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_exception = None
        self.node_config = None
        self.test_monitor = None

    def test_str_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, str(self.test_monitor))

    def test_get_monitor_period_returns_monitor_period(self) -> None:
        self.assertEqual(self.monitoring_period,
                         self.test_monitor.monitor_period)

    def test_get_monitor_name_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.monitor_name)

    def test_node_config_returns_node_config(self) -> None:
        self.assertEqual(self.node_config, self.test_monitor.node_config)

    def test_w3_interface_returns_w3_interface(self) -> None:
        self.test_monitor._w3_interface = self.test_data_str
        self.assertEqual(self.test_data_str, self.test_monitor.w3_interface)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges have not already been declared
        self.rabbitmq.connect()
        self.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_monitor._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open and
        # that the delivery confirmation variable is set.
        self.assertTrue(self.test_monitor.rabbitmq.is_connected)
        self.assertTrue(self.test_monitor.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_monitor.rabbitmq.channel._delivery_confirmation)

        # Check whether the exchange has been creating by sending messages to
        # it. If this fails an exception is raised hence the test fails.
        self.test_monitor.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE, routing_key=self.routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)
        self.test_monitor.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=self.routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

    @mock.patch.object(GethNodeMonitor, "_process_retrieved_data")
    @mock.patch.object(GethNodeMonitor, "_process_error")
    def test_process_data_calls_process_error_on_retrieval_error(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_error.return_value = self.test_data_dict

        self.test_monitor._process_data(True, [self.test_exception], [])

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        self.assertEqual(1, mock_process_error.call_count)
        self.assertEqual(0, mock_process_retrieved_data.call_count)

    @mock.patch.object(GethNodeMonitor, "_process_retrieved_data")
    @mock.patch.object(GethNodeMonitor, "_process_error")
    def test_process_data_calls_process_retrieved_data_on_retrieval_success(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_retrieved_data.return_value = self.test_data_dict

        self.test_monitor._process_data(False, [], [self.test_data_dict])

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        self.assertEqual(0, mock_process_error.call_count)
        self.assertEqual(1, mock_process_retrieved_data.call_count)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        self.test_monitor._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
        self.test_monitor._send_heartbeat(self.test_heartbeat)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    def test_display_data_returns_the_correct_string(self) -> None:
        expected_output = "current_height={}".format(
            self.retrieved_metrics_example['current_height'])
        actual_output = self.test_monitor._display_data(
            self.retrieved_metrics_example)
        self.assertEqual(expected_output, actual_output)

    @freeze_time("2012-01-01")
    def test_process_error_returns_expected_data(self) -> None:
        expected_output = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        actual_output = self.test_monitor._process_error(self.test_exception)
        self.assertEqual(actual_output, expected_output)

    @freeze_time("2012-01-01")
    def test_process_retrieved_data_returns_expected_data(self) -> None:
        expected_output = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': self.retrieved_metrics_example,
            }
        }

        actual_output = self.test_monitor._process_retrieved_data(
            self.retrieved_metrics_example)
        self.assertEqual(expected_output, actual_output)

    def test_send_data_sends_data_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_data, and checks that the data is
        # received
        self.test_monitor._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
            routing_key=GETH_NODE_RAW_DATA_ROUTING_KEY)

        self.test_monitor._send_data(self.test_data_dict)

        # By re-declaring the queue again we can get the number of messages in
        # the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_data_dict, json.loads(body))

    @freeze_time("2012-01-01")
    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data, mock_send_hb, mock_send_data) -> None:
        expected_output_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': self.retrieved_metrics_example,
            }
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }

        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_data.return_value = None
        mock_send_hb.return_value = None

        self.test_monitor._monitor()

        mock_send_hb.assert_called_once_with(expected_output_hb)
        mock_send_data.assert_called_once_with(expected_output_data)

    @mock.patch.object(GethNodeMonitor, "_process_data")
    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_sends_no_data_and_hb_if_data_ret_success_and_proc_fails(
            self, mock_get_data, mock_send_hb, mock_send_data,
            mock_process_data) -> None:
        mock_process_data.side_effect = self.test_exception
        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        self.test_monitor._initialise_rabbitmq()

        self.test_monitor._monitor()

        mock_send_hb.assert_not_called()
        mock_send_data.assert_not_called()

    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_sends_no_data_and_no_hb_on_get_data_unexpected_exception(
            self, mock_get_data, mock_send_hb, mock_send_data) -> None:
        mock_get_data.side_effect = self.test_exception
        mock_send_hb.return_value = None
        mock_send_data.return_value = None

        self.assertRaises(PANICException, self.test_monitor._monitor)

        mock_send_data.assert_not_called()
        mock_send_hb.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_sends_exception_data_and_hb_on_expected_exceptions(
            self, mock_get_data, mock_send_hb, mock_send_data) -> None:
        errors_exceptions_dict = {
            ReqConnectionError('test'): NodeIsDownException(
                self.test_monitor.node_config.node_name),
            ReadTimeout('test'): NodeIsDownException(
                self.test_monitor.node_config.node_name),
            IncompleteRead('test'): DataReadingException(
                self.test_monitor.monitor_name,
                self.test_monitor.node_config.node_name),
            ChunkedEncodingError('test'): DataReadingException(
                self.test_monitor.monitor_name,
                self.test_monitor.node_config.node_name),
            ProtocolError('test'): DataReadingException(
                self.test_monitor.monitor_name,
                self.test_monitor.node_config.node_name),
            InvalidURL('test'): InvalidUrlException(
                self.test_monitor.node_config.node_http_url),
            InvalidSchema('test'): InvalidUrlException(
                self.test_monitor.node_config.node_http_url),
            MissingSchema('test'): InvalidUrlException(
                self.test_monitor.node_config.node_http_url),
        }
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        for error, data_ret_exception in errors_exceptions_dict.items():
            mock_get_data.side_effect = error
            expected_output_data = {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp()
                    },
                    'message': data_ret_exception.message,
                    'code': data_ret_exception.code,
                }
            }
            expected_output_hb = {
                'component_name': self.test_monitor.monitor_name,
                'is_alive': True,
                'timestamp': datetime(2012, 1, 1).timestamp()
            }

            self.test_monitor._monitor()

            mock_send_data.assert_called_once_with(expected_output_data)
            mock_send_hb.assert_called_once_with(expected_output_hb)

            # Reset for next test
            mock_send_hb.reset_mock()
            mock_send_data.reset_mock()

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
        (MessageWasNotDeliveredException,
         MessageWasNotDeliveredException('test'))
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_raises_error_if_raised_by_send_hb_and_sends_data(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_hb, mock_send_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_data.return_value = None
        expected_output_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': self.retrieved_metrics_example,
            }
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }
        mock_send_hb.side_effect = exception_instance

        self.assertRaises(exception_class, self.test_monitor._monitor)

        mock_send_hb.assert_called_once_with(expected_output_hb)
        mock_send_data.assert_called_once_with(expected_output_data)

    @freeze_time("2012-01-01")
    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_does_not_send_hb_and_data_if_send_data_fails(
            self, mock_get_data, mock_send_hb, mock_send_data) -> None:
        mock_get_data.return_value = self.retrieved_metrics_example
        mock_send_hb.return_value = None
        exception_types_dict = {
            Exception('test'): Exception,
            pika.exceptions.AMQPConnectionError('test'):
                pika.exceptions.AMQPConnectionError,
            pika.exceptions.AMQPChannelError('test'):
                pika.exceptions.AMQPChannelError,
            MessageWasNotDeliveredException('test'):
                MessageWasNotDeliveredException
        }
        expected_output_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': self.retrieved_metrics_example,
            }
        }
        for exception, exception_type in exception_types_dict.items():
            mock_send_data.side_effect = exception
            self.assertRaises(exception_type, self.test_monitor._monitor)
            mock_send_data.assert_called_once_with(expected_output_data)
            mock_send_hb.assert_not_called()

            # Reset for next test
            mock_send_hb.reset_mock()
            mock_send_data.reset_mock()

    @mock.patch.object(logging.Logger, "info")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_logs_data_if_no_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = self.retrieved_metrics_example

        self.test_monitor._monitor()

        mock_log.assert_called_with(self.test_monitor._display_data(
            self.retrieved_metrics_example))

    @mock.patch.object(logging.Logger, "info")
    @mock.patch.object(GethNodeMonitor, "_send_heartbeat")
    @mock.patch.object(GethNodeMonitor, "_send_data")
    @mock.patch.object(GethNodeMonitor, "_get_data")
    def test_monitor_does_not_log_if_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.side_effect = ReqConnectionError('test')
        self.test_monitor._monitor()
        mock_log.assert_not_called()
