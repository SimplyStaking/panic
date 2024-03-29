import json
import sys
from configparser import (ConfigParser, NoOptionError, NoSectionError,
                          SectionProxy)
from datetime import datetime
from json import JSONDecodeError
from logging import Logger
from types import FrameType
from typing import Dict, List

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError

from src.abstract.publisher_subscriber import (
    QueuingPublisherSubscriberComponent
)
from src.alerter.alert_severities import Severity
from src.data_store.redis import Keys, RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (
    ALERT_ROUTER_CONFIGS_QUEUE_NAME, ALERT_ROUTER_CONFIGS_ROUTING_KEY,
    CONFIG_EXCHANGE, TOPIC, ALERT_EXCHANGE, ALERT_ROUTER_INPUT_QUEUE_NAME,
    ALERT_ROUTER_INPUT_ROUTING_KEY, STORE_EXCHANGE,
    ALERT_ROUTER_HEARTBEAT_QUEUE_NAME, PING_ROUTING_KEY, HEALTH_CHECK_EXCHANGE,
    CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE,
    CONSOLE_HANDLER_INPUT_ROUTING_KEY, LOG_HANDLER_INPUT_ROUTING_KEY,
    ALERT_STORE_INPUT_ROUTING_KEY, HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.exceptions import (
    MessageWasNotDeliveredException, MissingKeyInConfigException
)
from src.utils.logging import log_and_print

_ROUTED_ALERT_QUEUED_LOG_MESSAGE = "Routed Alert queued"


class AlertRouter(QueuingPublisherSubscriberComponent):
    def __init__(self, name: str, logger: Logger, rabbit_ip: str, redis_ip: str,
                 redis_db: int, redis_port: int, unique_alerter_identifier: str,
                 enable_console_alerts: bool, enable_log_alerts: bool):

        self._name = name
        self._redis = RedisApi(logger.getChild(RedisApi.__name__),
                               host=redis_ip, db=redis_db, port=redis_port,
                               namespace=unique_alerter_identifier)
        self._enable_console_alerts = enable_console_alerts
        self._enable_log_alerts = enable_log_alerts

        self._config = {}

        super().__init__(logger, RabbitMQApi(
            logger=logger.getChild(RabbitMQApi.__name__), host=rabbit_ip),
                         env.ALERT_ROUTER_PUBLISHING_QUEUE_SIZE)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    def _initialise_rabbitmq(self) -> None:
        """
        Initialises the rabbit connection and the exchanges needed
        :return: None
        """
        self._rabbitmq.connect_till_successful()
        self._logger.info(
            "Setting delivery confirmation on RabbitMQ channel")
        self._rabbitmq.confirm_delivery()

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self._publishing_queue.maxsize / 5)
        self._rabbitmq.basic_qos(prefetch_count=prefetch_count)

        self._declare_exchange_and_bind_queue(
            ALERT_ROUTER_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE, TOPIC,
            ALERT_ROUTER_CONFIGS_ROUTING_KEY
        )
        self._rabbitmq.basic_consume(
            queue=ALERT_ROUTER_CONFIGS_QUEUE_NAME,
            on_message_callback=self._process_configs, auto_ack=False,
            exclusive=False, consumer_tag=None)

        self._declare_exchange_and_bind_queue(
            ALERT_ROUTER_INPUT_QUEUE_NAME, ALERT_EXCHANGE, TOPIC,
            ALERT_ROUTER_INPUT_ROUTING_KEY
        )
        self._rabbitmq.basic_consume(
            queue=ALERT_ROUTER_INPUT_QUEUE_NAME,
            on_message_callback=self._process_alert, auto_ack=False,
            exclusive=False, consumer_tag=None
        )

        # Declare store exchange just in case it hasn't been declared
        # yet
        self._rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                        exchange_type=TOPIC, passive=False,
                                        durable=True, auto_delete=False,
                                        internal=False)

        self._declare_exchange_and_bind_queue(
            ALERT_ROUTER_HEARTBEAT_QUEUE_NAME, HEALTH_CHECK_EXCHANGE, TOPIC,
            PING_ROUTING_KEY
        )

        self._logger.debug("Declaring consuming intentions")
        self._rabbitmq.basic_consume(ALERT_ROUTER_HEARTBEAT_QUEUE_NAME,
                                     self._process_ping, True, False, None)

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
        self._rabbitmq.exchange_declare(
            exchange_name, exchange_type, False, True, False, False
        )
        self._logger.info("Creating and binding queue for %s exchange",
                          exchange_name)
        self._logger.debug("Creating queue %s", queue_name)
        self._rabbitmq.queue_declare(queue_name, False, True, False, False)
        self._logger.debug("Binding queue %s to %s exchange", queue_name,
                           exchange_name)
        self._rabbitmq.queue_bind(queue_name, exchange_name, routing_key)

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

        previous_config = self._config.get(config_filename, None)
        self._config[config_filename] = {}

        # Only take from the config if it is not empty
        if recv_config:
            # Taking what we need, and checking types
            try:
                for key in recv_config.sections():
                    self._config[config_filename][key] = self.extract_config(
                        recv_config[key], config_filename
                    )
            except (NoOptionError, NoSectionError,
                    MissingKeyInConfigException) as missing_error:
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

        self._rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_alert(self, ch: BlockingChannel,
                       method: pika.spec.Basic.Deliver,
                       properties: pika.spec.BasicProperties,
                       body: bytes) -> None:
        recv_alert: Dict = {}
        has_error: bool = False
        send_to_ids: List[str] = []
        try:
            # Placed in try-except in case of malformed JSON
            recv_alert = json.loads(body)

            if recv_alert and 'severity' in recv_alert:
                self._logger.debug("Received an alert to route")
                self._logger.debug("recv_alert = %s", recv_alert)
                # Where to route this alert to

                self._logger.debug("Checking if alert is muted")
                is_all_muted = self.is_all_muted(recv_alert.get('severity'))
                is_chain_severity_muted = self.is_chain_severity_muted(
                    recv_alert.get('parent_id'), recv_alert.get('severity'))

                if is_all_muted or is_chain_severity_muted:
                    self._logger.info("This alert has been muted")
                    self._logger.info(
                        "is_all_muted=%s, is_chain_severity_muted=%s",
                        is_all_muted, is_chain_severity_muted)
                else:
                    self._logger.info("Obtaining list of channels to alert")
                    self._logger.info([
                        channel.get('id') for channel_type in
                        self._config.values() for channel in
                        channel_type.values()
                    ])
                    send_to_ids = [
                        channel.get('id') for channel_type in
                        self._config.values()
                        for channel in channel_type.values()
                        if channel.get(recv_alert.get('severity').lower()) and
                           recv_alert.get('parent_id') in channel.get(
                            'parent_ids')
                    ]

                    self._logger.debug("send_to_ids = %s", send_to_ids)
        except JSONDecodeError as json_e:
            self._logger.error("Alert was not a valid JSON object")
            self._logger.exception(json_e)
            has_error = True
        except Exception as e:
            self._logger.error("Error when processing alert: %s", recv_alert)
            self._logger.exception(e)
            has_error = True

        self._rabbitmq.basic_ack(method.delivery_tag, False)

        if not has_error:
            # This will be empty if the alert was muted
            for channel_id in send_to_ids:
                send_alert: Dict = {**recv_alert,
                                    'destination_id': channel_id}

                self._logger.debug("Queuing %s to be sent to %s",
                                   send_alert, channel_id)

                self._push_to_queue(
                    send_alert, ALERT_EXCHANGE,
                    CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE.format(
                        channel_id), mandatory=False)
                self._logger.debug(_ROUTED_ALERT_QUEUED_LOG_MESSAGE)

            # Enqueue once to the console
            if self._enable_console_alerts:
                self._logger.debug("Queuing %s to be sent to console",
                                   recv_alert)
                self._push_to_queue(
                    {**recv_alert, 'destination_id': "console"}, ALERT_EXCHANGE,
                    CONSOLE_HANDLER_INPUT_ROUTING_KEY, mandatory=True)
                self._logger.debug(_ROUTED_ALERT_QUEUED_LOG_MESSAGE)

            if self._enable_log_alerts:
                self._logger.debug("Queuing %s to be sent to the alerts log",
                                   recv_alert)

                self._push_to_queue(
                    {**recv_alert, 'destination_id': "log"}, ALERT_EXCHANGE,
                    LOG_HANDLER_INPUT_ROUTING_KEY, mandatory=True)
                self._logger.debug(_ROUTED_ALERT_QUEUED_LOG_MESSAGE)

            # Enqueue once to the data store
            self._push_to_queue(recv_alert, STORE_EXCHANGE,
                                ALERT_STORE_INPUT_ROUTING_KEY, mandatory=True)

            self._logger.debug("Alert routed successfully")

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as message is residing in the
            # publisher queue.
            self._logger.exception(e)

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self._rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self._logger.debug("Sent heartbeat to %s exchange",
                           HEALTH_CHECK_EXCHANGE)

    def _process_ping(self, ch: BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:

        self._logger.debug("Received %s. Let's pong", body)
        try:
            heartbeat = {
                'component_name': self.name,
                'is_alive': True,
                'timestamp': datetime.now().timestamp(),
            }

            self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as the heartbeats must be
            # real-time
            self._logger.error("Problem sending heartbeat")
            self._logger.exception(e)

    def start(self) -> None:
        log_and_print("{} started.".format(self), self._logger)
        self._initialise_rabbitmq()
        while True:
            try:
                # Before listening for new data send the data waiting to be sent
                # in the publishing queue. If the message is not routed, start
                # consuming and perform sending later.
                try:
                    self._send_data()
                except MessageWasNotDeliveredException as e:
                    self._logger.exception(e)

                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self._logger.exception(e)
                raise e

    def _listen_for_data(self) -> None:
        self._logger.info("Starting the alert router listeners")
        self._rabbitmq.start_consuming()

    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self._logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self._logger)
        sys.exit()

    def is_all_muted(self, severity: str) -> bool:
        self._logger.debug("Getting mute_all key")
        alerter_mute_key = Keys.get_alerter_mute()

        self._logger.debug("Getting severities mute status")
        severities_muted = json.loads(
            self._redis.get(alerter_mute_key, default=b"{}")
        )
        return bool(severities_muted.get(severity, False))

    def is_chain_severity_muted(self, parent_id: str, severity: str) -> bool:
        # INTERNAL Severities cannot be muted
        if severity == Severity.INTERNAL.value:
            return False

        self._logger.debug("Getting chain mute key")
        mute_alerts_key = Keys.get_chain_mute_alerts()

        self._logger.debug("Getting chain hashes")
        chain_hash = Keys.get_hash_parent(parent_id)

        self._logger.debug("Getting severities mute status")
        severities_muted = json.loads(
            self._redis.hget(chain_hash, mute_alerts_key, default=b"{}")
        )

        return bool(severities_muted.get(severity, False))

    @staticmethod
    def extract_config(section: SectionProxy, config_filename: str) -> Dict[
        str, str]:
        AlertRouter.validate_config_fields_existence(section, config_filename)

        if "twilio" in config_filename:
            return {
                'id': section.get('id'),
                'parent_ids': [x for x in section.get('parent_ids').split(",")
                               if x.strip()],
                'info': False,
                'warning': False,
                'error': False,
                'critical': True,
            }

        return {
            'id': section.get('id'),
            'parent_ids': [x for x in section.get('parent_ids').split(",") if
                           x.strip()],
            'info': section.getboolean('info'),
            'warning': section.getboolean('warning'),
            'error': section.getboolean('error'),
            'critical': section.getboolean('critical'),
        }

    @staticmethod
    def validate_config_fields_existence(section: SectionProxy,
                                         config_filename: str) -> None:
        keys_expected = {'id', 'parent_ids'}
        if 'twilio' not in config_filename:
            keys_expected |= {'info', 'warning', 'error', 'critical'}
        for key in keys_expected:
            if key not in section:
                raise MissingKeyInConfigException(key, config_filename)
