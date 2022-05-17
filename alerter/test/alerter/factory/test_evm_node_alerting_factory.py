import copy
import logging
import unittest
from datetime import timedelta

from src.alerter.factory.evm_node_alerting_factory import \
    EVMNodeAlertingFactory
from src.alerter.grouped_alerts_metric_code.node.evm_node_metric_code \
    import GroupedEVMNodeAlertsMetricCode as MetricCode
from src.configs.alerts.node.evm import EVMNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter)


class TestEVMNodeAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data and objects
        self.dummy_logger = logging.getLogger('dummy')
        self.test_parent_id = 'test_parent_id'
        self.test_node_id = 'test_node_id'
        self.test_dummy_parent_id1 = 'dummy_parent_id1'
        self.test_dummy_node_id1 = 'dummy_node_id1'
        self.test_dummy_node_id2 = 'dummy_node_id2'
        self.test_dummy_state = 'dummy_state'

        # Construct the configs
        metrics_without_time_window = [
            'evm_block_syncing_no_change_in_block_height',
            'evm_block_syncing_block_height_difference',
            'evm_node_is_down'
        ]

        filtered = {}
        for metric in metrics_without_time_window:
            filtered[metric] = {
                'name': metric,
                'parent_id': self.test_parent_id,
                'enabled': 'true',
                'critical_threshold': '7',
                'critical_repeat': '5',
                'critical_enabled': 'true',
                'critical_repeat_enabled': 'true',
                'warning_threshold': '3',
                'warning_enabled': 'true'
            }

        self.evm_node_alerts_config = EVMNodeAlertsConfig(
            parent_id=self.test_parent_id,
            evm_node_is_down=filtered['evm_node_is_down'],
            evm_block_syncing_block_height_difference=filtered[
                'evm_block_syncing_block_height_difference'],
            evm_block_syncing_no_change_in_block_height=filtered[
                'evm_block_syncing_no_change_in_block_height']
        )

        # Test object
        self.evm_node_alerting_factory = EVMNodeAlertingFactory(
            self.dummy_logger)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.evm_node_alerts_config = None
        self.evm_node_alerting_factory = None

    def test_create_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id and node_id.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node are updated
        self.evm_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        warning_critical_sent_dict = {
            MetricCode.NoChangeInBlockHeight.value: False,
            MetricCode.BlockHeightDifference.value: False,
            MetricCode.NodeIsDown.value: False
        }

        warning_sent = copy.deepcopy(warning_critical_sent_dict)
        critical_sent = copy.deepcopy(warning_critical_sent_dict)
        error_sent = {
            MetricCode.InvalidUrl.value: False,
        }

        evm_node_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.evm_node_alerts_config.evm_node_is_down)
        block_height_difference_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'],
            self.evm_node_alerts_config
                .evm_block_syncing_block_height_difference)
        no_change_in_block_height_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.evm_node_alerts_config
                .evm_block_syncing_no_change_in_block_height
        )

        warning_window_timer = {
            MetricCode.NoChangeInBlockHeight.value:
                TimedTaskTracker(timedelta(
                    seconds=no_change_in_block_height_thresholds[
                        'warning_threshold'])),
            MetricCode.NodeIsDown.value:
                TimedTaskTracker(timedelta(
                    seconds=evm_node_is_down_thresholds[
                        'warning_threshold'])),
        }
        critical_window_timer = {
            MetricCode.NoChangeInBlockHeight.value:
                TimedTaskTracker(timedelta(
                    seconds=no_change_in_block_height_thresholds[
                        'critical_threshold'])),
            MetricCode.NodeIsDown.value:
                TimedTaskTracker(timedelta(
                    seconds=evm_node_is_down_thresholds[
                        'critical_threshold'])),
        }
        critical_repeat_timer = {
            MetricCode.NoChangeInBlockHeight.value: TimedTaskLimiter(
                timedelta(seconds=no_change_in_block_height_thresholds[
                    'critical_repeat'])),
            MetricCode.NodeIsDown.value:
                TimedTaskLimiter(timedelta(
                    seconds=evm_node_is_down_thresholds[
                        'critical_repeat'])),
            MetricCode.BlockHeightDifference.value:
                TimedTaskLimiter(timedelta(
                    seconds=block_height_difference_thresholds[
                        'critical_repeat']))
        }

        expected_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'warning_sent': warning_sent,
                    'critical_sent': critical_sent,
                    'error_sent': error_sent,
                    'warning_window_timer': warning_window_timer,
                    'critical_window_timer': critical_window_timer,
                    'critical_repeat_timer': critical_repeat_timer,
                    'current_height': None,
                },
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        self.evm_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.evm_node_alerts_config)

        self.assertDictEqual(
            expected_state, self.evm_node_alerting_factory.alerting_state)

    def test_create_alerting_state_does_not_modify_state_if_already_created(
            self) -> None:
        """
        In this test we will check that if a node's state is already created it
        cannot be overwritten.
        """
        self.evm_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.evm_node_alerting_factory.alerting_state)

        self.evm_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.evm_node_alerts_config)

        self.assertEqual(expected_state,
                         self.evm_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.evm_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.evm_node_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id]

        self.evm_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)
        self.assertEqual(expected_state,
                         self.evm_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.evm_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.evm_node_alerting_factory.alerting_state)

        self.evm_node_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.evm_node_alerting_factory.alerting_state)
