import copy
import logging
import unittest
from datetime import timedelta

from parameterized import parameterized

from src.alerter.factory.cosmos_node_alerting_factory import (
    CosmosNodeAlertingFactory)
from src.alerter.grouped_alerts_metric_code.node. \
    cosmos_node_metric_code import \
    GroupedCosmosNodeAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (
    TimedTaskTracker, TimedTaskLimiter, OccurrencesInTimePeriodTracker)


class TestCosmosNodeAlertingFactory(unittest.TestCase):
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
            'cannot_access_validator', 'cannot_access_node',
            'no_change_in_block_height_validator',
            'no_change_in_block_height_node', 'block_height_difference',
            'cannot_access_prometheus_validator',
            'cannot_access_prometheus_node',
            'cannot_access_cosmos_rest_validator',
            'cannot_access_cosmos_rest_node',
            'cannot_access_tendermint_rpc_validator',
            'cannot_access_tendermint_rpc_node'
        ]
        metrics_with_time_window = ['missed_blocks']
        severity_metrics = [
            'slashed', 'node_is_syncing', 'validator_is_syncing',
            'validator_not_active_in_session', 'validator_is_jailed',
            'node_is_peered_with_sentinel', 'validator_is_peered_with_sentinel',
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

        self.cosmos_node_alerts_config = CosmosNodeAlertsConfig(
            parent_id=self.test_parent_id,
            cannot_access_validator=filtered['cannot_access_validator'],
            cannot_access_node=filtered['cannot_access_node'],
            validator_not_active_in_session=filtered[
                'validator_not_active_in_session'],
            no_change_in_block_height_validator=filtered[
                'no_change_in_block_height_validator'],
            no_change_in_block_height_node=filtered[
                'no_change_in_block_height_node'],
            block_height_difference=filtered['block_height_difference'],
            cannot_access_prometheus_validator=filtered[
                'cannot_access_prometheus_validator'],
            cannot_access_prometheus_node=filtered[
                'cannot_access_prometheus_node'],
            cannot_access_cosmos_rest_validator=filtered[
                'cannot_access_cosmos_rest_validator'],
            cannot_access_cosmos_rest_node=filtered[
                'cannot_access_cosmos_rest_node'],
            cannot_access_tendermint_rpc_validator=filtered[
                'cannot_access_tendermint_rpc_validator'],
            cannot_access_tendermint_rpc_node=filtered[
                'cannot_access_tendermint_rpc_node'],
            missed_blocks=filtered['missed_blocks'], slashed=filtered[
                'slashed'], node_is_syncing=filtered['node_is_syncing'],
            validator_is_syncing=filtered['validator_is_syncing'],
            validator_is_jailed=filtered['validator_is_jailed'],
            node_is_peered_with_sentinel=filtered['node_is_peered_with_sentinel'],
            validator_is_peered_with_sentinel=filtered['validator_is_peered_with_sentinel'],
            )

        # Test object
        self.cosmos_node_alerting_factory = CosmosNodeAlertingFactory(
            self.dummy_logger)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.cosmos_node_alerts_config = None
        self.cosmos_node_alerting_factory = None

    @parameterized.expand([(True,), (False,)])
    def test_create_alerting_state_creates_the_correct_state(
            self, is_validator) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id, node_id and is_validator.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node are updated
        self.cosmos_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        warning_sent = {
            AlertsMetricCode.NodeIsDown.value: False,
            AlertsMetricCode.BlocksMissedThreshold.value: False,
            AlertsMetricCode.NoChangeInHeight.value: False,
            AlertsMetricCode.BlockHeightDifferenceThreshold.value: False,
            AlertsMetricCode.PrometheusSourceIsDown.value: False,
            AlertsMetricCode.CosmosRestSourceIsDown.value: False,
            AlertsMetricCode.TendermintRPCSourceIsDown.value: False,
        }
        critical_sent = copy.deepcopy(warning_sent)
        error_sent = {
            AlertsMetricCode.PrometheusInvalidUrl.value: False,
            AlertsMetricCode.CosmosRestInvalidUrl.value: False,
            AlertsMetricCode.TendermintRPCInvalidUrl.value: False,
            AlertsMetricCode.NoSyncedCosmosRestSource.value: False,
            AlertsMetricCode.NoSyncedTendermintRPCSource.value: False,
            AlertsMetricCode.CosmosRestDataNotObtained.value: False,
            AlertsMetricCode.TendermintRPCDataNotObtained.value: False,
            AlertsMetricCode.MetricNotFound.value: False,
        }
        any_severity_sent = {
            AlertsMetricCode.NodeIsNotPeeredWithSentinel.value: False,
            AlertsMetricCode.NodeIsSyncing.value: False,
            AlertsMetricCode.ValidatorIsNotActive.value: False,
            AlertsMetricCode.ValidatorIsJailed.value: False,
        }

        alerts_config = self.cosmos_node_alerts_config
        node_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_validator if is_validator
            else alerts_config.cannot_access_node
        )
        blocks_missed_thresholds = parse_alert_time_thresholds(
            ['warning_time_window', 'critical_time_window',
             'critical_repeat'], alerts_config.missed_blocks
        )
        no_change_in_height_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.no_change_in_block_height_validator
            if is_validator
            else alerts_config.no_change_in_block_height_node
        )
        height_difference_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'], alerts_config.block_height_difference
        )
        prometheus_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_prometheus_validator if is_validator
            else alerts_config.cannot_access_prometheus_node
        )
        cosmos_rest_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_cosmos_rest_validator
            if is_validator
            else alerts_config.cannot_access_cosmos_rest_node
        )
        tendermint_rpc_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_tendermint_rpc_validator
            if is_validator
            else alerts_config.cannot_access_tendermint_rpc_node
        )

        warning_window_timer = {
            AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                seconds=node_is_down_thresholds['warning_threshold'])),
            AlertsMetricCode.NoChangeInHeight.value: TimedTaskTracker(
                timedelta(seconds=no_change_in_height_thresholds[
                    'warning_threshold'])),
            AlertsMetricCode.PrometheusSourceIsDown.value: TimedTaskTracker(
                timedelta(seconds=prometheus_is_down_thresholds[
                    'warning_threshold'])),
            AlertsMetricCode.CosmosRestSourceIsDown.value: TimedTaskTracker(
                timedelta(seconds=cosmos_rest_is_down_thresholds[
                    'warning_threshold'])),
            AlertsMetricCode.TendermintRPCSourceIsDown.value:
                TimedTaskTracker(timedelta(
                    seconds=tendermint_rpc_is_down_thresholds[
                        'warning_threshold']))
        }
        critical_window_timer = {
            AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                seconds=node_is_down_thresholds['critical_threshold'])),
            AlertsMetricCode.NoChangeInHeight.value: TimedTaskTracker(
                timedelta(seconds=no_change_in_height_thresholds[
                    'critical_threshold'])),
            AlertsMetricCode.PrometheusSourceIsDown.value: TimedTaskTracker(
                timedelta(seconds=prometheus_is_down_thresholds[
                    'critical_threshold'])),
            AlertsMetricCode.CosmosRestSourceIsDown.value: TimedTaskTracker(
                timedelta(seconds=cosmos_rest_is_down_thresholds[
                    'critical_threshold'])),
            AlertsMetricCode.TendermintRPCSourceIsDown.value:
                TimedTaskTracker(timedelta(
                    seconds=tendermint_rpc_is_down_thresholds[
                        'critical_threshold'])),
        }
        critical_repeat_timer = {
            AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(timedelta(
                seconds=node_is_down_thresholds['critical_repeat'])),
            AlertsMetricCode.BlocksMissedThreshold.value:
                TimedTaskLimiter(timedelta(seconds=blocks_missed_thresholds[
                    'critical_repeat'])),
            AlertsMetricCode.NoChangeInHeight.value: TimedTaskLimiter(
                timedelta(seconds=no_change_in_height_thresholds[
                    'critical_repeat'])),
            AlertsMetricCode.BlockHeightDifferenceThreshold.value:
                TimedTaskLimiter(timedelta(
                    seconds=height_difference_thresholds[
                        'critical_repeat'])),
            AlertsMetricCode.PrometheusSourceIsDown.value:
                TimedTaskLimiter(timedelta(
                    seconds=prometheus_is_down_thresholds[
                        'critical_repeat'])),
            AlertsMetricCode.CosmosRestSourceIsDown.value:
                TimedTaskLimiter(timedelta(
                    seconds=cosmos_rest_is_down_thresholds[
                        'critical_repeat'])),
            AlertsMetricCode.TendermintRPCSourceIsDown.value:
                TimedTaskLimiter(timedelta(
                    seconds=tendermint_rpc_is_down_thresholds[
                        'critical_repeat'])),
        }
        warning_occurrences_in_period_tracker = {
            AlertsMetricCode.BlocksMissedThreshold.value:
                OccurrencesInTimePeriodTracker(timedelta(
                    seconds=blocks_missed_thresholds[
                        'warning_time_window'])),
        }
        critical_occurrences_in_period_tracker = {
            AlertsMetricCode.BlocksMissedThreshold.value:
                OccurrencesInTimePeriodTracker(timedelta(
                    seconds=blocks_missed_thresholds[
                        'critical_time_window'])),
        }

        expected_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'warning_sent': warning_sent,
                    'critical_sent': critical_sent,
                    'error_sent': error_sent,
                    'any_severity_sent': any_severity_sent,
                    'warning_window_timer': warning_window_timer,
                    'critical_window_timer': critical_window_timer,
                    'critical_repeat_timer': critical_repeat_timer,
                    'warning_occurrences_in_period_tracker':
                        warning_occurrences_in_period_tracker,
                    'critical_occurrences_in_period_tracker':
                        critical_occurrences_in_period_tracker,
                    'is_validator': is_validator,
                    'current_height': None,
                },
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        self.cosmos_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.cosmos_node_alerts_config, is_validator)

        self.assertDictEqual(
            expected_state, self.cosmos_node_alerting_factory.alerting_state)

    @parameterized.expand([(True,), (False,)])
    def test_create_alerting_state_same_state_if_created_and_unchanged_state(
            self, is_validator) -> None:
        """
        In this test we will check that if a node's state is already created and
        the is_validator status does not change, the alerting state cannot be
        overwritten.
        """
        self.cosmos_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'alerting_state': self.test_dummy_state,
                    'is_validator': is_validator
                },
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.cosmos_node_alerting_factory.alerting_state)

        self.cosmos_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.cosmos_node_alerts_config, is_validator)

        self.assertEqual(expected_state,
                         self.cosmos_node_alerting_factory.alerting_state)

    @parameterized.expand([(True,), (False,)])
    def test_create_alerting_state_changes_val_specific_alert_state_if_changes(
            self, is_validator) -> None:
        """
        In this test we will check that if a node's state is already created and
        the is_validator status changes, the part of the alerting state related
        to the validator status changes.
        """
        self.cosmos_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'alerting_state': self.test_dummy_state,
                    'warning_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInHeight.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.PrometheusSourceIsDown.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.CosmosRestSourceIsDown.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.TendermintRPCSourceIsDown.value:
                            TimedTaskTracker(timedelta(seconds=0))
                    },
                    'critical_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInHeight.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.PrometheusSourceIsDown.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.CosmosRestSourceIsDown.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.TendermintRPCSourceIsDown.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                    },
                    'critical_repeat_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(
                            timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInHeight.value:
                            TimedTaskLimiter(timedelta(seconds=0)),
                        AlertsMetricCode.PrometheusSourceIsDown.value:
                            TimedTaskLimiter(timedelta(seconds=0)),
                        AlertsMetricCode.CosmosRestSourceIsDown.value:
                            TimedTaskLimiter(timedelta(seconds=0)),
                        AlertsMetricCode.TendermintRPCSourceIsDown.value:
                            TimedTaskLimiter(timedelta(seconds=0)),
                    },
                    'is_validator': not is_validator
                },
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        alerts_config = self.cosmos_node_alerts_config
        node_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_validator if is_validator
            else alerts_config.cannot_access_node
        )
        no_change_in_height_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.no_change_in_block_height_validator
            if is_validator
            else alerts_config.no_change_in_block_height_node
        )
        prometheus_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_prometheus_validator if is_validator
            else alerts_config.cannot_access_prometheus_node
        )
        cosmos_rest_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_cosmos_rest_validator
            if is_validator
            else alerts_config.cannot_access_cosmos_rest_node
        )
        tendermint_rpc_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_tendermint_rpc_validator
            if is_validator
            else alerts_config.cannot_access_tendermint_rpc_node
        )
        expected_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'alerting_state': self.test_dummy_state,
                    'warning_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(
                                seconds=node_is_down_thresholds[
                                    'warning_threshold'])),
                        AlertsMetricCode.NoChangeInHeight.value:
                            TimedTaskTracker(timedelta(
                                seconds=no_change_in_height_thresholds[
                                    'warning_threshold'])),
                        AlertsMetricCode.PrometheusSourceIsDown.value:
                            TimedTaskTracker(timedelta(
                                seconds=prometheus_is_down_thresholds[
                                    'warning_threshold'])),
                        AlertsMetricCode.CosmosRestSourceIsDown.value:
                            TimedTaskTracker(timedelta(
                                seconds=cosmos_rest_is_down_thresholds[
                                    'warning_threshold'])),
                        AlertsMetricCode.TendermintRPCSourceIsDown.value:
                            TimedTaskTracker(timedelta(
                                seconds=tendermint_rpc_is_down_thresholds[
                                    'warning_threshold']))
                    },
                    'critical_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(
                                seconds=node_is_down_thresholds[
                                    'critical_threshold'])),
                        AlertsMetricCode.NoChangeInHeight.value:
                            TimedTaskTracker(timedelta(
                                seconds=no_change_in_height_thresholds[
                                    'critical_threshold'])),
                        AlertsMetricCode.PrometheusSourceIsDown.value:
                            TimedTaskTracker(timedelta(
                                seconds=prometheus_is_down_thresholds[
                                    'critical_threshold'])),
                        AlertsMetricCode.CosmosRestSourceIsDown.value:
                            TimedTaskTracker(timedelta(
                                seconds=cosmos_rest_is_down_thresholds[
                                    'critical_threshold'])),
                        AlertsMetricCode.TendermintRPCSourceIsDown.value:
                            TimedTaskTracker(timedelta(
                                seconds=tendermint_rpc_is_down_thresholds[
                                    'critical_threshold'])),
                    },
                    'critical_repeat_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(
                            timedelta(
                                seconds=node_is_down_thresholds[
                                    'critical_repeat'])),
                        AlertsMetricCode.NoChangeInHeight.value:
                            TimedTaskLimiter(timedelta(
                                seconds=no_change_in_height_thresholds[
                                    'critical_repeat'])),
                        AlertsMetricCode.PrometheusSourceIsDown.value:
                            TimedTaskLimiter(timedelta(
                                seconds=prometheus_is_down_thresholds[
                                    'critical_repeat'])),
                        AlertsMetricCode.CosmosRestSourceIsDown.value:
                            TimedTaskLimiter(timedelta(
                                seconds=cosmos_rest_is_down_thresholds[
                                    'critical_repeat'])),
                        AlertsMetricCode.TendermintRPCSourceIsDown.value:
                            TimedTaskLimiter(timedelta(
                                seconds=tendermint_rpc_is_down_thresholds[
                                    'critical_repeat'])),
                    },
                    'is_validator': is_validator
                },
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        self.cosmos_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.cosmos_node_alerts_config, is_validator)

        self.assertEqual(expected_state,
                         self.cosmos_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.cosmos_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.cosmos_node_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id]

        self.cosmos_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)
        self.assertEqual(expected_state,
                         self.cosmos_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.cosmos_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.cosmos_node_alerting_factory.alerting_state)

        self.cosmos_node_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.cosmos_node_alerting_factory.alerting_state)
