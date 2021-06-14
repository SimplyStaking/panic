from typing import Dict


class ChainlinkAlertsConfig:
    def __init__(self, parent_id: str,
                 open_file_descriptors: Dict,
                 system_cpu_usage: Dict,
                 system_storage_usage: Dict,
                 system_ram_usage: Dict,
                 system_is_down: Dict) -> None:
        self._parent_id = parent_id
        self._open_file_descriptors = open_file_descriptors
        self._system_cpu_usage = system_cpu_usage
        self._system_storage_usage = system_storage_usage
        self._system_ram_usage = system_ram_usage
        self._system_is_down = system_is_down

    @property
    def parent_id(self) -> str:
        return self._parent_id

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
    def system_is_down(self) -> Dict:
        return self._system_is_down
