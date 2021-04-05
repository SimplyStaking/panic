from src.alerter.alert_code import InternalAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.metric_code import InternalMetricCode


class SystemAlerterStarted(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.SystemAlerterStarted,
            "Alerter: {} has started.".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            InternalMetricCode.SystemAlerterStarted)


class GithubAlerterStarted(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            InternalAlertCode.GithubAlerterStarted,
            "Github Alerter started and configured for {}.".format(origin_name),
            severity, timestamp, parent_id, origin_id,
            InternalAlertCode.GithubAlerterStarted)
