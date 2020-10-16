# TODO: A system monitor starter -> Handling all errors from monitoring and
#     : always restarting on error
# TODO: A configs manager communicator, determining how many processes to start
#     : according to the configs manager message. We must kill and create
#     : processes dynamically
# TODO: Must tackle if parent dies, children must die also
import logging
import os
from typing import Dict

import pika.exceptions

from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi


class MonitorManager:
    def __init__(self, logger: logging.Logger):
        self._logger = logger  # TODO: General logger to be passed from outside
        self._config_process_dict = {}

        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def config_process_dict(self) -> Dict:
        return self._config_process_dict

    def _initialize_rabbitmq(self) -> None:
        pass

    def _listen_for_configs(self) -> None:
        pass

    def _process_configs(
            self, ch, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def manage(self) -> None:
        pass
