import logging
from abc import abstractmethod, ABC
from datetime import datetime
from typing import Dict, List, Any, Type

from src.alerter.alert_severities import Severity
from src.utils.types import (NoChangeInAlert, ChangeInAlert, str_to_bool,
                             IncreasedAboveThresholdAlert,
                             DecreasedBelowThresholdAlert, convert_to_float,
                             SeverityAlert)


class AlertingFactory(ABC):
    def __init__(self, component_logger: logging.Logger) -> None:
        """
        The alerting_state dict is to be structured as follows by the
        sub-classes:
        {
            <parent_id>: {
                <monitorable_id>: {
                    Optional[warning_sent]: {
                        GroupedAlertsMetricCode.value: bool
                    },
                    Optional[critical_sent]: {
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
                }
            }
        }
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

    def _classify_no_change_in_alert(
            self, current: Any, previous: Any, config: Dict,
            no_change_alert: Type[NoChangeInAlert],
            change_alert: Type[ChangeInAlert], data_for_alerting: List,
            parent_id: str, monitorable_id: str, metric_name: str,
            monitorable_name: str, last_monitored: float
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
        :param last_monitored: The data timestamp
        :return: None
        """
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_window_timer = self.alerting_state[parent_id][monitorable_id][
            'warning_window_timer'][metric_name]
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'warning_sent'][metric_name]

        # Parse critical thresholds and limiters
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_repeat_enabled = str_to_bool(config['critical_repeat_enabled'])
        critical_repeat_limiter = self.alerting_state[parent_id][
            monitorable_id]['critical_repeat_timer'][metric_name]
        critical_window_timer = self.alerting_state[parent_id][monitorable_id][
            'critical_window_timer'][metric_name]
        critical_sent = self.alerting_state[parent_id][monitorable_id][
            'critical_sent'][metric_name]

        monitoring_datetime = datetime.fromtimestamp(last_monitored)

        if current == previous:
            # We do not want to raise a warning alert if we are immediately in
            # critical state, therefore first we need to check if a critical
            # alert can be raised, and if it can we don't raise a warning alert.
            if critical_enabled:
                if not critical_window_timer.timer_started:
                    critical_window_timer.start_timer(monitoring_datetime)
                elif critical_window_timer.can_do_task(monitoring_datetime):
                    duration = last_monitored - \
                               critical_window_timer.start_time.timestamp()
                    alert = no_change_alert(
                        monitorable_name, duration, Severity.CRITICAL.value,
                        last_monitored, parent_id, monitorable_id, current)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    self.alerting_state[parent_id][monitorable_id][
                        'critical_sent'][metric_name] = True
                    critical_window_timer.do_task()
                    critical_repeat_limiter.set_last_time_that_did_task(
                        monitoring_datetime)
                elif (critical_sent
                      and critical_repeat_enabled
                      and critical_repeat_limiter.can_do_task(
                            monitoring_datetime)):
                    duration = last_monitored - \
                               critical_window_timer.start_time.timestamp()
                    alert = no_change_alert(
                        monitorable_name, duration, Severity.CRITICAL.value,
                        last_monitored, parent_id, monitorable_id, current)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    critical_repeat_limiter.set_last_time_that_did_task(
                        monitoring_datetime)

            if warning_enabled:
                if not warning_window_timer.timer_started:
                    warning_window_timer.start_timer(monitoring_datetime)
                elif not critical_sent and warning_window_timer.can_do_task(
                        monitoring_datetime):
                    duration = last_monitored - \
                               warning_window_timer.start_time.timestamp()
                    alert = no_change_alert(
                        monitorable_name, duration, Severity.WARNING.value,
                        last_monitored, parent_id, monitorable_id, current)
                    data_for_alerting.append(alert.alert_data)
                    self.component_logger.debug(
                        "Successfully classified alert %s", alert.alert_data)
                    warning_window_timer.do_task()
                    self.alerting_state[parent_id][monitorable_id][
                        'warning_sent'][metric_name] = True
        else:
            if warning_sent or critical_sent:
                alert = change_alert(
                    monitorable_name, Severity.INFO.value, last_monitored,
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

    def _classify_thresholded_time_window_alert(
            self, current: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, last_monitored: float
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
        :param last_monitored: The data timestamp
        :return: None
        """
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        warning_window_timer = self.alerting_state[parent_id][monitorable_id][
            'warning_window_timer'][metric_name]
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'warning_sent'][metric_name]

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
            'critical_sent'][metric_name]

        monitoring_datetime = datetime.fromtimestamp(last_monitored)

        # First check if there was a decrease so that an info alert is raised.
        # First check for critical as it is expected that
        # warning_threshold <= critical_threshold

        if critical_sent and current < critical_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value, last_monitored,
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
            if warning_sent and current >= warning_threshold:
                warning_window_timer.start_timer(
                    warning_window_timer.start_time)
                self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                    metric_name] = False

        if warning_sent and current < warning_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, current, Severity.INFO.value, last_monitored,
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
                duration = last_monitored - \
                           critical_window_timer.start_time.timestamp()
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    last_monitored, duration, Severity.CRITICAL.value,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                self.alerting_state[parent_id][monitorable_id][
                    'critical_sent'][metric_name] = True
                critical_window_timer.do_task()
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)
            elif (critical_sent
                  and critical_repeat_enabled
                  and critical_repeat_limiter.can_do_task(monitoring_datetime)):
                duration = last_monitored - \
                           critical_window_timer.start_time.timestamp()
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.CRITICAL.value,
                    last_monitored, duration, Severity.CRITICAL.value,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)

        if warning_enabled and current >= warning_threshold:
            if not warning_window_timer.timer_started:
                warning_window_timer.start_timer(monitoring_datetime)
            elif not critical_sent and warning_window_timer.can_do_task(
                    monitoring_datetime):
                duration = last_monitored - \
                           warning_window_timer.start_time.timestamp()
                alert = increased_above_threshold_alert(
                    monitorable_name, current, Severity.WARNING.value,
                    last_monitored, duration, Severity.WARNING.value, parent_id,
                    monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug(
                    "Successfully classified alert %s", alert.alert_data)
                warning_window_timer.do_task()
                self.alerting_state[parent_id][monitorable_id][
                    'warning_sent'][metric_name] = True

    def _classify_thresholded_in_time_period_alert(
            self, current: Any, previous: Any, config: Dict,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, last_monitored: float
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
        :param last_monitored: The data timestamp
        :return: None
        """
        # Parse warning thresholds and limiters
        warning_enabled = str_to_bool(config['warning_enabled'])
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        warning_occurrences_tracker = self.alerting_state[parent_id][
            monitorable_id]['warning_occurrences_in_period_tracker'][
            metric_name]
        warning_sent = self.alerting_state[parent_id][monitorable_id][
            'warning_sent'][metric_name]

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
            'critical_sent'][metric_name]

        monitoring_datetime = datetime.fromtimestamp(last_monitored)

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

        if critical_sent and critical_occurrences < critical_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, critical_occurrences, Severity.INFO.value,
                last_monitored, config['critical_time_window'],
                Severity.CRITICAL.value, parent_id, monitorable_id, )
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'critical_sent'][metric_name] = False
            critical_repeat_limiter.reset()

            # If this is the case we still need to raise a warning alert to
            # show the correct metric state in the UI.
            if warning_sent and warning_occurrences >= warning_threshold:
                self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                    metric_name] = False

        if warning_sent and warning_occurrences < warning_threshold:
            alert = decreased_below_threshold_alert(
                monitorable_name, warning_occurrences, Severity.INFO.value,
                last_monitored, config['warning_time_window'],
                Severity.WARNING.value, parent_id, monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                metric_name] = False

        # Now check if any of the thresholds are surpassed within the time
        # period. First check for critical and do not raise a warning alert if
        # we are immediately in critical state

        if critical_enabled and critical_occurrences >= critical_threshold:
            if not critical_sent:
                alert = increased_above_threshold_alert(
                    monitorable_name, critical_occurrences,
                    Severity.CRITICAL.value, last_monitored,
                    config['critical_time_window'], Severity.CRITICAL.value,
                    parent_id, monitorable_id)
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
                    Severity.CRITICAL.value, last_monitored,
                    config['critical_time_window'], Severity.CRITICAL.value,
                    parent_id, monitorable_id)
                data_for_alerting.append(alert.alert_data)
                self.component_logger.debug("Successfully classified alert %s",
                                            alert.alert_data)
                critical_repeat_limiter.set_last_time_that_did_task(
                    monitoring_datetime)

        if (warning_enabled
                and not warning_sent
                and not critical_sent
                and warning_occurrences >= warning_threshold):
            alert = increased_above_threshold_alert(
                monitorable_name, warning_occurrences, Severity.WARNING.value,
                last_monitored, config['warning_time_window'],
                Severity.WARNING.value, parent_id, monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'warning_sent'][metric_name] = True

    def _classify_severity_alert(
            self, severity_alert: Type[SeverityAlert],
            condition: bool, alert_args: List[Any], data_for_alerting: List
    ) -> None:
        """
        This function raises an alert if the passed condition is met.
        :param severity_alert: The alert to be raised
        :param condition: A condition such that if true, the alert is raised
                        : with the passed args
        :param alert_args: The arguments the alert is raised with
        :param data_for_alerting: The list to be appended with alerts
        :return: None
        """
        if condition:
            alert = severity_alert(*alert_args)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
