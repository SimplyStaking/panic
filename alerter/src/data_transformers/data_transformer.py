import logging
import sys
from abc import abstractmethod
from types import FrameType
from typing import Dict, Tuple

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.publisher_subscriber import (
    QueuingPublisherSubscriberComponent)
from src.data_store.redis.redis_api import RedisApi
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import Monitorable


class DataTransformer(QueuingPublisherSubscriberComponent):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi, rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0) -> None:
        self._transformer_name = transformer_name
        self._redis = redis
        self._state = {}

        super().__init__(logger, rabbitmq, max_queue_size)

    def __str__(self) -> str:
        return self.transformer_name

    @property
    def transformer_name(self) -> str:
        return self._transformer_name

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def state(self) -> Dict[str, Monitorable]:
        return self._state

    @abstractmethod
    def load_state(self, monitorable: Monitorable) -> Monitorable:
        pass

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    @abstractmethod
    def _update_state(self, transformed_data: Dict) -> None:
        pass

    @abstractmethod
    def _process_transformed_data_for_saving(self,
                                             transformed_data: Dict) -> Dict:
        pass

    @abstractmethod
    def _process_transformed_data_for_alerting(self,
                                               transformed_data: Dict) -> Dict:
        pass

    @abstractmethod
    def _transform_data(self, data: Dict) -> Tuple[Dict, Dict, Dict]:
        pass

    @abstractmethod
    def _place_latest_data_on_queue(self, transformed_data: Dict,
                                    data_for_alerting: Dict,
                                    data_for_saving: Dict) -> None:
        pass

    @abstractmethod
    def _process_raw_data(self, ch: BlockingChannel,
                          method: pika.spec.Basic.Deliver,
                          properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        pass

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

    def start(self) -> None:
        self._initialise_rabbitmq()
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
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
