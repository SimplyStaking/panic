import logging
import os
import time
from abc import ABC, abstractmethod
from queue import Queue
from typing import Dict

import pika.exceptions
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  PANICException)


class Alerter(ABC):

    def __init__(self, alerter_name: str, logger: logging.Logger) -> None:
        super().__init__()

        self._alerter_name = alerter_name
        self._logger = logger
        self._data_for_alert_router = {}
        # Set a max queue size so that if the alerter is not able to
        # send data, old data can be pruned
        max_queue_size = int(os.environ[
                                 "ALERTER_PUBLISHING_QUEUE_SIZE"])
        self._publishing_queue = Queue(max_queue_size)
        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    def __str__(self) -> str:
        return self.alerter_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def alerts_configs(self) -> None:
        pass

    @property
    def alerter_name(self) -> str:
        return self._alerter_name

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def data_for_alert_router(self) -> Dict:
        return self._data_for_alert_router

    @property
    def publishing_queue(self) -> Queue:
        return self._publishing_queue

    @abstractmethod
    def _place_latest_data_on_queue(self) -> None:
        pass

    @abstractmethod
    def _initialize_alerter(self) -> None:
        pass

    @abstractmethod
    def _start_listening(self) -> None:
        pass

    @abstractmethod
    def _process_data(self, *args) -> None:
        pass

    @abstractmethod
    def _alert_classifier_process(self) -> None:
        pass

    def _send_data(self) -> None:
        empty = True
        if not self.publishing_queue.empty():
            empty = False
            self.logger.info('Attempting to send all data waiting in the '
                             'publishing queue ...')

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
            self.logger.debug('Sent {} to \'{}\' exchange'
                              .format(data['data'], data['exchange']))
            self.publishing_queue.get()
            self.publishing_queue.task_done()

        if not empty:
            self.logger.info('Successfully sent all data from the publishing '
                             'queue')

    def start_alert_classification(self) -> None:
        self._initialize_alerter()
        while True:
            try:
                try:
                    self._send_data()
                except MessageWasNotDeliveredException as e:
                    self.logger.exception(e)
                self._alert_classifier_process()
            except pika.exceptions.AMQPChannelError:
                # Error would have already been logged by RabbitMQ logger. If
                # there is a channel error, the RabbitMQ interface creates a
                # new channel, therefore perform another monitoring round
                # without sleeping
                continue
            except MessageWasNotDeliveredException as e:
                # Log the fact that the message could not be sent. Sleep just
                # because there is no use in consuming a lot of resources until
                # the problem is fixed.
                self.logger.exception(e)
            except pika.exceptions.AMQPConnectionError as e:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

            self.logger.debug('Sleeping for %s seconds.', self.monitor_period)
            time.sleep(self.monitor_period)
