import logging
from datetime import timedelta, datetime, timezone
from typing import Dict, List, Type, Callable, Any, Optional

from src.alerter.alert_severities import Severity
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node. \
    substrate_node_metric_code import \
    GroupedSubstrateNodeAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.node.substrate import SubstrateNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.exceptions import SubstrateApiIsNotReachableException
from src.utils.timing import TimedTaskTracker, TimedTaskLimiter
from src.utils.types import (
    str_to_bool, convert_to_float, IncreasedAboveSubstrateEraThresholdAlert,
    ConditionalNoChangeInAlert, ConditionalChangeInAlert, ErrorAlert,
    ErrorSolvedAlert, DownAlert, StillDownAlert, BackUpAlert,
    SolvedSubstrateEraAlert)


class SubstrateNodeAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    substrate node alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            <node_id>: {
                Optional[warning_sent]: {
                    GroupedSubstrateNodeAlertsMetricCode.value: bool
                },
                Optional[critical_sent]: {
                    GroupedSubstrateNodeAlertsMetricCode.value: bool
                },
                Optional[error_sent]: {
                    GroupedSubstrateNodeAlertsMetricCode.value: bool
                },
                Optional[any_severity_sent]: {
                    GroupedSubstrateNodeAlertsMetricCode.value: bool
                },
                Optional[warning_window_timer]: {
                    GroupedSubstrateNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_window_timer]: {
                    GroupedSubstrateNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_repeat_timer]: {
                    GroupedSubstrateNodeAlertsMetricCode.value: TimedTaskLimiter
                },
                is_validator: bool,
                Optional[eras_state]: {
                    Optional[{era_index}]: {
                        Optional[warning_sent]: {
                            GroupedSubstrateNodeAlertsMetricCode.value: bool
                        },
                        Optional[critical_sent]: {
                            GroupedSubstrateNodeAlertsMetricCode.value: bool
                        },
                    }
                }
            }
        }
    }
    """

    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)

    def create_alerting_state(
            self, parent_id: str, node_id: str,
            alerts_config: SubstrateNodeAlertsConfig,
            is_validator: bool) -> None:
        """
        If no state is already stored, this function will create a new alerting
        state for a node based on the passed alerts config. Note that the stored
        configuration depends on if the node is a validator or not. If the
        is_validator value is changed mid-way through the program, we will
        modify the limiter thresholds during runtime.
        :param parent_id: The id of the chain
        :param node_id: The id of the node
        :param alerts_config: The alerts configuration
        :param is_validator: Whether the node is a validator or not
        :return: None
        """

        if parent_id not in self.alerting_state:
            self.alerting_state[parent_id] = {}

        if node_id not in self.alerting_state[parent_id]:
            warning_sent = {
                AlertsMetricCode.NodeIsDown.value: False,
                AlertsMetricCode.NoChangeInBestBlockHeight.value: False,
                AlertsMetricCode.NoChangeInFinalizedBlockHeight.value: False,
                AlertsMetricCode.NodeIsSyncing.value: False,
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value
                 ): False,
            }
            critical_sent = {
                AlertsMetricCode.NodeIsDown.value: False,
                AlertsMetricCode.NoChangeInBestBlockHeight.value: False,
                AlertsMetricCode.NoChangeInFinalizedBlockHeight.value: False,
                AlertsMetricCode.NodeIsSyncing.value: False,
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value
                 ): False,
            }
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
            self.alerting_state[parent_id][node_id] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
                'error_sent': error_sent,
                'any_severity_sent': any_severity_sent,
                'warning_window_timer': warning_window_timer,
                'critical_window_timer': critical_window_timer,
                'critical_repeat_timer': critical_repeat_timer,
                'is_validator': is_validator
            }
            if is_validator:
                self.alerting_state[parent_id][node_id]['eras_state'] = {}
        elif (self.alerting_state[parent_id][node_id][
                  'is_validator'] != is_validator):
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

            warning_window_timers = self.alerting_state[parent_id][node_id][
                'warning_window_timer']
            critical_window_timers = self.alerting_state[parent_id][node_id][
                'critical_window_timer']
            critical_repeat_timers = self.alerting_state[parent_id][node_id][
                'critical_repeat_timer']

            warning_window_timers[
                AlertsMetricCode.NodeIsDown.value].set_time_interval(timedelta(
                seconds=node_is_down_thresholds['warning_threshold']))
            warning_window_timers[
                AlertsMetricCode.NoChangeInBestBlockHeight.value
            ].set_time_interval(timedelta(
                seconds=no_change_in_best_block_height_thresholds[
                    'warning_threshold']))
            warning_window_timers[
                AlertsMetricCode.NoChangeInFinalizedBlockHeight.value
            ].set_time_interval(timedelta(
                seconds=no_change_in_finalized_block_height_thresholds[
                    'warning_threshold']))
            warning_window_timers[
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value)
            ].set_time_interval(timedelta(
                seconds=send_heartbeat_author_block_thresholds[
                    'warning_threshold']))

            critical_window_timers[
                AlertsMetricCode.NodeIsDown.value].set_time_interval(timedelta(
                seconds=node_is_down_thresholds['critical_threshold']))
            critical_window_timers[
                AlertsMetricCode.NoChangeInBestBlockHeight.value
            ].set_time_interval(timedelta(
                seconds=no_change_in_best_block_height_thresholds[
                    'critical_threshold']))
            critical_window_timers[
                AlertsMetricCode.NoChangeInFinalizedBlockHeight.value
            ].set_time_interval(timedelta(
                seconds=no_change_in_finalized_block_height_thresholds[
                    'critical_threshold']))
            critical_window_timers[
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value)
            ].set_time_interval(timedelta(
                seconds=send_heartbeat_author_block_thresholds[
                    'critical_threshold']))

            critical_repeat_timers[
                AlertsMetricCode.NodeIsDown.value].set_time_interval(timedelta(
                seconds=node_is_down_thresholds['critical_repeat']))
            critical_repeat_timers[
                AlertsMetricCode.NoChangeInBestBlockHeight.value
            ].set_time_interval(timedelta(
                seconds=no_change_in_best_block_height_thresholds[
                    'critical_repeat']))
            critical_repeat_timers[
                AlertsMetricCode.NoChangeInFinalizedBlockHeight.value
            ].set_time_interval(timedelta(
                seconds=no_change_in_finalized_block_height_thresholds[
                    'critical_repeat']))
            critical_repeat_timers[
                AlertsMetricCode.NodeIsSyncing.value].set_time_interval(
                timedelta(seconds=node_is_syncing_thresholds['critical_repeat'])
            )
            critical_repeat_timers[
                (AlertsMetricCode.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert.value)
            ].set_time_interval(timedelta(
                seconds=send_heartbeat_author_block_thresholds[
                    'critical_repeat']))

            self.alerting_state[parent_id][node_id][
                'is_validator'] = is_validator
            if is_validator:
                self.alerting_state[parent_id][node_id]['eras_state'] = {}
            elif 'eras_state' in self.alerting_state[parent_id][node_id]:
                del self.alerting_state[parent_id][node_id]['eras_state']

    def remove_chain_alerting_state(self, parent_id: str) -> None:
        """
        This function deletes an entire alerting state for a chain.
        :param parent_id: The id of the chain to be deleted
        :return: None
        """
        if parent_id in self.alerting_state:
            del self.alerting_state[parent_id]

    def create_era_alerting_state(self, parent_id: str, node_id: str,
                                  era_index: int):
        """
        If no era state is already stored, this function will create a new
        alerting state for an era based on the passed parent_id and node_id
        :param parent_id: The id of the chain
        :param node_id: The id of the node
        :param era_index: The index of the era
        :return: None
        """
        eras_state = self.alerting_state[parent_id][node_id]['eras_state']
        if era_index not in eras_state:
            warning_sent = {
                AlertsMetricCode.ValidatorPayoutNotClaimed: False,
            }
            critical_sent = {
                AlertsMetricCode.ValidatorPayoutNotClaimed: False,
            }
            eras_state[era_index] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
            }

    def remove_era_alerting_state(self, parent_id: str, node_id: str,
                                  era_index: int):
        """
        This function deletes an era alerting state for a given node.
        :param parent_id: The id of the chain which contains the node state
        :param node_id: The id of the node which contains the era state
        :param era_index: The index of the era to be deleted
        :return: None
        """
        eras_state = self.alerting_state[parent_id][node_id]['eras_state']
        if era_index in eras_state:
            del eras_state[era_index]

    def classify_thresholded_era_alert(
            self, era_occurred: int, era_difference: int, config: Dict,
            increased_above_threshold_alert:
            Type[IncreasedAboveSubstrateEraThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a critical/warning increase above threshold alert
        if the current era value is bigger than the respective era thresholds. 
        If the critical repeat era threshold is constantly elapsed, 
        the increase alert is re-raised with a critical severity each time. 
        :param era_occurred: The era at which the event occurred at
        :param era_difference: The difference in eras from event till now
        :param config: The metric's configuration to obtain the thresholds
        :param increased_above_threshold_alert: The alert to be raised if the
        current era value is no longer smaller than an era threshold
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param metric_name: The name of the metric
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :return: None
        """
        self.create_era_alerting_state(parent_id, monitorable_id, era_occurred)
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'eras_state'][era_occurred]['warning_sent']

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        critical_repeat_threshold = convert_to_float(config['critical_repeat'],
                                                     None)
        critical_repeat_enabled = str_to_bool(config['critical_repeat_enabled'])
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            'eras_state'][era_occurred]['critical_sent']

        # Check if the current value is bigger than any of the thresholds.
        # First check for critical and do not raise a warning alert if we are
        # immediately in critical state.
        if critical_enabled and era_difference >= critical_threshold:
            if not critical_sent[metric_name]:
                alert = increased_above_threshold_alert(
                    monitorable_name, era_occurred, era_difference,
                    Severity.CRITICAL.value, monitoring_timestamp,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                critical_sent[metric_name] = True
            elif (critical_repeat_enabled and
                  (era_difference - critical_threshold != 0) and
                  (era_difference - critical_threshold) %
                  critical_repeat_threshold == 0):
                alert = increased_above_threshold_alert(
                    monitorable_name, era_occurred, era_difference,
                    Severity.CRITICAL.value, monitoring_timestamp,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)

        if (warning_enabled
                and not warning_sent[metric_name]
                and not critical_sent[metric_name]
                and era_difference >= warning_threshold):
            alert = increased_above_threshold_alert(
                monitorable_name, era_occurred, era_difference,
                Severity.WARNING.value, monitoring_timestamp,
                parent_id, monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            warning_sent[metric_name] = True

    def classify_era_solve_alert(
            self, era_occurred: int, alert: Type[SolvedSubstrateEraAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a solved substrate era alert and removes the era
        alerting state of the given era if state for the given era exists.
        :param era_occurred: The era at which the event occurred at
        :param alert: The alert to be raised
        :param data_for_alerting: The list to be appended with alerts
        :param parent_id: The id of the base chain
        :param monitorable_id: The id of the monitorable
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :return: None
        """
        eras_state = self.alerting_state[parent_id][monitorable_id][
            'eras_state']
        if era_occurred in eras_state:
            self.remove_era_alerting_state(parent_id, monitorable_id,
                                           era_occurred)
            alert = alert(monitorable_name, era_occurred, Severity.INFO,
                          monitoring_timestamp, parent_id, monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)

    def classify_conditional_no_change_in_alert(
            self, current: Any, previous: Any, config: Dict,
            conditional_no_change_alert: Type[ConditionalNoChangeInAlert],
            conditional_change_alert: Type[ConditionalChangeInAlert],
            condition_function: Callable, condition_fn_args: List[Any],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a critical/warning no conditional change alert
        if the respective time window thresholds elapse and the condition
        function returns true. If the critical repeat time is constantly
        elapsed, the no change alert is re-raised with a critical
        severity each time. This function assumes that a problem is solved
        whenever a change occurs or the condition function returns false,
        in that case a related info alert is raised.
        :param current: Current metric value
        :param previous: Previous metric value
        :param config: The metric's configuration to obtain the thresholds
        :param conditional_no_change_alert: The alert to be raised if there is
        no change and conditional function is met
        :param conditional_change_alert: The alert to be raised if the problem
        is solved
        :param condition_function: The condition function to be checked
        :param condition_fn_args: The args to pass to the condition function
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
        warning_window_timer = self.alerting_state[parent_id][monitorable_id][
            'warning_window_timer'][metric_name]
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'warning_sent']

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_repeat_enabled = str_to_bool(config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id]['critical_repeat_timer'][metric_name]
        critical_window_timer = self.alerting_state[parent_id][monitorable_id][
            'critical_window_timer'][metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            'critical_sent']

        monitoring_datetime = datetime.fromtimestamp(monitoring_timestamp)

        if current == previous and condition_function(*condition_fn_args):
            # We do not want to raise a warning alert if we are immediately in
            # critical state, therefore first we need to check if a critical
            # alert can be raised, and if it can we don't raise a warning alert.
            if critical_enabled:
                if not critical_window_timer.timer_started:
                    critical_window_timer.start_timer(monitoring_datetime)
                elif critical_window_timer.can_do_task(monitoring_datetime):
                    duration = (monitoring_timestamp -
                                critical_window_timer.start_time.replace(
                                    tzinfo=timezone.utc).timestamp())
                    alert = conditional_no_change_alert(
                        monitorable_name, current, duration,
                        Severity.CRITICAL.value, monitoring_timestamp,
                        parent_id, monitorable_id)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    self.alerting_state[parent_id][monitorable_id][
                        'critical_sent'][metric_name] = True
                    critical_window_timer.do_task()
                    critical_repeat_limiter.set_last_time_that_did_task(
                        monitoring_datetime)
                elif (critical_sent[metric_name]
                      and critical_repeat_enabled
                      and critical_repeat_limiter.can_do_task(
                            monitoring_datetime)):
                    duration = (monitoring_timestamp -
                                critical_window_timer.start_time.replace(
                                    tzinfo=timezone.utc).timestamp())
                    alert = conditional_no_change_alert(
                        monitorable_name, current, duration,
                        Severity.CRITICAL.value, monitoring_timestamp,
                        parent_id, monitorable_id)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    critical_repeat_limiter.set_last_time_that_did_task(
                        monitoring_datetime)

            if warning_enabled:
                if not warning_window_timer.timer_started:
                    warning_window_timer.start_timer(monitoring_datetime)
                elif (not critical_sent[metric_name]
                      and warning_window_timer.can_do_task(
                            monitoring_datetime)):
                    duration = (monitoring_timestamp -
                                warning_window_timer.start_time.replace(
                                    tzinfo=timezone.utc).timestamp())
                    alert = conditional_no_change_alert(
                        monitorable_name, current, duration,
                        Severity.WARNING.value, monitoring_timestamp,
                        parent_id, monitorable_id)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    warning_window_timer.do_task()
                    self.alerting_state[parent_id][monitorable_id][
                        'warning_sent'][metric_name] = True
        elif current != previous:
            warning_window_timer.reset()
            critical_window_timer.reset()
            critical_repeat_limiter.reset()
            self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                metric_name] = False
            self.alerting_state[parent_id][monitorable_id]['critical_sent'][
                metric_name] = False
        else:
            warning_window_timer.reset()
            critical_window_timer.reset()
            critical_repeat_limiter.reset()
            if warning_sent[metric_name] or critical_sent[metric_name]:
                alert = conditional_change_alert(
                    monitorable_name, previous, Severity.INFO.value,
                    monitoring_timestamp, parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    'warning_sent'][metric_name] = False
                self.alerting_state[parent_id][monitorable_id][
                    'critical_sent'][metric_name] = False

    def classify_websocket_error_alert(
            self, error_code_to_detect: int,
            error_alert: Type[ErrorAlert],
            error_solved_alert: Type[ErrorSolvedAlert], data_for_alerting: List,
            parent_id: str, monitorable_id: str, monitorable_name: str,
            monitoring_timestamp: float, metric_name: str,
            error_message: str = "", resolved_message: str = "",
            received_error_code: int = None,
    ) -> None:
        """
        This function acts as a wrapper around the classify_error_alert
        function. This is done so that we do not classify other error alerts
        relating to the websocket source if the Substrate API is not reachable.
        """
        substrate_api_error_sent = (
            self.alerting_state[parent_id][monitorable_id]['error_sent'][
                AlertsMetricCode.SubstrateApiNotReachable.value])

        # For this to work, we need to classify the Substrate API Not Reachable
        # alert before every other possible alert
        if (not substrate_api_error_sent or received_error_code !=
                SubstrateApiIsNotReachableException.code):
            super().classify_error_alert(
                error_code_to_detect, error_alert, error_solved_alert,
                data_for_alerting, parent_id, monitorable_id,
                monitorable_name, monitoring_timestamp, metric_name,
                error_message, resolved_message, received_error_code
            )

    def classify_downtime_alert_with_substrate_api_downtime(
            self, current_went_down: Optional[float], config: Dict,
            went_down_at_alert: Type[DownAlert],
            still_down_alert: Type[StillDownAlert],
            back_up_alert: Type[BackUpAlert], data_for_alerting: List,
            parent_id: str, monitorable_id: str, metric_name: str,
            monitorable_name: str, monitoring_timestamp: float,
    ) -> None:
        """
        This function acts as a wrapper around the classify_downtime_alert
        function. This is done so that we do not classify downtime if the
        Substrate API is not reachable. This should only be used for downtime
        relating to the websocket source if the Substrate API is not reachable.
        """
        substrate_api_error_sent = (
            self.alerting_state[parent_id][monitorable_id]['error_sent'][
                AlertsMetricCode.SubstrateApiNotReachable.value])

        # For this to work, we need to classify the Substrate API Not Reachable
        # alert before every other possible alert
        if not substrate_api_error_sent:
            super().classify_downtime_alert(
                current_went_down, config, went_down_at_alert, still_down_alert,
                back_up_alert, data_for_alerting, parent_id, monitorable_id,
                metric_name, monitorable_name, monitoring_timestamp
            )
