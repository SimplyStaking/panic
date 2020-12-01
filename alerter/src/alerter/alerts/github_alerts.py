from enum import Enum

from src.alerter.alerts.alert import Alert


class GithubAlertCode(str, Enum):
    NewGitHubReleaseAlert = 'github_alert_1',
    CannotAccessGitHubPageAlert = 'github_alert_2',


class NewGitHubReleaseAlert(Alert):
    def __init__(self, origin_name: str, release_name: str, tag_name: str,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            GithubAlertCode.NewGitHubReleaseAlert,
            "Repo: {} has a new release {} tagged {}.".format(
                origin_name, release_name, tag_name), severity,
            timestamp, parent_id, origin_id)


class CannotAccessGitHubPageAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            GithubAlertCode.CannotAccessGitHubPageAlert,
            "Github page inaccessible {}.".format(origin_name), severity,
            timestamp, parent_id, origin_id)
