import logging
import os
from abc import ABC, abstractmethod

import pika
import pika.exceptions
from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis.redis_api import RedisApi
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi


class Store(ABC):
    def __init__(self, store_name: str, logger: logging.Logger):
        self._store_name = store_name
        rabbit_ip = os.environ['RABBIT_IP']
        self._mongo_ip = os.environ['DB_IP']
        self._mongo_db = os.environ['DB_NAME']
        self._mongo_port = int(os.environ['DB_PORT'])
        redis_ip = os.environ['REDIS_IP']
        redis_db = os.environ['REDIS_DB']
        redis_port = os.environ['REDIS_PORT']
        unique_alerter_identifier = os.environ['UNIQUE_ALERTER_IDENTIFIER']

        self._logger = logger
        self._rabbitmq = RabbitMQApi(logger=self._logger, host=rabbit_ip)
        self._mongo = None
        self._redis = RedisApi(logger=self._logger, db=redis_db,
                               host=redis_ip, port=redis_port,
                               namespace=unique_alerter_identifier)

    def __str__(self) -> str:
        return self.store_name

    @property
    def store_name(self) -> str:
        return self._store_name

    @property
    def mongo_ip(self) -> str:
        return self._mongo_ip

    @property
    def mongo_db(self) -> str:
        return self._mongo_db

    @property
    def mongo_port(self) -> int:
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

    def _process_redis_store(self, *args) -> None:
        pass

    def _process_mongo_store(self, *args) -> None:
        pass

    @abstractmethod
    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        pass

    @abstractmethod
    def _start_listening(self):
        pass

    def begin_store(self) -> None:
        self._initialize_store()
        while True:
            try:
                self._start_listening()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e
