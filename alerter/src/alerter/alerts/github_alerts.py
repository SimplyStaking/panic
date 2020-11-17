from enum import Enum

from src.alerter.alerts.alert import Alert
from src.utils.alert import SeverityCode


class AlertCode(str, Enum):
    NewGitHubReleaseAlert = 'github_alert_1',
    CannotAccessGitHubPageAlert = 'github_alert_2',


class NewGitHubReleaseAlert(Alert):
    def __init__(self, origin_name: str, release_name: str, tag_name: str,
                 severity: str, timestamp: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            AlertCode.NewGitHubReleaseAlert,
            'Repo: {} has a new release {} tagged {}.'.format(
                origin_name, release_name, tag_name), severity,
            timestamp, parent_id, origin_id)


class CannotAccessGitHubPageAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.CannotAccessGitHubPageAlert,
            'Github page inaccessible {}.'.format(origin_name), severity,
            timestamp, parent_id, origin_id)
