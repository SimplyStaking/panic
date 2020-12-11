import json
import logging
import signal
import sys
from datetime import datetime
from types import FrameType

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alert_code import AlertCode
from src.alerter.alerts.alert import Alert
from src.channels_manager.channels.console import ConsoleChannel
from src.channels_manager.handlers.handler import ChannelHandler
from src.utils.constants import ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE
from src.utils.data import RequestStatus
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class ConsoleAlertsHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 console_channel: ConsoleChannel) -> None:
        super().__init__(handler_name, logger)
        self._console_channel = console_channel

        # Handle termination signals by stopping the handler gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    @property
    def console_channel(self) -> ConsoleChannel:
        return self._console_channel

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '{}' exchange".format(ALERT_EXCHANGE))
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info(
            "Creating queue 'console_{}_alerts_handler_queue'".format(
                self.console_channel.channel_id))
        self.rabbitmq.queue_declare('console_{}_alerts_handler_queue'.format(
            self.console_channel.channel_id), False, True, False, False)
        self.logger.info(
            "Binding queue 'console_{}_alerts_handler_queue' to "
            "exchange '{}' with routing key 'channel.console'".format(
                self.console_channel.channel_id, ALERT_EXCHANGE))
        self.rabbitmq.queue_bind('console_{}_alerts_handler_queue'.format(
            self.console_channel.channel_id), ALERT_EXCHANGE, 'channel.console')

        prefetch_count = 200
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.info("Declaring consuming intentions")
        self.rabbitmq.basic_consume('console_{}_alerts_handler_queue'.format(
            self.console_channel.channel_id), self._process_alerts, False,
            False, None)

        # Set producing configuration for heartbeat publishing
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '{}' exchange".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.worker',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.info("Sent heartbeat to '{}' exchange".format(
            HEALTH_CHECK_EXCHANGE))

    def _process_alerts(self, ch: BlockingChannel,
                        method: pika.spec.Basic.Deliver,
                        properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        alert_json = json.loads(body)
        self.logger.info("Received {}. Now processing this alert.".format(
            alert_json))

        processing_error = False
        alert = None
        try:
            alert_code = alert_json['alert_code']
            alert_code_enum = AlertCode.get_enum_by_value(alert_code['code'])
            alert = Alert(alert_code_enum, alert_json['message'],
                          alert_json['severity'], alert_json['timestamp'],
                          alert_json['parent_id'], alert_json['origin_id'])

            self.logger.info("Successfully processed {}".format(alert_json))
        except Exception as e:
            self.logger.error("Error when processing {}".format(alert_json))
            self.logger.exception(e)
            processing_error = True

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        alert_result = RequestStatus.FAILED
        try:
            if not processing_error:
                alert_result = self.console_channel.alert(alert)
        except Exception as e:
            raise e

        if alert_result == RequestStatus.SUCCESS and not processing_error:
            try:
                heartbeat = {
                    'component_name': self.handler_name,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
            except MessageWasNotDeliveredException as e:
                # Log the message and do not raise it as heartbeats must be
                # real-time.
                self.logger.exception(e)
            except Exception as e:
                raise e

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def start(self) -> None:
        self._initialize_rabbitmq()
        while True:
            try:
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
                      "closed, and afterwards the process will "
                      "exit.".format(self), self.logger)
        self.rabbitmq.disconnect_till_successful()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
