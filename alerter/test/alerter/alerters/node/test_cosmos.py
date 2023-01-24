import copy
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
from src.alerter.alerters.node.cosmos import CosmosNodeAlerter
from src.alerter.alerts.node.cosmos import *
from src.alerter.factory.cosmos_node_alerting_factory import (
    CosmosNodeAlertingFactory)
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.configs.factory.alerts.cosmos_alerts import (
    CosmosNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.cosmos import BOND_STATUS_BONDED
from src.utils.constants.rabbitmq import (
    CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE, ALERT_EXCHANGE,
    COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY, COSMOS_NODE_ALERT_ROUTING_KEY)
from src.utils.env import RABBIT_IP
from src.utils.exceptions import (
    PANICException, NodeIsDownException, InvalidUrlException,
    MetricNotFoundException, NoSyncedDataSourceWasAccessibleException,
    CosmosRestServerDataCouldNotBeObtained, TendermintRPCDataCouldNotBeObtained)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit)


class TestCosmosNodeAlerter(unittest.TestCase):

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
        self.test_node_name = 'test_cosmos_node'
        self.test_node_id = 'test_cosmos_node_id345834t8h3r5893h8'
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.test_is_validator = True
        self.test_operator_address = 'test_address'
        self.test_exception = PANICException('test_exception', 1)
        self.test_node_is_down_exception = NodeIsDownException(
            self.test_node_name)
        self.test_is_mev_tendermint_node = False
        # Now we will construct the expected config objects
        self.received_configurations = {'DEFAULT': 'testing_if_will_be_deleted'}
        metrics_without_time_window = [
            'cannot_access_validator', 'cannot_access_node',
            'no_change_in_block_height_validator',
            'no_change_in_block_height_node', 'block_height_difference',
            'cannot_access_prometheus_validator',
            'cannot_access_prometheus_node',
            'cannot_access_cosmos_rest_validator',
            'cannot_access_cosmos_rest_node',
            'cannot_access_tendermint_rpc_validator',
            'cannot_access_tendermint_rpc_node',
        ]
        metrics_with_time_window = ['missed_blocks']
        severity_metrics = [
            'slashed', 'node_is_syncing', 'validator_is_syncing',
            'validator_not_active_in_session', 'validator_is_jailed',
            'node_is_peered_with_sentinel', 'validator_is_peered_with_sentinel',
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

        # Received transformed data examples
        self.transformed_data_result = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'current_height': {'current': 10000, 'previous': 34545},
                        'voting_power': {'current': 345456, 'previous': None},
                        'went_down_at': {'current': None, 'previous': None},
                    },
                }
            },
            'cosmos_rest': {
                'result': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'bond_status': {
                            'current': BOND_STATUS_BONDED,
                            'previous': None
                        },
                        'jailed': {
                            'current': False,
                            'previous': None
                        },
                        'went_down_at': {'current': None, 'previous': None},
                    },
                }
            },
            'tendermint_rpc': {
                'result': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'last_monitored': self.test_last_monitored,
                        'is_mev_tendermint_node': self.test_is_mev_tendermint_node,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'data': {
                        'slashed': {
                            'current': {
                                'slashed': True,
                                'amount_map': {
                                    '4500': 50.4,
                                    '4499': 23.4,
                                    '4498': None,
                                }
                            },
                            'previous': {
                                'slashed': False,
                                'amount_map': {}
                            }
                        },
                        'missed_blocks': {
                            'current': {
                                'total_count': 2,
                                'missed_heights': [4498, 4497]
                            },
                            'previous': {
                                'total_count': 0,
                                'missed_heights': []
                            },
                        },
                        'is_syncing': {'current': False, 'previous': None},
                        'went_down_at': {'current': None, 'previous': None},
                    },
                }
            }
        }

        self.transformed_data_result_mev = copy.deepcopy(self.transformed_data_result)
        self.transformed_data_result_mev['tendermint_rpc']['result']['meta_data']['is_mev_tendermint_node'] = not self.test_is_mev_tendermint_node
        self.transformed_data_result_mev['tendermint_rpc']['result']['data']['is_peered_with_sentinel'] = {
            'current': not self.test_is_mev_tendermint_node,
            'previous': None,
        }

        self.transformed_data_general_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node': self.test_is_mev_tendermint_node,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.transformed_data_downtime_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
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
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
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
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_node_name,
                        'node_id': self.test_node_id,
                        'node_parent_id': self.test_parent_id,
                        'time': self.test_last_monitored,
                        'is_mev_tendermint_node' : self.test_is_mev_tendermint_node,
                        'is_validator': self.test_is_validator,
                        'operator_address': self.test_operator_address,
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
        self.test_configs_factory = CosmosNodeAlertsConfigsFactory()
        self.test_alerting_factory = CosmosNodeAlertingFactory(
            self.dummy_logger)
        self.test_alerter = CosmosNodeAlerter(
            self.test_alerter_name, self.dummy_logger, self.rabbitmq,
            self.test_configs_factory, self.test_queue_size)

    def tearDown(self) -> None:
        connect_to_rabbit(self.test_alerter.rabbitmq)
        delete_queue_if_exists(self.test_alerter.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_alerter.rabbitmq,
                               COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
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
        self.rabbitmq.queue_delete(COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
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
            COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(0, res.method.message_count)
        self.test_alerter.rabbitmq.basic_publish_confirm(
            exchange=ALERT_EXCHANGE,
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str_1, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_alerter.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE, routing_key=self.test_configs_routing_key,
            body=self.test_data_str_2, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_alerter.rabbitmq.queue_declare(
            COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(2, res.method.message_count)

        # Check that the message contents are correct
        _, _, body = self.test_alerter.rabbitmq.basic_get(
            COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str_1, body.decode())
        _, _, body = self.test_alerter.rabbitmq.basic_get(
            COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str_2, body.decode())

        mock_basic_consume.assert_called_once()

    @parameterized.expand([
        (COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY, 'mock_proc_trans',),
        ('chains.cosmos.regen.alerts_config', 'mock_proc_confs',),
        ('unrecognized_routing_key', 'mock_basic_ack',),
    ])
    @mock.patch.object(CosmosNodeAlerter, "_process_transformed_data")
    @mock.patch.object(CosmosNodeAlerter, "_process_configs")
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

    @mock.patch.object(CosmosNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(CosmosNodeAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(CosmosNodeAlertingFactory, "remove_chain_alerting_state")
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
                                                   CosmosNodeAlertsConfig)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_ack.assert_called_once()

    @mock.patch.object(CosmosNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(CosmosNodeAlertsConfigsFactory, "remove_config")
    @mock.patch.object(CosmosNodeAlertingFactory, "remove_chain_alerting_state")
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
                                                   CosmosNodeAlertsConfig)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_remove_config.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(CosmosNodeAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(CosmosNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(CosmosNodeAlertsConfigsFactory, "remove_config")
    @mock.patch.object(CosmosNodeAlertingFactory, "remove_chain_alerting_state")
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
                                                   CosmosNodeAlertsConfig)
        mock_ack.assert_called_once()

    def test_place_latest_data_on_queue_places_data_on_queue_correctly(
            self) -> None:
        test_data = ['data_1', 'data_2']

        self.assertTrue(self.test_alerter.publishing_queue.empty())

        expected_data_1 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': COSMOS_NODE_ALERT_ROUTING_KEY,
            'data': 'data_1',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_2 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': COSMOS_NODE_ALERT_ROUTING_KEY,
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
                'routing_key': COSMOS_NODE_ALERT_ROUTING_KEY,
                'data': 'data_2',
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True
            }
            self.assertEqual(expected_data,
                             self.test_alerter.publishing_queue.get())

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_no_change_in_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_thresholded_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    def test_process_prometheus_result_does_nothing_if_config_not_received(
            self, mock_solvable_conditional, mock_thresholded, mock_no_change,
            mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if prometheus data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_prometheus_result(
            self.transformed_data_result['prometheus']['result'],
            data_for_alerting)

        mock_solvable_conditional.assert_not_called()
        mock_thresholded.assert_not_called()
        mock_no_change.assert_not_called()
        mock_error_alert.assert_not_called()

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_no_change_in_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_thresholded_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    def test_process_prometheus_result_does_not_classify_if_metrics_disabled(
            self, mock_solvable_conditional, mock_thresholded, mock_no_change,
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
        self.test_alerter._process_prometheus_result(
            self.transformed_data_result['prometheus']['result'],
            data_for_alerting)

        mock_solvable_conditional.assert_not_called()
        mock_thresholded.assert_not_called()
        mock_no_change.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            InvalidUrlException.code, PrometheusInvalidUrlAlert,
            PrometheusValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.PrometheusInvalidUrl.value, "",
            "Prometheus url is now valid!", None)
        call_2 = call(
            MetricNotFoundException.code, MetricNotFoundErrorAlert,
            MetricFoundAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.MetricNotFound.value, "",
            "All metrics found!", None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_no_change_in_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_thresholded_alert")
    def test_process_prometheus_result_classifies_correctly_if_data_valid(
            self, mock_thresholded, mock_no_change, mock_error_alert) -> None:
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
        self.test_alerter._process_prometheus_result(
            self.transformed_data_result['prometheus']['result'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        call_1 = call(
            InvalidUrlException.code, PrometheusInvalidUrlAlert,
            PrometheusValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.PrometheusInvalidUrl.value, "",
            "Prometheus url is now valid!", None)
        call_2 = call(
            MetricNotFoundException.code, MetricNotFoundErrorAlert,
            MetricFoundAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.MetricNotFound.value, "",
            "All metrics found!", None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

        calls = mock_no_change.call_args_list
        self.assertEqual(1, mock_no_change.call_count)
        current = self.transformed_data_result['prometheus']['result']['data'][
            'current_height']['current']
        previous = self.transformed_data_result['prometheus']['result']['data'][
            'current_height']['previous']
        no_change_in_configs = (
            configs.no_change_in_block_height_validator
            if self.test_is_validator
            else configs.no_change_in_block_height_node
        )
        call_1 = call(
            current, previous, no_change_in_configs, NoChangeInHeightAlert,
            BlockHeightUpdatedAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)

        calls = mock_thresholded.call_args_list
        self.assertEqual(1, mock_thresholded.call_count)
        call_1 = call(
            0, configs.block_height_difference,
            BlockHeightDifferenceIncreasedAboveThresholdAlert,
            BlockHeightDifferenceDecreasedBelowThresholdAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.BlockHeightDifferenceThreshold
                .value, self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    def test_process_prometheus_error_does_nothing_if_config_not_received(
            self, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if prometheus data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_prometheus_error(
            self.transformed_data_general_error['prometheus']['error'],
            data_for_alerting)

        mock_error_alert.assert_not_called()

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    def test_process_prometheus_error_classifies_correctly_if_data_valid(
            self, mock_error_alert) -> None:
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

        data_for_alerting = []
        self.test_alerter._process_prometheus_error(
            self.transformed_data_general_error['prometheus']['error'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(2, mock_error_alert.call_count)
        error_msg = self.transformed_data_general_error['prometheus']['error'][
            'message']
        error_code = self.transformed_data_general_error['prometheus']['error'][
            'code']
        call_1 = call(
            InvalidUrlException.code, PrometheusInvalidUrlAlert,
            PrometheusValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.PrometheusInvalidUrl.value,
            error_msg, "Prometheus url is now valid!", error_code)
        call_2 = call(
            MetricNotFoundException.code, MetricNotFoundErrorAlert,
            MetricFoundAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.MetricNotFound.value, error_msg,
            "All metrics found!", error_code)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    def test_process_cosmos_rest_result_does_nothing_if_config_not_received(
            self, mock_solvable_conditional, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if cosmos_rest data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_cosmos_rest_result(
            self.transformed_data_result['cosmos_rest']['result'],
            data_for_alerting)

        mock_solvable_conditional.assert_not_called()
        mock_error_alert.assert_not_called()

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    def test_process_cosmos_rest_result_does_not_classify_if_metrics_disabled(
            self, mock_solvable_conditional, mock_error_alert) -> None:
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

        mock_solvable_conditional.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(3, mock_error_alert.call_count)
        call_1 = call(
            InvalidUrlException.code, CosmosRestInvalidUrlAlert,
            CosmosRestValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.CosmosRestInvalidUrl.value, "",
            "Cosmos-Rest url is now valid!", None)
        call_2 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedCosmosRestDataSourcesAlert,
            SyncedCosmosRestDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.NoSyncedCosmosRestSource.value,
            "", "The monitor for {} found a Cosmos-Rest synced data source "
                "again".format(self.test_node_name), None)
        call_3 = call(
            CosmosRestServerDataCouldNotBeObtained.code,
            CosmosRestServerDataCouldNotBeObtainedAlert,
            CosmosRestServerDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.CosmosRestDataNotObtained.value,
            "", "The monitor for {} successfully retrieved Cosmos-Rest data "
                "again.".format(self.test_node_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    def test_process_cosmos_rest_result_classifies_correctly_if_data_valid(
            self, mock_solvable_conditional, mock_error_alert) -> None:
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
        self.assertEqual(3, mock_error_alert.call_count)
        call_1 = call(
            InvalidUrlException.code, CosmosRestInvalidUrlAlert,
            CosmosRestValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.CosmosRestInvalidUrl.value, "",
            "Cosmos-Rest url is now valid!", None)
        call_2 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedCosmosRestDataSourcesAlert,
            SyncedCosmosRestDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.NoSyncedCosmosRestSource.value,
            "", "The monitor for {} found a Cosmos-Rest synced data source "
                "again".format(self.test_node_name), None)
        call_3 = call(
            CosmosRestServerDataCouldNotBeObtained.code,
            CosmosRestServerDataCouldNotBeObtainedAlert,
            CosmosRestServerDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.CosmosRestDataNotObtained.value,
            "", "The monitor for {} successfully retrieved Cosmos-Rest data "
                "again.".format(self.test_node_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

        calls = mock_solvable_conditional.call_args_list
        self.assertEqual(2, mock_solvable_conditional.call_count)
        current = self.transformed_data_result['cosmos_rest']['result']['data'][
            'jailed']['current']
        jailed_configs = configs.validator_is_jailed
        call_1 = call(
            self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.ValidatorIsJailed.value,
            ValidatorIsJailedAlert,
            self.test_alerter._is_true_condition_function, [current],
            [self.test_node_name, jailed_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting, ValidatorIsNoLongerJailedAlert,
            [self.test_node_name, Severity.INFO.value, self.test_last_monitored,
             self.test_parent_id, self.test_node_id]
        )
        current = self.transformed_data_result['cosmos_rest']['result']['data'][
            'bond_status']['current']
        not_active_configs = configs.validator_not_active_in_session
        is_validator = self.transformed_data_result['cosmos_rest']['result'][
            'meta_data']['is_validator']
        call_2 = call(
            self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.ValidatorIsNotActive.value,
            ValidatorIsNotActiveAlert,
            self.test_alerter._node_is_not_active_condition_function,
            [is_validator, current],
            [self.test_node_name, not_active_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting, ValidatorIsActiveAlert,
            [self.test_node_name, Severity.INFO.value, self.test_last_monitored,
             self.test_parent_id, self.test_node_id]
        )
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
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

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
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
        self.assertEqual(3, mock_error_alert.call_count)
        error_msg = self.transformed_data_general_error['cosmos_rest']['error'][
            'message']
        error_code = self.transformed_data_general_error['cosmos_rest'][
            'error']['code']
        call_1 = call(
            InvalidUrlException.code, CosmosRestInvalidUrlAlert,
            CosmosRestValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.CosmosRestInvalidUrl.value,
            error_msg, "Cosmos-Rest url is now valid!", error_code)
        call_2 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedCosmosRestDataSourcesAlert,
            SyncedCosmosRestDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.NoSyncedCosmosRestSource.value,
            error_msg, "The monitor for {} found a Cosmos-Rest synced data "
                       "source again".format(self.test_node_name), error_code)
        call_3 = call(
            CosmosRestServerDataCouldNotBeObtained.code,
            CosmosRestServerDataCouldNotBeObtainedAlert,
            CosmosRestServerDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.CosmosRestDataNotObtained.value,
            error_msg, "The monitor for {} successfully retrieved Cosmos-Rest "
                       "data again.".format(self.test_node_name), error_code)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_conditional_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    def test_process_tendermint_rpc_result_does_nothing_if_config_not_received(
            self, mock_thresh_time, mock_conditional, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if tendermint_rpc data has been received for a node who's associated
        alerts configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_tendermint_rpc_result(
            self.transformed_data_result['tendermint_rpc']['result'],
            data_for_alerting)

        mock_conditional.assert_not_called()
        mock_error_alert.assert_not_called()
        mock_thresh_time.assert_not_called()

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_conditional_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    def test_process_tendermint_rpc_result_does_not_classify_if_metrics_disable(
            self, mock_thresh_time, mock_conditional, mock_error_alert) -> None:
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
        self.test_alerter._process_tendermint_rpc_result(
            self.transformed_data_result['tendermint_rpc']['result'],
            data_for_alerting)

        mock_thresh_time.assert_not_called()
        mock_conditional.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(3, mock_error_alert.call_count)
        call_1 = call(
            InvalidUrlException.code, TendermintRPCInvalidUrlAlert,
            TendermintRPCValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCInvalidUrl.value, "",
            "Tendermint-RPC url is now valid!", None)
        call_2 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedTendermintRPCDataSourcesAlert,
            SyncedTendermintRPCDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.NoSyncedTendermintRPCSource.value,
            "", "The monitor for {} found a Tendermint-RPC synced data source "
                "again".format(self.test_node_name), None)
        call_3 = call(
            TendermintRPCDataCouldNotBeObtained.code,
            TendermintRPCDataCouldNotBeObtainedAlert,
            TendermintRPCDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCDataNotObtained
                .value, "",
            "The monitor for {} successfully retrieved Tendermint-RPC data "
            "again.".format(self.test_node_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_conditional_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    def test_process_tendermint_rpc_result_classifies_correctly_if_data_valid(
            self, mock_solvable_conditional, mock_thresh_time, mock_conditional,
            mock_error_alert) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_tendermint_rpc_result function. Note
        that the actual logic for these classification functions was tested in
        the alert factory class.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_tendermint_rpc_result(
            self.transformed_data_result['tendermint_rpc']['result'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(3, mock_error_alert.call_count)
        call_1 = call(
            InvalidUrlException.code, TendermintRPCInvalidUrlAlert,
            TendermintRPCValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCInvalidUrl.value, "",
            "Tendermint-RPC url is now valid!", None)
        call_2 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedTendermintRPCDataSourcesAlert,
            SyncedTendermintRPCDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.NoSyncedTendermintRPCSource.value,
            "", "The monitor for {} found a Tendermint-RPC synced data source "
                "again".format(self.test_node_name), None)
        call_3 = call(
            TendermintRPCDataCouldNotBeObtained.code,
            TendermintRPCDataCouldNotBeObtainedAlert,
            TendermintRPCDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCDataNotObtained
                .value, "",
            "The monitor for {} successfully retrieved Tendermint-RPC data "
            "again.".format(self.test_node_name), None)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

        calls = mock_conditional.call_args_list
        self.assertEqual(3, mock_conditional.call_count)
        current = self.transformed_data_result['tendermint_rpc']['result'][
            'data']['slashed']['current']
        slashed_configs = configs.slashed
        call_1 = call(
            ValidatorWasSlashedAlert, self.test_alerter._true_fn, [],
            [self.test_node_name, current['amount_map']['4500'], 4500,
             slashed_configs['severity'], self.test_last_monitored,
             self.test_parent_id, self.test_node_id], data_for_alerting, None,
            None
        )
        call_2 = call(
            ValidatorWasSlashedAlert, self.test_alerter._true_fn, [],
            [self.test_node_name, current['amount_map']['4499'], 4499,
             slashed_configs['severity'], self.test_last_monitored,
             self.test_parent_id, self.test_node_id], data_for_alerting, None,
            None
        )
        call_3 = call(
            ValidatorWasSlashedAlert, self.test_alerter._true_fn, [],
            [self.test_node_name, current['amount_map']['4498'], 4498,
             slashed_configs['severity'], self.test_last_monitored,
             self.test_parent_id, self.test_node_id], data_for_alerting, None,
            None
        )
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

        calls = mock_thresh_time.call_args_list
        self.assertEqual(1, mock_thresh_time.call_count)
        current = self.transformed_data_result['tendermint_rpc']['result'][
            'data']['missed_blocks']['current']
        previous = self.transformed_data_result['tendermint_rpc']['result'][
            'data']['missed_blocks']['previous']
        missed_blocks_configs = configs.missed_blocks
        call_1 = call(
            current['total_count'], previous['total_count'],
            missed_blocks_configs, BlocksMissedIncreasedAboveThresholdAlert,
            BlocksMissedDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.BlocksMissedThreshold.value,
            self.test_node_name, self.test_last_monitored
        )
        self.assertTrue(call_1 in calls)

        calls = mock_solvable_conditional.call_args_list
        self.assertEqual(1, mock_solvable_conditional.call_count)
        is_syncing_configs = (
            configs.validator_is_syncing if self.test_is_validator
            else configs.node_is_syncing
        )
        current = self.transformed_data_result['tendermint_rpc']['result'][
            'data']['is_syncing']['current']
        call_1 = call(
            self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsSyncing.value,
            NodeIsSyncingAlert, self.test_alerter._is_true_condition_function,
            [current],
            [self.test_node_name, is_syncing_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting, NodeIsNoLongerSyncingAlert,
            [self.test_node_name, Severity.INFO.value,
             self.test_last_monitored, self.test_parent_id, self.test_node_id])
        self.assertTrue(call_1 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory,
                       "classify_solvable_conditional_alert_no_repetition")
    def test_process_tendermint_rpc_result_classify_sentinel_peering(
            self, mock_solvable_conditional) -> None:
        """
        In this test we will check that the classification functions for sentinel peering are triggered when the
        appropriate response fields exist.
        """
        # Add configs for the test data
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_alerter._process_tendermint_rpc_result(
            self.transformed_data_result_mev['tendermint_rpc']['result'],
            data_for_alerting)

        calls = mock_solvable_conditional.call_args_list
        self.assertEqual(2, mock_solvable_conditional.call_count)
        is_syncing_configs = (
            configs.validator_is_syncing if self.test_is_validator
            else configs.node_is_syncing
        )

         ## Test that the is_peered_with_sentinel call is in calls
        is_peered_with_sentinel_configs = (
            configs.validator_is_peered_with_sentinel if self.test_is_validator
            else configs.node_is_peered_with_sentinel
        )

        current = self.transformed_data_result['tendermint_rpc']['result'][
            'data']['is_syncing']['current']
        call_1 = call(
            self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsSyncing.value,
            NodeIsSyncingAlert, self.test_alerter._is_true_condition_function,
            [current],
            [self.test_node_name, is_syncing_configs['severity'],
             self.test_last_monitored, self.test_parent_id, self.test_node_id],
            data_for_alerting, NodeIsNoLongerSyncingAlert,
            [self.test_node_name, Severity.INFO.value,
             self.test_last_monitored, self.test_parent_id, self.test_node_id])
        self.assertTrue(call_1 in calls)

        current = self.transformed_data_result_mev['tendermint_rpc']['result']['data']['is_peered_with_sentinel']['current']
        call_2 = call(
            self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsNotPeeredWithSentinel.value,
            NodeIsNotPeeredWithSentinelAlert, self.test_alerter._is_false_condition_function,
            [current],
            [self.test_node_name, is_peered_with_sentinel_configs['severity'],
            self.test_last_monitored, self.test_parent_id, self.test_node_id], 
            data_for_alerting, NodeIsPeeredWithSentinelAlert,
           [self.test_node_name, Severity.INFO.value,
            self.test_last_monitored, self.test_parent_id, self.test_node_id])
        self.assertTrue(call_2 in calls)

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    def test_process_tendermint_rpc_error_does_nothing_if_config_not_received(
            self, mock_error_alert) -> None:
        """
        In this test we will check that no classification function is called
        if tendermint_rpc data has been received for a node who's associated
        alerts configuration is not received yet.
        """
        data_for_alerting = []
        self.test_alerter._process_tendermint_rpc_error(
            self.transformed_data_general_error['tendermint_rpc']['error'],
            data_for_alerting)

        mock_error_alert.assert_not_called()

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_error_alert")
    def test_process_tendermint_rpc_error_classifies_correctly_if_data_valid(
            self, mock_error_alert) -> None:
        """
        In this test we will check that the correct classification functions are
        called correctly by the process_tendermint_rpc_error function. Note that
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
        self.test_alerter._process_tendermint_rpc_error(
            self.transformed_data_general_error['tendermint_rpc']['error'],
            data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(3, mock_error_alert.call_count)
        error_msg = self.transformed_data_general_error['tendermint_rpc'][
            'error']['message']
        error_code = self.transformed_data_general_error['tendermint_rpc'][
            'error']['code']
        call_1 = call(
            InvalidUrlException.code, TendermintRPCInvalidUrlAlert,
            TendermintRPCValidUrlAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_node_name, self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCInvalidUrl.value,
            error_msg, "Tendermint-RPC url is now valid!", error_code)
        call_2 = call(
            NoSyncedDataSourceWasAccessibleException.code,
            ErrorNoSyncedTendermintRPCDataSourcesAlert,
            SyncedTendermintRPCDataSourcesFoundAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.NoSyncedTendermintRPCSource.value,
            error_msg, "The monitor for {} found a Tendermint-RPC synced data "
                       "source again".format(self.test_node_name), error_code)
        call_3 = call(
            TendermintRPCDataCouldNotBeObtained.code,
            TendermintRPCDataCouldNotBeObtainedAlert,
            TendermintRPCDataObtainedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCDataNotObtained
                .value, error_msg,
            "The monitor for {} successfully retrieved Tendermint-RPC data "
            "again.".format(self.test_node_name), error_code)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)

    @parameterized.expand([
        ("self.transformed_data_general_error",),
        ("self.transformed_data_result",),
        ("self.transformed_data_downtime_error",),
    ])
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_downtime_alert")
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
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_downtime_alert")
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

    @mock.patch.object(CosmosNodeAlertingFactory, "classify_downtime_alert")
    def test_process_downtime_classifies_node_downtime_if_all_sources_down(
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
            GroupedCosmosNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, self.test_last_monitored)

    @parameterized.expand([
        ("self.transformed_data_result",),
        ("self.transformed_data_general_error",),
    ])
    @mock.patch.object(CosmosNodeAlertingFactory, "classify_downtime_alert")
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
        self.assertEqual(4, mock_downtime.call_count)
        downtime_configs = (
            configs.cannot_access_validator if self.test_is_validator
            else configs.cannot_access_node
        )
        call_1 = call(
            None, downtime_configs, NodeWentDownAtAlert, NodeStillDownAlert,
            NodeBackUpAgainAlert, data_for_alerting, self.test_parent_id,
            self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, self.test_last_monitored)
        prometheus_down_configs = (
            configs.cannot_access_prometheus_validator if self.test_is_validator
            else configs.cannot_access_prometheus_node
        )
        call_2 = call(
            None, prometheus_down_configs, PrometheusSourceIsDownAlert,
            PrometheusSourceStillDownAlert, PrometheusSourceBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.PrometheusSourceIsDown.value,
            self.test_node_name, self.test_last_monitored)
        cosmos_rest_down_configs = (
            configs.cannot_access_cosmos_rest_validator
            if self.test_is_validator
            else configs.cannot_access_cosmos_rest_node
        )
        call_3 = call(
            None, cosmos_rest_down_configs, CosmosRestSourceIsDownAlert,
            CosmosRestSourceStillDownAlert, CosmosRestSourceBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.CosmosRestSourceIsDown.value,
            self.test_node_name, self.test_last_monitored)
        tendermint_rpc_down_configs = (
            configs.cannot_access_tendermint_rpc_validator
            if self.test_is_validator
            else configs.cannot_access_tendermint_rpc_node
        )
        call_4 = call(
            None, tendermint_rpc_down_configs, TendermintRPCSourceIsDownAlert,
            TendermintRPCSourceStillDownAlert,
            TendermintRPCSourceBackUpAgainAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCSourceIsDown.value,
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)
        self.assertTrue(call_2 in calls)
        self.assertTrue(call_3 in calls)
        self.assertTrue(call_4 in calls)

    @mock.patch("src.alerter.alerters.node.cosmos"
                ".transformed_data_processing_helper")
    @mock.patch.object(CosmosNodeAlerter, "_process_downtime")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_calls_the_correct_process_fns_correctly(
            self, mock_basic_ack, mock_process_downtime, mock_helper) -> None:
        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_process_downtime.assert_called_once_with(
            self.transformed_data_result, [])
        configuration = {
            'prometheus': {
                'result': self.test_alerter._process_prometheus_result,
                'error': self.test_alerter._process_prometheus_error,
            },
            'cosmos_rest': {
                'result': self.test_alerter._process_cosmos_rest_result,
                'error': self.test_alerter._process_cosmos_rest_error,
            },
            'tendermint_rpc': {
                'result': self.test_alerter._process_tendermint_rpc_result,
                'error': self.test_alerter._process_tendermint_rpc_error,
            },
        }
        mock_helper.assert_called_once_with(
            self.test_alerter_name, configuration, self.transformed_data_result,
            [])

    @mock.patch.object(CosmosNodeAlerter, "_place_latest_data_on_queue")
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
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_called_once()

    @mock.patch.object(CosmosNodeAlerter, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_place_alerts_on_queue_if_none(
            self, mock_basic_ack, mock_place_on_queue) -> None:
        # We will not be adding configs so that no alerts are generated

        # Declare some fields for the process_transformed_data function
        self.test_alerter._initialise_rabbitmq()
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        self.test_alerter._process_transformed_data(method, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_not_called()

    @mock.patch.object(CosmosNodeAlerter, "_process_downtime")
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
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)
        try:
            self.test_alerter._process_transformed_data(method, body)
        except PANICException as e:
            self.fail('Did not expect {} to be raised.'.format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(CosmosNodeAlerter, "_send_data")
    @mock.patch.object(CosmosNodeAlerter, "_process_downtime")
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
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
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
    @mock.patch.object(CosmosNodeAlerter, "_send_data")
    @mock.patch.object(CosmosNodeAlerter, "_send_heartbeat")
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
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
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
    @mock.patch.object(CosmosNodeAlerter, "_process_downtime")
    @mock.patch.object(CosmosNodeAlerter, "_send_data")
    @mock.patch.object(CosmosNodeAlerter, "_send_heartbeat")
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
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
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
    @mock.patch.object(CosmosNodeAlerter, "_send_data")
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
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_result)

        self.assertRaises(exception_class,
                          self.test_alerter._process_transformed_data,
                          method, body)

        mock_basic_ack.assert_called_once()
