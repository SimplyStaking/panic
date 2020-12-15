import logging
from abc import abstractmethod

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract import Component
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env


class ChannelHandler(Component):
    def __init__(self, handler_name: str, logger: logging.Logger) -> None:
        super().__init__()
        self._handler_name = handler_name
        self._logger = logger

        rabbit_ip = env.RABBIT_IP
        self._rabbitmq = RabbitMQApi(logger=self.logger.getChild('rabbitmq'),
                                     host=rabbit_ip)

    def __str__(self) -> str:
        return self.handler_name

    @property
    def handler_name(self) -> str:
        return self._handler_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abstractmethod
    def _process_alert(self, ch: BlockingChannel,
                       method: pika.spec.Basic.Deliver,
                       properties: pika.spec.BasicProperties,
                       body: bytes) -> None:
        pass

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @abstractmethod
    def start(self) -> None:
        pass
