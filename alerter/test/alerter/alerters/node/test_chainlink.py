import copy
import datetime
import json
import logging
import unittest
from unittest import mock
from unittest.mock import call

import pika
from parameterized import parameterized

from src.alerter.alerters.node.chainlink import (
    ChainlinkNodeAlerter, GroupedChainlinkNodeAlertsMetricCode)
from src.alerter.alerts.node.chainlink import (
    ReceivedANewHeaderAlert, InvalidUrlAlert, ValidUrlAlert,
    MetricNotFoundErrorAlert, MetricFoundAlert, NoChangeInHeightAlert,
    BlockHeightUpdatedAlert, NoChangeInTotalHeadersReceivedAlert,
    HeadsInQueueIncreasedAboveThresholdAlert,
    HeadsInQueueDecreasedBelowThresholdAlert,
    MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
    MaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
    NoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
    NoOfUnconfirmedTxsDecreasedBelowThresholdAlert,
    DroppedBlockHeadersIncreasedAboveThresholdAlert,
    DroppedBlockHeadersDecreasedBelowThresholdAlert,
    TotalErroredJobRunsIncreasedAboveThresholdAlert,
    TotalErroredJobRunsDecreasedBelowThresholdAlert,
    EthBalanceIncreasedAboveThresholdAlert,
    EthBalanceDecreasedBelowThresholdAlert, EthBalanceToppedUpAlert,
    ChangeInSourceNodeAlert, GasBumpIncreasedOverNodeGasPriceLimitAlert,
    NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
    PrometheusSourceIsDownAlert, PrometheusSourceBackUpAgainAlert)
from src.alerter.factory.chainlink_node_alerting_factory import \
    ChainlinkNodeAlertingFactory
from src.configs.factory.chainlink_alerts_configs_factory import \
    ChainlinkAlertsConfigsFactory
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    CONFIG_EXCHANGE, CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    HEALTH_CHECK_EXCHANGE, ALERT_EXCHANGE, CL_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    CL_NODE_ALERT_ROUTING_KEY)
from src.utils.env import RABBIT_IP
from src.utils.exceptions import PANICException, NodeIsDownException
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit)


