import json
import logging
from datetime import datetime
from typing import Dict

import pika

from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.mongo import REPLICA_SET_HOSTS, REPLICA_SET_NAME
from src.utils.constants.rabbitmq import (
    STORE_EXCHANGE, TOPIC, COSMOS_NODE_STORE_INPUT_QUEUE_NAME,
    COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  NodeIsDownException)

class CosmosNodeStore(Store):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(name, logger, rabbitmq)
        self._mongo = MongoApi(logger=self.logger.getChild(MongoApi.__name__),
                               db_name=self.mongo_db, host=REPLICA_SET_HOSTS,
                               replicaSet=REPLICA_SET_NAME)

    def _initialise_rabbitmq(self) -> None:
        """
        Initialise the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates a store exchange of type `topic`
        Declares a queue named `cosmos_node_store_input_queue` and binds it
        to the store exchange with a routing key
        `transformed_data.node.cosmos` meaning anything coming from the
        transformer with regards to a cosmos node will be received here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(COSMOS_NODE_STORE_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(
            queue=COSMOS_NODE_STORE_INPUT_QUEUE_NAME, exchange=STORE_EXCHANGE,
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=COSMOS_NODE_STORE_INPUT_QUEUE_NAME,
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
            'prometheus': {
                'result': self._process_redis_prometheus_result_store,
                'error': self._process_redis_prometheus_error_store,
            },
            'tendermint_rpc': {
                'result': self._process_redis_tendermint_rpc_result_store,
                'error': self._process_redis_tendermint_rpc_error_store,
            },
            'cosmos_rest': {
                'result': self._process_redis_cosmos_rest_result_store,
                'error': self._process_redis_cosmos_rest_error_store,
            }
        }
        transformed_data_processing_helper(self.name, configuration, data)

    def _process_redis_prometheus_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.logger.debug(
            "Saving %s state: _went_down_at=%s, "
            "_current_height=%s _voting_power=%s "
            " _last_monitored=%s",
            node_name, metrics['went_down_at'],
            metrics['current_height'], metrics['voting_power'],
            meta_data['last_monitored']
        )

        self.redis.hset_multiple(
            Keys.get_hash_parent(parent_id),
            {
                Keys.get_cosmos_node_went_down_at_prometheus(
                    node_id): str(metrics['went_down_at']),
                Keys.get_cosmos_node_current_height(
                    node_id): str(metrics['current_height']),
                Keys.get_cosmos_node_voting_power(node_id):
                    str(metrics['voting_power']),
                Keys.get_cosmos_node_last_monitored_prometheus(node_id):
                    str(meta_data['last_monitored']),
            })

    def _process_redis_prometheus_error_store(self, data: Dict) -> None:
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
                Keys.get_cosmos_node_went_down_at_prometheus(node_id):
                    str(metrics['went_down_at']),
            })

    def _process_redis_cosmos_rest_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.logger.debug(
            "Saving %s state: _went_down_at=%s, "
            "_bond_status=%s _jailed=%s _last_monitored=%s", node_name,
            metrics['went_down_at'], metrics['bond_status'], metrics['jailed'],
            meta_data['last_monitored']
        )

        self.redis.hset_multiple(
            Keys.get_hash_parent(parent_id),
            {
                Keys.get_cosmos_node_went_down_at_cosmos_rest(
                    node_id): str(metrics['went_down_at']),
                Keys.get_cosmos_node_bond_status(node_id):
                    str(metrics['bond_status']),
                Keys.get_cosmos_node_jailed(node_id):
                    str(metrics['jailed']),
                Keys.get_cosmos_node_last_monitored_cosmos_rest(node_id):
                    str(meta_data['last_monitored']),
            })

    def _process_redis_cosmos_rest_error_store(self, data: Dict) -> None:
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
                Keys.get_cosmos_node_went_down_at_cosmos_rest(node_id):
                    str(metrics['went_down_at']),
            })

    def _process_redis_tendermint_rpc_error_store(self, data: Dict) -> None:
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
                Keys.get_cosmos_node_went_down_at_tendermint_rpc(node_id):
                    str(metrics['went_down_at']),
            })

    def _process_redis_tendermint_rpc_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.logger.debug(
            "Saving %s state: _went_down_at=%s, "
            "_slashed=%s _missed_blocks=%s _is_syncing=%s"
            "_last_monitored=%s ", node_name,
            metrics['went_down_at'], metrics['slashed'],
            metrics['missed_blocks'], metrics['is_syncing'],
            meta_data['last_monitored'],
        )

        self.redis.hset_multiple(
            Keys.get_hash_parent(parent_id),
            {
                Keys.get_cosmos_node_went_down_at_tendermint_rpc(
                    node_id): str(metrics['went_down_at']),
                Keys.get_cosmos_node_is_syncing(node_id):
                    str(metrics['is_syncing']),
                Keys.get_cosmos_node_is_peered(node_id):
                    "" if ('is_peered_with_sentinel' not in metrics) else str(metrics['is_peered_with_sentinel']),
                Keys.get_cosmos_node_slashed(node_id):
                    json.dumps(metrics['slashed']),
                Keys.get_cosmos_node_missed_blocks(
                    node_id):
                    json.dumps(metrics['missed_blocks']),
                Keys.get_cosmos_node_last_monitored_tendermint_rpc(node_id):
                    str(meta_data['last_monitored']),
            })

    def _process_mongo_store(self, data: Dict) -> None:
        configuration = {
            'prometheus': {
                'result': self._process_mongo_prometheus_result_store,
                'error': self._process_mongo_prometheus_error_store,
            },
            'tendermint_rpc': {
                'result': self._process_mongo_tendermint_rpc_result_store,
                'error': self._process_mongo_tendermint_rpc_error_store,
            },
            'cosmos_rest': {
                'result': self._process_mongo_cosmos_rest_result_store,
                'error': self._process_mongo_cosmos_rest_error_store,
            }
        }
        transformed_data_processing_helper(self.name, configuration, data)

    def _process_mongo_prometheus_result_store(self, data: Dict) -> None:
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
                        'went_down_at_prometheus': str(metrics['went_down_at']),
                        'voting_power': str(metrics['voting_power']),
                        'timestamp': meta_data['last_monitored'],
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )

    def _process_mongo_prometheus_error_store(self, data: Dict) -> None:
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
                            'went_down_at_prometheus':
                                str(metrics['went_down_at']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )

    def _process_mongo_tendermint_rpc_result_store(self, data: Dict) -> None:
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
                        'went_down_at_tendermint_rpc': str(
                            metrics['went_down_at']),
                        'is_syncing': str(metrics['is_syncing']),
                        'is_peered_with_sentinel': "" if ('is_peered_with_sentinel' not in metrics) else str(metrics['is_peered_with_sentinel']),
                        'slashed': json.dumps(metrics['slashed']),
                        'missed_blocks': json.dumps(metrics['missed_blocks']),
                        'timestamp': meta_data['last_monitored'],
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )

    def _process_mongo_tendermint_rpc_error_store(self, data: Dict) -> None:
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
                            'went_down_at_tendermint_rpc':
                                str(metrics['went_down_at']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )

    def _process_mongo_cosmos_rest_result_store(self, data: Dict) -> None:
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
                        'went_down_at_cosmos_rest': str(
                            metrics['went_down_at']),
                        'bond_status': str(metrics['bond_status']),
                        'jailed': str(metrics['jailed']),
                        'timestamp': meta_data['last_monitored'],
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )

    def _process_mongo_cosmos_rest_error_store(self, data: Dict) -> None:
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
                            'went_down_at_cosmos_rest':
                                str(metrics['went_down_at']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
