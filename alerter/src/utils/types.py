from typing import Union, Any

RedisType = Union[bytes, str, int, float]


def convert_to_float_if_not_none(value: Union[int, str, float, bytes, None],
                                 default_return: Any) -> Any:
    # This function converts a value to float if it is not None, otherwise it
    # returns a default return
    return float(value) if value is not None else default_return
