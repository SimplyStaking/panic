import logging
from abc import abstractmethod
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.publisher_subscriber import (
    QueuingPublisherSubscriberComponent)
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants import (HEALTH_CHECK_EXCHANGE,
                                 HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)


class AlertersManager(QueuingPublisherSubscriberComponent):
    def __init__(self, logger: logging.Logger, name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, rabbitmq)
        self._name = name

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def _send_heartbeat(self, data_to_send: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

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
    def start(self) -> None:
        pass

    @abstractmethod
    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        pass

    @abstractmethod
    def _push_latest_data_to_queue_and_send(self, alert: Dict) -> None:
        pass
