import copy
import datetime
import logging
import unittest
from datetime import timedelta, datetime
from typing import Any

from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerts.contract.chainlink import (
    PriceFeedObservationsMissedIncreasedAboveThreshold, PriceFeedObservedAgain,
    PriceFeedDeviationIncreasedAboveThreshold,
    PriceFeedDeviationDecreasedBelowThreshold, ErrorContractsNotRetrieved,
    ContractsNowRetrieved, ErrorNoSyncedDataSources, SyncedDataSourcesFound)
from src.alerter.factory.chainlink_contract_alerting_factory import \
    ChainlinkContractAlertingFactory
from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code \
    import GroupedChainlinkContractAlertsMetricCode as MetricCode
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.exceptions import (
    CouldNotRetrieveContractsException,
    NoSyncedDataSourceWasAccessibleException)
from src.utils.timing import (TimedTaskLimiter)


class TestChainlinkContractAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data and objects
        self.dummy_logger = logging.getLogger('dummy')
        self.test_parent_id = 'test_parent_id'
        self.test_node_id = 'test_node_id'
        self.test_dummy_parent_id1 = 'dummy_parent_id1'
        self.test_dummy_node_id1 = 'dummy_node_id1'
        self.test_dummy_node_id2 = 'dummy_node_id2'
        self.test_dummy_state = 'dummy_state'
        self.test_proxy_1 = '0x567cC5F1A7c2B3240cb76E2aA1BF0F1bE7035897'
        self.test_proxy_2 = '0x3FcbE808D1f1A46764AB839B722Beb16c48A80cB'
        self.test_contract_name1 = 'test_contract_name1'
        self.test_contract_name2 = 'test_contract_name2'
        self.error_sent = {
            MetricCode.ErrorContractsNotRetrieved.value: False,
            MetricCode.ErrorNoSyncedDataSources.value: False,
        }
        self.test_alerting_state = {
            'test_key': 'test_val'
        }
        self.test_node_name = 'test_node_name'
        self.last_timestamp = datetime.now().timestamp()

        # Construct the configs
        severity_metrics = [
            'consensus_failure'
        ]
        metrics_without_time_window = [
            'price_feed_not_observed',
            'price_feed_deviation',
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

        self.cl_contract_alerts_config = ChainlinkContractAlertsConfig(
            parent_id=self.test_parent_id,
            price_feed_not_observed=filtered['price_feed_not_observed'],
            price_feed_deviation=filtered['price_feed_deviation'],
            consensus_failure=filtered['consensus_failure'],
        )

        # Test object
        self.chainlink_contract_alerting_factory = \
            ChainlinkContractAlertingFactory(self.dummy_logger)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.cl_contract_alerts_config = None
        self.chainlink_contract_alerting_factory = None

    def test_alerting_state_returns_alerting_state(self) -> None:
        self.chainlink_contract_alerting_factory._alerting_state = \
            self.test_alerting_state
        self.assertEqual(
            self.test_alerting_state,
            self.chainlink_contract_alerting_factory.alerting_state)

    def test_component_logger_returns_logger_instance(self) -> None:
        self.chainlink_contract_alerting_factory._component_logger = \
            self.dummy_logger
        self.assertEqual(
            self.dummy_logger,
            self.chainlink_contract_alerting_factory.component_logger)

    def test_create_alerting_state_creates_the_correct_state(self) -> None:
        """
        In this test we will check that all alerting tools are created correctly
        for the given parent_id, node_id and contract proxy address.
        """

        # We will also set a dummy state to confirm that the correct chain and
        # node and proxy address are updated
        self.chainlink_contract_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_dummy_node_id1: {
                    self.test_proxy_1: self.test_dummy_state
                },
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: {
                    self.test_proxy_2: self.test_dummy_state
                },
            }
        }

        warning_critical_sent_dict = {
            MetricCode.PriceFeedNotObserved.value: False,
            MetricCode.PriceFeedDeviation.value: False,
        }

        warning_sent = copy.deepcopy(warning_critical_sent_dict)
        critical_sent = copy.deepcopy(warning_critical_sent_dict)

        price_feed_not_observed_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'],
            self.cl_contract_alerts_config.price_feed_not_observed)
        price_feed_deviation_thresholds = parse_alert_time_thresholds(
            ['critical_repeat'],
            self.cl_contract_alerts_config.price_feed_deviation)

        critical_repeat_timer = {
            MetricCode.PriceFeedNotObserved.value:
                TimedTaskLimiter(timedelta(
                    seconds=price_feed_not_observed_thresholds[
                        'critical_repeat'])),
            MetricCode.
                PriceFeedDeviation.value:
                TimedTaskLimiter(timedelta(
                    seconds=price_feed_deviation_thresholds[
                        'critical_repeat'])),
        }

        expected_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    self.test_proxy_1: {
                        'warning_sent': warning_sent,
                        'critical_sent': critical_sent,
                        'critical_repeat_timer': critical_repeat_timer,
                    },
                },
                'chain_errors': {
                    'error_sent': self.error_sent
                },
                self.test_dummy_node_id1: {
                    self.test_proxy_1: self.test_dummy_state
                },
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: {
                    self.test_proxy_2: self.test_dummy_state
                },
            }
        }

        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)

        self.assertDictEqual(
            expected_state,
            self.chainlink_contract_alerting_factory.alerting_state)

    def test_create_alerting_state_does_not_modify_state_if_already_created(
            self) -> None:
        """
        In this test we will check that if a node's and contract's state is
        already created it cannot be overwritten.
        """
        self.chainlink_contract_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: {
                    self.test_proxy_1: self.test_dummy_state,
                },
                self.test_dummy_node_id1: {
                    self.test_proxy_1: self.test_dummy_state,
                },
                'chain_errors': {
                    'error_sent': self.error_sent,
                }
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: {
                    self.test_proxy_2: self.test_dummy_state,
                },
                'chain_errors': {
                    'error_sent': self.error_sent,
                }
            }
        }
        expected_state = copy.deepcopy(
            self.chainlink_contract_alerting_factory.alerting_state)

        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)

        self.assertEqual(
            expected_state,
            self.chainlink_contract_alerting_factory.alerting_state)

    def test_create_parent_alerting_state_creates_error_state_correctly(
            self) -> None:

        self.chainlink_contract_alerting_factory.create_parent_alerting_state(
            self.test_parent_id)
        expected_state = {
            self.test_parent_id: {
                'chain_errors': {
                    'error_sent': self.error_sent,
                }
            }
        }
        self.assertEqual(
            expected_state,
            self.chainlink_contract_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_removes_chain_alerting_state_correctly(
            self) -> None:
        """
        In this test we will check that the remove function removes the alerting
        state of the given chain
        """
        self.chainlink_contract_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.chainlink_contract_alerting_factory.alerting_state)
        del expected_state[self.test_parent_id]

        self.chainlink_contract_alerting_factory.remove_chain_alerting_state(
            self.test_parent_id)
        self.assertEqual(
            expected_state,
            self.chainlink_contract_alerting_factory.alerting_state)

    def test_remove_chain_alerting_state_does_nothing_if_chain_does_not_exist(
            self) -> None:
        """
        In this test we will check that if no alerting state has been created
        for the chain, then the state is unmodified.
        """
        self.chainlink_contract_alerting_factory._alerting_state = {
            self.test_parent_id: {
                self.test_node_id: self.test_dummy_state,
                self.test_dummy_node_id1: self.test_dummy_state,
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: self.test_dummy_state
            }
        }
        expected_state = copy.deepcopy(
            self.chainlink_contract_alerting_factory.alerting_state)

        self.chainlink_contract_alerting_factory.remove_chain_alerting_state(
            'bad_chain_id')
        self.assertEqual(
            expected_state,
            self.chainlink_contract_alerting_factory.alerting_state)

    @staticmethod
    def _equal_condition_function(current: Any, previous: Any) -> bool:
        return current == previous

    def test_classify_thresh_and_cond_alert_does_nothing_warn_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised whenever both warning
        and critical alerts are disabled. We will perform this test for both
        when current >= critical and current >= warning. For an alert to be
        raised when current < critical or current < warning it must be that one
        of the severities is enabled.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        self.cl_contract_alerts_config.price_feed_not_observed[
            'warning_enabled'] = 'False'
        self.cl_contract_alerts_config.price_feed_not_observed[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = float(self.cl_contract_alerts_config.price_feed_not_observed[
                            'critical_threshold']) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            self.last_timestamp, self.test_contract_name1
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('WARNING', 'warning_threshold'),
        ('CRITICAL', 'critical_threshold'),
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_raises_alert_if_above_threshold(
            self, severity, threshold_var) -> None:
        """
        In this test we will check that a warning/critical above threshold
        alert is raised if the current value goes above the warning/critical
        threshold.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        current = int(self.cl_contract_alerts_config.price_feed_not_observed[
                          threshold_var]) + 1
        self.chainlink_contract_alerting_factory. \
            classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            self.last_timestamp, self.test_contract_name1
        )
        expected_alert = PriceFeedObservationsMissedIncreasedAboveThreshold(
            self.test_node_name, current, severity, self.last_timestamp,
            severity, self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.test_contract_name1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        # Send first warning alert
        current = float(self.cl_contract_alerts_config.price_feed_not_observed[
                            'warning_threshold']) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, self.last_timestamp, self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            self.last_timestamp + 1, self.test_contract_name1
        )
        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical above threshold alert is
        re-raised if the critical repeat window elapses. We will also check that
        if the critical window does not elapse, a critical alert is not
        re-raised.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        # First critical below threshold alert
        current = (int(self.cl_contract_alerts_config.price_feed_not_observed[
                           'critical_threshold']) + 1)
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = (float(self.cl_contract_alerts_config.price_feed_not_observed[
                         'critical_repeat']) - 1)
        alert_timestamp = datetime.now().timestamp() + pad
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.cl_contract_alerts_config.price_feed_not_observed[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )
        expected_alert = PriceFeedObservationsMissedIncreasedAboveThreshold(
            self.test_node_name, current, "CRITICAL", alert_timestamp,
            "CRITICAL", self.test_parent_id, self.test_node_id,
            self.test_proxy_1, self.test_contract_name1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_only_1_crit_if_above_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        increase above critical alert is not re-raised.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        self.cl_contract_alerts_config.price_feed_not_observed[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        current = (float(self.cl_contract_alerts_config.price_feed_not_observed[
                             'critical_threshold']) + 1)
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = (float(self.cl_contract_alerts_config.price_feed_not_observed[
                         'critical_repeat']))
        alert_timestamp = datetime.now().timestamp() + pad
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_threshold',),
        ('warning_threshold',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_info_alert_if_below_thresh_and_alert_sent(
            self, threshold_var) -> None:
        """
        In this test we will check that once the current value is lower than a
        threshold, a decrease below threshold info alert is sent. We will
        perform this test for both warning and critical.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        # First below threshold alert
        current = float(self.cl_contract_alerts_config.price_feed_not_observed[
                            threshold_var]) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that a below threshold INFO alert is raised.
        current = 0
        alert_timestamp = datetime.now().timestamp()
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_and_conditional_alert(
            current, self.cl_contract_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain, self._equal_condition_function,
            [current, 0], data_for_alerting, self.test_parent_id,
            self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedNotObserved.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )
        expected_alert = PriceFeedObservedAgain(
            self.test_node_name, 'INFO', alert_timestamp,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.test_contract_name1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    def test_classify_thresholded_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised whenever both warning
        and critical alerts are disabled. We will perform this test for both
        when current>= critical and current >= warning. For an alert to be
        raised when current < critical or current < warning it must be that one
        of the severities is enabled.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        self.cl_contract_alerts_config.price_feed_deviation[
            'warning_enabled'] = 'False'
        self.cl_contract_alerts_config.price_feed_deviation[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = float(self.cl_contract_alerts_config.price_feed_deviation[
                            'critical_threshold']) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('WARNING', 'warning_threshold'),
        ('CRITICAL', 'critical_threshold'),
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresholded_raises_alert_if_above_threshold(
            self, severity, threshold_var) -> None:
        """
        In this test we will check that a warning/critical above threshold
        alert is raised if the current value goes above the warning/critical
        threshold.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        current = float(
            self.cl_contract_alerts_config.price_feed_deviation[
                threshold_var]) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        expected_alert = PriceFeedDeviationIncreasedAboveThreshold(
            self.test_node_name, current, severity, datetime.now().timestamp(),
            severity, self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.test_contract_name1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresholded_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        # Send first warning alert
        current = float(
            self.cl_contract_alerts_config.price_feed_deviation[
                'warning_threshold']) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp() + 1, self.test_contract_name1
        )
        self.assertEqual([], data_for_alerting)

    @freeze_time("2012-01-01")
    def test_classify_thresholded_raises_critical_if_repeat_elapsed(
            self) -> None:
        """
        In this test we will check that a critical above threshold alert is
        re-raised if the critical repeat window elapses. We will also check that
        if the critical window does not elapse, a critical alert is not
        re-raised.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        # First critical below threshold alert
        current = (float(
            self.cl_contract_alerts_config.price_feed_deviation[
                'critical_threshold']) + 1)
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = (float(self.cl_contract_alerts_config.price_feed_deviation[
                         'critical_repeat']) - 1)
        alert_timestamp = datetime.now().timestamp() + pad
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.cl_contract_alerts_config.price_feed_deviation[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )
        expected_alert = PriceFeedDeviationIncreasedAboveThreshold(
            self.test_node_name, current, "CRITICAL", alert_timestamp,
            "CRITICAL", self.test_parent_id, self.test_node_id,
            self.test_proxy_1, self.test_contract_name1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_threshold_only_1_critical_if_above_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        increase above critical alert is not re-raised.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        self.cl_contract_alerts_config.price_feed_deviation[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        current = (float(self.cl_contract_alerts_config.price_feed_deviation[
                             'critical_threshold']) + 1)
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = (float(self.cl_contract_alerts_config.price_feed_deviation[
                         'critical_repeat']))
        alert_timestamp = datetime.now().timestamp() + pad
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_threshold', 'CRITICAL',),
        ('warning_threshold', 'WARNING',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_info_alert_if_below_thresh_and_alert_sent(
            self, threshold_var, threshold_severity) -> None:
        """
        In this test we will check that once the current value is lower than a
        threshold, a decrease below threshold info alert is sent. We will
        perform this test for both warning and critical.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        # First below threshold alert
        current = float(
            self.cl_contract_alerts_config.price_feed_deviation[
                threshold_var]) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp(),
            self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that a below threshold INFO alert is raised. Current is set to
        # warning - 1 to not trigger an INFO alert
        current = float(self.cl_contract_alerts_config
                        .price_feed_deviation[
                            'warning_threshold']) - 1
        alert_timestamp = datetime.now().timestamp()
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, alert_timestamp, self.test_contract_name1
        )
        expected_alert = PriceFeedDeviationDecreasedBelowThreshold(
            self.test_node_name, current, 'INFO', alert_timestamp,
            threshold_severity, self.test_parent_id, self.test_node_id,
            self.test_proxy_1, self.test_contract_name1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_warn_alert_if_below_critical_above_warn(
            self) -> None:
        """
        In this test we will check that whenever
        warning <= current <= critical <= previous, a warning alert is raised to
        inform that the current value is bigger than the warning value. Note
        we will perform this test for the case when we first alert warning, then
        critical and not immediately critical, as the warning alerting would be
        obvious.
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        data_for_alerting = []

        # Send warning increases above threshold alert
        current = (float(self.cl_contract_alerts_config
                         .price_feed_deviation['warning_threshold']) + 1)
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(1, len(data_for_alerting))

        # Send critical increase above threshold alert
        current = float(self.cl_contract_alerts_config
                        .price_feed_deviation['critical_threshold']) + 1
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            datetime.now().timestamp(), self.test_contract_name1
        )
        self.assertEqual(2, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that 2 alerts are raised, below critical and above warning
        current = float(self.cl_contract_alerts_config.price_feed_deviation[
                            'critical_threshold']) - 1
        alert_timestamp = datetime.now().timestamp() + 10
        self.chainlink_contract_alerting_factory \
            .classify_thresholded_alert_contract(
            current, self.cl_contract_alerts_config.price_feed_deviation,
            PriceFeedDeviationIncreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            MetricCode.PriceFeedDeviation.value, self.test_node_name,
            alert_timestamp, self.test_contract_name1
        )

        expected_alert_1 = PriceFeedDeviationDecreasedBelowThreshold(
            self.test_node_name, current, 'INFO', alert_timestamp,
            'CRITICAL', self.test_parent_id, self.test_node_id,
            self.test_proxy_1, self.test_contract_name1)
        expected_alert_2 = PriceFeedDeviationIncreasedAboveThreshold(
            self.test_node_name, current, 'WARNING', alert_timestamp,
            'WARNING', self.test_parent_id, self.test_node_id,
            self.test_proxy_1, self.test_contract_name1)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_error_alert_if_matched_error_codes(
            self) -> None:
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        test_err_1 = CouldNotRetrieveContractsException(self.test_node_id,
                                                        self.test_parent_id)
        test_err_2 = NoSyncedDataSourceWasAccessibleException(
            self.test_node_id, self.test_parent_id)

        data_for_alerting = []

        self.chainlink_contract_alerting_factory.classify_error_alert(
            test_err_1.code, ErrorContractsNotRetrieved, ContractsNowRetrieved,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, datetime.now().timestamp(),
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", test_err_1.code
        )
        self.chainlink_contract_alerting_factory.classify_error_alert(
            test_err_2.code, ErrorNoSyncedDataSources, SyncedDataSourcesFound,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, datetime.now().timestamp(),
            MetricCode.ErrorNoSyncedDataSources.value, "error msg",
            "resolved msg", test_err_2.code
        )
        expected_alert_1 = ErrorContractsNotRetrieved(
            self.test_node_name, 'error msg', 'ERROR',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        expected_alert_2 = ErrorNoSyncedDataSources(
            self.test_node_name, 'error msg', 'ERROR',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_nothing_if_no_err_received_and_no_raised(
            self) -> None:
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        test_err_1 = CouldNotRetrieveContractsException(self.test_node_id,
                                                        self.test_parent_id)
        test_err_2 = NoSyncedDataSourceWasAccessibleException(
            self.test_node_id, self.test_parent_id)
        data_for_alerting = []

        self.chainlink_contract_alerting_factory.classify_error_alert(
            test_err_1.code, ErrorContractsNotRetrieved, ContractsNowRetrieved,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, datetime.now().timestamp(),
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", None
        )

        self.chainlink_contract_alerting_factory.classify_error_alert(
            test_err_2.code, ErrorNoSyncedDataSources, SyncedDataSourcesFound,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, datetime.now().timestamp(),
            MetricCode.ErrorNoSyncedDataSources.value, "error msg",
            "resolved msg", None
        )

        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        (None,), (5004,),
    ])
    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_err_solved_if_alerted_and_no_error(
            self, code) -> None:
        """
        In this test we will check that an error solved alert is raised whenever
        no error is detected or a new error is detected after reporting a
        different error
        """
        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.test_proxy_1,
            self.cl_contract_alerts_config)
        test_err_1 = CouldNotRetrieveContractsException(self.test_node_id,
                                                        self.test_parent_id)
        data_for_alerting = []

        # Generate first error alert
        self.chainlink_contract_alerting_factory.classify_error_alert(
            test_err_1.code, ErrorContractsNotRetrieved, ContractsNowRetrieved,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, datetime.now().timestamp(),
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", test_err_1.code
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Generate solved alert
        alerted_timestamp = datetime.now().timestamp() + 10
        self.chainlink_contract_alerting_factory.classify_error_alert(
            test_err_1.code, ErrorContractsNotRetrieved, ContractsNowRetrieved,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.test_node_name, alerted_timestamp,
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", code
        )

        expected_alert = ContractsNowRetrieved(
            self.test_node_name, 'resolved msg', 'INFO', alerted_timestamp,
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])
