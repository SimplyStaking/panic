import json
import logging
import sys
from datetime import datetime
from types import FrameType
from typing import List

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alert_code import AlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.metric_code import MetricCode
from src.channels_manager.channels.twilio import TwilioChannel
from src.channels_manager.handlers.handler import ChannelHandler
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                 CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE,
                                 CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE,
                                 TOPIC)
from src.utils.data import RequestStatus
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class TwilioAlertsHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi, twilio_channel: TwilioChannel,
                 call_from: str, call_to: List[str], twiml: str,
                 twiml_is_url: bool, max_attempts: int = 3,
                 alert_validity_threshold: int = 300) -> None:
        super().__init__(handler_name, logger, rabbitmq)

        self._twilio_channel = twilio_channel
        self._call_from = call_from
        self._call_to = call_to
        self._twiml = twiml
        self._twiml_is_url = twiml_is_url
        self._max_attempts = max_attempts
        self._alert_validity_threshold = alert_validity_threshold
        self._twilio_alerts_handler_queue = \
            CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE.format(
                self.twilio_channel.channel_id)
        self._twilio_channel_routing_key = \
            CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE.format(
                self.twilio_channel.channel_id)

    @property
    def twilio_channel(self) -> TwilioChannel:
        return self._twilio_channel

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         self._twilio_alerts_handler_queue)
        self.rabbitmq.queue_declare(self._twilio_alerts_handler_queue, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", self._twilio_alerts_handler_queue,
                         ALERT_EXCHANGE, self._twilio_channel_routing_key)
        self.rabbitmq.queue_bind(self._twilio_alerts_handler_queue,
                                 ALERT_EXCHANGE,
                                 self._twilio_channel_routing_key)

        self.rabbitmq.basic_qos(prefetch_count=200)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(self._twilio_alerts_handler_queue,
                                    self._process_alert, False, False, None)

        # Set producing configuration for heartbeat publishing
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

    def _process_alert(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        alert_json = json.loads(body)
        self.logger.debug("Received %s. Now processing this alert.", alert_json)

        processing_error = False
        alert = None
        try:
            alert_code = alert_json['alert_code']
            alert_code_enum = AlertCode.get_enum_by_value(alert_code['code'])
            metric_code_enum = MetricCode.get_enum_by_value(
                alert_json['metric'])
            alert = Alert(alert_code_enum, alert_json['message'],
                          alert_json['severity'], alert_json['timestamp'],
                          alert_json['parent_id'], alert_json['origin_id'],
                          metric_code_enum)

            self.logger.debug("Successfully processed %s", alert_json)
        except Exception as e:
            self.logger.error("Error when processing %s", alert_json)
            self.logger.exception(e)
            processing_error = True

        # If the alert is processed, it can be acknowledged.
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
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
            except MessageWasNotDeliveredException as e:
                # Log the message and do not raise it as heartbeats must be
                # real-time.
                self.logger.exception(e)
            except Exception as e:
                raise e

    def _call_using_twilio(self, alert: Alert) -> RequestStatus:
        # Do not call if alert_validity_threshold seconds passed since the alert
        # was last raised, as alert is considered to be old
        time_elapsed_since_alert_was_raised = \
            datetime.now().timestamp() - alert.timestamp
        if time_elapsed_since_alert_was_raised > self._alert_validity_threshold:
            self.logger.error("Did not call as alert was raised a while "
                              "ago")
            return RequestStatus.FAILED

        # For each number try calling max_attempts times with 5 seconds sleep in
        # between until the call is successful. If this threshold is reached,
        # we move on to the next number.
        calling_status = RequestStatus.SUCCESS
        for number in self._call_to:
            attempts = 1
            ret = self.twilio_channel.alert(call_from=self._call_from,
                                            call_to=number, twiml=self._twiml,
                                            twiml_is_url=self._twiml_is_url)
            while ret != RequestStatus.SUCCESS and \
                    attempts < self._max_attempts:
                self.logger.debug("Will re-trying calling in 5 seconds. "
                                  "Attempts left: %s",
                                  self._max_attempts - attempts)
                self.rabbitmq.connection.sleep(5)
                ret = self.twilio_channel.alert(call_from=self._call_from,
                                                call_to=number,
                                                twiml=self._twiml,
                                                twiml_is_url=self._twiml_is_url)
                attempts += 1

            if ret == RequestStatus.FAILED:
                calling_status = RequestStatus.FAILED

        if calling_status == RequestStatus.SUCCESS:
            self.logger.debug(
                "Successfully sent all calling requests to Twilio")
        else:
            self.logger.error("Could not succesfully send all calling requests "
                              "to Twilio")

        return calling_status

    def start(self) -> None:
        self._initialise_rabbitmq()
        while True:
            try:
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
                      "closed, and afterwards the process will "
                      "exit.".format(self), self.logger)
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _send_data(self, alert: Alert) -> None:
        """
        We are not implementing the _send_data function because with respect to
        rabbit, the twilio alerts handler only sends heartbeats. Alerts are sent
        through the third party channel.
        """
        pass
