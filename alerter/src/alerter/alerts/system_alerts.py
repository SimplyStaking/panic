from datetime import datetime, timedelta

from src.alerter.alert_code import SystemAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.metric_code import SystemMetricCode
from src.utils.datetime import strfdelta


class SystemWentDownAtAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemWentDownAtAlert,
            "{} System is down, last time checked: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            SystemMetricCode.SystemIsDown)


class SystemBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemBackUpAgainAlert,
            "{} System is back up, last successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            SystemMetricCode.SystemIsDown)


class SystemStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemStillDownAlert,
            "{} System is still down, it has been down for {}.".format(
                origin_name, strfdelta(timedelta(seconds=difference),
                                       "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            SystemMetricCode.SystemIsDown)


class InvalidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.InvalidUrlAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id,
            SystemMetricCode.InvalidUrl)


class OpenFileDescriptorsIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.OpenFileDescriptorsIncreasedAboveThresholdAlert,
            "{} open file descriptors INCREASED above {} Threshold. Current "
            "value {}%.".format(origin_name, threshold, new_value),
            severity, timestamp, parent_id, origin_id,
            SystemMetricCode.OpenFileDescriptors)


class OpenFileDescriptorsDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.OpenFileDescriptorsDecreasedBelowThresholdAlert,
            "{} open file descriptors DECREASED below {} Threshold. Current "
            "value {}%.".format(origin_name, threshold, new_value), severity,
            timestamp, parent_id, origin_id,
            SystemMetricCode.OpenFileDescriptors)


class SystemCPUUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemCPUUsageIncreasedAboveThresholdAlert,
            "{} system CPU usage INCREASED above {} Threshold. Current value: "
            "{}%.".format(origin_name, threshold, new_value), severity,
            timestamp, parent_id, origin_id, SystemMetricCode.SystemCPUUsage)


class SystemCPUUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemCPUUsageDecreasedBelowThresholdAlert,
            "{} system CPU usage DECREASED below {} Threshold. Current value: "
            "{}%.".format(origin_name, threshold, new_value), severity,
            timestamp, parent_id, origin_id,
            SystemMetricCode.SystemCPUUsage)


class SystemRAMUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemRAMUsageIncreasedAboveThresholdAlert,
            "{} system RAM usage INCREASED above {} Threshold. Current value: "
            "{}%.".format(origin_name, threshold, new_value), severity,
            timestamp, parent_id, origin_id, SystemMetricCode.SystemRAMUsage)


class SystemRAMUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemRAMUsageDecreasedBelowThresholdAlert,
            "{} system RAM usage DECREASED below {} Threshold. Current value: "
            "{}%.".format(origin_name, threshold, new_value), severity,
            timestamp, parent_id, origin_id,
            SystemMetricCode.SystemRAMUsage)


class SystemStorageUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemStorageUsageIncreasedAboveThresholdAlert,
            "{} system storage usage INCREASED above {} Threshold. Current "
            "value: {}%.".format(origin_name, threshold, new_value), severity,
            timestamp, parent_id, origin_id,
            SystemMetricCode.SystemStorageUsage)


class SystemStorageUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, new_value: float, severity: str,
                 timestamp: float, threshold: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemStorageUsageDecreasedBelowThresholdAlert,
            "{} system storage usage DECREASED below {} Threshold. Current "
            "value: {}%.".format(origin_name, threshold, new_value), severity,
            timestamp, parent_id, origin_id,
            SystemMetricCode.SystemStorageUsage)


class MetricNotFoundErrorAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.MetricNotFoundErrorAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, SystemMetricCode.MetricNotFound)


class MetricFoundAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.MetricFoundAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id,
            SystemMetricCode.MetricNotFound)


class ValidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.ValidUrlAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, SystemMetricCode.InvalidUrl)
