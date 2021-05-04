from src.alerter.alert_code import InternalAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.metric_code import InternalMetricCode
from src.alerter.alert_severities import Severity

"""
These internal alerts are used to send data from the alerter to the data store
to notify the data store what needs to be changed in REDIS.

ComponentReset is used to reset metrics for one chain, this is used when
an individual alerter starts/stops

ComponentResetAll is used to reset metrics for all chains, this is used when
an alerter manager is started.
"""


class ComponentReset(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.ComponentReset,
            "Component: {} has been reset for one chain.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.ComponentReset)


class ComponentResetAll(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.ComponentResetAll,
            "Component: {} has been reset for all chains.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.ComponentResetAll)
