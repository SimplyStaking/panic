import json
import logging
import unittest
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alert_severities import Severity
from src.alerter.alerters.node.substrate import SubstrateNodeAlerter
from src.alerter.alerts.node.substrate import *
from src.alerter.factory.substrate_node_alerting_factory import (
    SubstrateNodeAlertingFactory)
from src.configs.alerts.node.substrate import SubstrateNodeAlertsConfig
from src.configs.factory.alerts.substrate_alerts import (
    SubstrateNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE, ALERT_EXCHANGE,
    SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    SUBSTRATE_NODE_ALERT_ROUTING_KEY)
from src.utils.env import RABBIT_IP
from src.utils.exceptions import (
    PANICException, NodeIsDownException,
    NoSyncedDataSourceWasAccessibleException,
    SubstrateWebSocketDataCouldNotBeObtained,
    SubstrateApiIsNotReachableException)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit)


class TestSubstrateNodeAlerter(unittest.TestCase):

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
        self.test_configs_routing_key = 'chains.substrate.kusama.alerts_config'
        self.test_node_name = 'test_substrate_node'
        self.test_node_id = 'test_substrate_node_id345834t8h3r5893h8'
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.test_token_symbol = 'TEST'
        self.test_is_validator = True
        self.test_stash_address = 'test_address'
        self.test_exception = PANICException('test_exception', 1)
        self.test_node_is_down_exception = NodeIsDownException(
            self.test_node_name)

        # Now we will construct the expected config objects
        self.received_configurations = {'DEFAULT': 'testing_if_will_be_deleted'}
        metrics_without_time_window = [
            'cannot_access_validator', 'cannot_access_node',
            'no_change_in_best_block_height_validator',
            'no_change_in_best_block_height_node',
            'no_change_in_finalized_block_height_validator',
            'no_change_in_finalized_block_height_node',
            'validator_is_syncing', 'node_is_syncing',
            'no_heartbeat_did_not_author_block', 'payout_not_claimed'
        ]
        severity_metrics = [
            'not_active_in_session', 'is_disabled', 'not_elected',
            'bonded_amount_change', 'offline', 'slashed',
            'controller_address_change'
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

        # Received transformed data examples
        self.transformed_data_result = {
            'websocket': {
                'result': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'last_monitored': self.test_last_monitored,
                        'token_symbol': self.test_token_symbol,
                        'is_validator': self.test_is_validator,
                        'stash_address': self.test_stash_address,
                    },
                    'data': {
                        'best_height': {'current': 123, 'previous': 120},
                        'target_height': {'current': 123, 'previous': 120},
                        'finalized_height': {'current': 120, 'previous': 119},
                        'current_session': {'current': 123, 'previous': 123},
                        'current_era': {'current': 123, 'previous': 123},
                        'authored_blocks': {'current': 1, 'previous': 0},
                        'active': {'current': True, 'previous': False},
                        'elected': {'current': True, 'previous': False},
                        'disabled': {'current': False, 'previous': False},
                        'eras_stakers': {
                            'current': {
                                'total': 234.56,
                                'own': 123.45,
                                'others': [{
                                    'who': 'test_address',
                                    'value': 123.45
                                }]
                            },
                            'previous': {
                                'total': 234.56,
                                'own': 123.45,
                                'others': [{
                                    'who': 'test_address',
                                    'value': 123.45
                                }]
                            }},
                        'sent_heartbeat': {'current': True, 'previous': False},
                        'controller_address': {'current': 'abcdefg',
                                               'previous': 'abcdefg'},
                        'history_depth_eras': {'current': 84, 'previous': 84},
                        'unclaimed_rewards': {'current': [119, 120],
                                              'previous': [119]},
                        'claimed_rewards': {'current': [117, 118],
                                            'previous': [117]},
                        'previous_era_rewards': {'current': 123,
                                                 'previous': 123},
                        'historical': {
                            'current': [
                                {
                                    "height": 120,
                                    "slashed": False,
                                    "slashed_amount": 0,
                                    "is_offline": False
                                }
                            ],
                            'previous': [
                                {
                                    "height": 119,
                                    "slashed": True,
                                    "slashed_amount": 123.45,
                                    "is_offline": True
                                }
                            ]},
                        'went_down_at': {'current': None, 'previous': None},
                    },
                }
            },
        }
        self.transformed_data_general_error = {
            'websocket': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'stash_address': self.test_stash_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.transformed_data_substrate_api_error = {
            'websocket': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'stash_address': self.test_stash_address,
                    },
                    'message': self.test_exception.message,
                    'code': SubstrateApiIsNotReachableException.code,
                }
            }
        }
        self.transformed_data_downtime_error = {
            'websocket': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'stash_address': self.test_stash_address,
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': {
                            'current': self.test_last_monitored,
                            'previous': None
                        }
                    }
                }
            }
        }

        # Test objects
        self.test_configs_factory = SubstrateNodeAlertsConfigsFactory()
        self.test_alerting_factory = SubstrateNodeAlertingFactory(
            self.dummy_logger)
        self.test_alerter = SubstrateNodeAlerter(
            self.test_alerter_name, self.dummy_logger, self.rabbitmq,
            self.test_configs_factory, self.test_queue_size)

    def tearDown(self) -> None:
        connect_to_rabbit(self.test_alerter.rabbitmq)
        delete_queue_if_exists(self.test_alerter.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_alerter.rabbitmq,
                               SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
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
        self.test_node_is_down_exception = None

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
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
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
        self.test_alerter.rabbitmq.exchange_declare(
            HEALTH_CHECK_EXCHANGE, passive=True)

        # Check whether the consuming exchanges and queues have been creating by
        # sending messages with the same routing keys as for the bindings.
        res = self.test_alerter.rabbitmq.queue_declare(
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(0, res.method.message_count)
        self.test_alerter.rabbitmq.basic_publish_confirm(
            exchange=ALERT_EXCHANGE,
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str_1, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_alerter.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE, routing_key=self.test_configs_routing_key,
            body=self.test_data_str_2, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_alerter.rabbitmq.queue_declare(
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(2, res.method.message_count)

        # Check that the message contents are correct
        _, _, body = self.test_alerter.rabbitmq.basic_get(
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str_1, body.decode())
        _, _, body = self.test_alerter.rabbitmq.basic_get(
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str_2, body.decode())

        mock_basic_consume.assert_called_once()

    @parameterized.expand([
        (SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY, 'mock_proc_trans',),
        ('chains.substrate.kusama.alerts_config', 'mock_proc_confs',),
        ('unrecognized_routing_key', 'mock_basic_ack',),
    ])
    @mock.patch.object(SubstrateNodeAlerter, "_process_transformed_data")
    @mock.patch.object(SubstrateNodeAlerter, "_process_configs")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_calls_the_correct_sub_function(
            self, routing_key, called_mock, mock_basic_ack, mock_proc_confs,
            mock_proc_trans) -> None:
        """
        In this test we will check that if a configs routing key is received the
        process_data function calls the process_configs fn, if a transformed
        data routing key is received the process_data function calls the
        process_transformed_data fn, and if the routing key is unrecognized the
        process_data function calls the ack method.
        """
        mock_basic_ack.return_value = None
        mock_proc_confs.return_value = None
        mock_proc_trans.return_value = None

        self.test_alerter.rabbitmq.connect()
        blocking_channel = self.test_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=routing_key)
        body = json.dumps(self.test_data_str_1)
        properties = pika.spec.BasicProperties()
        self.test_alerter._process_data(blocking_channel, method, properties,
                                        body)

        eval(called_mock).assert_called_once()

    """
    In the majority of the tests below we will perform mocking. The tests for
    config processing and alerting were performed in separate test files which
    targeted the factory classes.
    """

    @mock.patch.object(SubstrateNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(SubstrateNodeAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(SubstrateNodeAlertingFactory,
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
        body = json.dumps(self.received_configurations)
        self.test_alerter._process_configs(method, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_add_new_conf.assert_called_once_with(chain,
                                                  self.received_configurations)
        mock_get_parent_id.assert_called_once_with(chain,
                                                   SubstrateNodeAlertsConfig)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_ack.assert_called_once()

    @mock.patch.object(SubstrateNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(SubstrateNodeAlertsConfigsFactory, "remove_config")
    @mock.patch.object(SubstrateNodeAlertingFactory,
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
        body = json.dumps({})
        self.test_alerter._process_configs(method, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_get_parent_id.assert_called_once_with(chain,
                                                   SubstrateNodeAlertsConfig)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_remove_config.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(SubstrateNodeAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(SubstrateNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(SubstrateNodeAlertsConfigsFactory, "remove_config")
    @mock.patch.object(SubstrateNodeAlertingFactory,
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
        body = json.dumps({})
        self.test_alerter._process_configs(method, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        mock_remove_alerting_state.assert_not_called()
        mock_remove_conf.assert_not_called()
        mock_add_new_conf.assert_not_called()
        mock_get_parent_id.assert_called_once_with(chain,
                                                   SubstrateNodeAlertsConfig)
        mock_ack.assert_called_once()

    def test_place_latest_data_on_queue_places_data_on_queue_correctly(
            self) -> None:
        test_data = ['data_1', 'data_2']

        self.assertTrue(self.test_alerter.publishing_queue.empty())

        expected_data_1 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': SUBSTRATE_NODE_ALERT_ROUTING_KEY,
            'data': 'data_1',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_2 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': SUBSTRATE_NODE_ALERT_ROUTING_KEY,
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
                'routing_key': SUBSTRATE_NODE_ALERT_ROUTING_KEY,
                'data': 'data_2',
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True
            }
            self.assertEqual(expected_data,
                             self.test_alerter.publishing_queue.get())

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_does_nothing_if_config_not_received(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if websocket data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        mock_era_solve.assert_not_called()
        mock_thresholded_era.assert_not_called()
        mock_conditional_no_change.assert_not_called()
        mock_conditional.assert_not_called()
        mock_solvable_conditional.assert_not_called()
        mock_thresholded.assert_not_called()
        mock_no_change.assert_not_called()
        mock_error_alert.assert_not_called()

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_websocket_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_does_not_classify_if_metrics_disabled(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
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
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        mock_era_solve.assert_not_called()
        mock_thresholded_era.assert_not_called()
        mock_conditional_no_change.assert_not_called()
        mock_conditional.assert_not_called()
        mock_solvable_conditional.assert_not_called()
        mock_thresholded.assert_not_called()
        mock_no_change.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            SyncedSubstrateWebSocketDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored, (GroupedSubstrateNodeAlertsMetricCode
                                       .NoSyncedSubstrateWebSocketSource.value),
            "", "The monitor for {} found a websocket synced data "
                "source again.".format(self.test_node_name), None)
        call_2 = call(
            SubstrateWebSocketDataCouldNotBeObtained.code,
            SubstrateWebSocketDataCouldNotBeObtainedAlert,
            SubstrateWebSocketDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            (GroupedSubstrateNodeAlertsMetricCode
             .SubstrateWebSocketDataNotObtained.value), "",
            "The monitor for {} successfully retrieved websocket data "
            "again.".format(self.test_node_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_era_solve_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct era solve classification
        function is called correctly by the process_websocket_result function.
        Note that the actual logic for this classification function was tested
        in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_era_solve.call_args_list
        current_claimed_rewards = self.transformed_data_result['websocket'][
            'result']['data']['claimed_rewards']['current']
        previous_claimed_rewards = self.transformed_data_result['websocket'][
            'result']['data']['claimed_rewards']['previous']
        new_claimed_rewards = (list(set(current_claimed_rewards) -
                                    set(previous_claimed_rewards)))
        self.assertEqual(len(new_claimed_rewards), mock_era_solve.call_count)
        for claimed_reward_era in new_claimed_rewards:
            call_1 = call(
                claimed_reward_era, ValidatorPayoutClaimedAlert,
                data_for_alerting, self.test_parent_id, self.test_node_id,
                self.test_node_name, self.test_last_monitored
            )
            self.assertTrue(call_1 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_thresholded_era_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct thresholded era
        classification function is called correctly by the
        process_websocket_result function. Note that the actual logic for
        this classification function was tested in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_thresholded_era.call_args_list
        current_unclaimed_rewards = self.transformed_data_result['websocket'][
            'result']['data']['unclaimed_rewards']['current']
        self.assertEqual(len(current_unclaimed_rewards),
                         mock_thresholded_era.call_count)
        current_era = self.transformed_data_result['websocket'][
            'result']['data']['current_era']['current']
        payout_not_claimed_configs = configs.payout_not_claimed
        for unclaimed_reward_era in current_unclaimed_rewards:
            era_difference = current_era - unclaimed_reward_era
            call_1 = call(
                unclaimed_reward_era, era_difference,
                payout_not_claimed_configs, ValidatorPayoutNotClaimedAlert,
                data_for_alerting, self.test_parent_id, self.test_node_id,
                (GroupedSubstrateNodeAlertsMetricCode
                 .ValidatorPayoutNotClaimed.value), self.test_node_name,
                self.test_last_monitored
            )
            self.assertTrue(call_1 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_conditional_no_change_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct conditional no change
        classification function is called correctly by the
        process_websocket_result function. Note that the actual logic for this
        classification function was tested in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_conditional_no_change.call_args_list
        self.assertEqual(1, mock_conditional_no_change.call_count)
        current_session = self.transformed_data_result['websocket'][
            'result']['data']['current_session']['current']
        previous_session = self.transformed_data_result['websocket'][
            'result']['data']['current_session']['previous']
        current_authored_blocks = self.transformed_data_result['websocket'][
            'result']['data']['authored_blocks']['current']
        current_sent_heartbeat = self.transformed_data_result['websocket'][
            'result']['data']['sent_heartbeat']['current']
        no_heartbeat_did_not_author_block_configs = (
            configs.no_heartbeat_did_not_author_block
        )
        call_1 = call(
            current_session, previous_session,
            no_heartbeat_did_not_author_block_configs,
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert,
            self.test_alerter._is_true_condition_function,
            [current_authored_blocks == 0 and not current_sent_heartbeat],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            (GroupedSubstrateNodeAlertsMetricCode
             .ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, self.test_last_monitored
        )
        self.assertTrue(call_1 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_conditional_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct conditional classification
        function is called correctly by the process_websocket_result
        function. Note that the actual logic for this classification function
        was tested in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_conditional.call_args_list
        expected_calls = []
        current_historical = self.transformed_data_result['websocket'][
            'result']['data']['historical']['current']
        total_calls = 2 + (len(current_historical) * 2)
        self.assertEqual(total_calls, mock_conditional.call_count)
        current_amount = self.transformed_data_result['websocket']['result'][
            'data']['eras_stakers']['current']['total']
        previous_amount = self.transformed_data_result['websocket']['result'][
            'data']['eras_stakers']['previous']['total']
        bonded_amount_change_configs = configs.bonded_amount_change
        expected_calls.append(call(
            ValidatorBondedAmountChangedAlert,
            self.test_alerter._not_equal_condition_function,
            [current_amount, previous_amount],
            [self.test_node_name, current_amount, previous_amount,
             self.test_token_symbol, bonded_amount_change_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting))
        offline_configs = configs.offline
        slashed_configs = configs.slashed
        for block in current_historical:
            expected_calls.append(call(
                ValidatorWasOfflineAlert,
                self.test_alerter._is_true_condition_function,
                [block['is_offline']],
                [self.test_node_name, block['height'],
                 offline_configs['severity'], self.test_last_monitored,
                 self.test_parent_id, self.test_node_id], data_for_alerting))
            expected_calls.append(call(
                ValidatorWasSlashedAlert,
                self.test_alerter._is_true_condition_function,
                [block['slashed']],
                [self.test_node_name, block['slashed_amount'], block['height'],
                 self.test_token_symbol, slashed_configs['severity'],
                 self.test_last_monitored, self.test_parent_id,
                 self.test_node_id], data_for_alerting))
        current_controller_address = self.transformed_data_result['websocket'][
            'result']['data']['controller_address']['current']
        previous_controller_address = self.transformed_data_result['websocket'][
            'result']['data']['controller_address']['previous']
        controller_address_change_configs = configs.controller_address_change
        expected_calls.append(call(
            ValidatorControllerAddressChangedAlert,
            self.test_alerter._not_equal_condition_function,
            [current_controller_address, previous_controller_address],
            [self.test_node_name, current_controller_address,
             previous_controller_address,
             controller_address_change_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting))
        for expected_call in expected_calls:
            self.assertTrue(expected_call in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_solvable_conditional_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct solvable conditional
        classification function is called correctly by the
        process_websocket_result function. Note that the actual logic for this
        classification function was tested in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_solvable_conditional.call_args_list
        self.assertEqual(3, mock_solvable_conditional.call_count)
        current_active = self.transformed_data_result['websocket']['result'][
            'data']['active']['current']
        not_active_configs = configs.not_active_in_session
        call_1 = call(
            self.test_parent_id, self.test_node_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorIsNotActive,
            ValidatorIsNotActiveAlert,
            self.test_alerter._is_true_condition_function,
            [self.test_is_validator and not current_active],
            [self.test_node_name, not_active_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting, ValidatorIsActiveAlert,
            [self.test_node_name, Severity.INFO.value, self.test_last_monitored,
             self.test_parent_id, self.test_node_id])
        current_disabled = self.transformed_data_result['websocket']['result'][
            'data']['disabled']['current']
        is_disabled_configs = configs.is_disabled
        call_2 = call(
            self.test_parent_id, self.test_node_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorIsDisabled,
            ValidatorIsDisabledAlert,
            self.test_alerter._is_true_condition_function,
            [self.test_is_validator and current_disabled],
            [self.test_node_name, is_disabled_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting, ValidatorIsNoLongerDisabledAlert,
            [self.test_node_name, Severity.INFO.value, self.test_last_monitored,
             self.test_parent_id, self.test_node_id])
        current_elected = self.transformed_data_result['websocket']['result'][
            'data']['elected']['current']
        not_elected_configs = configs.not_elected
        call_3 = call(
            self.test_parent_id, self.test_node_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorWasNotElected,
            ValidatorWasNotElectedAlert,
            self.test_alerter._is_true_condition_function,
            [self.test_is_validator and not current_elected],
            [self.test_node_name, not_elected_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting, ValidatorWasElectedAlert,
            [self.test_node_name, Severity.INFO.value, self.test_last_monitored,
             self.test_parent_id, self.test_node_id])
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_thresholded_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct thresholded classification
        function is called correctly by the process_websocket_result function.
        Note that the actual logic for this classification function was tested
        in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_thresholded.call_args_list
        self.assertEqual(1, mock_thresholded.call_count)
        current_target_height = self.transformed_data_result['websocket'][
            'result']['data']['target_height']['current']
        current_best_height = self.transformed_data_result['websocket'][
            'result']['data']['best_height']['current']
        difference = current_target_height - current_best_height
        is_syncing_configs = (
            configs.validator_is_syncing if self.test_is_validator
            else configs.node_is_syncing
        )
        call_1 = call(
            difference, is_syncing_configs,
            NodeIsSyncingAlert, NodeIsNoLongerSyncingAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsSyncing.value,
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_no_change_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct no change classification
        function is called correctly by the process_websocket_result function.
        Note that the actual logic for this classification function was tested
        in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_no_change.call_args_list
        self.assertEqual(2, mock_no_change.call_count)
        current = self.transformed_data_result['websocket']['result']['data'][
            'best_height']['current']
        previous = self.transformed_data_result['websocket']['result']['data'][
            'best_height']['previous']
        no_change_in_best_block_configs = (
            configs.no_change_in_best_block_height_validator
            if self.test_is_validator
            else configs.no_change_in_best_block_height_node
        )
        call_1 = call(
            current, previous, no_change_in_best_block_configs,
            NoChangeInBestBlockHeightAlert,
            BestBlockHeightUpdatedAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, (GroupedSubstrateNodeAlertsMetricCode.
                                NoChangeInBestBlockHeight.value),
            self.test_node_name, self.test_last_monitored)
        current = self.transformed_data_result['websocket']['result']['data'][
            'finalized_height']['current']
        previous = self.transformed_data_result['websocket']['result']['data'][
            'finalized_height']['previous']
        no_change_in_finalized_block_configs = (
            configs.no_change_in_finalized_block_height_validator
            if self.test_is_validator
            else configs.no_change_in_finalized_block_height_node
        )
        call_2 = call(
            current, previous, no_change_in_finalized_block_configs,
            NoChangeInFinalizedBlockHeightAlert,
            FinalizedBlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            (GroupedSubstrateNodeAlertsMetricCode.
             NoChangeInFinalizedBlockHeight.value),
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_websocket_error_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_conditional_no_change_in_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_thresholded_era_alert")
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_era_solve_alert")
    def test_process_websocket_result_classifies_error_correctly_if_data_valid(
            self, mock_era_solve, mock_thresholded_era,
            mock_conditional_no_change, mock_conditional,
            mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct error classification
        function is called correctly by the process_websocket_result function.
        Note that the actual logic for this classification function was tested
        in the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_websocket_result(
            self.transformed_data_result['websocket']['result'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            SyncedSubstrateWebSocketDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored, (GroupedSubstrateNodeAlertsMetricCode
                                       .NoSyncedSubstrateWebSocketSource.value),
            "", "The monitor for {} found a websocket synced data "
                "source again.".format(self.test_node_name), None)
        call_2 = call(
            SubstrateWebSocketDataCouldNotBeObtained.code,
            SubstrateWebSocketDataCouldNotBeObtainedAlert,
            SubstrateWebSocketDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            (GroupedSubstrateNodeAlertsMetricCode
             .SubstrateWebSocketDataNotObtained.value), "",
            "The monitor for {} successfully retrieved websocket data "
            "again.".format(self.test_node_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    def test_process_websocket_error_does_nothing_if_config_not_received(
            self, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if websocket data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_websocket_error(
            self.transformed_data_general_error['websocket']['error'],
            data_for_alerting)

        mock_error_alert.assert_not_called()

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_websocket_error_alert")
    def test_process_websocket_error_classifies_correctly_if_data_valid(
            self, mock_error_alert) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_websocket_error function. Note that
        the actual logic for this classification function was tested in the
        alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_alerter._process_websocket_error(
            self.transformed_data_general_error['websocket']['error'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        error_msg = self.transformed_data_general_error['websocket']['error'][
            'message']
        error_code = self.transformed_data_general_error['websocket']['error'][
            'code']
        call_1 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            SyncedSubstrateWebSocketDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored, (GroupedSubstrateNodeAlertsMetricCode
                                       .NoSyncedSubstrateWebSocketSource.value),
            error_msg, "The monitor for {} found a websocket synced data "
                       "source again.".format(self.test_node_name), error_code)
        call_2 = call(
            SubstrateWebSocketDataCouldNotBeObtained.code,
            SubstrateWebSocketDataCouldNotBeObtainedAlert,
            SubstrateWebSocketDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            (GroupedSubstrateNodeAlertsMetricCode
             .SubstrateWebSocketDataNotObtained.value), error_msg,
            "The monitor for {} successfully retrieved websocket data "
            "again.".format(self.test_node_name), error_code)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @parameterized.expand([
        ("self.transformed_data_general_error",),
        ("self.transformed_data_result",),
        ("self.transformed_data_downtime_error",),
    ])
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_downtime_alert_with_substrate_api_downtime")
    def test_process_downtime_does_nothing_if_config_not_received(
            self, transformed_data, mock_downtime) -> None:
        """
        In this test we will check that no classification function is called
        if transformed data has been received for a node who's associated alerts
        configuration is not received yet. We will perform this test for
        multiple transformed_data types.
        """
        data_for_alerting = []
        self.test_alerter._process_downtime(eval(transformed_data),
                                            data_for_alerting)

        mock_downtime.assert_not_called()

    @parameterized.expand([
        ("self.transformed_data_general_error",),
        ("self.transformed_data_result",),
        ("self.transformed_data_downtime_error",),
    ])
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_downtime_alert_with_substrate_api_downtime")
    def test_process_downtime_does_not_classify_if_metrics_disabled(
            self, transformed_data, mock_downtime) -> None:
        """
        In this test we will check that no alert classification is done if
        source/node downtime is disabled from the configs.
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
        self.test_alerter._process_downtime(eval(transformed_data),
                                            data_for_alerting)

        mock_downtime.assert_not_called()

    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_downtime_alert")
    def test_process_downtime_classifies_node_downtime_if_websocket_source_down(
            self, mock_downtime) -> None:
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_downtime(
            self.transformed_data_downtime_error, data_for_alerting)

        downtime_configs = (
            configs.cannot_access_validator if self.test_is_validator
            else configs.cannot_access_node
        )
        mock_downtime.assert_called_once_with(
            self.test_last_monitored, downtime_configs,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, self.test_last_monitored)

    @parameterized.expand([
        ("self.transformed_data_result",),
        ("self.transformed_data_general_error",),
    ])
    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_downtime_alert_with_substrate_api_downtime")
    def test_process_downtime_classifies_correctly_if_no_source_down(
            self, transformed_data, mock_downtime) -> None:
        """
        In this test we will check that if not all sources are down, the
        process_downtime function attempts to classify for a node backup again
        alert and source downtime alert.
        """
        transformed_data = eval(transformed_data)

        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_downtime(transformed_data,
                                            data_for_alerting)

        calls = mock_downtime.call_args_list
        self.assertEqual(1, mock_downtime.call_count)
        downtime_configs = (
            configs.cannot_access_validator if self.test_is_validator
            else configs.cannot_access_node
        )
        call_1 = call(
            None, downtime_configs, NodeWentDownAtAlert, NodeStillDownAlert,
            NodeBackUpAgainAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, self.test_last_monitored)

        self.assertTrue(call_1 in calls)

    @parameterized.expand([
        ("self.transformed_data_general_error",),
        ("self.transformed_data_result",),
        ("self.transformed_data_downtime_error",),
    ])
    @mock.patch.object(SubstrateNodeAlertingFactory, "classify_error_alert")
    def test_process_substrate_api_error_does_nothing_if_config_not_received(
            self, transformed_data, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if transformed data has been received for a node who's associated alerts
        configuration is not received yet. We will perform this test for
        multiple transformed_data types.
        """
        data_for_alerting = []
        self.test_alerter._process_substrate_api_error(eval(transformed_data),
                                                       data_for_alerting)

        mock_error_alert.assert_not_called()

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_websocket_error_alert")
    def test_process_substrate_api_error_classifies_correctly_if_api_error(
            self, mock_error_alert) -> None:
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_alerter._process_substrate_api_error(
            self.transformed_data_substrate_api_error, data_for_alerting)
        error_msg = self.transformed_data_substrate_api_error['websocket'][
            'error']['message']
        error_code = self.transformed_data_substrate_api_error['websocket'][
            'error']['code']

        mock_error_alert.assert_called_once_with(
            SubstrateApiIsNotReachableException.code,
            SubstrateApiIsNotReachableAlert, SubstrateApiIsReachableAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, self.test_last_monitored,
            GroupedSubstrateNodeAlertsMetricCode.SubstrateApiNotReachable,
            error_msg, "The monitor for {} is now reaching the Substrate "
                       "API.".format(self.test_node_name), error_code)

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_websocket_error_alert")
    def test_process_substrate_api_error_classifies_correctly_if_other_error(
            self, mock_error_alert) -> None:
        """
        In this test we will check that if a non-substrate API error is
        present, the process_substrate_api_error function attempts to classify
        for a Substrate API is reachable alert.
        """
        transformed_data = self.transformed_data_general_error

        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_alerter._process_substrate_api_error(transformed_data,
                                                       data_for_alerting)
        error_msg = transformed_data['websocket']['error']['message']
        error_code = transformed_data['websocket']['error']['code']

        calls = mock_error_alert.call_args_list
        self.assertEqual(1, mock_error_alert.call_count)
        call_1 = call(
            SubstrateApiIsNotReachableException.code,
            SubstrateApiIsNotReachableAlert, SubstrateApiIsReachableAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, self.test_last_monitored,
            GroupedSubstrateNodeAlertsMetricCode.SubstrateApiNotReachable,
            error_msg, "The monitor for {} is now reaching the Substrate "
                       "API.".format(self.test_node_name), error_code)

        self.assertTrue(call_1 in calls)

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_websocket_error_alert")
    def test_process_substrate_api_error_classifies_correctly_if_no_errors(
            self, mock_error_alert) -> None:
        """
        In this test we will check that if there are no errors present, the
        process_substrate_api_error function attempts to classify for a
        Substrate API is reachable alert.
        """
        transformed_data = self.transformed_data_result

        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)

        data_for_alerting = []
        self.test_alerter._process_substrate_api_error(transformed_data,
                                                       data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(1, mock_error_alert.call_count)
        call_1 = call(
            SubstrateApiIsNotReachableException.code,
            SubstrateApiIsNotReachableAlert, SubstrateApiIsReachableAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, self.test_last_monitored,
            GroupedSubstrateNodeAlertsMetricCode.SubstrateApiNotReachable.value,
            "", "The monitor for {} is now reaching the Substrate API.".format(
                self.test_node_name), None)

        self.assertTrue(call_1 in calls)

    @mock.patch("src.alerter.alerters.node.substrate"
                ".transformed_data_processing_helper")
    @mock.patch.object(SubstrateNodeAlerter, "_process_downtime")
    @mock.patch.object(SubstrateNodeAlerter, "_process_substrate_api_error")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_calls_the_correct_process_fns_correctly(
            self, mock_basic_ack, mock_process_api_error,
            mock_process_downtime, mock_helper) -> None:
        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_process_api_error.assert_called_once_with(
            self.transformed_data_result, [])
        mock_process_downtime.assert_called_once_with(
            self.transformed_data_result, [])
        configuration = {
            'websocket': {
                'result': self.test_alerter._process_websocket_result,
                'error': self.test_alerter._process_websocket_error,
            },
        }
        mock_helper.assert_called_once_with(
            self.test_alerter_name, configuration, self.transformed_data_result,
            [])

    @mock.patch.object(SubstrateNodeAlerter, "_place_latest_data_on_queue")
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
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_called_once()

    @mock.patch.object(SubstrateNodeAlerter, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_place_alerts_on_queue_if_none(
            self, mock_basic_ack, mock_place_on_queue) -> None:
        # We will not be adding configs so that no alerts are generated

        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_not_called()

    @mock.patch.object(SubstrateNodeAlerter, "_process_downtime")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_raise_processing_error(
            self, mock_basic_ack, mock_process_downtime) -> None:
        """
        In this test we will generate an exception from one of the processing
        functions to see if an exception is raised.
        """
        mock_process_downtime.side_effect = self.test_exception

        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        try:
            self.test_alerter._process_transformed_data(method, body)
        except PANICException as e:
            self.fail('Did not expect {} to be raised.'.format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(SubstrateNodeAlerter, "_send_data")
    @mock.patch.object(SubstrateNodeAlerter, "_process_downtime")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_attempts_to_send_data_from_queue(
            self, mock_basic_ack, mock_process_downtime,
            mock_send_data) -> None:
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
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

        # Now do the test for when there are processing errors
        mock_basic_ack.reset_mock()
        mock_send_data.reset_mock()
        mock_process_downtime.side_effect = self.test_exception

        # Declare some fields for the process_transformed_data function
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(SubstrateNodeAlerter, "_send_data")
    @mock.patch.object(SubstrateNodeAlerter, "_send_heartbeat")
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
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        test_hb = {
            'component_name': self.test_alerter_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(test_hb)

    @freeze_time("2012-01-01")
    @mock.patch.object(SubstrateNodeAlerter, "_process_downtime")
    @mock.patch.object(SubstrateNodeAlerter, "_send_data")
    @mock.patch.object(SubstrateNodeAlerter, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_send_hb_if_processing_error(
            self, mock_basic_ack, mock_send_hb, mock_send_data,
            mock_process_downtime) -> None:
        # To avoid sending data
        mock_send_data.return_value = None

        # Generate error in processing
        mock_process_downtime.side_effect = self.test_exception

        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
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
    @mock.patch.object(SubstrateNodeAlerter, "_send_data")
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
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)

        self.assertRaises(exception_class,
                          self.test_alerter._process_transformed_data,
                          method, body)

        mock_basic_ack.assert_called_once()
