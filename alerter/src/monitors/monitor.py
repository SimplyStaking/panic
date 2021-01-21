import logging
import os
import signal
import sys
from abc import ABC, abstractmethod
from types import FrameType
from typing import Dict

import pika.exceptions

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants import RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class Monitor(ABC):

    def __init__(self, monitor_name: str, logger: logging.Logger,
                 monitor_period: int) -> None:
        super().__init__()

        self._monitor_name = monitor_name
        self._logger = logger
        self._monitor_period = monitor_period
        self._data = {}
        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)
        self._data_retrieval_failed = False

        # Handle termination signals by stopping the monitor gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.monitor_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def monitor_period(self) -> int:
        return self._monitor_period

    @property
    def monitor_name(self) -> str:
        return self._monitor_name

    @property
    def data(self) -> Dict:
        return self._data

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def data_retrieval_failed(self) -> bool:
        return self._data_retrieval_failed

    @abstractmethod
    def status(self) -> str:
        pass

    def load_monitor_state(self) -> None:
        pass

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, 'direct', False,
                                       True, False, False)
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    @abstractmethod
    def _get_data(self) -> None:
        pass

    def _process_data(self, error: PANICException) -> None:
        if self.data_retrieval_failed:
            self._process_data_retrieval_failed(error)
        else:
            self._process_data_retrieval_successful()

    @abstractmethod
    def _process_data_retrieval_failed(self, error: PANICException) -> None:
        pass

    @abstractmethod
    def _process_data_retrieval_successful(self) -> None:
        pass

    @abstractmethod
    def _send_data(self) -> None:
        pass

    @abstractmethod
    def _monitor(self) -> None:
        pass

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.worker',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.info("Sent heartbeat to '%s' exchange",
                         HEALTH_CHECK_EXCHANGE)

    def start(self) -> None:
        self._initialize_rabbitmq()
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
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

            self.logger.debug("Sleeping for %s seconds.", self.monitor_period)

            # Use the BlockingConnection sleep to avoid dropped connections
            self.rabbitmq.connection.sleep(self.monitor_period)

    def disconnect_from_rabbit(self) -> None:
        """
        Disconnects the component from RabbitMQ
        :return:
        """
        self.rabbitmq.disconnect_till_successful()

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

# TODO: There are some monitors which may require redis. Therefore consider
#     : adding redis here in the future.
