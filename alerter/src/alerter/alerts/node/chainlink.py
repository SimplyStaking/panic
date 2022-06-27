from datetime import datetime, timedelta

from src.alerter.alert_code.node.chainlink_alert_code import (
    ChainlinkNodeAlertCode)
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.utils.datetime import strfdelta


class NoChangeInHeightAlert(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.NoChangeInHeightAlert,
            "The block height of {} was updated at least {} ago. Last synced "
            "block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight, [origin_id])


class BlockHeightUpdatedAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.BlockHeightUpdatedAlert,
            "{} is now receiving blocks again. Last synced block: {}.".format(
                origin_name, last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight, [origin_id])


class NoChangeInTotalHeadersReceivedAlert(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 current_headers_received: int) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.NoChangeInTotalHeadersReceivedAlert,
            "The last block header received by {} was at least {} ago. {} "
            "headers received in total.".format(
                origin_name, strfdelta(timedelta(seconds=duration),
                                       "{hours}h, {minutes}m, {seconds}s"),
                current_headers_received),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInTotalHeadersReceived,
            [origin_id])


class ReceivedANewHeaderAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str,
                 current_headers_received: int) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.ReceivedANewHeaderAlert,
            "{} received a new block header. {} headers received in "
            "total.".format(origin_name, current_headers_received),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoChangeInTotalHeadersReceived,
            [origin_id])


class MaxUnconfirmedBlocksIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
            "{} maximum number of blocks a transaction has been unconfirmed "
            "for has INCREASED above {} threshold. Current value: {} for at "
            "least {}.".format(origin_name, threshold_severity, current_value,
                               strfdelta(timedelta(seconds=duration),
                                         "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold,
            [origin_id])


class MaxUnconfirmedBlocksDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .MaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
            "{} maximum number of blocks a transaction has been unconfirmed "
            "for has DECREASED below {} threshold. Current value: {}.".format(
                origin_name, threshold_severity, current_value),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.MaxUnconfirmedBlocksThreshold,
            [origin_id])


class ChangeInSourceNodeAlert(Alert):
    def __init__(self, origin_name: str, new_source: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.ChangeInSourceNodeAlert,
            "{} restarted. PANIC will use {} as a source node for {}.".format(
                new_source, new_source, origin_name),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.ChangeInSourceNode,
            [origin_id])


class GasBumpIncreasedOverNodeGasPriceLimitAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.GasBumpIncreasedOverNodeGasPriceLimitAlert,
            "Gas bump increased over {}'s gas price limit.".format(origin_name),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode
                .GasBumpIncreasedOverNodeGasPriceLimit, [origin_id])


class NoOfUnconfirmedTxsIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .NoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
            "{} number of unconfirmed transactions have INCREASED above {} "
            "threshold. Current value: {} for at least {}.".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoOfUnconfirmedTxsThreshold,
            [origin_id])


class NoOfUnconfirmedTxsDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .NoOfUnconfirmedTxsDecreasedBelowThresholdAlert,
            "{} number of unconfirmed transactions have DECREASED below {} "
            "threshold. Current value: {}.".format(
                origin_name, threshold_severity, current_value),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NoOfUnconfirmedTxsThreshold,
            [origin_id])


class TotalErroredJobRunsIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .TotalErroredJobRunsIncreasedAboveThresholdAlert,
            "{} total errored jobs INCREASED above {} threshold. {} jobs "
            "errored in {}.".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold,
            [origin_id])


class TotalErroredJobRunsDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: int, severity: str,
                 timestamp: float, duration: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode
                .TotalErroredJobRunsDecreasedBelowThresholdAlert,
            "{} total errored jobs DECREASED below {} threshold. {} jobs "
            "errored in {}. ".format(
                origin_name, threshold_severity, current_value, strfdelta(
                    timedelta(seconds=duration),
                    "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.TotalErroredJobRunsThreshold,
            [origin_id])


class BalanceIncreasedAboveThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, symbol: str,
                 severity: str, timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.BalanceIncreasedAboveThresholdAlert,
            "{} account balance has INCREASED above {} threshold. Current "
            "value: {} {}.".format(
                origin_name, threshold_severity, current_value, symbol),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold, [origin_id])


class BalanceDecreasedBelowThresholdAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, symbol: str,
                 severity: str, timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.BalanceDecreasedBelowThresholdAlert,
            "{} account balance has DECREASED below {} threshold. Current "
            "value: {} {}.".format(
                origin_name, threshold_severity, current_value, symbol),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceThreshold, [origin_id])


class BalanceToppedUpAlert(Alert):
    def __init__(self, origin_name: str, current_value: float, increase: float,
                 symbol: str, severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.BalanceToppedUpAlert,
            "{} account balance has been topped up by {} {}. Current "
            "value: {} {}.".format(
                origin_name, increase, symbol, current_value, symbol),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.BalanceTopUp, [origin_id])


class InvalidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.InvalidUrlAlert, "{}: {}".format(
                origin_name, message), severity, timestamp, parent_id,
            origin_id, GroupedChainlinkNodeAlertsMetricCode.InvalidUrl,
            [origin_id])


class ValidUrlAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.ValidUrlAlert, "{}: {}".format(
                origin_name, message), severity, timestamp, parent_id,
            origin_id, GroupedChainlinkNodeAlertsMetricCode.InvalidUrl,
            [origin_id])


class PrometheusSourceIsDownAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.PrometheusSourceIsDownAlert,
            "Cannot access the prometheus source of node {}, last time "
            "checked: {}.".format(origin_name,
                                  datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown,
            [origin_id])


class PrometheusSourceBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.PrometheusSourceBackUpAgainAlert,
            "The prometheus source of node {} is accessible again, last "
            "successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.PrometheusSourceIsDown,
            [origin_id])


class NodeWentDownAtAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.NodeWentDownAtAlert,
            "Node {} is down, last time checked: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown, [origin_id])


class NodeBackUpAgainAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.NodeBackUpAgainAlert,
            "Node {} is back up, last successful monitor at: {}.".format(
                origin_name, datetime.fromtimestamp(timestamp)),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown, [origin_id])


class NodeStillDownAlert(Alert):
    def __init__(self, origin_name: str, difference: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.NodeStillDownAlert,
            "Node {} is still down, it has been down for {}.".format(
                origin_name, strfdelta(timedelta(seconds=difference),
                                       "{hours}h, {minutes}m, {seconds}s")),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.NodeIsDown, [origin_id])


class MetricNotFoundErrorAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.MetricNotFoundErrorAlert,
            "{}: {}".format(origin_name, message),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.MetricNotFound, [origin_id])


class MetricFoundAlert(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkNodeAlertCode.MetricFoundAlert,
            "{}: {}".format(origin_name, message),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkNodeAlertsMetricCode.MetricNotFound, [origin_id])
