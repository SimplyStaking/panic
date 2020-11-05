import logging
import os
import time
from abc import ABC, abstractmethod
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
    def _send_data_to_alert_router(self, *args) -> None:
        pass

    @abstractmethod
    def _alert_classifier_process(self) -> None:
        pass

    def start_alert_classification(self) -> None:
        self._initialize_alerter()
        while True:
            try:
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
