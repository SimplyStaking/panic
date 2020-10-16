
import logging
import json
import pika
import pika.exceptions
from datetime import datetime
from typing import Dict, List, Optional
from alerter.src.utils.exceptions import ( SavingMetricsToMongoException,
    UnknownRoutingKeyException)
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_store.redis.store_keys import Keys
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.types import GithubDataType
from alerter.src.data_store.store.store import Store

class GithubStore(Store):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    """
        Initialize the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates an exchange named `store` of type `topic`
        Declares a queue named `github_store_queue` and binds it to exchange
        `store` with a routing key `transformer.github` meaning anything
        coming from the transformer with regads to github updates will be
        received here.
    """
    def _initialize_store(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange='store', exchange_type='topic',
            passive=False, durable=True, auto_delete=False, internal=False)
        self.rabbitmq.queue_declare('github_store_queue', passive=False, \
            durable=True, exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(queue='github_store_queue', exchange='store',
            routing_key='transformer.github')
        self.rabbitmq.queue_purge(queue='github_store_queue')

    def _start_listening(self) -> None:
        self._mongo = MongoApi(logger=self.logger, db_name=self.mongo_db, \
            host=self.mongo_ip, port=self.mongo_port)
        self.rabbitmq.basic_consume(queue='github_store_queue', \
            on_message_callback=self._process_data, auto_ack=False, \
                exclusive=False, consumer_tag=None)
        self.rabbitmq.start_consuming()

    """
        Processes the data being received, from the queue. One type of metric
        will be received here which is a github update if a new release
        of a repository has been detected and monitored. This only needs
        to be stored in redis.
    """
    def _process_data(self, ch, method: pika.spec.Basic.Deliver, \
        properties: pika.spec.BasicProperties, body: bytes) -> None:
        github_data = json.loads(body.decode())
        self.rabbitmq.basic_ack(method.delivery_tag, False)
        if method.routing_key == 'transformer.github':
            self._process_redis_metrics_store(github_data)
        else:
            raise UnknownRoutingKeyException(
                'Received an unknown routing key {} from the transformer.' \
                    .format(method.routing_key))

    def _process_redis_metrics_store(self,  github: GithubDataType) -> None:
        key = Keys.get_github_releases(github['name'])
        self.logger.debug('Saving github monitor state: %s=%s', key,
            github['prev_no_of_releases'])
        self.redis.set(key, github['prev_no_of_releases'])
