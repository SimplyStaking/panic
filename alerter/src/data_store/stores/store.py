import logging
import sys
from abc import abstractmethod
from types import FrameType

import pika
import pika.exceptions

from src.abstract.publisher_subscriber import PublisherSubscriberComponent
from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis.redis_api import RedisApi
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils import env
from src.utils.constants import (HEALTH_CHECK_EXCHANGE,
                                 HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.logging import log_and_print


class Store(PublisherSubscriberComponent):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, rabbitmq)
        self._name = name
        self._mongo_ip = env.DB_IP
        self._mongo_db = env.DB_NAME
        self._mongo_port = env.DB_PORT

        redis_ip = env.REDIS_IP
        redis_db = env.REDIS_DB
        redis_port = env.REDIS_PORT
        unique_alerter_identifier = env.UNIQUE_ALERTER_IDENTIFIER

        self._mongo = None
        self._redis = RedisApi(logger=self._logger.getChild(RedisApi.__name__),
                               db=redis_db, host=redis_ip, port=redis_port,
                               namespace=unique_alerter_identifier)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

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
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def mongo(self) -> MongoApi:
        return self._mongo

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

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

    def start(self) -> None:
        self._initialise_rabbitmq()
        while True:
            try:
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _send_data(self, *args) -> None:
        """
        We are not implementing the _send_data function because wrt rabbit,
        any data store only sends heartbeats.
        """
        pass
