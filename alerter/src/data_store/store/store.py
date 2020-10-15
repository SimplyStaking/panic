import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from alerter.src.utils.exceptions import ( SavingMetricsToMongoException,
    UnknownRoutingKeyException)
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_store.redis.store_keys import Keys
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.types import (SystemData, SystemMonitorData, GithubData,
    AlertType)

"""
    Store needs to be initialized with Redis/Mongo/Rabbit APIS
    it will receive messages through Rabbit and store them in the respective
    databases.
"""
class Store:
    def __init__(self, logger: logging.Logger, redis: RedisApi,
                 mongo: MongoApi, rabbitmq: RabbitMQApi) -> None:
        self._logger = logger
        self._redis = redis
        self._mongo = mongo
        self._rabbitmq = rabbitmq
        self._logger.info('Store initialised.')

    @property
    def logger(self) -> logging.Logger:
      return self._logger
    
    @property
    def redis(self) -> RedisApi:
      return self._redis

    @property
    def mongo(self) -> MongoApi:
      return self._mongo

    @property
    def rabbitmq(self) -> RabbitMQApi:
      return self._rabbitmq

    def save_github_state(self, github: GithubData) -> None:
        key = Keys.get_github_releases(github['name'])
        self.logger.debug('Saving github monitor state: %s=%s', key,
            github['prev_no_of_releases'])
        self.redis.set(key, github['prev_no_of_releases'])

    def save_system_state(self, system: SystemData) -> None:
        self.logger.debug(
            'Saving %s state: _process_cpu_seconds_total=%s, '
            '_process_memory_usage=%s, _virtual_memory_usage=%s, '
            '_open_file_descriptors=%s, _system_cpu_usage=%s, '
            '_system_ram_usage=%s, _system_storage_usage=%s'
            '_system_network_transmit_bytes_per_second=%s'
            '_system_network_receive_bytes_per_second=%s',
            system['name'], system['process_cpu_seconds_total'],
            system['process_memory_usage'], system['virtual_memory_usage'],
            system['open_file_descriptors'], system['system_cpu_usage'],
            system['system_ram_usage'], system['system_storage_usage'],
            system['system_network_transmit_bytes_per_second'],
            system['system_network_receive_bytes_per_second']
        )

        self.redis.set_multiple({
            Keys.get_system_process_cpu_seconds_total(system['name']):
                system['process_cpu_seconds_total'],
            Keys.get_system_process_memory_usage(system['name']):
                system['process_memory_usage'],
            Keys.get_system_virtual_memory_usage(system['name']):
                system['virtual_memory_usage'],
            Keys.get_system_open_file_descriptors(system['name']):
                system['open_file_descriptors'],
            Keys.get_system_system_cpu_usage(system['name']):
                system['system_cpu_usage'],
            Keys.get_system_system_ram_usage(system['name']):
                system['system_ram_usage'],
            Keys.get_system_system_storage_usage(system['name']):
                system['system_storage_usage'],
            Keys.get_system_network_transmit_bytes_per_second(system['name']):
                system['system_network_transmit_bytes_per_second'],
            Keys.get_system_network_receive_bytes_per_second(system['name']):
                system['system_network_receive_bytes_per_second']
        })

    def save_system_monitor_state(self, monitor: SystemMonitorData) -> None:
        self.logger.debug(
            'Saving %s state: _system_monitor_alive=%s, '
            '_system_monitor_last_network_inspection=%s, '
            '_system_monitor_network_receive_bytes_total=%s, '
            '_system_monitor_network_transmit_bytes_total=%s',
            monitor['name'], monitor['system_monitor_alive'],
            monitor['system_monitor_last_network_inspection'],
            monitor['system_monitor_network_receive_bytes_total'],
            monitor['system_monitor_network_transmit_bytes_total']
        )

        self.redis.set_multiple({
            Keys.get_system_monitor_alive(monitor['name']):
                monitor['system_monitor_alive'],
            Keys.get_system_monitor_last_network_inspection(monitor['name']):
                monitor['system_monitor_last_network_inspection'],
            Keys.get_system_monitor_network_receive_bytes_total( 
                monitor['name']): \
                    monitor['system_monitor_network_receive_bytes_total'],
            Keys.get_system_monitor_network_transmit_bytes_total(
                monitor['name']): \
                    monitor['system_monitor_network_transmit_bytes_total']
        })

    """
        Updating mongo with alerts using a size-based document with 1000 entries
        Collection is the name of the chain, a document will keep incrementing
        with new alerts until it's reached 1000 entries at which point mongo
        will create a new document and repeat.

        Document type will always be alert, as only alerts will be stored in
        this document.
        Origin is the object the alert is associated with e.g cosmos_node_2.
        Alert name is the configured alerts e.g Validator Missing Blocks
        Message contains the specific details e.g Missed 40 Blocks in a row
        Timestamp is the time of alerting

        $min/$max are used for data aggregation
        $min is the timestamp of the first alert
        $max is the timestamp of the last alert entered
        $inc increments n_alerts by one each time an alert is added
    """
    def save_alerts_to_mongo(self, alert: AlertType) -> None:
        try:
            self.mongo.update_one(alert['chain_name'],
                {'doc_type': 'alert', 'n_alerts': {'$lt': 1000}},
                {'$push': { 'alerts': {
                    'origin': alert['origin'],  
                    'alert_name': alert['alert_name'],
                    'severity': alert['severity'],
                    'message': alert['message'],
                    'timestamp': alert['timestamp'],
                    }
                },
                    '$min': {'first': alert['timestamp']},
                    '$max': {'last': alert['timestamp']},
                    '$inc': {'n_alerts': 1},
                }
            )
        except Exception as e:
            self.logger.error(e)
            raise SavingMetricsToMongoException(
                'Failed to save alert to Mongo.')

    """
        Updating mongo with system metrics using a time-based document with 60
        entries per hour per system, assuming each system monitoring round is
        60 seconds.

        Collection is the name of the chain, a document will keep incrementing
        with new system metrics until it's the next hour at which point mongo
        will create a new document and repeat the process.

        Document type will always be system, as only system metrics are going
        to be stored in this document.

        Timestamp is the time of when the metric was saved into the database.

        $min/$max are used for data aggregation
        $min is the timestamp of the first alert
        $max is the timestamp of the last alert entered
        $inc increments n_alerts by one each time an alert is added
    """
    def save_system_metrics_to_mongo(self, system: SystemData) -> None:
        try:
            # Get the timestamp of when the metrics were saved into the db
            # shouldn't be much time difference between when they were monitored
            # on and when they are being saved.
            time_now = datetime.now()
            self.mongo.update_one(system['chain_name'],
                {'doc_type': 'system', 'd': time_now.hour },
                {'$push': { system['name'] : {
                    'process_cpu_seconds_total': \
                        system['process_cpu_seconds_total'],
                    'process_memory_usage': system['process_memory_usage'],
                    'virtual_memory_usage': system['virtual_memory_usage'],
                    'open_file_descriptors': system['open_file_descriptors'],
                    'system_cpu_usage': system['system_cpu_usage'],
                    'system_ram_usage': system['system_ram_usage'],
                    'system_storage_usage': system['system_storage_usage'],
                    'system_network_transmit_bytes_per_second': \
                        system['system_network_transmit_bytes_per_second'],
                    'system_network_receive_bytes_per_second': \
                        system['system_network_receive_bytes_per_second'],
                    'timestamp': time_now.timestamp(),
                    }
                },
                    '$inc': {'n_metrics': 1},
                }
            )
        except Exception as e:
            self.logger.error(e)
            raise SavingMetricsToMongoException(
                'Failed to save system metrics to mongo.')

    """
        Depending on the data coming from the transformer, it would need
        to be stored in only redis or in both redis and mongo.

        The routing_keys are used to determine what data is incoming to the
        datastore.
    """
    def save_transformer_data(self, ch, method, properties, body) -> None:
        received_data = json.loads(body.decode())
        if method.routing_key == 'transformer.system.state':
            self.save_system_state(received_data)
            self.save_system_metrics_to_mongo(received_data)
        elif method.routing_key == 'transformer.github.state':
            self.save_github_state(received_data)
        elif method.routing_key == 'transformer.system.monitor':
            self.save_system_monitor_state(received_data)
        else:
            raise UnknownRoutingKeyException(
                'Received an unknown routing key {} from the transformer.' \
                    .format(method.routing_key))

    def save_alert_to_mongo(self, ch, method, properties, body) -> None:
        received_data = json.loads(body.decode())
        self.save_alerts_to_mongo(received_data)

    def accept_transformer_data(self) -> None:        
        result = self.rabbitmq.queue_declare(queue='', exclusive=True)
        self.rabbitmq.queue_bind(exchange='store', \
            queue=result.method.queue, routing_key='transformer.*.*')
        self.rabbitmq.basic_consume(queue=result.method.queue, \
          on_message_callback=self.save_transformer_data, auto_ack=True)

    def accept_alert_router_data(self) -> None:
        result = self.rabbitmq.queue_declare(queue='', exclusive=True)
        self.rabbitmq.queue_bind(exchange='store', \
            queue=result.method.queue, routing_key='alert_router')
        self.rabbitmq.basic_consume(queue=result.method.queue, \
          on_message_callback=self.save_alert_to_mongo, auto_ack=True)

    def start_store(self) -> None:
        self.logger.debug("Connecting to RabbitMQ")
        self.rabbitmq.connect_till_successful()
        self.logger.debug("Connection successful")
        
        # Declare the store exchange
        self.rabbitmq.exchange_declare(exchange='store', exchange_type='topic')

        # Setup the queues for the data transformer, and data monitor
        self.accept_transformer_data()
        self.accept_alert_router_data()
        self.rabbitmq.start_consuming()

