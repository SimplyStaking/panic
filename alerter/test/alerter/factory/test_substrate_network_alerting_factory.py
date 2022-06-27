import copy
import logging
import unittest
from datetime import datetime

from freezegun import freeze_time
from parameterized import parameterized

import src.alerter.alerts.network.substrate as substrate_alerts
from src.alerter.factory.substrate_network_alerting_factory import (
    SubstrateNetworkAlertingFactory)
from src.alerter.grouped_alerts_metric_code.network. \
    substrate_network_metric_code import \
    GroupedSubstrateNetworkAlertsMetricCode as AlertsMetricCode
from src.utils.exceptions import (NoSyncedDataSourceWasAccessibleException,
                                  SubstrateNetworkDataCouldNotBeObtained,
                                  SubstrateApiIsNotReachableException)


class TestSubstrateNetworkAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data and objects
        self.dummy_logger = logging.getLogger('dummy')
        self.test_parent_id_1 = 'test_parent_id_1'
        self.test_parent_id_2 = 'test_parent_id_2'
        self.test_chain_name = 'polkadot'
        self.test_dummy_state = 'dummy_state'

        # Test object
        self.substrate_network_alerting_factory = (
            SubstrateNetworkAlertingFactory(self.dummy_logger))

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.substrate_network_alerting_factory = None

    def test_create_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id.
        """

        # We will also set a dummy state to confirm that the correct chain is
        # updated
        self.substrate_network_alerting_factory._alerting_state = {
            self.test_parent_id_2: self.test_dummy_state
        }

        any_severity_sent = {
            AlertsMetricCode.GrandpaIsStalled.value: False,
        }
        error_sent = {
            AlertsMetricCode.NoSyncedSubstrateWebSocketDataSource.value: False,
            AlertsMetricCode.SubstrateNetworkDataNotObtained.value: False,
            AlertsMetricCode.SubstrateApiNotReachable.value: False,
        }
        expected_state = {
            self.test_parent_id_1: {
                'any_severity_sent': any_severity_sent,
                'error_sent': error_sent,
            },
            self.test_parent_id_2: self.test_dummy_state
        }

        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        self.assertDictEqual(
            expected_state,
            self.substrate_network_alerting_factory.alerting_state)

    def test_create_alerting_state_same_state_if_created_and_unchanged_state(
            self) -> None:
        """
        In this test we will check that if a network's state is already created,
        the alerting state cannot be overwritten.
        """
        self.substrate_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: self.test_dummy_state,
            self.test_parent_id_2: self.test_dummy_state
        }
        expected_state = copy.deepcopy(
            self.substrate_network_alerting_factory.alerting_state)

        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        self.assertEqual(expected_state,
                         self.substrate_network_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.substrate_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: self.test_dummy_state,
            self.test_parent_id_2: self.test_dummy_state
        }
        expected_state = copy.deepcopy(
            self.substrate_network_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id_1]

        self.substrate_network_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id_1)
        self.assertEqual(expected_state,
                         self.substrate_network_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.substrate_network_alerting_factory._alerting_state = {
            self.test_parent_id_1: self.test_dummy_state,
            self.test_parent_id_2: self.test_dummy_state,
        }
        expected_state = copy.deepcopy(
            self.substrate_network_alerting_factory.alerting_state)

        self.substrate_network_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(expected_state,
                         self.substrate_network_alerting_factory.alerting_state)

    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_error_alert_if_matched_error_codes(
            self) -> None:
        test_err = NoSyncedDataSourceWasAccessibleException(
            'test_component', 'test_source')
        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)

        self.substrate_network_alerting_factory.classify_error_alert(
            test_err.code,
            substrate_alerts.ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.NoSyncedSubstrateWebSocketDataSource.value,
            "error msg",
            "resolved msg", test_err.code
        )

        expected_alert = \
            substrate_alerts.ErrorNoSyncedSubstrateWebSocketDataSourcesAlert(
                self.test_chain_name, 'error msg', 'ERROR',
                datetime.now().timestamp(), self.test_parent_id_1,
                self.test_parent_id_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_nothing_if_no_err_received_and_no_raised(
            self) -> None:
        test_err = NoSyncedDataSourceWasAccessibleException('test_component',
                                                            'test_source')
        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)

        self.substrate_network_alerting_factory.classify_error_alert(
            test_err.code,
            substrate_alerts.ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.NoSyncedSubstrateWebSocketDataSource.value,
            "error msg",
            "resolved msg", None
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        (None,), (SubstrateNetworkDataCouldNotBeObtained().code,),
    ])
    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_err_solved_if_alerted_and_no_error(
            self, code) -> None:
        """
        In this test we will check that an error solved alert is raised whenever
        no error is detected or a new error is detected after reporting a
        different error
        """
        test_err = NoSyncedDataSourceWasAccessibleException('test_component',
                                                            'test_source')
        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)

        # Generate first error alert
        self.substrate_network_alerting_factory.classify_error_alert(
            test_err.code,
            substrate_alerts.ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.NoSyncedSubstrateWebSocketDataSource.value,
            "error msg",
            "resolved msg", test_err.code
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Generate solved alert
        alerted_timestamp = datetime.now().timestamp() + 10
        self.substrate_network_alerting_factory.classify_error_alert(
            test_err.code,
            substrate_alerts.ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, alerted_timestamp,
            AlertsMetricCode.NoSyncedSubstrateWebSocketDataSource.value,
            "error msg",
            "resolved msg", code
        )

        expected_alert = (
            substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert(
                self.test_chain_name, 'resolved msg', 'INFO', alerted_timestamp,
                self.test_parent_id_1, self.test_parent_id_1))
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_nothing_if_api_error_sent(
            self) -> None:
        test_err = NoSyncedDataSourceWasAccessibleException(
            'test_component', 'test_source')
        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        self.substrate_network_alerting_factory.alerting_state[
            self.test_parent_id_1]['error_sent'][
            AlertsMetricCode.SubstrateApiNotReachable.value] = True

        self.substrate_network_alerting_factory.classify_error_alert(
            test_err.code,
            substrate_alerts.ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
            substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.NoSyncedSubstrateWebSocketDataSource.value,
            "error msg", "resolved msg",
            SubstrateApiIsNotReachableException.code
        )

        self.assertEqual([], data_for_alerting)

        self.substrate_network_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id_1)

    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_api_error_alert_if_first(
            self) -> None:
        test_err = SubstrateApiIsNotReachableException('test_component',
                                                       'test_source')
        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)

        self.substrate_network_alerting_factory.classify_error_alert(
            test_err.code, substrate_alerts.SubstrateApiIsNotReachableAlert,
            substrate_alerts.SubstrateApiIsReachableAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.SubstrateApiNotReachable.value,
            "error msg", "resolved msg", test_err.code
        )

        expected_alert = \
            substrate_alerts.SubstrateApiIsNotReachableAlert(
                self.test_chain_name, 'error msg', 'ERROR',
                datetime.now().timestamp(), self.test_parent_id_1,
                self.test_parent_id_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

        self.substrate_network_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id_1)

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_not_classify_api_error_if_already_unreachable(
            self) -> None:
        test_err = SubstrateApiIsNotReachableException('test_component',
                                                       'test_source')
        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        self.substrate_network_alerting_factory.alerting_state[
            self.test_parent_id_1]['error_sent'][
            AlertsMetricCode.SubstrateApiNotReachable.value] = True

        self.substrate_network_alerting_factory.classify_error_alert(
            test_err.code, substrate_alerts.SubstrateApiIsNotReachableAlert,
            substrate_alerts.SubstrateApiIsReachableAlert,
            data_for_alerting, self.test_parent_id_1, self.test_parent_id_1,
            self.test_chain_name, datetime.now().timestamp(),
            AlertsMetricCode.SubstrateApiNotReachable.value,
            "error msg", "resolved msg", test_err.code
        )

        self.assertEqual([], data_for_alerting)

        self.substrate_network_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id_1)

    @freeze_time("2012-01-01")
    def test_classify_solvable_cond_no_rep_raises_true_alert_if_not_raised(
            self) -> None:
        """
        Given a true condition, in this test we will check that the
        classify_solvable_conditional_alert_no_repetition fn calls the
        condition_true_alert
        """

        def condition_function(*args): return True

        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        classification_fn = (
            self.substrate_network_alerting_factory
                .classify_solvable_conditional_alert_no_repetition
        )

        classification_fn(
            self.test_parent_id_1, self.test_parent_id_1,
            AlertsMetricCode.GrandpaIsStalled,
            substrate_alerts.GrandpaIsStalledAlert,
            condition_function, [], [
                self.test_chain_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ], data_for_alerting,
            substrate_alerts.GrandpaIsNoLongerStalledAlert, [
                self.test_chain_name, 'INFO', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ],
        )

        expected_alert = substrate_alerts.GrandpaIsStalledAlert(
            self.test_chain_name, 'WARNING', datetime.now().timestamp(),
            self.test_parent_id_1, self.test_parent_id_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_solvable_cond_no_rep_no_true_alert_if_already_raised(
            self) -> None:
        """
        Given a true condition, in this test we will check that if a True alert
        has already been raised, the
        classify_solvable_conditional_alert_no_repetition fn does not call the
        condition_true_alert again
        """

        def condition_function(*args): return True

        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        classification_fn = (
            self.substrate_network_alerting_factory
                .classify_solvable_conditional_alert_no_repetition
        )
        self.substrate_network_alerting_factory.alerting_state[
            self.test_parent_id_1]['any_severity_sent'][
            AlertsMetricCode.GrandpaIsStalled] = True

        classification_fn(
            self.test_parent_id_1, self.test_parent_id_1,
            AlertsMetricCode.GrandpaIsStalled,
            substrate_alerts.GrandpaIsStalledAlert, condition_function, [], [
                self.test_chain_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ], data_for_alerting,
            substrate_alerts.GrandpaIsNoLongerStalledAlert, [
                self.test_chain_name, 'INFO', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ],
        )

        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_solvable_cond_no_rep_raises_false_alert_if_true_raised(
            self) -> None:
        """
        Given a false condition, in this test we will check that the
        classify_solvable_conditional_alert_no_repetition fn calls the
        solved_alert if the condition_true_alert has already been raised.
        """

        def condition_function(*args): return False

        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        classification_fn = (
            self.substrate_network_alerting_factory
                .classify_solvable_conditional_alert_no_repetition
        )
        self.substrate_network_alerting_factory.alerting_state[
            self.test_parent_id_1]['any_severity_sent'][
            AlertsMetricCode.GrandpaIsStalled] = True

        classification_fn(
            self.test_parent_id_1, self.test_parent_id_1,
            AlertsMetricCode.GrandpaIsStalled,
            substrate_alerts.GrandpaIsStalledAlert, condition_function, [], [
                self.test_chain_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ], data_for_alerting,
            substrate_alerts.GrandpaIsNoLongerStalledAlert, [
                self.test_chain_name, 'INFO', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ],
        )

        expected_alert = substrate_alerts.GrandpaIsNoLongerStalledAlert(
            self.test_chain_name, 'INFO', datetime.now().timestamp(),
            self.test_parent_id_1, self.test_parent_id_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_solvable_cond_no_rep_no_false_alert_if_true_not_raised(
            self) -> None:
        """
        Given a false condition, in this test we will check that the
        classify_solvable_conditional_alert_no_repetition fn does not call the
        solved_alert if the condition_true_alert has not been raised.
        """

        def condition_function(*args): return False

        data_for_alerting = []
        self.substrate_network_alerting_factory.create_alerting_state(
            self.test_parent_id_1)
        classification_fn = (
            self.substrate_network_alerting_factory
                .classify_solvable_conditional_alert_no_repetition
        )

        classification_fn(
            self.test_parent_id_1, self.test_parent_id_1,
            AlertsMetricCode.GrandpaIsStalled,
            substrate_alerts.GrandpaIsStalledAlert, condition_function, [], [
                self.test_chain_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ], data_for_alerting,
            substrate_alerts.GrandpaIsNoLongerStalledAlert, [
                self.test_chain_name, 'INFO', datetime.now().timestamp(),
                self.test_parent_id_1, self.test_parent_id_1
            ],
        )

        self.assertEqual([], data_for_alerting)
