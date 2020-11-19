import os
import logging

from src.message_broker.rabbitmq import RabbitMQApi


class HeartbeatPublisher:
    def __init__(self, interval: int, logger: logging.Logger):
        self._interval = interval
        self._logger = logger

        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    # def _initialize_rabbitmq(self) -> None:
    #     self.rabbitmq.connect_till_successful()
    #     self.logger.info("Setting delivery confirmation on RabbitMQ channel")
    #     self.rabbitmq.confirm_delivery()
    #     self.logger.info("Creating '{}' exchange".format(RAW_DATA_EXCHANGE))
    #     self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, 'direct', False, True,
    #                                    False, False)

    def start(self) -> None:
        pass
