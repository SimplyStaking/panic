import json
from configparser import ConfigParser, NoOptionError, NoSectionError, \
    ParsingError
from logging import Logger
from typing import Dict

import pika
from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.exceptions import ConnectionNotInitializedException, \
    MessageWasNotDeliveredException

ALERT_ROUTER_CONFIGS_QUEUE_NAME = "alert_router_configs_queue"
ALERT_ROUTER_INPUT_QUEUE_NAME = "alert_router_input_queue"


class AlertRouter:
    def __init__(self, logger: Logger, alert_input_channel: str,
                 alert_output_channel: str, config_input_channel: str,
                 rabbit_ip: str):

        self._config = {}
        self._logger = logger
        self._alert_input_channel = alert_input_channel
        self._alert_output_channel = alert_output_channel
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
                    "channels.*"
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

                # Declare output exchange
                self._logger.info("Creating %s exchange",
                                  self._alert_output_channel)
                self._rabbit.exchange_declare(
                    self._alert_output_channel, "topic", False, True, False,
                    False
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

        recv_config = ConfigParser()
        recv_config.read_dict(json.loads(body))
        config_filename = method.routing_key

        self._logger.info("Received a new configuration from %s",
                          config_filename)
        self._logger.debug("recv_config = %s", recv_config)

        previous_config = self._config[config_filename]
        self._config[config_filename] = {}
        # Taking what we need, and checking types
        try:
            for key in recv_config:
                self._config[config_filename][key] = {
                    'id': recv_config.get(key, 'id'),
                    'info': recv_config.getboolean(key, 'info'),
                    'warning': recv_config.getboolean(key, 'warning'),
                    'critical': recv_config.getboolean(key, 'critical'),
                    'error': recv_config.getboolean(key, 'error')
                }
        except (NoOptionError, NoSectionError) as missing_error:
            self._logger.error(
                "The configuration file %s is missing some configs",
                config_filename)
            self._logger.error(missing_error.message)
            self._logger.warning(
                "The previous configuration will be used instead")
            self._config[config_filename] = previous_config
        except (ParsingError, ValueError) as parsing_error:
            self._logger.error(
                "The configuration file %s has an incorrect entry",
                config_filename)
            self._logger.error(parsing_error.message)
            self._logger.warning(
                "The previous configuration will be used instead")
            self._config[config_filename] = previous_config

    def _process_alert(self, ch: BlockingChannel,
                       method: pika.spec.Basic.Deliver,
                       properties: pika.spec.BasicProperties,
                       body: bytes) -> None:
        recv_alert: Dict = json.loads(body)

        # Where to route this alert to
        send_to_ids = [
            channel.get('id') for channel_type in self._config.values()
            for channel in channel_type.values()
            if channel.get(recv_alert.get('severity').lower())
        ]
        while True:
            try:
                for channel_id in send_to_ids:
                    send_alert: Dict = {**recv_alert,
                                        'destination_id': channel_id}

                    self._rabbit.basic_publish_confirm(
                        self._alert_output_channel, f"channel.{channel_id}",
                        send_alert,
                        mandatory=True, is_body_dict=True,
                        properties=BasicProperties(delivery_mode=2)
                    )
                    self._logger.info("Configuration update sent")
                break
            except MessageWasNotDeliveredException as mwnde:
                self._logger.error("Config was not successfully sent")
                self._logger.exception(mwnde)
                self._logger.info("Will attempt sending the log again")
            except (
                    ConnectionNotInitializedException, AMQPConnectionError
            ) as connection_error:
                # If the connection is not initalized or there is a connection
                # error, we need to restart the connection and try it again
                self._logger.error("There has been a connection error")
                self._logger.exception(connection_error)
                self._logger.info("Restarting the connection")
                self._rabbit.connect_till_successful()

                self._logger.info("Connection restored, will attempt again")
            except AMQPChannelError:
                # This error would have already been logged by the RabbitMQ
                # logger and handled by RabbitMQ. As a result we don't need to
                # anything here, just re-try.
                continue

    def start_listening(self) -> None:
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
