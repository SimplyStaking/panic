from datetime import datetime
from enum import Enum

from src.alerter.alerts.alert import Alert
from src.utils.alert import SeverityCode


class SystemAlertCode(Enum):
    OpenFileDescriptorsIncreasedAboveThresholdAlert = 'system_alert_1',
    OpenFileDescriptorsDecreasedBelowThresholdAlert = 'system_alert_2',
    SystemCPUUsageIncreasedAboveThresholdAlert = 'system_alert_3',
    SystemCPUUsageDecreasedBelowThresholdAlert = 'system_alert_4',
    SystemRAMUsageIncreasedAboveThresholdAlert = 'system_alert_5',
    SystemRAMUsageDecreasedBelowThresholdAlert = 'system_alert_6',
    SystemStorageUsageIncreasedAboveThresholdAlert = 'system_alert_7',
    SystemStorageUsageDecreasedBelowThresholdAlert = 'system_alert_8',
    ReceivedUnexpectedDataAlert = 'system_alert_9',
    InvalidUrlAlert = 'system_alert_10',
    SystemWentDownAtAlert = 'system_alert_11',
    SystemBackUpAgainAlert = 'system_alert_12',
    SystemStillDownAlert = 'system_alert_13',


class ReceivedUnexpectedDataAlert(Alert):
    def __init__(self, message: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.ReceivedUnexpectedDataAlert,
            message, severity, timestamp, parent_id, origin_id)


class SystemWentDownAtAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemWentDownAtAlert,
            "{} System is down, last time checked: {}.".format(
                origin_name, datetime.fromtimestamp(int(float(timestamp)))),
            severity, timestamp, parent_id, origin_id)


class SystemBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemBackUpAgainAlert,
            "{} System is back up, last successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(int(float(timestamp)))),
            severity, timestamp, parent_id, origin_id)


class SystemStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: str, severity: str,
                 timestamp: str, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemStillDownAlert,
            "{} System is still down, it has been down for {}s.".format(
                origin_name, int(float(difference))),
            severity, timestamp, parent_id, origin_id)


class InvalidUrlAlert(Alert):
    def __init__(self, message: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.InvalidUrlAlert, message, severity,
            timestamp, parent_id, origin_id)


class OpenFileDescriptorsIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.OpenFileDescriptorsIncreasedAboveThresholdAlert,
            "{} open file descriptors INCREASED above {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class OpenFileDescriptorsDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.OpenFileDescriptorsDecreasedBelowThresholdAlert,
            "{} open file descriptors DECREASED below {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemCPUUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemCPUUsageIncreasedAboveThresholdAlert,
            "{} system CPU usage INCREASED above {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemCPUUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemCPUUsageDecreasedBelowThresholdAlert,
            "{} system CPU usage DECREASED below {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemRAMUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemRAMUsageIncreasedAboveThresholdAlert,
            "{} system RAM usage INCREASED above {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemRAMUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemRAMUsageDecreasedBelowThresholdAlert,
            "{} system RAM usage DECREASED below {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemStorageUsageIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemRAMUsageIncreasedAboveThresholdAlert,
            "{} system RAM usage INCREASED above {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)


class SystemStorageUsageDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, old_value: float, new_value: float,
                 severity: str, timestamp: str, threshold: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemStorageUsageDecreasedBelowThresholdAlert,
            "{} system storage usage DECREASED below {} Threshold from {}% to"
            " {}%.".format(origin_name, threshold, old_value, new_value),
            severity, timestamp, parent_id, origin_id)
