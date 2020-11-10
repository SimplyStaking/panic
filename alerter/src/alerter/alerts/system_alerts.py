from enum import Enum
from src.utils.alert import next_id, SeverityCode
from src.alerter.alerts.alert import Alert


class AlertCode(Enum):
    OpenFileDescriptorsIncreasedAlert = next_id(),
    OpenFileDescriptorsDecreasedAlert = next_id(),
    OpenFileDescriptorsIncreasedAboveCriticalThresholdAlert = next_id(),
    OpenFileDescriptorsIncreasedAboveWarningThresholdAlert = next_id(),
    SystemCPUUsageIncreasedAlert = next_id(),
    SystemCPUUsageDecreasedAlert = next_id(),
    SystemCPUUsageIncreasedAboveCriticalThresholdAlert = next_id(),
    SystemCPUUsageIncreasedAboveWarningThresholdAlert = next_id(),
    SystemRAMUsageIncreasedAlert = next_id(),
    SystemRAMUsageDecreasedAlert = next_id(),
    SystemRAMUsageIncreasedAboveCriticalThresholdAlert = next_id(),
    SystemRAMUsageIncreasedAboveWarningThresholdAlert = next_id(),
    SystemStorageUsageIncreasedAlert = next_id(),
    SystemStorageUsageDecreasedAlert = next_id(),
    SystemStorageUsageIncreasedAboveCriticalThresholdAlert = next_id(),
    SystemStorageUsageIncreasedAboveWarningThresholdAlert = next_id(),
    ReceivedUnexpectedDataAlert = next_id(),
    InvalidUrlAlert = next_id(),
    SystemWentDownAt = next_id(),
    SystemWentUpAt = next_id(),


class ReceivedUnexpectedDataAlert(Alert):
    def __init__(self, message: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.ReceivedUnexpectedDataAlert,
            message, severity, timestamp, parent_id, origin_id)


class SystemWentDownAt(Alert):
    def __init__(self, parent_name: str, origin_name: str, difference: str,
                 severity: str, timestamp: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemWentDownAt,
            '{}: {} System is down, total current downtime: {}s.'.format(
                parent_name, origin_name, difference),
            severity, timestamp, parent_id, origin_id)


class SystemWentUpAt(Alert):
    def __init__(self, parent_name: str, origin_name: str, difference: str,
                 severity: str, timestamp: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemWentUpAt,
            '{}: {} System is back up, it was down for {}s.'.format(
                parent_name, origin_name, difference),
            severity, timestamp, parent_id, origin_id)


class InvalidUrlAlert(Alert):
    def __init__(self, message: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.InvalidUrlAlert, message, severity,
            timestamp, parent_id, origin_id)


class OpenFileDescriptorsIncreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsIncreasedAlert,
            '{}: {} open file descriptors INCREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class OpenFileDescriptorsDecreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsDecreasedAlert,
            '{}: {} open file descriptors DECREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class OpenFileDescriptorsIncreasedAboveCriticalThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsIncreasedAboveCriticalThresholdAlert,
            '{}: {} open file descriptors INCREASED above CRITICAL threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)


class OpenFileDescriptorsIncreasedAboveWarningThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.OpenFileDescriptorsIncreasedAboveWarningThresholdAlert,
            '{}: {} open file descriptors INCREASED above WARNING threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)


class SystemCPUUsageIncreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageIncreasedAlert,
            '{}: {} system CPU usage INCREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class SystemCPUUsageDecreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageDecreasedAlert,
            '{}: {} system CPU usage DECREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class SystemCPUUsageIncreasedAboveCriticalThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageIncreasedAboveCriticalThresholdAlert,
            '{}: {} system CPU usage INCREASED above CRITICAL threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)


class SystemCPUUsageIncreasedAboveWarningThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemCPUUsageIncreasedAboveWarningThresholdAlert,
            '{}: {} system CPU usage INCREASED above WARNING threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)


class SystemRAMUsageIncreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedAlert,
            '{}: {} system RAM usage INCREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class SystemRAMUsageDecreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageDecreasedAlert,
            '{}: {} system RAM usage DECREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class SystemRAMUsageIncreasedAboveCriticalThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedAboveCriticalThresholdAlert,
            '{}: {} system RAM usage INCREASED above CRITICAL threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)


class SystemRAMUsageIncreasedAboveWarningThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemRAMUsageIncreasedAboveWarningThresholdAlert,
            '{}: {} system RAM usage INCREASED above WARNING threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)


class SystemStorageUsageIncreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageIncreasedAlert,
            '{}: {} system storage usage INCREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class SystemStorageUsageDecreasedAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageDecreasedAlert,
            '{}: {} system storage usage DECREASED from {}% to {}%.'.format(
                parent_name, origin_name, old_value, new_value), severity,
            timestamp, parent_id, origin_id)


class SystemStorageUsageIncreasedAboveCriticalThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageIncreasedAboveCriticalThresholdAlert,
            '{}: {} system storage usage INCREASED above CRITICAL threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)


class SystemStorageUsageIncreasedAboveWarningThresholdAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, old_value: float,
                 new_value: float, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SystemStorageUsageIncreasedAboveWarningThresholdAlert,
            '{}: {} system storage usage INCREASED above WARNING threshold '
            'from {}% to {}%.'.format(parent_name, origin_name, old_value,
                                      new_value), severity, timestamp,
            parent_id, origin_id)
