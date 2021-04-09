from .alert_code import AlertCode


class InternalAlertCode(AlertCode):
    SystemManagerStarted = 'system_manager_started'
    SystemAlerterStopped = 'system_alerter_stopped'
    GithubManagerStarted = 'github_manager_started'
    GithubManagerStopped = 'github_manager_stopped'
