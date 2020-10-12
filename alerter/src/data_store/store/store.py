import logging
import json
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
        self._redis_hash_channel= Keys.get_hash_channel()
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

    def save_channels_to_redis(self, routing_key: str, channel_dict: dict) \
        -> None:

        # Go through all the potential routing keys depending on the config
        # sent.
        if(routing_key == 'config.email'):
          for key in channel_dict:
              print(key)
              print(channel_dict[key]['configname'])
              self.redis.hset_multiple(self._redis_hash_channel, {
                  Keys.get_email_config_name(key): \
                      channel_dict[key]['configname'],
                  Keys.get_email_smtp_config(key): channel_dict[key]['smtp'],
                  Keys.get_email_from(key): channel_dict[key]['emailfrom'],
                  Keys.get_email_to(key): channel_dict[key]['emailsto'],
                  Keys.get_email_username(key): channel_dict[key]['username'],
                  Keys.get_email_password(key): channel_dict[key]['password'],
                  Keys.get_email_info(key): channel_dict[key]['info'],
                  Keys.get_email_warning(key): channel_dict[key]['warning'],
                  Keys.get_email_critical(key): channel_dict[key]['critical'],
                  Keys.get_email_error(key): channel_dict[key]['error'],
              })
          print(self.redis.hget(self._redis_hash_channel, \
              Keys.get_email_config_name('email_9fd2f8f1-06e0-4778-9918-0f856fe4906a')))

    def save_config_to_redis(self, ch, method, properties, body) -> None:
        new_dict = json.loads(body.decode())
        print(" [x] Received %r" % json.loads(body.decode()))
        self.save_channels_to_redis(method.routing_key, new_dict)

    def process_config(self) -> None:        
        self.rabbitmq.exchange_declare(exchange='config', \
            exchange_type='topic')
        result = self.rabbitmq.queue_declare(queue='', exclusive=True)
        # Bind queue to exchange, result.method.queue contains the randomly
        # created queue name
        self.rabbitmq.queue_bind(exchange='config', queue=result.method.queue,
            routing_key='config.*')
        print(' [*] Started config listener.')
        self.rabbitmq.basic_consume(queue=result.method.queue, \
          on_message_callback=self.save_config_to_redis, auto_ack=True)
        self.rabbitmq.start_consuming()

    def store(self):
      self.logger.debug("Connecting to RabbitMQ")
      self.rabbitmq.connect_till_successful()
      self.logger.debug("Connection successful")

      # Start the config listener queue
      self.process_config()
