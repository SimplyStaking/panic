import sys
from enum import Enum
from typing import Union

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

RedisType = Union[bytes, str, int, float]


class GithubDataType(TypedDict):
    name: str
    current_no_of_releases: int


class GithubMonitorDataType(TypedDict):
    monitor_name: str
    repo_name: str
    repo_id: str
    repo_parent_id: str
    time: str


class SystemDataType(TypedDict):
    name: str
    chain_name: str
    process_cpu_seconds_total: int
    process_memory_usage: int
    virtual_memory_usage: int
    open_file_descriptors: int
    system_cpu_usage: int
    system_ram_usage: int
    system_storage_usage: int
    network_transmit_bytes_per_second: int
    network_receive_bytes_per_second: int
    network_receive_bytes_total: int
    network_transmit_bytes_total: int
    disk_io_time_seconds_total: int
    disk_io_time_seconds_in_interval: int


class SystemMonitorDataType(TypedDict):
    monitor_name: str
    system_name: str
    system_id: str
    system_parent_id: str
    time: str


class AlertDataType(TypedDict):
    parent_id: str
    origin: str
    alert_name: str
    severity: str
    message: str
    timestamp: str


class AlertTypeThreshold(TypedDict):
    name: str
    enabled: bool
    critical_threshold: int
    critical_enabled: bool
    warning_threshold: int
    warning_enabled: bool


class AlertTypeTimeWindow(TypedDict):
    name: str
    enabled: bool
    critical_threshold: int
    critical_timewindow: int
    critical_enabled: bool
    warning_threshold: int
    warning_timewindow: int
    warning_enabled: bool


class AlertTypeRepeat(TypedDict):
    name: str
    enabled: bool
    critical_enabled: bool
    critical_repeat: int
    warning_enabled: bool
    warning_repeat: int


class Severity(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    ERROR = 4


class AlertTypeSeverity(TypedDict):
    name: str
    severity: Severity
    enabled: bool
