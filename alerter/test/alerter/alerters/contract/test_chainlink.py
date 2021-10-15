import copy
import datetime
import json
import logging
import unittest
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerters.contract.chainlink import ChainlinkContractAlerter
from src.alerter.alerts.contract.chainlink import (
    PriceFeedObservedAgain,
    PriceFeedObservationsIncreasedAboveThreshold,
    PriceFeedDeviationInreasedAboveThreshold,
    PriceFeedDeviationDecreasedBelowThreshold,
    ConsensusFailure, ErrorContractsNotRetrieved,
    ContractsNowRetrieved, ErrorNoSyncedDataSources, SyncedDataSourcesFound)
from src.alerter.factory.chainlink_contract_alerting_factory import \
    ChainlinkContractAlertingFactory
from src.alerter.grouped_alerts_metric_code.contract.chainlink_contract_metric_code \
    import GroupedChainlinkContractAlertsMetricCode as MetricCode
from src.configs.factory.node.chainlink_alerts import \
    ChainlinkContractAlertsConfigsFactory
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CL_CONTRACT_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE,
    CONFIG_EXCHANGE, CL_CONTRACT_ALERT_ROUTING_KEY,
    CL_ALERTS_CONFIGS_ROUTING_KEY)
from src.utils.env import RABBIT_IP
from src.utils.exceptions import PANICException
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit)
from src.utils.types import str_to_bool


