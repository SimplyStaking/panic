from enum import Enum
from src.utils.alerts import next_id, SeverityCode
from src.alerter.alerts import alert


class AlertCode(Enum):
    NewGitHubReleaseAlert = next_id(),
    CannotAccessGitHubPageAlert = next_id(),


class NewGitHubReleaseAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, release_name: str,
                 tag_name: str, severity: str, timestamp: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.NewGitHubReleaseAlert,
            '{}: {} of {} has just been released tagged {}.'.format(
                parent_name, origin_name, release_name, tag_name), severity,
            timestamp, parent_id, origin_id)


class CannotAccessGitHubPageAlert(Alert):
    def __init__(self, parent_name: str, origin_name: str, severity: str,
                 timestamp: str, parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.CannotAccessGitHubPageAlert,
            '{}: Github page inaccessible {}.'.format(
              parent_name, origin_name), severity, timestamp, parent_id,
            origin_id)
