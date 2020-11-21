import copy
import logging
from abc import ABC
from queue import Queue
from typing import Dict

import pika

from src.abstract import Component
from src.message_broker.rabbitmq import RabbitMQApi


class QueuingPublisherComponent(Component, ABC):
    """
    Abstract class
    Uses a queuing mechanism to publish messages to RabbitMQ
    """

    def __init__(self, logger: logging.Logger, rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0):
        """
        Initializes the queue needed for publishing. It also sets the prefetch
        count of the rabbitmq channel passed through.
        :param logger: The logger object to log with
        :param rabbitmq: The rabbit MQ connection to use
        :param max_queue_size: The max queue size, defaults to 0 for infinite
        """
        self._publishing_queue = Queue(max_queue_size)
        self._logger = logger
        self._rabbitmq = rabbitmq

        prefetch_count = round(self._publishing_queue.maxsize / 5)
        self._rabbitmq.basic_qos(prefetch_count=prefetch_count)

        super().__init__()

    def _push_to_queue(self, data: Dict, exchange: str,
                       routing_key: str) -> None:
        """
        Method that takes the data to save and puts the data in their respective
        queues
        :param data: The data to queue to be sent.
        :param exchange: The exchange to send the data to
        :param routing_key: The routing key to use
        """
        self._logger.debug("Adding data to the publishing queue ...")

        # Place the data on the publishing queue. If the queue is full,
        # remove old data.
        if self._publishing_queue.full():
            self._logger.debug("The queue is full, clearing the first item.")
            self._publishing_queue.get()
        data_dict = {'exchange': exchange, 'routing_key': routing_key,
                     'data': copy.deepcopy(data)}
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
                    properties=pika.BasicProperties(delivery_mode=2),
                    mandatory=True)
                self._logger.debug(
                    f"Sent {data['data']} to '{data['exchange']}' exchange"
                )
                self._publishing_queue.get()
                self._publishing_queue.task_done()
            except KeyError as ke:
                self._logger.error("Enqueued datum %s was incomplete", data)
                self._logger.exception(ke)
                self._logger.warn("Discarding this datum")

        if not empty:
            self._logger.info("Successfully sent all data from the publishing "
                              "queue")
