from ..alert_code import AlertCode


class ChainlinkContractAlertCode(AlertCode):
    PriceFeedNotObserved = 'cl_contract_alert_1'
    PriceFeedObserved = 'cl_contract_alert_2'
    PriceFeedDeviating = 'cl_contract_alert_3'
    PriceFeedNoLongerDeviating = 'cl_contract_alert_4'
    ConsensusNotReached = 'cl_contract_alert_5'
    ConsensusNowBeingReached = 'cl_contract_alert_6'
    ErrorRetrievingChainlinkContractData = 'cl_contract_alert_7'
    ChainlinkContractDataNowBeingRetrieved = 'cl_contract_alert_8'
