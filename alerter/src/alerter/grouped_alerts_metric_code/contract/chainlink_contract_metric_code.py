from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedChainlinkContractAlertsMetricCode(GroupedAlertsMetricCode):
    PriceFeedNotObserved = 'price_feed_not_observed'
    PriceFeedDeviation = 'price_feed_deviation'
    ConsensusFailure = 'consensus_failure'
    ErrorRetrievingChainlinkContractData = \
        'error_retrieving_chainlink_contract_data'

# @TODO REMOVE
"""
name=price_feed_not_observed
parent_id=chain_name_2be935b4-1072-469c-a5ff-1495f032fefa
enabled=true
warning_threshold=1
warning_enabled=true
critical_threshold=2
critical_repeat=300
critical_repeat_enabled=true
critical_enabled=true

[11]
name=price_feed_deviation
parent_id=chain_name_2be935b4-1072-469c-a5ff-1495f032fefa
enabled=true
warning_threshold=4
warning_enabled=true
critical_threshold=5
critical_repeat=300
critical_repeat_enabled=true
critical_enabled=true

[11]
name=error_retrieving_chainlink_contract_data
parent_id=chain_name_2be935b4-1072-469c-a5ff-1495f032fefa
enabled=true
warning_threshold=120
warning_enabled=true
critical_threshold=300
critical_repeat=300
critical_repeat_enabled=true
critical_enabled=true

[18]
name=consensus_failure
parent_id=chain_name_2be935b4-1072-469c-a5ff-1495f032fefa
enabled=true
severity=INFO
"""
