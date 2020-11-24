from typing import Union, Any

from src.alerter.alerts.system_alerts import \
    OpenFileDescriptorsIncreasedAboveThresholdAlert, \
    SystemCPUUsageIncreasedAboveThresholdAlert, \
    SystemRAMUsageIncreasedAboveThresholdAlert, \
    SystemStorageUsageIncreasedAboveThresholdAlert, \
    OpenFileDescriptorsDecreasedBelowThresholdAlert, \
    SystemCPUUsageDecreasedBelowThresholdAlert, \
    SystemRAMUsageDecreasedBelowThresholdAlert, \
    SystemStorageUsageDecreasedBelowThresholdAlert
from src.health_checker.heartbeat_handler import HeartbeatHandler
from src.health_checker.ping_publisher import PingPublisher

RedisType = Union[bytes, str, int, float]
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
HealthCheckerComponentType = Union[HeartbeatHandler, PingPublisher]


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
