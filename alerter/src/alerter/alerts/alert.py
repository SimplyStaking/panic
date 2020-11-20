from typing import Dict
from enum import Enum


class Alert():

    def __init__(self, alert_code: Enum, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        self._alert_code = alert_code
        self._message = message
        self._severity = severity
        self._parent_id = parent_id
        self._origin_id = origin_id
        self._timestamp = timestamp

    def __str__(self) -> str:
        return self.message

    def message(self) -> str:
        return self._message

    @property
    def alert_data(self) -> Dict:
        return {
            'alert_code': {
                'name': self._alert_code.name,
                'code': self._alert_code.value
            },
            'message': self._message,
            'severity': self._severity,
            'parent_id': self._parent_id,
            'origin_id': self._origin_id,
            'timestamp': self._timestamp
        }
