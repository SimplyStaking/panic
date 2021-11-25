import logging
import unittest
from datetime import datetime
from typing import Any

from freezegun import freeze_time
from parameterized import parameterized

import src.alerter.alerts.contract.chainlink as cl_alerts
from src.alerter.alerts.contract.chainlink import (
    PriceFeedObservedAgain,
    PriceFeedObservationsMissedIncreasedAboveThreshold,
    PriceFeedDeviationInreasedAboveThreshold,
    PriceFeedDeviationDecreasedBelowThreshold,
)
from src.alerter.factory.chainlink_contract_alerting_factory import \
    ChainlinkContractAlertingFactory
from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code import \
    GroupedChainlinkContractAlertsMetricCode as MetricCode
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.utils.exceptions import (CouldNotRetrieveContractsException,
                                  NoSyncedDataSourceWasAccessibleException)

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
            MetricCode.ErrorContractsNotRetrieved.value: False,
            MetricCode.ErrorNoSyncedDataSources.value: False,
        }
        self.missed_obs = 0
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

        self.test_alerts_config = ChainlinkContractAlertsConfig(
            parent_id=self.test_parent_id,
            price_feed_not_observed=filtered['price_feed_not_observed'],
            price_feed_deviation=filtered['price_feed_deviation'],
            consensus_failure=filtered['consensus_failure'],
        )

        self.test_factory_instance = ChainlinkContractAlertingFactory(
            self.dummy_logger)
        self.test_factory_instance.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.proxy_1,
            self.test_alerts_config)

    @staticmethod
    def _equal_condition_function(current: Any, previous: Any) -> bool:
        return current == previous

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

    def test_classify_thresh_and_cond_alert_does_nothing_warning_critical_disabled(
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
                            'critical_threshold']) + 1
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0], data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, self.last_timestamp
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
        data_for_alerting = []

        current = float(self.test_alerts_config.price_feed_not_observed[
                            threshold_var]) + 1
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0], data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, self.last_timestamp
        )
        expected_alert = PriceFeedObservationsMissedIncreasedAboveThreshold(
            self.test_node_name, current, severity, self.last_timestamp,
            severity, self.test_parent_id, self.test_node_id, self.proxy_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_no_warning_if_warning_already_sent(
            self) -> None:
        """
        In this test we will check that no warning alert is raised if a warning
        alert has already been sent
        """
        data_for_alerting = []

        # Send first warning alert
        current = float(self.test_alerts_config.price_feed_not_observed[
                            'warning_threshold']) + 1
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, self.last_timestamp
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, self.last_timestamp + 1
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
        data_for_alerting = []

        # First critical below threshold alert
        current = (int(self.test_alerts_config.price_feed_not_observed[
                           'critical_threshold']) + 1)
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = (float(self.test_alerts_config.price_feed_not_observed[
                         'critical_repeat']) - 1)
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.test_alerts_config.price_feed_not_observed[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = PriceFeedObservationsMissedIncreasedAboveThreshold(
            self.test_node_name, current, "CRITICAL", alert_timestamp,
            "CRITICAL", self.test_parent_id, self.test_node_id, self.proxy_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_only_1_critical_if_above_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        increase above critical alert is not re-raised.
        """
        self.test_alerts_config.price_feed_not_observed[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        current = (float(self.test_alerts_config.price_feed_not_observed[
                             'critical_threshold']) + 1)
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = (float(self.test_alerts_config.price_feed_not_observed[
                         'critical_repeat']))
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

    @parameterized.expand([
        ('critical_threshold', 'CRITICAL',),
        ('warning_threshold', 'WARNING',)
    ])
    @freeze_time("2012-01-01")
    def test_classify_thresh_and_cond_alert_info_alert_if_below_thresh_and_alert_sent(
            self, threshold_var, threshold_severity) -> None:
        """
        In this test we will check that once the current value is lower than a
        threshold, a decrease below threshold info alert is sent. We will
        perform this test for both warning and critical.
        """
        data_for_alerting = []

        # First below threshold alert
        current = float(self.test_alerts_config.price_feed_not_observed[
                            threshold_var]) + 1
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that a below threshold INFO alert is raised.
        current = 0
        alert_timestamp = datetime.now().timestamp()
        self.test_factory_instance.classify_thresholded_and_conditional_alert(
            current, self.test_alerts_config.price_feed_not_observed,
            PriceFeedObservationsMissedIncreasedAboveThreshold,
            PriceFeedObservedAgain,
            self._equal_condition_function, [current, 0],
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedNotObserved.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = PriceFeedObservedAgain(
            self.test_node_name, 'INFO', alert_timestamp,
            self.test_parent_id, self.test_node_id, self.proxy_1)
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
        self.test_alerts_config.price_feed_deviation[
            'warning_enabled'] = 'False'
        self.test_alerts_config.price_feed_deviation[
            'critical_enabled'] = 'False'

        data_for_alerting = []
        current = float(self.test_alerts_config.price_feed_deviation[
                            'critical_threshold']) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedDeviation.value,
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
            self.test_alerts_config.price_feed_deviation[threshold_var]) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp()
        )
        expected_alert = PriceFeedDeviationInreasedAboveThreshold(
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
            self.test_alerts_config.price_feed_deviation[
                'warning_threshold']) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify again to check if a warning alert is raised
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
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
            self.test_alerts_config.price_feed_deviation[
                'critical_threshold']) + 1)
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Classify with not elapsed repeat to confirm that no critical alert is
        # raised.
        pad = (float(self.test_alerts_config.price_feed_deviation[
                         'critical_repeat']) - 1)
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, alert_timestamp
        )
        self.assertEqual([], data_for_alerting)

        # Let repeat time to elapse and check that a critical alert is
        # re-raised
        pad = float(self.test_alerts_config.price_feed_deviation[
                        'critical_repeat'])
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = PriceFeedDeviationInreasedAboveThreshold(
            self.test_node_name, current, "CRITICAL", alert_timestamp,
            "CRITICAL", self.test_parent_id, self.test_node_id, self.proxy_1)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])

    @freeze_time("2012-01-01")
    def test_classify_threshold_only_1_critical_if_above_and_no_repeat(
            self) -> None:
        """
        In this test we will check that if critical_repeat is disabled, a
        increase above critical alert is not re-raised.
        """
        self.test_alerts_config.price_feed_deviation[
            'critical_repeat_enabled'] = "False"
        data_for_alerting = []

        # First critical below threshold alert
        current = (float(self.test_alerts_config.price_feed_deviation[
                             'critical_threshold']) + 1)
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Let repeat time to elapse and check that a critical alert is not
        # re-raised
        pad = (float(self.test_alerts_config.price_feed_deviation[
                         'critical_repeat']))
        alert_timestamp = datetime.now().timestamp() + pad
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, alert_timestamp
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
        data_for_alerting = []

        # First below threshold alert
        current = float(
            self.test_alerts_config.price_feed_deviation[threshold_var]) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that a below threshold INFO alert is raised. Current is set to
        # warning - 1 to not trigger an INFO alert
        current = float(self.test_alerts_config
                        .price_feed_deviation[
                            'warning_threshold']) - 1
        alert_timestamp = datetime.now().timestamp()
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, alert_timestamp
        )
        expected_alert = PriceFeedDeviationDecreasedBelowThreshold(
            self.test_node_name, current, 'INFO', alert_timestamp,
            threshold_severity, self.test_parent_id, self.test_node_id,
            self.proxy_1)
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
        data_for_alerting = []

        # Send warning increases above threshold alert
        current = (float(self.test_alerts_config
                         .price_feed_deviation['warning_threshold']) + 1)
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(1, len(data_for_alerting))

        # Send critical increase above threshold alert
        current = float(self.test_alerts_config
                        .price_feed_deviation['critical_threshold']) + 1
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting,
            self.test_parent_id, self.test_node_id, self.proxy_1,
            MetricCode.PriceFeedDeviation.value,
            self.test_node_name, datetime.now().timestamp()
        )
        self.assertEqual(2, len(data_for_alerting))
        data_for_alerting.clear()

        # Check that 2 alerts are raised, below critical and above warning
        current = float(self.test_alerts_config.price_feed_deviation[
                            'critical_threshold']) - 1
        alert_timestamp = datetime.now().timestamp() + 10
        self.test_factory_instance.classify_thresholded_alert(
            current, self.test_alerts_config.price_feed_deviation,
            PriceFeedDeviationInreasedAboveThreshold,
            PriceFeedDeviationDecreasedBelowThreshold,
            data_for_alerting, self.test_parent_id, self.test_node_id,
            self.proxy_1, MetricCode.PriceFeedDeviation.value,
            self.test_node_name, alert_timestamp
        )

        expected_alert_1 = PriceFeedDeviationDecreasedBelowThreshold(
            self.test_node_name, current, 'INFO', alert_timestamp,
            'CRITICAL', self.test_parent_id, self.test_node_id, self.proxy_1)
        expected_alert_2 = PriceFeedDeviationInreasedAboveThreshold(
            self.test_node_name, current, 'WARNING', alert_timestamp,
            'WARNING', self.test_parent_id, self.test_node_id, self.proxy_1)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_raises_error_alert_if_matched_error_codes(
            self) -> None:
        test_err_1 = CouldNotRetrieveContractsException(self.test_node_id,
                                                        self.test_parent_id)
        test_err_2 = NoSyncedDataSourceWasAccessibleException(
            self.test_node_id, self.test_parent_id)

        data_for_alerting = []

        self.test_factory_instance.classify_error_alert(
            test_err_1.code, cl_alerts.ErrorContractsNotRetrieved,
            cl_alerts.ContractsNowRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", test_err_1.code
        )
        self.test_factory_instance.classify_error_alert(
            test_err_2.code, cl_alerts.ErrorNoSyncedDataSources,
            cl_alerts.SyncedDataSourcesFound, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            MetricCode.ErrorNoSyncedDataSources.value, "error msg",
            "resolved msg", test_err_2.code
        )
        expected_alert_1 = cl_alerts.ErrorContractsNotRetrieved(
            self.test_node_name, 'error msg', 'ERROR',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        expected_alert_2 = cl_alerts.ErrorNoSyncedDataSources(
            self.test_node_name, 'error msg', 'ERROR',
            datetime.now().timestamp(), self.test_parent_id, self.test_node_id)
        self.assertEqual(2, len(data_for_alerting))
        self.assertEqual(expected_alert_1.alert_data, data_for_alerting[0])
        self.assertEqual(expected_alert_2.alert_data, data_for_alerting[1])

    @freeze_time("2012-01-01")
    def test_classify_error_alert_does_nothing_if_no_err_received_and_no_raised(
            self) -> None:
        test_err_1 = CouldNotRetrieveContractsException(self.test_node_id,
                                                        self.test_parent_id)
        test_err_2 = NoSyncedDataSourceWasAccessibleException(
            self.test_node_id, self.test_parent_id)
        data_for_alerting = []

        self.test_factory_instance.classify_error_alert(
            test_err_1.code, cl_alerts.ErrorContractsNotRetrieved,
            cl_alerts.ContractsNowRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", None
        )

        self.test_factory_instance.classify_error_alert(
            test_err_2.code, cl_alerts.ErrorNoSyncedDataSources,
            cl_alerts.SyncedDataSourcesFound, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
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
        test_err_1 = CouldNotRetrieveContractsException(self.test_node_id,
                                                        self.test_parent_id)
        data_for_alerting = []

        # Generate first error alert
        self.test_factory_instance.classify_error_alert(
            test_err_1.code, cl_alerts.ErrorContractsNotRetrieved,
            cl_alerts.ContractsNowRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            datetime.now().timestamp(),
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", test_err_1.code
        )
        self.assertEqual(1, len(data_for_alerting))
        data_for_alerting.clear()

        # Generate solved alert
        alerted_timestamp = datetime.now().timestamp() + 10
        self.test_factory_instance.classify_error_alert(
            test_err_1.code, cl_alerts.ErrorContractsNotRetrieved,
            cl_alerts.ContractsNowRetrieved, data_for_alerting,
            self.test_parent_id, self.test_node_id, self.test_node_name,
            alerted_timestamp,
            MetricCode.ErrorContractsNotRetrieved.value, "error msg",
            "resolved msg", code
        )

        expected_alert = cl_alerts.ContractsNowRetrieved(
            self.test_node_name, 'resolved msg', 'INFO', alerted_timestamp,
            self.test_parent_id, self.test_node_id)
        self.assertEqual(1, len(data_for_alerting))
        self.assertEqual(expected_alert.alert_data, data_for_alerting[0])
