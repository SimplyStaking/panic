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
                                          CL_NODE_STORE_INPUT_QUEUE_NAME,
                                          CL_NODE_TRANSFORMED_DATA_ROUTING_KEY,
                                          HEALTH_CHECK_EXCHANGE)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  NodeIsDownException)


class ChainlinkNodeStore(Store):
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
        Declares a queue named `chainlink_node_store_input_queue` and binds it
        to the store exchange with a routing key
        `transformed_data.node.chainlink` meaning anything coming from the
        transformer with regards to a chainlink node will be received here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(CL_NODE_STORE_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(
            queue=CL_NODE_STORE_INPUT_QUEUE_NAME, exchange=STORE_EXCHANGE,
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=CL_NODE_STORE_INPUT_QUEUE_NAME,
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
            "Saving %s state: _current_height=%s, "
            "_total_block_headers_received=%s, "
            "_max_pending_tx_delay=%s, _process_start_time_seconds=%s, "
            "_total_gas_bumps=%s, _total_gas_bumps_exceeds_limit=%s, "
            "_no_of_unconfirmed_txs=%s, _total_errored_job_runs=%s, "
            "_current_gas_price_info=%s, _balance_info=%s, "
            "_last_monitored_prometheus=%s, _last_prometheus_source_used=%s, "
            "_went_down_at_prometheus=%s", node_name, metrics['current_height'],
            metrics['total_block_headers_received'],
            metrics['max_pending_tx_delay'],
            metrics['process_start_time_seconds'], metrics['total_gas_bumps'],
            metrics['total_gas_bumps_exceeds_limit'],
            metrics['no_of_unconfirmed_txs'], metrics['total_errored_job_runs'],
            metrics['current_gas_price_info'], metrics['balance_info'],
            meta_data['last_monitored'], meta_data['last_source_used'],
            metrics['went_down_at'])

        self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
            Keys.get_cl_node_went_down_at_prometheus(node_id): str(
                metrics['went_down_at']),
            Keys.get_cl_node_current_height(node_id):
                str(metrics['current_height']),
            Keys.get_cl_node_total_block_headers_received(node_id):
                str(metrics['total_block_headers_received']),
            Keys.get_cl_node_max_pending_tx_delay(node_id):
                str(metrics['max_pending_tx_delay']),
            Keys.get_cl_node_process_start_time_seconds(node_id):
                str(metrics['process_start_time_seconds']),
            Keys.get_cl_node_total_gas_bumps(node_id):
                str(metrics['total_gas_bumps']),
            Keys.get_cl_node_total_gas_bumps_exceeds_limit(node_id):
                str(metrics['total_gas_bumps_exceeds_limit']),
            Keys.get_cl_node_no_of_unconfirmed_txs(node_id):
                str(metrics['no_of_unconfirmed_txs']),
            Keys.get_cl_node_total_errored_job_runs(node_id):
                str(metrics['total_errored_job_runs']),
            Keys.get_cl_node_current_gas_price_info(node_id):
                'None' if metrics['current_gas_price_info'] is None
                else json.dumps(metrics['current_gas_price_info']),
            Keys.get_cl_node_balance_info(node_id):
                json.dumps(metrics['balance_info']),
            Keys.get_cl_node_last_prometheus_source_used(node_id):
                str(meta_data['last_source_used']),
            Keys.get_cl_node_last_monitored_prometheus(node_id):
                str(meta_data['last_monitored'])
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
                "Saving %s state: _went_down_at=%s, "
                "_last_prometheus_source_used=%s", node_name,
                metrics['went_down_at'], meta_data['last_source_used']
            )

            self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
                Keys.get_cl_node_went_down_at_prometheus(node_id): str(
                    metrics['went_down_at']),
                Keys.get_cl_node_last_prometheus_source_used(node_id):
                    str(meta_data['last_source_used']),
            })
        else:
            self.logger.debug(
                "Saving %s state: _last_prometheus_source_used=%s", node_name,
                meta_data['last_source_used']
            )

            self.redis.hset(
                Keys.get_hash_parent(parent_id),
                Keys.get_cl_node_last_prometheus_source_used(node_id),
                str(meta_data['last_source_used']),
            )

    def _process_mongo_store(self, data: Dict) -> None:
        configuration = {
            'prometheus': {
                'result': self._process_mongo_prometheus_result_store,
                'error': self._process_mongo_prometheus_error_store,
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
                        'total_block_headers_received': str(
                            metrics['total_block_headers_received']),
                        'max_pending_tx_delay': str(
                            metrics['max_pending_tx_delay']),
                        'process_start_time_seconds': str(
                            metrics['process_start_time_seconds']),
                        'total_gas_bumps': str(metrics['total_gas_bumps']),
                        'total_gas_bumps_exceeds_limit': str(
                            metrics['total_gas_bumps_exceeds_limit']),
                        'no_of_unconfirmed_txs': str(
                            metrics['no_of_unconfirmed_txs']),
                        'total_errored_job_runs': str(
                            metrics['total_errored_job_runs']),
                        'current_gas_price_info':
                            'None' if metrics['current_gas_price_info'] is None
                            else json.dumps(metrics['current_gas_price_info']),
                        'balance_info':
                            json.dumps(metrics['balance_info']),
                        'went_down_at_prometheus': str(metrics['went_down_at']),
                        'last_prometheus_source_used':
                            str(meta_data['last_source_used']),
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
                            'last_prometheus_source_used':
                                str(meta_data['last_source_used']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
        else:
            self.mongo.update_one(
                parent_id,
                {'doc_type': 'node', 'd': time_now.hour},
                {
                    '$push': {
                        node_id: {
                            'last_prometheus_source_used':
                                str(meta_data['last_source_used']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
