import copy
import logging
import unittest
from datetime import timedelta

from src.alerter.factory.chainlink_node_alerting_factory import \
    ChainlinkNodeAlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import \
    GroupedChainlinkNodeAlertsMetricCode
from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import TimedTaskTracker, TimedTaskLimiter, \
    OccurrencesInTimePeriodTracker


class TestChainlinkNodeAlertingFactory(unittest.TestCase):
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
            'head_tracker_current_head', 'head_tracker_heads_received_total',
            'eth_balance_amount', 'node_is_down'
        ]
        metrics_with_time_window = [
            'max_unconfirmed_blocks',
            'unconfirmed_transactions', 'run_status_update_total'
        ]
        severity_metrics = [
            'process_start_time_seconds',
            'tx_manager_gas_bump_exceeds_limit_total',
            'eth_balance_amount_increase'
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

        self.cl_node_alerts_config = ChainlinkNodeAlertsConfig(
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
            eth_balance_amount=filtered['eth_balance_amount'],
            eth_balance_amount_increase=filtered[
                'eth_balance_amount_increase'],
            node_is_down=filtered['node_is_down']
        )

        # Test object
        self.chainlink_node_alerting_factory = ChainlinkNodeAlertingFactory(
            self.dummy_logger)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.cl_node_alerts_config = None
        self.chainlink_node_alerting_factory = None

    def test_create_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id and node_id.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node are updated
        self.chainlink_node_alerting_factory._alerting_state = {
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
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
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
            self.cl_node_alerts_config.head_tracker_current_head)
        total_headers_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.cl_node_alerts_config.head_tracker_heads_received_total)
        unconfirmed_blocks_thresholds = parse_alert_time_thresholds(
            ['warning_time_window', 'critical_time_window', 'critical_repeat'],
            self.cl_node_alerts_config.max_unconfirmed_blocks
        )
        unconfirmed_txs_thresholds = parse_alert_time_thresholds(
            ['warning_time_window', 'critical_time_window', 'critical_repeat'],
            self.cl_node_alerts_config.unconfirmed_transactions
        )
        error_jobs_thresholds = parse_alert_time_thresholds(
            ['warning_time_window', 'critical_time_window', 'critical_repeat'],
            self.cl_node_alerts_config.run_status_update_total
        )
        eth_balance_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'], self.cl_node_alerts_config.eth_balance_amount
        )
        node_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            self.cl_node_alerts_config.node_is_down
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
                MaxUnconfirmedBlocksThreshold.value: TimedTaskTracker(
                timedelta(seconds=unconfirmed_blocks_thresholds[
                    'warning_time_window'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoOfUnconfirmedTxsThreshold.value: TimedTaskTracker(
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
                MaxUnconfirmedBlocksThreshold.value: TimedTaskTracker(
                timedelta(seconds=unconfirmed_blocks_thresholds[
                    'critical_time_window'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoOfUnconfirmedTxsThreshold.value: TimedTaskTracker(
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
                MaxUnconfirmedBlocksThreshold.value: TimedTaskLimiter(
                timedelta(seconds=unconfirmed_blocks_thresholds[
                    'critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.
                NoOfUnconfirmedTxsThreshold.value: TimedTaskLimiter(
                timedelta(seconds=unconfirmed_txs_thresholds[
                    'critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.
                TotalErroredJobRunsThreshold.value: TimedTaskLimiter(
                timedelta(seconds=error_jobs_thresholds[
                    'critical_repeat'])),
            GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
                TimedTaskLimiter(timedelta(seconds=eth_balance_thresholds[
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

        self.chainlink_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.cl_node_alerts_config)

        self.assertDictEqual(
            expected_state, self.chainlink_node_alerting_factory.alerting_state)

    def test_create_alerting_state_does_not_modify_state_if_already_created(
            self) -> None:
        """
        In this test we will check that if a node's state is already created it
        cannot be overwritten.
        """
        self.chainlink_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.chainlink_node_alerting_factory.alerting_state)

        self.chainlink_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.cl_node_alerts_config)

        self.assertEqual(expected_state,
                         self.chainlink_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.chainlink_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.chainlink_node_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id]

        self.chainlink_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)
        self.assertEqual(expected_state,
                         self.chainlink_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.chainlink_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.chainlink_node_alerting_factory.alerting_state)

        self.chainlink_node_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.chainlink_node_alerting_factory.alerting_state)
