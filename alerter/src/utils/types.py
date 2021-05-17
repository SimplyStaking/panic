from enum import Enum
from typing import Union, Any

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert,
    SystemCPUUsageIncreasedAboveThresholdAlert,
    SystemRAMUsageIncreasedAboveThresholdAlert,
    SystemStorageUsageIncreasedAboveThresholdAlert,
    OpenFileDescriptorsDecreasedBelowThresholdAlert,
    SystemCPUUsageDecreasedBelowThresholdAlert,
    SystemRAMUsageDecreasedBelowThresholdAlert,
    SystemStorageUsageDecreasedBelowThresholdAlert)
from src.monitorables.nodes.node import Node
from src.monitorables.repo import GitHubRepo
from src.monitorables.system import System

RedisType = Union[bytes, str, int, float]
Monitorable = Union[System, GitHubRepo, Node]
IncreasedAboveThresholdSystemAlert = Union[
    OpenFileDescriptorsIncreasedAboveThresholdAlert,
    SystemCPUUsageIncreasedAboveThresholdAlert,
    SystemRAMUsageIncreasedAboveThresholdAlert,
    SystemStorageUsageIncreasedAboveThresholdAlert
]
DecreasedBelowThresholdSystemAlert = Union[
    OpenFileDescriptorsDecreasedBelowThresholdAlert,
    SystemCPUUsageDecreasedBelowThresholdAlert,
    SystemRAMUsageDecreasedBelowThresholdAlert,
    SystemStorageUsageDecreasedBelowThresholdAlert
]


class OpsgenieSeverities(Enum):
    CRITICAL = 'P1'
    ERROR = 'P4'
    WARNING = 'P3'
    INFO = 'P5'


class PagerDutySeverities(Enum):
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'


class ChannelTypes(Enum):
    TELEGRAM = 'telegram'
    TWILIO = 'twilio'
    EMAIL = 'email'
    OPSGENIE = 'opsgenie'
    PAGERDUTY = 'pagerduty'
    CONSOLE = 'console'
    LOG = 'log'


class ChannelHandlerTypes(Enum):
    ALERTS = 'alerts'
    COMMANDS = 'commands'


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


def convert_to_float_if_not_none_and_not_empty_str(value: Union[int, str, float,
                                                                bytes, None],
                                                   default_return: Any) -> Any:
    # This function converts a value to float if it is not None and not empty
    # str, otherwise it returns a default return
    return float(value) if value is not None and value != '' else default_return


def convert_to_int_if_not_none_and_not_empty_str(value: Union[int, str, float,
                                                              bytes, None],
                                                 default_return: Any) -> Any:
    # This function converts a value to int if it is not None and not empty
    # str, otherwise it returns a default return
    return int(value) if value is not None and value != '' else default_return


def str_to_bool(string: str) -> bool:
    return string.lower() in ['true', 'yes']
