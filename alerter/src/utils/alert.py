from enum import Enum

_ALERT_ID = 0


def next_id():
    global _ALERT_ID
    _ALERT_ID += 1
    return _ALERT_ID


class SeverityCode(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    ERROR = 4
