from src.alerter.alert_code import InternalAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.metric_code import InternalMetricCode
from src.alerter.alert_severties import Severity


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


# Alert that is sent to clear all metrics for one chain from Redis
# when it's started
class SystemAlerterStarted(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.SystemAlerterStarted,
            "Alerter: {} has started.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.SystemAlerterStarted)


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


# Alert that is sent to clear all metrics for chain from Redis when the alerter
# starts
class GithubAlerterStarted(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.GithubAlerterStarted,
            "Alerter: {} has started.".format(origin_name),
            severity, timestamp, parent_id, origin_id,
            InternalAlertCode.GithubAlerterStarted)


# Alert that is sent to clear all metrics for one chain from Redis when it
# stops
class GithubAlerterStopped(Alert):
    def __init__(self, origin_name: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.GithubAlerterStopped,
            "Alerter: {} has stopped.".format(origin_name),
            Severity.INTERNAL.value, timestamp, parent_id, origin_id,
            InternalMetricCode.GithubAlerterStopped)
