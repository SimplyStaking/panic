from src.alerter.alert_code import InternalAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.metric_code import InternalMetricCode
from src.alerter.alert_severities import Severity

"""
These internal alerts are used to send data from the alerter to the data store
to notify the data store what needs to be changed in REDIS.

ComponentResetChains is used to reset metrics for one chain, this is used when
an individual alerter starts/stops

ComponentResetAllChains is used to reset metrics for all chains, this is used when
an alerter manager is started.
"""


class ComponentResetChains(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.ComponentResetChains,
            "Component: {} has been reset for the chain {}.".format(
                origin_id, origin_name), Severity.INTERNAL.value, timestamp,
            parent_id, origin_id, InternalMetricCode.ComponentResetChains)


class ComponentResetAllChains(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.ComponentResetAllChains,
            "Component: {} has been reset for all chains.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.ComponentResetAllChains)