class TestChainlinkContractAlerter(unittest.TestCase):
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
        self.test_node_name_1 = 'test_cl_node_1'
        self.test_node_name_2 = 'test_cl_node_2'
        self.test_node_id_1 = 'test_cl_node_id345834t8h3r5893h8_1'
        self.test_node_id_2 = 'test_cl_node_id345834t8h3r5893h8_2'
        self.test_contract_proxy_address_1 = \
            '0x567cC5F1A7c2B3240cb76E2aA1BF0F1bE7035897'
        self.test_contract_proxy_address_2 = \
            '0x3FcbE808D1f1A46764AB839B722Beb16c48A80cB'

        # Some test metrics
        self.test_went_down_at = None
        self.test_last_monitored = datetime.datetime(2012, 1, 1).timestamp()
        self.test_exception = PANICException('test_exception', 1)

        # Construct received configurations
        self.received_configurations = {
            'DEFAULT': 'testing_if_will_be_deleted'
        }
        severity_metrics = [
            'consensus_failure'
        ]
        metrics_without_time_window = [
            'price_feed_not_observed',
            'price_feed_deviation',
            'error_retrieving_chainlink_contract_data'
        ]
        all_metrics = metrics_without_time_window + severity_metrics

        for i in range(len(all_metrics)):
            if all_metrics[i] in severity_metrics:
                self.received_configurations[str(i)] = {
                    'name': all_metrics[i],
                    'parent_id': self.test_parent_id,
                    'enabled': 'true',
                    'severity': 'WARNING'
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

        self.test_aggregator_address_1 = 'test_aggregator_address_1'
        self.test_aggregator_address_2 = 'test_aggregator_address_2'
        self.test_latest_round_1 = 40
        self.test_latest_answer_1 = 34534534563464
        self.test_latest_timestamp_1 = self.test_last_monitored
        self.test_answered_in_round_1 = 40
        self.test_withdrawable_payment_1 = 3458347534235
        self.test_owed_payment_1 = 34
        self.test_missed_observations_1 = 11  # Calculate using historical rnds

        self.test_latest_round_2 = 50
        self.test_latest_answer_2 = 3453453456
        self.test_latest_timestamp_2 = self.test_last_monitored + 30
        self.test_answered_in_round_2 = 40
        self.test_withdrawable_payment_2 = 3458347
        self.test_owed_payment_2 = 35
        self.test_missed_observations_2 = 21  # Calculate using historical rnds

        # Historical rounds data
        self.test_historical_rounds_1 = [
            {
                'roundId': 38,
                'roundAnswer': 10,
                'roundTimestamp': self.test_last_monitored + 10,
                'answeredInRound': 38,
                'deviation': 50.0,
                'nodeSubmission': 5
            },
            {
                'roundId': 39,
                'roundAnswer': 5,
                'roundTimestamp': self.test_last_monitored + 20,
                'answeredInRound': 39,
                'deviation': 100.0,
                'nodeSubmission': 10
            }
        ]
        self.test_historical_rounds_2 = [
            {
                'roundId': 48,
                'roundAnswer': 10,
                'roundTimestamp': self.test_last_monitored + 10,
                'answeredInRound': 48,
                'nodeSubmission': 5,
                'noOfObservations': 4,
                'deviation': 50.0,
                'noOfTransmitters': 14,
            },
            {
                'roundId': 49,
                'roundAnswer': 5,
                'roundTimestamp': self.test_last_monitored + 20,
                'answeredInRound': 49,
                'nodeSubmission': 10,
                'noOfObservations': 5,
                'deviation': 75.0,
                'noOfTransmitters': 16,
            }
        ]

        meta_data_for_alerting_result_v4 = {
            'node_name': self.test_node_name_1,
            'node_id': self.test_node_id_1,
            'node_parent_id': self.test_parent_id,
            'last_monitored': self.test_last_monitored
        }

        meta_data_for_alerting_result_v3 = {
            'node_name': self.test_node_name_2,
            'node_id': self.test_node_id_2,
            'node_parent_id': self.test_parent_id,
            'last_monitored': self.test_latest_timestamp_2
        }

        self.test_data_for_alerting_result_v4 = {
            'result': {
                'meta_data': meta_data_for_alerting_result_v4,
                'data': {
                    self.test_contract_proxy_address_1: {
                        'latestRound': {
                            'current': self.test_latest_round_1,
                            'previous': None,
                        },
                        'latestAnswer': {
                            'current': self.test_latest_answer_1,
                            'previous': None,
                        },
                        'latestTimestamp': {
                            'current': self.test_latest_timestamp_1,
                            'previous': None,
                        },
                        'answeredInRound': {
                            'current': self.test_answered_in_round_1,
                            'previous': None,
                        },
                        'owedPayment': {
                            'current': self.test_owed_payment_1,
                            'previous': None,
                        },
                        'historicalRounds': {
                            'current':
                                self.test_historical_rounds_1,
                            'previous': [],
                        },
                        'lastRoundObserved': {
                            'current': 29,
                            'previous': None
                        },
                        'contractVersion': 4,
                        'aggregatorAddress': self.test_aggregator_address_1,
                    }
                }
            }
        }

        self.test_data_for_alerting_result_v3 = {
            'result': {
                'meta_data': meta_data_for_alerting_result_v3,
                'data': {
                    self.test_contract_proxy_address_2: {
                        'latestRound': {
                            'current': self.test_latest_round_2,
                            'previous': None,
                        },
                        'latestAnswer': {
                            'current': self.test_latest_answer_2,
                            'previous': None,
                        },
                        'latestTimestamp': {
                            'current': self.test_latest_timestamp_2,
                            'previous': None,
                        },
                        'answeredInRound': {
                            'current': self.test_answered_in_round_2,
                            'previous': None,
                        },
                        'owedPayment': {
                            'current': self.test_owed_payment_2,
                            'previous': None,
                        },
                        'historicalRounds': {
                            'current':
                                self.test_historical_rounds_2,
                            'previous': [],
                        },
                        'lastRoundObserved': {
                            'current': 29,
                            'previous': None
                        },
                        'contractVersion': 3,
                        'aggregatorAddress': self.test_aggregator_address_2,
                    }
                }
            }
        }

        self.test_node_down_error = {
            'meta_data': {
                'node_name': self.test_node_name_1,
                'node_id': self.test_node_id_1,
                'node_parent_id': self.test_parent_id,
                'time': self.test_last_monitored
            },
            'message': self.test_exception.message,
            'code': self.test_exception.code,
        }

        # Test object
        self.test_configs_factory = ChainlinkContractAlertsConfigsFactory()
        self.test_alerting_factory = ChainlinkContractAlertingFactory(
            self.dummy_logger)
        self.test_contract_alerter = ChainlinkContractAlerter(
            self.test_alerter_name, self.dummy_logger,
            self.rabbitmq, self.test_configs_factory,
            self.test_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_contract_alerter.rabbitmq)
        delete_queue_if_exists(self.test_contract_alerter.rabbitmq,
                               self.test_queue_name)
        delete_queue_if_exists(self.test_contract_alerter.rabbitmq,
                               CL_CONTRACT_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_contract_alerter.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_contract_alerter.rabbitmq,
                                  ALERT_EXCHANGE)
        delete_exchange_if_exists(self.test_contract_alerter.rabbitmq,
                                  CONFIG_EXCHANGE)
        disconnect_from_rabbit(self.test_contract_alerter.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_configs_factory = None
        self.alerting_factory = None
        self.test_contract_alerter = None
        self.test_exception = None
        self.test_node_is_down_exception = None

    def test_alerts_configs_factory_returns_alerts_configs_factory(
            self) -> None:
        self.test_contract_alerter._alerts_configs_factory = \
            self.test_configs_factory
        self.assertEqual(self.test_configs_factory,
                         self.test_contract_alerter.alerts_configs_factory)

    def test_alerting_factory_returns_alerting_factory(self) -> None:
        self.test_contract_alerter._alerting_factory = \
            self.test_alerting_factory
        self.assertEqual(self.test_alerting_factory,
                         self.test_contract_alerter.alerting_factory)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already
        # established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.queue_delete(
            CL_CONTRACT_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        self.test_contract_alerter._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_contract_alerter.rabbitmq.is_connected)
        self.assertTrue(self.test_contract_alerter.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_contract_alerter.rabbitmq.channel._delivery_confirmation)

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_contract_alerter.rabbitmq.exchange_declare(
            HEALTH_CHECK_EXCHANGE, passive=True)

        # Check whether the consuming exchanges and queues have been created
        # by sending messages to them. Since at this point these queues have
        # only the bindings from _initialise_rabbit, it must be that if no
        # exception is raised, then all queues and exchanges have been created
        # and binded correctly.
        self.test_contract_alerter.rabbitmq.basic_publish_confirm(
            exchange=ALERT_EXCHANGE,
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_contract_alerter.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE, routing_key=self.test_configs_routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

    @parameterized.expand([
        (CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY, 'mock_proc_trans',),
        ('chains.chainlink.bsc.alerts_config', 'mock_proc_confs',),
        ('unrecognized_routing_key', 'mock_basic_ack',),
    ])
    @mock.patch.object(ChainlinkContractAlerter, "_process_transformed_data")
    @mock.patch.object(ChainlinkContractAlerter, "_process_configs")
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

        self.test_contract_alerter.rabbitmq.connect()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=routing_key)
        body = json.dumps(self.test_data_str)
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_data(blocking_channel, method,
                                                 properties, body)
        eval(called_mock).assert_called_once()

    """
    In the majority of the tests below we will perform mocking. The tests for
    config processing and alerting were performed in separate test files which
    targeted the factory classes.
    """
    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(ChainlinkContractAlertingFactory,
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

        self.test_contract_alerter.rabbitmq.connect()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps(self.received_configurations)
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_configs(blocking_channel, method,
                                                    properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_add_new_conf.assert_called_once_with(chain,
                                                  self.received_configurations)
        mock_get_parent_id.assert_called_once_with(chain)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "remove_config")
    @mock.patch.object(ChainlinkContractAlertingFactory,
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

        self.test_contract_alerter.rabbitmq.connect()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_configs(blocking_channel, method,
                                                    properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_get_parent_id.assert_called_once_with(chain)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_remove_config.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "remove_config")
    @mock.patch.object(ChainlinkContractAlertingFactory,
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

        self.test_contract_alerter.rabbitmq.connect()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_configs(blocking_channel, method,
                                                    properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        mock_remove_alerting_state.assert_not_called()
        mock_remove_conf.assert_not_called()
        mock_add_new_conf.assert_not_called()
        mock_get_parent_id.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkContractAlertsConfigsFactory, "get_parent_id")
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

        self.test_contract_alerter.rabbitmq.connect()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps(self.received_configurations)
        properties = pika.spec.BasicProperties()

        # Secondly test for when processing fails successful
        self.test_contract_alerter._process_configs(blocking_channel, method,
                                                    properties, body)
        mock_ack.assert_called_once()

    def test_place_latest_data_on_queue_places_data_on_queue_correctly(
            self) -> None:
        test_data = ['data_1', 'data_2']

        self.assertTrue(self.test_contract_alerter.publishing_queue.empty())

        expected_data_1 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': CL_CONTRACT_ALERT_ROUTING_KEY,
            'data': 'data_1',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_2 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': CL_CONTRACT_ALERT_ROUTING_KEY,
            'data': 'data_2',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        self.test_contract_alerter._place_latest_data_on_queue(test_data)
        self.assertEqual(2,
                         self.test_contract_alerter.publishing_queue.qsize())
        self.assertEqual(expected_data_1,
                         self.test_contract_alerter.publishing_queue.get())
        self.assertEqual(expected_data_2,
                         self.test_contract_alerter.publishing_queue.get())

    def test_place_latest_data_on_queue_removes_old_data_if_full_then_places(
            self) -> None:
        # First fill the queue with the same data
        test_data_1 = ['data_1']
        for i in range(self.test_queue_size):
            self.test_contract_alerter._place_latest_data_on_queue(test_data_1)

        # Now fill the queue with the second piece of data, and confirm that
        # now only the second piece of data prevails.
        test_data_2 = ['data_2']
        for i in range(self.test_queue_size):
            self.test_contract_alerter._place_latest_data_on_queue(test_data_2)

        for i in range(self.test_queue_size):
            expected_data = {
                'exchange': ALERT_EXCHANGE,
                'routing_key': CL_CONTRACT_ALERT_ROUTING_KEY,
                'data': 'data_2',
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True
            }
            self.assertEqual(expected_data,
                             self.test_contract_alerter.publishing_queue.get())

    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_error_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_conditional_alert")
    def test_process_result_does_nothing_if_config_not_received(
            self, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_win_alert, mock_no_change_alert,
            mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_contract_alerter._process_result(
            self.test_data_for_alerting_result_v3['result'],
            data_for_alerting)

        mock_cond_alert.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_thresh_win_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()
        mock_error_alert.assert_not_called()

    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_error_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_result_does_not_classify_if_metrics_disabled(
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
        self.test_contract_alerter._process_result(
            self.test_data_for_alerting_result_v3['result'], data_for_alerting)

        mock_reverse.assert_not_called()
        mock_cond_alert.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_thresh_win_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            5019, ErrorContractsNotRetrieved, ContractsNowRetrieved,
            data_for_alerting, self.test_parent_id, '', '',
            self.test_latest_timestamp_2,
            MetricCode.ErrorContractsNotRetrieved.value, "",
            "Chainlink contracts are now being retrieved!", None)
        call_2 = call(
            5018, ErrorNoSyncedDataSources, SyncedDataSourcesFound,
            data_for_alerting, self.test_parent_id, '', '',
            self.test_latest_timestamp_2,
            MetricCode.ErrorNoSyncedDataSources.value, "",
            "Synced EVM data sources found!", None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @parameterized.expand([
        ("self.test_data_for_alerting_result_v3",
         "self.test_missed_observations_2",
         "self.test_contract_proxy_address_2", 49),
        ("self.test_data_for_alerting_result_v4",
         "self.test_missed_observations_1",
         "self.test_contract_proxy_address_1", 39),
    ])
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_and_conditional_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_error_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_result_classifies_correctly_if_data_valid(
            self, mock_result_data, mock_observed, mock_proxy, mock_cons,
            mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_alert, mock_no_change_alert, mock_error_alert,
            mock_thresh_cond_alert) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_result function. Note that
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

        result_data = eval(mock_result_data)
        meta_data = result_data['result']['meta_data']
        data_for_alerting = []
        self.test_contract_alerter._process_result(
            result_data['result'], data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            5018, ErrorNoSyncedDataSources, SyncedDataSourcesFound,
            data_for_alerting, self.test_parent_id, "",
            "", meta_data['last_monitored'],
            MetricCode.ErrorNoSyncedDataSources.value, "",
            "Synced EVM data sources found!", None)
        call_2 = call(
            5019, ErrorContractsNotRetrieved, ContractsNowRetrieved,
            data_for_alerting, self.test_parent_id, "", "",
            meta_data['last_monitored'],
            MetricCode.ErrorContractsNotRetrieved.value, "",
            "Chainlink contracts are now being retrieved!", None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        calls = mock_cond_alert.call_args_list
        self.assertEqual(1, mock_cond_alert.call_count)
        call_1 = call(
            ConsensusFailure,
            self.test_contract_alerter._not_equal_condition_function,
            [mock_cons, mock_cons], [
                meta_data['node_name'],
                configs.consensus_failure['severity'],
                meta_data['last_monitored'],
                meta_data['node_parent_id'],
                meta_data['node_id'],
                eval(mock_proxy)],
            data_for_alerting)
        self.assertTrue(call_1 in calls)

        calls = mock_thresh_cond_alert.call_args_list
        self.assertEqual(1, mock_thresh_cond_alert.call_count)
        call_1 = call(
            eval(mock_observed), configs.price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self.test_contract_alerter._equal_condition_function, [
                eval(mock_observed), 0],
            data_for_alerting, self.test_parent_id, meta_data['node_id'],
            eval(mock_proxy), MetricCode.PriceFeedNotObserved.value,
            meta_data['node_name'], meta_data['last_monitored'])
        self.assertTrue(call_1 in calls)

        mock_thresh_alert.assert_not_called()
        mock_reverse.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()

    @parameterized.expand([
        ("self.test_data_for_alerting_result_v3", "None", "None", 0,
         "self.test_contract_proxy_address_2", 75.0),
        ("self.test_data_for_alerting_result_v3",
         "self.test_historical_rounds_2", "None", 1,
         "self.test_contract_proxy_address_2", 75.0),
        ("self.test_data_for_alerting_result_v3", "None",
         "self.test_historical_rounds_2", 1,
         "self.test_contract_proxy_address_2", 75.0),
        ("self.test_data_for_alerting_result_v4", "None", "None", 0,
         "self.test_contract_proxy_address_1", 100.0),
        ("self.test_data_for_alerting_result_v4",
         "self.test_historical_rounds_1", "None", 1,
         "self.test_contract_proxy_address_1", 100.0),
        ("self.test_data_for_alerting_result_v4", "None",
         "self.test_historical_rounds_1", 1,
         "self.test_contract_proxy_address_1", 100.0),
    ])
    @mock.patch.object(ChainlinkContractAlertingFactory,
                       "classify_thresholded_alert")
    def test_price_feed_deviation_executed_correctly(
            self, mock_result_data, mock_curr_hist, mock_prev_hist,
            call_count, mock_proxy, mock_deviation, mock_thresh_alert) -> None:
        """
        We want to test that all the data that is used to classify price
        feed observations is being processed correctly. We assume
        that we will always be calling thresh_alert for PriceFeedObservation
        therefore we add +1 to the call count.

        param 1: data_for_alerting
        param 2: curr_historical_rounds
        param 3: prev_historical_rounds
        param 4: thresh_call_count
        param 5: proxy address
        param 6: deviation
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        result_data = eval(mock_result_data)
        meta_data = result_data['result']['meta_data']

        # Convert data here for alert triggers
        result_data['result']['data'][eval(mock_proxy)]['historicalRounds'][
            'current'] = eval(mock_curr_hist)
        result_data['result']['data'][eval(mock_proxy)]['historicalRounds'][
            'previous'] = eval(mock_prev_hist)

        # Ensure that current_missed_observations is 0
        result_data['result']['data'][eval(mock_proxy)]['lastRoundObserved'][
            'current'] = result_data['result']['data'][eval(mock_proxy)][
                'latestRound']['current']

        data_for_alerting = []
        self.test_contract_alerter._process_result(
            result_data['result'], data_for_alerting)
        calls = mock_thresh_alert.call_args_list
        call_1 = call(
            mock_deviation, configs.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, meta_data['node_id'], eval(mock_proxy),
            MetricCode.PriceFeedDeviation.value, meta_data['node_name'],
            meta_data['last_monitored']
        )
        self.assertEqual(call_count, mock_thresh_alert.call_count)

        # Check if call_1 in calls only if we expect that alert to exist
        if call_count != 0:
            self.assertTrue(call_1 in calls)

    @mock.patch.object(ChainlinkContractAlertingFactory, "classify_error_alert")
    def test_process_error_classifies_correctly_if_data_valid(
            self, mock_error_alert) -> None:
        """
        In this test we will check that if we received an
        ErrorRetrievingChainlinkContractData Exception then we should generate
        an alert for it.
        """
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_contract_alerter._process_error(
            self.test_node_down_error, data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            5019, ErrorContractsNotRetrieved, ContractsNowRetrieved,
            data_for_alerting, self.test_parent_id, '', '',
            self.test_last_monitored,
            MetricCode.ErrorContractsNotRetrieved.value,
            self.test_exception.message,
            "Chainlink contracts are now being retrieved!",
            self.test_exception.code)
        call_2 = call(
            5018, ErrorNoSyncedDataSources, SyncedDataSourcesFound,
            data_for_alerting, self.test_parent_id, '', '',
            self.test_last_monitored,
            MetricCode.ErrorNoSyncedDataSources.value,
            self.test_exception.message,
            "Synced EVM data sources found!",
            self.test_exception.code)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(ChainlinkContractAlerter, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_places_alerts_on_queue_if_any(
            self, mock_basic_ack, mock_place_on_queue) -> None:
        """
        We are going to generate the alert through difference of heights
        between two nodes. We first send data for the first node to save it's
        current height then we send the second node whose height is very behind
        the first thus generating an alert.
        """
        # Add configs so that the data can be classified. The test data used
        # will generate an alert because it will obey the thresholds.
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        # Declare some fields for the process_transformed_data function
        self.test_contract_alerter._initialise_rabbitmq()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.test_data_for_alerting_result_v4)
        properties = pika.spec.BasicProperties()

        # Send data for first node
        self.test_contract_alerter._process_transformed_data(
            blocking_channel, method, properties, body)
        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_called_once()

    @mock.patch.object(ChainlinkContractAlerter,
                       "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_place_alerts_on_queue_if_none(
            self, mock_basic_ack, mock_place_on_queue) -> None:
        # We will not be adding configs so that no alerts are generated

        # Declare some fields for the process_transformed_data function
        self.test_contract_alerter._initialise_rabbitmq()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.test_data_for_alerting_result_v4)
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_not_called()

    @mock.patch.object(ChainlinkContractAlerter, "_process_result")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_raise_processing_error(
            self, mock_basic_ack, mock_process_result) -> None:
        """
        In this test we will generate an exception from one of the processing
        functions to see if an exception is raised.
        """
        mock_process_result.side_effect = self.test_exception

        # Declare some fields for the process_transformed_data function
        self.test_contract_alerter._initialise_rabbitmq()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.test_data_for_alerting_result_v4)
        properties = pika.spec.BasicProperties()
        try:
            self.test_contract_alerter._process_transformed_data(
                blocking_channel, method, properties, body)
        except PANICException as e:
            self.fail('Did not expect {} to be raised.'.format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(ChainlinkContractAlerter, "_send_data")
    @mock.patch.object(ChainlinkContractAlerter, "_process_result")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_attempts_to_send_data_from_queue(
            self, mock_basic_ack, mock_process_result,
            mock_send_data) -> None:
        # Add configs so that the data can be classified. The test data used
        # will generate an alert because it will obey the thresholds.
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        # First do the test for when there are no processing errors
        self.test_contract_alerter._initialise_rabbitmq()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.test_data_for_alerting_result_v4)
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

        # Now do the test for when there are processing errors
        mock_basic_ack.reset_mock()
        mock_send_data.reset_mock()
        mock_process_result.side_effect = self.test_exception

        # Declare some fields for the process_transformed_data function
        self.test_contract_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkContractAlerter, "_send_data")
    @mock.patch.object(ChainlinkContractAlerter, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_sends_hb_if_no_processing_errors(
            self, mock_basic_ack, mock_send_hb, mock_send_data) -> None:
        # To avoid sending data
        mock_send_data.return_value = None

        # Add configs so that the data can be classified. The test data used
        # will generate an alert because it will obey the thresholds.
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        self.test_contract_alerter._initialise_rabbitmq()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.test_data_for_alerting_result_v4)
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        test_hb = {
            'component_name': self.test_alerter_name,
            'is_alive': True,
            'timestamp': datetime.datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(test_hb)

    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkContractAlerter, "_process_result")
    @mock.patch.object(ChainlinkContractAlerter, "_send_data")
    @mock.patch.object(ChainlinkContractAlerter, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_send_hb_if_processing_error(
            self, mock_basic_ack, mock_send_hb, mock_send_data,
            mock_process_result) -> None:
        # To avoid sending data
        mock_send_data.return_value = None

        # Generate error in processing
        mock_process_result.side_effect = self.test_exception

        self.test_contract_alerter._initialise_rabbitmq()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.test_data_for_alerting_result_v4)
        properties = pika.spec.BasicProperties()
        self.test_contract_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        mock_send_hb.assert_not_called()

    @parameterized.expand([
        (pika.exceptions.AMQPConnectionError,
         pika.exceptions.AMQPConnectionError('test'),),
        (pika.exceptions.AMQPChannelError,
         pika.exceptions.AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(ChainlinkContractAlerter, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_raises_unexpected_exception(
            self, exception_class, exception_instance, mock_basic_ack,
            mock_send_data) -> None:
        # We will generate the error from the send_data fn
        mock_send_data.side_effect = exception_instance

        # Add configs so that the data can be classified. The test data used
        # will generate an alert because it will obey the thresholds.
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        self.test_contract_alerter._initialise_rabbitmq()
        blocking_channel = self.test_contract_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.test_data_for_alerting_result_v4)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_class,
                          self.test_contract_alerter._process_transformed_data,
                          blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
