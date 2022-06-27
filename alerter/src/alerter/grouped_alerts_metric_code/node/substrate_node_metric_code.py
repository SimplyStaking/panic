from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedSubstrateNodeAlertsMetricCode(GroupedAlertsMetricCode):
    NodeIsDown = 'substrate_node_is_down'
    NoChangeInBestBlockHeight = 'substrate_node_change_in_best_block_height'
    NoChangeInFinalizedBlockHeight = (
        'substrate_node_change_in_finalized_block_height'
    )
    NodeIsSyncing = 'substrate_node_syncing'
    ValidatorIsNotActive = 'substrate_node_active'
    ValidatorIsDisabled = 'substrate_node_disabled'
    ValidatorWasNotElected = 'substrate_node_elected'
    ValidatorBondedAmountChanged = 'substrate_node_bonded_amount_changed'
    ValidatorNoHeartbeatAndBlockAuthoredYetAlert = (
        'substrate_node_no_heartbeat_and_block_authored_yet'
    )
    ValidatorWasOffline = 'substrate_node_offline'
    ValidatorWasSlashed = 'substrate_node_slashed'
    ValidatorPayoutNotClaimed = 'substrate_node_payout_not_claimed'
    ValidatorControllerAddressChanged = (
        'substrate_node_controller_address_change'
    )
    NoSyncedSubstrateWebSocketSource = (
        'substrate_node_no_synced_substrate_websocket_source'
    )
    SubstrateWebSocketDataNotObtained = (
        'substrate_node_substrate_websocket_data_not_obtained'
    )
    SubstrateApiNotReachable = 'substrate_node_substrate_api_not_reachable'
