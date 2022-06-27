import copy
import logging
import unittest
from datetime import timedelta, datetime
from unittest import mock

from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerts.node.substrate import (
    ValidatorPayoutNotClaimedAlert, ValidatorPayoutClaimedAlert,
    ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
    ValidatorHeartbeatSentOrBlockAuthoredAlert,
    SubstrateWebSocketDataCouldNotBeObtainedAlert,
    SubstrateWebSocketDataObtainedAlert, NodeWentDownAtAlert,
    NodeStillDownAlert, NodeBackUpAgainAlert)
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.factory.substrate_node_alerting_factory import (
    SubstrateNodeAlertingFactory)
from src.alerter.grouped_alerts_metric_code.node. \
    substrate_node_metric_code import \
    GroupedSubstrateNodeAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.node.substrate import SubstrateNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.exceptions import (NoSyncedDataSourceWasAccessibleException,
                                  SubstrateApiIsNotReachableException)
from src.utils.timing import TimedTaskTracker, TimedTaskLimiter


class TestSubstrateNodeAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data and objects
        self.dummy_logger = logging.getLogger('dummy')
        self.test_parent_id = 'test_parent_id'
        self.test_node_id = 'test_node_id'
        self.test_node_name = 'test_node_name'
        self.test_era_index = 1
        self.test_session = 1
        self.test_dummy_parent_id1 = 'dummy_parent_id1'
        self.test_dummy_node_id1 = 'dummy_node_id1'
        self.test_dummy_node_id2 = 'dummy_node_id2'
        self.test_dummy_state = 'dummy_state'

        # Construct the configs
        metrics_without_time_window = [
            'cannot_access_validator', 'cannot_access_node',
            'no_change_in_best_block_height_validator',
            'no_change_in_best_block_height_node',
            'no_change_in_finalized_block_height_validator',
            'no_change_in_finalized_block_height_node',
            'validator_is_syncing', 'node_is_syncing',
            'no_heartbeat_did_not_author_block', 'payout_not_claimed'
        ]
        severity_metrics = [
            'not_active_in_session', 'is_disabled', 'not_elected',
            'bonded_amount_change', 'offline', 'slashed',
            'controller_address_change'
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
        for metric in severity_metrics:
            filtered[metric] = {
                'name': metric,
                'parent_id': self.test_parent_id,
                'enabled': 'true',
                'severity': 'WARNING'
            }

        self.substrate_node_alerts_config = SubstrateNodeAlertsConfig(
            parent_id=self.test_parent_id,
            cannot_access_validator=filtered['cannot_access_validator'],
            cannot_access_node=filtered['cannot_access_node'],
            no_change_in_best_block_height_validator=filtered[
                'no_change_in_best_block_height_validator'],
            no_change_in_best_block_height_node=filtered[
                'no_change_in_best_block_height_node'],
            no_change_in_finalized_block_height_validator=(filtered[
                'no_change_in_finalized_block_height_validator']),
            no_change_in_finalized_block_height_node=filtered[
                'no_change_in_finalized_block_height_node'],
            validator_is_syncing=filtered['validator_is_syncing'],
            node_is_syncing=filtered['node_is_syncing'],
            not_active_in_session=filtered['not_active_in_session'],
            is_disabled=filtered['is_disabled'],
            not_elected=filtered['not_elected'],
            bonded_amount_change=filtered['bonded_amount_change'],
            no_heartbeat_did_not_author_block=filtered[
                'no_heartbeat_did_not_author_block'],
            offline=filtered['offline'],
            slashed=filtered['slashed'],
            payout_not_claimed=filtered['payout_not_claimed'],
            controller_address_change=filtered['controller_address_change'],
        )

        # Test object
        self.substrate_node_alerting_factory = SubstrateNodeAlertingFactory(
            self.dummy_logger)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.substrate_node_alerts_config = None
        self.substrate_node_alerting_factory = None

    @parameterized.expand([(True,), (False,)])
    def test_create_alerting_state_creates_the_correct_state(
            self, is_validator) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id, node_id and is_validator.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node are updated
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        warning_sent = {
            AlertsMetricCode.NodeIsDown.value: False,
            AlertsMetricCode.NoChangeInBestBlockHeight.value: False,
            AlertsMetricCode.NoChangeInFinalizedBlockHeight.value: False,
            AlertsMetricCode.NodeIsSyncing.value: False,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value): False,
        }
        critical_sent = copy.deepcopy(warning_sent)
        error_sent = {
            AlertsMetricCode.NoSyncedSubstrateWebSocketSource.value: False,
            AlertsMetricCode.SubstrateWebSocketDataNotObtained.value: False,
            AlertsMetricCode.SubstrateApiNotReachable.value: False,
        }
        any_severity_sent = {
            AlertsMetricCode.ValidatorIsNotActive: False,
            AlertsMetricCode.ValidatorIsDisabled: False,
            AlertsMetricCode.ValidatorWasNotElected: False,
        }

        alerts_config = self.substrate_node_alerts_config
        node_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_validator if is_validator
            else alerts_config.cannot_access_node
        )
        no_change_in_best_block_height_thresholds = (
            parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'],
                alerts_config.no_change_in_best_block_height_validator
                if is_validator
                else alerts_config.no_change_in_best_block_height_node
            )
        )
        no_change_in_finalized_block_height_thresholds = (
            parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'],
                alerts_config.no_change_in_finalized_block_height_validator
                if is_validator
                else alerts_config.no_change_in_finalized_block_height_node
            )
        )
        node_is_syncing_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'], alerts_config.validator_is_syncing
            if is_validator else alerts_config.node_is_syncing
        )
        send_heartbeat_author_block_thresholds = (
            parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'],
                alerts_config.no_heartbeat_did_not_author_block
            )
        )

        warning_window_timer = {
            AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                seconds=node_is_down_thresholds['warning_threshold'])),
            AlertsMetricCode.NoChangeInBestBlockHeight.value:
                TimedTaskTracker(timedelta(
                    seconds=no_change_in_best_block_height_thresholds[
                        'warning_threshold'])),
            AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                TimedTaskTracker(timedelta(
                    seconds=no_change_in_finalized_block_height_thresholds[
                        'warning_threshold'])),
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value
             ): TimedTaskTracker(timedelta(
                seconds=send_heartbeat_author_block_thresholds[
                    'warning_threshold'])),
        }
        critical_window_timer = {
            AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                seconds=node_is_down_thresholds['critical_threshold'])),
            AlertsMetricCode.NoChangeInBestBlockHeight.value:
                TimedTaskTracker(timedelta(
                    seconds=no_change_in_best_block_height_thresholds[
                        'critical_threshold'])),
            AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                TimedTaskTracker(timedelta(
                    seconds=no_change_in_finalized_block_height_thresholds[
                        'critical_threshold'])),
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value
             ): TimedTaskTracker(timedelta(
                seconds=send_heartbeat_author_block_thresholds[
                    'critical_threshold'])),
        }
        critical_repeat_timer = {
            AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(timedelta(
                seconds=node_is_down_thresholds['critical_repeat'])),
            AlertsMetricCode.NoChangeInBestBlockHeight.value:
                TimedTaskLimiter(timedelta(
                    seconds=no_change_in_best_block_height_thresholds[
                        'critical_repeat'])),
            AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                TimedTaskLimiter(timedelta(
                    seconds=no_change_in_finalized_block_height_thresholds[
                        'critical_repeat'])),
            AlertsMetricCode.NodeIsSyncing.value: TimedTaskLimiter(
                timedelta(seconds=node_is_syncing_thresholds[
                    'critical_repeat'])),
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value
             ): TimedTaskLimiter(timedelta(
                seconds=send_heartbeat_author_block_thresholds[
                    'critical_repeat'])),
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
                    'is_validator': is_validator
                },
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        if is_validator:
            expected_state[self.test_parent_id][self.test_node_id][
                'eras_state'] = {}

        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, is_validator)

        self.assertDictEqual(
            expected_state, self.substrate_node_alerting_factory.alerting_state)

    @parameterized.expand([(True,), (False,)])
    def test_create_alerting_state_same_state_if_created_and_unchanged_state(
            self, is_validator) -> None:
        """
        In this test we will check that if a node's state is already created and
        the is_validator status does not change, the alerting state cannot be
        overwritten.
        """
        self.substrate_node_alerting_factory._alerting_state = {
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
            self.substrate_node_alerting_factory.alerting_state)

        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, is_validator)

        self.assertEqual(expected_state,
                         self.substrate_node_alerting_factory.alerting_state)

    @parameterized.expand([(True,), (False,)])
    def test_create_alerting_state_changes_val_specific_alert_state_if_changes(
            self, is_validator) -> None:
        """
        In this test we will check that if a node's state is already created and
        the is_validator status changes, the part of the alerting state related
        to the validator status changes.
        """
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'alerting_state': self.test_dummy_state,
                    'warning_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInBestBlockHeight.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        (AlertsMetricCode.
                         ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                         .value): TimedTaskTracker(timedelta(seconds=0)),
                    },
                    'critical_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInBestBlockHeight.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                            TimedTaskTracker(timedelta(seconds=0)),
                        (AlertsMetricCode.
                         ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                         .value): TimedTaskTracker(timedelta(seconds=0)),
                    },
                    'critical_repeat_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(
                            timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInBestBlockHeight.value:
                            TimedTaskLimiter(timedelta(seconds=0)),
                        AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                            TimedTaskLimiter(timedelta(seconds=0)),
                        AlertsMetricCode.NodeIsSyncing.value: TimedTaskLimiter(
                            timedelta(seconds=0)),
                        (AlertsMetricCode.
                         ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                         .value): TimedTaskLimiter(timedelta(seconds=0)),
                    },
                    'is_validator': not is_validator
                },
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        alerts_config = self.substrate_node_alerts_config
        node_is_down_thresholds = parse_alert_time_thresholds(
            ['warning_threshold', 'critical_threshold', 'critical_repeat'],
            alerts_config.cannot_access_validator if is_validator
            else alerts_config.cannot_access_node
        )
        no_change_in_best_block_height_thresholds = (
            parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'],
                alerts_config.no_change_in_best_block_height_validator
                if is_validator
                else alerts_config.no_change_in_best_block_height_node
            )
        )
        no_change_in_finalized_block_height_thresholds = (
            parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'],
                alerts_config.no_change_in_finalized_block_height_validator
                if is_validator
                else alerts_config.no_change_in_finalized_block_height_node
            )
        )
        node_is_syncing_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'], alerts_config.validator_is_syncing
            if is_validator else alerts_config.node_is_syncing
        )
        send_heartbeat_author_block_thresholds = (
            parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'],
                alerts_config.no_heartbeat_did_not_author_block
            )
        )
        expected_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'alerting_state': self.test_dummy_state,
                    'warning_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(seconds=node_is_down_thresholds[
                                'warning_threshold'])),
                        AlertsMetricCode.NoChangeInBestBlockHeight.value:
                            TimedTaskTracker(timedelta(
                                seconds=
                                no_change_in_best_block_height_thresholds[
                                    'warning_threshold'])),
                        AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                            TimedTaskTracker(timedelta(
                                seconds=
                                no_change_in_finalized_block_height_thresholds[
                                    'warning_threshold'])),
                        (AlertsMetricCode.
                         ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                         .value): TimedTaskTracker(timedelta(
                            seconds=send_heartbeat_author_block_thresholds[
                                'warning_threshold'])),
                    },
                    'critical_window_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(
                            timedelta(seconds=node_is_down_thresholds[
                                'critical_threshold'])),
                        AlertsMetricCode.NoChangeInBestBlockHeight.value:
                            TimedTaskTracker(timedelta(
                                seconds=
                                no_change_in_best_block_height_thresholds[
                                    'critical_threshold'])),
                        AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                            TimedTaskTracker(timedelta(
                                seconds=
                                no_change_in_finalized_block_height_thresholds[
                                    'critical_threshold'])),
                        (AlertsMetricCode.
                         ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                         .value): TimedTaskTracker(timedelta(
                            seconds=send_heartbeat_author_block_thresholds[
                                'critical_threshold'])),
                    },
                    'critical_repeat_timer': {
                        AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(
                            timedelta(seconds=node_is_down_thresholds[
                                'critical_repeat'])),
                        AlertsMetricCode.NoChangeInBestBlockHeight.value:
                            TimedTaskLimiter(timedelta(
                                seconds=
                                no_change_in_best_block_height_thresholds[
                                    'critical_repeat'])),
                        AlertsMetricCode.NoChangeInFinalizedBlockHeight.value:
                            TimedTaskLimiter(timedelta(
                                seconds=
                                no_change_in_finalized_block_height_thresholds[
                                    'critical_repeat'])),
                        AlertsMetricCode.NodeIsSyncing.value: TimedTaskLimiter(
                            timedelta(seconds=node_is_syncing_thresholds[
                                'critical_repeat'])),
                        (AlertsMetricCode.
                         ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                         .value): TimedTaskLimiter(timedelta(
                            seconds=send_heartbeat_author_block_thresholds[
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
        if is_validator:
            expected_state[self.test_parent_id][self.test_node_id][
                'eras_state'] = {}

        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, is_validator)

        self.assertEqual(expected_state,
                         self.substrate_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.substrate_node_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id]

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)
        self.assertEqual(expected_state,
                         self.substrate_node_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.substrate_node_alerting_factory.alerting_state)

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.substrate_node_alerting_factory.alerting_state)

    def test_create_era_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that era alerting tools are created correctly
        for the given parent_id, node_id and era_index.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node are updated. This will also include an empty alerting state since
        # this is redundant in the context of the era state
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'eras_state': {}
                },
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        warning_sent = {
            AlertsMetricCode.ValidatorPayoutNotClaimed: False,
        }
        critical_sent = {
            AlertsMetricCode.ValidatorPayoutNotClaimed: False,
        }

        expected_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'eras_state': {
                        self.test_era_index: {
                            'warning_sent': warning_sent,
                            'critical_sent': critical_sent,
                        },
                    },
                },
                self.test_dummy_node_id1: self.test_dummy_state
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }

        self.substrate_node_alerting_factory.create_era_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_era_index)

        self.assertDictEqual(
            expected_state, self.substrate_node_alerting_factory.alerting_state)

    def test_create_era_alerting_state_same_state_if_created_and_unchanged_state(
            self) -> None:
        """
        In this test we will check that if a node's era state is already
        created and, the era state cannot be overwritten.
        """
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'alerting_state': self.test_dummy_state,
                    'is_validator': True,
                    'eras_state': {
                        self.test_era_index: self.test_dummy_state
                    },
                },
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.substrate_node_alerting_factory.alerting_state)

        self.substrate_node_alerting_factory.create_era_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_era_index)

        self.assertEqual(expected_state,
                         self.substrate_node_alerting_factory.alerting_state)

    def test_remove_era_alerting_state_removes_era_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the
        era alerting state of the given chain, node, and era
        """
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'eras_state': {
                        self.test_era_index: self.test_dummy_state,
                        2: self.test_dummy_state
                    }
                },
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.substrate_node_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id][self.test_node_id][
            'eras_state'][self.test_era_index]

        self.substrate_node_alerting_factory.remove_era_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_era_index)
        self.assertEqual(expected_state,
                         self.substrate_node_alerting_factory.alerting_state)

    def test_remove_era_alerting_state_does_nothing_if_era_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the era, then the era state is unmodified.
        """
        self.substrate_node_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    'eras_state': {
                        2: self.test_dummy_state
                    }
                },
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.substrate_node_alerting_factory.alerting_state)

        self.substrate_node_alerting_factory.remove_era_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_era_index)
        self.assertEqual(expected_state,
                         self.substrate_node_alerting_factory.alerting_state)

    def test_classify_thresholded_era_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised whenever both warning
        and critical alerts are disabled. We will perform this test for both
        when current>= critical and current >= warning. For an alert to be
        raised when current < critical or current < warning it must be that one
        of the severities is enabled.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        self.substrate_node_alerts_config.payout_not_claimed[
            'warning_enabled'] = 'False'
        self.substrate_node_alerts_config.payout_not_claimed[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_threshold']) + 1
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )

        self.assertEqual([], data_for_alerting)
        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @parameterized.expand([
        ('WARNING', 'warning_threshold'),
        ('CRITICAL', 'critical_threshold'),
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresholded_era_raises_alert_if_above_threshold(
            self, severity, threshold_var) -> None:
        """
        In this test we will check that a warning/critical above threshold
        alert is raised if the current value goes above the warning/critical
        threshold.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                threshold_var]) + 1
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        expected_alert = ValidatorPayoutNotClaimedAlert(
            self.test_node_name, self.test_era_index, era_difference, severity,
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])
        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @freeze_time("2012-01-01")
    def test_classify_thresholded_era_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        # Send first warning alert
        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'warning_threshold']) + 1
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)
        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @freeze_time("2012-01-01")
    def test_classify_thresholded_era_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical above threshold alert is
        re-raised if the critical repeat window elapses. We will also check that
        if the critical window does not elapse, a critical alert is not
        re-raised.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        # First critical below threshold alert
        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_threshold']) + 1
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_threshold']) + int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_repeat']) - 1
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_threshold']) + int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_repeat'])
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        expected_alert = ValidatorPayoutNotClaimedAlert(
            self.test_node_name, self.test_era_index, era_difference,
            "CRITICAL", datetime.now().timestamp(), self.test_parent_id,
            self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])
        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @freeze_time("2012-01-01")
    def test_classify_threshold_era_only_1_critical_if_below_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        increase above critical alert is not re-raised.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        self.substrate_node_alerts_config.payout_not_claimed[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_threshold']) + 1
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        era_difference = int(
            self.substrate_node_alerts_config.payout_not_claimed[
                'critical_repeat'])
        self.substrate_node_alerting_factory.classify_thresholded_era_alert(
            self.test_era_index, era_difference,
            self.substrate_node_alerts_config.payout_not_claimed,
            ValidatorPayoutNotClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            AlertsMetricCode.ValidatorPayoutNotClaimed.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual([], data_for_alerting)
        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @freeze_time("2012-01-01")
    def test_classify_era_solve_alert_raises_alert_if_era_state_exists(
            self) -> None:
        """
        In this test we will check that the classify_era_solve_alert function
        calls the alert if the respective era state exists.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        self.substrate_node_alerting_factory.create_era_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_era_index)

        self.assertTrue(
            self.test_era_index in
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['eras_state'])

        data_for_alerting = []

        self.substrate_node_alerting_factory.classify_era_solve_alert(
            self.test_era_index, ValidatorPayoutClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id,
            self.test_node_name, datetime.now().timestamp()
        )

        expected_alert_1 = ValidatorPayoutClaimedAlert(
            self.test_node_name, self.test_era_index, 'INFO',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])

        self.assertTrue(
            self.test_era_index not in
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['eras_state'])

    @freeze_time("2012-01-01")
    def test_classify_era_solve_alert_does_not_raise_alert_if_no_era_state(
            self) -> None:
        """
        Given that the respective era state does not exist, in this test we
        will check that no alert is raised by the classify_era_solve_alert fn.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)

        self.assertTrue(
            self.test_era_index not in
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['eras_state'])

        data_for_alerting = []

        self.substrate_node_alerting_factory.classify_era_solve_alert(
            self.test_era_index, ValidatorPayoutClaimedAlert, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp()
        )

        self.assertEqual([], data_for_alerting)

        self.assertTrue(
            self.test_era_index not in
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['eras_state'])

    @parameterized.expand([
        ('warning_threshold', 'WARNING',), ('critical_threshold', 'CRITICAL',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_cond_no_change_in_alert_raises_alert_if_time_window_elapsed(
            self, threshold, severity) -> None:
        """
        In this test we will check that a warning/critical no change in alert is
        raised if the value is not being updated and the warning/critical time
        window elapses. We will also first check that no alert is raised first
        time round, (as the timer is started) and if the warning/critical time
        does not elapse. We will also assume that condition function is met.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        def condition_function(*args): return True

        # No alert is raised if timer not started yet
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, datetime.now().timestamp()
        ))
        self.assertEqual([], data_for_alerting)

        # No alert is raised if the time window is not elapsed yet
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, datetime.now().timestamp()
        ))
        self.assertEqual([], data_for_alerting)

        # No change in alert is raised if time window elapsed
        pad = float(self.substrate_node_alerts_config.
                    no_heartbeat_did_not_author_block[threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        expected_alert = (
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert(
                self.test_node_name, self.test_session, pad, severity,
                alert_timestamp, self.test_parent_id, self.test_node_id,
            ))
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @freeze_time("2012-01-01")
    def test_classify_cond_no_change_in_alert_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent. We will also assume that condition
        function is met.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        def condition_function(*args): return True

        # Set the timer
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, datetime.now().timestamp()
        ))

        # Send warning alert
        pad = float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'warning_threshold'])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        self.assertEqual(1, len(data_for_alerting))

        # Check that no alert is raised even if the warning window elapses again
        data_for_alerting.clear()
        alert_timestamp = datetime.now().timestamp() + (2 * pad)
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        self.assertEqual([], data_for_alerting)

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @freeze_time("2012-01-01")
    def test_classify_cond_no_change_in_alert_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical no change in alert is
        re-raised the critical window elapses. We will also check that if the
        critical window does not elapse, a critical alert is not re-raised. We
        will also assume that condition function is met.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        def condition_function(*args): return True

        # Start timer
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, datetime.now().timestamp()
        ))

        # First CRITICAL no change in alert
        pad = float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_threshold'])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_threshold']) + float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_repeat']) - 1
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_threshold']) + float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        expected_alert = (
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert(
                self.test_node_name, self.test_session, pad, 'CRITICAL',
                alert_timestamp, self.test_parent_id, self.test_node_id,
            ))
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @freeze_time("2012-01-01")
    def test_classify_cond_no_change_in_alert_only_1_critical_if_repeat_disabled(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a no
        change critical alert is not re-raised. We
        will also assume that condition function is met.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        def condition_function(*args): return True

        self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
            'critical_repeat_enabled'] = "False"

        # Start timer
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, datetime.now().timestamp()
        ))

        # First CRITICAL no change in alert
        pad = float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_threshold'])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is
        # still not re-raised
        pad = float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_threshold']) + float(
            self.substrate_node_alerts_config.no_heartbeat_did_not_author_block[
                'critical_repeat'])
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))
        self.assertEqual([], data_for_alerting)

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @parameterized.expand([
        ('warning_threshold',), ('critical_threshold',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_cond_no_change_in_alert_resets_state_if_changed(
            self, threshold) -> None:
        """
        In this test we will check that a change will reset the state of
        previous alerting states. We will also assume that condition function
        is met.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        def condition_function(*args):
            return True

        # No alert is raised if timer not started yet
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, datetime.now().timestamp()
        ))

        # No change in alert is raised if time window elapsed
        pad = float(self.substrate_node_alerts_config.
                    no_heartbeat_did_not_author_block[threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))

        if threshold == 'warning_threshold':
            self.assertTrue(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['warning_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])
            self.assertFalse(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['critical_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])
        else:
            self.assertFalse(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['warning_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])
            self.assertTrue(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['critical_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])

        # State is reset if current is not equal to previous
        pad = float(self.substrate_node_alerts_config.
                    no_heartbeat_did_not_author_block[threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session + 1,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert, condition_function,
            [], data_for_alerting, self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))

        self.assertFalse(
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['warning_sent'][
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                 .value)])
        self.assertFalse(
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['critical_sent'][
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                 .value)])

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @parameterized.expand([
        ('warning_threshold',), ('critical_threshold',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_cond_no_change_in_alert_raises_change_alert_if_solved(
            self, threshold) -> None:
        """
        In this test we will check that no change and the condition function
        is no longer met will send change alert and reset the state of
        previous alerting states. We will also assume that condition function
        is met.
        """
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        data_for_alerting = []

        def true_condition_function(*args):
            return True

        def false_condition_function(*args):
            return False

        # No alert is raised if timer not started yet
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert,
            true_condition_function, [], data_for_alerting,
            self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, datetime.now().timestamp()
        ))

        # No change in alert is raised if time window elapsed
        pad = float(self.substrate_node_alerts_config.
                    no_heartbeat_did_not_author_block[threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert,
            true_condition_function, [], data_for_alerting,
            self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))

        if threshold == 'warning_threshold':
            self.assertTrue(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['warning_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])
            self.assertFalse(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['critical_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])
        else:
            self.assertFalse(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['warning_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])
            self.assertTrue(
                self.substrate_node_alerting_factory.alerting_state[
                    self.test_parent_id][self.test_node_id]['critical_sent'][
                    (AlertsMetricCode.
                     ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                     .value)])

        data_for_alerting = []

        # Alert is sent and state is reset if current is condition function is
        # not met
        pad = float(self.substrate_node_alerts_config.
                    no_heartbeat_did_not_author_block[threshold])
        alert_timestamp = datetime.now().timestamp() + pad
        (self.substrate_node_alerting_factory
            .classify_conditional_no_change_in_alert(
            self.test_session, self.test_session,
            (self.substrate_node_alerts_config
             .no_heartbeat_did_not_author_block),
            ValidatorNoHeartbeatAndBlockAuthoredYetAlert,
            ValidatorHeartbeatSentOrBlockAuthoredAlert,
            false_condition_function, [], data_for_alerting,
            self.test_parent_id, self.test_node_id,
            (AlertsMetricCode.
             ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value),
            self.test_node_name, alert_timestamp
        ))

        expected_alert = (
            ValidatorHeartbeatSentOrBlockAuthoredAlert(
                self.test_node_name, self.test_session, 'INFO',
                alert_timestamp, self.test_parent_id, self.test_node_id,
            ))
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

        self.assertFalse(
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['warning_sent'][
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                 .value)])
        self.assertFalse(
            self.substrate_node_alerting_factory.alerting_state[
                self.test_parent_id][self.test_node_id]['critical_sent'][
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert
                 .value)])

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_websocket_error_alert")
    def test_classify_websocket_error_alert_classifies_if_api_reachable(
            self, mock_error_alert):
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        test_err = NoSyncedDataSourceWasAccessibleException('test', 'test')

        self.substrate_node_alerting_factory.classify_websocket_error_alert(
            test_err.code, SubstrateWebSocketDataCouldNotBeObtainedAlert,
            SubstrateWebSocketDataObtainedAlert, [],
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            AlertsMetricCode.SubstrateWebSocketDataNotObtained, "error msg",
            "resolved msg", test_err.code
        )

        mock_error_alert.assert_called_once()

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @mock.patch.object(AlertingFactory, "classify_error_alert")
    def test_classify_websocket_error_alert_does_not_classify_if_api_not_reachable(
            self, mock_error_alert):
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        self.substrate_node_alerting_factory.alerting_state[
            self.test_parent_id][self.test_node_id]['error_sent'][
            AlertsMetricCode.SubstrateApiNotReachable.value] = True
        test_err = NoSyncedDataSourceWasAccessibleException('test', 'test')

        self.substrate_node_alerting_factory.classify_websocket_error_alert(
            test_err.code, SubstrateWebSocketDataCouldNotBeObtainedAlert,
            SubstrateWebSocketDataObtainedAlert, [],
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            AlertsMetricCode.SubstrateWebSocketDataNotObtained, "error msg",
            "resolved msg", SubstrateApiIsNotReachableException.code
        )

        mock_error_alert.assert_not_called()

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @mock.patch.object(AlertingFactory, "classify_error_alert")
    def test_classify_websocket_error_alert_classifies_api_not_reachable_if_first(
            self, mock_error_alert):
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        test_err = SubstrateApiIsNotReachableException('test', 'test')

        self.substrate_node_alerting_factory.classify_websocket_error_alert(
            test_err.code, SubstrateWebSocketDataCouldNotBeObtainedAlert,
            SubstrateWebSocketDataObtainedAlert, [],
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            AlertsMetricCode.SubstrateWebSocketDataNotObtained, "error msg",
            "resolved msg", test_err.code
        )

        mock_error_alert.assert_called_once()

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @mock.patch.object(AlertingFactory, "classify_error_alert")
    def test_classify_websocket_error_alert_does_not_classify_api_error_if_already_unreachable(
            self, mock_error_alert):
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        self.substrate_node_alerting_factory.alerting_state[
            self.test_parent_id][self.test_node_id]['error_sent'][
            AlertsMetricCode.SubstrateApiNotReachable.value] = True
        test_err = SubstrateApiIsNotReachableException('test', 'test')

        self.substrate_node_alerting_factory.classify_websocket_error_alert(
            test_err.code, SubstrateWebSocketDataCouldNotBeObtainedAlert,
            SubstrateWebSocketDataObtainedAlert, [],
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            AlertsMetricCode.SubstrateWebSocketDataNotObtained, "error msg",
            "resolved msg", test_err.code
        )

        mock_error_alert.assert_not_called()

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @mock.patch.object(SubstrateNodeAlertingFactory,
                       "classify_downtime_alert_with_substrate_api_downtime")
    def test_classify_downtime_alert_with_substrate_api_downtime_with_substrate_api_downtime_classifies_if_api_reachable(
            self, mock_downtime):
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)

        (self.substrate_node_alerting_factory
            .classify_downtime_alert_with_substrate_api_downtime(
            datetime.now().timestamp(), {}, NodeWentDownAtAlert,
            NodeStillDownAlert, NodeBackUpAgainAlert, [],
            self.test_parent_id, self.test_node_id, AlertsMetricCode.NodeIsDown,
            self.test_node_name, datetime.now().timestamp()
        ))

        mock_downtime.assert_called_once()

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)

    @mock.patch.object(AlertingFactory, "classify_downtime_alert")
    def test_classify_downtime_alert_with_substrate_api_downtime_with_substrate_api_downtime_does_not_classify_if_api_not_reachable(
            self, mock_downtime):
        self.substrate_node_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id,
            self.substrate_node_alerts_config, True)
        self.substrate_node_alerting_factory.alerting_state[
            self.test_parent_id][self.test_node_id]['error_sent'][
            AlertsMetricCode.SubstrateApiNotReachable.value] = True

        (self.substrate_node_alerting_factory
            .classify_downtime_alert_with_substrate_api_downtime(
            datetime.now().timestamp(), {}, NodeWentDownAtAlert,
            NodeStillDownAlert, NodeBackUpAgainAlert, [],
            self.test_parent_id, self.test_node_id, AlertsMetricCode.NodeIsDown,
            self.test_node_name, datetime.now().timestamp()
        ))

        mock_downtime.assert_not_called()

        self.substrate_node_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)
