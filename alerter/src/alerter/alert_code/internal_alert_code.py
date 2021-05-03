from .alert_code import AlertCode


class InternalAlertCode(AlertCode):
    ComponentStarted = 'internal_alert_1'
    ComponentStopped = 'internal_alert_2'
    SystemManagerStarted = 'system_manager_started'
    SystemAlerterStopped = 'system_alerter_stopped'
    GithubManagerStarted = 'github_manager_started'
    GithubManagerStopped = 'github_manager_stopped'
