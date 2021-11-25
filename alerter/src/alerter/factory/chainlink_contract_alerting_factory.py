import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Type, Callable

from src.alerter.alert_severities import Severity
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code import \
    GroupedChainlinkContractAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.contract.chainlink import ChainlinkContractAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskLimiter)
from src.utils.types import (str_to_bool,
                             IncreasedAboveThresholdAlert,
                             DecreasedBelowThresholdAlert, convert_to_float,
                             ErrorAlert, ErrorSolvedAlert,
                             ConditionalAlert)


class ChainlinkContractAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    Chainlink contract alerter. The alerting_state dict is to be structured as
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
                AlertsMetricCode.ErrorContractsNotRetrieved.value: False,
                AlertsMetricCode.ErrorNoSyncedDataSources.value: False,
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
                AlertsMetricCode.ErrorContractsNotRetrieved.value: False,
                AlertsMetricCode.ErrorNoSyncedDataSources.value: False,
            }
            self.alerting_state[parent_id]['chain_errors'] = {
                'error_sent': error_sent
            }

        if node_id not in self.alerting_state[parent_id]:
            self.alerting_state[parent_id][node_id] = {}

        if contract_proxy_address not in \
                self.alerting_state[parent_id][node_id]:
            warning_sent = {
                AlertsMetricCode.PriceFeedNotObserved.value: False,
                AlertsMetricCode.PriceFeedDeviation.value: False,
            }
            critical_sent = {
                AlertsMetricCode.PriceFeedNotObserved.value: False,
                AlertsMetricCode.PriceFeedDeviation.value: False,
            }

            price_feed_not_observed_thresholds = parse_alert_time_thresholds(
                ['critical_repeat'],
                cl_contract_alerts_config.price_feed_not_observed)
            price_feed_deviation_thresholds = parse_alert_time_thresholds(
                ['critical_repeat'],
                cl_contract_alerts_config.price_feed_deviation)

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

    def classify_thresholded_and_conditional_alert(
            self, current: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            condition_true_alert: Type[ConditionalAlert],
            condition_function: Callable, condition_fn_args: List[Any],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            contract_proxy_address: str, metric_name: str,
            monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a critical/warning increase above threshold alert
        if the current value is bigger than the respective thresholds. If the
        critical repeat time is constantly elapsed, the increase alert is
        re-raised with a critical severity each time. Also, an increase above
        threshold info alert is raised whenever the current value is greater
        than a threshold. Note, a warning increase is re-raised if
        warning_threshold <= current < critical_threshold <= previous. This is
        done so that in the UI the respective metric is shown in warning state
        and not in info state.
        This function also classifies a conditional alert which should send
        an info alert to notify that we are no longer in warning or critical
        state.
        :param current: Current metric value
        :param config: The metric's configuration to obtain the thresholds
        :param increased_above_threshold_alert: The alert to be raised if the
        current value is no longer smaller than a threshold
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param metric_name: The name of the metric
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :return: None
        """
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['warning_sent']

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        critical_repeat_enabled = str_to_bool(
            config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id][contract_proxy_address][
            'critical_repeat_timer'][metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['critical_sent']

        monitoring_datetime = datetime.fromtimestamp(monitoring_timestamp)

        if ((critical_sent[metric_name] or warning_sent[metric_name]) and
                condition_function(*condition_fn_args)):
            alert = condition_true_alert(
                monitorable_name, Severity.INFO.value, monitoring_timestamp,
                parent_id, monitorable_id, contract_proxy_address)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                contract_proxy_address]['critical_sent'][metric_name] = False
            self.alerting_state[parent_id][monitorable_id][
                contract_proxy_address]['warning_sent'][metric_name] = False
            critical_repeat_limiter.reset()
        else:
            if (critical_enabled and not critical_sent[metric_name] and
                    current >= critical_threshold):
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                    monitorable_id, contract_proxy_address)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    contract_proxy_address]['critical_sent'][metric_name] = True
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)
            elif (critical_enabled and critical_sent[metric_name] and
                  critical_repeat_limiter.can_do_task(monitoring_datetime) and
                  critical_repeat_enabled):
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                    monitorable_id, contract_proxy_address)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)
            elif (warning_enabled and not critical_sent[metric_name] and
                  not warning_sent[metric_name] and
                  current >= warning_threshold):
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.WARNING.value,
                    monitoring_timestamp, Severity.WARNING.value, parent_id,
                    monitorable_id, contract_proxy_address)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    contract_proxy_address]['warning_sent'][metric_name] = True

    # TODO: Tmrw continue fixing from here

    def classify_thresholded_alert(
            self, current: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            contract_proxy_address: str, metric_name: str,
            monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        We are overwriting `classify_thresholded_alert` of the
        inherited class.
        This function raises a critical/warning increase above threshold alert
        if the current value is bigger than the respective thresholds. If the
        critical repeat time is constantly elapsed, the increase alert is
        re-raised with a critical severity each time. Also, an increase above
        threshold info alert is raised whenever the current value is greater
        than a threshold. Note, a warning increase is re-raised if
        warning_threshold <= current < critical_threshold <= previous. This is
        done so that in the UI the respective metric is shown in warning state
        and not in info state.
        :param current: Current metric value
        :param config: The metric's configuration to obtain the thresholds
        :param increased_above_threshold_alert: The alert to be raised if the
        current value is no longer smaller than a threshold
        :param decreased_below_threshold_alert: The alert to be raised if the
        current value is smaller than a threshold
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param metric_name: The name of the metric
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :return: None
        """
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['warning_sent']

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        critical_repeat_enabled = str_to_bool(
            config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id][contract_proxy_address][
            'critical_repeat_timer'][metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            contract_proxy_address]['critical_sent']

        monitoring_datetime = datetime.fromtimestamp(monitoring_timestamp)

        # First check for an increase above critical threshold and then check
        # for an increase above warning threshold as
        # warning_threshold <= critical_threshold
        if critical_sent[metric_name] and current < critical_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                monitorable_id, contract_proxy_address)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                contract_proxy_address]['critical_sent'][metric_name] = False
            critical_repeat_limiter.reset()

            # If this is the case we still need to raise a warning alert to
            # show the correct metric state in the UI.
            if warning_sent[metric_name] and current >= warning_threshold:
                self.alerting_state[parent_id][monitorable_id][
                    contract_proxy_address]['warning_sent'][metric_name] = False

        if warning_sent[metric_name] and current < warning_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp, Severity.WARNING.value, parent_id,
                monitorable_id, contract_proxy_address)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                contract_proxy_address]['warning_sent'][metric_name] = False

        # Now check if the current value is greater than any of the thresholds.
        # First check for critical and do not raise a warning alert if we are
        # immediately in critical state.
        if critical_enabled and current >= critical_threshold:
            if not critical_sent[metric_name]:
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                    monitorable_id, contract_proxy_address)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    contract_proxy_address]['critical_sent'][metric_name] = True
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)
            elif (critical_repeat_enabled
                  and critical_repeat_limiter.can_do_task(monitoring_datetime)):
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                    monitorable_id, contract_proxy_address)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)

        if (warning_enabled
                and not warning_sent[metric_name]
                and not critical_sent[metric_name]
                and current >= warning_threshold):
            alert = increased_above_threshold_alert(
                monitorable_name, current, Severity.WARNING.value,
                monitoring_timestamp, Severity.WARNING.value, parent_id,
                monitorable_id, contract_proxy_address)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                contract_proxy_address]['warning_sent'][metric_name] = True

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
