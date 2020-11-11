from typing import Union, Any
from enum import Enum

RedisType = Union[bytes, str, int, float]


class OpsgenieSeverities(Enum):
    CRITICAL = 'P1'
    ERROR = 'P3'
    WARNING = 'P3'
    INFO = 'P5'


def convert_to_float_if_not_none(value: Union[int, str, float, bytes, None],
                                 default_return: Any) -> Any:
    # This function converts a value to float if it is not None, otherwise it
    # returns a default return
    return float(value) if value is not None else default_return


def convert_to_int_if_not_none(value: Union[int, str, float, bytes, None],
                               default_return: Any) -> Any:
    # This function converts a value to int if it is not None, otherwise it
    # returns a default return
    return int(value) if value is not None else default_return


def str_to_bool(string: str) -> bool:
    return string.lower() in ['true', 'yes']
