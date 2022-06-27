# These functions assume that config files are given as parameters

from datetime import timedelta
from typing import Dict, List

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.configs.nodes.cosmos import CosmosNodeConfig
from src.configs.nodes.evm import EVMNodeConfig
from src.configs.nodes.substrate import SubstrateNodeConfig
from src.utils.types import convert_to_float, str_to_bool


def get_newly_added_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    new_keys_set = set(new_config_file.keys())
    current_keys_set = set(current_config_file.keys())
    added_keys_set = new_keys_set.difference(current_keys_set)
    return {key: new_config_file[key] for key in added_keys_set}


def get_removed_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    new_keys_set = set(new_config_file.keys())
    current_keys_set = set(current_config_file.keys())
    removed_keys_set = current_keys_set.difference(new_keys_set)
    return {key: current_config_file[key] for key in removed_keys_set}


# This function assumes that the configs obey the config schemas, and that
# sub-configurations within the config file are given
def config_is_modified(new_config: Dict, old_config: Dict) -> bool:
    for key, value in new_config.items():
        if value != old_config[key]:
            return True
    return False


def get_modified_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    removed_configs = get_removed_configs(new_config_file, current_config_file)
    removed_keys_set = set(removed_configs.keys())
    current_keys_set = set(current_config_file.keys())
    retained_keys_set = current_keys_set.difference(removed_keys_set)
    return {key: current_config_file[key] for key in retained_keys_set if
            config_is_modified(new_config_file[key], current_config_file[key])}


def get_non_modified_configs(new_config_file: Dict, current_config_file: Dict) \
        -> Dict:
    removed_configs = get_removed_configs(new_config_file, current_config_file)
    removed_keys_set = set(removed_configs.keys())
    current_keys_set = set(current_config_file.keys())
    retained_keys_set = current_keys_set.difference(removed_keys_set)
    return {key: current_config_file[key] for key in retained_keys_set
            if not config_is_modified(new_config_file[key],
                                      current_config_file[key])}


def parse_alert_time_thresholds(expected_thresholds: List[str],
                                config: Dict) -> Dict:
    """
    This function returns a dict containing all time thresholds parsed in the
    appropriate format. The returned thresholds are according to the values in
    expected_thresholds.
    :param config: The sub config
    :param expected_thresholds: The time thresholds to parse from the config
    :return: A dict containing all available time thresholds parsed from the
           : alert config. Note a KeyError is raised if a certain threshold
           : cannot be found
    """
    parsed_thresholds = {}
    for threshold in expected_thresholds:
        parsed_thresholds[threshold] = convert_to_float(
            config[threshold], timedelta.max.total_seconds() - 1)

    return parsed_thresholds


def parse_cosmos_node_config(node_config: Dict) -> CosmosNodeConfig:
    """
    Given the received node configuration, this function parses the values
    as a CosmosNodeConfig object
    :param node_config: The received configuration for the node
    :return: A representation of the node config as a CosmosNodeConfig
           : object
    """
    node_id = node_config['id']
    parent_id = node_config['parent_id']
    node_name = node_config['name']
    monitor_node = str_to_bool(node_config['monitor_node'])
    monitor_prometheus = str_to_bool(
        node_config['monitor_prometheus'])
    prometheus_url = node_config['prometheus_url']
    monitor_cosmos_rest = str_to_bool(
        node_config['monitor_cosmos_rest'])
    cosmos_rest_url = node_config['cosmos_rest_url']
    monitor_tendermint_rpc = str_to_bool(
        node_config['monitor_tendermint_rpc'])
    tendermint_rpc_url = node_config['tendermint_rpc_url']
    is_validator = str_to_bool(node_config['is_validator'])
    use_as_data_source = str_to_bool(node_config['use_as_data_source'])
    is_archive_node = str_to_bool(node_config['is_archive_node'])
    operator_address = node_config['operator_address']
    return CosmosNodeConfig(
        node_id, parent_id, node_name, monitor_node, monitor_prometheus,
        prometheus_url, monitor_cosmos_rest, cosmos_rest_url,
        monitor_tendermint_rpc, tendermint_rpc_url, is_validator,
        is_archive_node, use_as_data_source, operator_address)


def parse_substrate_node_config(node_config: Dict) -> SubstrateNodeConfig:
    """
    Given the received node configuration, this function parses the values
    as a SubstrateNodeConfig object
    :param node_config: The received configuration for the node
    :return: A representation of the node config as a SubstrateNodeConfig
           : object
    """
    node_id = node_config['id']
    parent_id = node_config['parent_id']
    node_name = node_config['name']
    monitor_node = str_to_bool(node_config['monitor_node'])
    node_ws_url = node_config['node_ws_url']
    is_validator = str_to_bool(node_config['is_validator'])
    use_as_data_source = str_to_bool(node_config['use_as_data_source'])
    is_archive_node = str_to_bool(node_config['is_archive_node'])
    stash_address = node_config['stash_address']
    return SubstrateNodeConfig(
        node_id, parent_id, node_name, monitor_node, node_ws_url,
        use_as_data_source, is_validator, is_archive_node, stash_address)


def parse_chainlink_node_config(node_config: Dict) -> ChainlinkNodeConfig:
    """
    Given the received node configuration, this function parses the values
    as a ChainlinkNodeConfig object
    :param node_config: The received configuration for the node
    :return: A representation of the node config as a ChainlinkNodeConfig
           : object
    """
    node_id = node_config['id']
    parent_id = node_config['parent_id']
    node_name = node_config['name']
    node_prometheus_urls = node_config['node_prometheus_urls'].split(',')
    monitor_node = str_to_bool(node_config['monitor_node'])
    monitor_prometheus = str_to_bool(node_config['monitor_prometheus'])
    return ChainlinkNodeConfig(
        node_id, parent_id, node_name, monitor_node, monitor_prometheus,
        node_prometheus_urls)


def parse_evm_node_config(node_config: Dict) -> EVMNodeConfig:
    """
    Given the received node configuration, this function parses the values
    as a EVMNodeConfig object
    :param node_config: The received configuration for the node
    :return: A representation of the node config as a EVMNodeConfig object
    """
    node_id = node_config['id']
    parent_id = node_config['parent_id']
    node_name = node_config['name']
    node_http_url = node_config['node_http_url']
    monitor_node = str_to_bool(node_config['monitor_node'])
    return EVMNodeConfig(node_id, parent_id, node_name, monitor_node,
                         node_http_url)
