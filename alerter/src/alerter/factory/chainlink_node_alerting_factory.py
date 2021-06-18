from datetime import timedelta
from typing import Dict, List

from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.utils.timing import TimedTaskTracker, TimedTaskLimiter
from src.utils.types import convert_to_float


class ChainlinkNodeAlertingFactory(AlertingFactory):
    # TODO: Modify this comment when alerter is done
    """
    This class is in charge of alerting and managing the alerting state for the
    chainlink node alerter. The alerting_state dict is to be structured as
    follows:
    {
        <parent_id>: {
            <node_id>: {
                warning_sent: {
                    GroupedChainlinkNodeAlertsMetricCode: bool
                },
                critical_sent: {
                    GroupedChainlinkNodeAlertsMetricCode: bool
                },
                warning_window_timer: {
                    GroupedChainlinkNodeAlertsMetricCode: TimedTaskTracker
                },
                critical_window_timer: {
                    GroupedChainlinkNodeAlertsMetricCode: TimedTaskTracker
                },
                critical_repeat_timer: {
                    GroupedChainlinkNodeAlertsMetricCode: TimedTaskLimiter
                },
            }
        }
    }
    """

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def _parse_alert_time_thresholds(expected_thresholds: List[str],
                                     config: Dict) -> Dict:
        """
        This function returns a dict containing all time thresholds parsed in
        tge appropriate format. The return thresholds are according to the
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
                    False
            }
            critical_sent = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    False
            }

            current_head_thresholds = self._parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                cl_node_alerts_config.head_tracker_current_head)

            warning_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['warning_threshold']))
            }
            critical_window_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskTracker(timedelta(
                        seconds=current_head_thresholds['critical_threshold']))
            }
            critical_repeat_timer = {
                GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight.value:
                    TimedTaskLimiter(timedelta(
                        seconds=current_head_thresholds['critical_repeat']))
            }

            self.alerting_state[parent_id][node_id] = {
                'warning_sent': warning_sent,
                'critical_sent': critical_sent,
                'warning_window_timer': warning_window_timer,
                'critical_window_timer': critical_window_timer,
                'critical_repeat_timer': critical_repeat_timer,
            }

    def remove_chain_alerting_state(self, parent_id: str) -> None:
        """
        This function deletes an entire alerting state for a chain.
        :param parent_id: The id of the chain to be deleted
        :return: None
        """
        if parent_id in self.alerting_state:
            del self.alerting_state[parent_id]

# TODO: Monday start by implementing the current_head_general_alerting

# TODO: When we alert the first critical time window alert we also need to
#     : do did task for the repeat, so the repeating starts.
