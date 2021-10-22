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

from src.alerter.alerters.node.evm import EVMNodeAlerter
from src.alerter.alerts.node.evm import (
    NoChangeInBlockHeight, BlockHeightUpdatedAlert,
    BlockHeightDifferenceIncreasedAboveThresholdAlert,
    BlockHeightDifferenceDecreasedBelowThresholdAlert,
    InvalidUrlAlert, ValidUrlAlert, NodeWentDownAtAlert,
    NodeBackUpAgainAlert, NodeStillDownAlert)
from src.alerter.factory.evm_node_alerting_factory import (
    EVMNodeAlertingFactory)
from src.alerter.grouped_alerts_metric_code.node.evm_node_metric_code \
    import GroupedEVMNodeAlertsMetricCode
from src.configs.alerts.node.evm import EVMNodeAlertsConfig
from src.configs.factory.node.evm_alerts import (
    EVMNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    CONFIG_EXCHANGE, EVM_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    HEALTH_CHECK_EXCHANGE, ALERT_EXCHANGE,
    EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    EVM_NODE_ALERT_ROUTING_KEY)
from src.utils.env import RABBIT_IP
from src.utils.exceptions import PANICException, NodeIsDownException
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit)


class TestEVMNodeAlerter(unittest.TestCase):
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
        self.test_node_name = 'test_evm_node'
        self.test_node_name_2 = 'test_evm_node_2'
        self.test_node_id = 'test_evm_node_id345834t8h3r5893h8'
        self.test_node_id_2 = 'test_evm_node_id345834t8h3r5893h8_2'
        # Some test metrics
        self.test_went_down_at = None
        self.test_current_height = 1000
        self.test_last_monitored = datetime.datetime(2012, 1, 1).timestamp()
        self.test_evm_node_is_down_exception = NodeIsDownException(
            self.test_node_name)
        # Construct received configurations
        self.received_configurations = {
            'DEFAULT': 'testing_if_will_be_deleted'
        }
        metrics_without_time_window = [
            'evm_block_syncing_no_change_in_block_height',
            'evm_block_syncing_block_height_difference',
            'evm_node_is_down'
        ]
        all_metrics = metrics_without_time_window

        for i in range(len(all_metrics)):
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

        self.test_current_height_1 = 100000
        self.test_current_height_2 = 200000
        self.test_difference_in_block_heights = 0
        self.test_result_data = {
            'meta_data': {
                'node_name': self.test_node_name,
                'node_id': self.test_node_id,
                'node_parent_id': self.test_parent_id,
                'last_monitored': self.test_last_monitored
            },
            'data': {
                'current_height': {
                    'current': self.test_current_height_1,
                    'previous': self.test_current_height_1 - 10
                },
                'syncing': {
                    'current': False,
                    'previous': False
                },
                'went_down_at': {
                    'current': self.test_last_monitored,
                    'previous': None,
                },
            },
        }

        self.test_node_down_error = {
            'meta_data': {
                'node_name': self.test_node_name,
                'node_id': self.test_node_id,
                'node_parent_id': self.test_parent_id,
                'time': self.test_last_monitored
            },
            'message': self.test_evm_node_is_down_exception.message,
            'code': self.test_evm_node_is_down_exception.code,
            'data': {'went_down_at': self.test_last_monitored + 60}
        }

        self.transformed_data_example_result = {
            'result': copy.deepcopy(self.test_result_data)
        }

        self.test_result_data_2 = copy.deepcopy(self.test_result_data)
        self.test_result_data_2['meta_data']['node_name'] = \
            self.test_node_name_2
        self.test_result_data_2['meta_data']['node_id'] = \
            self.test_node_id_2
        self.test_result_data_2['data']['current_height']['current'] = \
            self.test_current_height_1 - 900
        self.test_result_data_2['data']['current_height']['previous'] = \
            self.test_current_height_1 - 910
        self.transformed_data_example_result_2 = {
            'result': self.test_result_data_2
        }

        # Test object
        self.test_configs_factory = EVMNodeAlertsConfigsFactory()
        self.test_alerting_factory = EVMNodeAlertingFactory(
            self.dummy_logger)
        self.test_node_alerter = EVMNodeAlerter(
            self.test_alerter_name, self.dummy_logger,
            self.test_configs_factory,
            self.rabbitmq, self.test_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_node_alerter.rabbitmq)
        delete_queue_if_exists(self.test_node_alerter.rabbitmq,
                               self.test_queue_name)
        delete_queue_if_exists(self.test_node_alerter.rabbitmq,
                               EVM_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_node_alerter.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_node_alerter.rabbitmq,
                                  ALERT_EXCHANGE)
        delete_exchange_if_exists(self.test_node_alerter.rabbitmq,
                                  CONFIG_EXCHANGE)
        disconnect_from_rabbit(self.test_node_alerter.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_configs_factory = None
        self.alerting_factory = None
        self.test_node_alerter = None
        self.test_evm_node_is_down_exception = None

    def test_alerts_configs_factory_returns_alerts_configs_factory(
            self) -> None:
        self.test_node_alerter._alerts_configs_factory = \
            self.test_configs_factory
        self.assertEqual(self.test_configs_factory,
                         self.test_node_alerter.alerts_configs_factory)

    def test_alerting_factory_returns_alerting_factory(self) -> None:
        self.test_node_alerter._alerting_factory = self.test_alerting_factory
        self.assertEqual(self.test_alerting_factory,
                         self.test_node_alerter.alerting_factory)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already
        # established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.queue_delete(EVM_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        self.test_node_alerter._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_node_alerter.rabbitmq.is_connected)
        self.assertTrue(self.test_node_alerter.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_node_alerter.rabbitmq.channel._delivery_confirmation)

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_node_alerter.rabbitmq.exchange_declare(
            HEALTH_CHECK_EXCHANGE, passive=True)

        # Check whether the consuming exchanges and queues have been created
        # by sending messages to them. Since at this point these queues have
        # only the bindings from _initialise_rabbit, it must be that if no
        # exception is raised, then all queues and exchanges have been created
        # and binded correctly.
        self.test_node_alerter.rabbitmq.basic_publish_confirm(
            exchange=ALERT_EXCHANGE,
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_node_alerter.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE, routing_key=self.test_configs_routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

    @parameterized.expand([
        (EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY, 'mock_proc_trans',),
        ('chains.chainlink.bsc.alerts_config', 'mock_proc_confs',),
        ('unrecognized_routing_key', 'mock_basic_ack',),
    ])
    @mock.patch.object(EVMNodeAlerter, "_process_transformed_data")
    @mock.patch.object(EVMNodeAlerter, "_process_configs")
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

        self.test_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=routing_key)
        body = json.dumps(self.test_data_str)
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_data(blocking_channel, method,
                                             properties, body)

        eval(called_mock).assert_called_once()

    """
    In the majority of the tests below we will perform mocking. The tests for
    config processing and alerting were performed in separate test files which
    targeted the factory classes.
    """
    @mock.patch.object(EVMNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(EVMNodeAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(EVMNodeAlertingFactory, "remove_chain_alerting_state")
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

        self.test_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps(self.received_configurations)
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_configs(blocking_channel, method,
                                                properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_add_new_conf.assert_called_once_with(chain,
                                                  self.received_configurations)
        mock_get_parent_id.assert_called_once_with(chain)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_ack.assert_called_once()

    @mock.patch.object(EVMNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(EVMNodeAlertsConfigsFactory, "remove_config")
    @mock.patch.object(EVMNodeAlertingFactory, "remove_chain_alerting_state")
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

        self.test_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_configs(blocking_channel, method,
                                                properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        mock_get_parent_id.assert_called_once_with(chain)
        mock_remove_alerting_state.assert_called_once_with(self.test_parent_id)
        mock_remove_config.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(EVMNodeAlertsConfigsFactory, "add_new_config")
    @mock.patch.object(EVMNodeAlertsConfigsFactory, "get_parent_id")
    @mock.patch.object(EVMNodeAlertsConfigsFactory, "remove_config")
    @mock.patch.object(EVMNodeAlertingFactory, "remove_chain_alerting_state")
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

        self.test_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_configs(blocking_channel, method,
                                                properties, body)

        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        mock_remove_alerting_state.assert_not_called()
        mock_remove_conf.assert_not_called()
        mock_add_new_conf.assert_not_called()
        mock_get_parent_id.assert_called_once_with(chain)
        mock_ack.assert_called_once()

    @mock.patch.object(EVMNodeAlertsConfigsFactory, "get_parent_id")
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

        self.test_node_alerter.rabbitmq.connect()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_configs_routing_key)
        body = json.dumps(self.received_configurations)
        properties = pika.spec.BasicProperties()

        # Secondly test for when processing fails successful
        self.test_node_alerter._process_configs(blocking_channel, method,
                                                properties, body)
        mock_ack.assert_called_once()

    def test_place_latest_data_on_queue_places_data_on_queue_correctly(
            self) -> None:
        test_data = ['data_1', 'data_2']

        self.assertTrue(self.test_node_alerter.publishing_queue.empty())

        expected_data_1 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': EVM_NODE_ALERT_ROUTING_KEY,
            'data': 'data_1',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_2 = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': EVM_NODE_ALERT_ROUTING_KEY,
            'data': 'data_2',
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        self.test_node_alerter._place_latest_data_on_queue(test_data)
        self.assertEqual(2,
                         self.test_node_alerter.publishing_queue.qsize())
        self.assertEqual(expected_data_1,
                         self.test_node_alerter.publishing_queue.get())
        self.assertEqual(expected_data_2,
                         self.test_node_alerter.publishing_queue.get())

    def test_place_latest_data_on_queue_removes_old_data_if_full_then_places(
            self) -> None:
        # First fill the queue with the same data
        test_data_1 = ['data_1']
        for i in range(self.test_queue_size):
            self.test_node_alerter._place_latest_data_on_queue(test_data_1)

        # Now fill the queue with the second piece of data, and confirm that
        # now only the second piece of data prevails.
        test_data_2 = ['data_2']
        for i in range(self.test_queue_size):
            self.test_node_alerter._place_latest_data_on_queue(test_data_2)

        for i in range(self.test_queue_size):
            expected_data = {
                'exchange': ALERT_EXCHANGE,
                'routing_key': EVM_NODE_ALERT_ROUTING_KEY,
                'data': 'data_2',
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True
            }
            self.assertEqual(expected_data,
                             self.test_node_alerter.publishing_queue.get())

    @mock.patch.object(EVMNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_no_change_in_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_time_window_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_result_does_nothing_if_config_not_received(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_win_alert, mock_no_change_alert,
            mock_error_alert, mock_downtime_alert) -> None:
        """
        In this test we will check that no classification function is called
        if data has been received for a node who's associated alerts
        configuration is not received yet.
        """
        data_for_alerting = []
        self.test_node_alerter._process_result(self.test_result_data,
                                               data_for_alerting)

        mock_reverse.assert_not_called()
        mock_cond_alert.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_thresh_win_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()
        mock_error_alert.assert_not_called()
        mock_downtime_alert.assert_not_called()

    @mock.patch.object(EVMNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_no_change_in_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_time_window_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_result_does_not_classify_if_metrics_disabled(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_win_alert, mock_no_change_alert,
            mock_error_alert, mock_downtime_alert) -> None:
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
        self.test_node_alerter._process_result(self.test_result_data,
                                               data_for_alerting)

        mock_reverse.assert_not_called()
        mock_cond_alert.assert_not_called()
        mock_thresh_per_alert.assert_not_called()
        mock_thresh_win_alert.assert_not_called()
        mock_no_change_alert.assert_not_called()
        mock_downtime_alert.assert_not_called()

        calls = mock_error_alert.call_args_list
        self.assertEqual(1, mock_error_alert.call_count)
        call_1 = call(
            5009, InvalidUrlAlert,
            ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            self.test_node_name,
            self.test_last_monitored,
            GroupedEVMNodeAlertsMetricCode.InvalidUrl.value, "",
            "EVM URL is now valid!.", None)
        self.assertTrue(call_1 in calls)

    @mock.patch.object(EVMNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_no_change_in_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_result_classifies_correctly_if_data_valid(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_alert, mock_no_change_alert,
            mock_error_alert, mock_downtime_alert) -> None:
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

        data_for_alerting = []
        self.test_node_alerter._process_result(self.test_result_data,
                                               data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(1, mock_error_alert.call_count)
        call_1 = call(
            5009, InvalidUrlAlert,
            ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            self.test_node_name,
            self.test_last_monitored,
            GroupedEVMNodeAlertsMetricCode.InvalidUrl.value, "",
            "EVM URL is now valid!.", None)
        self.assertTrue(call_1 in calls)

        calls = mock_no_change_alert.call_args_list
        self.assertEqual(1, mock_no_change_alert.call_count)
        call_1 = call(
            self.test_current_height_1, self.test_current_height_1 - 10,
            configs.evm_block_syncing_no_change_in_block_height,
            NoChangeInBlockHeight, BlockHeightUpdatedAlert,
            data_for_alerting, self.test_parent_id,
            self.test_node_id,
            GroupedEVMNodeAlertsMetricCode.NoChangeInBlockHeight.value,
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)

        calls = mock_thresh_alert.call_args_list
        self.assertEqual(1, mock_thresh_alert.call_count)
        call_1 = call(
            self.test_difference_in_block_heights,
            configs.evm_block_syncing_block_height_difference,
            BlockHeightDifferenceIncreasedAboveThresholdAlert,
            BlockHeightDifferenceDecreasedBelowThresholdAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedEVMNodeAlertsMetricCode.BlockHeightDifference.value,
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)

        calls = mock_downtime_alert.call_args_list
        self.assertEqual(1, mock_downtime_alert.call_count)
        call_1 = call(
            None, configs.evm_node_is_down, NodeWentDownAtAlert,
            NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedEVMNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)

        mock_cond_alert.assert_not_called()
        mock_reverse.assert_not_called()
        mock_thresh_per_alert.assert_not_called()

    @mock.patch.object(EVMNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_error_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_no_change_in_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_in_time_period_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_conditional_alert")
    @mock.patch.object(EVMNodeAlertingFactory,
                       "classify_thresholded_alert_reverse")
    def test_process_result_classifies_correctly_if_data_valid_syncing_true(
            self, mock_reverse, mock_cond_alert, mock_thresh_per_alert,
            mock_thresh_alert, mock_no_change_alert,
            mock_error_alert, mock_downtime_alert) -> None:
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

        data_for_alerting = []
        self.test_result_data['data']['syncing']['current'] = True
        self.test_node_alerter._process_result(self.test_result_data,
                                               data_for_alerting)

        calls = mock_error_alert.call_args_list
        self.assertEqual(1, mock_error_alert.call_count)
        call_1 = call(
            5009, InvalidUrlAlert,
            ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            self.test_node_name,
            self.test_last_monitored,
            GroupedEVMNodeAlertsMetricCode.InvalidUrl.value, "",
            "EVM URL is now valid!.", None)
        self.assertTrue(call_1 in calls)

        calls = mock_downtime_alert.call_args_list
        self.assertEqual(1, mock_downtime_alert.call_count)
        call_1 = call(
            None, configs.evm_node_is_down, NodeWentDownAtAlert,
            NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedEVMNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, self.test_last_monitored)
        self.assertTrue(call_1 in calls)

        mock_no_change_alert.assert_not_called
        mock_thresh_alert.assert_not_called()
        mock_cond_alert.assert_not_called()
        mock_reverse.assert_not_called()
        mock_thresh_per_alert.assert_not_called()

    @mock.patch.object(EVMNodeAlertingFactory, "classify_downtime_alert")
    @mock.patch.object(EVMNodeAlertingFactory, "classify_error_alert")
    def test_process_error_classifies_correctly_if_data_valid(
            self, mock_error_alert, mock_downtime_alert) -> None:
        """
        In this test we will check that if we received an InvalidURL
        Exception then we should generate an alert for it.
        """
        parsed_routing_key = self.test_configs_routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        del self.received_configurations['DEFAULT']
        self.test_configs_factory.add_new_config(chain,
                                                 self.received_configurations)
        configs = self.test_configs_factory.configs[chain]

        data_for_alerting = []
        self.test_node_alerter._process_error(
            self.test_node_down_error, data_for_alerting)

        mock_error_alert.assert_called_once_with(
            5009,
            InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            self.test_last_monitored,
            GroupedEVMNodeAlertsMetricCode.InvalidUrl.value,
            self.test_evm_node_is_down_exception.message,
            "EVM URL is now valid!",
            self.test_evm_node_is_down_exception.code
        )
        meta_data = self.test_node_down_error['meta_data']
        mock_downtime_alert.assert_called_once_with(
            self.test_node_down_error['data']['went_down_at'],
            configs.evm_node_is_down, NodeWentDownAtAlert,
            NodeStillDownAlert, NodeBackUpAgainAlert, data_for_alerting,
            meta_data['node_parent_id'], meta_data['node_id'],
            GroupedEVMNodeAlertsMetricCode.NodeIsDown.value,
            meta_data['node_name'], meta_data['time']
        )

    @mock.patch.object(EVMNodeAlerter, "_place_latest_data_on_queue")
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
        self.test_node_alerter._initialise_rabbitmq()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_example_result)
        properties = pika.spec.BasicProperties()

        # Send data for first node
        self.test_node_alerter._process_transformed_data(
            blocking_channel, method, properties, body)
        mock_basic_ack.assert_called_once()

        # Send data for second node
        body_2 = json.dumps(self.transformed_data_example_result_2)
        self.test_node_alerter._process_transformed_data(
            blocking_channel, method, properties, body_2)
        self.assertEqual(2, mock_basic_ack.call_count)
        mock_place_on_queue.assert_called_once()

    @mock.patch.object(EVMNodeAlerter, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_place_alerts_on_queue_if_none(
            self, mock_basic_ack, mock_place_on_queue) -> None:
        # We will not be adding configs so that no alerts are generated

        # Declare some fields for the process_transformed_data function
        self.test_node_alerter._initialise_rabbitmq()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_example_result)
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        mock_place_on_queue.assert_not_called()

    @mock.patch.object(EVMNodeAlerter, "_process_result")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_raise_processing_error(
            self, mock_basic_ack, mock_process_result) -> None:
        """
        In this test we will generate an exception from one of the processing
        functions to see if an exception is raised.
        """
        mock_process_result.side_effect = self.test_evm_node_is_down_exception

        # Declare some fields for the process_transformed_data function
        self.test_node_alerter._initialise_rabbitmq()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_example_result)
        properties = pika.spec.BasicProperties()
        try:
            self.test_node_alerter._process_transformed_data(
                blocking_channel, method, properties, body)
        except PANICException as e:
            self.fail('Did not expect {} to be raised.'.format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(EVMNodeAlerter, "_send_data")
    @mock.patch.object(EVMNodeAlerter, "_process_result")
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
        self.test_node_alerter._initialise_rabbitmq()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_example_result)
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

        # Now do the test for when there are processing errors
        mock_basic_ack.reset_mock()
        mock_send_data.reset_mock()
        mock_process_result.side_effect = self.test_evm_node_is_down_exception

        # Declare some fields for the process_transformed_data function
        self.test_node_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        mock_send_data.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMNodeAlerter, "_send_data")
    @mock.patch.object(EVMNodeAlerter, "_send_heartbeat")
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

        self.test_node_alerter._initialise_rabbitmq()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_example_result)
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_transformed_data(
            blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
        test_hb = {
            'component_name': self.test_alerter_name,
            'is_alive': True,
            'timestamp': datetime.datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(test_hb)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMNodeAlerter, "_process_result")
    @mock.patch.object(EVMNodeAlerter, "_send_data")
    @mock.patch.object(EVMNodeAlerter, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_transformed_data_does_not_send_hb_if_processing_error(
            self, mock_basic_ack, mock_send_hb, mock_send_data,
            mock_process_result) -> None:
        # To avoid sending data
        mock_send_data.return_value = None

        # Generate error in processing
        mock_process_result.side_effect = self.test_evm_node_is_down_exception

        self.test_node_alerter._initialise_rabbitmq()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_example_result)
        properties = pika.spec.BasicProperties()
        self.test_node_alerter._process_transformed_data(
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
    @mock.patch.object(EVMNodeAlerter, "_send_data")
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

        self.test_node_alerter._initialise_rabbitmq()
        blocking_channel = self.test_node_alerter.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.transformed_data_example_result)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_class,
                          self.test_node_alerter._process_transformed_data,
                          blocking_channel, method, properties, body)

        mock_basic_ack.assert_called_once()
