from src.alerter.alert_code import AlertCode


class GithubAlertCode(AlertCode):
    NewGitHubReleaseAlert = 'github_alert_1'
    CannotAccessGitHubPageAlert = 'github_alert_2'
    GitHubPageNowAccessibleAlert = 'github_alert_3'
