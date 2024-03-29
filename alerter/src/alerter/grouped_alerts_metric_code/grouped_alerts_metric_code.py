from enum import Enum

from src.utils.enum import empty


@empty
class GroupedAlertsMetricCode(str, Enum):
    """
    GroupedAlertsMetricCode represent the metric identifier of a group of
    alerts. This is needed so that it is much easier to store data representing
    a group of alerts under one metric.
    No checks are made to ensure all values are unique. You need to make sure
    that no values are duplicated across the subclasses
    """

    @classmethod
    def get_enum_by_value(cls: type, value: str) -> 'GroupedAlertsMetricCode':
        for class_ in [cls] + cls.__subclasses__():
            try:
                return class_(value)
            except ValueError:
                continue

        raise ValueError(
            "'{}' is not a valid {}".format(value, cls.__name__))
