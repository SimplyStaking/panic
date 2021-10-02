import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Type, Callable, Optional
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code import \
    GroupedChainlinkContractAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.types import (NoChangeInAlert, ChangeInAlert, str_to_bool,
                             IncreasedAboveThresholdAlert,
                             DecreasedBelowThresholdAlert, convert_to_float,
                             ErrorAlert, ErrorSolvedAlert,
                             ConditionalAlert, DownAlert,
                             StillDownAlert, BackUpAlert)
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)
from src.alerter.alert_severities import Severity


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
            self.alerting_state[parent_id][node_id] = {}

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

    def classify_thresholded_time_window_alert(
            self, current: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            contract_proxy_address: str, metric_name: str,
            monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a critical/warning increase above threshold alert
        if the respective thresholds are surpassed and the time windows elapse.
        If the critical repeat time is constantly elapsed, the increase alert is
        re-raised with a critical severity each time. Also, a decrease below
        threshold info alert is raised whenever a threshold is no longer
        surpassed. Note, a warning increase is re-raised if
        warning_threshold <= current < critical_threshold <= previous. This is
        done so that the in the UI the respective metric is shown in warning
        state and not in info state.
        :param current: Current metric value
        :param config: The metric's configuration to obtain the thresholds
        :param increased_above_threshold_alert: The alert to be raised if a
        threshold is surpassed
        :param decreased_below_threshold_alert: The alert to be raised if a
        threshold is no longer surpassed
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param contract_proxy_address: The proxy address of the CL contract
        :param metric_name: The name of the metric
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :return: None
        """
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        warning_window_timer = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['warning_window_timer'][metric_name]
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['warning_sent']

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        critical_repeat_enabled = str_to_bool(
            config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id][contract_proxy_address]['critical_repeat_timer'][
                metric_name]
        critical_window_timer = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['critical_window_timer'][metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['critical_sent']

        monitoring_datetime = datetime.fromtimestamp(monitoring_timestamp)

        # First check for a decrease below critical threshold and then check
        # for a decrease below warning threshold as
        # warning_threshold <= critical_threshold

        if critical_sent[metric_name] and current < critical_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug(
                "Successfully classified alert %s", alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                contract_proxy_address]['critical_sent'][metric_name] = False
            critical_window_timer.reset()
            critical_repeat_limiter.reset()

            # If this is the case we still need to raise a warning alert to
            # show the correct metric state in the UI.
            if warning_sent[metric_name] and current >= warning_threshold:
                warning_window_timer.start_timer(
                    warning_window_timer.start_time)
                self.alerting_state[parent_id][monitorable_id][
                    contract_proxy_address]['warning_sent'][metric_name] = False

        if warning_sent[metric_name] and current < warning_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp, Severity.WARNING.value, parent_id,
                monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug(
                "Successfully classified alert %s", alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                contract_proxy_address]['warning_sent'][metric_name] = False
            warning_window_timer.reset()

        # Now check if any of the thresholds are surpassed. We will not generate
        # a warning alert if we are immediately in critical state.

        if critical_enabled and current >= critical_threshold:
            if not critical_window_timer.timer_started:
                critical_window_timer.start_timer(monitoring_datetime)
            elif critical_window_timer.can_do_task(monitoring_datetime):
                duration = monitoring_timestamp - \
                    critical_window_timer.start_time.replace(
                        tzinfo=timezone.utc).timestamp()
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, duration, Severity.CRITICAL.value,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    contract_proxy_address]['critical_sent'][metric_name] = True
                critical_window_timer.do_task()
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)
            elif (critical_sent[metric_name]
                  and critical_repeat_enabled
                  and critical_repeat_limiter.can_do_task(monitoring_datetime)):
                duration = monitoring_timestamp - \
                    critical_window_timer.start_time.replace(
                        tzinfo=timezone.utc).timestamp()
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, duration, Severity.CRITICAL.value,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)

        if warning_enabled and current >= warning_threshold:
            if not warning_window_timer.timer_started:
                warning_window_timer.start_timer(monitoring_datetime)
            elif (not critical_sent[metric_name]
                  and warning_window_timer.can_do_task(monitoring_datetime)):
                duration = monitoring_timestamp - \
                    warning_window_timer.start_time.replace(
                        tzinfo=timezone.utc).timestamp()
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.WARNING.value,
                    monitoring_timestamp, duration, Severity.WARNING.value,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                warning_window_timer.do_task()
                self.alerting_state[parent_id][monitorable_id][
                    contract_proxy_address]['warning_sent'][metric_name] = True

    def classify_conditional_alert(
            self, condition_true_alert: Type[ConditionalAlert],
            condition_function: Callable, condition_fn_args: List[Any],
            true_alert_args: List[Any], data_for_alerting: List,
            condition_false_alert: Type[ConditionalAlert] = None,
            false_alert_args: List[Any] = None
    ) -> None:
        if condition_function(*condition_fn_args):
            alert = condition_true_alert(*true_alert_args)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
        elif condition_false_alert is not None:
            if false_alert_args is None:
                false_alert_args = []
            alert = condition_false_alert(*false_alert_args)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)

    def classify_error_alert(
            self, error_code_to_detect: int,
            error_alert: Type[ErrorAlert],
            error_solved_alert: Type[ErrorSolvedAlert], data_for_alerting: List,
            parent_id: str, monitorable_id: str, monitorable_name: str,
            monitoring_timestamp: float, metric_name: str,
            error_message: str = "", resolved_message: str = "",
            received_error_code: int = None,
    ) -> None:
        """
        This function attempts to raise an error alert with code
        'received_error_code' if 'received_error_code' = 'error_code_to_detect',
        and raises an info alert that the error has been resolved otherwise,
        provided that an error alert has already been sent.
        :param received_error_code: The code associated with the received error
        if any. If no errors are received this should be set to None.
        :param error_code_to_detect: The error code to detect in order to raise
        the error alert
        :param error_alert: The error alert to be raised if detected
        :param error_solved_alert: The alert to be raised if the error is solved
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param metric_name: The name of the metric
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :param error_message: The alert's message when an error is raised
        :param resolved_message: The alert's message when an error is resolved
        :return: None
        """

        error_sent = self.alerting_state[parent_id]['chain_errors'][
            'error_sent'][metric_name]

        if error_sent and received_error_code != error_code_to_detect:
            alert = error_solved_alert(
                monitorable_name, resolved_message, Severity.INFO.value,
                monitoring_timestamp, parent_id, monitorable_id
            )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id]['chain_errors'][
                'error_sent'][metric_name] = False
        elif received_error_code == error_code_to_detect:
            alert = error_alert(
                monitorable_name, error_message, Severity.ERROR.value,
                monitoring_timestamp, parent_id, monitorable_id
            )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id]['chain_errors'][
                'error_sent'][metric_name] = True
