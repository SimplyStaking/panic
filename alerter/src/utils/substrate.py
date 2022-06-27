from typing import List, Dict

from src.data_store.redis import Keys
from src.monitorables.networks.substrate import SubstrateNetwork
from src.monitorables.nodes.substrate_node import SubstrateNode
from src.utils.types import convert_to_int, convert_to_float


def get_load_number_state_helper(substrate_node: SubstrateNode) -> List[Dict]:
    """
    Given a substrate node, this function will return a list of dicts containing
    information on how each number metric needs to be loaded from Redis.
    :param substrate_node: The node to consider
    :return: [{'convert_fn': convert_to_int/convert_to_float,
               'state_value': float/int, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = substrate_node.node_id
    return [
        {'convert_fn': convert_to_float,
         'state_value': substrate_node.went_down_at_websocket,
         'setter': substrate_node.set_went_down_at_websocket,
         'redis_key': Keys.get_substrate_node_went_down_at_websocket(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.best_height,
         'setter': substrate_node.set_best_height,
         'redis_key': Keys.get_substrate_node_best_height(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.target_height,
         'setter': substrate_node.set_target_height,
         'redis_key': Keys.get_substrate_node_target_height(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.finalized_height,
         'setter': substrate_node.set_finalized_height,
         'redis_key': Keys.get_substrate_node_finalized_height(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.current_session,
         'setter': substrate_node.set_current_session,
         'redis_key': Keys.get_substrate_node_current_session(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.current_era,
         'setter': substrate_node.set_current_era,
         'redis_key': Keys.get_substrate_node_current_era(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.authored_blocks,
         'setter': substrate_node.set_authored_blocks,
         'redis_key': Keys.get_substrate_node_authored_blocks(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.history_depth_eras,
         'setter': substrate_node.set_history_depth_eras,
         'redis_key': Keys.get_substrate_node_history_depth_eras(node_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_node.previous_era_rewards,
         'setter': substrate_node.set_previous_era_rewards,
         'redis_key': Keys.get_substrate_node_previous_era_rewards(node_id)},
        {'convert_fn': convert_to_float,
         'state_value': substrate_node.last_monitored_websocket,
         'setter': substrate_node.set_last_monitored_websocket,
         'redis_key': Keys.get_substrate_node_last_monitored_websocket(node_id)
         },
    ]


def get_load_bool_state_helper(substrate_node: SubstrateNode) -> List[Dict]:
    """
    Given a substrate node, this function will return a list of dicts containing
    information on how each boolean metric needs to be loaded from Redis.
    :param substrate_node: The node to consider
    :return: [{'state_value': bool, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = substrate_node.node_id
    return [
        {'state_value': substrate_node.active,
         'setter': substrate_node.set_active,
         'redis_key': Keys.get_substrate_node_active(node_id)},
        {'state_value': substrate_node.elected,
         'setter': substrate_node.set_elected,
         'redis_key': Keys.get_substrate_node_elected(node_id)},
        {'state_value': substrate_node.disabled,
         'setter': substrate_node.set_disabled,
         'redis_key': Keys.get_substrate_node_disabled(node_id)},
        {'state_value': substrate_node.sent_heartbeat,
         'setter': substrate_node.set_sent_heartbeat,
         'redis_key': Keys.get_substrate_node_sent_heartbeat(node_id)},
    ]


def get_load_str_state_helper(substrate_node: SubstrateNode) -> List[Dict]:
    """
    Given a substrate node, this function will return a list of dicts containing
    information on how each string metric needs to be loaded from Redis.
    :param substrate_node: The node to consider
    :return: [{'state_value': bool, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = substrate_node.node_id
    return [
        {'state_value': substrate_node.controller_address,
         'setter': substrate_node.set_controller_address,
         'redis_key': Keys.get_substrate_node_controller_address(node_id)},
        {'state_value': substrate_node.token_symbol,
         'setter': substrate_node.set_token_symbol,
         'redis_key': Keys.get_substrate_node_token_symbol(node_id)}
    ]


def get_load_dict_state_helper(substrate_node: SubstrateNode) -> List[Dict]:
    """
    Given a substrate node, this function will return a list of dicts containing
    information on how each dict metric needs to be loaded from Redis.
    :param substrate_node: The node to consider
    :return: [{'state_value': bool, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = substrate_node.node_id
    return [
        {'state_value': substrate_node.eras_stakers,
         'setter': substrate_node.set_eras_stakers,
         'redis_key': Keys.get_substrate_node_eras_stakers(node_id)},
    ]


def get_load_list_state_helper(substrate_node: SubstrateNode) -> List[Dict]:
    """
    Given a substrate node, this function will return a list of dicts containing
    information on how each list metric needs to be loaded from Redis.
    :param substrate_node: The node to consider
    :return: [{'state_value': bool, 'setter': attribute_setting_fn,
               'redis_key': fn_from_store_keys}]
    """
    node_id = substrate_node.node_id
    return [
        {'state_value': substrate_node.unclaimed_rewards,
         'setter': substrate_node.set_unclaimed_rewards,
         'redis_key': Keys.get_substrate_node_unclaimed_rewards(node_id)},
        {'state_value': substrate_node.claimed_rewards,
         'setter': substrate_node.set_claimed_rewards,
         'redis_key': Keys.get_substrate_node_claimed_rewards(node_id)},
        {'state_value': substrate_node.historical,
         'setter': substrate_node.set_historical,
         'redis_key': Keys.get_substrate_node_historical(node_id)},
    ]


def get_load_bool_state_helper_network(
        substrate_network: SubstrateNetwork) -> List[Dict]:
    parent_id = substrate_network.parent_id

    return [
        {'state_value': substrate_network.grandpa_stalled,
         'setter': substrate_network.set_grandpa_stalled,
         'redis_key': Keys.get_substrate_network_grandpa_stalled(parent_id)},
    ]


def get_load_number_state_helper_network(
        substrate_network: SubstrateNetwork) -> List[Dict]:
    parent_id = substrate_network.parent_id

    return [
        {'convert_fn': convert_to_int,
         'state_value': substrate_network.public_prop_count,
         'setter': substrate_network.set_public_prop_count,
         'redis_key':
             Keys.get_substrate_network_public_prop_count(parent_id)},
        {'convert_fn': convert_to_int,
         'state_value': substrate_network.referendum_count,
         'setter': substrate_network.set_referendum_count,
         'redis_key':
             Keys.get_substrate_network_referendum_count(parent_id)},
        {'convert_fn': convert_to_float,
         'state_value': substrate_network.last_monitored_websocket,
         'setter': substrate_network.set_last_monitored_websocket,
         'redis_key':
             Keys.get_substrate_network_last_monitored_websocket(parent_id)},
    ]


def get_load_list_of_dicts_state_helper_network(
        substrate_network: SubstrateNetwork) -> List[Dict]:
    parent_id = substrate_network.parent_id
    return [
        {'state_value': substrate_network.active_proposals,
         'setter': substrate_network.set_active_proposals,
         'redis_key': Keys.get_substrate_network_active_proposals(parent_id)},
        {'state_value': substrate_network.referendums,
         'setter': substrate_network.set_referendums,
         'redis_key': Keys.get_substrate_network_referendums(parent_id)},
    ]
