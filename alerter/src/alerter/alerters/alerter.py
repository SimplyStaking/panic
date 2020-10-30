import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Dict

import pika.exceptions

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException

class Alerter(ABC):

    def __init__(self, alerter_name: str, logger: logging.Logger) -> None:
        super().__init__()

        self._alerter_name = alerter_name
        self._logger = logger
        self._data = {}
        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    def __str__(self) -> str:
        return self.alerter_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def alerter_name(self) -> str:
        return self._alerter_name

    @property
    def data(self) -> Dict:
        return self._data

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @abstractmethod
    def status(self) -> str:
        pass

    def load_monitor_state(self) -> None:
        pass

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info('Setting delivery confirmation on RabbitMQ channel')
        self.rabbitmq.confirm_delivery()
        self.logger.info('Creating \'raw_data\' exchange')
        self.rabbitmq.exchange_declare('raw_data', 'direct', False, True, False,
                                       False)

    @abstractmethod
    def _alert(self) -> None:
        pass

    def start_alerting(self) -> None:
        self._initialize_rabbitmq()
        while True:
            try:
                self._alert()
            except pika.exceptions.AMQPChannelError:
                # Error would have already been logged by RabbitMQ logger. If
                # there is a channel error, the RabbitMQ interface creates a new
                # channel, therefore perform another monitoring round without
                # sleeping
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