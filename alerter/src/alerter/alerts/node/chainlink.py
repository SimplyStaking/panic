from datetime import datetime, timedelta

from src.alerter.alert_code.node.chainlink_alert_code import (
    ChainlinkNodeAlertCode)
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.utils.datetime import strfdelta


class NoChangeInHeightIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.NoChangeInHeightAlert,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight)


class BlockHeightUpdatedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.BlockHeightUpdatedAlert,
            "{} is now processing blocks again. Last processed block: "
            "{}".format(origin_name, last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight)


class HeadsInQueueIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.HeadsInQueueIncreasedAboveThresholdAlert,
            "The number of Ethereum blocks in queue to be processed by {} "
            "INCREASED above {} Threshold. Current value: {} for at least "
            "{}".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold)


class HeadsInQueueDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.HeadsInQueueDecreasedBelowThresholdAlert,
            "The number of Ethereum blocks in queue to be processed by {} "
            "DECREASED below {} Threshold. Current value: {}".format(
                origin_name, threshold_severity, current_value),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.HeadsInQueueThreshold)


class NoChangeInTotalHeadersReceivedAlert(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.NoChangeInTotalHeadersReceivedAlert,
            "The last block header received by {} was at least {} ago.".format(
                origin_name, strfdelta(timedelta(seconds=duration),
                                       "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInTotalHeadersReceived)


class ReceivedANewHeaderAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.ReceivedANewHeaderAlert,
            "{} received a new block header.".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInTotalHeadersReceived)


class DroppedBlockHeadersIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .DroppedBlockHeadersIncreasedAboveThresholdAlert,
            "The number of block headers dropped by {} INCREASED above {} "
            "Threshold. Dropped {} headers in {} ".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold)


class DroppedBlockHeadersDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .DroppedBlockHeadersDecreasedBelowThresholdAlert,
            "The number of block headers dropped by {} DECREASED below {} "
            "Threshold. Dropped {} headers in {} ".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.DroppedBlockHeadersThreshold)


class MaxUnconfirmedBlocksIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            "The maximum number of blocks a transaction has been unconfirmed "
            "for by {} has INCREASED above {} Threshold. Current value: {} "
            "for at least {}".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold)


class MaxUnconfirmedBlocksDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .MaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
            "The maximum number of blocks a transaction has been unconfirmed "
            "for by {} has DECREASED below {} Threshold. Current value: "
            "{}".format(origin_name, threshold_severity, current_value),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold)


class ChangeInSourceNodeAlert(Alert):
    def __init__(self, origin_name: str, new_source: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.ChangeInSourceNodeAlert,
            "{} restarted. PANIC will use {} as a source node for {}.".format(
                new_source, new_source, origin_name),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.ChangeInSourceNode)


class GasBumpIncreasedOverNodeGasPriceLimitAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.GasBumpIncreasedOverNodeGasPriceLimitAlert,
            "Gas bump increased over {}'s gas price limit.".format(origin_name),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode
                .GasBumpIncreasedOverNodeGasPriceLimit)


class NoOfUnconfirmedTxsIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .NoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
            "The number of unconfirmed transactions by {} have INCREASED "
            "above {} Threshold. Current value: {} for at least {}".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoOfUnconfirmedTxsThreshold)


class NoOfUnconfirmedTxsDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .NoOfUnconfirmedTxsDecreasedBelowThresholdAlert,
            "The number of unconfirmed transactions by {} have DECREASED "
            "below {} Threshold. Current value: {}.".format(
                origin_name, threshold_severity, current_value),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoOfUnconfirmedTxsThreshold)


class SystemWentDownAtAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemWentDownAtAlert,
            "{} System is down, last time checked: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedSystemAlertsMetricCode.SystemIsDown)


class SystemBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemBackUpAgainAlert,
            "{} System is back up, last successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedSystemAlertsMetricCode.SystemIsDown)


class SystemStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.SystemStillDownAlert,
            "{} System is still down, it has been down for {}.".format(
                origin_name, strfdelta(timedelta(seconds=difference),
                                       "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedSystemAlertsMetricCode.SystemIsDown)


class MetricNotFoundErrorAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.MetricNotFoundErrorAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id,
            GroupedSystemAlertsMetricCode.MetricNotFound)


class MetricFoundAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.MetricFoundAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id,
            GroupedSystemAlertsMetricCode.MetricNotFound)


class ValidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.ValidUrlAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id,
            GroupedSystemAlertsMetricCode.InvalidUrl)


class InvalidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            SystemAlertCode.InvalidUrlAlert,
            "{}: {}".format(origin_name, message), severity,
            timestamp, parent_id, origin_id,
            GroupedSystemAlertsMetricCode.InvalidUrl)
