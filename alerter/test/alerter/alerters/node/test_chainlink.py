import datetime
import json
import logging
import unittest
from unittest import mock

import pika
from parameterized import parameterized

from src.alerter.alerters.node.chainlink import ChainlinkNodeAlerter
from src.alerter.factory.chainlink_node_alerting_factory import \
    ChainlinkNodeAlertingFactory
from src.configs.factory.chainlink_alerts_configs_factory import \
    ChainlinkAlertsConfigsFactory
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    CONFIG_EXCHANGE, CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    HEALTH_CHECK_EXCHANGE, ALERT_EXCHANGE, CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.env import RABBIT_IP
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
        self.test_queue_size = 100
        self.test_parent_id = 'test_parent_id'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test_data_str'
        self.test_configs_routing_key = 'chains.chainlink.bsc.alerts_config'

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
