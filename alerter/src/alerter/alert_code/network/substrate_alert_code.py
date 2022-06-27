from ..alert_code import AlertCode


class SubstrateNetworkAlertCode(AlertCode):
    GrandpaIsStalledAlert = 'substrate_network_alert_1'
    GrandpaIsNoLongerStalledAlert = 'substrate_network_alert_2'
    NewProposalSubmittedAlert = 'substrate_network_alert_3'
    ReferendumInfoAlert = 'substrate_network_alert_4'
    ErrorNoSyncedSubstrateWebSocketDataSourcesAlert = (
        'substrate_network_alert_5'
    )
    SyncedSubstrateWebSocketDataSourcesFoundAlert = 'substrate_network_alert_6'
    SubstrateNetworkDataCouldNotBeObtainedAlert = 'substrate_network_alert_7'
    SubstrateNetworkDataObtainedAlert = 'substrate_network_alert_8'
    SubstrateApiIsNotReachableAlert = 'substrate_network_alert_9'
    SubstrateApiIsReachableAlert = 'substrate_network_alert_10'
