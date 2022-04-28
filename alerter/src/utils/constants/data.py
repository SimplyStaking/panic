from src.alerter.grouped_alerts_metric_code.contract. \
    chainlink_contract_metric_code import (
    GroupedChainlinkContractAlertsMetricCode)
from src.alerter.grouped_alerts_metric_code.network.cosmos_network_metric_code \
    import GroupedCosmosNetworkAlertsMetricCode
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.alerter.grouped_alerts_metric_code.node.cosmos_node_metric_code \
    import GroupedCosmosNodeAlertsMetricCode

VALID_CHAINLINK_SOURCES = ['prometheus']
VALID_COSMOS_NODE_SOURCES = ['prometheus', 'cosmos_rest', 'tendermint_rpc']
VALID_COSMOS_NETWORK_SOURCES = ['cosmos_rest']
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
RAW_TO_TRANSFORMED_COSMOS_NODE_PROM_METRICS = {
    'tendermint_consensus_latest_block_height': 'current_height',
    'tendermint_consensus_validator_power': 'voting_power',
}
INT_CHAINLINK_METRICS = ['current_height',
                         'total_block_headers_received',
                         'max_pending_tx_delay', 'total_gas_bumps',
                         'total_gas_bumps_exceeds_limit',
                         'no_of_unconfirmed_txs', 'total_errored_job_runs']
INT_COSMOS_NODE_PROM_METRICS = ['current_height', 'voting_power']
EXPIRE_METRICS = [
    GroupedChainlinkNodeAlertsMetricCode.ChangeInSourceNode,
    GroupedChainlinkNodeAlertsMetricCode.GasBumpIncreasedOverNodeGasPriceLimit,
    GroupedChainlinkNodeAlertsMetricCode.EthBalanceTopUp,
    GroupedCosmosNodeAlertsMetricCode.ValidatorWasSlashed,
    GroupedCosmosNetworkAlertsMetricCode.NewProposalSubmitted,
    GroupedCosmosNetworkAlertsMetricCode.ProposalConcluded,
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
    GroupedChainlinkContractAlertsMetricCode.ErrorNoSyncedDataSources,
    GroupedCosmosNetworkAlertsMetricCode.NewProposalSubmitted,
    GroupedCosmosNetworkAlertsMetricCode.ProposalConcluded,
    GroupedCosmosNetworkAlertsMetricCode.NoSyncedCosmosRestSource,
    GroupedCosmosNetworkAlertsMetricCode.CosmosNetworkDataNotObtained,
]
