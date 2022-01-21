from .grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedSystemAlertsMetricCode(GroupedAlertsMetricCode):
    SystemIsDown = 'system_is_down'
    InvalidUrl = 'system_invalid_url'
    OpenFileDescriptorsThreshold = 'system_open_file_descriptors'
    SystemCPUUsageThreshold = 'system_cpu_usage'
    SystemRAMUsageThreshold = 'system_ram_usage'
    SystemStorageUsageThreshold = 'system_storage_usage'
    MetricNotFound = 'system_metric_not_found'
