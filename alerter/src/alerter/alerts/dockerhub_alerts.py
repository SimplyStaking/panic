from src.alerter.alert_code import DockerhubAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code import (
    GroupedDockerhubAlertsMetricCode)


class DockerHubNewTagAlert(Alert):
    def __init__(self, repo_namespace: str, repo_name: str, tag_name: str,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            DockerhubAlertCode.DockerHubNewTagAlert,
            "Repo {}/{} has a new tag: {}.".format(
                repo_namespace, repo_name, tag_name), severity, timestamp,
            parent_id, origin_id,
            GroupedDockerhubAlertsMetricCode.DockerhubNewTag)


class DockerHubUpdatedTagAlert(Alert):
    def __init__(self, repo_namespace: str, repo_name: str, tag_name: str,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            DockerhubAlertCode.DockerHubUpdatedTagAlert,
            "Repo {}/{} has had an update released for the tag {}.".format(
                repo_namespace, repo_name, tag_name), severity, timestamp,
            parent_id, origin_id,
            GroupedDockerhubAlertsMetricCode.DockerhubUpdatedTag)


class DockerHubDeletedTagAlert(Alert):
    def __init__(self, repo_namespace: str, repo_name: str, tag_name: str,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            DockerhubAlertCode.DockerHubDeletedTagAlert,
            "Tag {} was deleted from repo {}/{}.".format(
                tag_name, repo_namespace, repo_name), severity, timestamp,
            parent_id, origin_id,
            GroupedDockerhubAlertsMetricCode.DockerhubDeletedTag)


class CannotAccessDockerHubPageAlert(Alert):
    def __init__(self, repo_namespace: str, repo_name: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            DockerhubAlertCode.CannotAccessDockerHubPageAlert,
            "Dockerhub page {}/{} is inaccessible.".format(repo_namespace,
                                                           repo_name),
            severity, timestamp, parent_id, origin_id,
            GroupedDockerhubAlertsMetricCode.CannotAccessDockerhub)


class DockerHubPageNowAccessibleAlert(Alert):
    def __init__(self, repo_namespace: str, repo_name: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            DockerhubAlertCode.DockerHubPageNowAccessibleAlert,
            "Dockerhub page {}/{} is now accessible.".format(repo_namespace,
                                                             repo_name),
            severity, timestamp, parent_id, origin_id,
            GroupedDockerhubAlertsMetricCode.CannotAccessDockerhub)


class DockerHubTagsAPICallErrorAlert(Alert):
    def __init__(self, repo_namespace: str, repo_name: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 error_msg: str) -> None:
        super().__init__(
            DockerhubAlertCode.DockerHubTagsAPICallErrorAlert,
            "{}/{}: {}".format(repo_namespace, repo_name, error_msg),
            severity, timestamp, parent_id, origin_id,
            GroupedDockerhubAlertsMetricCode.TagsAPICallError)


class DockerHubTagsAPICallErrorResolvedAlert(Alert):
    def __init__(self, repo_namespace: str, repo_name: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str, ) -> None:
        super().__init__(
            DockerhubAlertCode.DockerHubTagsAPICallErrorResolvedAlert,
            "{}/{}: DockerHub Tags API call no longer causing errors.".format(
                repo_namespace, repo_name),
            severity, timestamp, parent_id, origin_id,
            GroupedDockerhubAlertsMetricCode.TagsAPICallError)
