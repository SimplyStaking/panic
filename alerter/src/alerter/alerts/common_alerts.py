from typing import List, Union

from src.alerter.alert_code import AlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code import GroupedAlertsMetricCode


class ErrorNoSyncedDataSourcesAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 source_name: str, alert_code: AlertCode,
                 metric_code: GroupedAlertsMetricCode,
                 metric_state_args: List[Union[str, int]]) -> None:
        super().__init__(
            alert_code,
            "Could not retrieve {} data for {}: {}".format(
                source_name, origin_name, message), severity, timestamp,
            parent_id, origin_id, metric_code, metric_state_args)


class SyncedDataSourcesFoundAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: AlertCode, metric_code: GroupedAlertsMetricCode,
                 metric_state_args: List[Union[str, int]]) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code, metric_state_args)


class DataCouldNotBeObtainedAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: AlertCode, metric_code: GroupedAlertsMetricCode,
                 metric_state_args: List[Union[str, int]]) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code, metric_state_args)


class DataObtainedAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: AlertCode, metric_code: GroupedAlertsMetricCode,
                 metric_state_args: List[Union[str, int]]) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code, metric_state_args)
