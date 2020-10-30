import logging
import os
from abc import ABC, abstractmethod
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.logging import log_and_print

class AlertersManager(ABC):
    def __init__(self, name: str, logger: logging.Logger):
        self._logger = logger
        self._config_process_dict = {}
        self._name = name

        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    def __str__(self) -> str:
        return self.name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def config_process_dict(self) -> Dict:
        return self._config_process_dict

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def _initialize_rabbitmq(self) -> None:
        pass

    def _listen_for_configs(self) -> None:
        self.rabbitmq.start_consuming()

    @abstractmethod
    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def manage(self) -> None:
        log_and_print('{} started.'.format(self), self.logger)
        self._initialize_rabbitmq()
        while True:
            try:
                self._listen_for_configs()
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
            except Exception as e:
                self.logger.exception(e)
                raise e
