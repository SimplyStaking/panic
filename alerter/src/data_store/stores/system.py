import json
import logging
from datetime import datetime
from typing import Dict

import pika.exceptions

from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 SYSTEM_STORE_INPUT_QUEUE,
                                 SYSTEM_STORE_INPUT_ROUTING_KEY)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  SystemIsDownException,
                                  MessageWasNotDeliveredException)


class SystemStore(Store):
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

        Creates a store exchange of type `direct`
        Declares a queue named `system_store_queue` and binds it to the store
        exchange with a routing key `transformer.system.*` meaning anything
        coming from the transformer with regards to a system will be received
        here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a
        successful store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type='direct',
                                       passive=False, durable=True,
                                       auto_delete=False, internal=False)
        self.rabbitmq.queue_declare(SYSTEM_STORE_INPUT_QUEUE, passive=False,
                                    durable=True, exclusive=False,
                                    auto_delete=False)
        self.rabbitmq.queue_bind(queue=SYSTEM_STORE_INPUT_QUEUE,
                                 exchange=STORE_EXCHANGE,
                                 routing_key=SYSTEM_STORE_INPUT_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=SYSTEM_STORE_INPUT_QUEUE,
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
        system_data = json.loads(body.decode())
        self.logger.debug("Received %s. Now processing this data.", system_data)

        processing_error = False
        try:
            self._process_redis_store(system_data)
            self._process_mongo_store(system_data)
        except KeyError as e:
            self.logger.error("Error when parsing %s.", system_data)
            self.logger.exception(e)
            processing_error = True
        except ReceivedUnexpectedDataException as e:
            self.logger.error("Error when processing %s", system_data)
            self.logger.exception(e)
            processing_error = True
        except Exception as e:
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
        system_name = meta_data['system_name']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['data']

        self.logger.debug(
            'Saving %s state: _process_cpu_seconds_total=%s, '
            '_process_memory_usage=%s, _virtual_memory_usage=%s, '
            '_open_file_descriptors=%s, _system_cpu_usage=%s, '
            '_system_ram_usage=%s, _system_storage_usage=%s, '
            '_network_transmit_bytes_per_second=%s, '
            '_network_receive_bytes_per_second=%s, '
            '_network_receive_bytes_total=%s, '
            '_network_transmit_bytes_total=%s, '
            '_disk_io_time_seconds_total=%s, '
            '_disk_io_time_seconds_in_interval=%s, _went_down_at=%s, '
            '_last_monitored=%s', system_name,
            metrics['process_cpu_seconds_total'],
            metrics['process_memory_usage'], metrics['virtual_memory_usage'],
            metrics['open_file_descriptors'], metrics['system_cpu_usage'],
            metrics['system_ram_usage'], metrics['system_storage_usage'],
            metrics['network_transmit_bytes_per_second'],
            metrics['network_receive_bytes_per_second'],
            metrics['network_receive_bytes_total'],
            metrics['network_transmit_bytes_total'],
            metrics['disk_io_time_seconds_total'],
            metrics['disk_io_time_seconds_in_interval'],
            metrics['went_down_at'], meta_data['last_monitored']
        )

        self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
            Keys.get_system_process_cpu_seconds_total(system_id):
                str(metrics['process_cpu_seconds_total']),
            Keys.get_system_process_memory_usage(system_id):
                str(metrics['process_memory_usage']),
            Keys.get_system_virtual_memory_usage(system_id):
                str(metrics['virtual_memory_usage']),
            Keys.get_system_open_file_descriptors(system_id):
                str(metrics['open_file_descriptors']),
            Keys.get_system_system_cpu_usage(system_id):
                str(metrics['system_cpu_usage']),
            Keys.get_system_system_ram_usage(system_id):
                str(metrics['system_ram_usage']),
            Keys.get_system_system_storage_usage(system_id):
                str(metrics['system_storage_usage']),
            Keys.get_system_network_transmit_bytes_per_second(system_id):
                str(metrics['network_transmit_bytes_per_second']),
            Keys.get_system_network_receive_bytes_per_second(system_id):
                str(metrics['network_receive_bytes_per_second']),
            Keys.get_system_network_receive_bytes_total(system_id):
                str(metrics['network_receive_bytes_total']),
            Keys.get_system_network_transmit_bytes_total(system_id):
                str(metrics['network_transmit_bytes_total']),
            Keys.get_system_disk_io_time_seconds_total(system_id):
                str(metrics['disk_io_time_seconds_total']),
            Keys.get_system_disk_io_time_seconds_in_interval(system_id):
                str(metrics['disk_io_time_seconds_in_interval']),
            Keys.get_system_went_down_at(system_id):
                str(metrics['went_down_at']),
            Keys.get_system_last_monitored(system_id):
                str(meta_data['last_monitored']),
        })

    def _process_redis_error_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        error_code = data['code']
        system_name = meta_data['system_name']
        downtime_exception = SystemIsDownException(system_name)

        if error_code == downtime_exception.code:
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            metrics = data['data']

            self.logger.debug(
                "Saving %s state: _went_down_at=%s", system_name,
                metrics['went_down_at']
            )

            self.redis.hset(
                Keys.get_hash_parent(parent_id),
                Keys.get_system_went_down_at(system_id),
                str(metrics['went_down_at'])
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
        Updating mongo with system metrics using a time-based document with 60
        entries per hour per system, assuming each system monitoring round is
        60 seconds.

        Collection is the parent identifier of the system, a document will keep
        incrementing with new system metrics until it's the next hour at which
        point mongo will create a new document and repeat the process.

        Document type will always be system, as only system metrics are going
        to be stored in this document.

        Timestamp is the time of when these metrics were extracted.

        $inc increments n_entries by one each time an entry is added
        """

        meta_data = data['meta_data']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['data']
        time_now = datetime.now()
        self.mongo.update_one(
            parent_id,
            {'doc_type': 'system', 'd': time_now.hour},
            {
                '$push': {
                    system_id: {
                        'process_cpu_seconds_total': str(
                            metrics['process_cpu_seconds_total']),
                        'process_memory_usage': str(
                            metrics['process_memory_usage']),
                        'virtual_memory_usage': str(
                            metrics['virtual_memory_usage']),
                        'open_file_descriptors': str(
                            metrics['open_file_descriptors']),
                        'system_cpu_usage': str(metrics['system_cpu_usage']),
                        'system_ram_usage': str(metrics['system_ram_usage']),
                        'system_storage_usage': str(
                            metrics['system_storage_usage']),
                        'network_transmit_bytes_per_second': str(
                            metrics['network_transmit_bytes_per_second']),
                        'network_receive_bytes_per_second': str(
                            metrics['network_receive_bytes_per_second']),
                        'network_receive_bytes_total': str(
                            metrics['network_receive_bytes_total']),
                        'network_transmit_bytes_total': str(
                            metrics['network_transmit_bytes_total']),
                        'disk_io_time_seconds_total': str(
                            metrics['disk_io_time_seconds_total']),
                        'disk_io_time_seconds_in_interval': str(
                            metrics['disk_io_time_seconds_in_interval']),
                        'went_down_at': str(metrics['went_down_at']),
                        'timestamp': meta_data['last_monitored'],
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )

    def _process_mongo_error_store(self, data: Dict) -> None:
        """
        Updating mongo with error metrics using a time-based document with 60
        entries per hour per system, assuming each system monitoring round is
        60 seconds.

        Collection is the parent identifier of the system, a document will keep
        incrementing with new system metrics until it's the next hour at which
        point mongo will create a new document and repeat the process.

        Document type will always be system, as only system metrics are going
        to be stored in this document.

        Timestamp is the time of when these metrics were extracted.

        $inc increments n_entries by one each time an entry is added
        """

        meta_data = data['meta_data']
        error_code = data['code']
        system_name = meta_data['system_name']
        downtime_exception = SystemIsDownException(system_name)

        if error_code == downtime_exception.code:
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            metrics = data['data']
            time_now = datetime.now()
            self.mongo.update_one(
                parent_id,
                {'doc_type': 'system', 'd': time_now.hour},
                {
                    '$push': {
                        system_id: {
                            'went_down_at': str(metrics['went_down_at']),
                            'timestamp': meta_data['time'],
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
