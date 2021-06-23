import logging
from datetime import timedelta
from typing import Dict, List

from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)
from src.utils.types import convert_to_float


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

    @staticmethod
    def _parse_alert_time_thresholds(expected_thresholds: List[str],
                                     config: Dict) -> Dict:
        """
        This function returns a dict containing all time thresholds parsed in
        the appropriate format. The returned thresholds are according to the
        value of expected_thresholds.
        :param config: The sub alert config
        :param expected_thresholds: The time thresholds to parse from the config
        :return: A dict containing all available time thresholds parsed from the
               : alert config. Note a KeyError is raised if a certain threshold
               : cannot be found
        """
        parsed_thresholds = {}
        for threshold in expected_thresholds:
            parsed_thresholds[threshold] = convert_to_float(
                config[threshold], timedelta.max.total_seconds() - 1)

        return parsed_thresholds

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
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : False,
                GroupedChainlinkNodeAlertsMetricCode.
                    NoChangeInTotalHeadersReceived.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    NoOfUnconfirmedTxsThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    False,
            }
            critical_sent = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : False,
                GroupedChainlinkNodeAlertsMetricCode.
                    NoChangeInTotalHeadersReceived.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    NoOfUnconfirmedTxsThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value: False,
                GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
                    False,
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    False,
            }
            error_sent = {
                GroupedChainlinkNodeAlertsMetricCode.InvalidUrl.value: False,
                GroupedChainlinkNodeAlertsMetricCode.MetricNotFound.value:
                    False,
            }

            current_head_thresholds = self._parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_node_alerts_config.head_tracker_current_head)
            heads_in_queue_thresholds = self._parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.head_tracker_heads_in_queue)
            total_headers_thresholds = self._parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_node_alerts_config.head_tracker_heads_received_total)
            dropped_headers_thresholds = self._parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.head_tracker_num_heads_dropped_total
            )
            unconfirmed_blocks_thresholds = self._parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.max_unconfirmed_blocks
            )
            unconfirmed_txs_thresholds = self._parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.unconfirmed_transactions
            )
            error_jobs_thresholds = self._parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'],
                cl_node_alerts_config.run_status_update_total
            )
            eth_balance_thresholds = self._parse_alert_time_thresholds(
                ['critical_repeat'], cl_node_alerts_config.eth_balance_amount
            )
            node_is_down_thresholds = self._parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold',
                 'critical_repeat'], cl_node_alerts_config.node_is_down
            )

            warning_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['warning_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : TimedTaskTracker(timedelta(
                    seconds=heads_in_queue_thresholds['warning_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    NoChangeInTotalHeadersReceived.value:
                    TimedTaskTracker(timedelta(
                        seconds=total_headers_thresholds['warning_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value: TimedTaskTracker(
                    timedelta(seconds=unconfirmed_blocks_thresholds[
                        'warning_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    NoOfUnconfirmedTxsThreshold.value: TimedTaskTracker(
                    timedelta(seconds=unconfirmed_txs_thresholds[
                        'warning_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    TimedTaskTracker(timedelta(seconds=node_is_down_thresholds[
                        'warning_time_window'])),
            }
            critical_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['critical_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : TimedTaskTracker(timedelta(
                    seconds=heads_in_queue_thresholds['critical_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    NoChangeInTotalHeadersReceived.value:
                    TimedTaskTracker(timedelta(seconds=total_headers_thresholds[
                        'critical_threshold'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value: TimedTaskTracker(
                    timedelta(seconds=unconfirmed_blocks_thresholds[
                        'critical_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    NoOfUnconfirmedTxsThreshold.value: TimedTaskTracker(
                    timedelta(seconds=unconfirmed_txs_thresholds[
                        'critical_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    TimedTaskTracker(timedelta(seconds=node_is_down_thresholds[
                        'critical_time_window'])),
            }
            critical_repeat_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskLimiter(timedelta(
                        seconds=current_head_thresholds['critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold.value
                : TimedTaskLimiter(timedelta(
                    seconds=heads_in_queue_thresholds['critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    NoChangeInTotalHeadersReceived.value:
                    TimedTaskLimiter(timedelta(
                        seconds=total_headers_thresholds['critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=dropped_headers_thresholds['critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    MaxUnconfirmedBlocksThreshold.value: TimedTaskLimiter(
                    timedelta(seconds=unconfirmed_blocks_thresholds[
                        'critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    NoOfUnconfirmedTxsThreshold.value: TimedTaskLimiter(
                    timedelta(seconds=unconfirmed_txs_thresholds[
                        'critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value: TimedTaskLimiter(
                    timedelta(seconds=error_jobs_thresholds[
                        'critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.EthBalanceThreshold.value:
                    TimedTaskLimiter(timedelta(seconds=eth_balance_thresholds[
                        'critical_repeat'])),
                GroupedChainlinkNodeAlertsMetricCode.NodeIsDown.value:
                    TimedTaskLimiter(timedelta(seconds=node_is_down_thresholds[
                        'critical_repeat'])),
            }
            warning_occurrences_in_period_tracker = {
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=dropped_headers_thresholds[
                            'warning_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=error_jobs_thresholds['warning_time_window'])),
            }
            critical_occurrences_in_period_tracker = {
                GroupedChainlinkNodeAlertsMetricCode.
                    DroppedBlockHeadersThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=dropped_headers_thresholds[
                            'critical_time_window'])),
                GroupedChainlinkNodeAlertsMetricCode.
                    TotalErroredJobRunsThreshold.value:
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
