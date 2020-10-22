import logging
import os
from typing import Dict

import pika.exceptions

from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.logging import log_and_print


class MonitorsManager:
    def __init__(self, logger: logging.Logger, name: str):
        self._logger = logger
        self._config_process_dict = {}
        self._name = name

        # rabbit_ip = os.environ["RABBIT_IP"]
        rabbit_ip = "localhost"
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

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

    def _initialize_rabbitmq(self) -> None:
        pass

    def _listen_for_configs(self) -> None:
        self.rabbitmq.start_consuming()

    def _process_configs(
            self, ch, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def manage(self) -> None:
        log_and_print('{} started.'.format(self), self.logger)
        self._initialize_rabbitmq()
        while True:
            try:
                self._listen_for_configs()
            except pika.exceptions.AMQPChannelError:
                # Error would have already been logged by RabbitMQ logger. If
                # there is a channel error, the RabbitMQ interface creates a new
                # channel, therefore perform another managing round without
                # sleeping
                continue
            except pika.exceptions.AMQPConnectionError as e:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e
