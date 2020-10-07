from enum import Enum
from typing import Optional


class SystemType(Enum):
    NODE_SYSTEM = 1,
    GENERAL_SYSTEM = 2,


class System:
    def __init__(self, name: str, node_exporter_url: str,
                 system_type: SystemType, chain: str = None) -> None:
        self._name = name
        self._node_exporter_url = node_exporter_url
        self._system_type = system_type
        self._chain = chain
        self._system_type = system_type

        # Data fields
        self._process_cpu_seconds_total = None
        self._process_memory_usage = None
        self._virtual_memory_usage = None
        self._open_file_descriptors = None
        self._system_cpu_usage = None
        self._system_ram_usage = None
        self._system_storage_usage = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def node_exporter_url(self) -> str:
        return self._node_exporter_url

    @property
    def is_general_system(self) -> bool:
        return self._system_type == SystemType.GENERAL_SYSTEM

    @property
    def is_node_system(self) -> bool:
        return self._system_type == SystemType.NODE_SYSTEM

    @property
    def chain(self) -> Optional[str]:
        return self._chain

    @property
    def process_cpu_seconds_total(self) -> Optional[float]:
        return self._process_cpu_seconds_total

    @property
    def process_memory_usage(self) -> Optional[float]:
        return self._process_memory_usage

    @property
    def virtual_memory_usage(self) -> Optional[float]:
        return self._virtual_memory_usage

    @property
    def open_file_descriptors(self) -> Optional[float]:
        return self._open_file_descriptors

    @property
    def system_cpu_usage(self) -> Optional[float]:
        return self._system_cpu_usage

    @property
    def system_ram_usage(self) -> Optional[float]:
        return self._system_ram_usage

    @property
    def system_storage_usage(self) -> Optional[float]:
        return self._system_storage_usage

    def status(self) -> str:
        return "process_cpu_seconds_total={}, " \
               "process_memory_usage={}, virtual_memory_usage={}, " \
               "open_file_descriptors={}, system_cpu_usage={}, " \
               "system_ram_usage={}, system_storage_usage={}, " \
               "".format(self._process_cpu_seconds_total,
                         self._process_memory_usage, self._virtual_memory_usage,
                         self._open_file_descriptors, self._system_cpu_usage,
                         self._system_ram_usage, self._system_storage_usage)

    def set_process_cpu_seconds_total(self, process_cpu_seconds_total) -> None:
        self._process_cpu_seconds_total = process_cpu_seconds_total

    def set_process_memory_usage(self, process_memory_usage) -> None:
        self._process_memory_usage = process_memory_usage

    def set_virtual_memory_usage(self, virtual_memory_usage) -> None:
        self._virtual_memory_usage = virtual_memory_usage

    def set_open_file_descriptors(self, open_file_descriptors) -> None:
        self._open_file_descriptors = open_file_descriptors

    def set_system_cpu_usage(self, system_cpu_usage) -> None:
        self._system_cpu_usage = system_cpu_usage

    def set_system_ram_usage(self, system_ram_usage) -> None:
        self._system_ram_usage = system_ram_usage

    def set_system_storage_usage(self, system_storage_usage) -> None:
        self._system_storage_usage = system_storage_usage
