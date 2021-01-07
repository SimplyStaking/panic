import logging
import signal
import sys
from abc import ABC, abstractmethod
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils import env
from src.utils.constants import HEALTH_CHECK_EXCHANGE
from src.utils.logging import log_and_print


class MonitorsManager(ABC):
    def __init__(self, logger: logging.Logger, name: str):
        self._logger = logger
        self._config_process_dict = {}
        self._name = name

        rabbit_ip = env.RABBIT_IP
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

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
    def config_process_dict(self) -> Dict:
        return self._config_process_dict

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

    def manage(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialize_rabbitmq()
        while True:
            try:
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    # If termination signals are received, terminate all child process and
    # close the connection with rabbit mq before exiting
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and any running monitors will be stopped "
                      "gracefully. Afterwards the {} process will exit."
                      .format(self, self), self.logger)
        self.rabbitmq.disconnect_till_successful()

        for config_id, process_details in self.config_process_dict.items():
            log_and_print("Terminating the process of {}".format(config_id),
                          self.logger)
            process = process_details['process']
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
