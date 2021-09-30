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
_key_cl_node_no_of_active_jobs = 'cl3'
_key_cl_node_max_pending_tx_delay = 'cl4'
_key_cl_node_process_start_time_seconds = 'cl5'
_key_cl_node_total_gas_bumps = 'cl6'
_key_cl_node_total_gas_bumps_exceeds_limit = 'cl7'
_key_cl_node_no_of_unconfirmed_txs = 'cl8'
_key_cl_node_total_errored_job_runs = 'cl9'
_key_cl_node_current_gas_price_info = 'cl10'
_key_cl_node_eth_balance_info = 'cl11'
_key_cl_node_went_down_at_prometheus = 'cl12'
_key_cl_node_last_prometheus_source_used = 'cl13'
_key_cl_node_last_monitored_prometheus = 'cl14'

# evmX_<evm_node_id>
_key_evm_node_current_height = 'evm1'
_key_evm_node_went_down_at = 'evm2'
_key_evm_node_last_monitored = 'evm3'

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

# ghX_<repo_id>
_key_github_no_of_releases = 'gh1'
_key_github_last_monitored = 'gh2'

# cX_<component_name>
_key_component_heartbeat = 'c1'

# chX_<parent_id>
_key_chain_mute_alerts = 'ch1'

# confx_<routing_key>
_key_config = 'conf1'

# bcX_<base_chain>
_key_base_chain_monitorables_info = 'bc1'

# alert_systemX_<origin_id>
_key_alert_open_file_descriptors = 'alert_system1'
_key_alert_system_cpu_usage = 'alert_system2'
_key_alert_system_storage_usage = 'alert_system3'
_key_alert_system_ram_usage = 'alert_system4'
_key_alert_system_is_down = 'alert_system5'
_key_alert_metric_not_found = 'alert_system6'
_key_alert_invalid_url = 'alert_system7'

# alert_githubX_<origin_id>
_key_alert_github_release = 'alert_github1'
_key_alert_cannot_access_github = 'alert_github2'

# alert_cl_nodeX_<origin_id>
_key_alert_cl_head_tacker_current_head = 'alert_cl_node1'
_key_alert_cl_head_tracker_heads_received_total = 'alert_cl_node2'
_key_alert_cl_max_unconfirmed_blocks = 'alert_cl_node3'
_key_alert_cl_process_start_time_seconds = 'alert_cl_node4'
_key_alert_cl_tx_manager_gas_bump_exceeds_limit_total = 'alert_cl_node5'
_key_alert_cl_unconfirmed_transactions = 'alert_cl_node6'
_key_alert_cl_run_status_update_total = 'alert_cl_node7'
_key_alert_cl_eth_balance_amount = 'alert_cl_node8'
_key_alert_cl_eth_balance_amount_increase = 'alert_cl_node9'
_key_alert_cl_invalid_url = 'alert_cl_node10'
_key_alert_cl_metric_not_found = 'alert_cl_node11'
_key_alert_cl_node_is_down = 'alert_cl_node12'
_key_alert_cl_prometheus_is_down = 'alert_cl_node13'

# alert_cl_contractX_<cl_node_id>_<contract_proxy_address>
_key_alert_cl_contract_price_feed_not_observed = 'alert_cl_contract1'
_key_alert_cl_contract_price_feed_deviation = 'alert_cl_contract2'
_key_alert_cl_contract_consensus_failure = 'alert_cl_contract3'

