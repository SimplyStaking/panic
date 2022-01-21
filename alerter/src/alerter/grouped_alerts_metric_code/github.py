from .grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedGithubAlertsMetricCode(GroupedAlertsMetricCode):
    GithubRelease = 'github_release'
    CannotAccessGithub = 'github_cannot_access'
