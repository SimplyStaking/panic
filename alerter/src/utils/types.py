from typing import Union, TypedDict

RedisType = Union[bytes, str, int, float]

class GithubDataType(TypedDict):
    name: str
    prev_no_of_releases: int

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
    system_network_transmit_bytes_per_second: int
    system_network_receive_bytes_per_second: int

class SystemMonitorDataType(TypedDict):
    name: str
    system_monitor_alive: int
    system_monitor_last_network_inspection: int
    system_monitor_network_receive_bytes_total: int
    system_monitor_network_transmit_bytes_total: int

class AlertDataType(TypedDict):
    chain_name: str
    origin: str
    alert_name: str
    severity: str
    message: str
    timestamp: str