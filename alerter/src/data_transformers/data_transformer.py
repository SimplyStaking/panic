import logging
import os
import sys
from abc import abstractmethod
from queue import Queue
from types import FrameType
from typing import Dict, Union

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.component import Component
from src.data_store.redis.redis_api import RedisApi
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.monitorables.repo import GitHubRepo
from src.monitorables.system import System
from src.utils.constants import HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class DataTransformer(Component):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi) -> None:
        self._transformer_name = transformer_name
        self._logger = logger
        self._redis = redis
        self._transformed_data = {}
        self._data_for_saving = {}
        self._data_for_alerting = {}
        self._state = {}

        # Set a max queue size so that if the data transformer is not able to
        # send data, old data can be pruned
        max_queue_size = int(os.environ[
                                 'DATA_TRANSFORMER_PUBLISHING_QUEUE_SIZE'])
        self._publishing_queue = Queue(max_queue_size)

        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)
        super().__init__()

    def __str__(self) -> str:
        return self.transformer_name

    @property
    def transformer_name(self) -> str:
        return self._transformer_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def transformed_data(self) -> Dict:
        return self._transformed_data

    @property
    def data_for_saving(self) -> Dict:
        return self._data_for_saving

    @property
    def data_for_alerting(self) -> Dict:
        return self._data_for_alerting

    @property
    def state(self) -> Dict[str, Union[System, GitHubRepo]]:
        return self._state

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def publishing_queue(self) -> Queue:
        return self._publishing_queue

    @abstractmethod
    def _initialize_rabbitmq(self) -> None:
        pass

    @abstractmethod
    def load_state(self, monitorable: Union[System, GitHubRepo]) \
            -> Union[System, GitHubRepo]:
        pass

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    @abstractmethod
    def _update_state(self) -> None:
        pass

    @abstractmethod
    def _process_transformed_data_for_saving(self) -> None:
        pass

    @abstractmethod
    def _process_transformed_data_for_alerting(self) -> None:
        pass

    @abstractmethod
    def _transform_data(self, data: Dict) -> None:
        pass

    @abstractmethod
    def _place_latest_data_on_queue(self) -> None:
        pass

    def _send_data(self) -> None:
        empty = True
        if not self.publishing_queue.empty():
            empty = False
            self.logger.info("Attempting to send all data waiting in the "
                             "publishing queue ...")

        # Try sending the data in the publishing queue one by one. Important,
        # remove an item from the queue only if the sending was successful, so
        # that if an exception is raised, that message is not popped
        while not self.publishing_queue.empty():
            data = self.publishing_queue.queue[0]
            self.rabbitmq.basic_publish_confirm(
                exchange=data['exchange'], routing_key=data['routing_key'],
                body=data['data'], is_body_dict=True,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.logger.debug("Sent {} to '{}' exchange"
                              .format(data['data'], data['exchange']))
            self.publishing_queue.get()
            self.publishing_queue.task_done()

        if not empty:
            self.logger.info("Successfully sent all data from the publishing "
                             "queue")

    @abstractmethod
    def _process_raw_data(self, ch: BlockingChannel,
                          method: pika.spec.Basic.Deliver,
                          properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        pass

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.worker',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.info("Sent heartbeat to '{}' exchange".format(
            HEALTH_CHECK_EXCHANGE))

    def start(self) -> None:
        self._initialize_rabbitmq()
        while True:
            try:
                # Before listening for new data send the data waiting to be sent
                # in the publishing queue. If the message is not routed, start
                # consuming and perform sending later.
                if not self.publishing_queue.empty():
                    try:
                        self._send_data()
                    except MessageWasNotDeliveredException as e:
                        self.logger.exception(e)

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

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.rabbitmq.disconnect_till_successful()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
