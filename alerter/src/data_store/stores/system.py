
import logging
import json
import pika
import pika.exceptions
from datetime import datetime
from typing import Dict, List, Optional
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_store.redis.store_keys import Keys
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.types import SystemDataType, SystemMonitorDataType
from alerter.src.data_store.stores.store import Store
from alerter.src.utils.logging import log_and_print

class SystemStore(Store):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def _initialize_store(self) -> None:
        """
        Initialize the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates an exchange named `store` of type `direct`
        Declares a queue named `system_store_queue` and binds it to exchange
        `store` with a routing key `transformer.system.*` meaning anything
        coming from the transformer with regads to a system will be received 
        here.
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange='store', exchange_type='direct',
            passive=False, durable=True, auto_delete=False, internal=False)
        self.rabbitmq.queue_declare('system_store_queue', passive=False, \
            durable=True, exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(queue='system_store_queue', exchange='store',
            routing_key='system')

    def _start_listening(self) -> None:
        self._mongo = MongoApi(logger=self.logger, db_name=self.mongo_db, \
            host=self.mongo_ip, port=self.mongo_port)
        self.rabbitmq.basic_consume(queue='system_store_queue', \
            on_message_callback=self._process_data, auto_ack=False, \
                exclusive=False, consumer_tag=None)
        self.rabbitmq.start_consuming()

    def _process_data(self,
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties, body: bytes) -> None:
        """ 
        Processes the data being received, from the queue.
        Two types of metrics are going to be received, the system metrics
        of the system being monitored and the metrics of the monitor currently
        monitoring the system. System metrics need to be stored in redis and
        mongo while monitor metrics only need to be stored in redis.
        """
        system_data = json.loads(body.decode())
        try:
            self._process_redis_monitor_store(
                system_data['result']['meta_data']
            )
            self._process_redis_metrics_store(
              system_data['result']['data'],
              system_data['result']['meta_data']['system_parent_id'],
              system_data['result']['meta_data']['system_id'],
            )
            self._process_mongo_store(
                system_data['result']['data'],
                system_data['result']['meta_data'],
            )
        except KeyError as e:
            self.logger.error('Error when reading system data, in data store.')
            self.logger.exception(e)
        except Exception as e:
            self.logger.exception(e)
            raise e
        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_redis_monitor_store(self, monitor_data: SystemMonitorDataType \
        ) -> None:
        self.logger.debug(
            'Saving %s state: _system_monitor_last_monitoring_round=%s',
            monitor_data['monitor_name'], monitor_data['time']
        )

        self.redis.set_multiple({
            Keys.get_system_monitor_last_monitoring_round(
                monitor_data['monitor_name']): monitor_data['time']
        })

    def _process_redis_metrics_store(self, system: SystemDataType,
        parent_id: str, system_id: str) -> None:

        self.logger.debug(
            'Saving %s state: _process_cpu_seconds_total=%s, '
            '_process_memory_usage=%s, _virtual_memory_usage=%s, '
            '_open_file_descriptors=%s, _system_cpu_usage=%s, '
            '_system_ram_usage=%s, _system_storage_usage=%s, '
            '_system_network_transmit_bytes_per_second=%s, '
            '_system_network_receive_bytes_per_second=%s, '
            '_system_network_receive_bytes_total=%s, '
            '_system_network_transmit_bytes_total=%s, '
            '_system_disk_io_time_seconds_total=%s, ',
            '_system_disk_io_time_seconds_in_interval=%s',
            system_id, system['process_cpu_seconds_total'],
            system['process_memory_usage'], system['virtual_memory_usage'],
            system['open_file_descriptors'], system['system_cpu_usage'],
            system['system_ram_usage'], system['system_storage_usage'],
            system['system_network_transmit_bytes_per_second'],
            system['system_network_receive_bytes_per_second'],
            system['system_network_receive_bytes_total'],
            system['system_network_transmit_bytes_total'],
            system['system_disk_io_time_seconds_total'],
            system['system_disk_io_time_seconds_in_interval']
        )

        self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
            Keys.get_system_process_cpu_seconds_total(system_id):
                system['process_cpu_seconds_total'],
            Keys.get_system_process_memory_usage(system_id):
                system['process_memory_usage'],
            Keys.get_system_virtual_memory_usage(system_id):
                system['virtual_memory_usage'],
            Keys.get_system_open_file_descriptors(system_id):
                system['open_file_descriptors'],
            Keys.get_system_system_cpu_usage(system_id):
                system['system_cpu_usage'],
            Keys.get_system_system_ram_usage(system_id):
                system['system_ram_usage'],
            Keys.get_system_system_storage_usage(system_id):
                system['system_storage_usage'],
            Keys.get_system_network_transmit_bytes_per_second(system_id):
                system['system_network_transmit_bytes_per_second'],
            Keys.get_system_network_receive_bytes_per_second(system_id):
                system['system_network_receive_bytes_per_second'],
            Keys.get_system_network_receive_bytes_total(system_id):
                system['system_network_receive_bytes_total'],
            Keys.get_system_network_transmit_bytes_total(system_id):
                system['system_network_transmit_bytes_total'],
            Keys.get_system_disk_io_time_seconds_total(system_id):
                system['system_disk_io_time_seconds_total'],
            Keys.get_system_disk_io_time_seconds_in_interval(system_id):
                system['system_disk_io_time_seconds_in_interval'],
        })

    def _process_mongo_store(self, system: SystemDataType, monitor_data: \
        SystemMonitorDataType) -> None:
        """
        Updating mongo with system metrics using a time-based document with 60
        entries per hour per system, assuming each system monitoring round is
        60 seconds.

        Collection is the parent identifier of the system, a document will keep
        incrementing with new system metrics until it's the next hour at which
        point mongo will create a new document and repeat the process.

        Document type will always be system, as only system metrics are going
        to be stored in this document.

        Timestamp is the time of when the metric was saved into the database.

        $inc increments n_metrics by one each time a metric is added
        """
        time_now = datetime.now()
        self.mongo.update_one(monitor_data['system_parent_id'],
            {'doc_type': 'system', 'd': time_now.hour },
            {'$push': { monitor_data['system_id']: {
                'process_cpu_seconds_total': \
                    system['process_cpu_seconds_total'],
                'process_memory_usage': system['process_memory_usage'],
                'virtual_memory_usage': system['virtual_memory_usage'],
                'open_file_descriptors': \
                    system['open_file_descriptors'],
                'system_cpu_usage': system['system_cpu_usage'],
                'system_ram_usage': system['system_ram_usage'],
                'system_storage_usage': system['system_storage_usage'],
                'system_network_transmit_bytes_per_second': \
                    system['system_network_transmit_bytes_per_second'],
                'system_network_receive_bytes_per_second': \
                    system['system_network_receive_bytes_per_second'],
                'system_network_receive_bytes_total': \
                    system['system_network_receive_bytes_total'],
                'system_network_transmit_bytes_total':
                    system['system_network_transmit_bytes_total'],
                'system_disk_io_time_seconds_total':
                    system['system_disk_io_time_seconds_total'],
                'system_disk_io_time_seconds_in_interval':
                    system['system_disk_io_time_seconds_in_interval'],
                'timestamp': monitor_data['time'],
                }
            },
                '$inc': {'n_metrics': 1},
            }
        )

    def _begin_store(self) -> None:
        self._initialize_store()
        log_and_print('{} started.'.format(self), self.logger)
        while True:
            try:
                self._start_listening()
            except pika.exceptions.AMQPChannelError:
                # Error would have already been logged by RabbitMQ logger. If
                # there is a channel error, the RabbitMQ interface creates a new
                # channel, therefore perform another managing round without
                # sleeping
                continue
            except pika.exceptions.AMQPConnectionError as e:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                raise e
            except MessageWasNotDeliveredException as e:
                # Log the fact that the message could not be sent and re-try
                # another monitoring round without sleeping
                self.logger.exception(e)
                continue
            except Exception as e:
                self.logger.exception(e)
                raise e

