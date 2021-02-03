from enum import Enum

from typing import Type


def empty(enumeration: Type[Enum]):
    """
    Class decorator for enumerations ensuring an enum-superclass has no values.
    """
    if len(enumeration.__members__) > 0:
        raise ValueError(
            "There should not be any values in {0!r}".format(enumeration))

    return enumeration
