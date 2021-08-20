import logging

from src.data_store.redis.redis_api import RedisApi
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, STORE_EXCHANGE, RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    TOPIC, EVM_CONTRACTS_DT_INPUT_QUEUE_NAME,
    EVM_CONTRACTS_RAW_DATA_ROUTING_KEY)


class EVMContractsDataTransformer(DataTransformer):
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
        self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         EVM_CONTRACTS_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(EVM_CONTRACTS_DT_INPUT_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", EVM_CONTRACTS_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE, EVM_CONTRACTS_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(EVM_CONTRACTS_DT_INPUT_QUEUE_NAME,
                                 RAW_DATA_EXCHANGE,
                                 EVM_CONTRACTS_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(EVM_CONTRACTS_DT_INPUT_QUEUE_NAME,
                                    self._process_raw_data, False, False, None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", STORE_EXCHANGE)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    # TODO: Need to cater for version upgrades, if version changes change state
    #     : although proxy never changes. Monday continue from below.
    #
    # def _load_number_state(self, state_type: Union[Type[float], Type[int]],
    #                        evm_node: Monitorable) -> None:
    #     """
    #     This function will attempt to load a node's number metrics from redis.
    #     If the data from Redis cannot be obtained, the state won't be updated.
    #     :param state_type: What type of number metrics we want to obtain
    #     :param evm_node: The node in question
    #     :return: Nothing
    #     """
    #     redis_hash = Keys.get_hash_parent(evm_node.parent_id)
    #     evm_node_id = evm_node.node_id
    #     if state_type == int:
    #         metric_attributes = evm_node.get_int_metric_attributes()
    #         convert_fn = convert_to_int
    #     else:
    #         metric_attributes = evm_node.get_float_metric_attributes()
    #         convert_fn = convert_to_float
    #
    #     # We iterate over the number metric attributes and attempt to load from
    #     # redis. We are saving metrics in the following format b"value", so
    #     # first we need to decode, and then convert to int/float. Note, since
    #     # an error may occur when obtaining the data, the default value must
    #     # also be passed as bytes(str()).
    #     for attribute in metric_attributes:
    #         state_value = eval('evm_node.' + attribute)
    #         redis_key = eval('Keys.get_evm_node_' + attribute + '(evm_node_id)')
    #         default_value = bytes(str(state_value), 'utf-8')
    #         redis_value = self.redis.hget(redis_hash, redis_key, default_value)
    #         processed_redis_value = 'None' if redis_value is None \
    #             else redis_value.decode("utf-8")
    #         new_value = convert_fn(processed_redis_value, None)
    #         eval("evm_node.set_" + attribute + '(new_value)')
    #
    # def load_state(self, evm_node: Monitorable) -> Monitorable:
    #     """
    #     This function attempts to load the state of an evm_node from redis. If
    #     the data from Redis cannot be obtained, the state won't be updated.
    #     :param evm_node: The EVM Node whose state we are interested in
    #     :return: The loaded EVM node
    #     """
    #     self.logger.debug("Loading the state of %s from Redis", evm_node)
    #
    #     self._load_number_state(int, evm_node)
    #     self._load_number_state(float, evm_node)
    #
    #     self.logger.debug(
    #         "Restored %s state: _current_height=%s, _last_monitored=%s, "
    #         "_went_down_at=%s", evm_node, evm_node.current_height,
    #         evm_node.last_monitored, evm_node.went_down_at)
    #
    #     return evm_node
    #
    # def _update_state(self, transformed_data: Dict) -> None:
    #     self.logger.debug("Updating state ...")
    #
    #     if 'result' in transformed_data:
    #         meta_data = transformed_data['result']['meta_data']
    #         metrics = transformed_data['result']['data']
    #         node_id = meta_data['node_id']
    #         parent_id = meta_data['node_parent_id']
    #         node_name = meta_data['node_name']
    #         node = self.state[node_id]
    #
    #         # Set node details just in case the configs have changed
    #         node.set_parent_id(parent_id)
    #         node.set_node_name(node_name)
    #
    #         # Save the new metrics in process memory
    #         node.set_last_monitored(meta_data['last_monitored'])
    #         node.set_current_height(metrics['current_height'])
    #         node.set_as_up()
    #     elif 'error' in transformed_data:
    #         meta_data = transformed_data['error']['meta_data']
    #         error_code = transformed_data['error']['code']
    #         node_name = meta_data['node_name']
    #         node_id = meta_data['node_id']
    #         parent_id = meta_data['node_parent_id']
    #         downtime_exception = NodeIsDownException(node_name)
    #         node = self.state[node_id]
    #
    #         # Set node details just in case the configs have changed
    #         node.set_parent_id(parent_id)
    #         node.set_node_name(node_name)
    #
    #         if error_code == downtime_exception.code:
    #             went_down_at = transformed_data['error']['data']['went_down_at']
    #             node.set_as_down(went_down_at)
    #     else:
    #         raise ReceivedUnexpectedDataException(
    #             "{}: _update_state".format(self))
    #
    #     self.logger.debug("State updated successfully")
    #
    # def _process_transformed_data_for_saving(self,
    #                                          transformed_data: Dict) -> Dict:
    #     self.logger.debug("Performing further processing for storage ...")
    #
    #     if 'result' in transformed_data or 'error' in transformed_data:
    #         processed_data = copy.deepcopy(transformed_data)
    #     else:
    #         raise ReceivedUnexpectedDataException(
    #             "{}: _process_transformed_data_for_saving".format(self))
    #
    #     self.logger.debug("Processing successful")
    #
    #     return processed_data
    #
    # def _process_transformed_data_for_alerting(self,
    #                                            transformed_data: Dict) -> Dict:
    #     self.logger.debug("Performing further processing for alerting ...")
    #
    #     if 'result' in transformed_data:
    #         td_meta_data = transformed_data['result']['meta_data']
    #         td_node_id = td_meta_data['node_id']
    #         node = self.state[td_node_id]
    #         td_metrics = transformed_data['result']['data']
    #
    #         processed_data = {
    #             'result': {
    #                 'meta_data': copy.deepcopy(td_meta_data),
    #                 'data': {}
    #             }
    #         }
    #
    #         # Reformat the data in such a way that both the previous and current
    #         # states are sent to the alerter
    #         processed_data_metrics = processed_data['result']['data']
    #         for metric, value in td_metrics.items():
    #             processed_data_metrics[metric] = {}
    #             processed_data_metrics[metric]['current'] = value
    #
    #         processed_data_metrics['current_height'][
    #             'previous'] = node.current_height
    #         processed_data_metrics['went_down_at'][
    #             'previous'] = node.went_down_at
    #     elif 'error' in transformed_data:
    #         td_meta_data = transformed_data['error']['meta_data']
    #         td_error_code = transformed_data['error']['code']
    #         td_node_id = td_meta_data['node_id']
    #         td_node_name = td_meta_data['node_name']
    #         node = self.state[td_node_id]
    #         downtime_exception = NodeIsDownException(td_node_name)
    #
    #         processed_data = copy.deepcopy(transformed_data)
    #
    #         if td_error_code == downtime_exception.code:
    #             td_metrics = transformed_data['error']['data']
    #             processed_data_metrics = processed_data['error']['data']
    #
    #             for metric, value in td_metrics.items():
    #                 processed_data_metrics[metric] = {}
    #                 processed_data_metrics[metric]['current'] = value
    #
    #             processed_data_metrics['went_down_at'][
    #                 'previous'] = node.went_down_at
    #     else:
    #         raise ReceivedUnexpectedDataException(
    #             "{}: _process_transformed_data_for_alerting".format(self))
    #
    #     self.logger.debug("Processing successful.")
    #
    #     return processed_data
    #
    # def _transform_data(self, data: Dict) -> Tuple[Dict, Dict, Dict]:
    #     self.logger.debug("Performing data transformation on %s ...", data)
    #
    #     if 'result' in data:
    #         meta_data = data['result']['meta_data']
    #         transformed_data = copy.deepcopy(data)
    #         td_meta_data = transformed_data['result']['meta_data']
    #         td_metrics = transformed_data['result']['data']
    #
    #         # Transform the meta_data by deleting the monitor_name and changing
    #         # the time key to last_monitored key. Also set went_down_at as None
    #         # because data was successfully retrieved
    #         del td_meta_data['monitor_name']
    #         del td_meta_data['time']
    #         td_meta_data['last_monitored'] = meta_data['time']
    #         td_metrics['went_down_at'] = None
    #     elif 'error' in data:
    #         meta_data = data['error']['meta_data']
    #         error_code = data['error']['code']
    #         node_id = meta_data['node_id']
    #         node_name = meta_data['node_name']
    #         time_of_error = meta_data['time']
    #         node = self.state[node_id]
    #         downtime_exception = NodeIsDownException(node_name)
    #
    #         # In case of errors in the sent messages only remove the
    #         # monitor_name from the meta data
    #         transformed_data = copy.deepcopy(data)
    #         del transformed_data['error']['meta_data']['monitor_name']
    #
    #         # If we have a downtime error, set went_down_at to the time of error
    #         # if the system was up. Otherwise, leave went_down_at as stored in
    #         # the system state
    #         if error_code == downtime_exception.code:
    #             transformed_data['error']['data'] = {}
    #             td_metrics = transformed_data['error']['data']
    #             td_metrics['went_down_at'] = \
    #                 node.went_down_at if node.is_down else time_of_error
    #     else:
    #         raise ReceivedUnexpectedDataException(
    #             "{}: _transform_data".format(self))
    #
    #     data_for_alerting = self._process_transformed_data_for_alerting(
    #         transformed_data)
    #     data_for_saving = self._process_transformed_data_for_saving(
    #         transformed_data)
    #
    #     self.logger.debug("Data transformation successful")
    #
    #     return transformed_data, data_for_alerting, data_for_saving
    #
    # def _place_latest_data_on_queue(
    #         self, transformed_data: Dict, data_for_alerting: Dict,
    #         data_for_saving: Dict) -> None:
    #     self._push_to_queue(data_for_alerting, ALERT_EXCHANGE,
    #                         EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    #                         pika.BasicProperties(delivery_mode=2), True)
    #
    #     self._push_to_queue(data_for_saving, STORE_EXCHANGE,
    #                         EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    #                         pika.BasicProperties(delivery_mode=2), True)
    #
    # def _process_raw_data(
    #         self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
    #         properties: pika.spec.BasicProperties, body: bytes) -> None:
    #     raw_data = json.loads(body)
    #     self.logger.debug("Received %s from monitors. Now processing this "
    #                       "data.", raw_data)
    #
    #     processing_error = False
    #     transformed_data = {}
    #     data_for_alerting = {}
    #     data_for_saving = {}
    #     try:
    #         if 'result' in raw_data or 'error' in raw_data:
    #             response_index_key = \
    #                 'result' if 'result' in raw_data else 'error'
    #             meta_data = raw_data[response_index_key]['meta_data']
    #             node_id = meta_data['node_id']
    #             node_parent_id = meta_data['node_parent_id']
    #             node_name = meta_data['node_name']
    #
    #             if node_id not in self.state:
    #                 new_node = EVMNode(node_name, node_id, node_parent_id)
    #                 loaded_node = self.load_state(new_node)
    #                 self._state[node_id] = loaded_node
    #
    #             transformed_data, data_for_alerting, data_for_saving = \
    #                 self._transform_data(raw_data)
    #         else:
    #             raise ReceivedUnexpectedDataException(
    #                 "{}: _process_raw_data".format(self))
    #     except Exception as e:
    #         self.logger.error("Error when processing %s", raw_data)
    #         self.logger.exception(e)
    #         processing_error = True
    #
    #     # If the data is processed, it can be acknowledged.
    #     self.rabbitmq.basic_ack(method.delivery_tag, False)
    #
    #     # We want to update the state after the data is acknowledged, otherwise
    #     # if acknowledgement fails the state would be erroneous when processing
    #     # the data again. Note, only update the state if there were no
    #     # processing errors.
    #     if not processing_error:
    #         try:
    #             self._update_state(transformed_data)
    #             self.logger.debug("Successfully processed %s", raw_data)
    #         except Exception as e:
    #             self.logger.error("Error when processing %s", raw_data)
    #             self.logger.exception(e)
    #             processing_error = True
    #
    #     # Place the data on the publishing queue if there were no processing
    #     # errors. This is done after acknowledging the data, so that if
    #     # acknowledgement fails, the data is processed again and we do not have
    #     # duplication of data in the queue
    #     if not processing_error:
    #         self._place_latest_data_on_queue(
    #             transformed_data, data_for_alerting, data_for_saving)
    #
    #     # Send any data waiting in the publisher queue, if any
    #     try:
    #         self._send_data()
    #
    #         if not processing_error:
    #             heartbeat = {
    #                 'component_name': self.transformer_name,
    #                 'is_alive': True,
    #                 'timestamp': datetime.now().timestamp()
    #             }
    #             self._send_heartbeat(heartbeat)
    #     except MessageWasNotDeliveredException as e:
    #         # Log the message and do not raise it as message is residing in the
    #         # publisher queue.
    #         self.logger.exception(e)
    #     except Exception as e:
    #         # For any other exception raise it.
    #         raise e