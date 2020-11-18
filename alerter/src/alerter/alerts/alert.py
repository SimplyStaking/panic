from enum import Enum
from typing import Dict


# TODO: This needs to be updated as updated by Vitaly in the alerters. Must
#     : also keep the getters.


class Alert:

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

    @property
    def alert_code(self) -> Enum:
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
    def alert_data(self) -> Dict:
        return {
            'alert': self.alert_code.name,
            'message': self.message,
            'severity': self.severity,
            'parent_id': self.parent_id,
            'origin_id': self.origin_id,
            'timestamp': self.timestamp
        }
