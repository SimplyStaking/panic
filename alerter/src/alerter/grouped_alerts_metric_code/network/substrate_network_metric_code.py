from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedSubstrateNetworkAlertsMetricCode(GroupedAlertsMetricCode):
    GrandpaIsStalled = 'substrate_network_grandpa_stalled'
    NewProposalSubmitted = 'substrate_network_proposal_submitted'
    ReferendumInfo = 'substrate_network_referendum_info'
    NoSyncedSubstrateWebSocketDataSource = (
        'substrate_network_no_synced_substrate_websocket_source'
    )
    SubstrateNetworkDataNotObtained = (
        'substrate_network_substrate_network_data_not_obtained'
    )
    SubstrateApiNotReachable = 'substrate_network_substrate_api_not_reachable'
