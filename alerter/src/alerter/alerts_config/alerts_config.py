import logging
import os
import time
from abc import ABC, abstractmethod

class AlertsConfig(ABC):
    def __init__(self, alerts_config_name: str, logger: logging.Logger) -> None:
        super().__init__()

        self._alerts_config_name = alerts_config_name
        self._logger = logger

    def __str__(self) -> str:
        return self.alerts_config_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def alerts_config_name(self) -> str:
        return self._alerts_config_name

    def set_severity_alerts(self) -> None:
        pass

    def set_repeat_alerts(self) -> None:
        pass

    def set_threshold_alerts(self) -> None:
        pass

    def set_timewindow_alerts(self) -> None:
        pass