class TestChainlinkNodeAlerter(unittest.TestCase):

    def setUp(self) -> None:
        # Some dummy values and objects
        self.test_alerter_name = 'test_alerter'
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = datetime.timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)
        self.test_queue_size = 5
        self.test_parent_id = 'test_parent_id'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test_data_str'
        self.test_configs_routing_key = 'chains.chainlink.bsc.alerts_config'
        self.test_chainlink_node_name = 'test_chainlink_node'
        self.test_chainlink_node_id = 'test_chainlink_node_id345834t8h3r5893h8'
        self.test_went_down_at_prometheus = None
        self.test_current_height = 50000000000
        self.test_eth_blocks_in_queue = 3
        self.test_total_block_headers_received = 454545040
        self.test_total_block_headers_dropped = 4
        self.test_no_of_active_jobs = 10
        self.test_max_pending_tx_delay = 6
        self.test_process_start_time_seconds = 345474.4
        self.test_total_gas_bumps = 11
        self.test_total_gas_bumps_exceeds_limit = 13
        self.test_no_of_unconfirmed_txs = 7
        self.test_total_errored_job_runs = 15
        self.test_current_gas_price_info = {
            'percentile': 50.5,
            'price': 22.0,
        }
        self.test_eth_balance_info = {
            'address': 'address1', 'balance': 34.4, 'latest_usage': 5.0,
        }
        self.test_last_prometheus_source_used = "prometheus_source_1"
        self.test_last_monitored_prometheus = 45.666786
        self.test_went_down_at_prometheus_new = None
        self.test_current_height_new = 50000000001
        self.test_eth_blocks_in_queue_new = 4
        self.test_total_block_headers_received_new = 454545041
        self.test_total_block_headers_dropped_new = 5
        self.test_no_of_active_jobs_new = 11
        self.test_max_pending_tx_delay_new = 7
        self.test_process_start_time_seconds_new = 345476.4
        self.test_total_gas_bumps_new = 13
        self.test_total_gas_bumps_exceeds_limit_new = 14
        self.test_no_of_unconfirmed_txs_new = 8
        self.test_total_errored_job_runs_new = 16
        self.test_current_gas_price_info_new = {
            'percentile': 52.5,
            'price': 24.0,
        }
        self.test_eth_balance_info_new = {
            'address': 'address1', 'balance': 44.4, 'latest_usage': 0.0,
        }
        self.test_last_prometheus_source_used_new = "prometheus_source_2"
        self.test_last_monitored_prometheus_new = 47.666786
        self.test_exception = PANICException('test_exception', 1)
        self.test_node_is_down_exception = NodeIsDownException(
            self.test_chainlink_node_name)

        # Construct received configurations
        self.received_configurations = {
            'DEFAULT': 'testing_if_will_be_deleted'
        }
        metrics_without_time_window = [
            'head_tracker_current_head', 'head_tracker_heads_received_total',
            'eth_balance_amount', 'node_is_down'
        ]
        metrics_with_time_window = [
            'head_tracker_heads_in_queue',
            'head_tracker_num_heads_dropped_total', 'max_unconfirmed_blocks',
            'unconfirmed_transactions', 'run_status_update_total'
        ]
        severity_metrics = [
            'process_start_time_seconds',
            'tx_manager_gas_bump_exceeds_limit_total',
            'eth_balance_amount_increase'
        ]
        all_metrics = (metrics_without_time_window
                       + metrics_with_time_window
                       + severity_metrics)

        for i in range(len(all_metrics)):
            if all_metrics[i] in severity_metrics:
                self.received_configurations[str(i)] = {
                    'name': all_metrics[i],
                    'parent_id': self.test_parent_id,
                    'enabled': 'true',
                    'severity': 'WARNING'
                }
            elif all_metrics[i] in metrics_with_time_window:
                self.received_configurations[str(i)] = {
                    'name': all_metrics[i],
                    'parent_id': self.test_parent_id,
                    'enabled': 'true',
                    'critical_threshold': '7',
                    'critical_repeat': '5',
                    'critical_enabled': 'true',
                    'critical_repeat_enabled': 'true',
                    'warning_threshold': '3',
                    'warning_enabled': 'true',
                    'warning_time_window': '3',
                    'critical_time_window': '7',
                }
            else:
                self.received_configurations[str(i)] = {
                    'name': all_metrics[i],
                    'parent_id': self.test_parent_id,
                    'enabled': 'true',
                    'critical_threshold': '7',
                    'critical_repeat': '5',
                    'critical_enabled': 'true',
                    'critical_repeat_enabled': 'true',
                    'warning_threshold': '3',
                    'warning_enabled': 'true',
                }

        self.test_prom_result_data = {
            'result': {
                'meta_data': {
                    'node_name': self.test_chainlink_node_name,
                    'last_source_used': {
                        'current': self.test_last_prometheus_source_used_new,
                        'previous': self.test_last_prometheus_source_used
                    },
                    'node_id': self.test_chainlink_node_id,
                    'node_parent_id': self.test_parent_id,
                    'last_monitored': self.test_last_monitored_prometheus_new,
                },
                'data': {
                    'went_down_at': {
                        'current': self.test_went_down_at_prometheus_new,
                        'previous': self.test_went_down_at_prometheus
                    },
                    'current_height': {
                        'current': self.test_current_height_new,
                        'previous': self.test_current_height
                    },
                    'eth_blocks_in_queue': {
                        'current': self.test_eth_blocks_in_queue_new,
                        'previous': self.test_eth_blocks_in_queue
                    },
                    'total_block_headers_received': {
                        'current': self.test_total_block_headers_received_new,
                        'previous': self.test_total_block_headers_received,
                    },
                    'total_block_headers_dropped': {
                        'current': self.test_total_block_headers_dropped_new,
                        'previous': self.test_total_block_headers_dropped,
                    },
                    'no_of_active_jobs': {
                        'current': self.test_no_of_active_jobs_new,
                        'previous': self.test_no_of_active_jobs,
                    },
                    'max_pending_tx_delay': {
                        'current': self.test_max_pending_tx_delay_new,
                        'previous': self.test_max_pending_tx_delay
                    },
                    'process_start_time_seconds': {
                        'current': self.test_process_start_time_seconds_new,
                        'previous': self.test_process_start_time_seconds,
                    },
                    'total_gas_bumps': {
                        'current': self.test_total_gas_bumps_new,
                        'previous': self.test_total_gas_bumps
                    },
                    'total_gas_bumps_exceeds_limit': {
                        'current': self.test_total_gas_bumps_exceeds_limit_new,
                        'previous': self.test_total_gas_bumps_exceeds_limit,
                    },
                    'no_of_unconfirmed_txs': {
                        'current': self.test_no_of_unconfirmed_txs_new,
                        'previous': self.test_no_of_unconfirmed_txs,
                    },
                    'total_errored_job_runs': {
                        'current': self.test_total_errored_job_runs_new,
                        'previous': self.test_total_errored_job_runs,
                    },
                    'current_gas_price_info': {
                        'current': self.test_current_gas_price_info_new,
                        'previous': self.test_current_gas_price_info
                    },
                    'eth_balance_info': {
                        'current': self.test_eth_balance_info_new,
                        'previous': self.test_eth_balance_info
                    },
                },
            }
        }

        self.test_prom_non_down_error = {
            'error': {
                'meta_data': {
                    'node_name': self.test_chainlink_node_name,
                    'last_source_used': {
                        'current': self.test_last_prometheus_source_used_new,
                        'previous': self.test_last_prometheus_source_used,
                    },
                    'node_id': self.test_chainlink_node_id,
                    'node_parent_id': self.test_parent_id,
                    'time': self.test_last_monitored_prometheus_new
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }

        self.transformed_data_example_result = {
            'prometheus': copy.deepcopy(self.test_prom_result_data),
            # TODO: Add more data sources once they are enabled
        }
        self.transformed_data_example_not_all_sources_down = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used': {
                            'current':
                                self.test_last_prometheus_source_used_new,
                            'previous': self.test_last_prometheus_source_used,
                        },
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            # TODO: Add more data sources once they are enabled
        }
        self.transformed_data_example_all_sources_down = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used': {
                            'current':
                                self.test_last_prometheus_source_used_new,
                            'previous': self.test_last_prometheus_source_used,
                        },
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': {
                            'current': self.test_last_monitored_prometheus_new,
                            'previous': None
                        }
                    }
                }
            },
            # TODO: Add more data sources once they are enabled
        }

        # Test object
        self.test_configs_factory = ChainlinkAlertsConfigsFactory()
        self.test_alerting_factory = ChainlinkNodeAlertingFactory(
            self.dummy_logger)
        self.test_cl_node_alerter = ChainlinkNodeAlerter(
            self.test_alerter_name, self.dummy_logger, self.rabbitmq,
            self.test_configs_factory, self.test_queue_size)

    def tearDown(self) -> None:
        connect_to_rabbit(self.test_cl_node_alerter.rabbitmq)
        delete_queue_if_exists(self.test_cl_node_alerter.rabbitmq,
                               self.test_queue_name)
        delete_queue_if_exists(self.test_cl_node_alerter.rabbitmq,
                               CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_cl_node_alerter.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_cl_node_alerter.rabbitmq,
                                  ALERT_EXCHANGE)
        delete_exchange_if_exists(self.test_cl_node_alerter.rabbitmq,
                                  CONFIG_EXCHANGE)
        disconnect_from_rabbit(self.test_cl_node_alerter.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_configs_factory = None
        self.alerting_factory = None
        self.test_cl_node_alerter = None
        self.test_exception = None
        self.test_node_is_down_exception = None

    def test_alerts_configs_factory_returns_alerts_configs_factory(
            self) -> None:
        self.test_cl_node_alerter._alerts_configs_factory = \
            self.test_configs_factory
        self.assertEqual(self.test_configs_factory,
                         self.test_cl_node_alerter.alerts_configs_factory)

    def test_alerting_factory_returns_alerting_factory(self) -> None:
        self.test_cl_node_alerter._alerting_factory = self.test_alerting_factory
        self.assertEqual(self.test_alerting_factory,
                         self.test_cl_node_alerter.alerting_factory)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already
        # established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.queue_delete(CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        self.test_cl_node_alerter._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_cl_node_alerter.rabbitmq.is_connected)
        self.assertTrue(self.test_cl_node_alerter.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_cl_node_alerter.rabbitmq.channel._delivery_confirmation)

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_cl_node_alerter.rabbitmq.exchange_declare(
            HEALTH_CHECK_EXCHANGE, passive=True)

        # Check whether the consuming exchanges and queues have been created
        # by sending messages to them. Since at this point these queues have
        # only the bindings from _initialise_rabbit, it must be that if no
        # exception is raised, then all queues and exchanges have been created
        # and binded correctly.
        self.test_cl_node_alerter.rabbitmq.basic_publish_confirm(
            exchange=ALERT_EXCHANGE,
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_cl_node_alerter.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE, routing_key=self.test_configs_routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

    @parameterized.expand([
        (CL_NODE_TRANSFORMED_DATA_ROUTING_KEY, 'mock_proc_trans',),
        ('chains.chainlink.bsc.alerts_config', 'mock_proc_confs',),
        ('uncrecognized_routing_key', 'mock_basic_ack',),
    ])
    @mock.patch.object(ChainlinkNodeAlerter, "_process_transformed_data")
    @mock.patch.object(ChainlinkNodeAlerter, "_process_configs")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_calls_the_correct_sub_function(
            self, routing_key, called_mock, mock_basic_ack, mock_proc_confs,
            mock_proc_trans) -> None:
        """
        In this test we will check that if a configs routing key is received,
        the process_data function calls the process_configs fn, if a
        transformed data routing key is received, the process_data function
        calls the process_transformed_data fn, and if the routing key is
        unrecognized, the process_data function calls the ack method.
        """
        mock_basic_ack.return_value = None
        mock_proc_confs.return_value = None
        mock_proc_trans.return_value = None

        self.test_cl_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_cl_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=routing_key)
        body = json.dumps(self.test_data_str)
        properties = pika.spec.BasicProperties()
        self.test_cl_node_alerter._process_data(blocking_channel, method,
                                                properties, body)

        eval(called_mock).assert_called_once()

    """
    In the majority of the tests below we will perform mocking. The tests for
    config processing and alerting were performed in seperate test files which
    targeted the factory classes.
    """

    @mock.patch.object(ChainlinkAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(ChainlinkAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "remove_chain_alerting_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_confs_adds_new_conf_and_clears_alerting_state_if_new_confs(
            self, mock_ack, mock_remove_alerting_state,
            mock_add_new_conf, mock_get_parent_id) -> None:
        """
        In this test we will check that if new alert configs are received for
        a new chain, the new config is added and the alerting state is cleared.
        """
        mock_ack.return_value = None
        mock_get_parent_id.return_value = self.test_parent_id

        self.test_cl_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_cl_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps(self.received_configurations)
        properties = pika.spec.BasicProperties()
        self.test_cl_node_alerter._process_configs(blocking_channel, method,
                                                   properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_add_new_conf.assert_called_once_with(chain,
                                                  self.received_configurations)
        mock_get_parent_id.assert_called_once_with(chain)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(ChainlinkAlertsConfigsFactory, "remove_config")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "remove_chain_alerting_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_confs_removes_confs_and_alerting_state_if_conf_deleted(
            self, mock_ack, mock_remove_alerting_state, mock_remove_config,
            mock_get_parent_id) -> None:
        """
        In this test we will check that if alert configurations are deleted for
        a chain, the configs are removed and the alerting state is reset. Here
        we will assume that the configurations exist
        """
        mock_ack.return_value = None
        mock_get_parent_id.return_value = self.test_parent_id

        self.test_cl_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_cl_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        self.test_cl_node_alerter._process_configs(blocking_channel, method,
                                                   properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_get_parent_id.assert_called_once_with(chain)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_remove_config.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(ChainlinkAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(ChainlinkAlertsConfigsFactory, "remove_config")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "remove_chain_alerting_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_confs_does_nothing_if_received_new_empty_configs(
            self, mock_ack, mock_remove_alerting_state, mock_remove_conf,
            mock_get_parent_id, mock_add_new_conf) -> None:
        """
        In this test we will check that if empty alert configurations are
        received for a new chain, the function does nothing. We will mock that
        the config does not exist by making get_parent_id return None.
        """
        mock_ack.return_value = None
        mock_get_parent_id.return_value = None

        self.test_cl_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_cl_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        self.test_cl_node_alerter._process_configs(blocking_channel, method,
                                                   properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        mock_remove_alerting_state.assert_not_called()
        mock_remove_conf.assert_not_called()
        mock_add_new_conf.assert_not_called()
        mock_get_parent_id.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_acknowledges_received_data(
            self, mock_ack, mock_get_parent_id) -> None:
        """
        In this test we will check that if processing fails, the data is always
        acknowledged. The case for when processing does not fail was performed
        in each test above by checking that mock_ack has been called once.
        """
        mock_ack.return_value = None
        mock_get_parent_id.side_effect = Exception('test')

        self.test_cl_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_cl_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps(self.received_configurations)
        properties = pika.spec.BasicProperties()

        # Secondly test for when processing fails successful
        self.test_cl_node_alerter._process_configs(blocking_channel, method,
                                                   properties, body)
        mock_ack.assert_called_once()

    def test_place_latest_data_on_queue_places_data_on_queue_correctly(
            self) -> None:
        test_data = ['data_1', 'data_2']

        self.assertTrue(self.test_cl_node_alerter.publishing_queue.empty())

        expected_data_1 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': CL_NODE_ALERT_ROUTING_KEY,
            'data': 'data_1',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_2 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': CL_NODE_ALERT_ROUTING_KEY,
            'data': 'data_2',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        self.test_cl_node_alerter._place_latest_data_on_queue(test_data)
        self.assertEqual(2,
                         self.test_cl_node_alerter.publishing_queue.qsize())
        self.assertEqual(expected_data_1,
                         self.test_cl_node_alerter.publishing_queue.get())
        self.assertEqual(expected_data_2,
                         self.test_cl_node_alerter.publishing_queue.get())

    def test_place_latest_data_on_queue_removes_old_data_if_full_then_places(
            self) -> None:
        # First fill the queue with the same data
        test_data_1 = ['data_1']
        for i in range(self.test_queue_size):
            self.test_cl_node_alerter._place_latest_data_on_queue(test_data_1)

        # Now fill the queue with the second piece of data, and confirm that
        # now only the second piece of data prevails.
        test_data_2 = ['data_2']
        for i in range(self.test_queue_size):
            self.test_cl_node_alerter._place_latest_data_on_queue(test_data_2)

        for i in range(self.test_queue_size):
            expected_data = {
                'exchange': ALERT_EXCHANGE,
                'routing_key': CL_NODE_ALERT_ROUTING_KEY,
                'data': 'data_2',
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True
            }
            self.assertEqual(expected_data,
                             self.test_cl_node_alerter.publishing_queue.get())

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_time_window_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_prometheus_result_does_nothing_if_config_not_received(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_win_alert, mock_no_change_alert,
            mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if prometheus data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_result(
            self.test_prom_result_data, data_for_alerting)

        mock_reverse.assert_not_called()
        mock_cond_alert.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_thresh_win_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()
        mock_error_alert.assert_not_called()

    @mock.patch.object(ChainlinkNodeAlertingFactory, "create_alerting_state")
    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_time_window_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_prometheus_result_does_not_classify_if_current_is_None(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_win_alert, mock_no_change_alert,
            mock_error_alert, mock_create_alerting_state) -> None:
        """
        In this test we will check that if the current metric value is None, no
        alert classification is made for the metrics. The only alerts which are
        classified are the ones which try to detect error alerts (i.e. not
        associated with any data metric). Note that for easier testing we will
        assume that all current metric values are None. Here we will also test
        that create_alert_state is called once a configuration is found.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        # Set each current metric value to None
        data = self.test_prom_result_data['result']['data']
        for metric, current_previous in data.items():
            current_previous['current'] = None

        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_result(
            self.test_prom_result_data, data_for_alerting)

        mock_reverse.assert_not_called()
        mock_cond_alert.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_thresh_win_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            5009, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, "",
            "Prometheus url is now valid!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), None)
        call_2 = call(
            5003, MetricNotFoundErrorAlert, MetricFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.MetricNotFound.value, "",
            "All metrics found!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        mock_create_alerting_state.assert_called_once_with(
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_configs_factory.configs[chain])

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_time_window_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_prometheus_result_does_not_classify_if_metrics_disabled(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_win_alert, mock_no_change_alert,
            mock_error_alert) -> None:
        """
        In this test we will check that if a metric is disabled from the config,
        there will be no alert classification for the associated alerts. Note
        that for easier testing we will set every metric to be disabled. Again,
        the only classification which would happen is for the error alerts.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']

        # Set each metric to disabled
        for index, config in self.received_configurations.items():
            config['enabled'] = 'False'
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_result(
            self.test_prom_result_data, data_for_alerting)

        mock_reverse.assert_not_called()
        mock_cond_alert.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_thresh_win_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            5009, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, "",
            "Prometheus url is now valid!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), None)
        call_2 = call(
            5003, MetricNotFoundErrorAlert, MetricFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.MetricNotFound.value, "",
            "All metrics found!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_time_window_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_prometheus_result_classifies_correctly_if_data_valid(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_win_alert, mock_no_change_alert,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_prometheus_result function. Note that
        the actual logic for these classification functions was tested in the
        alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_result(
            self.test_prom_result_data, data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            5009, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, "",
            "Prometheus url is now valid!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), None)
        call_2 = call(
            5003, MetricNotFoundErrorAlert, MetricFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.MetricNotFound.value, "",
            "All metrics found!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        calls = mock_no_change_alert.call_args_list
        self.assertEqual(2, mock_no_change_alert.call_count)
        call_1 = call(
            self.test_current_height_new, self.test_current_height,
            configs.head_tracker_current_head, NoChangeInHeightAlert,
            BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        call_2 = call(
            self.test_total_block_headers_received_new,
            self.test_total_block_headers_received,
            configs.head_tracker_heads_received_total,
            NoChangeInTotalHeadersReceivedAlert, ReceivedANewHeaderAlert,
            data_for_alerting, self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInTotalHeadersReceived
                .value, self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        calls = mock_thresh_win_alert.call_args_list
        self.assertEqual(3, mock_thresh_win_alert.call_count)
        call_1 = call(
            self.test_eth_blocks_in_queue_new,
            configs.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        call_2 = call(
            self.test_max_pending_tx_delay_new, configs.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        call_3 = call(
            self.test_no_of_unconfirmed_txs_new,
            configs.unconfirmed_transactions,
            NoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
            NoOfUnconfirmedTxsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoOfUnconfirmedTxsThreshold
                .value, self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

        calls = mock_thresh_per_alert.call_args_list
        self.assertEqual(2, mock_thresh_per_alert.call_count)
        call_1 = call(
            self.test_total_block_headers_dropped_new,
            self.test_total_block_headers_dropped,
            configs.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        call_2 = call(
            self.test_total_errored_job_runs_new,
            self.test_total_errored_job_runs, configs.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        calls = mock_reverse.call_args_list
        self.assertEqual(1, mock_reverse.call_count)
        call_1 = call(
            self.test_eth_balance_info_new['balance'],
            configs.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        self.assertTrue(call_1 in calls)

        calls = mock_cond_alert.call_args_list
        self.assertEqual(3, mock_cond_alert.call_count)
        call_1 = call(
            EthBalanceToppedUpAlert,
            self.test_cl_node_alerter._greater_than_condition_function,
            [self.test_eth_balance_info_new['balance'],
             self.test_eth_balance_info['balance']], [
                self.test_chainlink_node_name,
                self.test_eth_balance_info_new['balance'],
                self.test_eth_balance_info_new[
                    'balance'] - self.test_eth_balance_info['balance'],
                configs.eth_balance_amount_increase['severity'],
                self.test_last_monitored_prometheus_new, self.test_parent_id,
                self.test_chainlink_node_id], data_for_alerting)
        call_2 = call(
            ChangeInSourceNodeAlert,
            self.test_cl_node_alerter._not_equal_condition_function,
            [self.test_process_start_time_seconds_new,
             self.test_process_start_time_seconds], [
                self.test_chainlink_node_name,
                self.test_last_prometheus_source_used_new,
                configs.process_start_time_seconds['severity'],
                self.test_last_monitored_prometheus_new, self.test_parent_id,
                self.test_chainlink_node_id], data_for_alerting)
        call_3 = call(
            GasBumpIncreasedOverNodeGasPriceLimitAlert,
            self.test_cl_node_alerter._greater_than_condition_function,
            [self.test_total_gas_bumps_exceeds_limit_new,
             self.test_total_gas_bumps_exceeds_limit], [
                self.test_chainlink_node_name,
                configs.tx_manager_gas_bump_exceeds_limit_total['severity'],
                self.test_last_monitored_prometheus_new, self.test_parent_id,
                self.test_chainlink_node_id], data_for_alerting)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    def test_process_prometheus_error_does_nothing_if_config_not_received(
            self, mock_cond_alert, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if prometheus data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_error(
            self.test_prom_non_down_error, data_for_alerting)

        mock_cond_alert.assert_not_called()
        mock_error_alert.assert_not_called()

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory, "create_alerting_state")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    def test_proc_prom_err_does_not_classify_change_in_source_current_is_None(
            self, mock_cond_alert, mock_create_alerting_state,
            mock_error) -> None:
        """
        In this test we will check that if the current value for
        last_source_used is None, the ChangeInSource alert is not classified.
        Here we will also test that create_alert_state is called once a
        configuration is found.
        """
        mock_error.return_value = None

        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        # Set last_source_used current to None
        self.test_prom_non_down_error['error']['meta_data'][
            'last_source_used']['current'] = None

        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_error(
            self.test_prom_non_down_error, data_for_alerting)

        mock_cond_alert.assert_not_called()

        mock_create_alerting_state.assert_called_once_with(
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_configs_factory.configs[chain])

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    def test_process_prom_error_does_not_classify_change_in_source_if_disabled(
            self, mock_cond_alert, mock_error_alert) -> None:
        """
        In this test we will check that if a process_start_seconds is disabled
        from the config, there will be no alert classification for the
        associated alert.
        """
        mock_error_alert.return_value = None

        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']

        # Set each metric to disabled
        for index, config in self.received_configurations.items():
            config['enabled'] = 'False'
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_error(
            self.test_prom_non_down_error, data_for_alerting)

        mock_cond_alert.assert_not_called()

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_conditional_alert")
    def test_process_prometheus_error_classifies_correctly_if_data_valid(
            self, mock_cond_alert, mock_error_alert) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_prometheus_error function. Note that
        the actual logic for these classification functions was tested in the
        alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_cl_node_alerter._process_prometheus_error(
            self.test_prom_non_down_error, data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        error_msg = self.test_prom_non_down_error['error']['message']
        error_code = self.test_prom_non_down_error['error']['code']
        call_1 = call(
            5009, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, error_msg,
            "Prometheus url is now valid!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), error_code)
        call_2 = call(
            5003, MetricNotFoundErrorAlert, MetricFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new,
            GroupedChainlinkNodeAlertsMetricCode.MetricNotFound.value,
            error_msg, "All metrics found!. Last source used {}.".format(
                self.test_last_prometheus_source_used_new), error_code)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        calls = mock_cond_alert.call_args_list
        self.assertEqual(1, mock_cond_alert.call_count)
        call_1 = call(
            ChangeInSourceNodeAlert,
            self.test_cl_node_alerter._not_equal_condition_function,
            [self.test_last_prometheus_source_used_new,
             self.test_last_prometheus_source_used], [
                self.test_chainlink_node_name,
                self.test_last_prometheus_source_used_new,
                configs.process_start_time_seconds['severity'],
                self.test_last_monitored_prometheus_new, self.test_parent_id,
                self.test_chainlink_node_id], data_for_alerting)
        self.assertTrue(call_1 in calls)

    @parameterized.expand([
        (10, 20, False,),
        (10, 10, False,),
        (20, 10, True,),
    ])
    def test_greater_than_condition_function_returns_correctly(
            self, current, previous, expected_result) -> None:
        actual_result = \
            self.test_cl_node_alerter._greater_than_condition_function(
                current, previous)
        self.assertEqual(expected_result, actual_result)

    @parameterized.expand([
        (10, 20, True,),
        (10, 10, False,),
        (20, 10, True,),
    ])
    def test_not_equal_condition_function_returns_correctly(
            self, current, previous, expected_result) -> None:
        actual_result = \
            self.test_cl_node_alerter._not_equal_condition_function(
                current, previous)
        self.assertEqual(expected_result, actual_result)

    @parameterized.expand([
        (None, 20, False,),
        ('result', 20, False,),
        ('result', None, False,),
        (None, None, False,),
        ('error', 10, False,),
        ('error', None, False,),
        ('error', 5015, True,),
    ])
    def test_prometheus_is_down_condition_function_returns_correctly(
            self, index_key, code, expected_result) -> None:
        actual_result = \
            self.test_cl_node_alerter._prometheus_is_down_condition_function(
                index_key, code)
        self.assertEqual(expected_result, actual_result)

    @parameterized.expand([
        ("self.transformed_data_example_result",),
        ("self.transformed_data_example_all_sources_down",),
        ("self.transformed_data_example_not_all_sources_down",),
    ])
    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_source_downtime_alert")
    def test_process_downtime_does_nothing_if_config_not_received(
            self, transformed_data, mock_source_downtime,
            mock_downtime) -> None:
        """
        In this test we will check that no classification function is called
        if transformed data has been received for a node who's associated alerts
        configuration is not received yet. We will perform this test for
        multiple transformed_data types.
        """
        data_for_alerting = []
        self.test_cl_node_alerter._process_downtime(eval(transformed_data),
                                                    data_for_alerting)

        mock_source_downtime.assert_not_called()
        mock_downtime.assert_not_called()

    @parameterized.expand([
        ("self.transformed_data_example_result",),
        ("self.transformed_data_example_all_sources_down",),
        ("self.transformed_data_example_not_all_sources_down",),
    ])
    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_source_downtime_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory, "create_alerting_state")
    def test_process_downtime_does_not_classify_if_downtime_disabled(
            self, transformed_data, mock_create_alerting_state,
            mock_source_downtime, mock_downtime) -> None:
        """
        In this test we will check that no alert classification is done if
        downtime is disabled from the configs. Here we will also test that
        create_alert_state is called once a configuration is found.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        for index, config in self.received_configurations.items():
            config['enabled'] = 'False'
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_cl_node_alerter._process_downtime(eval(transformed_data),
                                                    data_for_alerting)

        mock_source_downtime.assert_not_called()
        mock_downtime.assert_not_called()
        mock_create_alerting_state.assert_called_once_with(
            self.test_parent_id, self.test_chainlink_node_id,
            self.test_configs_factory.configs[chain])

    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_source_downtime_alert")
    def test_process_downtime_classifies_downtime_alert_if_all_sources_down(
            self, mock_source_downtime, mock_downtime) -> None:
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_cl_node_alerter._process_downtime(
            self.transformed_data_example_all_sources_down, data_for_alerting)

        mock_source_downtime.assert_not_called()
        mock_downtime.assert_called_once_with(
            self.test_last_monitored_prometheus_new, configs.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)

    @parameterized.expand([
        ("self.transformed_data_example_result", "result", None),
        ("self.transformed_data_example_not_all_sources_down", "error", 1),
    ])
    @mock.patch.object(ChainlinkNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(ChainlinkNodeAlertingFactory,
                       "classify_source_downtime_alert")
    def test_process_downtime_classifies_correctly_if_not_all_sources_down(
            self, transformed_data, response_index_key, error_code,
            mock_source_downtime, mock_downtime) -> None:
        """
        In this test we will check that if not all sources are down, the
        process_downtime function attempts to classify for a backup again alert
        and prometheus downtime alert.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_cl_node_alerter._process_downtime(
            eval(transformed_data), data_for_alerting)

        mock_downtime.assert_called_once_with(
            None, configs.node_is_down, NodeWentDownAtAlert, NodeStillDownAlert,
            NodeBackUpAgainAlert, data_for_alerting, self.test_parent_id,
            self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_chainlink_node_name,
            self.test_last_monitored_prometheus_new)
        mock_source_downtime.assert_called_once_with(
            PrometheusSourceIsDownAlert,
            self.test_cl_node_alerter._prometheus_is_down_condition_function,
            [response_index_key, error_code], [
                self.test_chainlink_node_name, "WARNING",
                self.test_last_monitored_prometheus_new, self.test_parent_id,
                self.test_chainlink_node_id
            ], data_for_alerting, self.test_parent_id,
            self.test_chainlink_node_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value,
            PrometheusSourceBackUpAgainAlert, [
                self.test_chainlink_node_name, "INFO",
                self.test_last_monitored_prometheus_new, self.test_parent_id,
                self.test_chainlink_node_id
            ]
        )
