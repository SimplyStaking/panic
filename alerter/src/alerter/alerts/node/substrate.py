from datetime import datetime, timedelta
from typing import Optional

from src.alerter.alert_code.node.substrate_alert_code import (
    SubstrateNodeAlertCode)
from src.alerter.alerts.alert import Alert
from src.alerter.alerts.common_alerts import (
    DataCouldNotBeObtainedAlert, DataObtainedAlert,
    ErrorNoSyncedDataSourcesAlert, SyncedDataSourcesFoundAlert)
from src.alerter.grouped_alerts_metric_code.node.substrate_node_metric_code \
    import GroupedSubstrateNodeAlertsMetricCode
from src.utils.datetime import strfdelta


class NodeWentDownAtAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.NodeWentDownAtAlert,
            "Node {} is down, last time checked: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsDown, [origin_id])


class NodeBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.NodeBackUpAgainAlert,
            "Node {} is back up, last successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsDown, [origin_id])


class NodeStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.NodeStillDownAlert,
            "Node {} is still down, it has been down for {}.".format(
                origin_name, strfdelta(timedelta(seconds=difference),
                                       "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsDown, [origin_id])


class NoChangeInBestBlockHeightAlert(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_best_block: int) -> None:
        super().__init__(
            SubstrateNodeAlertCode.NoChangeInBestBlockHeightAlert,
            "The best block height of {} was updated at least {} ago. Last "
            "best block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_best_block),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NoChangeInBestBlockHeight,
            [origin_id])


class BestBlockHeightUpdatedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str,
                 last_processed_best_block: int) -> None:
        super().__init__(
            SubstrateNodeAlertCode.BestBlockHeightUpdatedAlert,
            "The best block height of {} was updated. Last best block: "
            "{}.".format(origin_name, last_processed_best_block),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NoChangeInBestBlockHeight,
            [origin_id])


class NoChangeInFinalizedBlockHeightAlert(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_finalized_block: int) -> None:
        super().__init__(
            SubstrateNodeAlertCode.NoChangeInFinalizedBlockHeightAlert,
            "The finalized block height of {} was updated at least {} ago. "
            "Last finalized block: {}.".format(
                origin_name, strfdelta(timedelta(seconds=duration),
                                       "{hours}h, {minutes}m, {seconds}s"),
                last_processed_finalized_block),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NoChangeInFinalizedBlockHeight,
            [origin_id])


class FinalizedBlockHeightUpdatedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str,
                 last_processed_finalized_block: int) -> None:
        super().__init__(
            SubstrateNodeAlertCode.FinalizedBlockHeightUpdatedAlert,
            "The finalized block height of {} was updated. Last finalized "
            "block: {}.".format(origin_name, last_processed_finalized_block),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NoChangeInFinalizedBlockHeight,
            [origin_id])


class NodeIsSyncingAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.NodeIsSyncingAlert,
            "The best block height of {} is now {} blocks behind its target "
            "sync height. Value has INCREASED above {} threshold.".format(
                origin_name, current_value, threshold_severity),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsSyncing, [origin_id])


class NodeIsNoLongerSyncingAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.NodeIsNoLongerSyncingAlert,
            "The best block height of {} is now {} blocks behind its target "
            "sync height. Value has DECREASED below {} threshold.".format(
                origin_name, current_value, threshold_severity),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.NodeIsSyncing, [origin_id])


class ValidatorIsNotActiveAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorIsNotActiveAlert,
            "Validator {} is not in the active set of validators.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorIsNotActive,
            [origin_id])


class ValidatorIsActiveAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorIsActiveAlert,
            "Validator {} is now in the active set of validators.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorIsNotActive,
            [origin_id])


class ValidatorIsDisabledAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorIsDisabledAlert,
            "Validator {} has been disabled.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorIsDisabled,
            [origin_id])


class ValidatorIsNoLongerDisabledAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorIsNoLongerDisabledAlert,
            "Validator {} is no longer disabled.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorIsDisabled,
            [origin_id])


class ValidatorWasNotElectedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorWasNotElectedAlert,
            "Validator {} was not elected for next session.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorWasNotElected,
            [origin_id])


class ValidatorWasElectedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorWasElectedAlert,
            "Validator {} was elected for next session.".format(
                origin_name), severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorWasNotElected,
            [origin_id])


