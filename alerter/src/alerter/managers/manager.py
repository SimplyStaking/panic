import logging
import signal
from abc import ABC, abstractmethod
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils import env
from src.utils.constants import HEALTH_CHECK_EXCHANGE


class AlertersManager(ABC):
    def __init__(self, logger: logging.Logger, name: str):
        self._logger = logger
        self._name = name

        rabbit_ip = env.RABBIT_IP
        self._rabbitmq = RabbitMQApi(
            logger=logger.getChild(RabbitMQApi.__name__), host=rabbit_ip)

        # Handle termination signals by stopping the manager gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def _initialize_rabbitmq(self) -> None:
        pass

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def _send_heartbeat(self, data_to_send: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.manager',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.info("Sent heartbeat to '{}' exchange".format(
            HEALTH_CHECK_EXCHANGE))

    @abstractmethod
    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    @abstractmethod
    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    @abstractmethod
    def manage(self) -> None:
        pass

    @abstractmethod
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        pass
