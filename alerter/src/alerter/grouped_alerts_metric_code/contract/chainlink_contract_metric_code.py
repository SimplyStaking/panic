from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedChainlinkContractAlertsMetricCode(GroupedAlertsMetricCode):
    PriceFeedNotObserved = 'price_feed_not_observed'
    PriceFeedDeviation = 'price_feed_deviation'
    ConsensusFailure = 'consensus_failure'
    ErrorRetrievingChainlinkContractData = \
        'error_retrieving_chainlink_contract_data'
