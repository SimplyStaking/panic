from src.alerter.alerts_config.alerts_config import AlertsConfig
from src.alerter.alerters.alerter import Alerter

class SystemAlerter(Alerter):
    def __init__(self, alerter_name: str, logger: logging.Logger) -> None:
        super().__init__(alerter_name, logger)
        self._system_alerts_config = None

    def set_alerts_config(self, alerts_config: AlertsConfig) -> None:
        self._system_alerts_config = alerts_config

    def start_alerting(self) -> None:
        pass