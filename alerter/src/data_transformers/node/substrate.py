import copy
import json
import logging
from ast import literal_eval
from datetime import datetime
from typing import Dict, Tuple

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis import RedisApi, Keys
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.nodes.substrate_node import SubstrateNode
from src.utils.constants.data import (
    VALID_SUBSTRATE_NODE_SOURCES, INT_SUBSTRATE_NODE_WS_METRICS)
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, STORE_EXCHANGE, ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    SUBSTRATE_NODE_DT_INPUT_QUEUE_NAME, SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY,
    SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    ReceivedUnexpectedDataException, NodeIsDownException,
    MessageWasNotDeliveredException)
from src.utils.substrate import (
    get_load_number_state_helper, get_load_bool_state_helper,
    get_load_str_state_helper, get_load_dict_state_helper,
    get_load_list_state_helper)
from src.utils.types import str_to_bool_strict


class SubstrateNodeDataTransformer(DataTransformer):
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
        self.logger.info("Creating queue '%s'",
                         SUBSTRATE_NODE_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            SUBSTRATE_NODE_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", SUBSTRATE_NODE_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE, SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            SUBSTRATE_NODE_DT_INPUT_QUEUE_NAME, RAW_DATA_EXCHANGE,
            SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(SUBSTRATE_NODE_DT_INPUT_QUEUE_NAME,
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

    def _load_number_state(self, substrate_node: SubstrateNode) -> None:
        """
        This function will attempt to load a node's number metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param substrate_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(substrate_node.parent_id)
        loading_helper = get_load_number_state_helper(substrate_node)

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

    def _load_bool_state(self, substrate_node: SubstrateNode) -> None:
        """
        This function will attempt to load a node's boolean metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param substrate_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(substrate_node.parent_id)
        loading_helper = get_load_bool_state_helper(substrate_node)

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

    def _load_str_state(self, substrate_node: SubstrateNode) -> None:
        """
        This function will attempt to load a node's string metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param substrate_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(substrate_node.parent_id)
        loading_helper = get_load_str_state_helper(substrate_node)

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

    def _load_dict_state(self, substrate_node: SubstrateNode) -> None:
        """
        This function will attempt to load a node's dict metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param substrate_node: The node state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(substrate_node.parent_id)
        loading_helper = get_load_dict_state_helper(substrate_node)

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

    def _load_list_state(self, substrate_node: SubstrateNode) -> None:

        redis_hash = Keys.get_hash_parent(substrate_node.parent_id)
        loading_helper = get_load_list_state_helper(substrate_node)

        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            set_fn = configuration['setter']
            default_value = bytes(json.dumps(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            new_value = [] if redis_value is None else json.loads(
                redis_value.decode("utf-8"))
            set_fn(new_value)

    def load_state(self, substrate_node: SubstrateNode) -> SubstrateNode:
        self.logger.debug("Loading the state of %s from Redis", substrate_node)

        self._load_number_state(substrate_node)
        self._load_bool_state(substrate_node)
        self._load_str_state(substrate_node)
        self._load_dict_state(substrate_node)
        self._load_list_state(substrate_node)

        self.logger.debug(
            "Restored %s state: _last_monitored_websocket=%s, "
            "_token_symbol=%s, _best_height=%s, _target_height=%s, "
            "_finalized_height=%s, _current_session=%s, _current_era=%s, "
            "_authored_blocks=%s, _active=%s, _elected=%s, _disabled=%s, "
            "_eras_stakers=%s, _sent_heartbeat=%s, _controller_address=%s, "
            "_history_depth_eras=%s, _unclaimed_rewards=%s, "
            "_claimed_rewards=%s, _previous_era_rewards=%s, _historical=%s",
            substrate_node, substrate_node.last_monitored_websocket,
            substrate_node.token_symbol, substrate_node.best_height,
            substrate_node.target_height, substrate_node.finalized_height,
            substrate_node.current_session, substrate_node.current_era,
            substrate_node.authored_blocks, substrate_node.active,
            substrate_node.elected, substrate_node.disabled,
            substrate_node.eras_stakers, substrate_node.sent_heartbeat,
            substrate_node.controller_address,
            substrate_node.history_depth_eras, substrate_node.unclaimed_rewards,
            substrate_node.claimed_rewards, substrate_node.previous_era_rewards,
            substrate_node.historical
        )

        return substrate_node

    def _transform_websocket_data(self, websocket_data: Dict) -> Dict:
        if 'result' in websocket_data:
            meta_data = websocket_data['result']['meta_data']
            transformed_data = copy.deepcopy(websocket_data)
            td_meta_data = transformed_data['result']['meta_data']
            td_node_metrics = transformed_data['result']['data']

            system_properties = td_node_metrics['system_properties']
            token_decimals = (system_properties['tokenDecimals'][0] if
                              system_properties and 'tokenDecimals' in
                              system_properties and isinstance(
                                  system_properties['tokenDecimals'], list)
                              and len(system_properties['tokenDecimals']) > 0
                              else None)
            token_symbol = (system_properties['tokenSymbol'][0] if
                            system_properties and 'tokenSymbol' in
                            system_properties and isinstance(
                                system_properties['tokenSymbol'], list)
                            and len(system_properties['tokenSymbol']) > 0
                            else None)

            # Convert potential hex values to int metric values
            for transformed_metric in INT_SUBSTRATE_NODE_WS_METRICS:
                td_node_metrics[transformed_metric] = literal_eval(
                    str(td_node_metrics[transformed_metric]))

            if td_node_metrics['eras_stakers']:
                transformed_value = literal_eval(
                    str(td_node_metrics['eras_stakers']['total']))
                if transformed_value and token_decimals:
                    transformed_value = round(transformed_value /
                                              (10 ** token_decimals), 2)
                td_node_metrics['eras_stakers']['total'] = transformed_value

                transformed_value = literal_eval(
                    str(td_node_metrics['eras_stakers']['own']))
                if transformed_value and token_decimals:
                    transformed_value = round(transformed_value /
                                              (10 ** token_decimals), 2)
                td_node_metrics['eras_stakers']['own'] = transformed_value

                if td_node_metrics['eras_stakers']['others']:
                    for entry in td_node_metrics['eras_stakers']['others']:
                        transformed_value = literal_eval(str(entry['value']))
                        if transformed_value and token_decimals:
                            transformed_value = round(transformed_value /
                                                      (10 ** token_decimals), 2)
                        entry['value'] = transformed_value

            if td_node_metrics['historical'] and token_decimals:
                for block in td_node_metrics['historical']:
                    block['slashed_amount'] = round(block['slashed_amount'] /
                                                    (10 ** token_decimals), 2)

            del td_node_metrics['system_properties']
            # Transform the meta_data by deleting the monitor_name and changing
            # the time key to last_monitored key
            del td_meta_data['monitor_name']
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']
            td_meta_data['token_symbol'] = token_symbol
            td_node_metrics['went_down_at'] = None
        elif 'error' in websocket_data:
            meta_data = websocket_data['error']['meta_data']
            error_code = websocket_data['error']['code']
            node_id = meta_data['node_id']
            node_name = meta_data['node_name']
            time_of_error = meta_data['time']
            node: SubstrateNode = self.state[node_id]
            downtime_exception = NodeIsDownException(node_name)

            # In case of non-downtime errors only remove the monitor_name from
            # the meta data
            transformed_data = copy.deepcopy(websocket_data)
            del transformed_data['error']['meta_data']['monitor_name']

            # If we have a downtime error, set went_down_at_websocket to
            # the time of error if the interface was up. Otherwise, leave
            # went_down_at_websocket as stored in the node state
            if error_code == downtime_exception.code:
                transformed_data['error']['data'] = {}
                td_metrics = transformed_data['error']['data']
                td_metrics['went_down_at'] = (
                    node.went_down_at_websocket if node.is_down_websocket
                    else time_of_error
                )
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _transform_websocket_data".format(self))

        return transformed_data

    def _update_websocket_state(self, websocket_data: Dict) -> None:
        if 'result' in websocket_data:
            meta_data = websocket_data['result']['meta_data']
            metrics = websocket_data['result']['data']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            node: SubstrateNode = self.state[node_id]

            # Set node details just in case the configs have changed, and the
            # new metrics
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)
            node.set_best_height(metrics['best_height'])
            node.set_target_height(metrics['target_height'])
            node.set_finalized_height(metrics['finalized_height'])
            node.set_current_session(metrics['current_session'])
            node.set_current_era(metrics['current_era'])
            node.set_authored_blocks(metrics['authored_blocks'])
            node.set_active(metrics['active'])
            node.set_elected(metrics['elected'])
            node.set_disabled(metrics['disabled'])
            node.set_eras_stakers(metrics['eras_stakers'])
            node.set_sent_heartbeat(metrics['sent_heartbeat'])
            node.set_controller_address(metrics['controller_address'])
            node.set_history_depth_eras(metrics['history_depth_eras'])
            node.set_unclaimed_rewards(metrics['unclaimed_rewards'])
            node.set_claimed_rewards(metrics['claimed_rewards'])
            node.set_previous_era_rewards(metrics['previous_era_rewards'])
            node.set_historical(metrics['historical'])
            node.set_last_monitored_websocket(meta_data['last_monitored'])
            node.set_token_symbol(meta_data['token_symbol'])
            node.set_websocket_as_up()
        elif 'error' in websocket_data:
            meta_data = websocket_data['error']['meta_data']
            error_code = websocket_data['error']['code']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']
            node_name = meta_data['node_name']
            downtime_exception = NodeIsDownException(node_name)
            node: SubstrateNode = self.state[node_id]

            # Set node details just in case the configs have changed
            node.set_parent_id(parent_id)
            node.set_node_name(node_name)

            if error_code == downtime_exception.code:
                new_went_down_at = websocket_data['error']['data'][
                    'went_down_at']
                node.set_websocket_as_down(new_went_down_at)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _update_prometheus_state".format(self))

    def _update_state(self, transformed_data: Dict) -> None:
        self.logger.debug("Updating state ...")
        processing_performed = False
        update_helper = {
            'websocket': self._update_websocket_state,
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

    def _process_transformed_websocket_data_for_alerting(
            self, transformed_websocket_data: Dict) -> Dict:
        if 'result' in transformed_websocket_data:
            td_meta_data = transformed_websocket_data['result']['meta_data']
            td_node_id = td_meta_data['node_id']
            node: SubstrateNode = self.state[td_node_id]
            td_metrics = transformed_websocket_data['result']['data']

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
            pd_data['went_down_at']['previous'] = node.went_down_at_websocket
            pd_data['best_height']['previous'] = node.best_height
            pd_data['target_height']['previous'] = node.target_height
            pd_data['finalized_height']['previous'] = node.finalized_height
            pd_data['current_session']['previous'] = node.current_session
            pd_data['current_era']['previous'] = node.current_era
            pd_data['authored_blocks']['previous'] = node.authored_blocks
            pd_data['active']['previous'] = node.active
            pd_data['elected']['previous'] = node.elected
            pd_data['disabled']['previous'] = node.disabled
            pd_data['eras_stakers']['previous'] = node.eras_stakers
            pd_data['sent_heartbeat']['previous'] = node.sent_heartbeat
            pd_data['controller_address']['previous'] = node.controller_address
            pd_data['history_depth_eras']['previous'] = node.history_depth_eras
            pd_data['unclaimed_rewards']['previous'] = node.unclaimed_rewards
            pd_data['claimed_rewards']['previous'] = node.claimed_rewards
            pd_data['previous_era_rewards'][
                'previous'] = node.previous_era_rewards
            pd_data['historical']['previous'] = node.historical
        elif 'error' in transformed_websocket_data:
            td_meta_data = transformed_websocket_data['error']['meta_data']
            td_error_code = transformed_websocket_data['error']['code']
            td_node_id = td_meta_data['node_id']
            td_node_name = td_meta_data['node_name']
            node: SubstrateNode = self.state[td_node_id]
            downtime_exception = NodeIsDownException(td_node_name)

            processed_data = copy.deepcopy(transformed_websocket_data)
            if td_error_code == downtime_exception.code:
                td_data = transformed_websocket_data['error']['data']
                pd_data = processed_data['error']['data']

                for metric, value in td_data.items():
                    pd_data[metric] = {}
                    pd_data[metric]['current'] = value

                pd_data['went_down_at'][
                    'previous'] = node.went_down_at_websocket
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_websocket_data_for_alerting".format(
                    self))

        return processed_data

    def _process_transformed_data_for_saving(
            self, transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for storage ...")
        processing_performed = False

        # We must check that the source's data is valid
        for source in VALID_SUBSTRATE_NODE_SOURCES:
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

    def _process_transformed_data_for_alerting(
            self, transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for alerting ...")
        processing_performed = False
        processing_helper = {
            'websocket': self._process_transformed_websocket_data_for_alerting,
        }
        processed_data = {
            'websocket': {},
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

    def _transform_data(self, data: Dict) -> Tuple[Dict, Dict, Dict]:
        self.logger.debug("Performing data transformation on %s ...", data)
        processing_performed = False
        transformation_helper = {
            'websocket': self._transform_websocket_data,
        }
        transformed_data = {
            'websocket': {},
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
                            SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

        self._push_to_queue(data_for_saving, STORE_EXCHANGE,
                            SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY,
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
        if set(raw_data.keys()) != set(VALID_SUBSTRATE_NODE_SOURCES):
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
                new_node = SubstrateNode(node_name, node_id, node_parent_id)
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
