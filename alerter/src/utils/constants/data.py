from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code import (
        GroupedChainlinkContractAlertsMetricCode
    )
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode

VALID_CHAINLINK_SOURCES = ['prometheus']
RAW_TO_TRANSFORMED_CHAINLINK_METRICS = {
    'head_tracker_current_head': 'current_height',
    'head_tracker_heads_received_total': 'total_block_headers_received',
    'max_unconfirmed_blocks': 'max_pending_tx_delay',
    'process_start_time_seconds': 'process_start_time_seconds',
    'tx_manager_num_gas_bumps_total': 'total_gas_bumps',
    'tx_manager_gas_bump_exceeds_limit_total': 'total_gas_bumps_exceeds_limit',
    'unconfirmed_transactions': 'no_of_unconfirmed_txs',
    'gas_updater_set_gas_price': 'current_gas_price_info',
    'eth_balance': 'eth_balance_info',
    'run_status_update_total_errors': 'total_errored_job_runs',
}
INT_CHAINLINK_METRICS = ['current_height',
                         'total_block_headers_received',
                         'max_pending_tx_delay', 'total_gas_bumps',
                         'total_gas_bumps_exceeds_limit',
                         'no_of_unconfirmed_txs', 'total_errored_job_runs']
EXPIRE_METRICS = [
    GroupedChainlinkNodeAlertsMetricCode.ChangeInSourceNode,
    GroupedChainlinkNodeAlertsMetricCode.GasBumpIncreasedOverNodeGasPriceLimit,
    GroupedChainlinkNodeAlertsMetricCode.EthBalanceTopUp
]
CHAINLINK_CONTRACT_METRICS_TO_STORE = [
    GroupedChainlinkContractAlertsMetricCode.PriceFeedNotObserved,
    GroupedChainlinkContractAlertsMetricCode.PriceFeedDeviation,
    GroupedChainlinkContractAlertsMetricCode.ConsensusFailure,
    GroupedChainlinkContractAlertsMetricCode.ErrorContractsNotRetrieved,
    GroupedChainlinkContractAlertsMetricCode.ErrorNoSyncedDataSources
]
CHAIN_SOURCED_METRICS = [
    GroupedChainlinkContractAlertsMetricCode.ErrorContractsNotRetrieved,
    GroupedChainlinkContractAlertsMetricCode.ErrorNoSyncedDataSources
]
