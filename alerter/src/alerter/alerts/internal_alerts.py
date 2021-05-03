from src.alerter.alert_code import InternalAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.metric_code import InternalMetricCode
from src.alerter.alert_severities import Severity


# Alert that is sent on Manager start to clear all metrics for all chains from
# Redis
class SystemManagerStarted(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.SystemManagerStarted,
            "Manager: {} has started.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.SystemManagerStarted)


# Alert that is sent to clear all metrics for one chain from Redis when it
# stops
class SystemAlerterStopped(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.SystemAlerterStopped,
            "Alerter: {} has stopped.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.SystemAlerterStopped)


# Alert that is sent on Manager start to clear all metrics for all chains from
# Redis
class GithubManagerStarted(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.GithubManagerStarted,
            "Manager: {} has started.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.GithubManagerStarted)


# Alert that is sent to clear all metrics for all chains from Redis when the
# Manager stops
class GithubManagerStopped(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.GithubManagerStopped,
            "Alerter: {} has stopped.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.GithubManagerStopped)
