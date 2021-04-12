from src.alerter.metric_code.metric_code import MetricCode


class InternalMetricCode(MetricCode):
    SystemManagerStarted = 'system_manager_started'
    SystemAlerterStopped = 'system_alerter_stopped'
    GithubManagerStarted = 'github_manager_started'
    GithubManagerStopped = 'github_manager_stopped'
