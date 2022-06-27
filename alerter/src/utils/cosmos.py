from typing import List, Dict

import bech32

from src.data_store.redis import Keys
from src.monitorables.networks.cosmos import CosmosNetwork
from src.monitorables.nodes.cosmos_node import CosmosNode
from src.utils.types import convert_to_float, convert_to_int


def bech32_to_address(bech32_str: str) -> str:
    _, decoded = bech32.bech32_decode(bech32_str)
    address = bytearray(bech32.convertbits(decoded, 5, 8, False))
    address_hex = ''.join('{:02x}'.format(x) for x in address)
    return address_hex.upper()


def get_load_number_state_helper_network(
        cosmos_network: CosmosNetwork) -> List[Dict]:
    parent_id = cosmos_network.parent_id

    return [
        {'convert_fn': convert_to_float,
         'state_value': cosmos_network.last_monitored_cosmos_rest,
         'setter': cosmos_network.set_last_monitored_cosmos_rest,
         'redis_key':
             Keys.get_cosmos_network_last_monitored_cosmos_rest(parent_id)},
    ]


def get_load_number_state_helper(cosmos_node: CosmosNode) -> List[Dict]:
    """
    Given a cosmos node, this function will return a list of dicts containing
    information on how each number metric needs to be loaded from Redis.
    :param cosmos_node: The node to consider
    :return: [{'convert_fn': convert_to_int/convert_to_float,
               'state_value': float/int, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = cosmos_node.node_id
    return [
        {'convert_fn': convert_to_float,
         'state_value': cosmos_node.went_down_at_prometheus,
         'setter': cosmos_node.set_went_down_at_prometheus,
         'redis_key': Keys.get_cosmos_node_went_down_at_prometheus(node_id)},
        {'convert_fn': convert_to_float,
         'state_value': cosmos_node.went_down_at_cosmos_rest,
         'setter': cosmos_node.set_went_down_at_cosmos_rest,
         'redis_key': Keys.get_cosmos_node_went_down_at_cosmos_rest(node_id)},
        {'convert_fn': convert_to_float,
         'state_value': cosmos_node.went_down_at_tendermint_rpc,
         'setter': cosmos_node.set_went_down_at_tendermint_rpc,
         'redis_key': Keys.get_cosmos_node_went_down_at_tendermint_rpc(
             node_id)},
        {'convert_fn': convert_to_int,
         'state_value': cosmos_node.current_height,
         'setter': cosmos_node.set_current_height,
         'redis_key': Keys.get_cosmos_node_current_height(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': cosmos_node.voting_power,
         'setter': cosmos_node.set_voting_power,
         'redis_key': Keys.get_cosmos_node_voting_power(node_id)},
        {'convert_fn': convert_to_float,
         'state_value': cosmos_node.last_monitored_prometheus,
         'setter': cosmos_node.set_last_monitored_prometheus,
         'redis_key': Keys.get_cosmos_node_last_monitored_prometheus(node_id)},
        {'convert_fn': convert_to_float,
         'state_value': cosmos_node.last_monitored_cosmos_rest,
         'setter': cosmos_node.set_last_monitored_cosmos_rest,
         'redis_key': Keys.get_cosmos_node_last_monitored_cosmos_rest(node_id)},
        {'convert_fn': convert_to_float,
         'state_value': cosmos_node.last_monitored_tendermint_rpc,
         'setter': cosmos_node.set_last_monitored_tendermint_rpc,
         'redis_key': Keys.get_cosmos_node_last_monitored_tendermint_rpc(
             node_id)},
    ]


def get_load_bool_state_helper(cosmos_node: CosmosNode) -> List[Dict]:
    """
    Given a cosmos node, this function will return a list of dicts containing
    information on how each boolean metric needs to be loaded from Redis.
    :param cosmos_node: The node to consider
    :return: [{'state_value': bool, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = cosmos_node.node_id
    return [
        {'state_value': cosmos_node.is_syncing,
         'setter': cosmos_node.set_is_syncing,
         'redis_key': Keys.get_cosmos_node_is_syncing(node_id)},
        {'state_value': cosmos_node.jailed,
         'setter': cosmos_node.set_jailed,
         'redis_key': Keys.get_cosmos_node_jailed(node_id)},
    ]


def get_load_str_state_helper(cosmos_node: CosmosNode) -> List[Dict]:
    """
    Given a cosmos node, this function will return a list of dicts containing
    information on how each string metric needs to be loaded from Redis.
    :param cosmos_node: The node to consider
    :return: [{'state_value': bool, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = cosmos_node.node_id
    return [
        {'state_value': cosmos_node.bond_status,
         'setter': cosmos_node.set_bond_status,
         'redis_key': Keys.get_cosmos_node_bond_status(node_id)},
    ]


def get_load_dict_state_helper(cosmos_node: CosmosNode) -> List[Dict]:
    """
    Given a cosmos node, this function will return a list of dicts containing
    information on how each dict metric needs to be loaded from Redis.
    :param cosmos_node: The node to consider
    :return: [{'state_value': bool, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = cosmos_node.node_id
    return [
        {'state_value': cosmos_node.slashed,
         'setter': cosmos_node.set_slashed,
         'redis_key': Keys.get_cosmos_node_slashed(node_id)},
        {'state_value': cosmos_node.missed_blocks,
         'setter': cosmos_node.set_missed_blocks,
         'redis_key': Keys.get_cosmos_node_missed_blocks(node_id)},
    ]


def get_load_list_of_dicts_state_helper(
        cosmos_network: CosmosNetwork) -> List[Dict]:
    parent_id = cosmos_network.parent_id
    return [
        {'state_value': cosmos_network.proposals,
         'setter': cosmos_network.set_proposals,
         'redis_key': Keys.get_cosmos_network_proposals(parent_id)},
    ]
