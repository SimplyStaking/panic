import logging
import unittest
from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerts.node.chainlink import (NoChangeInHeightAlert,
                                               BlockHeightUpdatedAlert)
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
            }
            critical_sent = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value: False,
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

            warning_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['warning_threshold'])),
            }
            critical_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['critical_threshold'])),
            }
            critical_repeat_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskLimiter(timedelta(
                        seconds=current_head_thresholds['critical_repeat'])),
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
        self.test_alerts_config = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id,
            head_tracker_current_head=self.head_tracker_current_head,
            head_tracker_num_heads_dropped_total=
            self.head_tracker_num_heads_dropped_total,
            head_tracker_heads_in_queue={},
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
        In this test we will check that no alert is raised whenever both
        warning and critical alerts are disabled. We will perform this test only
        for when current == previous. For an alert to be raised when
        current != previous it must be that one of the severities is enabled.
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

        self.assertEqual([], data_for_alerting)

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
        self.assertTrue(1, len(data_for_alerting))
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
        self.assertTrue(1, len(data_for_alerting))
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
        self.assertTrue(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    def test_classify_thresh_time_win_does_nothing_warning_critical_disabled(
            self) -> None:
        pass

    def test_classify_thresh_time_win_raises_alert_if_above_thresh_and_elapsed(
            self) -> None:
        pass

    def test_classify_thresh_time_win_no_warning_if_warning_already_sent(
            self) -> None:
        pass

    def test_classify_thresh_time_win_raises_critical_if_repeat_elapsed(
            self) -> None:
        pass

    def test_classify_thresh_time_win_only_1_critical_if_above_and_no_repeat(
            self) -> None:
        pass

    def test_classify_thresh_time_win_info_alert_if_below_thresh_and_alert_sent(
            self) -> None:
        # TODO: Assume below warning as well for critical
        pass

    def test_classify_thresh_time_win_warn_alert_if_below_critical_above_warn(
            self) -> None:
        pass
