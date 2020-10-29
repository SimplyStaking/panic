import logging
import os
import pika
import pika.exceptions

from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from abc import ABC, abstractmethod

class Store(ABC):
    def __init__(self, logger: logging.Logger):
        rabbit_ip = os.environ["RABBIT_IP"]
        self._mongo_ip = os.environ["DB_IP"]
        self._mongo_db = os.environ["DB_NAME"]
        self._mongo_port = int(os.environ["DB_PORT"])
        redis_ip = os.environ["REDIS_IP"]
        redis_db = os.environ["REDIS_DB"]
        redis_port = os.environ["REDIS_PORT"]

        self._logger = logger
        self._rabbitmq = RabbitMQApi(logger=self._logger, host=rabbit_ip)
        self._mongo = None
        self._redis = RedisApi(logger=self._logger, db=redis_db, \
            host=redis_ip, port=redis_port, namespace='panic_alerter')

    @property
    def mongo_ip(self) -> str:
        return self._mongo_ip

    @property
    def mongo_db(self) -> str:
        return self._mongo_db

    @property
    def mongo_port(self) -> str:
        return self._mongo_port

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def redis(self) -> RedisApi:
      return self._redis

    @property
    def mongo(self) -> MongoApi:
      return self._mongo

    @abstractmethod
    def _initialize_store(self) -> None:
        pass

    def _process_redis_metrics_store(self) -> None:
        pass

    def _process_redis_monitor_store(self) -> None:
        pass

    def _process_mongo_store(self) -> None:
        pass

    @abstractmethod
    def _process_data(self,
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    @abstractmethod
    def _begin_store(self) -> None:
        pass
