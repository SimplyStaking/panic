from typing import Dict, Optional

from src.alerter.alert_code.network.substrate_alert_code import (
    SubstrateNetworkAlertCode as AlertCode
)
from src.alerter.alerts.alert import Alert
from src.alerter.alerts.common_alerts import (
    DataCouldNotBeObtainedAlert, DataObtainedAlert,
    ErrorNoSyncedDataSourcesAlert, SyncedDataSourcesFoundAlert)
from src.alerter.grouped_alerts_metric_code.network \
    .substrate_network_metric_code \
    import GroupedSubstrateNetworkAlertsMetricCode as GroupedAlertsMetricCode


class GrandpaIsStalledAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.GrandpaIsStalledAlert,
            "Grandpa is stalled on {}".format(origin_name), severity, timestamp,
            parent_id, origin_id, GroupedAlertsMetricCode.GrandpaIsStalled, [])


class GrandpaIsNoLongerStalledAlert(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.GrandpaIsNoLongerStalledAlert,
            "Grandpa is no longer stalled on {}".format(origin_name), severity,
            timestamp, parent_id, origin_id,
            GroupedAlertsMetricCode.GrandpaIsStalled, [])


class NewProposalSubmittedAlert(Alert):
    def __init__(self, origin_name: str, proposal_id: int, seconded: Dict,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        alert_msg = (
            "A new proposal (ID: {}) is now available for seconding on {}"
        ).format(proposal_id, origin_name)

        if any(seconded[address] for address in seconded):
            alert_msg += ":\n"
            for address, second in seconded.items():
                if second:
                    alert_msg += "{} seconded\n".format(address)

        super().__init__(
            AlertCode.NewProposalSubmittedAlert, alert_msg, severity,
            timestamp, parent_id, origin_id,
            GroupedAlertsMetricCode.NewProposalSubmitted, [proposal_id])


class NewReferendumSubmittedAlert(Alert):
    def __init__(self, origin_name: str, referendum_id: int,
                 is_passing: Optional[bool], voting_end_block: int,
                 votes: Dict, severity: str, timestamp: float,
                 parent_id: str, origin_id: str) -> None:
        alert_msg = ("A new referendum is now available for voting on {}:\n"
                     "Proposal ID: {}\n".format(origin_name, referendum_id))
        if is_passing is not None:
            alert_msg += "Status: {}\n".format('Passing' if is_passing else
                                               'Not Passing')
        alert_msg += "Voting end block: {}\n".format(voting_end_block)

        for address, voted in votes.items():
            if voted:
                alert_msg += "{} voted\n".format(address)

        super().__init__(
            AlertCode.ReferendumInfoAlert, alert_msg, severity, timestamp,
            parent_id, origin_id, GroupedAlertsMetricCode.ReferendumInfo,
            [referendum_id])


class ReferendumConcludedAlert(Alert):
    def __init__(self, origin_name: str, referendum_id: int, approved: bool,
                 severity: str, timestamp: float, parent_id: str,
                 origin_id: str) -> None:
        alert_msg = "Referendum {} concluded and was {} on {}".format(
            referendum_id, 'approved' if approved else 'not approved',
            origin_name
        )
        super().__init__(
            AlertCode.ReferendumInfoAlert, alert_msg, severity, timestamp,
            parent_id, origin_id, GroupedAlertsMetricCode.ReferendumInfo,
            [referendum_id])


class ErrorNoSyncedSubstrateWebSocketDataSourcesAlert(
    ErrorNoSyncedDataSourcesAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = AlertCode.ErrorNoSyncedSubstrateWebSocketDataSourcesAlert
        metric_code = (GroupedAlertsMetricCode.
                       NoSyncedSubstrateWebSocketDataSource)
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            'websocket', alert_code, metric_code, [])


class SyncedSubstrateWebSocketDataSourcesFoundAlert(
    SyncedDataSourcesFoundAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = AlertCode.SyncedSubstrateWebSocketDataSourcesFoundAlert
        metric_code = (GroupedAlertsMetricCode.
                       NoSyncedSubstrateWebSocketDataSource)
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code, [])


class SubstrateNetworkDataCouldNotBeObtainedAlert(DataCouldNotBeObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = AlertCode.SubstrateNetworkDataCouldNotBeObtainedAlert
        metric_code = GroupedAlertsMetricCode.SubstrateNetworkDataNotObtained
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code, [])


class SubstrateNetworkDataObtainedAlert(DataObtainedAlert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        alert_code = AlertCode.SubstrateNetworkDataObtainedAlert
        metric_code = GroupedAlertsMetricCode.SubstrateNetworkDataNotObtained
        super().__init__(
            origin_name, message, severity, timestamp, parent_id, origin_id,
            alert_code, metric_code, [])


class SubstrateApiIsNotReachableAlert(Alert):
    def __init__(self, _: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SubstrateApiIsNotReachableAlert, message, severity,
            timestamp, parent_id, origin_id,
            GroupedAlertsMetricCode.SubstrateApiNotReachable, [])


class SubstrateApiIsReachableAlert(Alert):
    def __init__(self, _: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            AlertCode.SubstrateApiIsReachableAlert, message, severity,
            timestamp, parent_id, origin_id,
            GroupedAlertsMetricCode.SubstrateApiNotReachable, [])
