import copy
import json
import logging
import unittest
from collections import ChainMap
from datetime import datetime
from datetime import timedelta
from http.client import IncompleteRead
from typing import Dict
from unittest import mock
from unittest.mock import call

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.node.chainlink import ChainlinkNodeMonitor
from src.utils import env
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          RAW_DATA_EXCHANGE,
                                          CHAINLINK_NODE_RAW_DATA_ROUTING_KEY,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.exceptions import (PANICException,
                                  EnabledSourceIsEmptyException,
                                  MetricNotFoundException, NodeIsDownException,
                                  DataReadingException, InvalidUrlException,
                                  MessageWasNotDeliveredException)
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit,
                              assert_not_called_with)


class TestChainlinkNodeMonitor(unittest.TestCase):
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
        self.monitor_prometheus = True
        self.node_prometheus_urls = ['https://test_ip_1:1000',
                                     'https://test_ip_2:1000',
                                     'https://test_ip_3:1000']
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
        self.prometheus_metrics = {
            'head_tracker_current_head': 'strict',
            'head_tracker_heads_in_queue': 'strict',
            'head_tracker_heads_received_total': 'strict',
            'head_tracker_num_heads_dropped_total': 'strict',
            'job_subscriber_subscriptions': 'strict',
            'max_unconfirmed_blocks': 'strict',
            'process_start_time_seconds': 'strict',
            'tx_manager_num_gas_bumps_total': 'strict',
            'tx_manager_gas_bump_exceeds_limit_total': 'strict',
            'unconfirmed_transactions': 'strict',
            'gas_updater_set_gas_price': 'optional',
            'eth_balance': 'strict',
            'run_status_update_total': 'strict',
        }
        self.retrieved_prometheus_data_example = {
            'eth_balance': {'{"account": "eth_add_1"}': 26.043292035081947},
            'gas_updater_set_gas_price': {
                '{"percentile": "20%"}': 5000000000.0
            },
            'head_tracker_current_head': 6924314.0,
            'head_tracker_heads_in_queue': 0.0,
            'head_tracker_heads_received_total': 26392.0,
            'head_tracker_num_heads_dropped_total': 2.0,
            'job_subscriber_subscriptions': 0.0,
            'max_unconfirmed_blocks': 0.0,
            'process_start_time_seconds': 1619431240.24,
            'run_status_update_total': {
                '{"from_status": "", "job_spec_id": '
                '"03ba2f182d5e4245b8492e7f8672482e", '
                '"status": "in_progress"}': 129.0,
                '{"from_status": "", "job_spec_id": '
                '"0b7dd91f5e8a40d8b0493fc0799fe5d3", '
                '"status": "in_progress"}': 189.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"03ba2f182d5e4245b8492e7f8672482e", '
                '"status": "completed"}': 389.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"03ba2f182d5e4245b8492e7f8672482e", "status": '
                '"pending_outgoing_confirmations"}': 1898.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"0b7dd91f5e8a40d8b0493fc0799fe5d3", '
                '"status": "completed"}': 569.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"0b7dd91f5e8a40d8b0493fc0799fe5d3", '
                '"status": "pending_outgoing_confirmations"}': 2780.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"2aacf8ce6827410dae6ff2ce68938edb", "status": "errored"}': 1.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"3cc0a79b77f8404fa193c1e56b3f29bf", '
                '"status": "errored"}': 90.0,
                '{"from_status": "in_progress", '
                '"job_spec_id": "4ae35b033a294c3db78a45db9ada9a57", '
                '"status": "errored"}': 1.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"7594586a567d4700b1a794f3363569e1", "status": "errored"}': 1.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"834275814b3b46de83aa7770dbc90912", "status": "errored"}': 4.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"8d2cde397b17415486bbd79de84c901e", '
                '"status": "errored"}': 112.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"d0dd062c26794ff1a9b9460cd5d529f6", "status": "errored"}': 2.0,
                '{"from_status": "in_progress", "job_spec_id": '
                '"f2e35bcb37b04198a9241121cd936572", "status": "errored"}': 4.0,
            },
            'tx_manager_gas_bump_exceeds_limit_total': 0.0,
            'tx_manager_num_gas_bumps_total': 2031.0,
            'unconfirmed_transactions': 1.0
        }
        self.retrieved_prometheus_data_example_optionals_none = copy.deepcopy(
            self.retrieved_prometheus_data_example)
        self.retrieved_prometheus_data_example_optionals_none[
            'gas_updater_set_gas_price'] = None
        self.processed_prometheus_data_example = {
            'head_tracker_current_head': 6924314.0,
            'head_tracker_heads_in_queue': 0.0,
            'head_tracker_heads_received_total': 26392.0,
            'head_tracker_num_heads_dropped_total': 2.0,
            'job_subscriber_subscriptions': 0.0,
            'max_unconfirmed_blocks': 0.0,
            'process_start_time_seconds': 1619431240.24,
            'tx_manager_gas_bump_exceeds_limit_total': 0.0,
            'tx_manager_num_gas_bumps_total': 2031.0,
            'unconfirmed_transactions': 1.0,
            'gas_updater_set_gas_price': {
                'percentile': '20%',
                'price': 5000000000.0
            },
            'eth_balance': {
                'address': 'eth_add_1',
                'balance': 26.043292035081947
            },
            'run_status_update_total_errors': 8
        }
        self.processed_prometheus_data_example_optionals_none = copy.deepcopy(
            self.processed_prometheus_data_example)
        self.processed_prometheus_data_example_optionals_none[
            'gas_updater_set_gas_price'] = None
        self.test_exception = PANICException('test_exception', 1)
        self.node_config = ChainlinkNodeConfig(
            self.node_id, self.parent_id, self.node_name, self.monitor_node,
            self.monitor_prometheus, self.node_prometheus_urls)
        self.test_monitor = ChainlinkNodeMonitor(
            self.monitor_name, self.node_config, self.dummy_logger,
            self.monitoring_period, self.rabbitmq
        )

        # The dicts below will make more sense when more source types are added
        self.received_retrieval_info_all_source_types_enabled = {
            'prometheus': {
                'data': self.retrieved_prometheus_data_example,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_prometheus_data,
                'processing_function':
                    self.test_monitor._process_retrieved_prometheus_data,
                'last_source_used_var': 'self._last_prometheus_source_used',
                'monitoring_enabled_var': 'self.node_config._monitor_prometheus'
            }
            # When more sources are added this should contain source types with
            # successfully obtained data.
        }
        self.received_retrieval_info_prometheus_disabled = {
            'prometheus': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_prometheus_data,
                'processing_function':
                    self.test_monitor._process_retrieved_prometheus_data,
                'last_source_used_var': 'self._last_prometheus_source_used',
                'monitoring_enabled_var': 'self.node_config._monitor_prometheus'
            }
            # When more sources are added this should contain source types with
            # successfully obtained data.
        }
        self.received_retrieval_info_all_source_types_enabled_err = {
            'prometheus': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_prometheus_data,
                'processing_function':
                    self.test_monitor._process_retrieved_prometheus_data,
                'last_source_used_var': 'self._last_prometheus_source_used',
                'monitoring_enabled_var': 'self.node_config._monitor_prometheus'
            }
            # When more sources are added this should contain source types with
            # successfully obtained data.
        }
        # TODO: When more sources are added we can add
        #  self.received_retrieval_info_prometheus_disabled_err

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

    def test_prometheus_metrics_returns_prometheus_metrics(self) -> None:
        self.assertEqual(self.prometheus_metrics,
                         self.test_monitor.prometheus_metrics)

    def test_last_prometheus_source_used_returns_last_prometheus_source_used(
            self) -> None:
        # Check that on startup
        # last_prometheus_source_used = node_prometheus_urls[0]
        self.assertEqual(self.node_prometheus_urls[0],
                         self.test_monitor.last_prometheus_source_used)

        # Check for any other value
        self.test_monitor._last_prometheus_source_used = \
            self.node_prometheus_urls[1]
        self.assertEqual(self.node_prometheus_urls[1],
                         self.test_monitor.last_prometheus_source_used)

    @parameterized.expand([
        ([],)
    ])
    def test_init_raises_EnabledSourceIsEmptyException_if_empty_enabled_source(
            self, node_prometheus_urls) -> None:
        """
        This function should be parameterized further once we increase the
        number of data sources.
        """
        node_config = ChainlinkNodeConfig(
            self.node_id, self.parent_id, self.node_name, self.monitor_node,
            self.monitor_prometheus, node_prometheus_urls)
        self.assertRaises(
            EnabledSourceIsEmptyException, ChainlinkNodeMonitor,
            self.monitor_name, node_config, self.dummy_logger,
            self.monitoring_period, self.rabbitmq)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already
        # established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges have not already been declared
        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

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

    @mock.patch.object(ChainlinkNodeMonitor, "_process_retrieved_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_process_error")
    def test_process_data_calls_process_error_on_retrieval_error(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_error.return_value = self.test_data_dict

        self.test_monitor._process_data(True, [self.test_exception],
                                        [self.test_data_dict])

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        self.assertEqual(1, mock_process_error.call_count)
        self.assertEqual(0, mock_process_retrieved_data.call_count)

    @mock.patch.object(ChainlinkNodeMonitor, "_process_retrieved_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_process_error")
    def test_process_data_calls_process_retrieved_data_on_retrieval_success(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_retrieved_data.return_value = self.test_data_dict

        self.test_monitor._process_data(False, [self.test_exception],
                                        [self.test_data_dict])

        # Test passes if _process_error is not called and process_retrieved_data
        # is called once
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
        _, _, body = self.test_monitor.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    def test_display_data_returns_the_correct_string_if_all_metrics_present(
            self) -> None:
        # Test when optionals are not None
        expected_output = \
            "head_tracker_current_head={}, head_tracker_heads_in_queue={}, " \
            "head_tracker_heads_received_total={}, " \
            "head_tracker_num_heads_dropped_total={}, " \
            "job_subscriber_subscriptions={}, max_unconfirmed_blocks={}, " \
            "process_start_time_seconds={}, " \
            "tx_manager_num_gas_bumps_total={}, " \
            "tx_manager_gas_bump_exceeds_limit_total={}, " \
            "unconfirmed_transactions={}, gas_updater_set_gas_price={}, " \
            "eth_balance={}, run_status_update_total_errors={}" \
            "".format(
                self.processed_prometheus_data_example[
                    'head_tracker_current_head'],
                self.processed_prometheus_data_example[
                    'head_tracker_heads_in_queue'],
                self.processed_prometheus_data_example[
                    'head_tracker_heads_received_total'],
                self.processed_prometheus_data_example[
                    'head_tracker_num_heads_dropped_total'],
                self.processed_prometheus_data_example[
                    'job_subscriber_subscriptions'],
                self.processed_prometheus_data_example[
                    'max_unconfirmed_blocks'],
                self.processed_prometheus_data_example[
                    'process_start_time_seconds'],
                self.processed_prometheus_data_example[
                    'tx_manager_num_gas_bumps_total'],
                self.processed_prometheus_data_example[
                    'tx_manager_gas_bump_exceeds_limit_total'],
                self.processed_prometheus_data_example[
                    'unconfirmed_transactions'],
                self.processed_prometheus_data_example[
                    'gas_updater_set_gas_price'],
                self.processed_prometheus_data_example['eth_balance'],
                self.processed_prometheus_data_example[
                    'run_status_update_total_errors']
            )

        actual_output = self.test_monitor._display_data(
            self.processed_prometheus_data_example)
        self.assertEqual(expected_output, actual_output)

        # Test when optionals are None
        expected_output = \
            "head_tracker_current_head={}, head_tracker_heads_in_queue={}, " \
            "head_tracker_heads_received_total={}, " \
            "head_tracker_num_heads_dropped_total={}, " \
            "job_subscriber_subscriptions={}, max_unconfirmed_blocks={}, " \
            "process_start_time_seconds={}, " \
            "tx_manager_num_gas_bumps_total={}, " \
            "tx_manager_gas_bump_exceeds_limit_total={}, " \
            "unconfirmed_transactions={}, gas_updater_set_gas_price={}, " \
            "eth_balance={}, run_status_update_total_errors={}" \
            "".format(
                self.processed_prometheus_data_example_optionals_none[
                    'head_tracker_current_head'],
                self.processed_prometheus_data_example_optionals_none[
                    'head_tracker_heads_in_queue'],
                self.processed_prometheus_data_example_optionals_none[
                    'head_tracker_heads_received_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'head_tracker_num_heads_dropped_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'job_subscriber_subscriptions'],
                self.processed_prometheus_data_example_optionals_none[
                    'max_unconfirmed_blocks'],
                self.processed_prometheus_data_example_optionals_none[
                    'process_start_time_seconds'],
                self.processed_prometheus_data_example_optionals_none[
                    'tx_manager_num_gas_bumps_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'tx_manager_gas_bump_exceeds_limit_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'unconfirmed_transactions'],
                self.processed_prometheus_data_example_optionals_none[
                    'gas_updater_set_gas_price'],
                self.processed_prometheus_data_example_optionals_none[
                    'eth_balance'],
                self.processed_prometheus_data_example_optionals_none[
                    'run_status_update_total_errors']
            )

        actual_output = self.test_monitor._display_data(
            self.processed_prometheus_data_example_optionals_none)
        self.assertEqual(expected_output, actual_output)

    def test_display_data_returns_the_correct_string_if_not_all_metrics_present(
            self) -> None:
        # Test when optionals are not None
        del self.processed_prometheus_data_example['head_tracker_current_head']
        del self.processed_prometheus_data_example['eth_balance']
        expected_output = \
            "head_tracker_current_head={}, head_tracker_heads_in_queue={}, " \
            "head_tracker_heads_received_total={}, " \
            "head_tracker_num_heads_dropped_total={}, " \
            "job_subscriber_subscriptions={}, max_unconfirmed_blocks={}, " \
            "process_start_time_seconds={}, " \
            "tx_manager_num_gas_bumps_total={}, " \
            "tx_manager_gas_bump_exceeds_limit_total={}, " \
            "unconfirmed_transactions={}, gas_updater_set_gas_price={}, " \
            "eth_balance={}, run_status_update_total_errors={}" \
            "".format(
                "Disabled",
                self.processed_prometheus_data_example[
                    'head_tracker_heads_in_queue'],
                self.processed_prometheus_data_example[
                    'head_tracker_heads_received_total'],
                self.processed_prometheus_data_example[
                    'head_tracker_num_heads_dropped_total'],
                self.processed_prometheus_data_example[
                    'job_subscriber_subscriptions'],
                self.processed_prometheus_data_example[
                    'max_unconfirmed_blocks'],
                self.processed_prometheus_data_example[
                    'process_start_time_seconds'],
                self.processed_prometheus_data_example[
                    'tx_manager_num_gas_bumps_total'],
                self.processed_prometheus_data_example[
                    'tx_manager_gas_bump_exceeds_limit_total'],
                self.processed_prometheus_data_example[
                    'unconfirmed_transactions'],
                self.processed_prometheus_data_example[
                    'gas_updater_set_gas_price'],
                "Disabled",
                self.processed_prometheus_data_example[
                    'run_status_update_total_errors']
            )

        actual_output = self.test_monitor._display_data(
            self.processed_prometheus_data_example)
        self.assertEqual(expected_output, actual_output)

        # Test when optionals are None
        del self.processed_prometheus_data_example_optionals_none[
            'head_tracker_current_head']
        del self.processed_prometheus_data_example_optionals_none[
            'eth_balance']
        expected_output = \
            "head_tracker_current_head={}, head_tracker_heads_in_queue={}, " \
            "head_tracker_heads_received_total={}, " \
            "head_tracker_num_heads_dropped_total={}, " \
            "job_subscriber_subscriptions={}, max_unconfirmed_blocks={}, " \
            "process_start_time_seconds={}, " \
            "tx_manager_num_gas_bumps_total={}, " \
            "tx_manager_gas_bump_exceeds_limit_total={}, " \
            "unconfirmed_transactions={}, gas_updater_set_gas_price={}, " \
            "eth_balance={}, run_status_update_total_errors={}" \
            "".format(
                "Disabled",
                self.processed_prometheus_data_example_optionals_none[
                    'head_tracker_heads_in_queue'],
                self.processed_prometheus_data_example_optionals_none[
                    'head_tracker_heads_received_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'head_tracker_num_heads_dropped_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'job_subscriber_subscriptions'],
                self.processed_prometheus_data_example_optionals_none[
                    'max_unconfirmed_blocks'],
                self.processed_prometheus_data_example_optionals_none[
                    'process_start_time_seconds'],
                self.processed_prometheus_data_example_optionals_none[
                    'tx_manager_num_gas_bumps_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'tx_manager_gas_bump_exceeds_limit_total'],
                self.processed_prometheus_data_example_optionals_none[
                    'unconfirmed_transactions'],
                self.processed_prometheus_data_example_optionals_none[
                    'gas_updater_set_gas_price'],
                "Disabled",
                self.processed_prometheus_data_example_optionals_none[
                    'run_status_update_total_errors']
            )

        actual_output = self.test_monitor._display_data(
            self.processed_prometheus_data_example_optionals_none)
        self.assertEqual(expected_output, actual_output)

    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_first_attempts_retrieval_using_last_prom_source_used(
            self, mock_get_prometheus_metrics_data) -> None:
        mock_get_prometheus_metrics_data.return_value = \
            self.processed_prometheus_data_example

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        actual_output = self.test_monitor._get_prometheus_data()
        mock_get_prometheus_metrics_data.assert_called_once_with(
            old_last_prometheus_source_used, self.prometheus_metrics,
            self.dummy_logger, verify=False)
        self.assertEqual(self.processed_prometheus_data_example, actual_output)

    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_does_not_change_last_prom_sourced_used_if_online(
            self, mock_get_prometheus_metrics_data) -> None:
        mock_get_prometheus_metrics_data.return_value = \
            self.processed_prometheus_data_example

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        self.test_monitor._get_prometheus_data()
        self.assertEqual(old_last_prometheus_source_used,
                         self.test_monitor.last_prometheus_source_used)

    @parameterized.expand([
        (IncompleteRead, IncompleteRead('test'),),
        (ChunkedEncodingError, ChunkedEncodingError('test'),),
        (ProtocolError, ProtocolError('test'),),
        (InvalidURL, InvalidURL('test'),),
        (InvalidSchema, InvalidSchema('test'),),
        (MissingSchema, MissingSchema('test'),),
        (MetricNotFoundException, MetricNotFoundException('test', 'test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_raises_non_conn_err_if_last_source_used_on_and_errs(
            self, exception_class, exception_instance,
            mock_get_prometheus_metrics_data) -> None:
        mock_get_prometheus_metrics_data.side_effect = exception_instance

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        self.assertRaises(exception_class,
                          self.test_monitor._get_prometheus_data)
        mock_get_prometheus_metrics_data.assert_called_once_with(
            old_last_prometheus_source_used, self.prometheus_metrics,
            self.dummy_logger, verify=False)

    @parameterized.expand([
        (IncompleteRead, IncompleteRead('test'),),
        (ChunkedEncodingError, ChunkedEncodingError('test'),),
        (ProtocolError, ProtocolError('test'),),
        (InvalidURL, InvalidURL('test'),),
        (InvalidSchema, InvalidSchema('test'),),
        (MissingSchema, MissingSchema('test'),),
        (MetricNotFoundException, MetricNotFoundException('test', 'test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_no_change_last_source_used_if_online_and_it_errors(
            self, exception_class, exception_instance,
            mock_get_prometheus_metrics_data) -> None:
        # Here we are assuming that the error is not connection related
        mock_get_prometheus_metrics_data.side_effect = exception_instance

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        try:
            self.test_monitor._get_data()
        except exception_class:
            pass
        self.assertEqual(old_last_prometheus_source_used,
                         self.test_monitor.last_prometheus_source_used)

    @parameterized.expand([
        (ReadTimeout('test'),),
        (ReqConnectionError('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_gets_data_from_online_source_if_last_source_used_off(
            self, exception_instance, mock_get_prometheus_metrics_data) -> None:
        # In this case we are setting the final source to be online
        mock_get_prometheus_metrics_data.side_effect = [
            exception_instance, exception_instance, exception_instance,
            self.processed_prometheus_data_example]

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        actual_output = self.test_monitor._get_prometheus_data()
        actual_calls = mock_get_prometheus_metrics_data.call_args_list
        self.assertEqual(4, len(actual_calls))

        # In this case there are two calls to
        # self.test_monitor.node_config._node_prometheus_urls[0] because
        # initially this url was also the last prometheus source used.
        expected_calls = [call(old_last_prometheus_source_used,
                               self.prometheus_metrics, self.dummy_logger,
                               verify=False)]
        for i in range(0, len(self.node_prometheus_urls)):
            expected_calls.append(call(
                self.test_monitor.node_config.node_prometheus_urls[i],
                self.prometheus_metrics, self.dummy_logger, verify=False))

        self.assertEqual(expected_calls, actual_calls)
        self.assertEqual(self.processed_prometheus_data_example, actual_output)

    @parameterized.expand([
        (ReadTimeout('test'),),
        (ReqConnectionError('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_changes_last_source_if_last_source_off_other_node_on(
            self, exception_instance, mock_get_prometheus_metrics_data) -> None:
        # In this case we are setting the final source to be online
        mock_get_prometheus_metrics_data.side_effect = [
            exception_instance, exception_instance, exception_instance,
            self.processed_prometheus_data_example]
        self.test_monitor._get_prometheus_data()
        self.assertEqual(self.test_monitor.node_config.node_prometheus_urls[-1],
                         self.test_monitor.last_prometheus_source_used)

    @parameterized.expand([
        (IncompleteRead, IncompleteRead('test'),),
        (ChunkedEncodingError, ChunkedEncodingError('test'),),
        (ProtocolError, ProtocolError('test'),),
        (InvalidURL, InvalidURL('test'),),
        (InvalidSchema, InvalidSchema('test'),),
        (MissingSchema, MissingSchema('test'),),
        (MetricNotFoundException, MetricNotFoundException('test', 'test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_raises_non_connection_err_if_online_source_errors(
            self, exception_class, exception_instance,
            mock_get_prometheus_metrics_data) -> None:
        # Here we will assume that the last prometheus source used was deemed as
        # offline as we have already tested the online case in a previous test.
        # We will also assume that the second source is online but it errors.
        mock_get_prometheus_metrics_data.side_effect = [
            ReqConnectionError('test'), ReqConnectionError('test'),
            exception_instance]

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        self.assertRaises(exception_class,
                          self.test_monitor._get_prometheus_data)
        actual_calls = mock_get_prometheus_metrics_data.call_args_list
        self.assertEqual(3, len(actual_calls))
        self.assertEqual([
            call(old_last_prometheus_source_used, self.prometheus_metrics,
                 self.dummy_logger, verify=False),
            call(self.test_monitor.node_config._node_prometheus_urls[0],
                 self.prometheus_metrics, self.dummy_logger, verify=False),
            call(self.test_monitor.node_config._node_prometheus_urls[1],
                 self.prometheus_metrics, self.dummy_logger, verify=False)],
            actual_calls)

    @parameterized.expand([
        (IncompleteRead, IncompleteRead('test'),),
        (ChunkedEncodingError, ChunkedEncodingError('test'),),
        (ProtocolError, ProtocolError('test'),),
        (InvalidURL, InvalidURL('test'),),
        (InvalidSchema, InvalidSchema('test'),),
        (MissingSchema, MissingSchema('test'),),
        (MetricNotFoundException, MetricNotFoundException('test', 'test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_changes_last_prom_source_used_if_online_source_errs(
            self, exception_class, exception_instance,
            mock_get_prometheus_metrics_data) -> None:
        # Here we will assume that the last prometheus source used was deemed as
        # offline as we have already tested when it is online in a previous
        # test. We will also assume that the second source is online but it
        # errors.
        mock_get_prometheus_metrics_data.side_effect = [
            ReqConnectionError('test'), ReqConnectionError('test'),
            exception_instance]

        try:
            self.test_monitor._get_prometheus_data()
        except exception_class:
            pass
        self.assertEqual(self.test_monitor.node_config.node_prometheus_urls[1],
                         self.test_monitor.last_prometheus_source_used)

    @parameterized.expand([
        (ReadTimeout('test'),),
        (ReqConnectionError('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_raises_NodeIsDownException_if_all_prom_sources_down(
            self, exception_instance, mock_get_prometheus_metrics_data) -> None:
        mock_get_prometheus_metrics_data.side_effect = [
            exception_instance, exception_instance, exception_instance,
            exception_instance]

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        self.assertRaises(NodeIsDownException,
                          self.test_monitor._get_prometheus_data)
        actual_calls = mock_get_prometheus_metrics_data.call_args_list
        self.assertEqual(4, len(actual_calls))

        # In this case there are two calls to
        # self.test_monitor.node_config._node_prometheus_urls[0] because
        # initially this url was also the last prometheus source used.
        expected_calls = [call(old_last_prometheus_source_used,
                               self.prometheus_metrics, self.dummy_logger,
                               verify=False)]
        for i in range(0, len(self.node_prometheus_urls)):
            expected_calls.append(call(
                self.test_monitor.node_config.node_prometheus_urls[i],
                self.prometheus_metrics, self.dummy_logger, verify=False))

        self.assertEqual(expected_calls, actual_calls)

    @parameterized.expand([
        (ReadTimeout('test'),),
        (ReqConnectionError('test'),),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_prom_data_does_not_change_last_prom_source_used_if_all_down(
            self, exception_instance, mock_get_prometheus_metrics_data) -> None:
        mock_get_prometheus_metrics_data.side_effect = [
            exception_instance, exception_instance, exception_instance,
            exception_instance]

        old_last_prometheus_source_used = \
            self.test_monitor.last_prometheus_source_used
        try:
            self.test_monitor._get_prometheus_data()
        except NodeIsDownException:
            pass
        self.assertEqual(old_last_prometheus_source_used,
                         self.test_monitor.last_prometheus_source_used)

    @parameterized.expand([
        ('self.received_retrieval_info_prometheus_disabled', [], False,),
        ('self.received_retrieval_info_all_source_types_enabled',
         ['self.retrieved_prometheus_data_example'], True,),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_data_return_if_no_errors_raised(
            self, expected_return, retrieved_prometheus_data,
            monitor_prometheus, mock_get_prometheus_metrics_data) -> None:
        get_prometheus_metrics_data_return = list(map(
            eval, retrieved_prometheus_data))
        mock_get_prometheus_metrics_data.side_effect = \
            get_prometheus_metrics_data_return
        self.test_monitor._node_config._monitor_prometheus = monitor_prometheus

        actual_ret = self.test_monitor._get_data()
        expected_ret = eval(expected_return)
        self.assertEqual(expected_ret, actual_ret)

    @parameterized.expand([
        ("IncompleteRead('test')",
         "DataReadingException(self.test_monitor.monitor_name, self.test_monitor.last_prometheus_source_used)",
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
        ("ChunkedEncodingError('test')",
         "DataReadingException(self.test_monitor.monitor_name, self.test_monitor.last_prometheus_source_used)",
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
        ("ProtocolError('test')",
         "DataReadingException(self.test_monitor.monitor_name, self.test_monitor.last_prometheus_source_used)",
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
        ("InvalidURL('test')",
         "InvalidUrlException(self.test_monitor.last_prometheus_source_used)",
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
        ("InvalidSchema('test')",
         "InvalidUrlException(self.test_monitor.last_prometheus_source_used)",
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
        ("MissingSchema('test')",
         "InvalidUrlException(self.test_monitor.last_prometheus_source_used)",
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
        ("MetricNotFoundException('test_metric', 'test_endpoint')",
         "MetricNotFoundException('test_metric', 'test_endpoint')",
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
        ('NodeIsDownException(self.node_name)',
         'NodeIsDownException(self.node_name)',
         'self.received_retrieval_info_all_source_types_enabled_err', True,
         'prometheus'),
    ])
    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_data_return_if_recognised_error_raised(
            self, raised_err, returned_err, expected_return, monitor_prometheus,
            errored_source_type, mock_get_prometheus_metrics_data) -> None:
        # This test will be expanded when adding more source types to cater for
        # when monitor_prometheus is False
        mock_get_prometheus_metrics_data.side_effect = \
            eval(raised_err) if errored_source_type == "prometheus" else None
        self.test_monitor._node_config._monitor_prometheus = monitor_prometheus

        actual_ret = self.test_monitor._get_data()
        expected_ret = eval(expected_return)
        expected_ret[errored_source_type][
            'data_retrieval_exception'] = eval(returned_err)
        self.assertEqual(expected_ret, actual_ret)

    @mock.patch("src.monitors.node.chainlink.get_prometheus_metrics_data")
    def test_get_data_raises_unrecognised_error_if_raised(
            self, mock_get_prometheus_metrics_data) -> None:
        mock_get_prometheus_metrics_data.side_effect = self.test_exception
        self.assertRaises(PANICException, self.test_monitor._get_data)

    @parameterized.expand([
        ("self.test_monitor.last_prometheus_source_used",),
    ])
    @freeze_time("2012-01-01")
    def test_process_error_returns_expected_data(self,
                                                 last_source_used) -> None:
        # We will add more parameters to this test as the source types increase
        expected_output = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'last_source_used': eval(last_source_used),
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        actual_output = self.test_monitor._process_error(self.test_exception,
                                                         eval(last_source_used))
        self.assertEqual(actual_output, expected_output)

    @parameterized.expand([
        ("self.processed_prometheus_data_example",
         "self.retrieved_prometheus_data_example"),
        ("self.processed_prometheus_data_example_optionals_none",
         "self.retrieved_prometheus_data_example_optionals_none"),
    ])
    @freeze_time("2012-01-01")
    def test_process_retrieved_prometheus_data_returns_expected_data(
            self, expected_data_output, retrieved_data) -> None:
        expected_output = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'last_source_used':
                        self.test_monitor.last_prometheus_source_used,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': eval(expected_data_output),
            }
        }

        actual_output = self.test_monitor._process_retrieved_prometheus_data(
            eval(retrieved_data))
        self.assertEqual(expected_output, actual_output)

    def test_process_retrieved_data_returns_the_correct_dict(self) -> None:
        def test_fn(x: Dict): return x

        actual_ret = self.test_monitor._process_retrieved_data(
            test_fn, self.test_data_dict)
        expected_ret = test_fn(self.test_data_dict)
        self.assertEqual(expected_ret, actual_ret)

    def test_send_data_sends_data_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_data, and checks that the
        # data is received
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
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)

        self.test_monitor._send_data(self.processed_prometheus_data_example)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.processed_prometheus_data_example,
                         json.loads(body))

    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data) -> None:
        # Here we are assuming that all sources are enabled.
        expected_output_data = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'last_source_used':
                            self.test_monitor.last_prometheus_source_used,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp()
                    },
                    'data': self.processed_prometheus_data_example,
                }
            }
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }

        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
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
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

        self.test_monitor._monitor()

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        # There must be 2 messages in the queue, the heartbeat and the
        # processed data
        self.assertEqual(2, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output_data, json.loads(body))

        # Check that the message received is actually the HB
        _, _, body = self.test_monitor.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output_hb, json.loads(body))

    @parameterized.expand([
        (False, ['prometheus'],)
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_sends_empty_dict_for_disabled_source(
            self, monitor_prometheus, disabled_sources, mock_get_data) -> None:
        # Once more sources are added this test will make more sense.
        self.test_monitor.node_config._monitor_prometheus = monitor_prometheus
        expected_output_data = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'last_source_used':
                            self.test_monitor.last_prometheus_source_used,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp()
                    },
                    'data': self.processed_prometheus_data_example,
                }
            }
        }
        for disabled_source in disabled_sources:
            expected_output_data[disabled_source] = {}
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }

        # We can get all data since that won't effect how _monitor() works
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
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
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

        self.test_monitor._monitor()

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        # There must be 2 messages in the queue, the heartbeat and the
        # processed data
        self.assertEqual(2, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output_data, json.loads(body))

        # Check that the message received is actually the HB
        _, _, body = self.test_monitor.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output_hb, json.loads(body))

    @parameterized.expand([
        (['self.test_exception'],)
    ])
    @mock.patch.object(ChainlinkNodeMonitor, "_process_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_sends_no_data_and_hb_if_data_ret_success_and_proc_fails(
            self, process_data_side_effect, mock_get_data,
            mock_process_data) -> None:
        # This test will be expanded further once more sources are added. We
        # can eventually test for when example the first source is processed
        # correctly but the second fails.
        process_data_side_effect_eval = list(map(
            eval, process_data_side_effect))
        mock_process_data.side_effect = process_data_side_effect_eval
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
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
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

        self.test_monitor._monitor()

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        # There must be 0 messages in the queue.
        self.assertEqual(0, res.method.message_count)

    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_sends_no_data_and_no_hb_on_get_data_unexpected_exception(
            self, mock_get_data) -> None:
        mock_get_data.side_effect = self.test_exception
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
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

        self.assertRaises(PANICException, self.test_monitor._monitor)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        # There must be 0 messages in the queue.
        self.assertEqual(0, res.method.message_count)

    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_raises_msg_not_delivered_exception_if_data_not_routed(
            self, mock_get_data) -> None:
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        self.test_monitor._initialise_rabbitmq()
        self.assertRaises(MessageWasNotDeliveredException,
                          self.test_monitor._monitor)

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (InvalidUrlException, InvalidUrlException('test'),),
        (DataReadingException, DataReadingException('test', 'test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(ChainlinkNodeMonitor, "_send_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_raises_error_if_raised_by_send_data(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_data) -> None:
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        mock_send_data.side_effect = exception_instance
        self.test_monitor._initialise_rabbitmq()
        self.assertRaises(exception_class, self.test_monitor._monitor)

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (MessageWasNotDeliveredException,
         MessageWasNotDeliveredException('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(ChainlinkNodeMonitor, "_send_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_does_not_send_hb_and_data_if_send_data_fails(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_data) -> None:
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        mock_send_data.side_effect = exception_instance
        self.test_monitor._initialise_rabbitmq()

        self.test_monitor.rabbitmq.queue_delete(
            self.test_queue_name)
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name,
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)

        try:
            self.test_monitor._monitor()
        except exception_class:
            pass

        # By re-declaring the queue again we can get the number of
        # messages in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True,
            exclusive=False, auto_delete=False, passive=True
        )
        # There must be no messages in the queue.
        self.assertEqual(0, res.method.message_count)

    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_raises_msg_not_del_except_if_hb_not_routed_and_sends_data(
            self, mock_get_data) -> None:
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        expected_output_data = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'last_source_used':
                            self.test_monitor.last_prometheus_source_used,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp()
                    },
                    'data': self.processed_prometheus_data_example,
                }
            }
        }
        self.test_monitor._initialise_rabbitmq()

        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)

        self.assertRaises(MessageWasNotDeliveredException,
                          self.test_monitor._monitor)

        # By re-declaring the queue again we can get the number of
        # messages in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        # There must be 1 message in the queue, the processed data
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output_data, json.loads(body))

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkNodeMonitor, "_send_heartbeat")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_raises_error_if_raised_by_send_hb_and_sends_data(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_hb) -> None:
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        expected_output_data = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'last_source_used':
                            self.test_monitor.last_prometheus_source_used,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp()
                    },
                    'data': self.processed_prometheus_data_example,
                }
            }
        }
        mock_send_hb.side_effect = exception_instance

        self.test_monitor._initialise_rabbitmq()

        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)

        self.assertRaises(exception_class, self.test_monitor._monitor)

        # By re-declaring the queue again we can get the number of
        # messages in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        # There must be 1 message in the queue, the processed data
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output_data, json.loads(body))

    @mock.patch.object(logging.Logger, "info")
    @mock.patch.object(ChainlinkNodeMonitor, "_send_heartbeat")
    @mock.patch.object(ChainlinkNodeMonitor, "_send_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_logs_data_if_all_sources_enabled_and_no_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled

        self.test_monitor._monitor()

        mock_log.assert_called_with(self.test_monitor._display_data(
            self.processed_prometheus_data_example))

    @mock.patch.object(logging.Logger, "info")
    @mock.patch.object(ChainlinkNodeMonitor, "_send_heartbeat")
    @mock.patch.object(ChainlinkNodeMonitor, "_send_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_does_not_log_if_no_retrieval_performed(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        # This needs to be updated as we increase the number of sources
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled

        self.test_monitor.node_config._monitor_prometheus = False
        processed_data = dict(ChainMap(
            *[self.processed_prometheus_data_example]))

        self.test_monitor._monitor()
        assert_not_called_with(mock_log,
                               self.test_monitor._display_data(processed_data))

    @mock.patch.object(logging.Logger, "info")
    @mock.patch.object(ChainlinkNodeMonitor, "_send_heartbeat")
    @mock.patch.object(ChainlinkNodeMonitor, "_send_data")
    @mock.patch.object(ChainlinkNodeMonitor, "_get_data")
    def test_monitor_does_not_log_if_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        # This needs to be updated as we increase the number of sources
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled_err
        processed_data = {}

        self.test_monitor._monitor()
        assert_not_called_with(mock_log,
                               self.test_monitor._display_data(processed_data))

    # TODO: When more sources are added we need to test for when some sources
    #     : are enabled and some disabled
