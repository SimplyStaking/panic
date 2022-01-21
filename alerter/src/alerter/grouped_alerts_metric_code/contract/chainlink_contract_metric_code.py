from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedChainlinkContractAlertsMetricCode(GroupedAlertsMetricCode):
    PriceFeedNotObserved = 'cl_contract_price_feed_not_observed'
    PriceFeedDeviation = 'cl_contract_price_feed_deviation'
    ConsensusFailure = 'cl_contract_consensus_failure'
    ErrorContractsNotRetrieved = 'cl_contract_contracts_not_retrieved'
    ErrorNoSyncedDataSources = 'cl_contract_no_synced_data_sources'