class ValidatorBondedAmountChangedAlert(Alert):
    def __init__(self, origin_name: str, current: float, previous: float,
                 symbol: Optional[str], severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        if symbol:
            message = (
                "The bonded amount of validator {} was changed from {} {} to "
                "{} {}.".format(origin_name, previous, symbol, current, symbol))
        else:
            message = ("The bonded amount of validator {} was changed from {} "
                       "to {}.".format(origin_name, previous, current))
        super().__init__(
            SubstrateNodeAlertCode.ValidatorBondedAmountChangedAlert,
            message, severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorBondedAmountChanged,
            [origin_id])


class ValidatorNoHeartbeatAndBlockAuthoredYetAlert(Alert):
    def __init__(self, origin_name: str, session_index: int, duration: float,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        metric_code = (SubstrateNodeAlertCode.
                       ValidatorNoHeartbeatAndBlockAuthoredYetAlert)
        grp_metric_code = (GroupedSubstrateNodeAlertsMetricCode.
                           ValidatorNoHeartbeatAndBlockAuthoredYetAlert)
        super().__init__(
            metric_code,
            "Validator {} did not send a heartbeat and did not author block in "
            "current session yet. Session: {} has been ongoing for "
            "{}.".format(origin_name, session_index, strfdelta(
                timedelta(seconds=duration), "{hours}h, {minutes}m, {seconds}s"
            )), severity, timestamp, parent_id, origin_id, grp_metric_code,
            [origin_id, session_index])


class ValidatorHeartbeatSentOrBlockAuthoredAlert(Alert):
    def __init__(self, origin_name: str, session_index: int, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        grp_metric_code = (GroupedSubstrateNodeAlertsMetricCode.
                           ValidatorNoHeartbeatAndBlockAuthoredYetAlert)
        super().__init__(
            SubstrateNodeAlertCode.ValidatorHeartbeatSentOrBlockAuthoredAlert,
            "Validator {} sent a heartbeat or authored block in current "
            "session. Session: {}.".format(origin_name, session_index),
            severity, timestamp, parent_id, origin_id, grp_metric_code,
            [origin_id, session_index])


class ValidatorWasOfflineAlert(Alert):
    def __init__(self, origin_name: str, height: int, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorWasOfflineAlert,
            "An Offline event was generated for validator {} at height {}"
            ".".format(origin_name, height), severity, timestamp, parent_id,
            origin_id, GroupedSubstrateNodeAlertsMetricCode.ValidatorWasOffline,
            [origin_id, height])


class ValidatorWasSlashedAlert(Alert):
    def __init__(self, origin_name: str, amount: int, height: int,
                 symbol: Optional[str], severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        if symbol:
            message = "Validator {} was slashed {} {} at height {}.".format(
                origin_name, amount, symbol, height)
        else:
            message = "Validator {} was slashed {} at height {}.".format(
                origin_name, symbol, height)
        super().__init__(
            SubstrateNodeAlertCode.ValidatorWasSlashedAlert,
            message, severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorWasSlashed,
            [origin_id, height])


class ValidatorPayoutNotClaimedAlert(Alert):
    def __init__(self, origin_name: str, era: int, eras_count: int,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorPayoutNotClaimedAlert,
            "Validator {} has an unclaimed payout for era {}, which has been "
            "unclaimed for {} eras.".format(origin_name, era, eras_count),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorPayoutNotClaimed,
            [origin_id, era])


class ValidatorPayoutClaimedAlert(Alert):
    def __init__(self, origin_name: str, era: int, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.ValidatorPayoutClaimedAlert,
            "Validator {} has claimed payout for era {}.".format(
                origin_name, era),
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.ValidatorPayoutNotClaimed,
            [origin_id, era])


class ValidatorControllerAddressChangedAlert(Alert):
    def __init__(self, origin_name: str, current: int, previous: int,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        metric_code = (GroupedSubstrateNodeAlertsMetricCode.
                       ValidatorControllerAddressChanged)
        super().__init__(
            SubstrateNodeAlertCode.ValidatorControllerAddressChangedAlert,
            "The controller address of validator {} was changed from {} to "
            "{}.".format(origin_name, previous, current),
            severity, timestamp, parent_id, origin_id, metric_code, [origin_id])


class ErrorNoSyncedSubstrateWebSocketDataSourcesAlert(
    ErrorNoSyncedDataSourcesAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (SubstrateNodeAlertCode.
                      ErrorNoSyncedSubstrateWebSocketDataSourcesAlert)
        metric_code = (GroupedSubstrateNodeAlertsMetricCode.
                       NoSyncedSubstrateWebSocketSource)
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            'websocket', alert_code, metric_code, [origin_id])


class SyncedSubstrateWebSocketDataSourcesFoundAlert(
    SyncedDataSourcesFoundAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (SubstrateNodeAlertCode.
                      SyncedSubstrateWebSocketDataSourcesFoundAlert)
        metric_code = (GroupedSubstrateNodeAlertsMetricCode.
                       NoSyncedSubstrateWebSocketDataSource)
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code, [origin_id])


class SubstrateWebSocketDataCouldNotBeObtainedAlert(
    DataCouldNotBeObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (SubstrateNodeAlertCode.
                      SubstrateWebSocketDataCouldNotBeObtainedAlert)
        metric_code = (GroupedSubstrateNodeAlertsMetricCode.
                       SubstrateWebSocketDataNotObtained)
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code, [origin_id])


class SubstrateWebSocketDataObtainedAlert(DataObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = (SubstrateNodeAlertCode.
                      SubstrateWebSocketDataObtainedAlert)
        metric_code = (GroupedSubstrateNodeAlertsMetricCode.
                       SubstrateWebSocketDataNotObtained)
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code, [origin_id])


class SubstrateApiIsNotReachableAlert(Alert):
    def __init__(self, _: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.SubstrateApiIsNotReachableAlert, message,
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.SubstrateApiNotReachable,
            [origin_id])


class SubstrateApiIsReachableAlert(Alert):
    def __init__(self, _: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SubstrateNodeAlertCode.SubstrateApiIsReachableAlert, message,
            severity, timestamp, parent_id, origin_id,
            GroupedSubstrateNodeAlertsMetricCode.SubstrateApiNotReachable,
            [origin_id])
