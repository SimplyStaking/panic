from typing import Optional


class System:
    def __init__(self, system_id: str) -> None:
        self._system_id = system_id

        # Data fields
        self._process_cpu_seconds_total = None  # Seconds
        self._process_memory_usage = None  # Percentage
        self._virtual_memory_usage = None  # Bytes
        self._open_file_descriptors = None  # Percentage
        self._system_cpu_usage = None  # Percentage
        self._system_ram_usage = None  # Percentage
        self._system_storage_usage = None  # Percentage
        self._network_transmit_bytes_per_second = None
        self._network_receive_bytes_per_second = None

        # Time in seconds spent doing i/o between monitoring rounds
        self._disk_io_time_seconds_in_interval = None

    def __str__(self) -> str:
        return self.system_id

    @property
    def system_id(self) -> str:
        return self._system_id

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

    @property
    def network_transmit_bytes_per_second(self) -> Optional[float]:
        return self._network_transmit_bytes_per_second

    @property
    def network_receive_bytes_per_second(self) -> Optional[float]:
        return self._network_receive_bytes_per_second

    @property
    def disk_io_time_seconds_in_interval(self) -> Optional[float]:
        return self._disk_io_time_seconds_in_interval

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

    def set_network_transmit_bytes_per_second(
            self, network_transmit_bytes_per_second) -> None:
        self._network_transmit_bytes_per_second = \
            network_transmit_bytes_per_second

    def set_network_receive_bytes_per_second(
            self, network_receive_bytes_per_second) -> None:
        self._network_receive_bytes_per_second = \
            network_receive_bytes_per_second

    def set_disk_io_time_seconds_in_interval(
            self, disk_io_time_seconds_in_interval) -> None:
        self._disk_io_time_seconds_in_interval = \
            disk_io_time_seconds_in_interval
