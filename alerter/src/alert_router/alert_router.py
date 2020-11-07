import json
from logging import Logger

from typing import Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.alert import Alert
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.exceptions import ConnectionNotInitializedException

ALERT_ROUTER_CONFIGS_QUEUE_NAME = "alert_router_configs_queue"
ALERT_ROUTER_INPUT_QUEUE_NAME = "alert_router_input_queue"


class AlertRouter:
    def __init__(self, logger: Logger, alert_input_channel: str,
                 config_input_channel: str, rabbit_ip: str):

        self._config = {}
        self._logger = logger
        self._alert_input_channel = alert_input_channel
        self._config_input_channel = config_input_channel
        self._rabbit = RabbitMQApi(logger.getChild("rabbitmq"), host=rabbit_ip)
        self._initialise_rabbit()

    def _initialise_rabbit(self) -> None:
        """
        Initialises the rabbit connection and the exchanges needed
        :return: None
        """
        while True:
            try:
                self._rabbit.connect_till_successful()
                self._logger.info(
                    "Setting delivery confirmation on RabbitMQ channel")
                self._rabbit.confirm_delivery()

                self._declare_exchange_and_bind_queue(
                    ALERT_ROUTER_CONFIGS_QUEUE_NAME, self._config_input_channel,
                    "general.alert_router"
                )
                self._rabbit.basic_consume(
                    queue=ALERT_ROUTER_CONFIGS_QUEUE_NAME,
                    on_message_callback=self._process_configs, auto_ack=False,
                    exclusive=False, consumer_tag=None)

                self._declare_exchange_and_bind_queue(
                    ALERT_ROUTER_INPUT_QUEUE_NAME, self._alert_input_channel,
                    "#"
                )
                self._rabbit.basic_consume(
                    queue=ALERT_ROUTER_INPUT_QUEUE_NAME,
                    on_message_callback=self._process_alert, auto_ack=False,
                    exclusive=False, consumer_tag=None
                )

            except (ConnectionNotInitializedException,
                    AMQPConnectionError) as connection_error:
                # Should be impossible, but since exchange_declare can throw
                # it we shall ensure to log that the error passed through here
                # too.
                self._logger.error(
                    "Something went wrong that meant a connection was not made")
                self._logger.error(connection_error.message)
                raise connection_error
            except AMQPChannelError:
                # This error would have already been logged by the RabbitMQ
                # logger and handled by RabbitMQ. As a result we don't need to
                # anything here, just re-try.
                continue

    def _declare_exchange_and_bind_queue(self, queue_name: str,
                                         exchange_name: str,
                                         routing_key: str) -> None:
        """
        Declare the specified exchange and queue and binds that queue to the
        exchange
        :param queue_name: The queue to declare and bind to the exchange
        :param exchange_name: The exchange to declare and bind the queue to
        :return: None
        """
        self._logger.info("Creating %s exchange", exchange_name)
        self._rabbit.exchange_declare(
            exchange_name, "topic", False, True, False, False
        )
        self._logger.info("Creating and binding queue for %s exchange",
                          exchange_name)
        self._logger.debug("Creating queue %s", queue_name)
        self._rabbit.queue_declare(queue_name, False, True, False, False)
        self._logger.debug("Binding queue %s to %s exchange", queue_name,
                           exchange_name)
        self._rabbit.queue_bind(queue_name, exchange_name, routing_key)

    def _process_configs(self, ch: BlockingChannel,
                         method: pika.spec.Basic.Deliver,
                         properties: pika.spec.BasicProperties,
                         body: bytes) -> None:
        """
        Sets the config whenever there is a new config via rabbit
        :param config: The configuration to set
        :return: None
        """
        sent_config = json.loads(body)

        self._logger.info("Received a new configuration")
        self._logger.debug("cofnig = %s", sent_config)
        self._config = sent_config  # TODO into object

    def _process_alert(self, alert: Alert) -> None:
        # see web installer part
        pass

    def _start_listening(self) -> None:
        while True:
            try:
                self._rabbit.start_consuming()
            except (ConnectionNotInitializedException,
                    AMQPConnectionError) as connection_error:
                # Should be impossible, but since exchange_declare can throw
                # it we shall ensure to log that the error passed through here
                # too.
                self._logger.error(
                    "Something went wrong that meant a connection was not made")
                self._logger.error(connection_error.message)
                raise connection_error
            except AMQPChannelError:
                # This error would have already been logged by the RabbitMQ
                # logger and handled by RabbitMQ. As a result we don't need to
                # anything here, just re-try.
                continue


    def run(self):
        pass
