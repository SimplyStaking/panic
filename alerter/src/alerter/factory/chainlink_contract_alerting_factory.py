import logging
from datetime import timedelta

from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code import \
    GroupedChainlinkContractAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)


class ChainlinkContractAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    chainlink contract alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            <node_id>: {
                <contract_proxy_address>: {
                    Optional[warning_sent]: {
                        GroupedChainlinkContractAlertsMetricCode.value: bool
                    },
                    Optional[critical_sent]: {
                        GroupedChainlinkContractAlertsMetricCode.value: bool
                    },
                    Optional[warning_window_timer]: {
                        GroupedChainlinkContractAlertsMetricCode.value:
                            TimedTaskTracker
                    },
                    Optional[critical_window_timer]: {
                        GroupedChainlinkContractAlertsMetricCode.value:
                            TimedTaskTracker
                    },
                    Optional[critical_repeat_timer]: {
                        GroupedChainlinkContractAlertsMetricCode.value:
                            TimedTaskLimiter
                    }
                }
            },
            chain_errors: {
                Optional[error_sent]: {
                    GroupedChainlinkContractAlertsMetricCode.value: bool
                }
            }
        }
    }
    """

    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)

    def create_parent_alerting_state(
            self, parent_id: str,
            cl_contract_alerts_config: ChainlinkContractAlertsConfig) -> None:
        """
        During the Chainlink monitoring process it may be found that the
        contracts are unreadable or weiwatchers is un-reachable, in this case
        error data will be generated containing only the parent identifier of
        the blockchain. Therefore we cannot create state for nodes and contracts
        but can create the error state for the parent chain.
        :param parent_id: The id of the chain
        :param cl_contract_alerts_config: The alerts configuration
        :return: None
        """
        if parent_id not in self.alerting_state:
            self.alerting_state[parent_id] = {}

        if 'chain_errors' not in self.alerting_state[parent_id]:
            error_sent = {
                AlertsMetricCode.ErrorRetrievingChainlinkContractData.value:
                    False,
            }

            self.alerting_state[parent_id]['chain_errors'] = {
                'error_sent': error_sent
            }

    def create_alerting_state(
            self, parent_id: str, node_id: str, contract_proxy_address: str,
            cl_contract_alerts_config: ChainlinkContractAlertsConfig) -> None:
        """
        If no state is already stored, this function will create a new alerting
        state for a node and contract based on the passed alerts config.
        :param parent_id: The id of the chain
        :param node_id: The id of the node
        :param contract_proxy_address: The proxy address of the contract
        :param cl_contract_alerts_config: The alerts configuration
        :return: None
        """

        if parent_id not in self.alerting_state:
            self.alerting_state[parent_id] = {}

        if 'chain_errors' not in self.alerting_state[parent_id]:
            error_sent = {
                AlertsMetricCode.ErrorRetrievingChainlinkContractData.value:
                    False,
            }
            self.alerting_state[parent_id]['chain_errors'] = {
                'error_sent': error_sent
            }

        if node_id not in self.alerting_state[parent_id]:
            self.alerting_state[parent_id][node_id] = []

        if contract_proxy_address not in self.alerting_state[parent_id][
                node_id]:

            warning_sent = {
                AlertsMetricCode.PriceFeedNotObserved.value: False,
                AlertsMetricCode.PriceFeedDeviation.value: False,
            }
            critical_sent = {
                AlertsMetricCode.PriceFeedNotObserved.value: False,
                AlertsMetricCode.PriceFeedDeviation.value: False,
            }

            price_feed_not_observed_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_contract_alerts_config.price_feed_not_observed)
            price_feed_deviation_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_contract_alerts_config.price_feed_deviation)

            warning_window_timer = {
                AlertsMetricCode.PriceFeedNotObserved.value: TimedTaskTracker(
                    timedelta(seconds=price_feed_not_observed_thresholds[
                        'warning_threshold'])),
                AlertsMetricCode.PriceFeedDeviation.value:
                    TimedTaskTracker(timedelta(
                        seconds=price_feed_deviation_thresholds[
                            'warning_threshold']))
            }
            critical_window_timer = {
                AlertsMetricCode.PriceFeedNotObserved.value: TimedTaskTracker(
                    timedelta(seconds=price_feed_not_observed_thresholds[
                        'critical_threshold'])),
                AlertsMetricCode.PriceFeedDeviation.value:
                    TimedTaskTracker(
                        timedelta(seconds=price_feed_deviation_thresholds[
                            'critical_threshold']))
            }
            critical_repeat_timer = {
                AlertsMetricCode.PriceFeedNotObserved.value: TimedTaskLimiter(
                    timedelta(seconds=price_feed_not_observed_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.PriceFeedDeviation.value:
                    TimedTaskLimiter(
                        timedelta(seconds=price_feed_deviation_thresholds[
                            'critical_repeat']))
            }

            self.alerting_state[parent_id][node_id][contract_proxy_address] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
                'warning_window_timer': warning_window_timer,
                'critical_window_timer': critical_window_timer,
                'critical_repeat_timer': critical_repeat_timer
            }

    def remove_chain_alerting_state(self, parent_id: str) -> None:
        """
        This function deletes an entire alerting state for a chain.
        :param parent_id: The id of the chain to be deleted
        :return: None
        """
        if parent_id in self.alerting_state:
            del self.alerting_state[parent_id]
