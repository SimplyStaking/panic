VALID_CHAINLINK_SOURCES = ['prometheus']
RAW_TO_TRANSFORMED_CHAINLINK_METRICS = {
    'head_tracker_current_head': 'current_height',
    'head_tracker_heads_in_queue': 'eth_blocks_in_queue',
    'head_tracker_heads_received_total': 'total_block_headers_received',
    'head_tracker_num_heads_dropped_total': 'total_block_headers_dropped',
    'job_subscriber_subscriptions': 'no_of_active_jobs',
    'max_unconfirmed_blocks': 'max_pending_tx_delay',
    'process_start_time_seconds': 'process_start_time_seconds',
    'tx_manager_num_gas_bumps_total': 'total_gas_bumps',
    'tx_manager_gas_bump_exceeds_limit_total': 'total_gas_bumps_exceeds_limit',
    'unconfirmed_transactions': 'no_of_unconfirmed_txs',
    'gas_updater_set_gas_price': 'current_gas_price_info',
    'eth_balance': 'eth_balance_info',
    'run_status_update_total': 'total_errored_job_runs',
}
INT_CHAINLINK_METRICS = ['current_height', 'eth_blocks_in_queue',
                         'total_block_headers_received',
                         'total_block_headers_dropped', 'no_of_active_jobs',
                         'max_pending_tx_delay', 'total_gas_bumps',
                         'total_gas_bumps_exceeds_limit',
                         'no_of_unconfirmed_txs', 'total_errored_job_runs']
