import logging
from datetime import timedelta, datetime
from typing import Any, Dict, Type, List

from src.alerter.alert_severities import Severity
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)
from src.utils.types import (IncreasedAboveThresholdAlert, convert_to_float,
                             DecreasedBelowThresholdAlert, str_to_bool)


class ChainlinkNodeAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    chainlink node alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            <node_id>: {
                Optional[warning_sent]: {
                    GroupedChainlinkNodeAlertsMetricCode.value: bool
                },
                Optional[critical_sent]: {
                    GroupedChainlinkNodeAlertsMetricCode.value: bool
                },
                Optional[error_sent]: {
                    GroupedChainlinkNodeAlertsMetricCode.value: bool
                },
                Optional[warning_window_timer]: {
                    GroupedChainlinkNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_window_timer]: {
                    GroupedChainlinkNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_repeat_timer]: {
                    GroupedChainlinkNodeAlertsMetricCode.value: TimedTaskLimiter
                },
                Optional[warning_occurrences_in_period_tracker]: {
                    GroupedChainlinkNodeAlertsMetricCode.value:
                    OccurrencesInTimePeriodTracker
                },
                Optional[critical_occurrences_in_period_tracker]: {
                    GroupedChainlinkNodeAlertsMetricCode.value:
                    OccurrencesInTimePeriodTracker
                },
            }
        }
    }
    """

    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)

    def create_alerting_state(
            self, parent_id: str, node_id: str,
            cl_node_alerts_config: ChainlinkNodeAlertsConfig) -> None:
        """
        If no state is already stored, this function will create a new alerting
        state for a node based on the passed alerts config.
        :param parent_id: The id of the chain
        :param node_id: The id of the node
        :param cl_node_alerts_config: The alerts configuration
        :return: None
        """

        if parent_id not in self.alerting_state:
            self.alerting_state[parent_id] = {}

        if node_id not in self.alerting_state[parent_id]:
            warning_sent = {
                AlertsMetricCode.NoChangeInHeight.value: False,
                AlertsMetricCode.NoChangeInTotalHeadersReceived.value: False,
                AlertsMetricCode.MaxUnconfirmedBlocksThreshold.value: False,
                AlertsMetricCode.NoOfUnconfirmedTxsThreshold.value: False,
                AlertsMetricCode.TotalErroredJobRunsThreshold.value: False,
                AlertsMetricCode.BalanceThreshold.value: False,
                AlertsMetricCode.NodeIsDown.value: False,
                AlertsMetricCode.PrometheusSourceIsDown.value: False
            }
            critical_sent = {
                AlertsMetricCode.NoChangeInHeight.value: False,
                AlertsMetricCode.NoChangeInTotalHeadersReceived.value: False,
                AlertsMetricCode.MaxUnconfirmedBlocksThreshold.value: False,
                AlertsMetricCode.NoOfUnconfirmedTxsThreshold.value: False,
                AlertsMetricCode.TotalErroredJobRunsThreshold.value: False,
                AlertsMetricCode.BalanceThreshold.value: False,
                AlertsMetricCode.NodeIsDown.value: False,
            }
            error_sent = {
                AlertsMetricCode.InvalidUrl.value: False,
                AlertsMetricCode.MetricNotFound.value: False,
            }

            current_head_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_node_alerts_config.head_tracker_current_head)
            total_headers_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_node_alerts_config.head_tracker_heads_received_total)
            unconfirmed_blocks_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.max_unconfirmed_blocks
            )
            unconfirmed_txs_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.unconfirmed_transactions
            )
            error_jobs_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.run_status_update_total
            )
            balance_thresholds = parse_alert_time_thresholds(
                ['critical_repeat'], cl_node_alerts_config.balance_amount
            )
            node_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'], cl_node_alerts_config.node_is_down
            )

            warning_window_timer = {
                AlertsMetricCode.NoChangeInHeight.value: TimedTaskTracker(
                    timedelta(seconds=current_head_thresholds[
                        'warning_threshold'])),
                AlertsMetricCode.NoChangeInTotalHeadersReceived.value:
                    TimedTaskTracker(timedelta(seconds=total_headers_thresholds[
                        'warning_threshold'])),
                AlertsMetricCode.MaxUnconfirmedBlocksThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=unconfirmed_blocks_thresholds[
                            'warning_time_window'])),
                AlertsMetricCode.NoOfUnconfirmedTxsThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=unconfirmed_txs_thresholds[
                            'warning_time_window'])),
                AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                    seconds=node_is_down_thresholds['warning_threshold'])),
            }
            critical_window_timer = {
                AlertsMetricCode.NoChangeInHeight.value: TimedTaskTracker(
                    timedelta(seconds=current_head_thresholds[
                        'critical_threshold'])),
                AlertsMetricCode.NoChangeInTotalHeadersReceived.value:
                    TimedTaskTracker(timedelta(seconds=total_headers_thresholds[
                        'critical_threshold'])),
                AlertsMetricCode.MaxUnconfirmedBlocksThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=unconfirmed_blocks_thresholds[
                            'critical_time_window'])),
                AlertsMetricCode.NoOfUnconfirmedTxsThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=unconfirmed_txs_thresholds[
                            'critical_time_window'])),
                AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                    seconds=node_is_down_thresholds['critical_threshold'])),
            }
            critical_repeat_timer = {
                AlertsMetricCode.NoChangeInHeight.value: TimedTaskLimiter(
                    timedelta(seconds=current_head_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.NoChangeInTotalHeadersReceived.value:
                    TimedTaskLimiter(timedelta(seconds=total_headers_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.MaxUnconfirmedBlocksThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=unconfirmed_blocks_thresholds[
                            'critical_repeat'])),
                AlertsMetricCode.NoOfUnconfirmedTxsThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=unconfirmed_txs_thresholds['critical_repeat'])),
                AlertsMetricCode.TotalErroredJobRunsThreshold.value:
                    TimedTaskLimiter(timedelta(seconds=error_jobs_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.BalanceThreshold.value: TimedTaskLimiter(
                    timedelta(seconds=balance_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(timedelta(
                    seconds=node_is_down_thresholds['critical_repeat'])),
            }
            warning_occurrences_in_period_tracker = {
                AlertsMetricCode.TotalErroredJobRunsThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=error_jobs_thresholds['warning_time_window'])),
            }
            critical_occurrences_in_period_tracker = {
                AlertsMetricCode.TotalErroredJobRunsThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=error_jobs_thresholds['critical_time_window'])),
            }

            self.alerting_state[parent_id][node_id] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
                'error_sent': error_sent,
                'warning_window_timer': warning_window_timer,
                'critical_window_timer': critical_window_timer,
                'critical_repeat_timer': critical_repeat_timer,
                'warning_occurrences_in_period_tracker':
                    warning_occurrences_in_period_tracker,
                'critical_occurrences_in_period_tracker':
                    critical_occurrences_in_period_tracker,
            }

    def remove_chain_alerting_state(self, parent_id: str) -> None:
        """
        This function deletes an entire alerting state for a chain.
        :param parent_id: The id of the chain to be deleted
        :return: None
        """
        if parent_id in self.alerting_state:
            del self.alerting_state[parent_id]

    def classify_thresholded_alert_reverse_chainlink_node(
            self, current: Any, config: Dict, symbol: str,
            increased_above_threshold_alert: Type[IncreasedAboveThresholdAlert],
            decreased_below_threshold_alert: Type[DecreasedBelowThresholdAlert],
            data_for_alerting: List, parent_id: str, monitorable_id: str,
            metric_name: str, monitorable_name: str, monitoring_timestamp: float
    ) -> None:
        """
        We are overwriting `classify_thresholded_alert_reverse` of the
        inherited class.
        This function raises a critical/warning decrease below threshold alert
        if the current value is smaller than the respective thresholds. If the
        critical repeat time is constantly elapsed, the decrease alert is
        re-raised with a critical severity each time. Also, an increase above
        threshold info alert is raised whenever the current value is less
        than a threshold. Note, a warning decrease is re-raised if
        warning_threshold >= current > critical_threshold >= previous. This is
        done so that in the UI the respective metric is shown in warning state
        and not in info state.
        :param current: Current metric value
        :param config: The metric's configuration to obtain the thresholds
        :param symbol: The currency symbol of the chain.
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
                monitorable_name, current, symbol, Severity.INFO.value,
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
                monitorable_name, current, symbol, Severity.INFO.value,
                monitoring_timestamp, Severity.WARNING.value, parent_id,
                monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id]['warning_sent'][
                metric_name] = False

        # Now check if the current value is greater than any of the thresholds.
        # First check for critical and do not raise a warning alert if we are
        # immediately in critical state.

        if critical_enabled and current <= critical_threshold:
            if not critical_sent[metric_name]:
                alert = decreased_below_threshold_alert(
                    monitorable_name, current, symbol, Severity.CRITICAL.value,
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
                    monitorable_name, current, symbol, Severity.CRITICAL.value,
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
                monitorable_name, current, symbol, Severity.WARNING.value,
                monitoring_timestamp, Severity.WARNING.value, parent_id,
                monitorable_id)
            data_for_alerting.append(alert.alert_data)
            self.component_logger.debug("Successfully classified alert %s",
                                        alert.alert_data)
            self.alerting_state[parent_id][monitorable_id][
                'warning_sent'][metric_name] = True
