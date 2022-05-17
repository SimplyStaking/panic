import logging
from datetime import timedelta

from src.alerter.factory.alerting_factory import AlertingFactory
from src.alerter.grouped_alerts_metric_code.system \
    import GroupedSystemAlertsMetricCode as AlertsMetricCode
from src.configs.alerts.system import SystemAlertsConfig
from src.utils.configs import parse_alert_time_thresholds
from src.utils.timing import TimedTaskTracker, TimedTaskLimiter


class SystemAlertingFactory(AlertingFactory):
    """
    This class is in charge of alerting and managing the alerting state for the
    system alerter. The alerting_state dict is to be structured as follows:
    {
        <parent_id>: {
            <node_id>: {
                Optional[warning_sent]: {
                    GroupedSystemAlertsMetricCode.value: bool
                },
                Optional[critical_sent]: {
                    GroupedSystemAlertsMetricCode.value: bool
                },
                Optional[error_sent]: {
                    GroupedSystemAlertsMetricCode.value: bool
                },
                Optional[warning_window_timer]: {
                    GroupedSystemAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_window_timer]: {
                    GroupedSystemAlertsMetricCode.value: TimedTaskTracker
                },
                Optional[critical_repeat_timer]: {
                    GroupedSystemAlertsMetricCode.value: TimedTaskLimiter
                }
            }
        }
    }
    """

    def __init__(self, component_logger: logging.Logger) -> None:
        super().__init__(component_logger)

    def create_alerting_state(self, parent_id: str, system_id: str,
                              system_alerts_config: SystemAlertsConfig) -> None:
        """
        If no state is already stored, this function will create a new alerting
        state for a system based on the passed alerts config.
        :param parent_id: The id of the chain
        :param system_id: The id of the system
        :param system_alerts_config: The system alerts configuration
        :return: None
        """

        if parent_id not in self.alerting_state:
            self.alerting_state[parent_id] = {}

        if system_id not in self.alerting_state[parent_id]:
            warning_sent = {
                AlertsMetricCode.OpenFileDescriptorsThreshold.value: False,
                AlertsMetricCode.SystemCPUUsageThreshold.value: False,
                AlertsMetricCode.SystemRAMUsageThreshold.value: False,
                AlertsMetricCode.SystemStorageUsageThreshold.value: False,
                AlertsMetricCode.SystemIsDown.value: False
            }
            critical_sent = {
                AlertsMetricCode.OpenFileDescriptorsThreshold.value: False,
                AlertsMetricCode.SystemCPUUsageThreshold.value: False,
                AlertsMetricCode.SystemRAMUsageThreshold.value: False,
                AlertsMetricCode.SystemStorageUsageThreshold.value: False,
                AlertsMetricCode.SystemIsDown.value: False
            }
            error_sent = {
                AlertsMetricCode.InvalidUrl.value: False,
                AlertsMetricCode.MetricNotFound.value: False,
            }

            open_file_descriptors_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                system_alerts_config.open_file_descriptors)
            system_cpu_usage_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                system_alerts_config.system_cpu_usage)
            system_ram_usage_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                system_alerts_config.system_ram_usage
            )
            system_storage_usage_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                system_alerts_config.system_storage_usage
            )
            system_is_down_thresholds = parse_alert_time_thresholds(
                ['warning_threshold', 'critical_threshold', 'critical_repeat'],
                system_alerts_config.system_is_down
            )

            warning_window_timer = {
                AlertsMetricCode.OpenFileDescriptorsThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=open_file_descriptors_thresholds[
                            'warning_threshold'])),
                AlertsMetricCode.SystemCPUUsageThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=system_cpu_usage_thresholds['warning_threshold']
                    )),
                AlertsMetricCode.SystemRAMUsageThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=system_ram_usage_thresholds[
                            'warning_threshold'])),
                AlertsMetricCode.SystemStorageUsageThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=system_storage_usage_thresholds[
                            'warning_threshold'])),
                AlertsMetricCode.SystemIsDown.value: TimedTaskTracker(timedelta(
                    seconds=system_is_down_thresholds['warning_threshold']))
            }
            critical_window_timer = {
                AlertsMetricCode.OpenFileDescriptorsThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=open_file_descriptors_thresholds[
                            'critical_threshold'])),
                AlertsMetricCode.SystemCPUUsageThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=system_cpu_usage_thresholds[
                            'critical_threshold'])),
                AlertsMetricCode.SystemRAMUsageThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=system_ram_usage_thresholds[
                            'critical_threshold'])),
                AlertsMetricCode.SystemStorageUsageThreshold.value:
                    TimedTaskTracker(timedelta(
                        seconds=system_storage_usage_thresholds[
                            'critical_threshold'])),
                AlertsMetricCode.SystemIsDown.value: TimedTaskTracker(timedelta(
                    seconds=system_is_down_thresholds['critical_threshold']))
            }
            critical_repeat_timer = {
                AlertsMetricCode.OpenFileDescriptorsThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=open_file_descriptors_thresholds[
                            'critical_repeat'])),
                AlertsMetricCode.SystemCPUUsageThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=system_cpu_usage_thresholds['critical_repeat'])
                    ),
                AlertsMetricCode.SystemRAMUsageThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=system_ram_usage_thresholds['critical_repeat'])
                    ),
                AlertsMetricCode.SystemStorageUsageThreshold.value:
                    TimedTaskLimiter(timedelta(
                        seconds=system_storage_usage_thresholds[
                            'critical_repeat'])),
                AlertsMetricCode.SystemIsDown.value: TimedTaskLimiter(timedelta(
                    seconds=system_is_down_thresholds['critical_repeat']))
            }

            self.alerting_state[parent_id][system_id] = {
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
