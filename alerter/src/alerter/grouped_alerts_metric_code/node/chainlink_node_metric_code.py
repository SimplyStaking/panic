from ..grouped_alerts_metric_code import GroupedAlertsMetricCode


class GroupedChainlinkNodeAlertsMetricCode(GroupedAlertsMetricCode):
    NoChangeInHeight = 'cl_head_tracker_current_head'
    NoChangeInTotalHeadersReceived = 'cl_head_tracker_heads_received_total'
    MaxUnconfirmedBlocksThreshold = 'cl_max_unconfirmed_blocks'
    ChangeInSourceNode = 'cl_process_start_time_seconds'
    GasBumpIncreasedOverNodeGasPriceLimit = (
        'cl_tx_manager_gas_bump_exceeds_limit_total')
    NoOfUnconfirmedTxsThreshold = 'cl_unconfirmed_transactions'
    TotalErroredJobRunsThreshold = 'cl_run_status_update_total'
    BalanceThreshold = 'cl_balance_amount'
    BalanceTopUp = 'cl_balance_amount_increase'
    InvalidUrl = 'cl_invalid_url'
    MetricNotFound = 'cl_metric_not_found'
    NodeIsDown = 'cl_node_is_down'
    PrometheusSourceIsDown = 'cl_prometheus_is_down'
