import logging
from datetime import timedelta

from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)


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
                AlertsMetricCode.EthBalanceThreshold.value: False,
                AlertsMetricCode.NodeIsDown.value: False,
                AlertsMetricCode.PrometheusSourceIsDown.value: False
            }
            critical_sent = {
                AlertsMetricCode.NoChangeInHeight.value: False,
                AlertsMetricCode.NoChangeInTotalHeadersReceived.value: False,
                AlertsMetricCode.MaxUnconfirmedBlocksThreshold.value: False,
                AlertsMetricCode.NoOfUnconfirmedTxsThreshold.value: False,
                AlertsMetricCode.TotalErroredJobRunsThreshold.value: False,
                AlertsMetricCode.EthBalanceThreshold.value: False,
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
            eth_balance_thresholds = parse_alert_time_thresholds(
                ['critical_repeat'], cl_node_alerts_config.eth_balance_amount
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
                AlertsMetricCode.EthBalanceThreshold.value: TimedTaskLimiter(
                    timedelta(seconds=eth_balance_thresholds[
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
