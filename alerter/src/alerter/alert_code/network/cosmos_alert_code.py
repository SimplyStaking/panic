from ..alert_code import AlertCode


class CosmosNetworkAlertCode(AlertCode):
    NewProposalSubmittedAlert = 'cosmos_network_alert_1'
    ProposalConcludedAlert = 'cosmos_network_alert_2'
    ErrorNoSyncedCosmosRestDataSourcesAlert = 'cosmos_network_alert_3'
    SyncedCosmosRestDataSourcesFoundAlert = 'cosmos_network_alert_4'
    CosmosNetworkDataCouldNotBeObtainedAlert = 'cosmos_network_alert_5'
    CosmosNetworkDataObtainedAlert = 'cosmos_network_alert_6'
