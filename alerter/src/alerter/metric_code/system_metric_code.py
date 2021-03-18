from .metric_code import MetricCode


class SystemMetricCode(MetricCode):
    SystemIsDown = 'system_is_down'
    InvalidUrl = 'invalid_url'
    OpenFileDescriptors = 'open_file_descriptors'
    SystemCPUUsage = 'system_cpu_usage'
    SystemRAMUsage = 'system_ram_usage'
    SystemStorageUsage = 'system_storage_usage'
    MetricNotFound = 'metric_not_found'
