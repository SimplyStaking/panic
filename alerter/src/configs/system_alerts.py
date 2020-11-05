from typing import Dict


class SystemAlertsConfig:
    def __init__(self, system_id: str,
                 open_file_descriptors: Dict,
                 system_cpu_usage: Dict,
                 system_storage_usage: Dict,
                 system_ram_usage: Dict,
                 system_network_usage: Dict) -> None:
        self._system_id = system_id
        self._open_file_descriptors = open_file_descriptors
        self._system_cpu_usage = system_cpu_usage
        self._system_storage_usage = system_storage_usage
        self._system_ram_usage = system_ram_usage
        self._system_network_usage = system_network_usage

    @property
    def system_id(self) -> str:
        return self._system_id

    @property
    def open_file_descriptors(self) -> Dict:
        return self._open_file_descriptors

    @property
    def system_cpu_usage(self) -> Dict:
        return self._system_cpu_usage

    @property
    def system_storage_usage(self) -> Dict:
        return self._system_storage_usage

    @property
    def system_ram_usage(self) -> Dict:
        return self._system_ram_usage

    @property
    def system_network_usage(self) -> Dict:
        return self._system_network_usage

    def set_system_id(self, system_id: str) -> None:
        self._system_id = system_id

    def set_open_file_descriptors(self, open_file_descriptors:
                                  Dict) -> None:
        self._open_file_descriptors = open_file_descriptors

    def set_system_cpu_usage(self, system_cpu_usage:
                             Dict) -> None:
        self._system_cpu_usage = system_cpu_usage

    def set_system_storage_usage(self, system_storage_usage:
                                 Dict) -> None:
        self._system_storage_usage = system_storage_usage

    def set_system_network_usage(self, system_network_usage:
                                 Dict) -> None:
        self._system_network_usage = system_network_usage
