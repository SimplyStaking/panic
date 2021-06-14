from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedChainlinkNodeAlertsMetricCode(GroupedAlertsMetricCode):
    NoChangeInHeight = 'head_tacker_current_head'
    HeadsInQueueThreshold = 'head_tracker_heads_in_queue'
    NoChangeInTotalHeadersReceivedThreshold = \
        'head_tracker_heads_received_total'
    DroppedBlockHeadersThreshold = 'head_tracker_num_heads_dropped_total'
    MaxUnconfirmedBlocksThreshold = 'max_unconfirmed_blocks'
    ChangeInSourceNode = 'process_start_time_seconds'
    GasBumpIncreasedOverNodeGasPriceLimit = \
        'tx_manager_gas_bump_exceeds_limit_total'
    NoOfUnconfirmedTxsThreshold = 'unconfirmed_transactions'
    TotalErroredJobRunsThreshold = 'run_status_update_total'
    EthBalanceThreshold = 'eth_balance_amount'
    EthBalanceTopUp = 'eth_balance_amount_increase'
    InvalidUrl = 'invalid_url'
    MetricNotFound = 'metric_not_found'
    NodeIsDown = 'node_is_down'
    PrometheusSourceIsDown = 'prometheus_is_down'
