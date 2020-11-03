from src.utils.types import AlertTypeThreshold


class SystemAlertsConfig:
    def __init__(self, system_id: str,
                 open_file_descriptors: AlertTypeThreshold,
                 system_cpu_usage: AlertTypeThreshold,
                 system_storage_usage: AlertTypeThreshold,
                 system_ram_usage: AlertTypeThreshold,
                 system_network_usage: AlertTypeThreshold) -> None:
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
    def open_file_descriptors(self) -> AlertTypeThreshold:
        return self._open_file_descriptors

    @property
    def system_cpu_usage(self) -> AlertTypeThreshold:
        return self._system_cpu_usage

    @property
    def system_storage_usage(self) -> AlertTypeThreshold:
        return self._system_storage_usage

    @property
    def system_ram_usage(self) -> AlertTypeThreshold:
        return self._system_ram_usage

    @property
    def system_network_usage(self) -> AlertTypeThreshold:
        return self._system_network_usage

    def set_system_id(self, system_id: str) -> None:
        self._system_id = system_id

    def set_open_file_descriptors(self, open_file_descriptors:
                                  AlertTypeThreshold) -> None:
        self._open_file_descriptors = open_file_descriptors

    def set_system_cpu_usage(self, system_cpu_usage:
                             AlertTypeThreshold) -> None:
        self._system_cpu_usage = system_cpu_usage

    def set_system_storage_usage(self, system_storage_usage:
                                 AlertTypeThreshold) -> None:
        self._system_storage_usage = system_storage_usage

    def set_system_network_usage(self, system_network_usage:
                                 AlertTypeThreshold) -> None:
        self._system_network_usage = system_network_usage
