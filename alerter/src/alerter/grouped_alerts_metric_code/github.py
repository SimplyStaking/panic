from .grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedGithubAlertsMetricCode(GroupedAlertsMetricCode):
    GithubRelease = 'github_release'
    CannotAccessGithub = 'cannot_access_github'
