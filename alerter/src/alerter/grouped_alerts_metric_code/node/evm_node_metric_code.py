from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedEVMNodeAlertsMetricCode(GroupedAlertsMetricCode):
    NodeIsDown = 'evm_node_is_down'
    BlockHeightDifference = 'evm_block_syncing_block_height_difference'
    NoChangeInBlockHeight = 'evm_block_syncing_no_change_in_block_height'
    InvalidUrl = 'evm_invalid_url'
