from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedCosmosNetworkAlertsMetricCode(GroupedAlertsMetricCode):
    NewProposalSubmitted = 'cosmos_network_proposals_submitted'
    ProposalConcluded = 'cosmos_network_concluded_proposals'
    NoSyncedCosmosRestSource = 'cosmos_network_no_synced_cosmos_rest_source'
    CosmosNetworkDataNotObtained = (
        'cosmos_network_cosmos_network_data_not_obtained'
    )
