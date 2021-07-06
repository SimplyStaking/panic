from src.alerter.alert_code import GithubAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code import GroupedGithubAlertsMetricCode


class NewGitHubReleaseAlert(Alert):
    def __init__(self, origin_name: str, release_name: str, tag_name: str,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            GithubAlertCode.NewGitHubReleaseAlert,
            "Repo: {} has a new release {} tagged {}.".format(
                origin_name, release_name, tag_name), severity,
            timestamp, parent_id, origin_id,
            GroupedGithubAlertsMetricCode.GithubRelease)


class CannotAccessGitHubPageAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            GithubAlertCode.CannotAccessGitHubPageAlert,
            "Github page inaccessible {}.".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            GroupedGithubAlertsMetricCode.CannotAccessGithub)


class GitHubPageNowAccessibleAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            GithubAlertCode.GitHubPageNowAccessibleAlert,
            "Github page accessible {}.".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            GroupedGithubAlertsMetricCode.CannotAccessGithub)
