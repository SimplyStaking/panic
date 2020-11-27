import logging
import os
import signal
from abc import ABC, abstractmethod
from datetime import datetime
from queue import Queue
from types import FrameType
from typing import Dict

import pika.exceptions

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants import HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import (MessageWasNotDeliveredException)


class Alerter(ABC):

    def __init__(self, alerter_name: str, logger: logging.Logger) -> None:
        super().__init__()

        self._alerter_name = alerter_name
        self._logger = logger

        # Set a max queue size so that if the alerter is not able to
        # send data, old data can be pruned
        max_queue_size = int(os.environ[
                                 'ALERTER_PUBLISHING_QUEUE_SIZE'])
        self._publishing_queue = Queue(max_queue_size)

        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

        # Handle termination signals by stopping the monitor gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.alerter_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def alerter_name(self) -> str:
        return self._alerter_name

    @property
    def publishing_queue(self) -> Queue:
        return self._publishing_queue

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @abstractmethod
    def _place_latest_data_on_queue(self, data_list: Dict) -> None:
        pass

    @abstractmethod
    def _initialize_alerter(self) -> None:
        pass

    @abstractmethod
    def _process_data(self, *args) -> None:
        pass

    @abstractmethod
    def _alert_classifier_process(self) -> None:
        pass

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.worker',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.info("Sent heartbeat to '{}' exchange".format(
            HEALTH_CHECK_EXCHANGE))

    def _send_data(self) -> None:
        empty = True
        if not self.publishing_queue.empty():
            empty = False
            self.logger.info("Attempting to send all data waiting in the "
                             "publishing queue ...")

        # Try sending the data in the publishing queue one by one. Important,
        # remove an item from the queue only if the sending was successful, so
        # that if an exception is raised, that message is not popped
        while not self.publishing_queue.empty():
            data = self.publishing_queue.queue[0]
            self.rabbitmq.basic_publish_confirm(
                exchange=data['exchange'], routing_key=data['routing_key'],
                body=data['data'], is_body_dict=True,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.logger.debug("Sent {} to '{}' exchange".format(
                data['data'], data['exchange']))
            self.publishing_queue.get()
            self.publishing_queue.task_done()

        if not empty:
            self.logger.info("Successfully sent all data from the publishing "
                             "queue")

    def start_alert_classification(self) -> None:
        self._initialize_alerter()
        while True:
            try:
                # Before listening for new data send the data waiting to be sent
                # in the publishing queue. If the message is not routed, start
                # consuming and perform sending later.
                if not self.publishing_queue.empty():
                    try:
                        self._send_data()

                        # Send heartbeat if sending was successful
                        heartbeat = {
                            'component_name': self.alerter_name,
                            'timestamp': datetime.now().timestamp()
                        }
                        self._send_heartbeat(heartbeat)
                    except MessageWasNotDeliveredException as e:
                        self.logger.exception(e)

                self._alert_classifier_process()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel may be reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    @abstractmethod
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        pass

# TODO: Monday start from the beginning from here and compare with data
#     : transformer. Go through the implementation bit by bit to make sure that
#     : you break nothing.
