import logging
import sys
from abc import ABC, abstractmethod
from types import FrameType
from typing import Dict, List, Any, Union

import pika.exceptions
import urllib3

from src.abstract.publisher import PublisherComponent
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.rabbitmq import (RAW_DATA_EXCHANGE,
                                          HEALTH_CHECK_EXCHANGE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          TOPIC)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Monitor(PublisherComponent, ABC):

    def __init__(self, monitor_name: str, logger: logging.Logger,
                 monitor_period: int, rabbitmq: RabbitMQApi) -> None:
        self._monitor_name = monitor_name
        self._monitor_period = monitor_period
        super().__init__(logger, rabbitmq)

    def __str__(self) -> str:
        return self.monitor_name

    @property
    def monitor_period(self) -> int:
        return self._monitor_period

    @property
    def monitor_name(self) -> str:
        return self._monitor_name

    @abstractmethod
    def _display_data(self, data: Dict) -> str:
        pass

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    @abstractmethod
    def _get_data(self, *args) -> Union[Dict, List]:
        pass

    def _process_data(self, data_retrieval_failed: bool,
                      failure_args: List[Any], success_args: List[Any]) -> Dict:
        if data_retrieval_failed:
            return self._process_error(*failure_args)
        else:
            return self._process_retrieved_data(*success_args)

    @abstractmethod
    def _process_error(self, *args) -> Dict:
        pass

    @abstractmethod
    def _process_retrieved_data(self, *args) -> Dict:
        pass

    @abstractmethod
    def _monitor(self) -> None:
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
                self._monitor()
            except MessageWasNotDeliveredException as e:
                # Log the fact that the message could not be sent. Sleep just
                # because there is no use in consuming a lot of resources until
                # the problem is fixed.
                self.logger.exception(e)
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

            self.logger.debug("Sleeping for %s seconds.", self.monitor_period)

            # Use the BlockingConnection sleep to avoid dropped connections
            self.rabbitmq.connection.sleep(self.monitor_period)

    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
