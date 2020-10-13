import logging
import os
from typing import Optional, Dict

from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi


# TODO: A monitor starters process which manages processes

class Monitor:

    def __init__(self, monitor_name: str, logger: logging.Logger,
                 redis: Optional[RedisApi] = None) -> None:
        super().__init__()

        self._monitor_name = monitor_name
        self._logger = logger
        self._redis = redis
        self._data = {}
        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    def __str__(self) -> str:
        return self.monitor_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def redis(self) -> Optional[RedisApi]:
        return self._redis

    @property
    def monitor_name(self) -> str:
        return self._monitor_name

    @property
    def data(self) -> Dict:
        return self._data

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    def status(self) -> str:
        pass

    def load_monitor_state(self) -> None:
        pass

    def _get_data(self) -> None:
        pass

    def _process_data(self) -> None:
        pass

    def _send_data(self) -> None:
        pass

    def _monitor(self) -> None:
        # TODO: Must add error handling on the calling function. Also the
        #       calling function must first connect with RabbitMQ, and perform
        #       the RabbitMQ initializations (like queue creation). The calling
        #       function must also perform all error handling due to errors that
        #       may occur in the 3 functions below (such as urlib3 errors). We
        #       must also handle the case when a metric name changes (although
        #       this might be handled inside the prometheus get function, but
        #       still reminder to keep a general exception handler, and rabbit
        #       specific errors. On the outside we must also post the status to
        #       the logs
        self._get_data()
        self._process_data()
        self._send_data()

    def start(self) -> None:
        # TODO: Must perform good error handling for everything
        pass

    def stop(self) -> None:
        # TODO: Must do proper cleaning and closing
        pass

        # TODO: Mark will send configs through RABBITMQ NOT REDIS
