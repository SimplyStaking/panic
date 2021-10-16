import copy
import logging
import unittest
from datetime import timedelta

from src.alerter.factory.chainlink_contract_alerting_factory import \
    ChainlinkContractAlertingFactory
from src.alerter.grouped_alerts_metric_code.contract.chainlink_contract_metric_code \
    import GroupedChainlinkContractAlertsMetricCode as MetricCode
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)


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
        self.proxy_1 = '0x567cC5F1A7c2B3240cb76E2aA1BF0F1bE7035897'
        self.proxy_2 = '0x3FcbE808D1f1A46764AB839B722Beb16c48A80cB'
        self.error_sent = {
            MetricCode.ErrorContractsNotRetrieved.value: False,
            MetricCode.ErrorNoSyncedDataSources.value: False,
        }
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
                    self.proxy_1: self.test_dummy_state
                },
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: {
                    self.proxy_2: self.test_dummy_state
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
                    self.proxy_1: {
                        'warning_sent': warning_sent,
                        'critical_sent': critical_sent,
                        'critical_repeat_timer': critical_repeat_timer,
                    },
                },
                'chain_errors': {
                    'error_sent': self.error_sent
                },
                self.test_dummy_node_id1: {
                    self.proxy_1: self.test_dummy_state
                },
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: {
                    self.proxy_2: self.test_dummy_state
                },
            }
        }

        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.proxy_1,
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
                    self.proxy_1: self.test_dummy_state,
                },
                self.test_dummy_node_id1: {
                    self.proxy_1: self.test_dummy_state,
                },
                'chain_errors': {
                    'error_sent': self.error_sent,
                }
            },
            self.test_dummy_parent_id1: {
                self.test_dummy_node_id2: {
                    self.proxy_2: self.test_dummy_state,
                },
                'chain_errors': {
                    'error_sent': self.error_sent,
                }
            }
        }
        expected_state = copy.deepcopy(
            self.chainlink_contract_alerting_factory.alerting_state)

        self.chainlink_contract_alerting_factory.create_alerting_state(
            self.test_parent_id, self.test_node_id, self.proxy_1,
            self.cl_contract_alerts_config)

        self.assertEqual(
            expected_state,
            self.chainlink_contract_alerting_factory.alerting_state)

    def test_create_parent_alerting_state_creates_error_state_correctly(
            self) -> None:

        self.chainlink_contract_alerting_factory.create_parent_alerting_state(
            self.test_parent_id, self.cl_contract_alerts_config)
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
