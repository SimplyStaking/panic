from abc import abstractmethod
from logging import Logger
from multiprocessing.context import Process
from typing import Set, Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract import Component
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import HEALTH_CHECK_EXCHANGE


class ChannelManager(Component):
    def __init__(self, logger: Logger, rabbit_ip: str):
        super().__init__()
        self._logger = logger
        self._process_set: Set[Process] = set()
        self._rabbit = RabbitMQApi(logger=logger.getChild(RabbitMQApi.__name__),
                                   host=rabbit_ip)

    @abstractmethod
    def _initialise_rabbit(self) -> None:
        """Initialise the RabbitMQ connection, exchanges and queues here"""
        pass

    @abstractmethod
    def _process_config(self, ch: BlockingChannel,
                        method: pika.spec.Basic.Deliver,
                        properties: pika.spec.BasicProperties,
                        body: bytes) -> None:
        """
        All subclasses must process a config received via rabbit through which
        the processes will be created
        """
        pass

    @abstractmethod
    def _process_ping(self, ch: BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        """
        All subclasses must process a ping received via rabbit through which the
        heartbeat
        """
        pass

    def _listen_for_data(self) -> None:
        self._rabbit.start_consuming()

    def _send_heartbeat(self, data_to_send: Dict) -> None:
        self._rabbit.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.manager',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self._logger.info("Sent heartbeat to '{}' exchange".format(
            HEALTH_CHECK_EXCHANGE))

    @abstractmethod
    def manage(self) -> None:
        pass

