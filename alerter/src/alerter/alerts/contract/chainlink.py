from datetime import datetime, timedelta

from src.alerter.alert_code.contract.chainlink_alert_code import (
    ChainlinkContractAlertCode)
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code.contract.chainlink_contract_metric_code \
    import GroupedChainlinkContractAlertsMetricCode
from src.utils.datetime import strfdelta


# @TODO Change the words
class PriceFeedNotObserved(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedNotObserved,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkContractAlertsMetricCode.PriceFeedNotObserved)


class PriceFeedObserved(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedObserved,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkContractAlertsMetricCode.PriceFeedNotObserved)


class PriceFeedDeviating(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedDeviating,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkContractAlertsMetricCode.PriceFeedDeviation)


class PriceFeedNoLongerDeviating(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkContractAlertCode.PriceFeedNoLongerDeviating,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkContractAlertsMetricCode.PriceFeedDeviation)


class ConsensusFailure(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ConsensusNowBeingReached,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkContractAlertsMetricCode.ConsensusFailure)


class ErrorRetrievingChainlinkContractData(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ErrorRetrievingChainlinkContractData,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkContractAlertsMetricCode.
            ErrorRetrievingChainlinkContractData)


class ChainlinkContractDataNowBeingRetrieved(Alert):
    def __init__(self, origin_name: str, duration: float, severity: str,
                 timestamp: float, parent_id: str, origin_id: str,
                 last_processed_block: int) -> None:
        super().__init__(
            ChainlinkContractAlertCode.ChainlinkContractDataNowBeingRetrieved,
            "The latest block height processed by {} was at least {} "
            "ago. Last processed block: {}.".format(origin_name, strfdelta(
                timedelta(seconds=duration),
                "{hours}h, {minutes}m, {seconds}s"), last_processed_block),
            severity, timestamp, parent_id, origin_id,
            GroupedChainlinkContractAlertsMetricCode.
            ErrorRetrievingChainlinkContractData)
