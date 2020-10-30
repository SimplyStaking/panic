from typing import Dict
from src.alerter.alerts_config.alerts_config import AlertsConfig

class SystemAlertsConfig(AlertsConfig):
    def __init__(self, alerts_config_name: str, logger: logging.Logger) -> None:
        super().__init__(alerts_config_name, logger)
        self._open_file_descriptors = {}
        self._system_cpu_usage = {}
        self._system_storage_usage = {}
        self._system_ram_usage = {}
        self._system_network_usage = {}

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

    def set_threshold_alerts(self, config: Dict) -> None:
        print(config)
        pass
