import json
import sys
from configparser import ConfigParser, NoOptionError, NoSectionError
from datetime import datetime
from logging import Logger
from types import FrameType
from typing import Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError

from src.abstract import QueuingPublisherComponent
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import CONFIG_EXCHANGE, STORE_EXCHANGE, \
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE, ALERT_ROUTER_CONFIGS_QUEUE_NAME
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print

_ALERT_ROUTER_INPUT_QUEUE_NAME = 'alert_router_input_queue'
_HEARTBEAT_QUEUE_NAME = 'alert_router_ping'


class AlertRouter(QueuingPublisherComponent):
    def __init__(self, name: str, logger: Logger, rabbit_ip: str,
                 enable_console_alerts: bool):

        self._name = name
        self._rabbit = RabbitMQApi(logger.getChild("rabbitmq"), host=rabbit_ip)
        self._enable_console_alerts = enable_console_alerts

        self._config = {}

        self._logger = logger
        super().__init__(logger, self._rabbit,
                         env.ALERT_ROUTER_PUBLISHING_QUEUE_SIZE)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    def _initialise_rabbit(self) -> None:
        """
        Initialises the rabbit connection and the exchanges needed
        :return: None
        """
        self._rabbit.connect_till_successful()
        self._logger.info(
            "Setting delivery confirmation on RabbitMQ channel")
        self._rabbit.confirm_delivery()

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self._publishing_queue.maxsize / 5)
        self._rabbit.basic_qos(prefetch_count=prefetch_count)

        self._declare_exchange_and_bind_queue(
            ALERT_ROUTER_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE, 'topic',
            'channels.*'
        )
        self._rabbit.basic_consume(
            queue=ALERT_ROUTER_CONFIGS_QUEUE_NAME,
            on_message_callback=self._process_configs, auto_ack=False,
            exclusive=False, consumer_tag=None)

        self._declare_exchange_and_bind_queue(
            _ALERT_ROUTER_INPUT_QUEUE_NAME, ALERT_EXCHANGE, 'topic',
            'alert_router.*'
        )
        self._rabbit.basic_consume(
            queue=_ALERT_ROUTER_INPUT_QUEUE_NAME,
            on_message_callback=self._process_alert, auto_ack=False,
            exclusive=False, consumer_tag=None
        )

        # Declare store exchange just in case it hasn't been declared
        # yet
        self._rabbit.exchange_declare(exchange=STORE_EXCHANGE,
                                      exchange_type='direct', passive=False,
                                      durable=True, auto_delete=False,
                                      internal=False)

        self._declare_exchange_and_bind_queue(
            _HEARTBEAT_QUEUE_NAME, HEALTH_CHECK_EXCHANGE, 'topic', 'ping'
        )

        self._logger.debug("Declaring consuming intentions")
        self._rabbit.basic_consume(_HEARTBEAT_QUEUE_NAME, self._process_ping,
                                   True, False, None)

    def _declare_exchange_and_bind_queue(self, queue_name: str,
                                         exchange_name: str, exchange_type: str,
                                         routing_key: str) -> None:
        """
        Declare the specified exchange and queue and binds that queue to the
        exchange
        :param exchange_type:
        :param queue_name: The queue to declare and bind to the exchange
        :param exchange_name: The exchange to declare and bind the queue to
        :return: None
        """
        self._logger.info("Creating %s exchange", exchange_name)
        self._rabbit.exchange_declare(
            exchange_name, exchange_type, False, True, False, False
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

        self._logger.debug("Got a lock on the config")
        previous_config = self._config.get(config_filename, None)
        self._config[config_filename] = {}

        # Only take from the config if it is not empty
        if recv_config:
            # Taking what we need, and checking types
            try:
                for key in recv_config.sections():
                    self._config[config_filename][key] = self._extract_config(
                        recv_config[key], config_filename
                    )
            except (NoOptionError, NoSectionError) as missing_error:
                self._logger.error(
                    "The configuration file %s is missing some configs",
                    config_filename)
                self._logger.error(missing_error.message)
                self._logger.warning(
                    "The previous configuration will be used instead")
                self._config[config_filename] = previous_config
            except Exception as e:
                self._logger.error("Encountered an error when reading the "
                                   "configuration files")
                self._logger.exception(e)
                self._logger.warning(
                    "The previous configuration will be used instead")
                self._config[config_filename] = previous_config
            self._logger.debug(self._config)
        self._logger.debug("Removed the lock from the config dict")

        self._rabbit.basic_ack(method.delivery_tag, False)

    def _process_alert(self, ch: BlockingChannel,
                       method: pika.spec.Basic.Deliver,
                       properties: pika.spec.BasicProperties,
                       body: bytes) -> None:
        recv_alert: Dict = json.loads(body)

        # If the alert is empty, just acknowledge and return
        if not recv_alert:
            self._rabbit.basic_ack(method.delivery_tag, False)
            return

        self._logger.debug("recv_alert = %s", recv_alert)
        # Where to route this alert to
        self._logger.debug("Got a lock on the config")
        self._logger.debug("Obtaining list of channels to alert")
        self._logger.debug(
            [channel.get('id') for channel_type in self._config.values()
             for channel in channel_type.values()])
        send_to_ids = [
            channel.get('id') for channel_type in self._config.values()
            for channel in channel_type.values()
            if channel.get(recv_alert.get('severity').lower()) and
               recv_alert.get('parent_id') in channel.get('parent_ids')
        ]

        self._logger.debug("Removed the lock from the config dict")
        self._logger.debug("send_to_ids = %s", send_to_ids)

        for channel_id in send_to_ids:
            send_alert: Dict = {**recv_alert,
                                'destination_id': channel_id}

            self._logger.debug("Queuing %s to be sent to %s",
                               send_alert, channel_id)

            self._push_to_queue(send_alert, ALERT_EXCHANGE,
                                "channel.{}".format(channel_id),
                                mandatory=True)
            self._logger.debug("Routed Alert queued")

        # Enqueue once to the console
        if self._enable_console_alerts:
            self._push_to_queue(
                {**recv_alert, 'destination_id': 'console'},
                ALERT_EXCHANGE, 'channel.console', mandatory=True)

        self._push_to_queue(
            {**recv_alert, 'destination_id': 'log'},
            ALERT_EXCHANGE, 'channel.log', mandatory=True)

        self._rabbit.basic_ack(method.delivery_tag, False)

        # Enqueue once to the data store
        self._push_to_queue(recv_alert, STORE_EXCHANGE, 'alert')

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as message is residing in the
            # publisher queue.
            self._logger.exception(e)

    def _process_ping(self, ch: BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:

        self._logger.debug("Received %s. Let's pong", body)
        heartbeat = {
            'component_name': self.name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp(),
        }

        self._rabbit.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key='heartbeat.worker', body=heartbeat,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self._logger.info("Sent heartbeat to %s exchange",
                          HEALTH_CHECK_EXCHANGE)

    def start(self) -> None:
        log_and_print("{} started.".format(self), self._logger)
        self._initialise_rabbit()
        while True:
            try:
                # Before listening for new data send the data waiting to be sent
                # in the publishing queue. If the message is not routed, start
                # consuming and perform sending later.
                try:
                    self._send_data()
                except MessageWasNotDeliveredException as e:
                    self._logger.exception(e)

                self._logger.info("Starting the alert router listeners")
                self._rabbit.start_consuming()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self._logger.exception(e)
                raise e

    def disconnect(self) -> None:
        """
        Disconnects the component from RabbitMQ
        :return:
        """
        self._rabbit.disconnect_till_successful()

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self._logger)
        self.disconnect()
        log_and_print("{} terminated.".format(self), self._logger)
        sys.exit()

    @staticmethod
    def _extract_config(section, config_filename: str) -> Dict[str, str]:
        if "twilio" in config_filename:
            return {
                'id': section.get('id'),
                'parent_ids': section.get('parent_ids').split(","),
                'info': False,
                'warning': False,
                'error': False,
                'critical': True,
            }

        return {
            'id': section.get('id'),
            'parent_ids': section.get('parent_ids').split(","),
            'info': section.getboolean('info'),
            'warning': section.getboolean('warning'),
            'error': section.getboolean('error'),
            'critical': section.getboolean('critical'),
        }
