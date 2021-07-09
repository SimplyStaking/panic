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
_key_cl_node_eth_blocks_in_queue = 'cl2'
_key_cl_node_total_block_headers_received = 'cl3'
_key_cl_node_total_block_headers_dropped = 'cl4'
_key_cl_node_no_of_active_jobs = 'cl5'
_key_cl_node_max_pending_tx_delay = 'cl6'
_key_cl_node_process_start_time_seconds = 'cl7'
_key_cl_node_total_gas_bumps = 'cl8'
_key_cl_node_total_gas_bumps_exceeds_limit = 'cl9'
_key_cl_node_no_of_unconfirmed_txs = 'cl10'
_key_cl_node_total_errored_job_runs = 'cl11'
_key_cl_node_current_gas_price_info = 'cl12'
_key_cl_node_eth_balance_info = 'cl13'
_key_cl_node_went_down_at_prometheus = 'cl14'
_key_cl_node_last_prometheus_source_used = 'cl15'
_key_cl_node_last_monitored_prometheus = 'cl16'

# ghX_<repo_id>
_key_github_no_of_releases = 'gh1'
_key_github_last_monitored = 'gh2'

# cX_<component_name>
_key_component_heartbeat = 'c1'

# chX_<parent_id>
_key_chain_mute_alerts = 'ch1'

# confx_<config_type>
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
_key_alert_cl_head_tracker_heads_in_queue = 'alert_cl_node2'
_key_alert_cl_head_tracker_heads_received_total = 'alert_cl_node3'
_key_alert_cl_head_tracker_num_heads_dropped_total = 'alert_cl_node4'
_key_alert_cl_max_unconfirmed_blocks = 'alert_cl_node5'
_key_alert_cl_process_start_time_seconds = 'alert_cl_node6'
_key_alert_cl_tx_manager_gas_bump_exceeds_limit_total = 'alert_cl_node7'
_key_alert_cl_unconfirmed_transactions = 'alert_cl_node8'
_key_alert_cl_run_status_update_total = 'alert_cl_node9'
_key_alert_cl_eth_balance_amount = 'alert_cl_node10'
_key_alert_cl_eth_balance_amount_increase = 'alert_cl_node11'
_key_alert_cl_invalid_url = 'alert_cl_node12'
_key_alert_cl_metric_not_found = 'alert_cl_node13'
_key_alert_cl_node_is_down = 'alert_cl_node14'
_key_alert_cl_prometheus_is_down = 'alert_cl_node15'


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
    def get_cl_node_eth_blocks_in_queue(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_eth_blocks_in_queue) + cl_node_id

    @staticmethod
    def get_cl_node_total_block_headers_received(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_block_headers_received) \
               + cl_node_id

    @staticmethod
    def get_cl_node_total_block_headers_dropped(cl_node_id: str) -> str:
        return Keys._as_prefix(_key_cl_node_total_block_headers_dropped) \
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
    def get_config(config_type: str) -> str:
        return Keys._as_prefix(_key_config) + config_type

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
    def get_alert_cl_head_tracker_num_heads_dropped_total(
            origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_head_tracker_num_heads_dropped_total) + origin_id

    @staticmethod
    def get_alert_cl_head_tracker_heads_received_total(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_head_tracker_heads_received_total) + origin_id

    @staticmethod
    def get_alert_cl_head_tracker_heads_in_queue(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_head_tracker_heads_in_queue) + origin_id

    @staticmethod
    def get_alert_cl_head_tacker_current_head(origin_id: str) -> str:
        return Keys._as_prefix(
            _key_alert_cl_head_tacker_current_head) + origin_id

    @staticmethod
    def get_base_chain_monitorables_info(base_chain: str) -> str:
        return Keys._as_prefix(_key_base_chain_monitorables_info) + base_chain
