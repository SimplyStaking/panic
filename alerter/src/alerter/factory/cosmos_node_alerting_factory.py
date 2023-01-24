import logging
from datetime import timedelta

from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node. \
    cosmos_node_metric_code import \
    GroupedCosmosNodeAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)


class CosmosNodeAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    cosmos node alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            <node_id>: {
                Optional[warning_sent]: {
                    GroupedCosmosNodeAlertsMetricCode.value: bool
                },
                Optional[critical_sent]: {
                    GroupedCosmosNodeAlertsMetricCode.value: bool
                },
                Optional[error_sent]: {
                    GroupedCosmosNodeAlertsMetricCode.value: bool
                },
                Optional[any_severity_sent]: {
                    GroupedCosmosNodeAlertsMetricCode.value: bool
                },
                Optional[warning_window_timer]: {
                    GroupedCosmosNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_window_timer]: {
                    GroupedCosmosNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_repeat_timer]: {
                    GroupedCosmosNodeAlertsMetricCode.value: TimedTaskLimiter
                },
                Optional[warning_occurrences_in_period_tracker]: {
                    GroupedCosmosNodeAlertsMetricCode.value:
                    OccurrencesInTimePeriodTracker
                },
                Optional[critical_occurrences_in_period_tracker]: {
                    GroupedCosmosNodeAlertsMetricCode.value:
                    OccurrencesInTimePeriodTracker
                },
                is_validator: bool,
                Optional[current_height]: Int
            }
        }
    }
    """

    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)

    def create_alerting_state(
            self, parent_id: str, node_id: str,
            alerts_config: CosmosNodeAlertsConfig, is_validator: bool) -> None:
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
                AlertsMetricCode.BlocksMissedThreshold.value: False,
                AlertsMetricCode.NoChangeInHeight.value: False,
                AlertsMetricCode.BlockHeightDifferenceThreshold.value: False,
                AlertsMetricCode.PrometheusSourceIsDown.value: False,
                AlertsMetricCode.CosmosRestSourceIsDown.value: False,
                AlertsMetricCode.TendermintRPCSourceIsDown.value: False,
            }
            critical_sent = {
                AlertsMetricCode.NodeIsDown.value: False,
                AlertsMetricCode.BlocksMissedThreshold.value: False,
                AlertsMetricCode.NoChangeInHeight.value: False,
                AlertsMetricCode.BlockHeightDifferenceThreshold.value: False,
                AlertsMetricCode.PrometheusSourceIsDown.value: False,
                AlertsMetricCode.CosmosRestSourceIsDown.value: False,
                AlertsMetricCode.TendermintRPCSourceIsDown.value: False,
            }
            error_sent = {
                AlertsMetricCode.PrometheusInvalidUrl.value: False,
                AlertsMetricCode.CosmosRestInvalidUrl.value: False,
                AlertsMetricCode.TendermintRPCInvalidUrl.value: False,
                AlertsMetricCode.NoSyncedCosmosRestSource.value: False,
                AlertsMetricCode.NoSyncedTendermintRPCSource.value: False,
                AlertsMetricCode.CosmosRestDataNotObtained.value: False,
                AlertsMetricCode.TendermintRPCDataNotObtained.value: False,
                AlertsMetricCode.MetricNotFound.value: False,
            }
            any_severity_sent = {
                AlertsMetricCode.NodeIsNotPeeredWithSentinel.value: False,
                AlertsMetricCode.NodeIsSyncing.value: False,
                AlertsMetricCode.ValidatorIsNotActive.value: False,
                AlertsMetricCode.ValidatorIsJailed.value: False,
            }

            node_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_validator if is_validator
                else alerts_config.cannot_access_node
            )
            blocks_missed_thresholds = parse_alert_time_thresholds(
                ['warning_time_window', 'critical_time_window',
                 'critical_repeat'], alerts_config.missed_blocks
            )
            no_change_in_height_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.no_change_in_block_height_validator
                if is_validator
                else alerts_config.no_change_in_block_height_node
            )
            height_difference_thresholds = parse_alert_time_thresholds(
                ['critical_repeat'], alerts_config.block_height_difference
            )
            prometheus_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_prometheus_validator if is_validator
                else alerts_config.cannot_access_prometheus_node
            )
            cosmos_rest_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_cosmos_rest_validator
                if is_validator
                else alerts_config.cannot_access_cosmos_rest_node
            )
            tendermint_rpc_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_tendermint_rpc_validator
                if is_validator
                else alerts_config.cannot_access_tendermint_rpc_node
            )

            warning_window_timer = {
                AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                    seconds=node_is_down_thresholds['warning_threshold'])),
                AlertsMetricCode.NoChangeInHeight.value: TimedTaskTracker(
                    timedelta(seconds=no_change_in_height_thresholds[
                        'warning_threshold'])),
                AlertsMetricCode.PrometheusSourceIsDown.value: TimedTaskTracker(
                    timedelta(seconds=prometheus_is_down_thresholds[
                        'warning_threshold'])),
                AlertsMetricCode.CosmosRestSourceIsDown.value: TimedTaskTracker(
                    timedelta(seconds=cosmos_rest_is_down_thresholds[
                        'warning_threshold'])),
                AlertsMetricCode.TendermintRPCSourceIsDown.value:
                    TimedTaskTracker(timedelta(
                        seconds=tendermint_rpc_is_down_thresholds[
                            'warning_threshold']))
            }
            critical_window_timer = {
                AlertsMetricCode.NodeIsDown.value: TimedTaskTracker(timedelta(
                    seconds=node_is_down_thresholds['critical_threshold'])),
                AlertsMetricCode.NoChangeInHeight.value: TimedTaskTracker(
                    timedelta(seconds=no_change_in_height_thresholds[
                        'critical_threshold'])),
                AlertsMetricCode.PrometheusSourceIsDown.value: TimedTaskTracker(
                    timedelta(seconds=prometheus_is_down_thresholds[
                        'critical_threshold'])),
                AlertsMetricCode.CosmosRestSourceIsDown.value: TimedTaskTracker(
                    timedelta(seconds=cosmos_rest_is_down_thresholds[
                        'critical_threshold'])),
                AlertsMetricCode.TendermintRPCSourceIsDown.value:
                    TimedTaskTracker(timedelta(
                        seconds=tendermint_rpc_is_down_thresholds[
                            'critical_threshold'])),
            }
            critical_repeat_timer = {
                AlertsMetricCode.NodeIsDown.value: TimedTaskLimiter(timedelta(
                    seconds=node_is_down_thresholds['critical_repeat'])),
                AlertsMetricCode.BlocksMissedThreshold.value:
                    TimedTaskLimiter(timedelta(seconds=blocks_missed_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.NoChangeInHeight.value: TimedTaskLimiter(
                    timedelta(seconds=no_change_in_height_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.BlockHeightDifferenceThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=height_difference_thresholds[
                            'critical_repeat'])),
                AlertsMetricCode.PrometheusSourceIsDown.value:
                    TimedTaskLimiter(timedelta(
                        seconds=prometheus_is_down_thresholds[
                            'critical_repeat'])),
                AlertsMetricCode.CosmosRestSourceIsDown.value:
                    TimedTaskLimiter(timedelta(
                        seconds=cosmos_rest_is_down_thresholds[
                            'critical_repeat'])),
                AlertsMetricCode.TendermintRPCSourceIsDown.value:
                    TimedTaskLimiter(timedelta(
                        seconds=tendermint_rpc_is_down_thresholds[
                            'critical_repeat'])),
            }
            warning_occurrences_in_period_tracker = {
                AlertsMetricCode.BlocksMissedThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=blocks_missed_thresholds[
                            'warning_time_window'])),
            }
            critical_occurrences_in_period_tracker = {
                AlertsMetricCode.BlocksMissedThreshold.value:
                    OccurrencesInTimePeriodTracker(timedelta(
                        seconds=blocks_missed_thresholds[
                            'critical_time_window'])),
            }
            self.alerting_state[parent_id][node_id] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
                'error_sent': error_sent,
                'any_severity_sent': any_severity_sent,
                'warning_window_timer': warning_window_timer,
                'critical_window_timer': critical_window_timer,
                'critical_repeat_timer': critical_repeat_timer,
                'warning_occurrences_in_period_tracker':
                    warning_occurrences_in_period_tracker,
                'critical_occurrences_in_period_tracker':
                    critical_occurrences_in_period_tracker,
                'is_validator': is_validator,
                'current_height': None,
            }
        elif (self.alerting_state[parent_id][node_id][
                  'is_validator'] != is_validator):
            node_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_validator if is_validator
                else alerts_config.cannot_access_node
            )
            no_change_in_height_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.no_change_in_block_height_validator
                if is_validator
                else alerts_config.no_change_in_block_height_node
            )
            prometheus_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_prometheus_validator if is_validator
                else alerts_config.cannot_access_prometheus_node
            )
            cosmos_rest_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_cosmos_rest_validator
                if is_validator
                else alerts_config.cannot_access_cosmos_rest_node
            )
            tendermint_rpc_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                alerts_config.cannot_access_tendermint_rpc_validator
                if is_validator
                else alerts_config.cannot_access_tendermint_rpc_node
            )

            warning_window_timers = self.alerting_state[parent_id][node_id][
                'warning_window_timer']
            critical_window_timers = self.alerting_state[parent_id][node_id][
                'critical_window_timer']
            critical_repeat_timers = self.alerting_state[parent_id][node_id][
                'critical_repeat_timer']

            warning_window_timers[
                AlertsMetricCode.NodeIsDown.value].set_time_interval(
                timedelta(seconds=node_is_down_thresholds['warning_threshold']))
            warning_window_timers[
                AlertsMetricCode.NoChangeInHeight.value].set_time_interval(
                timedelta(seconds=no_change_in_height_thresholds[
                    'warning_threshold']))
            warning_window_timers[
                AlertsMetricCode.PrometheusSourceIsDown.value
            ].set_time_interval(timedelta(seconds=prometheus_is_down_thresholds[
                'warning_threshold']))
            warning_window_timers[
                AlertsMetricCode.CosmosRestSourceIsDown.value
            ].set_time_interval(timedelta(
                seconds=cosmos_rest_is_down_thresholds['warning_threshold']))
            warning_window_timers[
                AlertsMetricCode.TendermintRPCSourceIsDown.value
            ].set_time_interval(timedelta(
                seconds=tendermint_rpc_is_down_thresholds['warning_threshold']))

            critical_window_timers[
                AlertsMetricCode.NodeIsDown.value].set_time_interval(
                timedelta(seconds=node_is_down_thresholds[
                    'critical_threshold']))
            critical_window_timers[
                AlertsMetricCode.NoChangeInHeight.value].set_time_interval(
                timedelta(seconds=no_change_in_height_thresholds[
                    'critical_threshold']))
            critical_window_timers[
                AlertsMetricCode.PrometheusSourceIsDown.value
            ].set_time_interval(
                timedelta(seconds=prometheus_is_down_thresholds[
                    'critical_threshold']))
            critical_window_timers[
                AlertsMetricCode.CosmosRestSourceIsDown.value
            ].set_time_interval(
                timedelta(seconds=cosmos_rest_is_down_thresholds[
                    'critical_threshold']))
            critical_window_timers[
                AlertsMetricCode.TendermintRPCSourceIsDown.value
            ].set_time_interval(
                timedelta(seconds=tendermint_rpc_is_down_thresholds[
                    'critical_threshold']))

            critical_repeat_timers[
                AlertsMetricCode.NodeIsDown.value].set_time_interval(
                timedelta(seconds=node_is_down_thresholds['critical_repeat']))
            critical_repeat_timers[
                AlertsMetricCode.NoChangeInHeight.value].set_time_interval(
                timedelta(seconds=no_change_in_height_thresholds[
                    'critical_repeat']))
            critical_repeat_timers[
                AlertsMetricCode.PrometheusSourceIsDown.value
            ].set_time_interval(
                timedelta(seconds=prometheus_is_down_thresholds[
                    'critical_repeat']))
            critical_repeat_timers[
                AlertsMetricCode.CosmosRestSourceIsDown.value
            ].set_time_interval(
                timedelta(seconds=cosmos_rest_is_down_thresholds[
                    'critical_repeat']))
            critical_repeat_timers[
                AlertsMetricCode.TendermintRPCSourceIsDown.value
            ].set_time_interval(
                timedelta(seconds=tendermint_rpc_is_down_thresholds[
                    'critical_repeat']))

            self.alerting_state[parent_id][node_id][
                'is_validator'] = is_validator

    def remove_chain_alerting_state(self, parent_id: str) -> None:
        """
        This function deletes an entire alerting state for a chain.
        :param parent_id: The id of the chain to be deleted
        :return: None
        """
        if parent_id in self.alerting_state:
            del self.alerting_state[parent_id]
