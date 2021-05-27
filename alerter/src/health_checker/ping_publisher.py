import json
import logging
import signal
import sys
from datetime import datetime
from types import FrameType

import pika
import pika.exceptions

from src.data_store.redis import Keys, RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          PING_ROUTING_KEY, TOPIC)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class PingPublisher:
    def __init__(self, interval: int, logger: logging.Logger, redis: RedisApi,
                 name: str) -> None:
        self._name = name
        self._interval = interval
        self._logger = logger
        self._redis = redis

        rabbit_ip = env.RABBIT_IP
        self._rabbitmq = RabbitMQApi(
            logger=self.logger.getChild(RabbitMQApi.__name__), host=rabbit_ip)

        # Handle termination signals by stopping the monitor gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def ping(self) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=PING_ROUTING_KEY,
            body='ping', is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.debug("Sent data to '%s' exchange", HEALTH_CHECK_EXCHANGE)

    def start(self) -> None:
        self._initialise_rabbitmq()
        while True:
            try:
                self.ping()
            except MessageWasNotDeliveredException as e:
                # Log the fact that we could not ping the alerter and sleep
                # until the next round of publishing.
                self.logger.exception(e)
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

            self.logger.debug("Saving %s heartbeat to Redis", self)
            key_heartbeat = Keys.get_component_heartbeat(self.name)
            ping_pub_heartbeat = {'component_name': self.name,
                                  'timestamp': datetime.now().timestamp()}
            transformed_ping_pub_heartbeat = json.dumps(ping_pub_heartbeat)
            self.redis.set(key_heartbeat, transformed_ping_pub_heartbeat)
            ret = self.redis.set(key_heartbeat, transformed_ping_pub_heartbeat)
            if ret is None:
                self.logger.error("Could not save %s=%s to Redis.",
                                  key_heartbeat, transformed_ping_pub_heartbeat)

            self.logger.debug("Sleeping for %s seconds.", self.interval)

            # Use the BlockingConnection sleep to avoid dropped connections
            self.rabbitmq.connection.sleep(self.interval)

    def disconnect_from_rabbit(self) -> None:
        """
        Disconnects the component from RabbitMQ
        :return:
        """
        self.rabbitmq.disconnect_till_successful()

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
