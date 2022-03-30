from .grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedDockerhubAlertsMetricCode(GroupedAlertsMetricCode):
    DockerhubNewTag = 'dockerhub_new_tag'
    DockerhubUpdatedTag = 'dockerhub_updated_tag'
    DockerhubDeletedTag = 'dockerhub_deleted_tag'
    CannotAccessDockerhub = 'dockerhub_cannot_access'
    TagsAPICallError = 'dockerhub_tags_api_call_error'
