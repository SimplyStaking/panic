# TODO Needs updating in the future.

import sys
from typing import Union, Optional, Any

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

RedisType = Union[bytes, str, int, float]


def convert_to_float_if_not_none(value: Optional[int, str, float, bytes],
                                 default_return: Any) -> Any:
    # This function converts a value to float if it is not None, otherwise it
    # returns a default return
    return float(value) if value is not None else default_return


class GithubDataType(TypedDict):
    def __init__(self):
        pass

    name: str
    current_no_of_releases: int


class GithubMonitorDataType(TypedDict):
    def __init__(self):
        pass

    monitor_name: str
    repo_name: str
    repo_id: str
    repo_parent_id: str
    time: str


class SystemDataType(TypedDict):
    def __init__(self):
        pass

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
    def __init__(self):
        pass

    monitor_name: str
    system_name: str
    system_id: str
    system_parent_id: str
    time: str


class AlertDataType(TypedDict):
    def __init__(self):
        pass

    parent_id: str
    origin: str
    alert_name: str
    severity: str
    message: str
    timestamp: str
