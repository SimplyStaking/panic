import logging
from abc import ABC, abstractmethod
from typing import Dict

from src.abstract import Component
from src.message_broker.rabbitmq import RabbitMQApi


class PublisherSubscriberComponent(Component, ABC):
    """
    Represents a blue print for a component being both a Subscriber and
    Publisher
    """

    def __init__(self, logger: logging.Logger, rabbitmq: RabbitMQApi):
        """
        :param logger: The logger object to log with
        :param rabbitmq: The rabbit MQ connection to use
        """
        self._logger = logger
        self._rabbitmq = rabbitmq

        super().__init__()

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @abstractmethod
    def _initialise_rabbitmq(self) -> None:
        pass

    def disconnect_from_rabbit(self) -> None:
        """
        Disconnects the component from RabbitMQ
        :return:
        """
        self.rabbitmq.disconnect_till_successful()

    @abstractmethod
    def _listen_for_data(self) -> None:
        pass

    @abstractmethod
    def _send_data(self, data: Dict) -> None:
        pass

    @abstractmethod
    def _send_heartbeat(self, data_to_send: dict) -> None:
        pass
