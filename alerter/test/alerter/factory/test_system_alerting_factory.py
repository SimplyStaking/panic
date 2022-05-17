import copy
import logging
import unittest
from datetime import timedelta

from src.alerter.factory.system_alerting_factory import SystemAlertingFactory
from src.alerter.grouped_alerts_metric_code.system \
    import GroupedSystemAlertsMetricCode as MetricCode
from src.configs.alerts.system import SystemAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter)


class TestSystemAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data and objects
        self.dummy_logger = logging.getLogger('dummy')
        self.test_parent_id = 'test_parent_id'
        self.test_system_id = 'test_system_id'
        self.test_dummy_parent_id1 = 'dummy_parent_id1'
        self.test_dummy_system_id1 = 'dummy_system_id1'
        self.test_dummy_system_id2 = 'dummy_system_id2'
        self.test_dummy_state = 'dummy_state'

        # Construct the configs
        all_metrics = [
            'open_file_descriptors',
            'system_cpu_usage',
            'system_storage_usage',
            'system_ram_usage',
            'system_is_down'
        ]

        filtered = {}
        for metric in all_metrics:
            filtered[metric] = {
                'name': metric,
                'parent_id': self.test_parent_id,
                'enabled': 'true',
                'critical_threshold': '95',
                'critical_repeat': '300',
                'critical_enabled': 'true',
                'critical_repeat_enabled': 'true',
                'warning_threshold': '85',
                'warning_enabled': 'true'
            }

        self.system_alerts_config = SystemAlertsConfig(
            parent_id=self.test_parent_id,
            open_file_descriptors=filtered['open_file_descriptors'],
            system_cpu_usage=filtered['system_cpu_usage'],
            system_storage_usage=filtered['system_storage_usage'],
            system_ram_usage=filtered['system_ram_usage'],
            system_is_down=filtered['system_is_down']
        )

        # Test object
        self.system_alerting_factory = SystemAlertingFactory(self.dummy_logger)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.system_alerts_config = None
        self.system_alerting_factory = None

    def test_create_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id and system_id.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # system are updated
        self.system_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_dummy_system_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_system_id2: self.test_dummy_state
            }
        }
        warning_critical_sent_dict = {
            MetricCode.OpenFileDescriptorsThreshold.value: False,
            MetricCode.SystemCPUUsageThreshold.value: False,
            MetricCode.SystemStorageUsageThreshold.value: False,
            MetricCode.SystemRAMUsageThreshold.value: False,
            MetricCode.SystemIsDown.value: False
        }

        warning_sent = copy.deepcopy(warning_critical_sent_dict)
        critical_sent = copy.deepcopy(warning_critical_sent_dict)
        error_sent = {
            MetricCode.InvalidUrl.value: False,
            MetricCode.MetricNotFound.value: False,
        }

        open_file_descriptors_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.system_alerts_config.open_file_descriptors)
        system_cpu_usage_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.system_alerts_config.system_cpu_usage)
        system_ram_usage_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.system_alerts_config.system_ram_usage
        )
        system_storage_usage_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.system_alerts_config.system_storage_usage
        )
        system_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.system_alerts_config.system_is_down
        )

        warning_window_timer = {
            MetricCode.OpenFileDescriptorsThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=open_file_descriptors_thresholds[
                        'warning_threshold'])),
            MetricCode.SystemCPUUsageThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=system_cpu_usage_thresholds['warning_threshold']
                )),
            MetricCode.SystemRAMUsageThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=system_ram_usage_thresholds[
                        'warning_threshold'])),
            MetricCode.SystemStorageUsageThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=system_storage_usage_thresholds[
                        'warning_threshold'])),
            MetricCode.SystemIsDown.value: TimedTaskTracker(timedelta(
                seconds=system_is_down_thresholds['warning_threshold']))
        }
        critical_window_timer = {
            MetricCode.OpenFileDescriptorsThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=open_file_descriptors_thresholds[
                        'critical_threshold'])),
            MetricCode.SystemCPUUsageThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=system_cpu_usage_thresholds[
                        'critical_threshold'])),
            MetricCode.SystemRAMUsageThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=system_ram_usage_thresholds[
                        'critical_threshold'])),
            MetricCode.SystemStorageUsageThreshold.value:
                TimedTaskTracker(timedelta(
                    seconds=system_storage_usage_thresholds[
                        'critical_threshold'])),
            MetricCode.SystemIsDown.value: TimedTaskTracker(timedelta(
                seconds=system_is_down_thresholds['critical_threshold']))
        }
        critical_repeat_timer = {
            MetricCode.OpenFileDescriptorsThreshold.value:
                TimedTaskLimiter(timedelta(
                    seconds=open_file_descriptors_thresholds[
                        'critical_repeat'])),
            MetricCode.SystemCPUUsageThreshold.value:
                TimedTaskLimiter(timedelta(
                    seconds=system_cpu_usage_thresholds['critical_repeat'])
                ),
            MetricCode.SystemRAMUsageThreshold.value:
                TimedTaskLimiter(timedelta(
                    seconds=system_ram_usage_thresholds['critical_repeat'])
                ),
            MetricCode.SystemStorageUsageThreshold.value:
                TimedTaskLimiter(timedelta(
                    seconds=system_storage_usage_thresholds[
                        'critical_repeat'])),
            MetricCode.SystemIsDown.value: TimedTaskLimiter(timedelta(
                seconds=system_is_down_thresholds['critical_repeat']))
        }

        expected_state = {
            self.test_parent_id: {
                self.test_system_id: {
                    'warning_sent': warning_sent,
                    'critical_sent': critical_sent,
                    'error_sent': error_sent,
                    'warning_window_timer': warning_window_timer,
                    'critical_window_timer': critical_window_timer,
                    'critical_repeat_timer': critical_repeat_timer
                },
                self.test_dummy_system_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_system_id2: self.test_dummy_state
            }
        }

        self.system_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_system_id, self.system_alerts_config)

        self.assertDictEqual(
            expected_state, self.system_alerting_factory.alerting_state)

    def test_create_alerting_state_does_not_modify_state_if_already_created(
            self) -> None:
        """
        In this test we will check that a system's state cannot be overwritten
        if it has already been created.
        """
        self.system_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_system_id: self.test_dummy_state,
                self.test_dummy_system_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_system_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.system_alerting_factory.alerting_state)

        self.system_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_system_id, self.system_alerts_config)

        self.assertEqual(expected_state,
                         self.system_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.system_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_system_id: self.test_dummy_state,
                self.test_dummy_system_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_system_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.system_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id]

        self.system_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)
        self.assertEqual(expected_state,
                         self.system_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.system_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_system_id: self.test_dummy_state,
                self.test_dummy_system_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_system_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.system_alerting_factory.alerting_state)

        self.system_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.system_alerting_factory.alerting_state)
