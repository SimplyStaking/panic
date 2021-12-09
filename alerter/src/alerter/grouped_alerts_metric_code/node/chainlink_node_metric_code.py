from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedChainlinkNodeAlertsMetricCode(GroupedAlertsMetricCode):
    NoChangeInHeight = 'head_tracker_current_head'
    NoChangeInTotalHeadersReceived = 'head_tracker_heads_received_total'
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
