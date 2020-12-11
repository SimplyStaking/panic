from .alert_code import AlertCode


class SystemAlertCode(AlertCode):
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
    MetricNotFoundErrorAlert = 'system_alert_14'
