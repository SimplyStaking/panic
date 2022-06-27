import json
import logging
from datetime import datetime
from typing import Dict

import pika

from src.data_store.mongo import MongoApi
from src.data_store.redis import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE, TOPIC,
    SUBSTRATE_NODE_STORE_INPUT_QUEUE_NAME,
    SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY
)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import (
    MessageWasNotDeliveredException, NodeIsDownException)


class SubstrateNodeStore(Store):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(name, logger, rabbitmq)
        self._mongo = MongoApi(logger=self.logger.getChild(MongoApi.__name__),
                               db_name=self.mongo_db, host=self.mongo_ip,
                               port=self.mongo_port)

    def _initialise_rabbitmq(self) -> None:
        """
        Initialise the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates a store exchange of type `topic`
        Declares a queue named `substrate_node_store_input_queue` and binds it
        to the store exchange with a routing key
        `transformed_data.node.substrate` meaning anything coming from the
        transformer with regards to a substrate node will be received here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(SUBSTRATE_NODE_STORE_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(
            queue=SUBSTRATE_NODE_STORE_INPUT_QUEUE_NAME,
            exchange=STORE_EXCHANGE,
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=SUBSTRATE_NODE_STORE_INPUT_QUEUE_NAME,
                                    on_message_callback=self._process_data,
                                    auto_ack=False, exclusive=False,
                                    consumer_tag=None)
        self.rabbitmq.start_consuming()

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        """
        Processes the data being received, from the queue. This data will be
        saved in Mongo and Redis as required. If successful, a heartbeat will be
        sent.
        """
        node_data = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.", node_data)

        processing_error = False
        try:
            self._process_redis_store(node_data)
            self._process_mongo_store(node_data)
        except Exception as e:
            self.logger.error("Error when processing %s", node_data)
            self.logger.exception(e)
            processing_error = True

        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # Send a heartbeat only if there were no errors
        if not processing_error:
            try:
                heartbeat = {
                    'component_name': self.name,
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
            except MessageWasNotDeliveredException as e:
                self.logger.exception(e)
            except Exception as e:
                # For any other exception raise it.
                raise e

    def _process_redis_store(self, data: Dict) -> None:
        configuration = {
            'websocket': {
                'result': self._process_redis_websocket_result_store,
                'error': self._process_redis_websocket_error_store,
            }
        }
        transformed_data_processing_helper(self.name, configuration, data)

    def _process_redis_websocket_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.logger.debug(
            "Saving %s state: _went_down_at=%s, best_height=%s, "
            "target_height=%s, finalized_height=%s, current_session=%s, "
            "current_era=%s, authored_blocks=%s, active=%s, elected=%s, "
            "disabled=%s, eras_stakers=%s, sent_heartbeat=%s, "
            "controller_address=%s, history_depth_eras=%s, "
            "unclaimed_rewards=%s, claimed_rewards=%s, "
            "previous_era_rewards=%s, historical=%s, last_monitored=%s, "
            "token_symbol=%s",
            node_name, metrics['went_down_at'],
            metrics['best_height'], metrics['target_height'],
            metrics['finalized_height'], metrics['current_session'],
            metrics['current_era'], metrics['authored_blocks'],
            metrics['active'], metrics['elected'],
            metrics['disabled'], metrics['eras_stakers'],
            metrics['sent_heartbeat'], metrics['controller_address'],
            metrics['history_depth_eras'], metrics['unclaimed_rewards'],
            metrics['claimed_rewards'], metrics['previous_era_rewards'],
            metrics['historical'], meta_data['last_monitored'],
            meta_data['token_symbol'],
        )

        self.redis.hset_multiple(
            Keys.get_hash_parent(parent_id),
            {
                Keys.get_substrate_node_went_down_at_websocket(
                    node_id): str(metrics['went_down_at']),
                Keys.get_substrate_node_best_height(
                    node_id): str(metrics['best_height']),
                Keys.get_substrate_node_target_height(
                    node_id): str(metrics['target_height']),
                Keys.get_substrate_node_finalized_height(
                    node_id): str(metrics['finalized_height']),
                Keys.get_substrate_node_current_session(
                    node_id): str(metrics['current_session']),
                Keys.get_substrate_node_current_era(
                    node_id): str(metrics['current_era']),
                Keys.get_substrate_node_authored_blocks(
                    node_id): str(metrics['authored_blocks']),
                Keys.get_substrate_node_active(
                    node_id): str(metrics['active']),
                Keys.get_substrate_node_elected(
                    node_id): str(metrics['elected']),
                Keys.get_substrate_node_disabled(
                    node_id): str(metrics['disabled']),
                Keys.get_substrate_node_eras_stakers(
                    node_id): json.dumps(metrics['eras_stakers']),
                Keys.get_substrate_node_sent_heartbeat(
                    node_id): str(metrics['sent_heartbeat']),
                Keys.get_substrate_node_controller_address(
                    node_id): str(metrics['controller_address']),
                Keys.get_substrate_node_history_depth_eras(
                    node_id): str(metrics['history_depth_eras']),
                Keys.get_substrate_node_unclaimed_rewards(
                    node_id): json.dumps(metrics['unclaimed_rewards']),
                Keys.get_substrate_node_claimed_rewards(
                    node_id): json.dumps(metrics['claimed_rewards']),
                Keys.get_substrate_node_previous_era_rewards(
                    node_id): str(metrics['previous_era_rewards']),
                Keys.get_substrate_node_historical(
                    node_id): json.dumps(metrics['historical']),
                Keys.get_substrate_node_last_monitored_websocket(
                    node_id): str(meta_data['last_monitored']),
                Keys.get_substrate_node_token_symbol(
                    node_id): str(meta_data['token_symbol']),
            })

    def _process_redis_websocket_error_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        error_code = data['code']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        downtime_exception = NodeIsDownException(node_name)

        if error_code == downtime_exception.code:
            metrics = data['data']
            self.logger.debug(
                "Saving %s state: _went_down_at=%s ",
                node_name, metrics['went_down_at']
            )

            self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
                Keys.get_substrate_node_went_down_at_websocket(node_id):
                    str(metrics['went_down_at']),
            })

    def _process_mongo_store(self, data: Dict) -> None:
        configuration = {
            'websocket': {
                'result': self._process_mongo_websocket_result_store,
                'error': self._process_mongo_websocket_error_store,
            },
        }
        transformed_data_processing_helper(self.name, configuration, data)

    def _process_mongo_websocket_result_store(self, data: Dict) -> None:
        """
        Updating mongo with node metrics using a time-based document with 360
        entries per hour per node, assuming each node monitoring round is
        10 seconds.

        Collection is the parent identifier of the node, a document will keep
        incrementing with new node metrics until it's the next hour at which
        point mongo will create a new document and repeat the process.

        Document type will always be node, as only node metrics are going to be
        stored in this document.

        Timestamp is the time of when these metrics were extracted.

        $inc increments n_entries by one each time an entry is added
        """

        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']
        time_now = datetime.now()
        self.mongo.update_one(
            parent_id,
            {'doc_type': 'node', 'd': time_now.hour},
            {
                '$push': {
                    node_id: {
                        'went_down_at_websocket': str(metrics['went_down_at']),
                        'best_height': str(metrics['best_height']),
                        'target_height': str(metrics['target_height']),
                        'finalized_height': str(metrics['finalized_height']),
                        'current_session': str(metrics['current_session']),
                        'current_era': str(metrics['current_era']),
                        'authored_blocks': str(metrics['authored_blocks']),
                        'active': str(metrics['active']),
                        'elected': str(metrics['elected']),
                        'disabled': str(metrics['disabled']),
                        'sent_heartbeat': str(metrics['sent_heartbeat']),
                        'controller_address': str(
                            metrics['controller_address']),
                        'claimed_rewards': json.dumps(
                            metrics['claimed_rewards']),
                        'previous_era_rewards': str(
                            metrics['previous_era_rewards']),
                        'timestamp': str(meta_data['last_monitored']),
                        'token_symbol': str(meta_data['token_symbol']),
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )

    def _process_mongo_websocket_error_store(self, data: Dict) -> None:
        """
        Updating mongo with error metrics using a time-based document with 360
        entries per hour per node, assuming each node monitoring round is 10
        seconds.

        Collection is the parent identifier of the node, a document will keep
        incrementing with new node metrics until it's the next hour at which
        point mongo will create a new document and repeat the process.

        Document type will always be node, as only node metrics are going to be
        stored in this document.

        Timestamp is the time of when these metrics were extracted.

        $inc increments n_entries by one each time an entry is added
        """

        meta_data = data['meta_data']
        error_code = data['code']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        time_now = datetime.now()
        downtime_exception = NodeIsDownException(node_name)

        if error_code == downtime_exception.code:
            metrics = data['data']
            self.mongo.update_one(
                parent_id,
                {'doc_type': 'node', 'd': time_now.hour},
                {
                    '$push': {
                        node_id: {
                            'went_down_at_websocket':
                                str(metrics['went_down_at']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
