import logging
import unittest
from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerts.node.chainlink import (
    NoChangeInHeightAlert, BlockHeightUpdatedAlert,
    TotalErroredJobRunsIncreasedAboveThresholdAlert,
    TotalErroredJobRunsDecreasedBelowThresholdAlert,
    MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
    MaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
    ChangeInSourceNodeAlert, PrometheusSourceIsDownAlert,
    PrometheusSourceBackUpAgainAlert, EthBalanceIncreasedAboveThresholdAlert,
    EthBalanceDecreasedBelowThresholdAlert, InvalidUrlAlert, ValidUrlAlert,
    NodeWentDownAtAlert, NodeBackUpAgainAlert, NodeStillDownAlert)
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.exceptions import InvalidUrlException, MetricNotFoundException
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)

"""
We will use some chainlink node alerts and configurations for the tests below.
This should not effect the validity and scope of the tests because the 
implementation was conducted to be as general as possible.
"""


class AlertingFactoryInstance(AlertingFactory):
    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)

    def create_alerting_state(
            self, parent_id: str, node_id: str,
            cl_node_alerts_config: ChainlinkNodeAlertsConfig) -> None:
        """
        This function is a smaller version of the ChainlinkNodeAlertingFactory
        create_alerting_state function
        """
        if parent_id not in self.alerting_state:
            self.alerting_state[parent_id] = {}

        if node_id not in self.alerting_state[parent_id]:
            warning_sent = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value: False,
                GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown:
                    False,
            }
            critical_sent = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value: False,
            }
            error_sent = {
                GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value: False,
            }

            current_head_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_node_alerts_config.head_tracker_current_head)
            eth_balance_thresholds = parse_alert_time_thresholds(
                ['critical_repeat'], cl_node_alerts_config.eth_balance_amount
            )
            node_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'], cl_node_alerts_config.node_is_down
            )
            error_jobs_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.run_status_update_total
            )
            unconfirmed_blocks_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.max_unconfirmed_blocks
            )
            warning_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['warning_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=unconfirmed_blocks_thresholds[
                            'warning_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    TimedTaskTracker(timedelta(seconds=node_is_down_thresholds[
                        'warning_threshold'])),
            }
            critical_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['critical_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=unconfirmed_blocks_thresholds[
                            'critical_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    TimedTaskTracker(timedelta(seconds=node_is_down_thresholds[
                        'critical_threshold'])),
            }
            critical_repeat_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskLimiter(timedelta(
                        seconds=current_head_thresholds['critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
                    TimedTaskLimiter(timedelta(seconds=eth_balance_thresholds[
                        'critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    TimedTaskLimiter(timedelta(seconds=node_is_down_thresholds[
                        'critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=unconfirmed_blocks_thresholds[
                            'critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value:
                    TimedTaskLimiter(timedelta(seconds=error_jobs_thresholds[
                        'critical_repeat'])),
            }
            warning_occurrences_in_period_tracker = {
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=error_jobs_thresholds[
                            'warning_time_window'])),
            }
            critical_occurrences_in_period_tracker = {
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=error_jobs_thresholds[
                            'critical_time_window'])),
            }

            self.alerting_state[parent_id][node_id] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
                'error_sent': error_sent,
                'warning_window_timer': warning_window_timer,
                'critical_window_timer': critical_window_timer,
                'critical_repeat_timer': critical_repeat_timer,
                'warning_occurrences_in_period_tracker':
                    warning_occurrences_in_period_tracker,
                'critical_occurrences_in_period_tracker':
                    critical_occurrences_in_period_tracker,
            }


class TestAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('dummy')
        self.test_alerting_state = {
            'test_key': 'test_val'
        }
        self.test_parent_id = 'chain_name_4569u540hg8d0fgd0f8th4050h_3464597'
        self.test_node_id = 'node_id34543496346t9345459-34689346h-3463-5'
        self.test_node_name = 'test_node_name'

        # Dummy test objects
        self.head_tracker_current_head = {
            'name': 'head_tracker_current_head',
            'parent_id': self.test_parent_id,
            'enabled': 'true',
            'critical_threshold': '7',
            'critical_repeat': '5',
            'critical_enabled': 'true',
            'critical_repeat_enabled': 'true',
            'warning_threshold': '3',
            'warning_enabled': 'true'
        }
        self.max_unconfirmed_blocks = {
            'name': 'max_unconfirmed_blocks',
            'parent_id': self.test_parent_id,
            'enabled': 'true',
            'critical_threshold': '5',
            'critical_repeat': '5',
            'critical_enabled': 'true',
            'critical_repeat_enabled': 'true',
            'warning_threshold': '3',
            'warning_enabled': 'true',
            'warning_time_window': '3',
            'critical_time_window': '7',
        }
        self.run_status_update_total = {
            'name': 'run_status_update_total',
            'parent_id': self.test_parent_id,
            'enabled': 'true',
            'critical_threshold': '5',
            'critical_repeat': '5',
            'critical_enabled': 'true',
            'critical_repeat_enabled': 'true',
            'warning_threshold': '3',
            'warning_enabled': 'true',
            'warning_time_window': '3',
            'critical_time_window': '7',
        }
        self.eth_balance_amount = {
            'name': 'eth_balance_amount',
            'parent_id': self.test_parent_id,
            'enabled': 'true',
            'critical_threshold': '5',
            'critical_repeat': '5',
            'critical_enabled': 'true',
            'critical_repeat_enabled': 'true',
            'warning_threshold': '10',
            'warning_enabled': 'true',
        }
        self.node_is_down = {
            'name': 'node_is_down',
            'parent_id': self.test_parent_id,
            'enabled': 'true',
            'critical_threshold': '5',
            'critical_repeat': '5',
            'critical_enabled': 'true',
            'critical_repeat_enabled': 'true',
            'warning_threshold': '3',
            'warning_enabled': 'true',
        }
        self.test_alerts_config = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id,
            head_tracker_current_head=self.head_tracker_current_head,
            head_tracker_heads_received_total={},
            max_unconfirmed_blocks=self.max_unconfirmed_blocks,
            process_start_time_seconds={},
            tx_manager_gas_bump_exceeds_limit_total={},
            unconfirmed_transactions={},
            run_status_update_total=self.run_status_update_total,
            eth_balance_amount=self.eth_balance_amount,
            eth_balance_amount_increase={}, node_is_down=self.node_is_down,
        )
        self.test_factory_instance = AlertingFactoryInstance(self.dummy_logger)
        self.test_factory_instance.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_alerts_config)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_alerts_config = None
        self.test_factory_instance = None

    def test_alerting_state_returns_alerting_state(self) -> None:
        self.test_factory_instance._alerting_state = self.test_alerting_state
        self.assertEqual(self.test_alerting_state,
                         self.test_factory_instance.alerting_state)

    def test_component_logger_returns_logger_instance(self) -> None:
        self.test_factory_instance._component_logger = self.dummy_logger
        self.assertEqual(self.dummy_logger,
                         self.test_factory_instance.component_logger)

    def test_classify_no_change_in_alert_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised and no timer is
        started whenever both warning and critical alerts are disabled. We will
        perform this test only for when current == previous. For an alert to be
        raised when current != previous it must be that one of the severities is
        enabled.
        """
        self.test_alerts_config.head_tracker_current_head[
            'warning_enabled'] = 'False'
        self.test_alerts_config.head_tracker_current_head[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )

        critical_window_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['critical_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value]
        warning_window_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['warning_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value]
        self.assertEqual([], data_for_alerting)
        self.assertFalse(critical_window_timer.timer_started)
        self.assertFalse(warning_window_timer.timer_started)

    def test_classify_no_change_does_nothing_if_change_and_no_issue_raised(
            self) -> None:
        """
        In this test we will check that no alert is raised if the value is being
        changed and no issue has been already reported.
        """
        data_for_alerting = []
        self.test_factory_instance.classify_no_change_in_alert(
            51, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('warning_threshold', 'WARNING',), ('critical_threshold', 'CRITICAL',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_no_change_in_alert_raises_alert_if_time_window_elapsed(
            self, threshold, severity) -> None:
        """
        In this test we will check that a warning/critical no change in alert is
        raised if the value is not being updated and the warning/critical time
        window elapses. We will also first check that no alert is raised first
        time round, (as the timer is started) and if the warning/critical time
        does not elapse.
        """
        data_for_alerting = []

        # No alert is raised if timer not started yet
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # No alert is raised if the time window is not elapsed yet
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # No change in alert is raised if time window elapsed
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = NoChangeInHeightAlert(
            self.test_node_name, pad, severity, alert_timestamp,
            self.test_parent_id, self.test_node_id, 50)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_no_change_in_alert_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        data_for_alerting = []

        # Set the timer
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )

        # Send warning alert
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        'warning_threshold'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))

        # Check that no alert is raised even if the warning window elapses again
        data_for_alerting.clear()
        alert_timestamp = datetime.now().timestamp() + (2 * pad)
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_no_change_in_alert_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical no change in alert is
        re-raised the critical window elapses. We will also check that if the
        critical window does not elapse, a critical alert is not re-raised.
        """
        data_for_alerting = []

        # Start timer
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )

        # First CRITICAL no change in alert
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        'critical_threshold'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        'critical_threshold']) + float(
            self.test_alerts_config.head_tracker_current_head[
                'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        'critical_threshold']) + float(
            self.test_alerts_config.head_tracker_current_head[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = NoChangeInHeightAlert(
            self.test_node_name, pad, 'CRITICAL', alert_timestamp,
            self.test_parent_id, self.test_node_id, 50)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_no_change_in_alert_only_1_critical_if_repeat_disabled(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a no
        change critical alert is not re-raised.
        """
        self.test_alerts_config.head_tracker_current_head[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # Start timer
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )

        # First CRITICAL no change in alert
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        'critical_threshold'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is
        # still not re-raised
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        'critical_threshold']) + float(
            self.test_alerts_config.head_tracker_current_head[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_threshold',), ('warning_threshold',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_no_change_alert_raises_info_if_issue_solved(
            self, threshold) -> None:
        """
        In this test we will check that once the no change problem is solved,
        an info alert is raised. We will perform this test for both when a
        warning alert has been sent or a critical alert has been sent.
        """
        data_for_alerting = []

        # Start timers
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # Raise problem alert
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_no_change_in_alert(
            50, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that an INFO alert is raised
        pad = float(self.test_alerts_config.head_tracker_current_head[
                        threshold])
        alert_timestamp = datetime.now().timestamp() + pad + 60
        self.test_factory_instance.classify_no_change_in_alert(
            51, 50, self.test_alerts_config.head_tracker_current_head,
            NoChangeInHeightAlert, BlockHeightUpdatedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = BlockHeightUpdatedAlert(
            self.test_node_name, 'INFO', alert_timestamp, self.test_parent_id,
            self.test_node_id, 51)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    def test_classify_thresh_time_win_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised and that no timer is
        starter whenever both warning and critical alerts are disabled. We will
        perform this test for both when current >= critical and
        current >= warning. For an alert to be raised when current < critical or
        current < warning it must be that one of the severities is enabled.
        """
        self.test_alerts_config.max_unconfirmed_blocks[
            'warning_enabled'] = 'False'
        self.test_alerts_config.max_unconfirmed_blocks[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = int(self.test_alerts_config.max_unconfirmed_blocks[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        warning_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['warning_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold.value]
        critical_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['critical_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold.value]
        self.assertEqual([], data_for_alerting)
        self.assertFalse(warning_timer.timer_started)
        self.assertFalse(critical_timer.timer_started)

    @parameterized.expand([
        ('warning_time_window', 'WARNING',),
        ('critical_time_window', 'CRITICAL',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_time_win_raises_alert_if_above_thresh_and_elapsed(
            self, threshold, severity) -> None:
        """
        In this test we will check that a warning/critical above threshold alert
        is raised if the time window above warning/critical threshold elapses.
        We will also first check that no alert is raised first time round,
        (as the timer is started) and if the warning/critical time does not
        elapse.
        """
        data_for_alerting = []

        # No alert is raised if timer not started yet
        current = int(self.test_alerts_config.max_unconfirmed_blocks[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # No alert is raised if the time window is not elapsed yet
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # Above threshold alert is raised if time window elapsed
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = MaxUnconfirmedBlocksIncreasedAboveThresholdAlert(
            self.test_node_name, current, severity, alert_timestamp, pad,
            severity, self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_time_win_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        data_for_alerting = []

        # Set the timer
        current = int(self.test_alerts_config.max_unconfirmed_blocks[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # Send warning alert
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'warning_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))

        # Check that no alert is raised even if the warning window elapses again
        data_for_alerting.clear()
        alert_timestamp = datetime.now().timestamp() + (2 * pad)
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_thresh_time_win_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical above threshold alert is
        re-raised if the critical window elapses. We will also check that if the
        critical window does not elapse, a critical alert is not re-raised.
        """
        data_for_alerting = []

        # Start timer
        current = int(self.test_alerts_config.max_unconfirmed_blocks[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First CRITICAL above threshold alert
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'critical_time_window']) + float(
            self.test_alerts_config.max_unconfirmed_blocks[
                'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'critical_time_window']) + float(
            self.test_alerts_config.max_unconfirmed_blocks[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = MaxUnconfirmedBlocksIncreasedAboveThresholdAlert(
            self.test_node_name, current, 'CRITICAL', alert_timestamp, pad,
            'CRITICAL', self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_time_win_only_1_critical_if_above_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, an
        increased abaove critical alert is not re-raised.
        """
        self.test_alerts_config.max_unconfirmed_blocks[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # Start timer
        current = int(self.test_alerts_config.max_unconfirmed_blocks[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First CRITICAL above threshold alert
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is
        # still not re-raised
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'critical_time_window']) + float(
            self.test_alerts_config.max_unconfirmed_blocks[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_threshold', 'critical_time_window', 'CRITICAL',),
        ('warning_threshold', 'warning_time_window', 'WARNING',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_time_win_info_alert_if_below_thresh_and_alert_sent(
            self, threshold, time_window_threshold, threshold_severity) -> None:
        """
        In this test we will check that once the current value is less than a
        threshold, a decreased below threshold info alert is sent. We will
        perform this test for both warning and critical.
        """
        data_for_alerting = []

        # Start timers
        current = int(self.test_alerts_config.max_unconfirmed_blocks[
                          threshold])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First above threshold alert
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        time_window_threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that an INFO alert is raised
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        time_window_threshold])
        alert_timestamp = datetime.now().timestamp() + pad + 60
        self.test_factory_instance.classify_thresholded_time_window_alert(
            0,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = MaxUnconfirmedBlocksDecreasedBelowThresholdAlert(
            self.test_node_name, 0, 'INFO', alert_timestamp,
            threshold_severity, self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_time_win_warn_alert_if_below_critical_above_warn(
            self) -> None:
        """
        In this test we will check that whenever
        warning <= current <= critical <= previous, a warning alert is raised to
        inform that the current value is greater than the critical value. Note
        we will perform this test for the case when we first alert warning, then
        critical and not immediately critical, as the warning alerting would be
        obvious.
        """
        data_for_alerting = []

        # Start times
        current = int(self.test_alerts_config.max_unconfirmed_blocks[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First above warning threshold alert
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'warning_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))

        # First above critical threshold alert
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual(2, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that 2 alerts are raised, below critical and above warning
        pad = float(self.test_alerts_config.max_unconfirmed_blocks[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad + 60
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current - 1,
            self.test_alerts_config.max_unconfirmed_blocks,
            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
            .value, self.test_node_name, alert_timestamp
        )
        expected_alert_1 = MaxUnconfirmedBlocksDecreasedBelowThresholdAlert(
            self.test_node_name, current - 1, 'INFO', alert_timestamp,
            'CRITICAL', self.test_parent_id, self.test_node_id)
        expected_alert_2 = MaxUnconfirmedBlocksIncreasedAboveThresholdAlert(
            self.test_node_name, current - 1, 'WARNING', alert_timestamp,
                                 pad + 60, 'WARNING', self.test_parent_id,
            self.test_node_id
        )
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    def test_classify_thresh_time_period_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised whenever both warning
        and critical alerts are disabled. We will perform this test for both
        when current_occurrences >= critical and current_occurrences >= warning.
        For an alert to be raised when current_occurrences < critical or
        current_occurrences < warning it must be that one of the severities is
        enabled.
        """
        self.test_alerts_config.run_status_update_total[
            'warning_enabled'] = 'False'
        self.test_alerts_config.run_status_update_total[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            100, 50,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('warning_time_window', 'WARNING', 'warning_threshold'),
        ('critical_time_window', 'CRITICAL', 'critical_threshold'),
    ])
    @freeze_time("2012-01-01")
    def test_classify_threshold_in_time_period_raises_alert_if_above_threshold(
            self, period_var, severity, threshold_var) -> None:
        """
        In this test we will check that a warning/critical above threshold alert
        is raised if the current value exceeds the warning/critical threshold.
        """
        current = int(
            self.test_alerts_config.run_status_update_total[
                threshold_var])
        previous = 0
        data_for_alerting = []

        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        period = float(
            self.test_alerts_config.run_status_update_total[
                period_var])
        expected_alert = TotalErroredJobRunsIncreasedAboveThresholdAlert(
            self.test_node_name, current, severity, datetime.now().timestamp(),
            period, severity, self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_threshold_time_period_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        data_for_alerting = []

        # Set the timer
        current = int(
            self.test_alerts_config.run_status_update_total[
                'warning_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current + 1, current,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
            .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_threshold_time_period_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical above threshold alert is
        re-raised if the critical repeat window elapses. We will also check that
        if the critical window does not elapse, a critical alert is not
        re-raised.
        """
        data_for_alerting = []

        # First critical above threshold alert
        current = int(
            self.test_alerts_config.run_status_update_total[
                'critical_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(
            self.test_alerts_config.run_status_update_total[
                'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(
            self.test_alerts_config.run_status_update_total[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, alert_timestamp
        )
        period = float(
            self.test_alerts_config.run_status_update_total[
                'critical_time_window'])
        expected_alert = TotalErroredJobRunsIncreasedAboveThresholdAlert(
            self.test_node_name, current, "CRITICAL", alert_timestamp, period,
            "CRITICAL", self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_threshold_time_per_only_1_critical_if_above_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, an
        increased above critical alert is not re-raised.
        """
        self.test_alerts_config.run_status_update_total[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical above threshold alert
        current = int(
            self.test_alerts_config.run_status_update_total[
                'critical_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = float(
            self.test_alerts_config.run_status_update_total[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_time_window', 'critical_threshold', 'CRITICAL',),
        ('warning_time_window', 'warning_threshold', 'WARNING',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_time_per_info_alert_if_below_thresh_and_alert_sent(
            self, period_var, threshold, threshold_severity) -> None:
        """
        In this test we will check that once the current value is less than a
        threshold, a decreased below threshold info alert is sent. We will
        perform this test for both warning and critical.
        """
        data_for_alerting = []

        # First above threshold alert
        current = int(
            self.test_alerts_config.run_status_update_total[
                threshold])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that a below threshold INFO alert is raised
        period = int(
            self.test_alerts_config.run_status_update_total[
                period_var])
        alert_timestamp = datetime.now().timestamp() + period + 1
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = TotalErroredJobRunsDecreasedBelowThresholdAlert(
            self.test_node_name, 0, 'INFO', alert_timestamp, period,
            threshold_severity, self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_time_per_warn_alert_if_below_critical_above_warn(
            self) -> None:
        """
        In this test we will check that whenever
        warning <= current <= critical <= previous, a warning alert is raised to
        inform that the current value is greater than the critical value. Note
        we will perform this test for the case when we first alert warning, then
        critical and not immediately critical, as the warning alerting would be
        obvious.
        """
        data_for_alerting = []

        # Send warning increase above threshold alert
        current = int(
            self.test_alerts_config.run_status_update_total[
                'warning_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))

        # Send critical increase above threshold alert
        previous = 0
        current = int(
            self.test_alerts_config.run_status_update_total[
                'critical_threshold'])
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(2, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that 2 alerts are raised, below critical and above warning
        critical_period = int(
            self.test_alerts_config.run_status_update_total[
                'critical_time_window'])
        warning_period = int(
            self.test_alerts_config.run_status_update_total[
                'warning_time_window'])
        current = int(
            self.test_alerts_config.run_status_update_total[
                'warning_threshold'])
        previous = 0

        # Allow a lot of time to pass so that all previous occurences are
        # automatically deleted, and we are thus above warning.
        alert_timestamp = datetime.now().timestamp() + critical_period + 100

        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.run_status_update_total,
            TotalErroredJobRunsIncreasedAboveThresholdAlert,
            TotalErroredJobRunsDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value, self.test_node_name, alert_timestamp
        )

        new_current = int(
            self.test_alerts_config.run_status_update_total[
                'warning_threshold'])
        expected_alert_1 = TotalErroredJobRunsDecreasedBelowThresholdAlert(
            self.test_node_name, new_current, 'INFO', alert_timestamp,
            critical_period, 'CRITICAL', self.test_parent_id, self.test_node_id)
        expected_alert_2 = TotalErroredJobRunsIncreasedAboveThresholdAlert(
            self.test_node_name, new_current, "WARNING", alert_timestamp,
            warning_period, "WARNING", self.test_parent_id, self.test_node_id)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    @freeze_time("2012-01-01")
    def test_classify_conditional_alert_raises_condition_true_alert_if_true(
            self) -> None:
        """
        Given a true condition, in this test we will check that the
        classify_conditional_alert fn calls the condition_true_alert
        """

        def condition_function(*args): return True

        data_for_alerting = []

        self.test_factory_instance.classify_conditional_alert(
            ChangeInSourceNodeAlert, condition_function, [], [
                self.test_node_name, 'new_source', 'WARNING',
                datetime.now().timestamp(), self.test_parent_id,
                self.test_node_id
            ], data_for_alerting
        )

        expected_alert_1 = ChangeInSourceNodeAlert(
            self.test_node_name, 'new_source', 'WARNING',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_conditional_alert_raises_condition_false_alert_if_false(
            self) -> None:
        """
        Given a false condition, in this test we will check that the
        classify_conditional_alert fn calls the condition_false_alert if it is
        not None.
        """

        def condition_function(*args): return False

        data_for_alerting = []

        self.test_factory_instance.classify_conditional_alert(
            PrometheusSourceIsDownAlert, condition_function, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id, self.test_node_id
            ], data_for_alerting, PrometheusSourceBackUpAgainAlert,
            [self.test_node_name, 'INFO', datetime.now().timestamp(),
             self.test_parent_id, self.test_node_id]
        )

        expected_alert_1 = PrometheusSourceBackUpAgainAlert(
            self.test_node_name, 'INFO', datetime.now().timestamp(),
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_conditional_alert_no_alert_if_no_false_alert_and_false(
            self) -> None:
        """
        Given a false condition and no condition_false_alert, in this test we
        will check that no alert is raised by the classify_conditional_alert fn.
        """

        def condition_function(*args): return False

        data_for_alerting = []

        self.test_factory_instance.classify_conditional_alert(
            PrometheusSourceIsDownAlert, condition_function, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id, self.test_node_id
            ], data_for_alerting
        )

        self.assertEqual([], data_for_alerting)

    def test_classify_thresholded_reverse_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised whenever both warning
        and critical alerts are disabled. We will perform this test for both
        when current <= critical and current <= warning. For an alert to be
        raised when current > critical or current > warning it must be that one
        of the severities is enabled.
        """
        self.test_alerts_config.eth_balance_amount[
            'warning_enabled'] = 'False'
        self.test_alerts_config.eth_balance_amount[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = float(self.test_alerts_config.eth_balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('WARNING', 'warning_threshold'),
        ('CRITICAL', 'critical_threshold'),
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresholded_reverse_raises_alert_if_below_threshold(
            self, severity, threshold_var) -> None:
        """
        In this test we will check that a warning/critical below threshold alert
        is raised if the current value goes below the warning/critical
        threshold.
        """
        data_for_alerting = []

        current = float(
            self.test_alerts_config.eth_balance_amount[threshold_var]) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        expected_alert = EthBalanceDecreasedBelowThresholdAlert(
            self.test_node_name, current, severity, datetime.now().timestamp(),
            severity, self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresholded_reverse_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        data_for_alerting = []

        # Send first warning alert
        current = float(
            self.test_alerts_config.eth_balance_amount['warning_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp() + 1
        )
        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_thresholded_reverse_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical below threshold alert is
        re-raised if the critical repeat window elapses. We will also check that
        if the critical window does not elapse, a critical alert is not
        re-raised.
        """
        data_for_alerting = []

        # First critical below threshold alert
        current = float(self.test_alerts_config.eth_balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(self.test_alerts_config.eth_balance_amount[
                        'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.test_alerts_config.eth_balance_amount[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = EthBalanceDecreasedBelowThresholdAlert(
            self.test_node_name, current, "CRITICAL", alert_timestamp,
            "CRITICAL", self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_threshold_reverse_only_1_critical_if_below_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        decreased below critical alert is not re-raised.
        """
        self.test_alerts_config.eth_balance_amount[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        current = float(self.test_alerts_config.eth_balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = float(self.test_alerts_config.eth_balance_amount[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_threshold', 'CRITICAL',),
        ('warning_threshold', 'WARNING',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_reverse_info_alert_if_above_thresh_and_alert_sent(
            self, threshold_var, threshold_severity) -> None:
        """
        In this test we will check that once the current value is greater than a
        threshold, an increased above threshold info alert is sent. We will
        perform this test for both warning and critical.
        """
        data_for_alerting = []

        # First below threshold alert
        current = float(self.test_alerts_config.eth_balance_amount[
                            threshold_var]) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that an above threshold INFO alert is raised. Current is set to
        # warning + 1 to not trigger a warning alert as it is expected that
        # critical <= warning.
        current = float(self.test_alerts_config.eth_balance_amount[
                            'warning_threshold']) + 1
        alert_timestamp = datetime.now().timestamp()
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = EthBalanceIncreasedAboveThresholdAlert(
            self.test_node_name, current, 'INFO', alert_timestamp,
            threshold_severity, self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_reverse_warn_alert_if_above_critical_below_warn(
            self) -> None:
        """
        In this test we will check that whenever
        warning >= current >= critical >= previous, a warning alert is raised to
        inform that the current value is smaller than the warning value. Note
        we will perform this test for the case when we first alert warning, then
        critical and not immediately critical, as the warning alerting would be
        obvious.
        """
        data_for_alerting = []

        # Send warning decrease below threshold alert
        current = float(self.test_alerts_config.eth_balance_amount[
                            'warning_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))

        # Send critical decrease below threshold alert
        current = float(self.test_alerts_config.eth_balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(2, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that 2 alerts are raised, above critical and below warning
        current = float(self.test_alerts_config.eth_balance_amount[
                            'critical_threshold']) + 1
        alert_timestamp = datetime.now().timestamp() + 10
        self.test_factory_instance.classify_thresholded_alert_reverse(
            current, self.test_alerts_config.eth_balance_amount,
            EthBalanceIncreasedAboveThresholdAlert,
            EthBalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )

        expected_alert_1 = EthBalanceIncreasedAboveThresholdAlert(
            self.test_node_name, current, 'INFO', alert_timestamp,
            'CRITICAL', self.test_parent_id, self.test_node_id)
        expected_alert_2 = EthBalanceDecreasedBelowThresholdAlert(
            self.test_node_name, current, 'WARNING', alert_timestamp,
            'WARNING', self.test_parent_id, self.test_node_id)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_error_alert_if_matched_error_codes(
            self) -> None:
        test_err = InvalidUrlException('test_url')
        data_for_alerting = []

        self.test_factory_instance.classify_error_alert(
            test_err.code, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, "error msg",
            "resolved msg", test_err.code
        )

        expected_alert = InvalidUrlAlert(
            self.test_node_name, 'error msg', 'ERROR',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_nothing_if_no_err_received_and_no_raised(
            self) -> None:
        test_err = InvalidUrlException('test_url')
        data_for_alerting = []

        self.test_factory_instance.classify_error_alert(
            test_err.code, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, "error msg",
            "resolved msg", None
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        (None,), (MetricNotFoundException('test-metric', 'test_url').code,),
    ])
    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_err_solved_if_alerted_and_no_error(
            self, code) -> None:
        """
        In this test we will check that an error solved alert is raised whenever
        no error is detected or a new error is detected after reporting a
        different error
        """
        test_err = InvalidUrlException('test_url')
        data_for_alerting = []

        # Generate first error alert
        self.test_factory_instance.classify_error_alert(
            test_err.code, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, "error msg",
            "resolved msg", test_err.code
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Generate solved alert
        alerted_timestamp = datetime.now().timestamp() + 10
        self.test_factory_instance.classify_error_alert(
            test_err.code, InvalidUrlAlert, ValidUrlAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            alerted_timestamp,
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value, "error msg",
            "resolved msg", code
        )

        expected_alert = ValidUrlAlert(
            self.test_node_name, 'resolved msg', 'INFO', alerted_timestamp,
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_downtime_alert_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised and no timer is
        started whenever both warning and critical alerts are disabled. We will
        perform this test for both when downtime >= critical_window and
        downtime >= warning_window.
        """
        self.test_alerts_config.node_is_down['warning_enabled'] = 'False'
        self.test_alerts_config.node_is_down['critical_enabled'] = 'False'

        data_for_alerting = []
        current_went_down = datetime.now().timestamp()
        alert_timestamp = \
            current_went_down + float(self.test_alerts_config.node_is_down[
                                          'critical_threshold'])
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )

        critical_window_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['critical_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value]
        warning_window_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['warning_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value]
        self.assertEqual([], data_for_alerting)
        self.assertFalse(critical_window_timer.timer_started)
        self.assertFalse(warning_window_timer.timer_started)

    @parameterized.expand([
        ('WARNING', 'warning_threshold'),
        ('CRITICAL', 'critical_threshold'),
    ])
    @freeze_time("2012-01-01")
    def test_classify_downtime_alert_raises_alert_if_above_time_window(
            self, severity, threshold_var) -> None:
        """
        In this test we will check that a warning/critical downtime alert is
        raised if downtime exceeds the warning/critical window. We will also 
        check that no alert is raised if the timer is not started or not elapsed
        """
        data_for_alerting = []
        current_went_down = datetime.now().timestamp()
        alert_timestamp = \
            current_went_down + float(self.test_alerts_config.node_is_down[
                                          threshold_var])

        # Start timer, no alert is raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, current_went_down
        )
        self.assertEqual([], data_for_alerting)

        # No alert is raised if the time window is not elapsed yet
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, current_went_down
        )
        self.assertEqual([], data_for_alerting)

        # A critical/warning downtime alert is now raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = NodeWentDownAtAlert(
            self.test_node_name, severity, alert_timestamp, self.test_parent_id,
            self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_downtime_alert_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        data_for_alerting = []
        current_went_down = datetime.now().timestamp()
        alert_timestamp = \
            current_went_down + float(self.test_alerts_config.node_is_down[
                                          'warning_threshold'])

        # Start timer, no alert is raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, current_went_down
        )

        # Raise a warning downtime alert is now raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Try to generate another warning alert. Confirm that none was raised.
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp + 10
        )

    @freeze_time("2012-01-01")
    def test_classify_downtime_alert_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical downtime alert is re-raised
        if the critical window elapses. We will also check that if the critical
        window does not elapse, a critical alert is not re-raised.
        """
        data_for_alerting = []
        current_went_down = datetime.now().timestamp()
        alert_timestamp = \
            current_went_down + float(self.test_alerts_config.node_is_down[
                                          'critical_threshold'])

        # Start timer, no alert is raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, current_went_down
        )

        # A first critical/warning downtime alert is now raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # No alert is re-raised if the repeat time is not elapsed
        alert_timestamp = \
            alert_timestamp + float(self.test_alerts_config.node_is_down[
                                        'critical_repeat'])
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp - 1
        )
        self.assertEqual([], data_for_alerting)

        # Critical alert is re-raised if the repeat time elapsed.
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        difference = alert_timestamp - current_went_down
        expected_alert = NodeStillDownAlert(
            self.test_node_name, difference, 'CRITICAL', alert_timestamp,
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_downtime_alert_only_1_critical_if_repeat_disabled(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        critical downtime alert is not re-raised.
        """
        self.test_alerts_config.node_is_down[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []
        current_went_down = datetime.now().timestamp()
        alert_timestamp = \
            current_went_down + float(self.test_alerts_config.node_is_down[
                                          'critical_threshold'])

        # Start timer, no alert is raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, current_went_down
        )

        # A first critical/warning downtime alert is now raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Critical alert is not re-raised if the repeat time elapsed.
        alert_timestamp = \
            alert_timestamp + float(self.test_alerts_config.node_is_down[
                                        'critical_repeat'])
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('warning_threshold',), ('critical_threshold',),
    ])
    @freeze_time("2012-01-01")
    def test_classify_downtime_alert_raises_info_if_node_is_back_up(
            self, threshold_var) -> None:
        """
        In this test we will check that an info alert is raised whenever a
        node is no longer down after it has been reported that it is down. We
        will perform this test for both critical and warning
        """
        data_for_alerting = []
        current_went_down = datetime.now().timestamp()
        alert_timestamp = \
            current_went_down + float(self.test_alerts_config.node_is_down[
                                          threshold_var])

        # Start timer, no alert is raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, current_went_down
        )

        # A first critical/warning downtime alert is now raised
        self.test_factory_instance.classify_downtime_alert(
            current_went_down, self.test_alerts_config.node_is_down,
            NodeWentDownAtAlert, NodeStillDownAlert, NodeBackUpAgainAlert,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Info back up again alert is raised if node is no longer down.
        alert_timestamp = alert_timestamp + 10
        self.test_factory_instance.classify_downtime_alert(
            None, self.test_alerts_config.node_is_down, NodeWentDownAtAlert,
            NodeStillDownAlert, NodeBackUpAgainAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = NodeBackUpAgainAlert(
            self.test_node_name, 'INFO', alert_timestamp, self.test_parent_id,
            self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    def test_classify_downtime_alert_does_nothing_if_node_is_never_down(
            self) -> None:
        """
        In this test we will check that no timer is started and no alert is
        raised if the node was and is not down.
        """
        data_for_alerting = []

        # Send data indicating that the node is not down, and check that no
        # alert is raised and that no timer is started.
        self.test_factory_instance.classify_downtime_alert(
            None, self.test_alerts_config.node_is_down, NodeWentDownAtAlert,
            NodeStillDownAlert, NodeBackUpAgainAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value,
            self.test_node_name, datetime.now().timestamp()
        )

        critical_window_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['critical_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value]
        warning_window_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['warning_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value]
        self.assertEqual([], data_for_alerting)
        self.assertFalse(critical_window_timer.timer_started)
        self.assertFalse(warning_window_timer.timer_started)

    """new"""

    @freeze_time("2012-01-01")
    def test_classify_source_downtime_alert_raises_condition_true_alert_if_true(
            self) -> None:
        """
        Given a true condition, in this test we will check that the
        classify_source_downtime_alert fn calls the condition_true_alert
        """

        def condition_function(*args): return True

        data_for_alerting = []

        self.test_factory_instance.classify_source_downtime_alert(
            PrometheusSourceIsDownAlert, condition_function, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id, self.test_node_id
            ], data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value,
            PrometheusSourceBackUpAgainAlert
        )

        expected_alert_1 = PrometheusSourceIsDownAlert(
            self.test_node_name, 'WARNING', datetime.now().timestamp(),
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_source_downtime_alert_raises_condition_false_alert_if_false_and_warning_sent(
            self) -> None:
        """
        Given a false condition, in this test we will check that the
        classify_source_downtime_alert fn calls the condition_false_alert if it
        is not None and a warning alert notifying the problem has already been
        sent.
        """

        def condition_function_true(*args): return True

        def condition_function_false(*args): return not condition_function_true(
            args)

        data_for_alerting = []

        # Send the warning alert first
        self.test_factory_instance.classify_source_downtime_alert(
            PrometheusSourceIsDownAlert, condition_function_true, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id, self.test_node_id
            ], data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value,
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        self.test_factory_instance.classify_source_downtime_alert(
            PrometheusSourceIsDownAlert, condition_function_false, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp() + 1,
                self.test_parent_id, self.test_node_id
            ], data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value,
            PrometheusSourceBackUpAgainAlert, [
                self.test_node_name, 'INFO', datetime.now().timestamp() + 1,
                self.test_parent_id, self.test_node_id
            ]
        )

        expected_alert_1 = PrometheusSourceBackUpAgainAlert(
            self.test_node_name, 'INFO', datetime.now().timestamp() + 1,
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_source_down_alert_no_alert_if_no_false_alert_and_false(
            self) -> None:
        """
        Given a false condition and no condition_false_alert, in this test we
        will check that no alert is raised by the classify_source_downtime_alert
        fn.
        """

        def condition_function_true(*args): return True

        def condition_function_false(*args): return not condition_function_true(
            args)

        data_for_alerting = []

        # Send the warning alert first
        self.test_factory_instance.classify_source_downtime_alert(
            PrometheusSourceIsDownAlert, condition_function_true, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id, self.test_node_id
            ], data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value,
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        self.test_factory_instance.classify_source_downtime_alert(
            PrometheusSourceIsDownAlert, condition_function_false, [], [
                self.test_node_name, 'INFO', datetime.now().timestamp() + 1,
                self.test_parent_id, self.test_node_id
            ], data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value,
        )

        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_source_down_alert_no_alert_if_warning_not_sent_and_false(
            self) -> None:
        """
        Given a false condition and that no warning alert has been sent, in this
        test we will check that no alert is raised by the
        classify_source_downtime_alert fn.
        """

        def condition_function_true(*args): return True

        def condition_function_false(*args): return not condition_function_true(
            args)

        data_for_alerting = []

        self.test_factory_instance.classify_source_downtime_alert(
            PrometheusSourceIsDownAlert, condition_function_false, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp() + 1,
                self.test_parent_id, self.test_node_id
            ], data_for_alerting, self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value,
            PrometheusSourceBackUpAgainAlert, [
                self.test_node_name, 'INFO', datetime.now().timestamp() + 1,
                self.test_parent_id, self.test_node_id
            ]
        )

        self.assertEqual([], data_for_alerting)
