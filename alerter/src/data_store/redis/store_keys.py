# Hashes
_hash_parent = 'hash_p1'

# Unique keys
_key_alerter_mute = "a1"

# sX_<system_id>
_key_system_process_cpu_seconds_total = 's1'
_key_system_process_memory_usage = 's2'
_key_system_virtual_memory_usage = 's3'
_key_system_open_file_descriptors = 's4'
_key_system_system_cpu_usage = 's5'
_key_system_system_ram_usage = 's6'
_key_system_system_storage_usage = 's7'
_key_system_network_transmit_bytes_per_second = 's8'
_key_system_network_receive_bytes_per_second = 's9'
_key_system_network_receive_bytes_total = 's10'
_key_system_network_transmit_bytes_total = 's11'
_key_system_disk_io_time_seconds_total = 's12'
_key_system_disk_io_time_seconds_in_interval = 's13'
_key_system_last_monitored = 's14'
_key_system_went_down_at = 's15'

# clX_<cl_node_id>
_key_cl_node_current_height = 'cl1'
_key_cl_node_total_block_headers_received = 'cl2'
_key_cl_node_max_pending_tx_delay = 'cl3'
_key_cl_node_process_start_time_seconds = 'cl4'
_key_cl_node_total_gas_bumps = 'cl5'
_key_cl_node_total_gas_bumps_exceeds_limit = 'cl6'
_key_cl_node_no_of_unconfirmed_txs = 'cl7'
_key_cl_node_total_errored_job_runs = 'cl8'
_key_cl_node_current_gas_price_info = 'cl9'
_key_cl_node_balance_info = 'cl10'
_key_cl_node_went_down_at_prometheus = 'cl11'
_key_cl_node_last_prometheus_source_used = 'cl12'
_key_cl_node_last_monitored_prometheus = 'cl13'

# evmX_<evm_node_id>
_key_evm_node_current_height = 'evm1'
_key_evm_node_went_down_at = 'evm2'
_key_evm_node_last_monitored = 'evm3'
_key_evm_node_syncing = 'evm4'

# CosmosNodeX_<cosmos_node_id>
_key_cosmos_node_current_height = 'CosmosNode1'
_key_cosmos_node_voting_power = 'CosmosNode2'
_key_cosmos_node_is_syncing = 'CosmosNode3'
_key_cosmos_node_bond_status = 'CosmosNode4'
_key_cosmos_node_jailed = 'CosmosNode5'
_key_cosmos_node_slashed = 'CosmosNode6'
_key_cosmos_node_missed_blocks = 'CosmosNode7'
_key_cosmos_node_went_down_at_prometheus = 'CosmosNode8'
_key_cosmos_node_went_down_at_cosmos_rest = 'CosmosNode9'
_key_cosmos_node_went_down_at_tendermint_rpc = 'CosmosNode10'
_key_cosmos_node_last_monitored_prometheus = 'CosmosNode11'
_key_cosmos_node_last_monitored_cosmos_rest = 'CosmosNode12'
_key_cosmos_node_last_monitored_tendermint_rpc = 'CosmosNode13'

# CosmosNetworkX_<cosmos_network_id>
_key_cosmos_network_proposals = 'CosmosNetwork1'
_key_cosmos_network_last_monitored_cosmos_rest = 'CosmosNetwork2'

# SubstrateNodeX_<substrate_node_id>
_key_substrate_node_best_height = 'SubstrateNode1'
_key_substrate_node_target_height = 'SubstrateNode2'
_key_substrate_node_finalized_height = 'SubstrateNode3'
_key_substrate_node_current_session = 'SubstrateNode4'
_key_substrate_node_current_era = 'SubstrateNode5'
_key_substrate_node_authored_blocks = 'SubstrateNode6'
_key_substrate_node_active = 'SubstrateNode7'
_key_substrate_node_elected = 'SubstrateNode8'
_key_substrate_node_disabled = 'SubstrateNode9'
_key_substrate_node_eras_stakers = 'SubstrateNode10'
_key_substrate_node_sent_heartbeat = 'SubstrateNode11'
_key_substrate_node_controller_address = 'SubstrateNode12'
_key_substrate_node_history_depth_eras = 'SubstrateNode13'
_key_substrate_node_unclaimed_rewards = 'SubstrateNode14'
_key_substrate_node_claimed_rewards = 'SubstrateNode15'
_key_substrate_node_previous_era_rewards = 'SubstrateNode16'
_key_substrate_node_historical = 'SubstrateNode17'
_key_substrate_node_token_symbol = 'SubstrateNode18'
_key_substrate_node_went_down_at_websocket = 'SubstrateNode19'
_key_substrate_node_last_monitored_websocket = 'SubstrateNode20'