# alert_evm_nodeX_<evm_node_id>
_key_alert_evm_node_is_down = 'alert_evm_node1'
_key_alert_evm_block_syncing_block_height_difference = 'alert_evm_node2'
_key_alert_evm_block_syncing_no_change_in_block_height = 'alert_evm_node3'
_key_alert_evm_invalid_url = 'alert_evm_node4'


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
        return Keys._as_prefix(_key_system_process_cpu_seconds_total) \
            + system_id

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
        return Keys._as_prefix(_key_system_network_receive_bytes_per_second) \
            + system_id

    @staticmethod
    def get_system_network_receive_bytes_total(system_id: str) -> str:
        return Keys._as_prefix(_key_system_network_receive_bytes_total) \
            + system_id

    @staticmethod
    def get_system_network_transmit_bytes_total(system_id: str) -> str:
        return Keys._as_prefix(_key_system_network_transmit_bytes_total) \
            + system_id

    @staticmethod
    def get_system_disk_io_time_seconds_total(system_id: str) -> str:
        return Keys._as_prefix(_key_system_disk_io_time_seconds_total) \
            + system_id

    @staticmethod
    def get_system_disk_io_time_seconds_in_interval(
            system_id: str) -> str:
        return Keys._as_prefix(_key_system_disk_io_time_seconds_in_interval) \
            + system_id

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
        return Keys._as_prefix(_key_cl_node_total_block_headers_received) \
            + cl_node_id

    @staticmethod
    def get_cl_node_no_of_active_jobs(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_no_of_active_jobs) + cl_node_id

    @staticmethod
    def get_cl_node_max_pending_tx_delay(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_max_pending_tx_delay) + cl_node_id

    @staticmethod
    def get_cl_node_process_start_time_seconds(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_process_start_time_seconds) \
            + cl_node_id

    @staticmethod
    def get_cl_node_total_gas_bumps(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_gas_bumps) + cl_node_id

    @staticmethod
    def get_cl_node_total_gas_bumps_exceeds_limit(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_gas_bumps_exceeds_limit) \
            + cl_node_id

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
    def get_cl_node_eth_balance_info(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_eth_balance_info) + cl_node_id

    @staticmethod
    def get_cl_node_went_down_at_prometheus(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_went_down_at_prometheus) + \
            cl_node_id

    @staticmethod
    def get_cl_node_last_prometheus_source_used(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_last_prometheus_source_used) \
            + cl_node_id

    @staticmethod
    def get_cl_node_last_monitored_prometheus(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_last_monitored_prometheus) \
            + cl_node_id

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
    def get_cl_contract_version(cl_node_id: str,
                                contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_version) + Keys._as_prefix(
            cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_aggregator_address(cl_node_id: str,
                                           contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_aggregator_address) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_latest_round(cl_node_id: str,
                                     contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_latest_round) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_latest_answer(cl_node_id: str,
                                      contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_latest_answer) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_latest_timestamp(cl_node_id: str,
                                         contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_latest_timestamp) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_answered_in_round(cl_node_id: str,
                                          contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_answered_in_round) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_withdrawable_payment(cl_node_id: str,
                                             contract_proxy_address: str
                                             ) -> str:
        return Keys._as_prefix(_key_cl_contract_withdrawable_payment) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_owed_payment(cl_node_id: str,
                                     contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_owed_payment) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_cl_contract_last_monitored(cl_node_id: str,
                                       contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_cl_contract_last_monitored) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

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
    def get_component_heartbeat(component_name: str) -> str:
        return Keys._as_prefix(_key_component_heartbeat) + component_name

    @staticmethod
    def get_chain_mute_alerts() -> str:
        return _key_chain_mute_alerts

    @staticmethod
    def get_config(routing_key: str) -> str:
        return Keys._as_prefix(_key_config) + routing_key

    @staticmethod
    def get_alert_open_file_descriptors(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_open_file_descriptors) + origin_id

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
    def get_alert_invalid_url(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_invalid_url) + origin_id

    @staticmethod
    def get_alert_metric_not_found(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_metric_not_found) + origin_id

    @staticmethod
    def get_alert_github_release(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_github_release) + origin_id

    @staticmethod
    def get_alert_cannot_access_github(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cannot_access_github) + origin_id

    @staticmethod
    def get_key_alert_cl_prometheus_is_down(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_prometheus_is_down) + origin_id

    @staticmethod
    def get_alert_cl_node_is_down(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_node_is_down) + origin_id

    @staticmethod
    def get_key_alert_cl_metric_not_found(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_metric_not_found) + origin_id

    @staticmethod
    def get_key_alert_cl_invalid_url(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_invalid_url) + origin_id

    @staticmethod
    def get_key_alert_cl_eth_balance_amount_increase(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_eth_balance_amount_increase) + origin_id

    @staticmethod
    def get_key_alert_cl_eth_balance_amount(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cl_eth_balance_amount) + origin_id

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
    def get_alert_cl_head_tacker_current_head(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_head_tacker_current_head) + origin_id

    @staticmethod
    def get_alert_cl_contract_price_feed_not_observed(
            cl_node_id: str, contract_proxy_address: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_contract_price_feed_not_observed) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_alert_cl_contract_price_feed_deviation(
            cl_node_id: str, contract_proxy_address: str) -> str:
        return Keys._as_prefix(_key_alert_cl_contract_price_feed_deviation) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_alert_cl_contract_consensus_failure(
            cl_node_id: str, contract_proxy_address: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_contract_consensus_failure) + \
            Keys._as_prefix(cl_node_id) + contract_proxy_address

    @staticmethod
    def get_alert_evm_evm_node_is_down(evm_node_id: str) -> str:
        return Keys._as_prefix(_key_alert_evm_node_is_down) + evm_node_id

    @staticmethod
    def get_alert_evm_evm_block_syncing_block_height_difference(
            evm_node_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_evm_block_syncing_block_height_difference) + evm_node_id

    @staticmethod
    def get_alert_evm_evm_block_syncing_no_change_in_block_height(
            evm_node_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_evm_block_syncing_no_change_in_block_height) + \
            evm_node_id

    @staticmethod
    def get_alert_evm_evm_invalid_url(
            evm_node_id: str) -> str:
        return Keys._as_prefix(_key_alert_evm_invalid_url) + evm_node_id

    @staticmethod
    def get_base_chain_monitorables_info(base_chain: str) -> str:
        return Keys._as_prefix(_key_base_chain_monitorables_info) + base_chain
