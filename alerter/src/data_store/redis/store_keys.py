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

# ghX_<repo_id>
_key_github_no_of_releases = 'gh1'
_key_github_last_monitored = 'gh2'

# cX_<component_name>
_key_component_heartbeat = 'c1'

# chX_<parent_id>
_key_chain_mute_alerts = 'ch1'

# confx_<config_type>
_key_config = 'conf1'

# alertX_<origin_id>
_key_alert_open_file_descriptors = 'alert1'
_key_alert_system_cpu_usage = 'alert2'
_key_alert_system_storage_usage = 'alert3'
_key_alert_system_ram_usage = 'alert4'
_key_alert_system_is_down = 'alert5'
_key_alert_metric_not_found = 'alert6'
_key_alert_invalid_url = 'alert7'
_key_alert_github_release = 'alert8'
_key_alert_cannot_access_github = 'alert9'


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
    def get_alert_github_release(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_github_release) + origin_id

    @staticmethod
    def get_alert_cannot_access_github(origin_id: str) -> str:
        return Keys._as_prefix(_key_alert_cannot_access_github) + origin_id
