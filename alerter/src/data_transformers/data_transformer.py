from abc import ABC, abstractmethod
from typing import Dict
import logging
import os
from queue import Queue

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis.redis_api import RedisApi
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.moniterables.system import System


class DataTransformer(ABC):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi) -> None:
        self._transformer_name = transformer_name
        self._logger = logger
        self._redis = redis
        self._transformed_data = {}
        self._data_for_saving = {}
        self._data_for_alerting = {}
        self._state = {}
        self._publishing_queue = Queue()

        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    def __str__(self) -> str:
        return self.transformer_name

    @property
    def transformer_name(self) -> str:
        return self._transformer_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def transformed_data(self) -> Dict:
        return self._transformed_data

    @property
    def data_for_saving(self) -> Dict:
        return self._data_for_saving

    @property
    def data_for_alerting(self) -> Dict:
        return self._data_for_alerting

    # TODO: Need to change output type to Dict[str, Union[System, Repo]]
    @property
    def state(self) -> Dict[str, System]:
        return self._state

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def publishing_queue(self) -> Queue:
        return self._publishing_queue

    @abstractmethod
    def _initialize_rabbitmq(self) -> None:
        pass

    @abstractmethod
    def _listen_for_data(self) -> None:
        pass

    @abstractmethod
    def _update_state(self) -> None:
        pass

    @abstractmethod
    def _process_transformed_data_for_storage(self) -> None:
        pass

    @abstractmethod
    def _process_transformed_data_for_alerting(self) -> None:
        pass

    @abstractmethod
    def _transform_data(self, data: Dict) -> None:
        pass

    @abstractmethod
    def _send_data_for_saving(self) -> None:
        pass

    @abstractmethod
    def _send_data_for_alerting(self) -> None:
        pass

    @abstractmethod
    def _send_data(self) -> None:
        # TODO: Use queues and concurrent.futures
        pass

    @abstractmethod
    def _process_raw_data(self, ch: BlockingChannel,
                          method: pika.spec.Basic.Deliver,
                          properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        pass

    def start(self) -> None:
        pass

# TODO: Must handle processing errors (handle as written on design paper)
# TODO: Must handle data received with `error` from monitors (handle as written
#     : on design paper
# TODO: Must check if Redis can be shared across process including it's logger,
#     : otherwise must use a different Redis for each process. i.e. declare
#     : redis here and do not pass it as parameter
# TODO: Must do proper error handling including errors in processing, getting
#     : data etc