# SubstrateNetworkX_<substrate_network_id>
_key_substrate_network_grandpa_stalled = 'SubstrateNetwork1'
_key_substrate_network_public_prop_count = 'SubstrateNetwork2'
_key_substrate_network_active_proposals = 'SubstrateNetwork3'
_key_substrate_network_referendum_count = 'SubstrateNetwork4'
_key_substrate_network_referendums = 'SubstrateNetwork5'
_key_substrate_network_last_monitored_websocket = 'SubstrateNetwork6'

# ChainlinkContractX_<cl_node_id>_<contract_proxy_address>
_key_cl_contract_version = 'ChainlinkContract1'
_key_cl_contract_aggregator_address = 'ChainlinkContract2'
_key_cl_contract_latest_round = 'ChainlinkContract3'
_key_cl_contract_latest_answer = 'ChainlinkContract4'
_key_cl_contract_latest_timestamp = 'ChainlinkContract5'
_key_cl_contract_answered_in_round = 'ChainlinkContract6'
_key_cl_contract_historical_rounds = 'ChainlinkContract7'
_key_cl_contract_withdrawable_payment = 'ChainlinkContract8'
_key_cl_contract_owed_payment = 'ChainlinkContract9'
_key_cl_contract_last_monitored = 'ChainlinkContract10'
_key_cl_contract_last_round_observed = 'ChainlinkContract11'

# ghX_<repo_id>
_key_github_no_of_releases = 'gh1'
_key_github_last_monitored = 'gh2'

# dhX_<repo_id>
_key_dockerhub_last_tags = 'dh1'
_key_dockerhub_last_monitored = 'dh2'

# cX_<component_name>
_key_component_heartbeat = 'c1'

# chX_<parent_id>
_key_chain_mute_alerts = 'ch1'

# alert_systemX_<origin_id>
_key_alert_system_open_file_descriptors = 'alert_system1'
_key_alert_system_cpu_usage = 'alert_system2'
_key_alert_system_storage_usage = 'alert_system3'
_key_alert_system_ram_usage = 'alert_system4'
_key_alert_system_is_down = 'alert_system5'
_key_alert_system_metric_not_found = 'alert_system6'
_key_alert_system_invalid_url = 'alert_system7'

# alert_githubX_<origin_id>
_key_alert_github_release = 'alert_github1'
_key_alert_github_cannot_access = 'alert_github2'
_key_alert_github_api_call_error = 'alert_github3'

# alert_dockerhubX_<origin_id>
_key_alert_dockerhub_new_tag = 'alert_dockerhub1'
_key_alert_dockerhub_updated_tag = 'alert_dockerhub2'
_key_alert_dockerhub_deleted_tag = 'alert_dockerhub3'
_key_alert_dockerhub_cannot_access = 'alert_dockerhub4'
_key_alert_dockerhub_tags_api_call_error = 'alert_dockerhub5'

# alert_cl_nodeX_<origin_id>
_key_alert_cl_head_tracker_current_head = 'alert_cl_node1'
_key_alert_cl_head_tracker_heads_received_total = 'alert_cl_node2'
_key_alert_cl_max_unconfirmed_blocks = 'alert_cl_node3'
_key_alert_cl_process_start_time_seconds = 'alert_cl_node4'
_key_alert_cl_tx_manager_gas_bump_exceeds_limit_total = 'alert_cl_node5'
_key_alert_cl_unconfirmed_transactions = 'alert_cl_node6'
_key_alert_cl_run_status_update_total = 'alert_cl_node7'
_key_alert_cl_balance_amount = 'alert_cl_node8'
_key_alert_cl_balance_amount_increase = 'alert_cl_node9'
_key_alert_cl_invalid_url = 'alert_cl_node10'
_key_alert_cl_metric_not_found = 'alert_cl_node11'
_key_alert_cl_node_is_down = 'alert_cl_node12'
_key_alert_cl_prometheus_is_down = 'alert_cl_node13'

