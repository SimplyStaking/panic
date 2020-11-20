import logging
import os
import signal
import sys
from types import FrameType

import pika
import pika.exceptions

from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import HEARTBEAT_EXCHANGE
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class HeartbeatPublisher:
    def __init__(self, interval: int, logger: logging.Logger):
        self._interval = interval
        self._logger = logger

        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

        # Handle termination signals by stopping the monitor gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '{}' exchange".format(HEARTBEAT_EXCHANGE))
        self.rabbitmq.exchange_declare(HEARTBEAT_EXCHANGE, 'direct', False,
                                       True, False, False)

    def _send_heartbeat(self) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEARTBEAT_EXCHANGE, routing_key='heartbeat', body='ping',
            is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to '{}' exchange".format(
            HEARTBEAT_EXCHANGE))

    def start(self) -> None:
        self._initialize_rabbitmq()
        while True:
            try:
                self._send_heartbeat()
            except MessageWasNotDeliveredException as e:
                # Log the fact that the heartbeat could not be sent and sleep
                # until the next round of publishing.
                self.logger.exception(e)
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

            self.logger.debug("Sleeping for %s seconds.", self.interval)

            # Use the BlockingConnection sleep to avoid dropped connections
            self.rabbitmq.connection.sleep(self.interval)

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.rabbitmq.disconnect_till_successful()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
