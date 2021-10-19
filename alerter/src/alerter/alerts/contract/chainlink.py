from datetime import datetime, timedelta

from src.alerter.alert_code.contract.chainlink_alert_code import (
    ChainlinkContractAlertCode)
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code.contract.chainlink_contract_metric_code \
    import GroupedChainlinkContractAlertsMetricCode as MetricCode
from src.utils.datetime import strfdelta


class PriceFeedObservationsMissedIncreasedAboveThreshold(Alert):
    def __init__(self, origin_name: str, missed_observations: int,
                 severity: str, timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedNotObservedIncreaseAboveThreshold,
            "The Chainlink {} node's missed observations have increased above "
            "{} threshold to {} missed observations for price feed {}.".format(
                origin_name, threshold_severity, missed_observations,
                proxy_address),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedNotObserved,
            {'contract_proxy_address': proxy_address})


class PriceFeedObservedAgain(Alert):
    def __init__(self, origin_name: str, severity: str, timestamp: float,
                 parent_id: str, origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedObservedAgain,
            "The Chainlink {} node is no longer missing observations for "
            "price feed {}.".format(
                origin_name, proxy_address),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedNotObserved,
            {'contract_proxy_address': proxy_address})


class PriceFeedDeviationInreasedAboveThreshold(Alert):
    def __init__(self, origin_name: str, deviation: float, severity: str,
                 timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedDeviationInreasedAboveThreshold,
            "The Chainlink {} node's submission has increased above {} "
            "threshold to {}% deviation for the price feed {}.".format(
                origin_name, threshold_severity, deviation,
                proxy_address),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedDeviation,
            {'contract_proxy_address': proxy_address})


class PriceFeedDeviationDecreasedBelowThreshold(Alert):
    def __init__(self, origin_name: str, deviation: float, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedDeviationDecreasedBelowThreshold,
            "The Chainlink {} node's submission has decreased below {} "
            "threshold to {}% deviation for the price feed {}.".format(
                origin_name, threshold_severity, deviation,
                proxy_address),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedDeviation,
            {'contract_proxy_address': proxy_address})


class ConsensusFailure(Alert):
    def __init__(self, origin_name: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ConsensusNotReached,
            "The Price Feed {} has a Consensus failure."
            "The Chainlink Node observing the price feed is {}."
            .format(proxy_address, origin_name),
            severity, timestamp, parent_id, origin_id,
            MetricCode.ConsensusFailure)


class ErrorContractsNotRetrieved(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ErrorContractsNotRetrieved,
            "{}: {}".format(parent_id, message), severity, timestamp,
            parent_id, origin_id,
            MetricCode.ErrorContractsNotRetrieved)


class ContractsNowRetrieved(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ContractsNowRetrieved,
            "{}: {}".format(parent_id, message), severity, timestamp,
            parent_id, origin_id,
            MetricCode.ErrorContractsNotRetrieved)


class ErrorNoSyncedDataSources(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ErrorNoSyncedDataSources,
            "{}: {}".format(parent_id, message), severity, timestamp,
            parent_id, origin_id,
            MetricCode.ErrorNoSyncedDataSources)


class SyncedDataSourcesFound(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.SyncedDataSourcesFound,
            "{}: {}".format(parent_id, message), severity, timestamp,
            parent_id, origin_id,
            MetricCode.ErrorNoSyncedDataSources)
