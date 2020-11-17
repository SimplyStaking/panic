from enum import Enum
from src.utils.alert import next_id, SeverityCode
from src.alerter.alerts.alert import Alert


class AlertCode(Enum):
    OpenFileDescriptorsIncreasedAboveThresholdAlert = next_id(),
    OpenFileDescriptorsDecreasedBelowThresholdAlert = next_id(),
    SystemCPUUsageIncreasedAboveThresholdAlert = next_id(),
    SystemCPUUsageDecreasedBelowThresholdAlert = next_id(),
    SystemRAMUsageIncreasedAboveThresholdAlert = next_id(),
    SystemRAMUsageDecreasedBelowThresholdAlert = next_id(),
    SystemStorageUsageIncreasedAboveThresholdAlert = next_id(),
    SystemStorageUsageDecreasedBelowThresholdAlert = next_id(),
    ReceivedUnexpectedDataAlert = next_id(),
    InvalidUrlAlert = next_id(),
    SystemWentDownAtAlert = next_id(),
    SystemBackUpAgainAlert = next_id(),
    SystemStillDownAlert = next_id(),


class ReceivedUnexpectedDataAlert(Alert):
    def __init__(self, message: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.ReceivedUnexpectedDataAlert,
            message, severity, timestamp, parent_id, origin_id)


class SystemWentDownAtAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, difference: str,
                 severity: str, timestamp: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemWentDownAtAlert,
            '{}: {} System is down, total current downtime: {}s.'.format(
                parent_name, origin_name, difference),
            severity, timestamp, parent_id, origin_id)


class SystemBackUpAgainAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, difference: str,
                 severity: str, timestamp: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemBackUpAgainAlert,
            '{}: {} System is back up, it was down for {}s.'.format(
                parent_name, origin_name, difference),
            severity, timestamp, parent_id, origin_id)


class SystemStillDownAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, difference: str,
                 severity: str, timestamp: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemStillDownAlert,
            '{}: {} System is back up, it was down for {}s.'.format(
                parent_name, origin_name, difference),
            severity, timestamp, parent_id, origin_id)


class InvalidUrlAlert(Alert):
    def __init__(self, message: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.InvalidUrlAlert, message, severity,
            timestamp, parent_id, origin_id)


class OpenFileDescriptorsIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsIncreasedAboveThresholdAlert,
            '{} open file descriptors INCREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class OpenFileDescriptorsDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsDecreasedBelowThresholdAlert,
            '{} open file descriptors DECREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemCPUUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageIncreasedAboveThresholdAlert,
            '{} system CPU usage INCREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemCPUUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageDecreasedBelowThresholdAlert,
            '{} system CPU usage DECREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemRAMUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedAboveThresholdAlert,
            '{} system RAM usage INCREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemRAMUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageDecreasedBelowThresholdAlert,
            '{} system RAM usage DECREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemStorageUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedAboveThresholdAlert,
            '{} system RAM usage INCREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemStorageUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageDecreasedBelowThresholdAlert,
            '{} system storage usage DECREASED above {} Threshold from {}% to'
            ' {}%.'.format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)
