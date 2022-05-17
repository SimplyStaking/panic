import copy
import logging
import unittest
from datetime import timedelta, datetime

from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerts.node.chainlink import (
    BalanceIncreasedAboveThresholdAlert, BalanceDecreasedBelowThresholdAlert)
from src.alerter.factory.chainlink_node_alerting_factory import \
    ChainlinkNodeAlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)


class TestChainlinkNodeAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data and objects
        self.dummy_logger = logging.getLogger('dummy')
        self.test_parent_id = 'test_parent_id'
        self.test_node_id = 'test_node_id'
        self.test_node_name = 'test_node_name'
        self.test_symbol = 'TEST'
        self.test_dummy_parent_id1 = 'dummy_parent_id1'
        self.test_dummy_node_id1 = 'dummy_node_id1'
        self.test_dummy_node_id2 = 'dummy_node_id2'
        self.test_dummy_state = 'dummy_state'

        # Construct the configs
        metrics_without_time_window = [
            'head_tracker_current_head', 'head_tracker_heads_received_total',
            'balance_amount', 'node_is_down'
        ]
        metrics_with_time_window = [
            'max_unconfirmed_blocks',
            'unconfirmed_transactions', 'run_status_update_total'
        ]
        severity_metrics = [
            'process_start_time_seconds',
            'tx_manager_gas_bump_exceeds_limit_total',
            'balance_amount_increase'
        ]

        filtered = {}
        for metric in metrics_without_time_window:
            filtered[metric] = {
                'name': metric,
                'parent_id': self.test_parent_id,
                'enabled': 'true',
                'critical_threshold': '5',
                'critical_repeat': '5',
                'critical_enabled': 'true',
                'critical_repeat_enabled': 'true',
                'warning_threshold': '10',
                'warning_enabled': 'true'
            }
        for metric in metrics_with_time_window:
            filtered[metric] = {
                'name': metric,
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
        for metric in severity_metrics:
            filtered[metric] = {
                'name': metric,
                'parent_id': self.test_parent_id,
                'enabled': 'true',
                'severity': 'WARNING'
            }

        self.test_alerts_config = ChainlinkNodeAlertsConfig(
            parent_id=self.test_parent_id,
            head_tracker_current_head=filtered[
                'head_tracker_current_head'],
            head_tracker_heads_received_total=filtered[
                'head_tracker_heads_received_total'],
            max_unconfirmed_blocks=filtered['max_unconfirmed_blocks'],
            process_start_time_seconds=filtered[
                'process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered[
                'unconfirmed_transactions'],
            run_status_update_total=filtered['run_status_update_total'],
            balance_amount=filtered['balance_amount'],
            balance_amount_increase=filtered[
                'balance_amount_increase'],
            node_is_down=filtered['node_is_down']
        )

        # Test object
        self.test_factory_instance = ChainlinkNodeAlertingFactory(
            self.dummy_logger)
        self.test_factory_instance.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_alerts_config)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_alerts_config = None
        self.test_factory_instance = None

    def test_create_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id and node_id.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node are updated
        self.test_factory_instance._alerting_state = {
            self.test_parent_id: {
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        warning_critical_sent_dict = {
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value: False,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInTotalHeadersReceived
                .value: False,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold
                .value: False,
            GroupedChainlinkNodeAlertsMetricCode.NoOfUnconfirmedTxsThreshold
                .value: False,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold
                .value: False,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value:
                False,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value: False,
        }

        warning_sent = copy.deepcopy(warning_critical_sent_dict)
        warning_sent[
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown.value
        ] = False
        critical_sent = copy.deepcopy(warning_critical_sent_dict)
        error_sent = {
            GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value: False,
            GroupedChainlinkNodeAlertsMetricCode.MetricNotFound.value:
                False,
        }

        current_head_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.test_alerts_config.head_tracker_current_head)
        total_headers_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.test_alerts_config.head_tracker_heads_received_total)
        unconfirmed_blocks_thresholds = parse_alert_time_thresholds(
            ['warning_time_window', 'critical_time_window', 'critical_repeat'],
            self.test_alerts_config.max_unconfirmed_blocks
        )
        unconfirmed_txs_thresholds = parse_alert_time_thresholds(
            ['warning_time_window', 'critical_time_window', 'critical_repeat'],
            self.test_alerts_config.unconfirmed_transactions
        )
        error_jobs_thresholds = parse_alert_time_thresholds(
            ['warning_time_window', 'critical_time_window', 'critical_repeat'],
            self.test_alerts_config.run_status_update_total
        )
        balance_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'], self.test_alerts_config.balance_amount
        )
        node_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.test_alerts_config.node_is_down
        )

        warning_window_timer = {
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                TimedTaskTracker(timedelta(
                    seconds=current_head_thresholds['warning_threshold'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoChangeInTotalHeadersReceived.value:
                TimedTaskTracker(timedelta(
                    seconds=total_headers_thresholds['warning_threshold'])),
            GroupedChainlinkNodeAlertsMetricCode.
                MaxUnconfirmedBlocksThreshold.value:
                TimedTaskTracker(
                    timedelta(seconds=unconfirmed_blocks_thresholds[
                        'warning_time_window'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoOfUnconfirmedTxsThreshold.value:
                TimedTaskTracker(
                    timedelta(seconds=unconfirmed_txs_thresholds[
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
                NoChangeInTotalHeadersReceived.value:
                TimedTaskTracker(timedelta(seconds=total_headers_thresholds[
                    'critical_threshold'])),
            GroupedChainlinkNodeAlertsMetricCode.
                MaxUnconfirmedBlocksThreshold.value:
                TimedTaskTracker(
                    timedelta(seconds=unconfirmed_blocks_thresholds[
                        'critical_time_window'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoOfUnconfirmedTxsThreshold.value:
                TimedTaskTracker(
                    timedelta(seconds=unconfirmed_txs_thresholds[
                        'critical_time_window'])),
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                TimedTaskTracker(timedelta(seconds=node_is_down_thresholds[
                    'critical_threshold'])),
        }
        critical_repeat_timer = {
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                TimedTaskLimiter(timedelta(
                    seconds=current_head_thresholds['critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoChangeInTotalHeadersReceived.value:
                TimedTaskLimiter(timedelta(
                    seconds=total_headers_thresholds['critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.
                MaxUnconfirmedBlocksThreshold.value:
                TimedTaskLimiter(
                    timedelta(seconds=unconfirmed_blocks_thresholds[
                        'critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoOfUnconfirmedTxsThreshold.value:
                TimedTaskLimiter(
                    timedelta(seconds=unconfirmed_txs_thresholds[
                        'critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.
                TotalErroredJobRunsThreshold.value:
                TimedTaskLimiter(
                    timedelta(seconds=error_jobs_thresholds[
                        'critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value:
                TimedTaskLimiter(timedelta(seconds=balance_thresholds[
                    'critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                TimedTaskLimiter(timedelta(seconds=node_is_down_thresholds[
                    'critical_repeat'])),
        }
        warning_occurrences_in_period_tracker = {
            GroupedChainlinkNodeAlertsMetricCode.
                TotalErroredJobRunsThreshold.value:
                OccurrencesInTimePeriodTracker(timedelta(
                    seconds=error_jobs_thresholds['warning_time_window'])),
        }
        critical_occurrences_in_period_tracker = {
            GroupedChainlinkNodeAlertsMetricCode.
                TotalErroredJobRunsThreshold.value:
                OccurrencesInTimePeriodTracker(timedelta(
                    seconds=error_jobs_thresholds['critical_time_window'])),
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
                    'warning_occurrences_in_period_tracker':
                        warning_occurrences_in_period_tracker,
                    'critical_occurrences_in_period_tracker':
                        critical_occurrences_in_period_tracker,
                },
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        self.test_factory_instance.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_alerts_config)

        self.assertDictEqual(
            expected_state, self.test_factory_instance.alerting_state)

    def test_create_alerting_state_does_not_modify_state_if_already_created(
            self) -> None:
        """
        In this test we will check that if a node's state is already created it
        cannot be overwritten.
        """
        self.test_factory_instance._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.test_factory_instance.alerting_state)

        self.test_factory_instance.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_alerts_config)

        self.assertEqual(expected_state,
                         self.test_factory_instance.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.test_factory_instance._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.test_factory_instance.alerting_state)
        del expected_state[self.test_parent_id]

        self.test_factory_instance.remove_chain_alerting_state(
            self.test_parent_id)
        self.assertEqual(expected_state,
                         self.test_factory_instance.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.test_factory_instance._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.test_factory_instance.alerting_state)

        self.test_factory_instance.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.test_factory_instance.alerting_state)

    def test_classify_thresholded_reverse_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised whenever both warning
        and critical alerts are disabled. We will perform this test for both
        when current <= critical and current <= warning. For an alert to be
        raised when current > critical or current > warning it must be that one
        of the severities is enabled.
        """
        self.test_alerts_config.balance_amount[
            'warning_enabled'] = 'False'
        self.test_alerts_config.balance_amount[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = float(self.test_alerts_config.balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
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
            self.test_alerts_config.balance_amount[threshold_var]) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        expected_alert = BalanceDecreasedBelowThresholdAlert(
            self.test_node_name, current, self.test_symbol, severity,
            datetime.now().timestamp(), severity, self.test_parent_id,
            self.test_node_id)
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
            self.test_alerts_config.balance_amount['warning_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
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
        current = float(self.test_alerts_config.balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(self.test_alerts_config.balance_amount[
                        'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.test_alerts_config.balance_amount[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = BalanceDecreasedBelowThresholdAlert(
            self.test_node_name, current, self.test_symbol, "CRITICAL",
            alert_timestamp, "CRITICAL", self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_threshold_reverse_only_1_critical_if_below_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        decreased below critical alert is not re-raised.
        """
        self.test_alerts_config.balance_amount[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        current = float(self.test_alerts_config.balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = float(self.test_alerts_config.balance_amount[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
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
        current = float(self.test_alerts_config.balance_amount[
                            threshold_var]) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that an above threshold INFO alert is raised. Current is set to
        # warning + 1 to not trigger a warning alert as it is expected that
        # critical <= warning.
        current = float(self.test_alerts_config.balance_amount[
                            'warning_threshold']) + 1
        alert_timestamp = datetime.now().timestamp()
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = BalanceIncreasedAboveThresholdAlert(
            self.test_node_name, current, self.test_symbol, 'INFO',
            alert_timestamp, threshold_severity, self.test_parent_id,
            self.test_node_id)
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
        current = float(self.test_alerts_config.balance_amount[
                            'warning_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))

        # Send critical decrease below threshold alert
        current = float(self.test_alerts_config.balance_amount[
                            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(2, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that 2 alerts are raised, above critical and below warning
        current = float(self.test_alerts_config.balance_amount[
                            'critical_threshold']) + 1
        alert_timestamp = datetime.now().timestamp() + 10
        self.test_factory_instance.classify_thresholded_alert_reverse_chainlink_node(
            current, self.test_alerts_config.balance_amount, 'TEST',
            BalanceIncreasedAboveThresholdAlert,
            BalanceDecreasedBelowThresholdAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold.value,
            self.test_node_name, alert_timestamp
        )

        expected_alert_1 = BalanceIncreasedAboveThresholdAlert(
            self.test_node_name, current, self.test_symbol, 'INFO',
            alert_timestamp, 'CRITICAL', self.test_parent_id, self.test_node_id)
        expected_alert_2 = BalanceDecreasedBelowThresholdAlert(
            self.test_node_name, current, self.test_symbol, 'WARNING',
            alert_timestamp, 'WARNING', self.test_parent_id, self.test_node_id)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])
