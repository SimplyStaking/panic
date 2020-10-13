import logging
import json
from typing import Dict, List, Optional
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_store.redis.store_keys import Keys
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi

# Store needs to be initialized with Redis/Mongo/Rabbit APIS
# it will receive messages through Rabbit and store them in the respective
# databases.
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

    def save_github_state(self, github: Dict) -> None:
        key = Keys.get_github_releases(github['repo_name'])
        self.logger.debug('Saving github monitor state: %s=%s',
                              key, github['prev_no_of_releases'])
        self.redis.set(key, github['prev_no_of_releases'])

    # TODO maybe some sanitation to make sure all the keys exist in the 
    # dictionary received
    def save_system_state(self, system: Dict) -> None:
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

    # TODO maybe some sanitation to make sure all the keys exist in the 
    # dictionary received
    def save_system_monitor_state(self, monitor: Dict) -> None:
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

    def save_system_alerts_to_mongo(self, system: Dict) -> None:
        print('chicken')
        # try:
        #     ret = self.mongo.insert_one(self._mongo_coll, {
        #         'origin': self.channel_name,
        #         'severity': severity,
        #         'message': alert.message,
        #         'timestamp': datetime.now().timestamp()
        #     })
        #     # TODO: add checks around 'ret', if necessary
        # except Exception as e:
        #     self._backup_channels.alert_error(ProblemWithMongo(e))

    def save_transformer_to_redis(self, ch, method, properties, body) -> None:
        data_dict = json.loads(body.decode())
        print(" [x] Received %r" % json.loads(body.decode()))
        # Depending on the routing key proceed to store in redis the appropriate
        # dictionary received
        if self.redis.is_live:
          if method.routing_key == 'transformer.system.state':
              self.save_system_state(data_dict)
          elif method.routing_key == 'transformer.github.state':
              self.save_github_state(data_dict)
          elif method.routing_key == 'transformer.system.monitor':
              self.save_system_monitor_state(data_dict)
          else:
              print('Unknown state, ')

    def save_alert_to_mongo(self, ch, method, properties, body) -> None:
        data_dict = json.loads(body.decode())
        print(" [x] Received %r" % json.loads(body.decode()))
        # Depending on the routing key proceed to store in redis the appropriate
        # dictionary received
        if self.mongo.is_live:
          if method.routing_key == 'alert_router.system':
              self.save_system_alerts_to_mongo(data_dict)
          elif method.routing_key == 'alert_router.github':
              print('self.save_system_alerts')
              print('self.save_github_alerts')
          else:
              print('Unknown state, should throw')

    def accept_transformer_data(self) -> None:        
        result = self.rabbitmq.queue_declare(queue='', exclusive=True)
        self.rabbitmq.queue_bind(exchange='store', \
            queue=result.method.queue, routing_key='transformer.*.*')
        self.rabbitmq.basic_consume(queue=result.method.queue, \
          on_message_callback=self.save_transformer_to_redis, auto_ack=True)

    def accept_alert_router_data(self) -> None:
        result = self.rabbitmq.queue_declare(queue='', exclusive=True)
        self.rabbitmq.queue_bind(exchange='store', \
            queue=result.method.queue, routing_key='alert_router.*')
        self.rabbitmq.basic_consume(queue=result.method.queue, \
          on_message_callback=self.save_alert_to_mongo, auto_ack=True)

    def store(self):
        self.logger.debug("Connecting to RabbitMQ")
        self.rabbitmq.connect_till_successful()
        self.logger.debug("Connection successful")
        
        # Declare the store exchange
        self.rabbitmq.exchange_declare(exchange='store', exchange_type='topic')

        # Setup the queues for the data transformer, and data monitor
        self.accept_transformer_data()
        # self.accept_monitor_data()
        self.rabbitmq.start_consuming()

