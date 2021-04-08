from .alert_code import AlertCode


class InternalAlertCode(AlertCode):
    SystemManagerStarted = 'system_manager_started'
    SystemAlerterStarted = 'system_alerter_started'
    SystemAlerterStopped = 'system_alerter_stopped'
    GithubManagerStarted = 'github_manager_started'
    GithubAlerterStarted = 'github_alerter_started'
    GithubAlerterStopped = 'github_alerter_stopped'
