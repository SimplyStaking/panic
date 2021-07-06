import logging
import unittest
from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerts.node.chainlink import (
    NoChangeInHeightAlert, BlockHeightUpdatedAlert,
    HeadsInQueueIncreasedAboveThresholdAlert,
    HeadsInQueueDecreasedBelowThresholdAlert,
    DroppedBlockHeadersIncreasedAboveThresholdAlert,
    DroppedBlockHeadersDecreasedBelowThresholdAlert, ChangeInSourceNodeAlert,
    PrometheusSourceIsDownAlert, PrometheusSourceBackUpAgainAlert)
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
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
                    DroppedBlockHeadersThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : False
            }
            critical_sent = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : False
            }
            error_sent = {
                GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value: False,
            }

            current_head_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_node_alerts_config.head_tracker_current_head)
            dropped_headers_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.head_tracker_num_heads_dropped_total
            )
            heads_in_queue_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.head_tracker_heads_in_queue)

            warning_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['warning_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : TimedTaskTracker(timedelta(
                    seconds=heads_in_queue_thresholds['warning_time_window']))
            }
            critical_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['critical_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : TimedTaskTracker(timedelta(
                    seconds=heads_in_queue_thresholds['critical_time_window'])),
            }
            critical_repeat_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskLimiter(timedelta(
                        seconds=current_head_thresholds['critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : TimedTaskLimiter(timedelta(
                    seconds=heads_in_queue_thresholds['critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=dropped_headers_thresholds['critical_repeat'])),
            }
            warning_occurrences_in_period_tracker = {
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=dropped_headers_thresholds[
                            'warning_time_window'])),
            }
            critical_occurrences_in_period_tracker = {
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=dropped_headers_thresholds[
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
        self.head_tracker_num_heads_dropped_total = {
            'name': 'head_tracker_num_heads_dropped_total',
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
        self.head_tracker_heads_in_queue = {
            'name': 'head_tracker_heads_in_queue',
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
        self.test_alerts_config = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id,
            head_tracker_current_head=self.head_tracker_current_head,
            head_tracker_num_heads_dropped_total=
            self.head_tracker_num_heads_dropped_total,
            head_tracker_heads_in_queue=self.head_tracker_heads_in_queue,
            head_tracker_heads_received_total={}, max_unconfirmed_blocks={},
            process_start_time_seconds={},
            tx_manager_gas_bump_exceeds_limit_total={},
            unconfirmed_transactions={}, run_status_update_total={},
            eth_balance_amount={}, eth_balance_amount_increase={},
            node_is_down={},
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
        :return:
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
        self.test_alerts_config.head_tracker_heads_in_queue[
            'warning_enabled'] = 'False'
        self.test_alerts_config.head_tracker_heads_in_queue[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = int(self.test_alerts_config.head_tracker_heads_in_queue[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        warning_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['warning_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value]
        critical_timer = self.test_factory_instance.alerting_state[
            self.test_parent_id][self.test_node_id]['critical_window_timer'][
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value]
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
        current = int(self.test_alerts_config.head_tracker_heads_in_queue[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # No alert is raised if the time window is not elapsed yet
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # Above threshold alert is raised if time window elapsed
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = HeadsInQueueIncreasedAboveThresholdAlert(
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
        current = int(self.test_alerts_config.head_tracker_heads_in_queue[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # Send warning alert
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'warning_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )

        # Check that no alert is raised even if the warning window elapses again
        data_for_alerting.clear()
        alert_timestamp = datetime.now().timestamp() + (2 * pad)
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
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
        current = int(self.test_alerts_config.head_tracker_heads_in_queue[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First CRITICAL above threshold alert
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'critical_time_window']) + float(
            self.test_alerts_config.head_tracker_heads_in_queue[
                'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'critical_time_window']) + float(
            self.test_alerts_config.head_tracker_heads_in_queue[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = HeadsInQueueIncreasedAboveThresholdAlert(
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
        self.test_alerts_config.head_tracker_heads_in_queue[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # Start timer
        current = int(self.test_alerts_config.head_tracker_heads_in_queue[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First CRITICAL above threshold alert
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is
        # still not re-raised
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'critical_time_window']) + float(
            self.test_alerts_config.head_tracker_heads_in_queue[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
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
        current = int(self.test_alerts_config.head_tracker_heads_in_queue[
                          threshold])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First above threshold alert
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        time_window_threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        data_for_alerting.clear()

        # Check that an INFO alert is raised
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        time_window_threshold])
        alert_timestamp = datetime.now().timestamp() + pad + 60
        self.test_factory_instance.classify_thresholded_time_window_alert(
            0,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = HeadsInQueueDecreasedBelowThresholdAlert(
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
        current = int(self.test_alerts_config.head_tracker_heads_in_queue[
                          'critical_threshold'])
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # First above warning threshold alert
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'warning_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )

        # First above critical threshold alert
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
                .value, self.test_node_name, alert_timestamp
        )
        data_for_alerting.clear()

        # Check that 2 alerts are raised, below critical and above warning
        pad = float(self.test_alerts_config.head_tracker_heads_in_queue[
                        'critical_time_window'])
        alert_timestamp = datetime.now().timestamp() + pad + 60
        self.test_factory_instance.classify_thresholded_time_window_alert(
            current - 1,
            self.test_alerts_config.head_tracker_heads_in_queue,
            HeadsInQueueIncreasedAboveThresholdAlert,
            HeadsInQueueDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold
            .value, self.test_node_name, alert_timestamp
        )
        expected_alert_1 = HeadsInQueueDecreasedBelowThresholdAlert(
            self.test_node_name, current - 1, 'INFO', alert_timestamp,
            'CRITICAL', self.test_parent_id, self.test_node_id)
        expected_alert_2 = HeadsInQueueIncreasedAboveThresholdAlert(
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
        self.test_alerts_config.head_tracker_num_heads_dropped_total[
            'warning_enabled'] = 'False'
        self.test_alerts_config.head_tracker_num_heads_dropped_total[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            100, 50,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
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
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                threshold_var])
        previous = 0
        data_for_alerting = []

        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        period = float(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                period_var])
        expected_alert = DroppedBlockHeadersIncreasedAboveThresholdAlert(
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
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'warning_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        data_for_alerting.clear()

        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current + 1, current,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
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
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, alert_timestamp
        )
        period = float(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_time_window'])
        expected_alert = DroppedBlockHeadersIncreasedAboveThresholdAlert(
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
        self.test_alerts_config.head_tracker_num_heads_dropped_total[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical above threshold alert
        current = int(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = float(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
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
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                threshold])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        data_for_alerting.clear()

        # Check that a below threshold INFO alert is raised
        period = int(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                period_var])
        alert_timestamp = datetime.now().timestamp() + period + 1
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, current,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, alert_timestamp
        )
        expected_alert = DroppedBlockHeadersDecreasedBelowThresholdAlert(
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
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'warning_threshold'])
        previous = 0
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )

        # Send critical increase above threshold alert
        previous = 0
        current = int(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_threshold'])
        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, datetime.now().timestamp()
        )
        data_for_alerting.clear()

        # Check that 2 alerts are raised, below critical and above warning
        critical_period = int(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'critical_time_window'])
        warning_period = int(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'warning_time_window'])
        current = int(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'warning_threshold'])
        previous = 0

        # Allow a lot of time to pass so that all previous occurences are
        # automatically deleted, and we are thus above warning.
        alert_timestamp = datetime.now().timestamp() + critical_period + 100

        self.test_factory_instance.classify_thresholded_in_time_period_alert(
            current, previous,
            self.test_alerts_config.head_tracker_num_heads_dropped_total,
            DroppedBlockHeadersIncreasedAboveThresholdAlert,
            DroppedBlockHeadersDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold
                .value, self.test_node_name, alert_timestamp
        )

        new_current = int(
            self.test_alerts_config.head_tracker_num_heads_dropped_total[
                'warning_threshold'])
        expected_alert_1 = DroppedBlockHeadersDecreasedBelowThresholdAlert(
            self.test_node_name, new_current, 'INFO', alert_timestamp,
            critical_period, 'CRITICAL', self.test_parent_id, self.test_node_id)
        expected_alert_2 = DroppedBlockHeadersIncreasedAboveThresholdAlert(
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
            ], data_for_alerting, PrometheusSourceBackUpAgainAlert
        )

        expected_alert_1 = PrometheusSourceBackUpAgainAlert(
            self.test_node_name, 'WARNING', datetime.now().timestamp(),
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
