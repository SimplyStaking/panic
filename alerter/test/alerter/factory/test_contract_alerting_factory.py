import logging
import unittest
from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time
from parameterized import parameterized
from typing import Dict

from src.alerter.alerts.contract.chainlink import (
    PriceFeedObservationsDecreasedBelowThreshold,
    PriceFeedObservationsIncreasedAboveThreshold,
    PriceFeedDeviationInreasedAboveThreshold,
    PriceFeedDeciationDecreasedBelowThreshold,
    ConsensusFailure, ErrorRetrievingChainlinkContractData,
    ChainlinkContractDataNowBeingRetrieved)
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.factory.chainlink_contract_alerting_factory import \
    ChainlinkContractAlertingFactory
from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code import \
    GroupedChainlinkContractAlertsMetricCode as MetricCode
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)
from src.utils.exceptions import ErrorRetrievingChainlinkContractData as ERCCD

"""
We will use some chainlink contract alerts and configurations for the tests
below. This should not effect the validity and scope of the tests because the
implementation was conducted to be as general as possible.

These tests will be testing additional functions which are implemented
for the Chainlink Contract Alerting Factory, these functions overwrite
the general ones in the Alerting Factory as they have an extra depth to them
with regards to the contract address.
"""


class TestAlertingFactory(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('dummy')
        self.test_alerting_state = {
            'test_key': 'test_val'
        }
        self.test_parent_id = 'chain_name_4569u540hg8d0fgd0f8th4050h_3464597'
        self.test_node_id = 'node_id34543496346t9345459-34689346h-3463-5'
        self.test_contract_address = ''
        self.test_node_name = 'test_node_name'
        self.proxy_1 = '0x567cC5F1A7c2B3240cb76E2aA1BF0F1bE7035897'
        self.proxy_2 = '0x3FcbE808D1f1A46764AB839B722Beb16c48A80cB'
        self.error_sent = {
            MetricCode.ErrorRetrievingChainlinkContractData.value: False,
        }
        # Construct the configs
        severity_metrics = [
            'consensus_failure'
        ]
        metrics_without_time_window = [
            'price_feed_not_observed',
            'price_feed_deviation',
            'error_retrieving_chainlink_contract_data'
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

        self.test_alerts_config = ChainlinkContractAlertsConfig(
            parent_id=self.test_parent_id,
            price_feed_not_observed=filtered['price_feed_not_observed'],
            price_feed_deviation=filtered['price_feed_deviation'],
            consensus_failure=filtered['consensus_failure'],
            error_retrieving_chainlink_contract_data=filtered[
                'error_retrieving_chainlink_contract_data'],
        )

        self.test_factory_instance = ChainlinkContractAlertingFactory(
            self.dummy_logger)
        self.test_factory_instance.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.proxy_1,
            self.test_alerts_config)

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
            ConsensusFailure, condition_function, [], [
                self.test_node_name, 'WARNING',
                datetime.now().timestamp(), self.test_parent_id,
                self.test_node_id, self.proxy_1
            ], data_for_alerting
        )

        expected_alert_1 = ConsensusFailure(
            self.test_node_name, 'WARNING',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id,
            self.proxy_1)
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
            ConsensusFailure, condition_function, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id, self.test_node_id, self.proxy_1
            ], data_for_alerting, ConsensusFailure,
            [self.test_node_name, 'INFO', datetime.now().timestamp(),
             self.test_parent_id, self.test_node_id,  self.proxy_1]
        )

        expected_alert_1 = ConsensusFailure(
            self.test_node_name, 'INFO', datetime.now().timestamp(),
            self.test_parent_id, self.test_node_id, self.proxy_1)
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
            ConsensusFailure, condition_function, [], [
                self.test_node_name, 'WARNING', datetime.now().timestamp(),
                self.test_parent_id, self.test_node_id,  self.proxy_1
            ], data_for_alerting
        )

        self.assertEqual([], data_for_alerting)

    def test_classify_thresholded_does_nothing_warning_critical_disabled(
            self) -> None:
        """
        In this test we will check that no alert is raised whenever both warning
        and critical alerts are disabled. We will perform this test for both
        when current>= critical and current >= warning. For an alert to be
        raised when current < critical or current < warning it must be that one
        of the severities is enabled.
        """
        self.test_alerts_config.price_feed_not_observed[
            'warning_enabled'] = 'False'
        self.test_alerts_config.price_feed_not_observed[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = float(self.test_alerts_config.price_feed_not_observed[
            'critical_threshold']) - 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
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
        data_for_alerting = []

        current = float(
            self.test_alerts_config
            .price_feed_not_observed[threshold_var]) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        expected_alert = PriceFeedObservationsIncreasedAboveThreshold(
            self.test_node_name, current, severity, datetime.now().timestamp(),
            severity, self.test_parent_id, self.test_node_id, self.proxy_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresholded_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        data_for_alerting = []

        # Send first warning alert
        current = float(
            self.test_alerts_config
            .price_feed_not_observed['warning_threshold']) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp() + 1
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
        data_for_alerting = []

        # First critical below threshold alert
        current = (float(
            self.test_alerts_config
            .price_feed_not_observed['critical_threshold'])
            + 1)
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = (float(
               self.test_alerts_config
               .price_feed_not_observed[
                   'critical_repeat']) - 1)
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(
            self.test_alerts_config
            .price_feed_not_observed[
                'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = PriceFeedObservationsIncreasedAboveThreshold(
            self.test_node_name, current, "CRITICAL", alert_timestamp,
            "CRITICAL", self.test_parent_id, self.test_node_id, self.proxy_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_threshold_only_1_critical_if_below_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        increase above critical alert is not re-raised.
        """
        self.test_alerts_config.price_feed_not_observed[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        current = (float(
            self.test_alerts_config
            .price_feed_not_observed[
                'critical_threshold']) + 1)
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = (float(
            self.test_alerts_config
            .price_feed_not_observed[
                'critical_repeat']))
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_threshold', 'CRITICAL',),
        ('warning_threshold', 'WARNING',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_info_alert_if_above_thresh_and_alert_sent(
            self, threshold_var, threshold_severity) -> None:
        """
        In this test we will check that once the current value is lower than a
        threshold, a decrease below threshold info alert is sent. We will
        perform this test for both warning and critical.
        """
        data_for_alerting = []

        # First below threshold alert
        current = float(
            self.test_alerts_config
            .price_feed_not_observed[threshold_var]) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that an above threshold INFO alert is raised. Current is set to
        # warning + 1 to not trigger a warning alert as it is expected that
        # critical <= warning.
        current = float(self.test_alerts_config
                        .price_feed_not_observed[
                            'warning_threshold']) - 1
        alert_timestamp = datetime.now().timestamp()
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = PriceFeedObservationsDecreasedBelowThreshold(
            self.test_node_name, current, 'INFO', alert_timestamp,
            threshold_severity, self.test_parent_id, self.test_node_id,
            self.proxy_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_warn_alert_if_above_critical_below_warn(
            self) -> None:
        """
        In this test we will check that whenever
        warning <= current <= critical <= previous, a warning alert is raised to
        inform that the current value is bigger than the warning value. Note
        we will perform this test for the case when we first alert warning, then
        critical and not immediately critical, as the warning alerting would be
        obvious.
        """
        data_for_alerting = []

        # Send warning increases above threshold alert
        current = (float(self.test_alerts_config
                         .price_feed_not_observed[
                             'warning_threshold']) + 1)
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))

        # Send critical decrease below threshold alert
        current = float(self.test_alerts_config
                        .price_feed_not_observed[
                            'critical_threshold']) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(2, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that 2 alerts are raised, below critical and above warning
        current = float(self.test_alerts_config.price_feed_not_observed[
            'critical_threshold']) - 1
        alert_timestamp = datetime.now().timestamp() + 10
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config
            .price_feed_not_observed,
            PriceFeedObservationsIncreasedAboveThreshold,
            PriceFeedObservationsDecreasedBelowThreshold,
            data_for_alerting,
            self.test_parent_id, self.test_node_id,  self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )

        expected_alert_1 = PriceFeedObservationsDecreasedBelowThreshold(
            self.test_node_name, current, 'INFO', alert_timestamp,
            'CRITICAL', self.test_parent_id, self.test_node_id,  self.proxy_1)
        expected_alert_2 = PriceFeedObservationsIncreasedAboveThreshold(
            self.test_node_name, current, 'WARNING', alert_timestamp,
            'WARNING', self.test_parent_id, self.test_node_id,  self.proxy_1)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_error_alert_if_matched_error_codes(
            self) -> None:
        test_err = ERCCD(self.test_node_id, self.test_parent_id)
        data_for_alerting = []

        self.test_factory_instance.classify_error_alert(
            test_err.code, ErrorRetrievingChainlinkContractData,
            ChainlinkContractDataNowBeingRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            MetricCode.ErrorRetrievingChainlinkContractData.value, "error msg",
            "resolved msg", test_err.code
        )

        expected_alert = ErrorRetrievingChainlinkContractData(
            self.test_node_name, 'error msg', 'ERROR',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_nothing_if_no_err_received_and_no_raised(
            self) -> None:
        test_err = ERCCD(self.test_node_id, self.test_parent_id)
        data_for_alerting = []

        self.test_factory_instance.classify_error_alert(
            test_err.code, ErrorRetrievingChainlinkContractData,
            ChainlinkContractDataNowBeingRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            MetricCode.ErrorRetrievingChainlinkContractData.value, "error msg",
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
        test_err = ERCCD('test-node', 'test-parent')
        data_for_alerting = []

        # Generate first error alert
        self.test_factory_instance.classify_error_alert(
            test_err.code, ErrorRetrievingChainlinkContractData,
            ChainlinkContractDataNowBeingRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            MetricCode.ErrorRetrievingChainlinkContractData.value, "error msg",
            "resolved msg", test_err.code
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Generate solved alert
        alerted_timestamp = datetime.now().timestamp() + 10
        self.test_factory_instance.classify_error_alert(
            test_err.code, ErrorRetrievingChainlinkContractData,
            ChainlinkContractDataNowBeingRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            alerted_timestamp,
            MetricCode.ErrorRetrievingChainlinkContractData.value, "error msg",
            "resolved msg", code
        )

        expected_alert = ChainlinkContractDataNowBeingRetrieved(
            self.test_node_name, 'resolved msg', 'INFO', alerted_timestamp,
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])
