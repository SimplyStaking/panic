from src.alerter.alert_code import AlertCode


class DockerhubAlertCode(AlertCode):
    DockerHubNewTagAlert = 'dockerhub_alert_1'
    DockerHubUpdatedTagAlert = 'dockerhub_alert_2'
    DockerHubDeletedTagAlert = 'dockerhub_alert_3'
    CannotAccessDockerHubPageAlert = 'dockerhub_alert_4'
    DockerHubPageNowAccessibleAlert = 'dockerhub_alert_5'
    DockerHubTagsAPICallErrorAlert = 'dockerhub_alert_6'
    DockerHubTagsAPICallErrorResolvedAlert = 'dockerhub_alert_7'
