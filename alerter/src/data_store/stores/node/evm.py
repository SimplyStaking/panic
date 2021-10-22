import json
import logging
from datetime import datetime
from typing import Dict

import pika

from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.rabbitmq import (STORE_EXCHANGE, TOPIC,
                                          EVM_NODE_STORE_INPUT_QUEUE_NAME,
                                          EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
                                          HEALTH_CHECK_EXCHANGE)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  NodeIsDownException,
                                  ReceivedUnexpectedDataException)


class EVMNodeStore(Store):
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
        Declares a queue named `evm_node_store_input_queue` and binds it
        to the store exchange with a routing key
        `transformed_data.node.evm` meaning anything coming from the
        transformer with regards to evm node data will be received here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(EVM_NODE_STORE_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(
            queue=EVM_NODE_STORE_INPUT_QUEUE_NAME, exchange=STORE_EXCHANGE,
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=EVM_NODE_STORE_INPUT_QUEUE_NAME,
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
        if 'result' in data:
            self._process_redis_result_store(data['result'])
        elif 'error' in data:
            self._process_redis_error_store(data['error'])
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_redis_store".format(self))

    def _process_redis_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.logger.debug(
            "Saving %s state: _current_height=%s, _syncing=%s, "
            "_last_monitored=%s, _went_down_at=%s", node_name,
            metrics['current_height'], metrics['syncing'],
            meta_data['last_monitored'],
            metrics['went_down_at'])

        self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
            Keys.get_evm_node_current_height(node_id):
                str(metrics['current_height']),
            Keys.get_evm_node_syncing(node_id):
                str(metrics['syncing']),
            Keys.get_evm_node_went_down_at(node_id): str(
                metrics['went_down_at']),
            Keys.get_evm_node_last_monitored(node_id):
                str(meta_data['last_monitored'])
        })

    def _process_redis_error_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        error_code = data['code']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        downtime_exception = NodeIsDownException(node_name)

        if error_code == downtime_exception.code:
            metrics = data['data']
            self.logger.debug(
                "Saving %s state: _went_down_at=%s", node_name,
                metrics['went_down_at']
            )

            self.redis.hset(
                Keys.get_hash_parent(parent_id),
                Keys.get_evm_node_went_down_at(node_id), str(metrics[
                                                                 'went_down_at'])
            )

    def _process_mongo_store(self, data: Dict) -> None:
        if 'result' in data:
            self._process_mongo_result_store(data['result'])
        elif 'error' in data:
            self._process_mongo_error_store(data['error'])
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_mongo_store".format(self))

    def _process_mongo_result_store(self, data: Dict) -> None:
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
                        'current_height': str(metrics['current_height']),
                        'syncing': str(metrics['syncing']),
                        'went_down_at': str(metrics['went_down_at']),
                        'timestamp': meta_data['last_monitored'],
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )

    def _process_mongo_error_store(self, data: Dict) -> None:
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
                            'went_down_at': str(metrics['went_down_at']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
