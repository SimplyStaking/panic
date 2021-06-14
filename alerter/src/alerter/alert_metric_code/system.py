from .alert_metric_code import AlertMetricCode


class SystemAlertMetricCode(AlertMetricCode):
    SystemIsDown = 'system_is_down'
    InvalidUrl = 'invalid_url'
    OpenFileDescriptorsThreshold = 'open_file_descriptors'
    SystemCPUUsageThreshold = 'system_cpu_usage'
    SystemRAMUsageThreshold = 'system_ram_usage'
    SystemStorageUsageThreshold = 'system_storage_usage'
    MetricNotFound = 'metric_not_found'
