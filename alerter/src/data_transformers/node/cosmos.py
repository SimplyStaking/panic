import copy
import json
import logging
from datetime import datetime
from typing import Dict, Tuple

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis import RedisApi, Keys
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.nodes.cosmos_node import CosmosNode
from src.utils.constants.data import (
    RAW_TO_TRANSFORMED_COSMOS_NODE_PROM_METRICS, INT_COSMOS_NODE_PROM_METRICS,
    VALID_COSMOS_NODE_SOURCES)
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, COSMOS_NODE_DT_INPUT_QUEUE_NAME,
    COSMOS_NODE_RAW_DATA_ROUTING_KEY, STORE_EXCHANGE, ALERT_EXCHANGE,
    HEALTH_CHECK_EXCHANGE, COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.cosmos import (
    get_load_number_state_helper, get_load_bool_state_helper,
    get_load_str_state_helper, get_load_dict_state_helper)
from src.utils.exceptions import (
    ReceivedUnexpectedDataException, NodeIsDownException,
    MessageWasNotDeliveredException)
from src.utils.types import str_to_bool_strict, convert_to_int


class CosmosNodeDataTransformer(DataTransformer):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi, rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0) -> None:
        super().__init__(transformer_name, logger, redis, rabbitmq,
                         max_queue_size)

    def _initialise_rabbitmq(self) -> None:
        # A data transformer is both a consumer and producer, therefore we need
        # to initialise both the consuming and producing configurations.
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '%s' exchange", RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_declare(
            RAW_DATA_EXCHANGE, 'topic', False, True, False, False)
        self.logger.info("Creating queue '%s'", COSMOS_NODE_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            COSMOS_NODE_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", COSMOS_NODE_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE, COSMOS_NODE_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            COSMOS_NODE_DT_INPUT_QUEUE_NAME, RAW_DATA_EXCHANGE,
            COSMOS_NODE_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(COSMOS_NODE_DT_INPUT_QUEUE_NAME,
                                    self._process_raw_data, False, False, None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", STORE_EXCHANGE)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def _load_number_state(self, cosmos_node: CosmosNode) -> None:
        """
        This function will attempt to load a node's number metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param cosmos_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(cosmos_node.parent_id)
        loading_helper = get_load_number_state_helper(cosmos_node)

        # We iterate over each metric configuration and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode, and then convert to int/float. Note, since
        # an error may occur when obtaining the data, the default value must
        # also be passed as bytes(str()).
        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            convert_fn = configuration['convert_fn']
            set_fn = configuration['setter']
            default_value = bytes(str(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            processed_redis_value = ('None'
                                     if redis_value is None
                                     else redis_value.decode("utf-8"))
            new_value = convert_fn(processed_redis_value, state_value)
            set_fn(new_value)

    def _load_bool_state(self, cosmos_node: CosmosNode) -> None:
        """
        This function will attempt to load a node's boolean metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param cosmos_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(cosmos_node.parent_id)
        loading_helper = get_load_bool_state_helper(cosmos_node)

        # We iterate over each metric configuration and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode, and then convert to bool. Note, since an
        # error may occur when obtaining the data, the default value must also
        # be passed as bytes(str()).
        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            set_fn = configuration['setter']
            default_value = bytes(str(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            processed_redis_value = ('None'
                                     if redis_value is None
                                     else redis_value.decode("utf-8"))
            new_value = (
                None if redis_value == 'None'
                else str_to_bool_strict(processed_redis_value, state_value)
            )
            set_fn(new_value)

    def _load_str_state(self, cosmos_node: CosmosNode) -> None:
        """
        This function will attempt to load a node's string metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param cosmos_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(cosmos_node.parent_id)
        loading_helper = get_load_str_state_helper(cosmos_node)

        # We iterate over each metric configuration and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode and check if the value is None or a string.
        # Note, since an error may occur when obtaining the data, the default
        # value must also be passed as bytes(str()).
        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            set_fn = configuration['setter']
            default_value = bytes(str(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            new_value = (
                None if redis_value is None or redis_value == b'None'
                else redis_value.decode("utf-8")
            )
            set_fn(new_value)

    def _load_dict_state(self, cosmos_node: CosmosNode) -> None:
        """
        This function will attempt to load a node's dict metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param cosmos_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(cosmos_node.parent_id)
        loading_helper = get_load_dict_state_helper(cosmos_node)

        # We iterate over each metric configuration and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode, and then convert to json. Note, since an
        # error may occur when obtaining the data, the default value must also
        # be passed as bytes(json.dumps()).
        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            set_fn = configuration['setter']
            default_value = bytes(json.dumps(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            new_value = (
                state_value if redis_value is None
                else json.loads(redis_value.decode("utf-8"))
            )
            set_fn(new_value)

    def load_state(self, cosmos_node: CosmosNode) -> CosmosNode:
        self.logger.debug("Loading the state of %s from Redis", cosmos_node)

        self._load_number_state(cosmos_node)
        self._load_bool_state(cosmos_node)
        self._load_str_state(cosmos_node)
        self._load_dict_state(cosmos_node)

        self.logger.debug(
            "Restored %s state: _went_down_at_prometheus=%s, "
            "_went_down_at_cosmos_rest=%s, _went_down_at_tendermint_rpc=%s, "
            "_current_height=%s, _voting_power=%s, _is_syncing=%s, "
            "_bond_status=%s, _jailed=%s, _slashed=%s, _missed_blocks=%s, "
            "_last_monitored_prometheus=%s, _last_monitored_tendermint_rpc=%s, "
            "_last_monitored_cosmos_rest=%s", cosmos_node,
            cosmos_node.went_down_at_prometheus,
            cosmos_node.went_down_at_cosmos_rest,
            cosmos_node.went_down_at_tendermint_rpc, cosmos_node.current_height,
            cosmos_node.voting_power, cosmos_node.is_syncing,
            cosmos_node.bond_status, cosmos_node.jailed, cosmos_node.slashed,
            cosmos_node.missed_blocks, cosmos_node.last_monitored_prometheus,
            cosmos_node.last_monitored_tendermint_rpc,
            cosmos_node.last_monitored_cosmos_rest
        )

        return cosmos_node

    def _update_tendermint_rpc_state(self, tendermint_rpc_data: Dict) -> None:
        if 'result' in tendermint_rpc_data:
            meta_data = tendermint_rpc_data['result']['meta_data']
            metrics = tendermint_rpc_data['result']['data']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            node: CosmosNode = self.state[node_id]

            # Set node details just in case the configs have changed, and the
            # new metrics
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)
            node.set_slashed(metrics['slashed'])
            node.set_missed_blocks(metrics['missed_blocks'])
            node.set_is_syncing(metrics['is_syncing'])
            node.set_last_monitored_tendermint_rpc(meta_data['last_monitored'])
            node.set_tendermint_rpc_as_up()
        elif 'error' in tendermint_rpc_data:
            meta_data = tendermint_rpc_data['error']['meta_data']
            error_code = tendermint_rpc_data['error']['code']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            downtime_exception = NodeIsDownException(node_name)
            node: CosmosNode = self.state[node_id]

            # Set node details just in case the configs have changed
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)

            if error_code == downtime_exception.code:
                new_went_down_at = tendermint_rpc_data['error']['data'][
                    'went_down_at']
                node.set_tendermint_rpc_as_down(new_went_down_at)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _update_tendermint_rpc_state".format(self))

    def _update_cosmos_rest_state(self, cosmos_rest_data: Dict) -> None:
        if 'result' in cosmos_rest_data:
            meta_data = cosmos_rest_data['result']['meta_data']
            metrics = cosmos_rest_data['result']['data']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            node: CosmosNode = self.state[node_id]

            # Set node details just in case the configs have changed, and the
            # new metrics
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)
            node.set_bond_status(metrics['bond_status'])
            node.set_jailed(metrics['jailed'])
            node.set_last_monitored_cosmos_rest(meta_data['last_monitored'])
            node.set_cosmos_rest_as_up()
        elif 'error' in cosmos_rest_data:
            meta_data = cosmos_rest_data['error']['meta_data']
            error_code = cosmos_rest_data['error']['code']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            downtime_exception = NodeIsDownException(node_name)
            node: CosmosNode = self.state[node_id]

            # Set node details just in case the configs have changed
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)

            if error_code == downtime_exception.code:
                new_went_down_at = cosmos_rest_data['error']['data'][
                    'went_down_at']
                node.set_cosmos_rest_as_down(new_went_down_at)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _update_cosmos_rest_state".format(self))

    def _update_prometheus_state(self, prometheus_data: Dict) -> None:
        if 'result' in prometheus_data:
            meta_data = prometheus_data['result']['meta_data']
            metrics = prometheus_data['result']['data']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            node: CosmosNode = self.state[node_id]

            # Set node details just in case the configs have changed, and the
            # new metrics
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)
            node.set_current_height(metrics['current_height'])
            node.set_voting_power(metrics['voting_power'])
            node.set_last_monitored_prometheus(meta_data['last_monitored'])
            node.set_prometheus_as_up()
        elif 'error' in prometheus_data:
            meta_data = prometheus_data['error']['meta_data']
            error_code = prometheus_data['error']['code']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            downtime_exception = NodeIsDownException(node_name)
            node: CosmosNode = self.state[node_id]

            # Set node details just in case the configs have changed
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)

            if error_code == downtime_exception.code:
                new_went_down_at = prometheus_data['error']['data'][
                    'went_down_at']
                node.set_prometheus_as_down(new_went_down_at)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _update_prometheus_state".format(self))

    def _update_state(self, transformed_data: Dict) -> None:
        self.logger.debug("Updating state ...")
        processing_performed = False
        update_helper = {
            'prometheus': self._update_prometheus_state,
            'cosmos_rest': self._update_cosmos_rest_state,
            'tendermint_rpc': self._update_tendermint_rpc_state,
        }

        for data_type, update_fn in update_helper.items():
            if data_type in transformed_data and transformed_data[data_type]:
                processing_performed = True
                update_fn(transformed_data[data_type])

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _update_state".format(self))

        self.logger.debug("State updated successfully")

    def _process_transformed_data_for_saving(self,
                                             transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for storage ...")
        processing_performed = False

        # We must check that the source's data is valid
        for source in VALID_COSMOS_NODE_SOURCES:
            if source in transformed_data and transformed_data[source]:
                if ('result' in transformed_data[source]
                        or 'error' in transformed_data[source]):
                    processing_performed = True
                else:
                    raise ReceivedUnexpectedDataException(
                        "{}: _process_transformed_data_for_saving".format(self))

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_saving".format(self))

        return copy.deepcopy(transformed_data)

    def _process_transformed_tendermint_rpc_data_for_alerting(
            self, transformed_tendermint_rpc_data: Dict) -> Dict:
        if 'result' in transformed_tendermint_rpc_data:
            td_meta_data = transformed_tendermint_rpc_data['result'][
                'meta_data']
            td_node_id = td_meta_data['node_id']
            node: CosmosNode = self.state[td_node_id]
            td_metrics = transformed_tendermint_rpc_data['result']['data']

            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {}
                }
            }
            pd_data = processed_data['result']['data']

            # Reformat the data in such a way that both the previous and current
            # states are sent to the alerter
            for metric, value in td_metrics.items():
                pd_data[metric] = {}
                pd_data[metric]['current'] = value

            # Add previous for each metric
            pd_data['went_down_at'][
                'previous'] = node.went_down_at_tendermint_rpc
            pd_data['slashed']['previous'] = copy.deepcopy(node.slashed)
            pd_data['missed_blocks']['previous'] = copy.deepcopy(
                node.missed_blocks)
            pd_data['is_syncing']['previous'] = node.is_syncing
        elif 'error' in transformed_tendermint_rpc_data:
            td_meta_data = transformed_tendermint_rpc_data['error']['meta_data']
            td_error_code = transformed_tendermint_rpc_data['error']['code']
            td_node_id = td_meta_data['node_id']
            td_node_name = td_meta_data['node_name']
            node: CosmosNode = self.state[td_node_id]
            downtime_exception = NodeIsDownException(td_node_name)

            processed_data = copy.deepcopy(transformed_tendermint_rpc_data)
            if td_error_code == downtime_exception.code:
                td_data = transformed_tendermint_rpc_data['error']['data']
                pd_data = processed_data['error']['data']

                for metric, value in td_data.items():
                    pd_data[metric] = {}
                    pd_data[metric]['current'] = value

                pd_data['went_down_at'][
                    'previous'] = node.went_down_at_tendermint_rpc
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_tendermint_rpc_data_for_"
                "alerting".format(self))

        return processed_data

    def _process_transformed_cosmos_rest_data_for_alerting(
            self, transformed_cosmos_rest_data: Dict) -> Dict:
        if 'result' in transformed_cosmos_rest_data:
            td_meta_data = transformed_cosmos_rest_data['result']['meta_data']
            td_node_id = td_meta_data['node_id']
            node: CosmosNode = self.state[td_node_id]
            td_metrics = transformed_cosmos_rest_data['result']['data']

            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {}
                }
            }
            pd_data = processed_data['result']['data']

            # Reformat the data in such a way that both the previous and current
            # states are sent to the alerter
            for metric, value in td_metrics.items():
                pd_data[metric] = {}
                pd_data[metric]['current'] = value

            # Add previous for each metric
            pd_data['went_down_at']['previous'] = node.went_down_at_cosmos_rest
            pd_data['bond_status']['previous'] = node.bond_status
            pd_data['jailed']['previous'] = node.jailed
        elif 'error' in transformed_cosmos_rest_data:
            td_meta_data = transformed_cosmos_rest_data['error']['meta_data']
            td_error_code = transformed_cosmos_rest_data['error']['code']
            td_node_id = td_meta_data['node_id']
            td_node_name = td_meta_data['node_name']
            node: CosmosNode = self.state[td_node_id]
            downtime_exception = NodeIsDownException(td_node_name)

            processed_data = copy.deepcopy(transformed_cosmos_rest_data)
            if td_error_code == downtime_exception.code:
                td_data = transformed_cosmos_rest_data['error']['data']
                pd_data = processed_data['error']['data']

                for metric, value in td_data.items():
                    pd_data[metric] = {}
                    pd_data[metric]['current'] = value

                pd_data['went_down_at'][
                    'previous'] = node.went_down_at_cosmos_rest
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_cosmos_rest_data_for_alerting".format(
                    self))

        return processed_data

    def _process_transformed_prometheus_data_for_alerting(
            self, transformed_prometheus_data: Dict) -> Dict:
        if 'result' in transformed_prometheus_data:
            td_meta_data = transformed_prometheus_data['result']['meta_data']
            td_node_id = td_meta_data['node_id']
            node: CosmosNode = self.state[td_node_id]
            td_metrics = transformed_prometheus_data['result']['data']

            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {}
                }
            }
            pd_data = processed_data['result']['data']

            # Reformat the data in such a way that both the previous and current
            # states are sent to the alerter
            for metric, value in td_metrics.items():
                pd_data[metric] = {}
                pd_data[metric]['current'] = value

            # Add previous for each metric
            pd_data['went_down_at']['previous'] = node.went_down_at_prometheus
            pd_data['current_height']['previous'] = node.current_height
            pd_data['voting_power']['previous'] = node.voting_power
        elif 'error' in transformed_prometheus_data:
            td_meta_data = transformed_prometheus_data['error']['meta_data']
            td_error_code = transformed_prometheus_data['error']['code']
            td_node_id = td_meta_data['node_id']
            td_node_name = td_meta_data['node_name']
            node: CosmosNode = self.state[td_node_id]
            downtime_exception = NodeIsDownException(td_node_name)

            processed_data = copy.deepcopy(transformed_prometheus_data)
            if td_error_code == downtime_exception.code:
                td_data = transformed_prometheus_data['error']['data']
                pd_data = processed_data['error']['data']

                for metric, value in td_data.items():
                    pd_data[metric] = {}
                    pd_data[metric]['current'] = value

                pd_data['went_down_at'][
                    'previous'] = node.went_down_at_prometheus
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_prometheus_data_for_alerting".format(
                    self))

        return processed_data

    def _process_transformed_data_for_alerting(self,
                                               transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for alerting ...")
        processing_performed = False
        processing_helper = {
            'prometheus':
                self._process_transformed_prometheus_data_for_alerting,
            'cosmos_rest':
                self._process_transformed_cosmos_rest_data_for_alerting,
            'tendermint_rpc':
                self._process_transformed_tendermint_rpc_data_for_alerting,
        }
        processed_data = {
            'prometheus': {},
            'cosmos_rest': {},
            'tendermint_rpc': {},
        }

        for data_type, processing_fn in processing_helper.items():
            if data_type in transformed_data and transformed_data[data_type]:
                processing_performed = True
                processed_data[data_type] = processing_fn(
                    transformed_data[data_type])

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_alerting".format(self))

        self.logger.debug("Processing successful.")

        return processed_data

    def _transform_tendermint_rpc_data(self, tendermint_rpc_data: Dict) -> Dict:
        if 'result' in tendermint_rpc_data:
            meta_data = tendermint_rpc_data['result']['meta_data']
            node_metrics = tendermint_rpc_data['result']['data']
            transformed_data = copy.deepcopy(tendermint_rpc_data)
            td_meta_data = transformed_data['result']['meta_data']
            td_node_metrics = transformed_data['result']['data']
            node_id = meta_data['node_id']
            node: CosmosNode = self.state[node_id]

            # Historical data will be used to compute new metrics slashed and
            # missed blocks
            del td_node_metrics['historical']
            td_node_metrics['slashed'] = {
                'slashed': False,
                'amount_map': {}
            }
            td_node_metrics['missed_blocks'] = {
                'total_count': node.missed_blocks['total_count'],
                'missed_heights': []
            }

            if node_metrics['historical'] is not None:
                historical_data = node_metrics['historical']
                transformed_slashed = td_node_metrics['slashed']
                transformed_missed_blocks = td_node_metrics['missed_blocks']
                for datum in historical_data:
                    # Check each historical datum from the previous round to
                    # confirm whether slashing occurred. If slashing occurred in
                    # at least one block height, then _slashed['slashed'] will
                    # be set to True, and _slashed['slashed']['amount'] will
                    # contain a map from the slashed block heights to the amount
                    # slashed at that height (if amount is available).
                    block_height = int(datum['height'])
                    slashed_at_height = datum['slashed']
                    slashed_amount = datum['slashed_amount']
                    if slashed_at_height:
                        transformed_slashed['slashed'] = True
                        transformed_slashed['amount_map'][str(block_height)] = (
                            None if slashed_amount is None
                            else float(slashed_amount)
                        )

                    # Traverse each historical datum from the previous round to
                    # check if the node missed some blocks. If the node is an
                    # active validator and did not sign a block, _missed_blocks[
                    # 'total_count'] will be incremented by one and the block
                    # height - 1 will be added to _missed_blocks[
                    # 'missed_heights']. Note that each block has signing
                    # information related to the previous block height.
                    was_active = datum['active_in_prev_block']
                    signed_block = datum['signed_prev_block']
                    if was_active and not signed_block:
                        transformed_missed_blocks['total_count'] += 1
                        transformed_missed_blocks['missed_heights'].append(
                            block_height - 1)

            # Transform the meta_data by deleting the monitor_name and changing
            # the time key to last_monitored key
            del td_meta_data['monitor_name']
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']
            td_node_metrics['went_down_at'] = None
        elif 'error' in tendermint_rpc_data:
            meta_data = tendermint_rpc_data['error']['meta_data']
            error_code = tendermint_rpc_data['error']['code']
            node_id = meta_data['node_id']
            node_name = meta_data['node_name']
            time_of_error = meta_data['time']
            node: CosmosNode = self.state[node_id]
            downtime_exception = NodeIsDownException(node_name)

            # In case of non-downtime errors only remove the monitor_name from
            # the meta data
            transformed_data = copy.deepcopy(tendermint_rpc_data)
            del transformed_data['error']['meta_data']['monitor_name']

            # If we have a downtime error, set went_down_at_tendermint_rpc to
            # the time of error if the interface was up. Otherwise, leave
            # went_down_at_tendermint_rpc as stored in the node state
            if error_code == downtime_exception.code:
                transformed_data['error']['data'] = {}
                td_metrics = transformed_data['error']['data']
                td_metrics['went_down_at'] = (
                    node.went_down_at_tendermint_rpc
                    if node.is_down_tendermint_rpc
                    else time_of_error
                )
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _transform_tendermint_rpc_data".format(self))

        return transformed_data

    def _transform_cosmos_rest_data(self, cosmos_rest_data: Dict) -> Dict:
        if 'result' in cosmos_rest_data:
            # In the case of cosmos_rest metric we will only transform the
            # meta_data by deleting the monitor_name and changing the time key
            # to last_monitored key
            meta_data = cosmos_rest_data['result']['meta_data']
            transformed_data = copy.deepcopy(cosmos_rest_data)
            td_meta_data = transformed_data['result']['meta_data']
            td_node_metrics = transformed_data['result']['data']
            del td_meta_data['monitor_name']
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']
            td_node_metrics['went_down_at'] = None
        elif 'error' in cosmos_rest_data:
            meta_data = cosmos_rest_data['error']['meta_data']
            error_code = cosmos_rest_data['error']['code']
            node_id = meta_data['node_id']
            node_name = meta_data['node_name']
            time_of_error = meta_data['time']
            node: CosmosNode = self.state[node_id]
            downtime_exception = NodeIsDownException(node_name)

            # In case of non-downtime errors only remove the monitor_name from
            # the meta data
            transformed_data = copy.deepcopy(cosmos_rest_data)
            del transformed_data['error']['meta_data']['monitor_name']

            # If we have a downtime error, set went_down_at_cosmos_rest to the
            # time of error if the interface was up. Otherwise, leave
            # went_down_at_cosmos_rest as stored in the node state
            if error_code == downtime_exception.code:
                transformed_data['error']['data'] = {}
                td_metrics = transformed_data['error']['data']
                td_metrics['went_down_at'] = (
                    node.went_down_at_cosmos_rest if node.is_down_cosmos_rest
                    else time_of_error
                )
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _transform_cosmos_rest_data".format(self))

        return transformed_data

    def _transform_prometheus_data(self, prometheus_data: Dict) -> Dict:
        if 'result' in prometheus_data:
            meta_data = prometheus_data['result']['meta_data']
            node_metrics = prometheus_data['result']['data']
            transformed_data = copy.deepcopy(prometheus_data)
            td_meta_data = transformed_data['result']['meta_data']
            td_node_metrics = transformed_data['result']['data']

            # First convert the raw metric names into the transformed names
            for raw_metric, transformed_metric in \
                    RAW_TO_TRANSFORMED_COSMOS_NODE_PROM_METRICS.items():
                del td_node_metrics[raw_metric]
                td_node_metrics[transformed_metric] = node_metrics[
                    raw_metric]

            # Convert the int metric values
            for transformed_metric in INT_COSMOS_NODE_PROM_METRICS:
                td_node_metrics[transformed_metric] = convert_to_int(
                    td_node_metrics[transformed_metric], None)

            # Transform the meta_data by deleting the monitor_name and changing
            # the time key to last_monitored key
            del td_meta_data['monitor_name']
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']
            td_node_metrics['went_down_at'] = None
        elif 'error' in prometheus_data:
            meta_data = prometheus_data['error']['meta_data']
            error_code = prometheus_data['error']['code']
            node_id = meta_data['node_id']
            node_name = meta_data['node_name']
            time_of_error = meta_data['time']
            node: CosmosNode = self.state[node_id]
            downtime_exception = NodeIsDownException(node_name)

            # In case of non-downtime errors only remove the monitor_name from
            # the meta data
            transformed_data = copy.deepcopy(prometheus_data)
            del transformed_data['error']['meta_data']['monitor_name']

            # If we have a downtime error, set went_down_at_prometheus to
            # the time of error if the interface was up. Otherwise, leave
            # went_down_at_prometheus as stored in the node state
            if error_code == downtime_exception.code:
                transformed_data['error']['data'] = {}
                td_metrics = transformed_data['error']['data']
                td_metrics['went_down_at'] = (
                    node.went_down_at_prometheus if node.is_down_prometheus
                    else time_of_error
                )
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _transform_prometheus_data".format(self))

        return transformed_data

    def _transform_data(self, data: Dict) -> Tuple[Dict, Dict, Dict]:
        self.logger.debug("Performing data transformation on %s ...", data)
        processing_performed = False
        transformation_helper = {
            'prometheus': self._transform_prometheus_data,
            'cosmos_rest': self._transform_cosmos_rest_data,
            'tendermint_rpc': self._transform_tendermint_rpc_data,
        }
        transformed_data = {
            'prometheus': {},
            'cosmos_rest': {},
            'tendermint_rpc': {},
        }

        for data_type, transformation_fn in transformation_helper.items():
            if data_type in data and data[data_type]:
                processing_performed = True
                transformed_data[data_type] = transformation_fn(data[data_type])

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _transform_data".format(self))

        data_for_alerting = self._process_transformed_data_for_alerting(
            transformed_data)
        data_for_saving = self._process_transformed_data_for_saving(
            transformed_data)

        self.logger.debug("Data transformation successful")

        return transformed_data, data_for_alerting, data_for_saving

    def _place_latest_data_on_queue(self, data_for_alerting: Dict,
                                    data_for_saving: Dict) -> None:
        self._push_to_queue(data_for_alerting, ALERT_EXCHANGE,
                            COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

        self._push_to_queue(data_for_saving, STORE_EXCHANGE,
                            COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

    def _validate_and_parse_raw_data_sources(
            self, raw_data: Dict) -> Tuple[str, str, str]:
        """
        This method checks the following things about the raw_data:
        1. Only valid sources are inside the raw_data
        2. All valid sources are inside the raw_data
        3. At least one source is not empty
        4. All source's data is indexed by 'result' or 'error' and all data
           has a 'node_parent_id', 'node_id', 'node_name'
        5. All node_parent_ids, node_ids, node_names are equal across all
           sources
        :param raw_data: The raw_data being received from the monitor
        :return: node_parent_id, node_id, node_name       : If valid raw_data
               : Raises ReceivedUnexpectedDataException   : otherwise
        """

        # Check that raw_data has all the valid sources and no other sources
        if set(raw_data.keys()) != set(VALID_COSMOS_NODE_SOURCES):
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        list_of_sources_values = [value for source, value in raw_data.items()]

        # Check that at least one value is not empty
        if all(not value for value in list_of_sources_values):
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        # If all non-empty source data is not indexed by 'result' or 'error', or
        # some non-empty source data does not have `node_parent_id`, `node_id`
        # or `node_name`, a  ReceivedUnexpectedDataException is raised.
        try:
            list_of_parent_ids = []
            list_of_node_ids = []
            list_of_node_names = []
            for value in list_of_sources_values:
                if value:
                    response_index_key = (
                        'result' if 'result' in value
                        else 'error'
                    )
                    list_of_parent_ids.append(
                        value[response_index_key]['meta_data'][
                            'node_parent_id'])
                    list_of_node_ids.append(
                        value[response_index_key]['meta_data']['node_id'])
                    list_of_node_names.append(
                        value[response_index_key]['meta_data']['node_name'])
        except KeyError:
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        # Check that all node_parent_ids, node_ids and node_names are equal. If
        # a list has identical elements, then when converted to a set there must
        # be only 1 element in the set
        if (
                not len(set(list_of_parent_ids)) == 1 or
                not len(set(list_of_node_ids)) == 1 or
                not len(set(list_of_node_names)) == 1
        ):
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        return list_of_parent_ids[0], list_of_node_ids[0], list_of_node_names[0]

    def _process_raw_data(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        raw_data = json.loads(body)
        self.logger.debug("Received %s from monitors. Now processing this "
                          "data.", raw_data)

        processing_error = False
        transformed_data = {}
        data_for_alerting = {}
        data_for_saving = {}
        try:
            node_parent_id, node_id, node_name = \
                self._validate_and_parse_raw_data_sources(raw_data)

            if node_id not in self.state:
                new_node = CosmosNode(node_name, node_id, node_parent_id)
                loaded_node = self.load_state(new_node)
                self._state[node_id] = loaded_node

            transformed_data, data_for_alerting, data_for_saving = \
                self._transform_data(raw_data)
        except Exception as e:
            self.logger.error("Error when processing %s", raw_data)
            self.logger.exception(e)
            processing_error = True

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # We want to update the state after the data is acknowledged, otherwise
        # if acknowledgement fails the state would be erroneous when processing
        # the data again. Note, only update the state if there were no
        # processing errors. IMP: We are allowed to update the state before
        # sending the data because deep copies where constructed when computing
        # data_for_alerting, data_for_saving and transformed_data.
        if not processing_error:
            try:
                self._update_state(transformed_data)
                self.logger.debug("Successfully processed %s", raw_data)
            except Exception as e:
                self.logger.error("Error when processing %s", raw_data)
                self.logger.exception(e)
                processing_error = True

        # Place the data on the publishing queue if there were no processing
        # errors. This is done after acknowledging the data, so that if
        # acknowledgement fails, the data is processed again and we do not have
        # duplication of data in the queue
        if not processing_error:
            self._place_latest_data_on_queue(data_for_alerting, data_for_saving)

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()

            if not processing_error:
                heartbeat = {
                    'component_name': self.transformer_name,
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as message is residing in the
            # publisher queue.
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it.
            raise e
