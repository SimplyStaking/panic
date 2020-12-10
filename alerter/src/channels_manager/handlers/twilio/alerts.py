import json
import logging
import signal
import sys
from datetime import datetime
from enum import Enum
from types import FrameType
from typing import List

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerts.alert import Alert
from src.channels_manager.channels.twilio import TwilioChannel
from src.channels_manager.handlers.handler import ChannelHandler
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils import env
from src.utils.constants import ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE
from src.utils.data import RequestStatus
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class TwilioAlertsHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 twilio_channel: TwilioChannel, call_from: str,
                 call_to: List[str], twiml: str, twiml_is_url: bool) -> None:
        super().__init__(handler_name, logger)
        self._twilio_channel = twilio_channel
        self._call_from = call_from
        self._call_to = call_to
        self._twiml = twiml
        self._twiml_is_url = twiml_is_url

        rabbit_ip = env.RABBIT_IP
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

        # Handle termination signals by stopping the handler gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    @property
    def twilio_channel(self) -> TwilioChannel:
        return self._twilio_channel

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '{}' exchange".format(ALERT_EXCHANGE))
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info(
            "Creating queue 'twilio_{}_alerts_handler_queue'".format(
                self.twilio_channel.channel_id))
        self.rabbitmq.queue_declare('twilio_{}_alerts_handler_queue'.format(
            self.twilio_channel.channel_id), False, True, False, False)
        self.logger.info(
            "Binding queue 'twilio_{}_alerts_handler_queue' to "
            "exchange '{}' with routing key 'channel.{}'".format(
                self.twilio_channel.channel_id, ALERT_EXCHANGE,
                self.twilio_channel.channel_id))
        self.rabbitmq.queue_bind('twilio_{}_alerts_handler_queue'.format(
            self.twilio_channel.channel_id), ALERT_EXCHANGE,
            'channel.{}'.format(self.twilio_channel.channel_id))

        prefetch_count = 200
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.info("Declaring consuming intentions")
        self.rabbitmq.basic_consume('twilio_{}_alerts_handler_queue'.format(
            self.twilio_channel.channel_id), self._process_alerts, False, False,
            None)

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
            message = alert_json['message']
            severity = alert_json['severity']
            parent_id = alert_json['parent_id']
            origin_id = alert_json['origin_id']
            timestamp = alert_json['timestamp']
            alert_code_enum = Enum('AlertCode',
                                   {alert_code['name']: alert_code['code']})
            alert = Alert(alert_code_enum, message, severity, timestamp,
                          parent_id, origin_id)

            self.logger.info("Successfully processed {}".format(alert_json))
        except Exception as e:
            self.logger.error("Error when processing {}".format(alert_json))
            self.logger.exception(e)
            processing_error = True

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        calling_successful = RequestStatus.FAILED
        try:
            # Initiate the calling procedure if the data sent was a valid alert
            if not processing_error:
                calling_successful = self._call_using_twilio(alert)
        except Exception as e:
            raise e

        if calling_successful == RequestStatus.SUCCESS and not processing_error:
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

    def _call_using_twilio(self, alert: Alert) -> RequestStatus:
        # Do not call if 5 minutes passed since the alert was last raised, as
        # alert is considered to be old
        alert_validity_threshold = 300
        if (datetime.now().timestamp() - alert.timestamp) \
                > alert_validity_threshold:
            self.logger.error('Did not call as alert was raised a while '
                              'ago')
            return RequestStatus.FAILED

        # For each number try calling 3 times in a space of 15 seconds until the
        # call is successful. If this threshold is reached, we move to the next
        # number.
        max_attempts = 3
        calling_status = RequestStatus.SUCCESS
        for number in self._call_to:
            attempts = 0
            ret = self.twilio_channel.alert(call_from=self._call_from,
                                            call_to=number, twiml=self._twiml,
                                            twiml_is_url=self._twiml_is_url)
            while ret != RequestStatus.SUCCESS and attempts <= max_attempts:
                self.logger.info(
                    "Will re-trying calling in 5 seconds. "
                    "Attempts left: {}".format(max_attempts - attempts))
                self.rabbitmq.connection.sleep(5)
                ret = self.twilio_channel.alert(call_from=self._call_from,
                                                call_to=number,
                                                twiml=self._twiml,
                                                twiml_is_url=self._twiml_is_url)
                attempts += 1

            if ret == RequestStatus.FAILED:
                calling_status = RequestStatus.FAILED

        if calling_status == RequestStatus.SUCCESS:
            self.logger.info('Successfully sent all calling requests to Twilio')
        else:
            self.logger.error('Could not succesfully send all calling '
                              'requests to Twilio')

        return calling_status

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
