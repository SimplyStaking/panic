import logging
from datetime import timedelta
from typing import Dict
from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node.evm_node_metric_code \
    import GroupedEVMNodeAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.node.evm import EVMAlertsConfigsFactory
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import (TimedTaskTracker, TimedTaskLimiter,
                              OccurrencesInTimePeriodTracker)


class EVMNodeAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    EVM node alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            <node_id>: {
                Optional[warning_sent]: {
                    GroupedEVMNodeAlertsMetricCode.value: bool
                },
                Optional[critical_sent]: {
                    GroupedEVMNodeAlertsMetricCode.value: bool
                },
                Optional[error_sent]: {
                    GroupedEVMNodeAlertsMetricCode.value: bool
                },
                Optional[warning_window_timer]: {
                    GroupedEVMNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_window_timer]: {
                    GroupedEVMNodeAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_repeat_timer]: {
                    GroupedEVMNodeAlertsMetricCode.value: TimedTaskLimiter
                }
            }
        }
    }
    """

    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)
        self._nodes_configs = {}

    @property
    def nodes_configs(self) -> Dict:
        return self._nodes_configs

    def create_alerting_state(
            self, parent_id: str, node_id: str,
            evm_node_alerts_config: EVMAlertsConfigsFactory) -> None:
        """
        If no state is already stored, this function will create a new alerting
        state for a node based on the passed alerts config.
        :param parent_id: The id of the chain
        :param node_id: The id of the node
        :param node_name: The name of the node
        :param evm_node_alerts_config: The alerts configuration
        :return: None
        """

        if parent_id not in self.alerting_state:
            self.alerting_state[parent_id] = {}
            self.nodes_configs[parent_id] = {}

        if node_id not in self.alerting_state[parent_id]:
            warning_sent = {
                AlertsMetricCode.NoChangeInBlockHeight.value: False,
                AlertsMetricCode.BlockHeightDifference.value: False,
                AlertsMetricCode.NodeIsDown.value: False
            }
            critical_sent = {
                AlertsMetricCode.NoChangeInBlockHeight.value: False,
                AlertsMetricCode.BlockHeightDifference.value: False,
                AlertsMetricCode.NodeIsDown.value: False
            }
            error_sent = {
                AlertsMetricCode.InvalidUrl.value: False,
            }

            evm_node_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                evm_node_alerts_config.evm_node_is_down)
            block_height_difference_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                evm_node_alerts_config.
                evm_block_syncing_block_height_difference)
            no_change_in_block_height_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                evm_node_alerts_config.
                evm_block_syncing_no_change_in_block_height)

            warning_window_timer = {
                AlertsMetricCode.NoChangeInBlockHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=no_change_in_block_height_thresholds[
                            'warning_threshold'])),
                AlertsMetricCode.NodeIsDown.value:
                    TimedTaskTracker(timedelta(
                        seconds=evm_node_is_down_thresholds[
                            'warning_threshold'])),
                AlertsMetricCode.BlockHeightDifference.value:
                    TimedTaskTracker(timedelta(
                        seconds=block_height_difference_thresholds[
                            'warning_threshold']))
            }
            critical_window_timer = {
                AlertsMetricCode.NoChangeInBlockHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=no_change_in_block_height_thresholds[
                            'critical_threshold'])),
                AlertsMetricCode.NodeIsDown.value:
                    TimedTaskTracker(timedelta(
                        seconds=evm_node_is_down_thresholds[
                            'critical_threshold'])),
                AlertsMetricCode.BlockHeightDifference.value:
                    TimedTaskTracker(timedelta(
                        seconds=block_height_difference_thresholds[
                            'critical_threshold']))
            }
            critical_repeat_timer = {
                AlertsMetricCode.NoChangeInBlockHeight.value: TimedTaskLimiter(
                    timedelta(seconds=no_change_in_block_height_thresholds[
                        'critical_repeat'])),
                AlertsMetricCode.NodeIsDown.value:
                    TimedTaskLimiter(timedelta(
                        seconds=evm_node_is_down_thresholds[
                            'critical_repeat'])),
                AlertsMetricCode.BlockHeightDifference.value:
                    TimedTaskLimiter(timedelta(
                        seconds=block_height_difference_thresholds[
                            'critical_repeat']))
            }

            self.nodes_configs[parent_id][node_id] = None
            self.alerting_state[parent_id][node_id] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
                'error_sent': error_sent,
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
            del self.nodes_configs[parent_id]
