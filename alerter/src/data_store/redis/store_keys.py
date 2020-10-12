# TODO: Need to be rebuilt as we go along in development. Basically, redis uses
#       hashed keys, so these are not known before. What we must keep in mind
#       is that for a chain, there must be only 1 node with the same name
#       (This was enforced in the setup but not in the config parsing).
#       Hash(Chain) -> Key(node)

# Hashes
_hash_blockchain = "hash_bc1"

# smX_<monitor_name>
_key_system_monitor_alive = "sm1"
_key_system_monitor_network_inspection_period = "sm2"
# TODO: Add the transmitted/received bytes here

# sX_<system_name>
_key_system_process_cpu_seconds_total = "s1"
_key_system_process_memory_usage = "s2"
_key_system_virtual_memory_usage = "s3"
_key_system_open_file_descriptors = "s4"
_key_system_system_cpu_usage = "s5"
_key_system_system_ram_usage = "s6"
_key_system_system_storage_usage = "s7"
# TODO: Add the network rates here


def _as_prefix(key) -> str:
    return key + "_"


class Keys:

    @staticmethod
    def get_hash_blockchain(chain_name: str) -> str:
        return _as_prefix(_hash_blockchain) + chain_name

    @staticmethod
    def get_system_monitor_alive(monitor_name: str) -> str:
        return _as_prefix(_key_system_monitor_alive) + monitor_name

    @staticmethod
    def get_system_process_cpu_seconds_total(system_name: str) -> str:
        return _as_prefix(_key_system_process_cpu_seconds_total) + system_name

    @staticmethod
    def get_system_process_memory_usage(system_name: str) -> str:
        return _as_prefix(_key_system_process_memory_usage) + system_name

    @staticmethod
    def get_system_virtual_memory_usage(system_name: str) -> str:
        return _as_prefix(_key_system_virtual_memory_usage) + system_name

    @staticmethod
    def get_system_open_file_descriptors(system_name: str) -> str:
        return _as_prefix(_key_system_open_file_descriptors) + system_name

    @staticmethod
    def get_system_system_cpu_usage(system_name: str) -> str:
        return _as_prefix(_key_system_system_cpu_usage) + system_name

    @staticmethod
    def get_system_system_ram_usage(system_name: str) -> str:
        return _as_prefix(_key_system_system_ram_usage) + system_name

    @staticmethod
    def get_system_system_storage_usage(system_name: str) -> str:
        return _as_prefix(_key_system_system_storage_usage) + system_name

    @staticmethod
    def get_system_monitor_network_inspection_period(monitor_name: str) -> str:
        return _as_prefix(_key_system_monitor_network_inspection_period) \
               + monitor_name
