from datetime import datetime, timedelta
from typing import Optional

from src.alerter.alert_code.node.cosmos_alert_code import CosmosNodeAlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code.node.cosmos_node_metric_code \
    import GroupedCosmosNodeAlertsMetricCode
from src.utils.datetime import strfdelta


class NodeWentDownAtAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.NodeWentDownAtAlert,
            "Node {} is down, last time checked: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsDown)


class NodeBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.NodeBackUpAgainAlert,
            "Node {} is back up, last successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsDown)


class NodeStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.NodeStillDownAlert,
            "Node {} is still down, it has been down for {}.".format(
                origin_name, strfdelta(timedelta(seconds=difference),
                                       "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsDown)


class ValidatorWasSlashedAlert(Alert):
    def __init__(self, origin_name: str, amount: Optional[float], height: int,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        if amount is None:
            alert_msg = "Validator {} was slashed at height {}.".format(
                origin_name, height)
        else:
            alert_msg = "Validator {} was slashed {} at height {}.".format(
                origin_name, amount, height)
        super().__init__(
            CosmosNodeAlertCode.ValidatorWasSlashedAlert, alert_msg, severity,
            timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.ValidatorWasSlashed)


class NodeIsSyncingAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.NodeIsSyncingAlert,
            "Node {} is syncing.".format(origin_name), severity, timestamp,
            parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsSyncing)


class NodeIsNoLongerSyncingAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.NodeIsNoLongerSyncingAlert,
            "Node {} is no longer syncing.".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.NodeIsSyncing)


class ValidatorIsNotActiveAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.ValidatorIsNotActiveAlert,
            "Validator {} is not in the active set of validators.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.ValidatorIsNotActive)


class ValidatorIsActiveAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.ValidatorIsActiveAlert,
            "Validator {} is now in the active set of validators.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.ValidatorIsNotActive)


class ValidatorIsJailedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.ValidatorIsJailedAlert,
            "Validator {} is currently jailed.".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.ValidatorIsJailed)


class ValidatorIsNoLongerJailedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.ValidatorIsNoLongerJailedAlert,
            "Validator {} is no longer jailed.".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.ValidatorIsJailed)


class BlocksMissedIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, blocks_missed: int, severity: str,
                 timestamp: float, period_seconds: float,
                 threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.BlocksMissedIncreasedAboveThresholdAlert,
            "{} is not signing enough blocks, missed blocks have INCREASED "
            "above {} threshold. Current value: {} missed blocks within "
            "{}.".format(origin_name, threshold_severity, blocks_missed,
                         strfdelta(timedelta(seconds=period_seconds),
                                   "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.BlocksMissedThreshold)


class BlocksMissedDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, blocks_missed: int, severity: str,
                 timestamp: float, period_seconds: float,
                 threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.BlocksMissedDecreasedBelowThresholdAlert,
            "{} is signing enough blocks again, missed blocks have DECREASED "
            "below {} threshold. Current value: {} missed blocks within "
            "{}.".format(origin_name, threshold_severity, blocks_missed,
                         strfdelta(timedelta(seconds=period_seconds),
                                   "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.BlocksMissedThreshold)


class NoChangeInHeightAlert(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            CosmosNodeAlertCode.NoChangeInHeightAlert,
            "The block height of {} was updated at least {} ago. Last synced "
            "block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.NoChangeInHeight)


class BlockHeightUpdatedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            CosmosNodeAlertCode.BlockHeightUpdatedAlert,
            "{} is now receiving blocks again. Last synced block: {}.".format(
                origin_name, last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.NoChangeInHeight)


class BlockHeightDifferenceIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode
                .BlockHeightDifferenceIncreasedAboveThresholdAlert,
            "Node {} is now {} blocks behind the node with the highest block "
            "height. Value has INCREASED above {} threshold.".format(
                origin_name, current_value, threshold_severity),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.BlockHeightDifferenceThreshold)


class BlockHeightDifferenceDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode
                .BlockHeightDifferenceDecreasedBelowThresholdAlert,
            "Node {} is now {} blocks behind the node with the highest block "
            "height. Value has DECREASED below {} threshold.".format(
                origin_name, current_value, threshold_severity),
            severity, timestamp, parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.BlockHeightDifferenceThreshold)


class InvalidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code)


class ValidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code)


class PrometheusInvalidUrlAlert(InvalidUrlAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.PrometheusInvalidUrlAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.PrometheusInvalidUrl
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class PrometheusValidUrlAlert(ValidUrlAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.PrometheusValidUrlAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.PrometheusInvalidUrl
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class CosmosRestInvalidUrlAlert(InvalidUrlAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.CosmosRestInvalidUrlAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.CosmosRestInvalidUrl
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class CosmosRestValidUrlAlert(ValidUrlAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.CosmosRestValidUrlAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.CosmosRestInvalidUrl
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class TendermintRPCInvalidUrlAlert(InvalidUrlAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.TendermintRPCInvalidUrlAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.TendermintRPCInvalidUrl
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class TendermintRPCValidUrlAlert(ValidUrlAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.TendermintRPCValidUrlAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.TendermintRPCInvalidUrl
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class SourceIsDownAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str, source_name: str,
                 alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code,
            "Cannot access the {} source of node {}, last time checked: "
            "{}.".format(source_name, origin_name,
                         datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id, metric_code)


class SourceStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 source_name: str, alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code,
            "The {} source of node {} is still down, it has been down for "
            "{}.".format(source_name, origin_name,
                         strfdelta(timedelta(seconds=difference),
                                   "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id, metric_code)


class SourceBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str, source_name: str,
                 alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code,
            "The {} source of node {} is accessible again, last successful "
            "monitor at: {}.".format(source_name, origin_name,
                                     datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id, metric_code)


class PrometheusSourceIsDownAlert(SourceIsDownAlert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.PrometheusSourceIsDownAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.PrometheusSourceIsDown
        super().__init__(
            origin_name, severity, timestamp, parent_id, origin_id,
            'prometheus', alert_code, metric_code)


class PrometheusSourceStillDownAlert(SourceStillDownAlert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.PrometheusSourceStillDownAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.PrometheusSourceIsDown
        super().__init__(
            origin_name, difference, severity, timestamp, parent_id, origin_id,
            'prometheus', alert_code, metric_code)


class PrometheusSourceBackUpAgainAlert(SourceBackUpAgainAlert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.PrometheusSourceBackUpAgainAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.PrometheusSourceIsDown
        super().__init__(
            origin_name, severity, timestamp, parent_id, origin_id,
            'prometheus', alert_code, metric_code)


class CosmosRestSourceIsDownAlert(SourceIsDownAlert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.CosmosRestSourceIsDownAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.CosmosRestSourceIsDown
        super().__init__(
            origin_name, severity, timestamp, parent_id, origin_id,
            'cosmos-rest', alert_code, metric_code)


class CosmosRestSourceStillDownAlert(SourceStillDownAlert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.CosmosRestSourceStillDownAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.CosmosRestSourceIsDown
        super().__init__(
            origin_name, difference, severity, timestamp, parent_id, origin_id,
            'cosmos-rest', alert_code, metric_code)


class CosmosRestSourceBackUpAgainAlert(SourceBackUpAgainAlert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.CosmosRestSourceBackUpAgainAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.CosmosRestSourceIsDown
        super().__init__(
            origin_name, severity, timestamp, parent_id, origin_id,
            'cosmos-rest', alert_code, metric_code)


class TendermintRPCSourceIsDownAlert(SourceIsDownAlert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.TendermintRPCSourceIsDownAlert
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCSourceIsDown
        )
        super().__init__(
            origin_name, severity, timestamp, parent_id, origin_id,
            'tendermint-rpc', alert_code, metric_code)


class TendermintRPCSourceStillDownAlert(SourceStillDownAlert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.TendermintRPCSourceStillDownAlert
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCSourceIsDown
        )
        super().__init__(
            origin_name, difference, severity, timestamp, parent_id, origin_id,
            'tendermint-rpc', alert_code, metric_code)


class TendermintRPCSourceBackUpAgainAlert(SourceBackUpAgainAlert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.TendermintRPCSourceBackUpAgainAlert
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCSourceIsDown
        )
        super().__init__(
            origin_name, severity, timestamp, parent_id, origin_id,
            'tendermint-rpc', alert_code, metric_code)


class ErrorNoSyncedDataSourcesAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 source_name: str, alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code,
            "Could not retrieve {} data for {}: {}".format(
                source_name, origin_name, message), severity, timestamp,
            parent_id, origin_id, metric_code)


class SyncedDataSourcesFoundAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code)


class ErrorNoSyncedCosmosRestDataSourcesAlert(ErrorNoSyncedDataSourcesAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.ErrorNoSyncedCosmosRestDataSourcesAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.NoSyncedCosmosRestSource
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            'cosmos-rest', alert_code, metric_code)


class SyncedCosmosRestDataSourcesFoundAlert(SyncedDataSourcesFoundAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.SyncedCosmosRestDataSourcesFoundAlert
        metric_code = GroupedCosmosNodeAlertsMetricCode.NoSyncedCosmosRestSource
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class ErrorNoSyncedTendermintRPCDataSourcesAlert(ErrorNoSyncedDataSourcesAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (
            CosmosNodeAlertCode.ErrorNoSyncedTendermintRPCDataSourcesAlert
        )
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.NoSyncedTendermintRPCSource
        )
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            'tendermint-rpc', alert_code, metric_code)


class SyncedTendermintRPCDataSourcesFoundAlert(SyncedDataSourcesFoundAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (
            CosmosNodeAlertCode.SyncedTendermintRPCDataSourcesFoundAlert
        )
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.NoSyncedTendermintRPCSource
        )
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class DataCouldNotBeObtainedAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code)


class DataObtainedAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 alert_code: CosmosNodeAlertCode,
                 metric_code: GroupedCosmosNodeAlertsMetricCode) -> None:
        super().__init__(
            alert_code, "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id, metric_code)


class CosmosRestServerDataCouldNotBeObtainedAlert(DataCouldNotBeObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (
            CosmosNodeAlertCode.CosmosRestServerDataCouldNotBeObtainedAlert
        )
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.CosmosRestDataNotObtained
        )
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class CosmosRestServerDataObtainedAlert(DataObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.CosmosRestServerDataObtainedAlert
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.CosmosRestDataNotObtained
        )
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class TendermintRPCDataCouldNotBeObtainedAlert(DataCouldNotBeObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (
            CosmosNodeAlertCode.TendermintRPCDataCouldNotBeObtainedAlert
        )
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCDataNotObtained
        )
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class TendermintRPCDataObtainedAlert(DataObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = CosmosNodeAlertCode.TendermintRPCDataObtainedAlert
        metric_code = (
            GroupedCosmosNodeAlertsMetricCode.TendermintRPCDataNotObtained
        )
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code)


class MetricNotFoundErrorAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.MetricNotFoundErrorAlert,
            "{}: {}".format(origin_name, message), severity, timestamp,
            parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.MetricNotFound)


class MetricFoundAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            CosmosNodeAlertCode.MetricFoundAlert,
            "{}: {}".format(origin_name, message), severity, timestamp,
            parent_id, origin_id,
            GroupedCosmosNodeAlertsMetricCode.MetricNotFound)