# alert_cosmos_nodeX_<origin_id>
_key_alert_cosmos_node_is_down = 'alert_cosmos_node1'
_key_alert_cosmos_node_slashed = 'alert_cosmos_node2'
_key_alert_cosmos_node_syncing = 'alert_cosmos_node3'
_key_alert_cosmos_node_active = 'alert_cosmos_node4'
_key_alert_cosmos_node_jailed = 'alert_cosmos_node5'
_key_alert_cosmos_node_blocks_missed = 'alert_cosmos_node6'
_key_alert_cosmos_node_change_in_height = 'alert_cosmos_node7'
_key_alert_cosmos_node_height_difference = 'alert_cosmos_node8'
_key_alert_cosmos_node_prometheus_url_invalid = 'alert_cosmos_node9'
_key_alert_cosmos_node_cosmos_rest_url_invalid = 'alert_cosmos_node10'
_key_alert_cosmos_node_tendermint_rpc_url_invalid = 'alert_cosmos_node11'
_key_alert_cosmos_node_prometheus_is_down = 'alert_cosmos_node12'
_key_alert_cosmos_node_cosmos_rest_is_down = 'alert_cosmos_node13'
_key_alert_cosmos_node_tendermint_rpc_is_down = 'alert_cosmos_node14'
_key_alert_cosmos_node_no_synced_cosmos_rest_source = 'alert_cosmos_node15'
_key_alert_cosmos_node_no_synced_tendermint_rpc_source = 'alert_cosmos_node16'
_key_alert_cosmos_node_cosmos_rest_data_not_obtained = 'alert_cosmos_node17'
_key_alert_cosmos_node_tendermint_rpc_data_not_obtained = 'alert_cosmos_node18'
_key_alert_cosmos_node_metric_not_found = 'alert_cosmos_node19'

# alert_cosmos_networkX
_key_alert_cosmos_network_proposals_submitted = 'alert_cosmos_network1'
_key_alert_cosmos_network_concluded_proposals = 'alert_cosmos_network2'
_key_alert_cosmos_network_no_synced_cosmos_rest_source = 'alert_cosmos_network3'
_key_alert_cosmos_network_cosmos_network_data_not_obtained = (
    'alert_cosmos_network4')

# alert_cl_contractX_<cl_node_id>_<contract_proxy_address>
_key_alert_cl_contract_price_feed_not_observed = 'alert_cl_contract1'
_key_alert_cl_contract_price_feed_deviation = 'alert_cl_contract2'
_key_alert_cl_contract_consensus_failure = 'alert_cl_contract3'
# alert_cl_contractX
_key_alert_cl_contract_contracts_not_retrieved = 'alert_cl_contract4'
_key_alert_cl_contract_no_synced_data_sources = 'alert_cl_contract5'

# alert_evm_nodeX_<evm_node_id>
_key_alert_evm_node_is_down = 'alert_evm_node1'
_key_alert_evm_block_syncing_block_height_difference = 'alert_evm_node2'
_key_alert_evm_block_syncing_no_change_in_block_height = 'alert_evm_node3'
_key_alert_evm_invalid_url = 'alert_evm_node4'

# alert_substrate_nodeX_<origin_id>
_key_alert_substrate_node_is_down = 'alert_substrate_node1'
_key_alert_substrate_node_change_in_best_block_height = 'alert_substrate_node2'
_key_alert_substrate_node_change_in_finalized_block_height = (
    'alert_substrate_node3')
_key_alert_substrate_node_syncing = 'alert_substrate_node4'
_key_alert_substrate_node_active = 'alert_substrate_node5'
_key_alert_substrate_node_disabled = 'alert_substrate_node6'
_key_alert_substrate_node_elected = 'alert_substrate_node7'
_key_alert_substrate_node_bonded_amount_changed = 'alert_substrate_node8'
_key_alert_substrate_node_controller_address_change = 'alert_substrate_node9'
_key_alert_substrate_node_no_synced_substrate_websocket_source = (
    'alert_substrate_node10')
_key_alert_substrate_node_substrate_websocket_data_not_obtained = (
    'alert_substrate_node11')
_key_alert_substrate_node_substrate_api_not_reachable = 'alert_substrate_node12'
# alert_substrate_nodeX_<origin_id>_<session_id>
_key_alert_substrate_node_no_heartbeat_and_block_authored_yet = (
    'alert_substrate_node13')
# alert_substrate_nodeX_<origin_id>_<block_height>
_key_alert_substrate_node_offline = 'alert_substrate_node14'
_key_alert_substrate_node_slashed = 'alert_substrate_node15'
# alert_substrate_nodeX_<origin_id>_<era_id>
_key_alert_substrate_node_payout_not_claimed = 'alert_substrate_node16'

# alert_substrate_networkX
_key_alert_substrate_network_grandpa_stalled = 'alert_substrate_network1'
_key_alert_substrate_network_no_synced_substrate_websocket_source = (
    'alert_substrate_network2')
_key_alert_substrate_network_substrate_network_data_not_obtained = (
    'alert_substrate_network3')
_key_alert_substrate_network_substrate_api_not_reachable = (
    'alert_substrate_network4')
# alert_substrate_networkX_<proposal_id>
_key_alert_substrate_network_proposal_submitted = 'alert_substrate_network5'
# alert_substrate_networkX_<referendum_id>
_key_alert_substrate_network_referendum_info = 'alert_substrate_network6'


