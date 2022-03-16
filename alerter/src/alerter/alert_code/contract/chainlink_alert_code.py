from ..alert_code import AlertCode


class ChainlinkContractAlertCode(AlertCode):
    PriceFeedNotObservedIncreaseAboveThreshold = 'cl_contract_alert_1'
    PriceFeedObservedAgain = 'cl_contract_alert_2'
    PriceFeedDeviationIncreasedAboveThreshold = 'cl_contract_alert_3'
    PriceFeedDeviationDecreasedBelowThreshold = 'cl_contract_alert_4'
    ConsensusNotReached = 'cl_contract_alert_5'
    ErrorContractsNotRetrieved = 'cl_contract_alert_6'
    ContractsNowRetrieved = 'cl_contract_alert_7'
    ErrorNoSyncedDataSources = 'cl_contract_alert_8'
    SyncedDataSourcesFound = 'cl_contract_alert_9'
