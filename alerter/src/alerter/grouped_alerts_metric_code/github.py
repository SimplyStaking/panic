from .grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedGithubAlertsMetricCode(GroupedAlertsMetricCode):
    GithubRelease = 'github_release'
    CannotAccessGithub = 'github_cannot_access'
    APICallError = 'github_api_call_error'
