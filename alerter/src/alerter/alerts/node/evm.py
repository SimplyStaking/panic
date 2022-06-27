from datetime import datetime, timedelta

from src.alerter.alert_code.node.evm_alert_code import (EVMNodeAlertCode)
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code.node.evm_node_metric_code \
    import GroupedEVMNodeAlertsMetricCode
from src.utils.datetime import strfdelta


class NoChangeInBlockHeight(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            EVMNodeAlertCode.NoChangeInBlockHeight,
            "The block height of {} was updated at least {} ago. Last synced "
            "block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedEVMNodeAlertsMetricCode.NoChangeInBlockHeight, [origin_id])


class BlockHeightUpdatedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            EVMNodeAlertCode.BlockHeightUpdatedAlert,
            "{} is now receiving blocks again. Last synced block: {}.".format(
                origin_name, last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedEVMNodeAlertsMetricCode.NoChangeInBlockHeight, [origin_id])


class BlockHeightDifferenceIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            EVMNodeAlertCode
                .BlockHeightDifferenceIncreasedAboveThresholdAlert,
            "Node {} is now {} blocks behind the node with the highest block "
            "height. Value has INCREASED above {} threshold."
                .format(origin_name, current_value, threshold_severity),
            severity, timestamp, parent_id, origin_id,
            GroupedEVMNodeAlertsMetricCode.BlockHeightDifference, [origin_id])


class BlockHeightDifferenceDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            EVMNodeAlertCode
                .BlockHeightDifferenceDecreasedBelowThresholdAlert,
            "Node {} is now {} blocks behind the node with the highest block "
            "height. Value has DECREASED below {} threshold."
                .format(origin_name, current_value, threshold_severity),
            severity, timestamp, parent_id, origin_id,
            GroupedEVMNodeAlertsMetricCode.BlockHeightDifference, [origin_id])


class InvalidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            EVMNodeAlertCode.InvalidUrlAlert, "{}: {}".format(
                origin_name, message), severity, timestamp, parent_id,
            origin_id, GroupedEVMNodeAlertsMetricCode.InvalidUrl, [origin_id])


class ValidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            EVMNodeAlertCode.ValidUrlAlert, "{}: {}".format(
                origin_name, message), severity, timestamp, parent_id,
            origin_id, GroupedEVMNodeAlertsMetricCode.InvalidUrl, [origin_id])


class NodeWentDownAtAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            EVMNodeAlertCode.NodeWentDownAtAlert,
            "Node {} is down, last time checked: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedEVMNodeAlertsMetricCode.NodeIsDown, [origin_id])


class NodeBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            EVMNodeAlertCode.NodeBackUpAgainAlert,
            "Node {} is back up, last successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedEVMNodeAlertsMetricCode.NodeIsDown, [origin_id])


class NodeStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            EVMNodeAlertCode.NodeStillDownAlert,
            "Node {} is still down, it has been down for {}.".format(
                origin_name, strfdelta(timedelta(seconds=difference),
                                       "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedEVMNodeAlertsMetricCode.NodeIsDown, [origin_id])
