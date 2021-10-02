from datetime import datetime, timedelta

from src.alerter.alert_code.contract.chainlink_alert_code import (
    ChainlinkContractAlertCode)
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code.contract.chainlink_contract_metric_code \
    import GroupedChainlinkContractAlertsMetricCode as MetricCode
from src.utils.datetime import strfdelta


class PriceFeedObservationsIncreasedAboveThreshold(Alert):
    def __init__(self, origin_name: str, missed_observations: int,
                 severity: str, timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedNotObserved,
            "The Chainlink {} node's missed observations have increased above "
            "threshold {} to {} missed observations for the price feed {} of "
            "the chain {}.".format(
                origin_name, threshold_severity, missed_observations,
                proxy_address, parent_id),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedNotObserved,
            {'contract_proxy_address': proxy_address})


class PriceFeedObservationsDecreasedBelowThreshold(Alert):
    def __init__(self, origin_name: str, missed_observations: int,
                 severity: str, timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedObserved,
            "The Chainlink {} node's missed observations have decreased below "
            "threshold {} to {} missed observations for the price feed {} of "
            "the chain {}.".format(
                origin_name, threshold_severity, missed_observations,
                proxy_address, parent_id),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedNotObserved,
            {'contract_proxy_address': proxy_address})


class PriceFeedDeviationInreasedAboveThreshold(Alert):
    def __init__(self, origin_name: str, deviation: float, severity: str,
                 timestamp: float, threshold_severity: str,
                 parent_id: str, origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedDeviationInreasedAboveThreshold,
            "The Chainlink {} node's submission has increased above the "
            "threshold {} to {}% deviation for the price feed {} of the chain "
            "{}.".format(origin_name, threshold_severity, deviation,
                         proxy_address, parent_id),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedDeviation,
            {'contract_proxy_address': proxy_address})


class PriceFeedDeciationDecreasedBelowThreshold(Alert):
    def __init__(self, origin_name: str, deviation: float, severity: str,
                 timestamp: float, threshold_severity: str, parent_id: str,
                 origin_id: str, proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedDeciationDecreasedBelowThreshold,
            "The Chainlink {} node's submission has decreased below the "
            "threshold {} to {}% deviation for the price feed {} of the chain "
            "{}.".format(origin_name, threshold_severity, deviation,
                         proxy_address, parent_id),
            severity, timestamp, parent_id, origin_id,
            MetricCode.PriceFeedDeviation,
            {'contract_proxy_address': proxy_address})


class ConsensusFailure(Alert):
    def __init__(self, origin_name: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 proxy_address: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ConsensusNotReached,
            "The Price Feed {} has a Consensus failure for the chain {}."
            "The Chainlink Node observing the price feed is {}."
            .format(proxy_address, parent_id, origin_name),
            severity, timestamp, parent_id, origin_id,
            MetricCode.ConsensusFailure)


class ErrorRetrievingChainlinkContractData(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ErrorRetrievingChainlinkContractData,
            "{}: {}".format(parent_id, message), severity, timestamp,
            parent_id, origin_id,
            MetricCode.ErrorRetrievingChainlinkContractData)


class ChainlinkContractDataNowBeingRetrieved(Alert):
    def __init__(self, origin_name: str, message: str, severity: str,
                 timestamp: float, parent_id: str, origin_id: str) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ChainlinkContractDataNowBeingRetrieved,
            "{}: {}".format(parent_id, message), severity, timestamp,
            parent_id, origin_id,
            MetricCode.ErrorRetrievingChainlinkContractData)