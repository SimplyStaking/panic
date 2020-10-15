import logging
import os
from typing import Dict

from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.exceptions import PANICException


class Monitor:

    def __init__(self, monitor_name: str, logger: logging.Logger,
                 monitor_period: int) -> None:
        super().__init__()

        self._monitor_name = monitor_name
        self._logger = logger
        self._monitor_period = monitor_period
        self._data = {}
        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)
        self._data_retrieval_failed = False

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

    def status(self) -> str:
        pass

    def load_monitor_state(self) -> None:
        pass

    def _initialize_rabbitmq(self) -> None:
        pass

    def _get_data(self) -> None:
        pass

    def _process_data(self, error: PANICException) -> None:
        if self.data_retrieval_failed:
            self._process_data_retrieval_failed(error)
        else:
            self._process_data_retrieval_successful()

    def _process_data_retrieval_failed(self, error: PANICException) -> None:
        pass

    def _process_data_retrieval_successful(self) -> None:
        pass

    def _send_data(self) -> None:
        pass

    def _monitor(self) -> None:
        pass

    def start(self) -> None:
        pass

    def close_rabbitmq_connection(self) -> None:
        pass

# TODO: There are some monitors which may require redis. Therefore consider
#     : adding redis here in the future.
