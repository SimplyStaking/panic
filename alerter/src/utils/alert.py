from enum import Enum

_ALERT_ID = 0


def next_id():
    global _ALERT_ID
    _ALERT_ID += 1
    return _ALERT_ID


def floaty(value: str) -> float:
    if value is None:
        return 0
    else:
        return float(value)


class SeverityCode(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    ERROR = 4
