import copy
import json
import logging
import unittest
from datetime import timedelta
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerters.network.cosmos import CosmosNetworkAlerter
from src.alerter.alerts.network.cosmos import *
from src.alerter.factory.cosmos_network_alerting_factory import (
    CosmosNetworkAlertingFactory)
from src.alerter.grouped_alerts_metric_code.network.cosmos_network_metric_code \
    import GroupedCosmosNetworkAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.network.cosmos import CosmosNetworkAlertsConfig
from src.configs.factory.alerts.cosmos_alerts import (
    CosmosNetworkAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.cosmos import (
    PROPOSAL_STATUS_PASSED, PROPOSAL_STATUS_VOTING_PERIOD,
    PROPOSAL_STATUS_REJECTED, PROPOSAL_STATUS_DEPOSIT_PERIOD)
from src.utils.constants.rabbitmq import (
    CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE, ALERT_EXCHANGE,
    COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY,
    COSMOS_NETWORK_ALERT_ROUTING_KEY)
from src.utils.env import RABBIT_IP
from src.utils.exceptions import (
    PANICException, NoSyncedDataSourceWasAccessibleException,
    CosmosNetworkDataCouldNotBeObtained)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, disconnect_from_rabbit,
    delete_exchange_if_exists)


class TestCosmosNetworkAlerter(unittest.TestCase):

    def setUp(self) -> None:
        # Some dummy values and objects
        self.test_alerter_name = 'test_alerter'
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)
        self.test_queue_size = 5
        self.test_parent_id = 'test_parent_id'
        self.test_queue_name = 'Test Queue'
        self.test_data_str_1 = 'test_data_str_1'
        self.test_data_str_2 = 'test_data_str_2'
        self.test_configs_routing_key = 'chains.cosmos.regen.alerts_config'
        self.test_chain_name = 'regen'
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.test_exception = PANICException('test_exception', 1)

        # Now we will construct the expected config objects
        self.received_configurations = {'DEFAULT': 'testing_if_will_be_deleted'}
        metrics_without_time_window, metrics_with_time_window = [], []
        severity_metrics = ['new_proposal', 'proposal_concluded']
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

        # Received transformed data examples
        self.test_proposal_1_current = {
            'proposal_id': 1,
            'title': 'test_proposal_1',
            'description': 'description_1',
            'status': PROPOSAL_STATUS_PASSED,
            'final_tally_result': {
                'yes': 100.0,
                'abstain': 60.0,
                'no': 20.0,
                'no_with_veto': 10.0,
            },
            'submit_time': datetime(2012, 1, 1).timestamp(),
            'deposit_end_time': datetime(2012, 1, 1).timestamp(),
            'total_deposit': [
                {
                    'denom': 'btc',
                    'amount': 100.0
                }
            ],
            'voting_start_time': datetime(2012, 1, 1).timestamp(),
            'voting_end_time': datetime(2012, 1, 1).timestamp(),
        }
        self.test_proposal_1_previous = copy.deepcopy(
            self.test_proposal_1_current)
        self.test_proposal_1_previous['status'] = PROPOSAL_STATUS_VOTING_PERIOD
        self.test_proposal_2_current = {
            'proposal_id': 2,
            'title': 'test_proposal_2',
            'description': 'description_2',
            'status': PROPOSAL_STATUS_VOTING_PERIOD,
            'final_tally_result': {
                'yes': 102.0,
                'abstain': 62.0,
                'no': 22.0,
                'no_with_veto': 12.0,
            },
            'submit_time': datetime(2012, 1, 1).timestamp(),
            'deposit_end_time': datetime(2012, 1, 1).timestamp(),
            'total_deposit': [
                {
                    'denom': 'btc',
                    'amount': 102.0
                }
            ],
            'voting_start_time': datetime(2012, 1, 1).timestamp(),
            'voting_end_time': datetime(2012, 1, 1).timestamp(),
        }
        self.test_proposal_2_previous = copy.deepcopy(
            self.test_proposal_2_current)
        self.test_proposal_2_previous['status'] = PROPOSAL_STATUS_DEPOSIT_PERIOD
        self.test_proposal_3_current = {
            'proposal_id': None,
            'title': 'test_proposal_3',
            'description': 'description_3',
            'status': PROPOSAL_STATUS_REJECTED,
            'final_tally_result': {
                'yes': 103.0,
                'abstain': 63.0,
                'no': 23.0,
                'no_with_veto': 13.0,
            },
            'submit_time': datetime(2012, 1, 1).timestamp(),
            'deposit_end_time': datetime(2012, 1, 1).timestamp(),
            'total_deposit': [
                {
                    'denom': 'btc',
                    'amount': 103.0
                }
            ],
            'voting_start_time': datetime(2012, 1, 1).timestamp(),
            'voting_end_time': datetime(2012, 1, 1).timestamp(),
        }
        self.test_proposal_3_previous = copy.deepcopy(
            self.test_proposal_3_current)
        self.test_current_proposals = [
            self.test_proposal_1_current,
            self.test_proposal_2_current,
            self.test_proposal_3_current,
        ]
        self.test_previous_proposals = [
            self.test_proposal_1_previous,
            self.test_proposal_2_previous,
            self.test_proposal_3_previous,
        ]
        self.transformed_data_result = {
            'cosmos_rest': {
                'result': {
                    'meta_data': {
                        'parent_id': self.test_parent_id,
                        'chain_name': self.test_chain_name,
                        'last_monitored': self.test_last_monitored,
                    },
                    'data': {
                        'proposals': {
                            'current': self.test_current_proposals,
                            'previous': self.test_previous_proposals
                        },
                    },
                }
            },
        }
        self.transformed_data_general_error = {
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'parent_id': self.test_parent_id,
                        'chain_name': self.test_chain_name,
                        'time': self.test_last_monitored,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
        }

        # Test objects
        self.test_configs_factory = CosmosNetworkAlertsConfigsFactory()
        self.test_alerting_factory = CosmosNetworkAlertingFactory(
            self.dummy_logger)
        self.test_alerter = CosmosNetworkAlerter(
            self.test_alerter_name, self.dummy_logger, self.rabbitmq,
            self.test_configs_factory, self.test_queue_size)

    def tearDown(self) -> None:
        connect_to_rabbit(self.test_alerter.rabbitmq)
        delete_queue_if_exists(self.test_alerter.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_alerter.rabbitmq,
                               COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_alerter.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_alerter.rabbitmq, ALERT_EXCHANGE)
        delete_exchange_if_exists(self.test_alerter.rabbitmq, CONFIG_EXCHANGE)
        disconnect_from_rabbit(self.test_alerter.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_configs_factory = None
        self.test_alerting_factory = None
        self.test_alerter = None
        self.test_exception = None

    def test_alerts_configs_factory_returns_alerts_configs_factory(
            self) -> None:
        self.test_alerter._alerts_configs_factory = self.test_configs_factory
        self.assertEqual(self.test_configs_factory,
                         self.test_alerter.alerts_configs_factory)

    def test_alerting_factory_returns_alerting_factory(self) -> None:
        self.test_alerter._alerting_factory = self.test_alerting_factory
        self.assertEqual(self.test_alerting_factory,
                         self.test_alerter.alerting_factory)

    @mock.patch.object(RabbitMQApi, "basic_consume")
    @mock.patch.object(RabbitMQApi, "basic_qos")
    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self, mock_basic_qos, mock_basic_consume) -> None:
        mock_basic_consume.return_value = None
        mock_basic_qos.return_value = None

        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.queue_delete(
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        self.test_alerter._initialise_rabbitmq()

        # Perform checks that the connection has been opened and marked as open,
        # that the delivery confirmation variable is set and basic_qos called
        # successfully.
        self.assertTrue(self.test_alerter.rabbitmq.is_connected)
        self.assertTrue(self.test_alerter.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_alerter.rabbitmq.channel._delivery_confirmation)
        mock_basic_qos.assert_called_once_with(
            prefetch_count=round(self.test_queue_size / 5))

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_alerter.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE,
                                                    passive=True)

        # Check whether the consuming exchanges and queues have been creating by
        # sending messages with the same routing keys as for the bindings.
        res = self.test_alerter.rabbitmq.queue_declare(
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(0, res.method.message_count)
        self.test_alerter.rabbitmq.basic_publish_confirm(
            exchange=ALERT_EXCHANGE,
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str_1, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_alerter.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE, routing_key=self.test_configs_routing_key,
            body=self.test_data_str_2, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_alerter.rabbitmq.queue_declare(
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(2, res.method.message_count)

        # Check that the message contents are correct
        _, _, body = self.test_alerter.rabbitmq.basic_get(
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str_1, body.decode())
        _, _, body = self.test_alerter.rabbitmq.basic_get(
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str_2, body.decode())

        mock_basic_consume.assert_called_once()

    @parameterized.expand([
        (COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY, 'mock_proc_trans',),
        ('chains.cosmos.regen.alerts_config', 'mock_proc_confs',),
        ('unrecognized_routing_key', 'mock_basic_ack',),
    ])
    @mock.patch.object(CosmosNetworkAlerter, "_process_transformed_data")
    @mock.patch.object(CosmosNetworkAlerter, "_process_configs")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_calls_the_correct_sub_function(
            self, routing_key, called_mock, mock_basic_ack, mock_proc_confs,
            mock_proc_trans) -> None:
        """
        In this test we will check that if a configs routing key is received,
        the process_data function calls the process_configs fn, if a transformed
        data routing key is received, the process_data function calls the
        process_transformed_data fn, and if the routing key is unrecognized, the
        process_data function calls the ack method.
        """
        mock_basic_ack.return_value = None
        mock_proc_confs.return_value = None
        mock_proc_trans.return_value = None

        self.test_alerter.rabbitmq.connect()
        blocking_channel = self.test_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=routing_key)
        body = bytes(json.dumps(self.test_data_str_1), 'utf-8')
        properties = pika.spec.BasicProperties()
        self.test_alerter._process_data(blocking_channel, method, properties,
                                        body)

        eval(called_mock).assert_called_once()

    """
    In the majority of the tests below we will perform mocking. The tests for
    config processing and alerting were performed in separate test files which
    targeted the factory classes.
    """

    @mock.patch.object(CosmosNetworkAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(CosmosNetworkAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(CosmosNetworkAlertingFactory,
                       "remove_chain_alerting_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_confs_adds_new_conf_and_clears_alerting_state_if_new_confs(
            self, mock_ack, mock_remove_alerting_state, mock_add_new_conf,
            mock_get_parent_id) -> None:
        """
        In this test we will check that if new alert configs are received for
        a new chain, the new config is added and the alerting state is cleared.
        """
        mock_ack.return_value = None
        mock_get_parent_id.return_value = self.test_parent_id

        self.test_alerter.rabbitmq.connect()
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = bytes(json.dumps(self.received_configurations), 'utf-8')
        self.test_alerter._process_configs(method, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_add_new_conf.assert_called_once_with(chain,
                                                  self.received_configurations)
        mock_get_parent_id.assert_called_once_with(chain,
                                                   CosmosNetworkAlertsConfig)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_ack.assert_called_once()

    @mock.patch.object(CosmosNetworkAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(CosmosNetworkAlertsConfigsFactory, "remove_config")
    @mock.patch.object(CosmosNetworkAlertingFactory,
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

        self.test_alerter.rabbitmq.connect()
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = bytes(json.dumps({}), 'utf-8')
        self.test_alerter._process_configs(method, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_get_parent_id.assert_called_once_with(chain,
                                                   CosmosNetworkAlertsConfig)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_remove_config.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(CosmosNetworkAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(CosmosNetworkAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(CosmosNetworkAlertsConfigsFactory, "remove_config")
    @mock.patch.object(CosmosNetworkAlertingFactory,
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

        self.test_alerter.rabbitmq.connect()
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = bytes(json.dumps({}), 'utf-8')
        self.test_alerter._process_configs(method, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        mock_remove_alerting_state.assert_not_called()
        mock_remove_conf.assert_not_called()
        mock_add_new_conf.assert_not_called()
        mock_get_parent_id.assert_called_once_with(chain,
                                                   CosmosNetworkAlertsConfig)
        mock_ack.assert_called_once()

    def test_place_latest_data_on_queue_places_data_on_queue_correctly(
            self) -> None:
        test_data = ['data_1', 'data_2']

        self.assertTrue(self.test_alerter.publishing_queue.empty())

        expected_data_1 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': COSMOS_NETWORK_ALERT_ROUTING_KEY,
            'data': 'data_1',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_2 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': COSMOS_NETWORK_ALERT_ROUTING_KEY,
            'data': 'data_2',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        self.test_alerter._place_latest_data_on_queue(test_data)
        self.assertEqual(2,
                         self.test_alerter.publishing_queue.qsize())
        self.assertEqual(expected_data_1,
                         self.test_alerter.publishing_queue.get())
        self.assertEqual(expected_data_2,
                         self.test_alerter.publishing_queue.get())

    def test_place_latest_data_on_queue_removes_old_data_if_full_then_places(
            self) -> None:
        # First fill the queue with the same data
        test_data_1 = ['data_1']
        for i in range(self.test_queue_size):
            self.test_alerter._place_latest_data_on_queue(test_data_1)

        # Now fill the queue with the second piece of data, and confirm that
        # now only the second piece of data prevails.
        test_data_2 = ['data_2']
        for i in range(self.test_queue_size):
            self.test_alerter._place_latest_data_on_queue(test_data_2)

        for i in range(self.test_queue_size):
            expected_data = {
                'exchange': ALERT_EXCHANGE,
                'routing_key': COSMOS_NETWORK_ALERT_ROUTING_KEY,
                'data': 'data_2',
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True
            }
            self.assertEqual(expected_data,
                             self.test_alerter.publishing_queue.get())

    @parameterized.expand([
        (True, [{}, {}], True, True, True),
        (True, [{}, {}], True, False, True),
        (True, [{}, {}], False, True, True),
        (True, [{}, {}], False, False, False),
        (True, [], True, True, False),
        (True, [], True, False, False),
        (True, [], False, True, False),
        (True, [], False, False, False),
        (False, [{}, {}], True, True, False),
        (False, [{}, {}], True, False, False),
        (False, [{}, {}], False, True, False),
        (False, [{}, {}], False, False, False),
        (False, [], True, True, False),
        (False, [], True, False, False),
        (False, [], False, True, False),
        (False, [], False, False, False),
    ])
    def test_alert_new_proposal_returns_as_expected(
            self, is_active, previous_proposals, new_proposal, was_not_active,
            expected_return) -> None:
        """
        We will iterate over every possible scenario to check that the
        self._alert_new_proposal function returns as expected
        """
        actual_return = self.test_alerter._alert_new_proposal(
            is_active, previous_proposals, new_proposal, was_not_active)
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        (True, False, False,),
        (False, True, True,),
        (True, True, False,),
        (False, False, False),
    ])
    def test_alert_proposal_conclusion_returns_as_expected(
            self, is_active, was_active, expected_return) -> None:
        """
        We will iterate over every possible scenario to check that the
        self._alert_proposal_conclusion function returns as expected
        """
        actual_return = self.test_alerter._alert_proposal_conclusion(is_active,
                                                                     was_active)
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(CosmosNetworkAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNetworkAlertingFactory,
                       "classify_conditional_alert")
    def test_process_cosmos_rest_result_does_nothing_if_config_not_received(
            self, mock_conditional, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if cosmos_rest data has been received for a network who's associated
        alerts configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_cosmos_rest_result(
            self.transformed_data_result['cosmos_rest']['result'],
            data_for_alerting)

        mock_conditional.assert_not_called()
        mock_error_alert.assert_not_called()

    @mock.patch.object(CosmosNetworkAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNetworkAlertingFactory,
                       "classify_conditional_alert")
    def test_process_cosmos_rest_result_does_not_classify_if_metrics_disabled(
            self, mock_conditional, mock_error_alert) -> None:
        """
        In this test we will check that if a metric is disabled from the config,
        there will be no alert classification for the associated metric. Note
        that for easier testing we will set every metric to be disabled. IMP,
        the only classification which would happen is for the error alerts as
        they are not associated with any metric.
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
        self.test_alerter._process_cosmos_rest_result(
            self.transformed_data_result['cosmos_rest']['result'],
            data_for_alerting)

        mock_conditional.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedCosmosRestDataSourcesAlert,
            SyncedCosmosRestDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_parent_id, self.test_chain_name,
            self.test_last_monitored,
            AlertsMetricCode.NoSyncedCosmosRestSource.value, "",
            "The Network Monitor for {} found a Cosmos-Rest synced data source "
            "again".format(self.test_chain_name), None)
        call_2 = call(
            CosmosNetworkDataCouldNotBeObtained.code,
            CosmosNetworkDataCouldNotBeObtainedAlert,
            CosmosNetworkDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_parent_id, self.test_chain_name,
            self.test_last_monitored,
            AlertsMetricCode.CosmosNetworkDataNotObtained.value, "",
            "The Network Monitor for {} successfully retrieved network data "
            "again.".format(self.test_chain_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(CosmosNetworkAlertingFactory, "add_active_proposal")
    @mock.patch.object(CosmosNetworkAlertingFactory, "remove_active_proposal")
    @mock.patch.object(CosmosNetworkAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNetworkAlertingFactory,
                       "classify_conditional_alert")
    def test_process_cosmos_rest_result_classifies_correctly_if_data_valid(
            self, mock_conditional, mock_error_alert,
            mock_remove_active_proposal, mock_add_active_proposal) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_cosmos_rest_result function. Note that
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
        self.test_alerter._process_cosmos_rest_result(
            self.transformed_data_result['cosmos_rest']['result'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedCosmosRestDataSourcesAlert,
            SyncedCosmosRestDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_parent_id, self.test_chain_name,
            self.test_last_monitored,
            AlertsMetricCode.NoSyncedCosmosRestSource.value, "",
            "The Network Monitor for {} found a Cosmos-Rest synced data source "
            "again".format(self.test_chain_name), None)
        call_2 = call(
            CosmosNetworkDataCouldNotBeObtained.code,
            CosmosNetworkDataCouldNotBeObtainedAlert,
            CosmosNetworkDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_parent_id, self.test_chain_name,
            self.test_last_monitored,
            AlertsMetricCode.CosmosNetworkDataNotObtained.value, "",
            "The Network Monitor for {} successfully retrieved network data "
            "again.".format(self.test_chain_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        calls = mock_conditional.call_args_list
        self.assertEqual(2, mock_conditional.call_count)
        new_proposal_configs = configs.new_proposal
        proposal_concluded_configs = configs.proposal_concluded
        call_1 = call(
            NewProposalSubmittedAlert, self.test_alerter._alert_new_proposal,
            [True, self.test_previous_proposals, False, True],
            [self.test_chain_name, self.test_proposal_2_current['proposal_id'],
             self.test_proposal_2_current['title'],
             self.test_proposal_2_current['voting_end_time'],
             new_proposal_configs['severity'], self.test_last_monitored,
             self.test_parent_id, self.test_parent_id], data_for_alerting,
        )
        call_2 = call(
            ProposalConcludedAlert,
            self.test_alerter._alert_proposal_conclusion, [False, True],
            [self.test_chain_name, self.test_proposal_1_current['proposal_id'],
             self.test_proposal_1_current['title'],
             self.test_proposal_1_current['status'],
             self.test_proposal_1_current['final_tally_result'],
             proposal_concluded_configs['severity'], self.test_last_monitored,
             self.test_parent_id, self.test_parent_id], data_for_alerting,
        )
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        # Check that active proposals have been added to the alerting state, and
        # concluded proposals have been removed from the alerting state. Note
        # that in this test we are assuming that no active proposals have been
        # added previously.
        mock_remove_active_proposal.assert_called_once_with(
            self.test_parent_id, self.test_proposal_1_current['proposal_id'])
        mock_add_active_proposal.assert_called_once_with(
            self.test_parent_id, self.test_proposal_2_current,
            self.test_proposal_2_current['proposal_id'])

    @mock.patch.object(CosmosNetworkAlertingFactory, "classify_error_alert")
    def test_process_cosmos_rest_error_does_nothing_if_config_not_received(
            self, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if cosmos_rest data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_cosmos_rest_error(
            self.transformed_data_general_error['cosmos_rest']['error'],
            data_for_alerting)

        mock_error_alert.assert_not_called()

    @mock.patch.object(CosmosNetworkAlertingFactory, "classify_error_alert")
    def test_process_cosmos_rest_error_classifies_correctly_if_data_valid(
            self, mock_error_alert) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_cosmos_rest_error function. Note that
        the actual logic for these classification functions was tested in the
        alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_alerter._process_cosmos_rest_error(
            self.transformed_data_general_error['cosmos_rest']['error'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        error_msg = self.transformed_data_general_error['cosmos_rest']['error'][
            'message']
        error_code = self.transformed_data_general_error['cosmos_rest'][
            'error']['code']
        call_1 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedCosmosRestDataSourcesAlert,
            SyncedCosmosRestDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_parent_id, self.test_chain_name,
            self.test_last_monitored,
            AlertsMetricCode.NoSyncedCosmosRestSource.value, error_msg,
            "The Network Monitor for {} found a Cosmos-Rest synced data source "
            "again".format(self.test_chain_name), error_code)
        call_2 = call(
            CosmosNetworkDataCouldNotBeObtained.code,
            CosmosNetworkDataCouldNotBeObtainedAlert,
            CosmosNetworkDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_parent_id, self.test_chain_name,
            self.test_last_monitored,
            AlertsMetricCode.CosmosNetworkDataNotObtained.value, error_msg,
            "The Network Monitor for {} successfully retrieved network data "
            "again.".format(self.test_chain_name), error_code)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch(
        "src.alerter.alerters.network.cosmos.transformed_data_processing_helper"
    )
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_calls_the_correct_process_fns_correctly(
            self, mock_basic_ack, mock_helper) -> None:
        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = bytes(json.dumps(self.transformed_data_result), 'utf-8')
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        configuration = {
            'cosmos_rest': {
                'result': self.test_alerter._process_cosmos_rest_result,
                'error': self.test_alerter._process_cosmos_rest_error,
            },
        }
        mock_helper.assert_called_once_with(
            self.test_alerter_name, configuration, self.transformed_data_result,
            [])

    @mock.patch.object(CosmosNetworkAlerter, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_places_alerts_on_queue_if_any(
            self, mock_basic_ack, mock_place_on_queue) -> None:
        # Add configs so that the data can be classified. The test data used
        # will generate an alert because it will obey the thresholds.
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = bytes(json.dumps(self.transformed_data_result), 'utf-8')
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_called_once()

    @mock.patch.object(CosmosNetworkAlerter, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_place_alerts_on_queue_if_none(
            self, mock_basic_ack, mock_place_on_queue) -> None:
        # We will not be adding configs so that no alerts are generated

        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = bytes(json.dumps(self.transformed_data_result), 'utf-8')
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_not_called()

    @mock.patch(
        "src.alerter.alerters.network.cosmos.transformed_data_processing_helper"
    )
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_raise_processing_error(
            self, mock_basic_ack, mock_helper) -> None:
        """
        In this test we will generate an exception from one of the processing
        functions to see if an exception is raised.
        """
        mock_helper.side_effect = self.test_exception

        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = bytes(json.dumps(self.transformed_data_result), 'utf-8')
        try:
            self.test_alerter._process_transformed_data(method, body)
        except PANICException as e:
            self.fail('Did not expect {} to be raised.'.format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(CosmosNetworkAlerter, "_send_data")
    @mock.patch(
        "src.alerter.alerters.network.cosmos.transformed_data_processing_helper"
    )
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_attempts_to_send_data_from_queue(
            self, mock_basic_ack, mock_helper, mock_send_data) -> None:
        # Add configs so that the data can be classified. The test data used
        # will generate an alert because it will obey the thresholds.
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        # First do the test for when there are no processing errors
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = bytes(json.dumps(self.transformed_data_result), 'utf-8')
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

        # Now do the test for when there are processing errors
        mock_basic_ack.reset_mock()
        mock_send_data.reset_mock()
        mock_helper.side_effect = self.test_exception

        # Declare some fields for the process_transformed_data function
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(CosmosNetworkAlerter, "_send_data")
    @mock.patch.object(CosmosNetworkAlerter, "_send_heartbeat")
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

        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = bytes(json.dumps(self.transformed_data_result), 'utf-8')
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        test_hb = {
            'component_name': self.test_alerter_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(test_hb)

    @freeze_time("2012-01-01")
    @mock.patch(
        "src.alerter.alerters.network.cosmos.transformed_data_processing_helper"
    )
    @mock.patch.object(CosmosNetworkAlerter, "_send_data")
    @mock.patch.object(CosmosNetworkAlerter, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_send_hb_if_processing_error(
            self, mock_basic_ack, mock_send_hb, mock_send_data,
            mock_helper) -> None:
        # To avoid sending data
        mock_send_data.return_value = None

        # Generate error in processing
        mock_helper.side_effect = self.test_exception

        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = bytes(json.dumps(self.transformed_data_result), 'utf-8')
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_send_hb.assert_not_called()

    @parameterized.expand([
        (pika.exceptions.AMQPConnectionError,
         pika.exceptions.AMQPConnectionError('test'),),
        (pika.exceptions.AMQPChannelError,
         pika.exceptions.AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(CosmosNetworkAlerter, "_send_data")
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

        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)

        self.assertRaises(exception_class,
                          self.test_alerter._process_transformed_data,
                          method, body)

        mock_basic_ack.assert_called_once()
