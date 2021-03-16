from typing import Dict

from src.alerter.alert_code import AlertCode
from src.alerter.metric_code import MetricCode


class Alert:

    def __init__(self, alert_code: AlertCode, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 metric_code: MetricCode) -> None:
        self._alert_code = alert_code
        self._message = message
        self._severity = severity
        self._parent_id = parent_id
        self._origin_id = origin_id
        self._timestamp = timestamp
        self._metric_code = metric_code

    def __str__(self) -> str:
        return self.message

    @property
    def alert_code(self) -> AlertCode:
        return self._alert_code

    @property
    def message(self) -> str:
        return self._message

    @property
    def severity(self) -> str:
        return self._severity

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def origin_id(self) -> str:
        return self._origin_id

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def metric_code(self) -> MetricCode:
        return self._metric_code

    @property
    def alert_data(self) -> Dict:
        return {
            'alert_code': {
                'name': self._alert_code.name,
                'code': self._alert_code.value
            },
            'metric': self._metric_code.name,
            'message': self._message,
            'severity': self._severity,
            'parent_id': self._parent_id,
            'origin_id': self._origin_id,
            'timestamp': self._timestamp
        }
