import logging
from abc import abstractmethod, ABC
from datetime import datetime, timezone
from typing import Dict, List, Any, Type, Callable, Optional

from src.alerter.alert_severities import Severity
from src.utils.types import (NoChangeInAlert, ChangeInAlert, str_to_bool,
                             IncreasedAboveThresholdAlert,
                             DecreasedBelowThresholdAlert, convert_to_float,
                             ErrorAlert, ErrorSolvedAlert,
                             ConditionalAlert, DownAlert,
                             StillDownAlert, BackUpAlert)


class AlertingFactory(ABC):
    def __init__(self, component_logger: logging.Logger) -> None:
        """
        The alerting_state dict is to be structured as follows by the
        sub-classes. Note some functions cannot be used if some of the fields
        in the json structure are omitted:
        {
        <parent_id>: {
            <monitorable_id>: {
                Optional[warning_sent]: {
                    GroupedAlertsMetricCode.value: bool
                },
                Optional[critical_sent]: {
                    GroupedAlertsMetricCode.value: bool
                },
                Optional[error_sent]: {
                    GroupedAlertsMetricCode.value: bool
                },
                Optional[warning_window_timer]: {
                    GroupedAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_window_timer]: {
                    GroupedAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_repeat_timer]: {
                    GroupedAlertsMetricCode.value: TimedTaskLimiter
                },
                Optional[warning_occurrences_in_period_tracker]: {
                    GroupedAlertsMetricCode.value:
                        OccurrencesInTimePeriodTracker
                },
                Optional[critical_occurrences_in_period_tracker]: {
                    GroupedAlertsMetricCode.value:
                        OccurrencesInTimePeriodTracker
                },
            }
        }}
        """
        self._alerting_state = {}
        self._component_logger = component_logger

    @property
    def alerting_state(self) -> Dict:
        return self._alerting_state

    @property
    def component_logger(self) -> logging.Logger:
        return self._component_logger

    @abstractmethod
    def create_alerting_state(self, *args) -> None:
        pass

    def classify_no_change_in_alert(
            self, current: Any, previous: Any, config: Dict,
            no_change_alert: Type[NoChangeInAlert],
            change_alert: Type[ChangeInAlert], data_for_alerting: List,
            parent_id: str, monitorable_id: str, metric_name: str,
            monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a critical/warning no change alert if the
        respective time window thresholds elapse. If the critical repeat time is
        constantly elapsed, the no change alert is re-raised with a critical
        severity each time. This function assumes that a problem is solved
        whenever a change occurs, in that case a related info alert is raised.
        :param current: Current metric value
        :param previous: Previous metric value
        :param config: The metric's configuration to obtain the thresholds
        :param no_change_alert: The alert to be raised if there is no change
        :param change_alert: The alert to be raised if the problem is solved
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

        if current == previous:
            # We do not want to raise a warning alert if we are immediately in
            # critical state, therefore first we need to check if a critical
            # alert can be raised, and if it can we don't raise a warning alert.
            if critical_enabled:
                if not critical_window_timer.timer_started:
                    critical_window_timer.start_timer(monitoring_datetime)
                elif critical_window_timer.can_do_task(monitoring_datetime):
                    duration = monitoring_timestamp - \
                               critical_window_timer.start_time.replace(
                                   tzinfo=timezone.utc).timestamp()
                    alert = no_change_alert(
                        monitorable_name, duration, Severity.CRITICAL.value,
                        monitoring_timestamp, parent_id, monitorable_id,
                        current)
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
                    duration = monitoring_timestamp - \
                               critical_window_timer.start_time.replace(
                                   tzinfo=timezone.utc).timestamp()
                    alert = no_change_alert(
                        monitorable_name, duration, Severity.CRITICAL.value,
                        monitoring_timestamp, parent_id, monitorable_id,
                        current)
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
                    duration = monitoring_timestamp - \
                               warning_window_timer.start_time.replace(
                                   tzinfo=timezone.utc).timestamp()
                    alert = no_change_alert(
                        monitorable_name, duration, Severity.WARNING.value,
                        monitoring_timestamp, parent_id, monitorable_id,
                        current)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    warning_window_timer.do_task()
                    self.alerting_state[parent_id][monitorable_id][
                        'warning_sent'][metric_name] = True
        else:
            if warning_sent[metric_name] or critical_sent[metric_name]:
                alert = change_alert(
                    monitorable_name, Severity.INFO.value, monitoring_timestamp,
                    parent_id, monitorable_id, current)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    'warning_sent'][metric_name] = False
                self.alerting_state[parent_id][monitorable_id][
                    'critical_sent'][metric_name] = False
                warning_window_timer.reset()
                critical_window_timer.reset()
                critical_repeat_limiter.reset()

    def classify_thresholded_time_window_alert(
            self, current: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, monitoring_timestamp: float
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
        :param metric_name: The name of the metric
        :param monitorable_name: The name of the monitorable
        :param monitoring_timestamp: The data timestamp
        :return: None
        """
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        warning_window_timer = self.alerting_state[parent_id][monitorable_id][
            'warning_window_timer'][metric_name]
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'warning_sent']

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        critical_repeat_enabled = str_to_bool(config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id]['critical_repeat_timer'][metric_name]
        critical_window_timer = self.alerting_state[parent_id][monitorable_id][
            'critical_window_timer'][metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            'critical_sent']

        monitoring_datetime = datetime.fromtimestamp(monitoring_timestamp)

        # First check if there was a decrease so that an info alert is raised.
        # First check for critical as it is expected that
        # warning_threshold <= critical_threshold

        if critical_sent[metric_name] and current < critical_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp,
                Severity.CRITICAL.value, parent_id, monitorable_id, )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug(
                "Successfully classified alert %s", alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'critical_sent'][metric_name] = False
            critical_window_timer.reset()
            critical_repeat_limiter.reset()

            # If this is the case we still need to raise a warning alert to
            # show the correct metric state in the UI.
            if warning_sent[metric_name] and current >= warning_threshold:
                warning_window_timer.start_timer(
                    warning_window_timer.start_time)
                self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                    metric_name] = False

        if warning_sent[metric_name] and current < warning_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp,
                Severity.WARNING.value, parent_id, monitorable_id, )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug(
                "Successfully classified alert %s", alert.alert_data)
            self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                metric_name] = False
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
                    'critical_sent'][metric_name] = True
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
                    parent_id,
                    monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                warning_window_timer.do_task()
                self.alerting_state[parent_id][monitorable_id][
                    'warning_sent'][metric_name] = True

    def classify_thresholded_in_time_period_alert(
            self, current: Any, previous: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a critical/warning increase above threshold alert
        if the respective thresholds are surpassed within a time period. If the
        critical repeat time is constantly elapsed, the increase alert is
        re-raised with a critical severity each time. Also, a decrease below
        threshold info alert is raised whenever a threshold is no longer
        surpassed. Note, a warning increase is re-raised if
        warning_threshold <= current < critical_threshold <= previous. This is
        done so that in the UI the respective metric is shown in warning state
        and not in info state.
        :param current: Current metric value
        :param previous: The metric's previous value
        :param config: The metric's configuration to obtain the thresholds
        :param increased_above_threshold_alert: The alert to be raised if a
        threshold is surpassed within a time period
        :param decreased_below_threshold_alert: The alert to be raised if a
        threshold is no longer surpassed
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
        warning_occurrences_tracker = self.alerting_state[parent_id][
            monitorable_id]['warning_occurrences_in_period_tracker'][
            metric_name]
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'warning_sent']
        warning_period = convert_to_float(config['warning_time_window'], None)

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        critical_repeat_enabled = str_to_bool(config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id]['critical_repeat_timer'][metric_name]
        critical_occurrences_tracker = self.alerting_state[parent_id][
            monitorable_id]['critical_occurrences_in_period_tracker'][
            metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            'critical_sent']
        critical_period = convert_to_float(config['critical_time_window'], None)

        monitoring_datetime = datetime.fromtimestamp(monitoring_timestamp)

        # First calculate how many occurrences have occurred in a time period,
        # then alert accordingly.
        occurrences = current - previous
        if occurrences > 0:
            for i in range(occurrences):
                # add_occurrence calls remove_old_occurrences
                warning_occurrences_tracker.add_occurrence(monitoring_datetime)
                critical_occurrences_tracker.add_occurrence(monitoring_datetime)
        else:
            warning_occurrences_tracker.remove_old_occurrences(
                monitoring_datetime)
            critical_occurrences_tracker.remove_old_occurrences(
                monitoring_datetime)

        warning_occurrences = warning_occurrences_tracker.no_of_occurrences()
        critical_occurrences = critical_occurrences_tracker.no_of_occurrences()

        # First check if there was a decrease so that an info alert is raised.
        # First check for critical as it is expected that
        # warning_threshold <= critical_threshold

        if (critical_sent[metric_name]
                and critical_occurrences < critical_threshold):
            alert = decreased_below_threshold_alert(
                monitorable_name, critical_occurrences, Severity.INFO.value,
                monitoring_timestamp, critical_period, Severity.CRITICAL.value,
                parent_id, monitorable_id,)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'critical_sent'][metric_name] = False
            critical_repeat_limiter.reset()

            # If this is the case we still need to raise a warning alert to
            # show the correct metric state in the UI.
            if (warning_sent[metric_name]
                    and warning_occurrences >= warning_threshold):
                self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                    metric_name] = False

        if (warning_sent[metric_name]
                and warning_occurrences < warning_threshold):
            alert = decreased_below_threshold_alert(
                monitorable_name, warning_occurrences, Severity.INFO.value,
                monitoring_timestamp, warning_period, Severity.WARNING.value,
                parent_id, monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                metric_name] = False

        # Now check if any of the thresholds are surpassed within the time
        # period. First check for critical and do not raise a warning alert if
        # we are immediately in critical state

        if critical_enabled and critical_occurrences >= critical_threshold:
            if not critical_sent[metric_name]:
                alert = increased_above_threshold_alert(
                    monitorable_name, critical_occurrences,
                    Severity.CRITICAL.value, monitoring_timestamp,
                    critical_period, Severity.CRITICAL.value, parent_id,
                    monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    'critical_sent'][metric_name] = True
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)
            elif (critical_repeat_enabled
                  and critical_repeat_limiter.can_do_task(monitoring_datetime)):
                alert = increased_above_threshold_alert(
                    monitorable_name, critical_occurrences,
                    Severity.CRITICAL.value, monitoring_timestamp,
                    critical_period, Severity.CRITICAL.value, parent_id,
                    monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)

        if (warning_enabled
                and not warning_sent[metric_name]
                and not critical_sent[metric_name]
                and warning_occurrences >= warning_threshold):
            alert = increased_above_threshold_alert(
                monitorable_name, warning_occurrences, Severity.WARNING.value,
                monitoring_timestamp, warning_period, Severity.WARNING.value,
                parent_id, monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'warning_sent'][metric_name] = True

    def classify_conditional_alert(
            self, condition_true_alert: Type[ConditionalAlert],
            condition_function: Callable, condition_fn_args: List[Any],
            alert_args: List[Any], data_for_alerting: List,
            condition_false_alert: Type[ConditionalAlert] = None
    ) -> None:
        if condition_function(*condition_fn_args):
            alert = condition_true_alert(*alert_args)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
        elif condition_false_alert is not None:
            alert = condition_false_alert(*alert_args)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)

    def classify_thresholded_alert_reverse(
            self, current: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        This function raises a critical/warning decrease below threshold alert
        if the current value is smaller than the respective thresholds. If the
        critical repeat time is constantly elapsed, the decrease alert is
        re-raised with a critical severity each time. Also, an increase above
        threshold info alert is raised whenever the current value is greater
        than a threshold. Note, a warning decrease is re-raised if
        warning_threshold >= current > critical_threshold >= previous. This is
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
            'warning_sent']

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        critical_repeat_enabled = str_to_bool(config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id]['critical_repeat_timer'][metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            'critical_sent']

        monitoring_datetime = datetime.fromtimestamp(monitoring_timestamp)

        # First check if there was an increase so that an info alert is raised.
        # First check for critical as it is expected that
        # warning_threshold >= critical_threshold

        if critical_sent[metric_name] and current > critical_threshold:
            alert = increased_above_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'critical_sent'][metric_name] = False
            critical_repeat_limiter.reset()

            # If this is the case we still need to raise a warning alert to
            # show the correct metric state in the UI.
            if warning_sent[metric_name] and current <= warning_threshold:
                self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                    metric_name] = False

        if warning_sent[metric_name] and current > warning_threshold:
            alert = increased_above_threshold_alert(
                monitorable_name, current, Severity.INFO.value,
                monitoring_timestamp, Severity.WARNING.value, parent_id,
                monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                metric_name] = False

        # Now check if the current value is smaller than any of the thresholds.
        # First check for critical and do not raise a warning alert if we are
        # immediately in critical state.

        if critical_enabled and current <= critical_threshold:
            if not critical_sent[metric_name]:
                alert = decreased_below_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                    monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    'critical_sent'][metric_name] = True
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)
            elif (critical_repeat_enabled
                  and critical_repeat_limiter.can_do_task(monitoring_datetime)):
                alert = decreased_below_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    monitoring_timestamp, Severity.CRITICAL.value, parent_id,
                    monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)

        if (warning_enabled
                and not warning_sent[metric_name]
                and not critical_sent[metric_name]
                and current <= warning_threshold):
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.WARNING.value,
                monitoring_timestamp, Severity.WARNING.value, parent_id,
                monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'warning_sent'][metric_name] = True

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

        error_sent = self.alerting_state[parent_id][monitorable_id][
            'error_sent'][metric_name]

        if error_sent and received_error_code != error_code_to_detect:
            alert = error_solved_alert(
                monitorable_name, resolved_message, Severity.INFO.value,
                monitoring_timestamp, parent_id, monitorable_id
            )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'error_sent'][metric_name] = False
        elif received_error_code == error_code_to_detect:
            alert = error_alert(
                monitorable_name, error_message, Severity.ERROR.value,
                monitoring_timestamp, parent_id, monitorable_id
            )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'error_sent'][metric_name] = True

    def classify_downtime_alert(
            self, current_went_down: Optional[float], config: Dict,
            went_down_at_alert: Type[DownAlert],
            still_down_alert: Type[StillDownAlert],
            back_up_alert: Type[BackUpAlert], data_for_alerting: List,
            parent_id: str, monitorable_id: str, metric_name: str,
            monitorable_name: str, monitoring_timestamp: float,
    ) -> None:
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

        if current_went_down is None:
            if warning_sent[metric_name] or critical_sent[metric_name]:
                alert = back_up_alert(
                    monitorable_name, Severity.INFO.value, monitoring_timestamp,
                    parent_id, monitorable_id
                )
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    'warning_sent'][metric_name] = False
                self.alerting_state[parent_id][monitorable_id][
                    'critical_sent'][metric_name] = False
                warning_window_timer.reset()
                critical_window_timer.reset()
                critical_repeat_limiter.reset()
        else:
            went_down_datetime = datetime.fromtimestamp(current_went_down)
            if critical_enabled:
                if not critical_window_timer.timer_started:
                    critical_window_timer.start_timer(went_down_datetime)
                elif critical_window_timer.can_do_task(monitoring_datetime):
                    alert = went_down_at_alert(
                        monitorable_name, Severity.CRITICAL.value,
                        monitoring_timestamp, parent_id, monitorable_id)
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
                    difference = monitoring_timestamp - current_went_down
                    alert = still_down_alert(
                        monitorable_name, difference, Severity.CRITICAL.value,
                        monitoring_timestamp, parent_id, monitorable_id)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    critical_repeat_limiter.set_last_time_that_did_task(
                        monitoring_datetime)

            if warning_enabled:
                if not warning_window_timer.timer_started:
                    warning_window_timer.start_timer(went_down_datetime)
                elif not critical_sent[metric_name] and \
                        warning_window_timer.can_do_task(monitoring_datetime):
                    alert = went_down_at_alert(
                        monitorable_name, Severity.WARNING.value,
                        monitoring_timestamp, parent_id, monitorable_id)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    warning_window_timer.do_task()
                    self.alerting_state[parent_id][monitorable_id][
                        'warning_sent'][metric_name] = True

    def classify_source_downtime_alert(
            self, condition_true_alert: Type[ConditionalAlert],
            condition_function: Callable, condition_fn_args: List[Any],
            alert_args: List[Any], data_for_alerting: List,
            parent_id: str, monitorable_id: str, metric_name: str,
            condition_false_alert: Type[ConditionalAlert] = None,
    ) -> None:
        """
        This function operators exactly as the classify_conditional_alert with
        the only difference being that we are not alerting repetitively if the
        condition no longer is true. In the case of source downtime, this
        prevents BackUpAgain alerts from being re-raised again.
        """
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'warning_sent']
        if condition_function(*condition_fn_args):
            alert = condition_true_alert(*alert_args)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'warning_sent'][metric_name] = True
        elif condition_false_alert is not None and warning_sent[metric_name]:
            alert = condition_false_alert(*alert_args)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'warning_sent'][metric_name] = False