class Keys:

    @staticmethod
    def _as_prefix(key: str) -> str:
        return key + '_'

    @staticmethod
    def get_hash_parent(parent_id: str) -> str:
        return Keys._as_prefix(_hash_parent) + parent_id

    @staticmethod
    def get_hash_parent_raw() -> str:
        return _hash_parent

    @staticmethod
    def get_alerter_mute() -> str:
        return _key_alerter_mute

    @staticmethod
    def get_system_process_cpu_seconds_total(system_id: str) -> str:
        return Keys._as_prefix(_key_system_process_cpu_seconds_total) + (
            system_id)

    @staticmethod
    def get_system_process_memory_usage(system_id: str) -> str:
        return Keys._as_prefix(_key_system_process_memory_usage) + system_id

    @staticmethod
    def get_system_virtual_memory_usage(system_id: str) -> str:
        return Keys._as_prefix(_key_system_virtual_memory_usage) + system_id

    @staticmethod
    def get_system_open_file_descriptors(system_id: str) -> str:
        return Keys._as_prefix(_key_system_open_file_descriptors) + system_id

    @staticmethod
    def get_system_system_cpu_usage(system_id: str) -> str:
        return Keys._as_prefix(_key_system_system_cpu_usage) + system_id

    @staticmethod
    def get_system_system_ram_usage(system_id: str) -> str:
        return Keys._as_prefix(_key_system_system_ram_usage) + system_id

    @staticmethod
    def get_system_system_storage_usage(system_id: str) -> str:
        return Keys._as_prefix(_key_system_system_storage_usage) + system_id

    @staticmethod
    def get_system_network_transmit_bytes_per_second(system_id: str) -> str:
        return Keys._as_prefix(_key_system_network_transmit_bytes_per_second) \
               + system_id

    @staticmethod
    def get_system_network_receive_bytes_per_second(system_id: str) -> str:
        return Keys._as_prefix(_key_system_network_receive_bytes_per_second) + (
            system_id)

    @staticmethod
    def get_system_network_receive_bytes_total(system_id: str) -> str:
        return Keys._as_prefix(_key_system_network_receive_bytes_total) + (
            system_id)

    @staticmethod
    def get_system_network_transmit_bytes_total(system_id: str) -> str:
        return Keys._as_prefix(_key_system_network_transmit_bytes_total) + (
            system_id)

    @staticmethod
    def get_system_disk_io_time_seconds_total(system_id: str) -> str:
        return Keys._as_prefix(_key_system_disk_io_time_seconds_total) + (
            system_id)

    @staticmethod
    def get_system_disk_io_time_seconds_in_interval(
            system_id: str) -> str:
        return Keys._as_prefix(_key_system_disk_io_time_seconds_in_interval) + (
            system_id)

    @staticmethod
    def get_system_went_down_at(system_id: str) -> str:
        return Keys._as_prefix(_key_system_went_down_at) + system_id

    @staticmethod
    def get_system_last_monitored(system_id: str) -> str:
        return Keys._as_prefix(_key_system_last_monitored) + system_id

    @staticmethod
    def get_cl_node_current_height(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_current_height) + cl_node_id

    @staticmethod
    def get_cl_node_total_block_headers_received(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_block_headers_received) + (
            cl_node_id)

    @staticmethod
    def get_cl_node_max_pending_tx_delay(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_max_pending_tx_delay) + cl_node_id

    @staticmethod
    def get_cl_node_process_start_time_seconds(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_process_start_time_seconds) + (
            cl_node_id)

    @staticmethod
    def get_cl_node_total_gas_bumps(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_gas_bumps) + cl_node_id

    @staticmethod
    def get_cl_node_total_gas_bumps_exceeds_limit(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_gas_bumps_exceeds_limit) + (
            cl_node_id)

    @staticmethod
    def get_cl_node_no_of_unconfirmed_txs(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_no_of_unconfirmed_txs) + cl_node_id

    @staticmethod
    def get_cl_node_total_errored_job_runs(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_errored_job_runs) + cl_node_id

    @staticmethod
    def get_cl_node_current_gas_price_info(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_current_gas_price_info) + cl_node_id

    @staticmethod
    def get_cl_node_balance_info(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_balance_info) + cl_node_id

    @staticmethod
    def get_cl_node_went_down_at_prometheus(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_went_down_at_prometheus) + (
            cl_node_id)

    @staticmethod
    def get_cl_node_last_prometheus_source_used(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_last_prometheus_source_used) + (
            cl_node_id)

    @staticmethod
    def get_cl_node_last_monitored_prometheus(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_last_monitored_prometheus) + (
            cl_node_id)

    @staticmethod
    def get_evm_node_current_height(evm_node_id: str) -> str:
        return Keys._as_prefix(_key_evm_node_current_height) + evm_node_id

    @staticmethod
    def get_evm_node_went_down_at(evm_node_id: str) -> str:
        return Keys._as_prefix(_key_evm_node_went_down_at) + evm_node_id

    @staticmethod
    def get_evm_node_last_monitored(evm_node_id: str) -> str:
        return Keys._as_prefix(_key_evm_node_last_monitored) + evm_node_id

    @staticmethod
    def get_evm_node_syncing(evm_node_id: str) -> str:
        return Keys._as_prefix(_key_evm_node_syncing) + evm_node_id

    @staticmethod
    def get_cosmos_node_current_height(cosmos_node_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_node_current_height) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_voting_power(cosmos_node_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_node_voting_power) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_is_syncing(cosmos_node_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_node_is_syncing) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_bond_status(cosmos_node_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_node_bond_status) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_jailed(cosmos_node_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_node_jailed) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_slashed(cosmos_node_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_node_slashed) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_missed_blocks(cosmos_node_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_node_missed_blocks) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_went_down_at_prometheus(cosmos_node_id: str) -> str:
        return Keys._as_prefix(
            _key_cosmos_node_went_down_at_prometheus) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_went_down_at_cosmos_rest(cosmos_node_id: str) -> str:
        return Keys._as_prefix(
            _key_cosmos_node_went_down_at_cosmos_rest) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_went_down_at_tendermint_rpc(cosmos_node_id: str) -> str:
        return Keys._as_prefix(
            _key_cosmos_node_went_down_at_tendermint_rpc) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_last_monitored_prometheus(cosmos_node_id: str) -> str:
        return Keys._as_prefix(
            _key_cosmos_node_last_monitored_prometheus) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_last_monitored_cosmos_rest(cosmos_node_id: str) -> str:
        return Keys._as_prefix(
            _key_cosmos_node_last_monitored_cosmos_rest) + cosmos_node_id

    @staticmethod
    def get_cosmos_node_last_monitored_tendermint_rpc(
            cosmos_node_id: str) -> str:
        return Keys._as_prefix(
            _key_cosmos_node_last_monitored_tendermint_rpc) + cosmos_node_id

    @staticmethod
    def get_cosmos_network_proposals(parent_id: str) -> str:
        return Keys._as_prefix(_key_cosmos_network_proposals) + parent_id

    @staticmethod
    def get_cosmos_network_last_monitored_cosmos_rest(parent_id: str) -> str:
        return Keys._as_prefix(
            _key_cosmos_network_last_monitored_cosmos_rest) + parent_id

    @staticmethod
    def get_substrate_node_went_down_at_websocket(
            substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_went_down_at_websocket) + substrate_node_id

    @staticmethod
    def get_substrate_node_last_monitored_websocket(
            substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_last_monitored_websocket) + substrate_node_id

    @staticmethod
    def get_substrate_node_best_height(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_best_height) + substrate_node_id

    @staticmethod
    def get_substrate_node_target_height(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_target_height) + substrate_node_id

    @staticmethod
    def get_substrate_node_finalized_height(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_finalized_height) + substrate_node_id

    @staticmethod
    def get_substrate_node_current_session(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_current_session) + substrate_node_id

    @staticmethod
    def get_substrate_node_current_era(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_current_era) + substrate_node_id

    @staticmethod
    def get_substrate_node_authored_blocks(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_authored_blocks) + substrate_node_id

    @staticmethod
    def get_substrate_node_active(substrate_node_id: str) -> str:
        return Keys._as_prefix(_key_substrate_node_active) + substrate_node_id

    @staticmethod
    def get_substrate_node_elected(substrate_node_id: str) -> str:
        return Keys._as_prefix(_key_substrate_node_elected) + substrate_node_id

    @staticmethod
    def get_substrate_node_disabled(substrate_node_id: str) -> str:
        return Keys._as_prefix(_key_substrate_node_disabled) + substrate_node_id

    @staticmethod
    def get_substrate_node_eras_stakers(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_eras_stakers) + substrate_node_id

    @staticmethod
    def get_substrate_node_sent_heartbeat(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_sent_heartbeat) + substrate_node_id

    @staticmethod
    def get_substrate_node_controller_address(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_controller_address) + substrate_node_id

    @staticmethod
    def get_substrate_node_history_depth_eras(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_history_depth_eras) + substrate_node_id

    @staticmethod
    def get_substrate_node_unclaimed_rewards(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_unclaimed_rewards) + substrate_node_id

    @staticmethod
    def get_substrate_node_claimed_rewards(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_claimed_rewards) + substrate_node_id

    @staticmethod
    def get_substrate_node_previous_era_rewards(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_previous_era_rewards) + substrate_node_id

    @staticmethod
    def get_substrate_node_historical(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_historical) + substrate_node_id

    @staticmethod
    def get_substrate_node_token_symbol(substrate_node_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_node_token_symbol) + substrate_node_id

    @staticmethod
    def get_substrate_network_grandpa_stalled(parent_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_network_grandpa_stalled) + parent_id

    @staticmethod
    def get_substrate_network_public_prop_count(parent_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_network_public_prop_count) + parent_id

    @staticmethod
    def get_substrate_network_active_proposals(parent_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_network_active_proposals) + parent_id

    @staticmethod
    def get_substrate_network_referendum_count(parent_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_network_referendum_count) + parent_id

    @staticmethod
    def get_substrate_network_referendums(parent_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_network_referendums) + parent_id

    @staticmethod
    def get_substrate_network_last_monitored_websocket(parent_id: str) -> str:
        return Keys._as_prefix(
            _key_substrate_network_last_monitored_websocket) + parent_id

    @staticmethod
    def get_cl_contract_version(cl_node_id: str,
                                contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_version) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_aggregator_address(cl_node_id: str,
                                           contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_aggregator_address) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_latest_round(cl_node_id: str,
                                     contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_latest_round) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_latest_answer(cl_node_id: str,
                                      contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_latest_answer) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_latest_timestamp(cl_node_id: str,
                                         contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_latest_timestamp) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_answered_in_round(cl_node_id: str,
                                          contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_answered_in_round) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_withdrawable_payment(cl_node_id: str,
                                             contract_proxy_address: str
                                             ) -> str:
        return Keys._as_prefix(_key_cl_contract_withdrawable_payment) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_owed_payment(cl_node_id: str,
                                     contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_owed_payment) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_last_monitored(cl_node_id: str,
                                       contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_last_monitored) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_last_round_observed(
            cl_node_id: str, contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_last_round_observed) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_cl_contract_historical_rounds(cl_node_id: str,
                                          contract_proxy_address: str) -> str:
        return Keys._as_prefix(
            _key_cl_contract_historical_rounds) + Keys._as_prefix(
            cl_node_id) + contract_proxy_address

    @staticmethod
    def get_github_no_of_releases(repo_id: str) -> str:
        return Keys._as_prefix(_key_github_no_of_releases) + repo_id

    @staticmethod
    def get_github_last_monitored(repo_id: str) -> str:
        return Keys._as_prefix(_key_github_last_monitored) + repo_id

    @staticmethod
    def get_dockerhub_last_tags(repo_id: str) -> str:
        return Keys._as_prefix(_key_dockerhub_last_tags) + repo_id

    @staticmethod
    def get_dockerhub_last_monitored(repo_id: str) -> str:
        return Keys._as_prefix(_key_dockerhub_last_monitored) + repo_id

    @staticmethod
    def get_component_heartbeat(component_name: str) -> str:
        return Keys._as_prefix(_key_component_heartbeat) + component_name

    @staticmethod
    def get_chain_mute_alerts() -> str:
        return _key_chain_mute_alerts

    @staticmethod
    def get_alert_system_open_file_descriptors(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_system_open_file_descriptors) + (
            origin_id)

    @staticmethod
    def get_alert_system_cpu_usage(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_system_cpu_usage) + origin_id

    @staticmethod
    def get_alert_system_storage_usage(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_system_storage_usage) + origin_id

    @staticmethod
    def get_alert_system_ram_usage(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_system_ram_usage) + origin_id

    @staticmethod
    def get_alert_system_is_down(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_system_is_down) + origin_id

    @staticmethod
    def get_alert_system_invalid_url(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_system_invalid_url) + origin_id

    @staticmethod
    def get_alert_system_metric_not_found(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_system_metric_not_found) + origin_id

    @staticmethod
    def get_alert_github_release(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_github_release) + origin_id

    @staticmethod
    def get_alert_github_cannot_access(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_github_cannot_access) + origin_id

    @staticmethod
    def get_alert_github_api_call_error(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_github_api_call_error) + origin_id

    @staticmethod
    def get_alert_dockerhub_new_tag(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_dockerhub_new_tag) + origin_id

    @staticmethod
    def get_alert_dockerhub_updated_tag(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_dockerhub_updated_tag) + origin_id

    @staticmethod
    def get_alert_dockerhub_deleted_tag(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_dockerhub_deleted_tag) + origin_id

    @staticmethod
    def get_alert_dockerhub_cannot_access(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_dockerhub_cannot_access) + origin_id

    @staticmethod
    def get_alert_dockerhub_tags_api_call_error(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_dockerhub_tags_api_call_error) + origin_id

    @staticmethod
    def get_alert_cl_prometheus_is_down(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_prometheus_is_down) + origin_id

    @staticmethod
    def get_alert_cl_node_is_down(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_node_is_down) + origin_id

    @staticmethod
    def get_alert_cl_metric_not_found(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_metric_not_found) + origin_id

    @staticmethod
    def get_alert_cl_invalid_url(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_invalid_url) + origin_id

    @staticmethod
    def get_alert_cl_balance_amount_increase(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_balance_amount_increase) + origin_id

    @staticmethod
    def get_alert_cl_balance_amount(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_balance_amount) + origin_id

    @staticmethod
    def get_alert_cl_run_status_update_total(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_run_status_update_total) + origin_id

    @staticmethod
    def get_alert_cl_unconfirmed_transactions(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_unconfirmed_transactions) + origin_id

    @staticmethod
    def get_alert_cl_tx_manager_gas_bump_exceeds_limit_total(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_tx_manager_gas_bump_exceeds_limit_total) + origin_id

    @staticmethod
    def get_alert_cl_process_start_time_seconds(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_process_start_time_seconds) + origin_id

    @staticmethod
    def get_alert_cl_max_unconfirmed_blocks(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_max_unconfirmed_blocks) + origin_id

    @staticmethod
    def get_alert_cl_head_tracker_heads_received_total(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_head_tracker_heads_received_total) + origin_id

    @staticmethod
    def get_alert_cl_head_tracker_current_head(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_head_tracker_current_head) + origin_id

    @staticmethod
    def get_alert_cosmos_node_is_down(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_is_down) + origin_id

    @staticmethod
    def get_alert_cosmos_node_slashed(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_slashed) + origin_id

    @staticmethod
    def get_alert_cosmos_node_syncing(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_syncing) + origin_id

    @staticmethod
    def get_alert_cosmos_node_active(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_active) + origin_id

    @staticmethod
    def get_alert_cosmos_node_jailed(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_jailed) + origin_id

    @staticmethod
    def get_alert_cosmos_node_blocks_missed(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_blocks_missed) + origin_id

    @staticmethod
    def get_alert_cosmos_node_change_in_height(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_change_in_height) + origin_id

    @staticmethod
    def get_alert_cosmos_node_height_difference(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_height_difference) + origin_id

    @staticmethod
    def get_alert_cosmos_node_prometheus_url_invalid(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_prometheus_url_invalid) + origin_id

    @staticmethod
    def get_alert_cosmos_node_cosmos_rest_url_invalid(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_cosmos_rest_url_invalid) + origin_id

    @staticmethod
    def get_alert_cosmos_node_tendermint_rpc_url_invalid(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_tendermint_rpc_url_invalid
        ) + origin_id

    @staticmethod
    def get_alert_cosmos_node_prometheus_is_down(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_prometheus_is_down) + origin_id

    @staticmethod
    def get_alert_cosmos_node_cosmos_rest_is_down(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_cosmos_rest_is_down) + origin_id

    @staticmethod
    def get_alert_cosmos_node_tendermint_rpc_is_down(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_tendermint_rpc_is_down) + origin_id

    @staticmethod
    def get_alert_cosmos_node_no_synced_cosmos_rest_source(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_no_synced_cosmos_rest_source) + origin_id

    @staticmethod
    def get_alert_cosmos_node_no_synced_tendermint_rpc_source(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_no_synced_tendermint_rpc_source) + origin_id

    @staticmethod
    def get_alert_cosmos_node_cosmos_rest_data_not_obtained(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_cosmos_rest_data_not_obtained) + origin_id

    @staticmethod
    def get_alert_cosmos_node_tendermint_rpc_data_not_obtained(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_tendermint_rpc_data_not_obtained) + origin_id

    @staticmethod
    def get_alert_cosmos_node_metric_not_found(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cosmos_node_metric_not_found) + origin_id

    @staticmethod
    def get_alert_cosmos_network_proposals_submitted() -> str:
        return _key_alert_cosmos_network_proposals_submitted

    @staticmethod
    def get_alert_cosmos_network_concluded_proposals() -> str:
        return _key_alert_cosmos_network_concluded_proposals

    @staticmethod
    def get_alert_cosmos_network_no_synced_cosmos_rest_source() -> str:
        return _key_alert_cosmos_network_no_synced_cosmos_rest_source

    @staticmethod
    def get_alert_cosmos_network_cosmos_network_data_not_obtained() -> str:
        return _key_alert_cosmos_network_cosmos_network_data_not_obtained

    @staticmethod
    def get_alert_cl_contract_price_feed_not_observed(
            cl_node_id: str, contract_proxy_address: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_contract_price_feed_not_observed) + (
                       Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_alert_cl_contract_price_feed_deviation(
            cl_node_id: str, contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_alert_cl_contract_price_feed_deviation) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_alert_cl_contract_consensus_failure(
            cl_node_id: str, contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_alert_cl_contract_consensus_failure) + (
                Keys._as_prefix(cl_node_id) + contract_proxy_address)

    @staticmethod
    def get_alert_cl_contract_contracts_not_retrieved() -> str:
        return _key_alert_cl_contract_contracts_not_retrieved

    @staticmethod
    def get_alert_cl_contract_no_synced_data_sources() -> str:
        return _key_alert_cl_contract_no_synced_data_sources

    @staticmethod
    def get_alert_evm_node_is_down(evm_node_id: str) -> str:
        return Keys._as_prefix(_key_alert_evm_node_is_down) + evm_node_id

    @staticmethod
    def get_alert_evm_block_syncing_block_height_difference(
            evm_node_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_evm_block_syncing_block_height_difference) + evm_node_id

    @staticmethod
    def get_alert_evm_block_syncing_no_change_in_block_height(
            evm_node_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_evm_block_syncing_no_change_in_block_height
        ) + evm_node_id

    @staticmethod
    def get_alert_evm_invalid_url(
            evm_node_id: str) -> str:
        return Keys._as_prefix(_key_alert_evm_invalid_url) + evm_node_id

    @staticmethod
    def get_alert_substrate_node_is_down(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_substrate_node_is_down) + origin_id

    @staticmethod
    def get_alert_substrate_node_change_in_best_block_height(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_change_in_best_block_height) + origin_id

    @staticmethod
    def get_alert_substrate_node_change_in_finalized_block_height(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_change_in_finalized_block_height
        ) + origin_id

    @staticmethod
    def get_alert_substrate_node_syncing(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_substrate_node_syncing) + origin_id

    @staticmethod
    def get_alert_substrate_node_active(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_substrate_node_active) + origin_id

    @staticmethod
    def get_alert_substrate_node_disabled(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_substrate_node_disabled) + origin_id

    @staticmethod
    def get_alert_substrate_node_elected(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_substrate_node_elected) + origin_id

    @staticmethod
    def get_alert_substrate_node_bonded_amount_changed(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_bonded_amount_changed) + origin_id

    @staticmethod
    def get_alert_substrate_node_controller_address_change(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_controller_address_change) + origin_id

    @staticmethod
    def get_alert_substrate_node_no_synced_substrate_websocket_source(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_no_synced_substrate_websocket_source
        ) + origin_id

    @staticmethod
    def get_alert_substrate_node_substrate_websocket_data_not_obtained(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_substrate_websocket_data_not_obtained
        ) + origin_id

    @staticmethod
    def get_alert_substrate_node_substrate_api_not_reachable(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_substrate_api_not_reachable) + origin_id

    @staticmethod
    def get_alert_substrate_node_no_heartbeat_and_block_authored_yet(
            origin_id: str, session_id: int) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_no_heartbeat_and_block_authored_yet
        ) + Keys._as_prefix(origin_id) + str(session_id)

    @staticmethod
    def get_alert_substrate_node_offline(origin_id: str,
                                         block_height: int) -> str:
        return (Keys._as_prefix(_key_alert_substrate_node_offline) +
                Keys._as_prefix(origin_id) + str(block_height))

    @staticmethod
    def get_alert_substrate_node_slashed(origin_id: str,
                                         block_height: int) -> str:
        return (Keys._as_prefix(_key_alert_substrate_node_slashed) +
                Keys._as_prefix(origin_id) + str(block_height))

    @staticmethod
    def get_alert_substrate_node_payout_not_claimed(origin_id: str,
                                                    era_id: int) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_node_payout_not_claimed) + Keys._as_prefix(
            origin_id) + str(era_id)

    @staticmethod
    def get_alert_substrate_network_grandpa_stalled() -> str:
        return _key_alert_substrate_network_grandpa_stalled

    @staticmethod
    def get_alert_substrate_network_no_synced_substrate_websocket_source(
    ) -> str:
        return _key_alert_substrate_network_no_synced_substrate_websocket_source

    @staticmethod
    def get_alert_substrate_network_substrate_network_data_not_obtained(
    ) -> str:
        return _key_alert_substrate_network_substrate_network_data_not_obtained

    @staticmethod
    def get_alert_substrate_network_substrate_api_not_reachable() -> str:
        return _key_alert_substrate_network_substrate_api_not_reachable

    @staticmethod
    def get_alert_substrate_network_proposal_submitted(proposal_id: int) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_network_proposal_submitted) + str(proposal_id)

    @staticmethod
    def get_alert_substrate_network_referendum_info(referendum_id: int) -> str:
        return Keys._as_prefix(
            _key_alert_substrate_network_referendum_info) + str(referendum_id)
