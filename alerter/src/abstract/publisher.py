import copy
import logging
from abc import ABC, abstractmethod
from queue import Queue
from typing import Dict

from pika import BasicProperties

from src.abstract import Component
from src.message_broker.rabbitmq import RabbitMQApi


class PublisherComponent(Component, ABC):
    """
    Represents a blue print for a publisher
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
    def _send_data(self, data: Dict) -> None:
        pass

    @abstractmethod
    def _send_heartbeat(self, data_to_send: dict) -> None:
        pass


class QueuingPublisherComponent(Component, ABC):
    """
    Abstract class
    Uses a queuing mechanism to publish messages to RabbitMQ
    """

    def __init__(self, logger: logging.Logger, rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0):
        """
        Initializes the queue needed for publishing.
        :param logger: The logger object to log with
        :param rabbitmq: The rabbit MQ connection to use
        :param max_queue_size: The max queue size, defaults to 0 for infinite
        """
        self._publishing_queue = Queue(max_queue_size)
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

    def _push_to_queue(self, data: Dict, exchange: str, routing_key: str,
                       properties: BasicProperties = BasicProperties(
                           delivery_mode=2), mandatory: bool = True) -> None:
        """
        Method that takes the data to save and puts the data in their respective
        queues
        :param data: The data to queue to be sent.
        :param exchange: The exchange to send the data to
        :param routing_key: The routing key to use
        :param properties: Any pika properties to use
        (defaults to delivery_mode = 2)
        :param mandatory: Whether the message must be delivered or not
        (defaults to True)
        """
        self._logger.debug("Adding data to the publishing queue ...")

        # Place the data on the publishing queue. If the queue is full,
        # remove old data.
        if self._publishing_queue.full():
            self._logger.debug("The queue is full, clearing the first item.")
            self._publishing_queue.get()
        data_dict = {'exchange': exchange, 'routing_key': routing_key,
                     'data': copy.deepcopy(data), 'properties': properties,
                     'mandatory': mandatory}
        self._logger.debug("Adding %s to the queue", data_dict)
        self._publishing_queue.put(data_dict)

        self._logger.debug("Data added to the publishing queue successfully.")

    def _send_data(self) -> None:
        empty = True
        if not self._publishing_queue.empty():
            empty = False
            self._logger.info("Attempting to send all data waiting in the "
                              "publishing queue ...")

        # Try sending the data in the publishing queue one by one. Important,
        # remove an item from the queue only if the sending was successful, so
        # that if an exception is raised, that message is not popped
        while not self._publishing_queue.empty():
            data = self._publishing_queue.queue[0]
            try:
                self._rabbitmq.basic_publish_confirm(
                    exchange=data['exchange'], routing_key=data['routing_key'],
                    body=data['data'], is_body_dict=True,
                    properties=data['properties'], mandatory=data['mandatory'])
                self._logger.debug(
                    "Sent %s to '%s' exchange", data['data'], data['exchange']
                )
                self._publishing_queue.get()
                self._publishing_queue.task_done()
            except KeyError as ke:
                self._logger.error("Enqueued datum %s was incomplete", data)
                self._logger.exception(ke)
                self._logger.warning("Discarding this datum")
                self._publishing_queue.get()
                self._publishing_queue.task_done()

        if not empty:
            self._logger.info("Successfully sent all data from the publishing "
                              "queue")

    @abstractmethod
    def _send_heartbeat(self, data_to_send: dict) -> None:
        pass
