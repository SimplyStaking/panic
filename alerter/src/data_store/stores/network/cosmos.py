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
    STORE_EXCHANGE, TOPIC, COSMOS_NETWORK_STORE_INPUT_QUEUE_NAME,
    COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import MessageWasNotDeliveredException


class CosmosNetworkStore(Store):
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
        Declares a queue named `cosmos_network_store_input_queue` and binds it
        to the store exchange with a routing key
        `transformed_data.network.cosmos` meaning anything coming from the
        transformer with regards to a cosmos network will be received here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(COSMOS_NETWORK_STORE_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(
            queue=COSMOS_NETWORK_STORE_INPUT_QUEUE_NAME,
            exchange=STORE_EXCHANGE,
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=COSMOS_NETWORK_STORE_INPUT_QUEUE_NAME,
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
        network_data = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.",
                          network_data)

        processing_error = False
        try:
            self._process_redis_store(network_data)
            self._process_mongo_store(network_data)
        except Exception as e:
            self.logger.error("Error when processing %s", network_data)
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
            'cosmos_rest': {
                'result': self._process_redis_cosmos_rest_result_store,
                'error': self._process_redis_cosmos_rest_error_store,
            }
        }
        transformed_data_processing_helper(self.name, configuration, data)

    def _process_redis_cosmos_rest_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        parent_id = meta_data['parent_id']
        chain_name = meta_data['chain_name']
        metrics = data['data']

        self.logger.debug(
            "Saving %s state: _last_monitored=%s, _proposals=%s",
            chain_name, meta_data['last_monitored'], metrics['proposals'],
        )

        self.redis.hset_multiple(
            Keys.get_hash_parent(parent_id),
            {
                Keys.get_cosmos_network_last_monitored_cosmos_rest(
                    parent_id): str(meta_data['last_monitored']),
                Keys.get_cosmos_network_proposals(parent_id):
                    json.dumps(metrics['proposals']),
            })

    def _process_redis_cosmos_rest_error_store(self, data: Dict) -> None:
        pass

    def _process_mongo_store(self, data: Dict) -> None:
        configuration = {
            'cosmos_rest': {
                'result': self._process_mongo_cosmos_rest_result_store,
                'error': self._process_mongo_cosmos_rest_error_store,
            }
        }
        transformed_data_processing_helper(self.name, configuration, data)

    def _process_mongo_cosmos_rest_result_store(self, data: Dict) -> None:
        """
        Updating mongo with network metrics using a time-based document with 60
        entries per hour per network, assuming each network monitoring round is
        60 seconds.

        Collection is the chain ID, a document will keep incrementing with new
        network metrics until it's the next hour at which point mongo will
        create a new document and repeat the process.

        Document type will always be network, as only network metrics are going
        to be stored in this document.

        Timestamp is the time of when these metrics were extracted.

        $inc increments n_entries by one each time an entry is added
        """

        meta_data = data['meta_data']
        parent_id = meta_data['parent_id']
        time_now = datetime.now()
        self.mongo.update_one(
            parent_id,
            {'doc_type': 'network', 'd': time_now.hour},
            {
                '$push': {
                    parent_id: {
                        'last_monitored': meta_data['last_monitored'],
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )

    def _process_mongo_cosmos_rest_error_store(self, data: Dict) -> None:
        pass
