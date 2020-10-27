# TODO: Need to be rebuilt as we go along in development. Basically, redis uses
#       hashed keys, so these are not known before. What we must keep in mind
#       is that for a chain, there must be only 1 node with the same name
#       (This was enforced in the setup but not in the config parsing).
#       Hash(Chain) -> Key(node)

# Hashes
_hash_parent = "hash_p1"

# smX_<monitor_name>
_key_system_monitor_last_monitoring_round = "sm1"

# sX_<system_id>
_key_system_process_cpu_seconds_total = "s1"
_key_system_process_memory_usage = "s2"
_key_system_virtual_memory_usage = "s3"
_key_system_open_file_descriptors = "s4"
_key_system_system_cpu_usage = "s5"
_key_system_system_ram_usage = "s6"
_key_system_system_storage_usage = "s7"
_key_system_network_transmit_bytes_per_second = "s8"
_key_system_network_receive_bytes_per_second = "s9"
_key_system_network_receive_bytes_total = "s10"
_key_system_network_transmit_bytes_total = "s11"
_key_system_disk_io_time_seconds_total = "s12"
_key_system_disk_io_time_seconds_in_interval = "s13"

# gmX_<monitor_name>
_key_github_monitor_last_monitoring_round = "gm1"

# ghX_<repo_id>
_key_github_release_name = "gh1"
_key_github_tag_name = "gh2"

def _as_prefix(key) -> str:
    return key + "_"

class Keys:

    @staticmethod
    def get_hash_parent(parent_id: str) -> str:
        return _as_prefix(_hash_parent) + parent_id

    @staticmethod
    def get_system_monitor_last_monitoring_round(monitor_name: str) -> str:
        return _as_prefix(_key_system_monitor_last_monitoring_round) \
              + monitor_name

    @staticmethod
    def get_github_monitor_last_monitoring_round(monitor_name: str) -> str:
        return _as_prefix(_key_github_monitor_last_monitoring_round) \
              + monitor_name

    @staticmethod
    def get_system_process_cpu_seconds_total(system_id: str) -> str:
        return _as_prefix(_key_system_process_cpu_seconds_total) + system_id

    @staticmethod
    def get_system_process_memory_usage(system_id: str) -> str:
        return _as_prefix(_key_system_process_memory_usage) + system_id

    @staticmethod
    def get_system_virtual_memory_usage(system_id: str) -> str:
        return _as_prefix(_key_system_virtual_memory_usage) + system_id

    @staticmethod
    def get_system_open_file_descriptors(system_id: str) -> str:
        return _as_prefix(_key_system_open_file_descriptors) + system_id

    @staticmethod
    def get_system_system_cpu_usage(system_id: str) -> str:
        return _as_prefix(_key_system_system_cpu_usage) + system_id

    @staticmethod
    def get_system_system_ram_usage(system_id: str) -> str:
        return _as_prefix(_key_system_system_ram_usage) + system_id

    @staticmethod
    def get_system_system_storage_usage(system_id: str) -> str:
        return _as_prefix(_key_system_system_storage_usage) + system_id

    @staticmethod
    def get_system_network_transmit_bytes_per_second(system_id: str) -> str:
        return _as_prefix(_key_system_network_transmit_bytes_per_second) \
              + system_id

    @staticmethod
    def get_system_network_receive_bytes_per_second(system_id: str) -> str:
        return _as_prefix(_key_system_network_receive_bytes_per_second) \
              + system_id

    @staticmethod
    def get_system_network_receive_bytes_total(system_id: str) -> str:
        return _as_prefix(_key_system_network_receive_bytes_total) \
              + system_id

    @staticmethod
    def get_system_network_transmit_bytes_total(system_id: str) -> str:
        return _as_prefix(_key_system_network_transmit_bytes_total) \
              + system_id

    @staticmethod
    def get_system_disk_io_time_seconds_total(system_id: str) -> str:
        return _as_prefix(_key_system_disk_io_time_seconds_total) \
              + system_id

    @staticmethod
    def get_system_disk_io_time_seconds_total_in_interval(
            system_id: str) -> str:
        return _as_prefix(_key_system_disk_io_time_seconds_in_interval) \
              + system_id

    @staticmethod
    def get_github_release_name(repo_id: str) -> str:
        return _as_prefix(_key_github_release_name) + repo_id

    @staticmethod
    def get_github_tag_name(repo_id: str) -> str:
        return _as_prefix(_key_github_tag_name) + repo_id