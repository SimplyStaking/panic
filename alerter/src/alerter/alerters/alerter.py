import logging
import sys
from abc import abstractmethod
from types import FrameType
from typing import Any

import pika.exceptions

from src.abstract.publisher_subscriber import (
    QueuingPublisherSubscriberComponent)
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class Alerter(QueuingPublisherSubscriberComponent):

    def __init__(self, alerter_name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi, max_queue_size: int = 0) -> None:
        super().__init__(logger, rabbitmq, max_queue_size)

        self._alerter_name = alerter_name

    def __str__(self) -> str:
        return self.alerter_name

    @property
    def alerter_name(self) -> str:
        return self._alerter_name

    @staticmethod
    def _greater_than_condition_function(current: Any, previous: Any) -> bool:
        return current > previous

    @staticmethod
    def _not_equal_condition_function(current: Any, previous: Any) -> bool:
        return current != previous

    @staticmethod
    def _equal_condition_function(current: Any, previous: Any) -> bool:
        return current == previous

    @staticmethod
    def _is_true_condition_function(current: Any) -> bool:
        return current is True

    @staticmethod
    def _true_fn() -> bool:
        return True

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    @abstractmethod
    def _place_latest_data_on_queue(self, *args) -> None:
        pass

    @abstractmethod
    def _process_data(self, *args) -> None:
        pass

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

    def start(self) -> None:
        self._initialise_rabbitmq()
        while True:
            try:
                # Before listening for new data send the data waiting to be sent
                # in the publishing queue. If the message is not routed, start
                # consuming and perform sending later.
                if not self.publishing_queue.empty():
                    try:
                        self._send_data()
                    except MessageWasNotDeliveredException as e:
                        self.logger.exception(e)

                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel may be reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
