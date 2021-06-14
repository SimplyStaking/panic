import json
import logging
import sys
from datetime import datetime
from queue import Queue
from types import FrameType

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.alerter.alert_code import AlertCode
from src.alerter.alerts.alert import Alert
from src.alerter.grouped_alerts_metric_code import MetricCode
from src.channels_manager.channels import PagerDutyChannel
from src.channels_manager.handlers import ChannelHandler
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE, TOPIC)
from src.utils.data import RequestStatus
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class PagerDutyAlertsHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi, pagerduty_channel: PagerDutyChannel,
                 queue_size: int = 0, max_attempts: int = 6,
                 alert_validity_threshold: int = 600):
        super().__init__(handler_name, logger, rabbitmq)

        self._pagerduty_channel = pagerduty_channel
        self._alerts_queue = Queue(queue_size)
        self._max_attempts = max_attempts
        self._alert_validity_threshold = alert_validity_threshold
        self._pagerduty_alerts_handler_queue = \
            CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE.format(
                self._pagerduty_channel.channel_id)
        self._pagerduty_channel_routing_key = \
            CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE.format(
                self.pagerduty_channel.channel_id)

    @property
    def pagerduty_channel(self) -> PagerDutyChannel:
        return self._pagerduty_channel

    @property
    def alerts_queue(self) -> Queue:
        return self._alerts_queue

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
        self.logger.debug("Received and processing alert: %s", alert_json)

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

        # Place the alert on the alerts queue if there were no processing
        # errors. This is done after acknowledging the alert, so that if
        # acknowledgement fails, the alert is processed again and we do not have
        # duplication of alerts in the queue
        if not processing_error:
            self._place_alert_on_queue(alert)

        # Send any alerts waiting in the queue, if any
        try:
            self._send_alerts()
        except Exception as e:
            raise e

        # By this condition we are sending heartbeats only when there were no
        # processing errors and when all alerts have been sent successfully.
        if self.alerts_queue.empty() and not processing_error:
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

    def _place_alert_on_queue(self, alert: Alert) -> None:
        self.logger.debug("Adding %s to the alerts queue ...",
                          alert.alert_code.name)

        # Place the alert on the alerts queue. If the queue is full, remove old
        # alerts first.
        if self._alerts_queue.full():
            self._alerts_queue.get()
        self._alerts_queue.put(alert)

        self.logger.debug("%s added to the alerts queue", alert.alert_code.name)

    def _send_alerts(self) -> None:
        empty = True
        if not self._alerts_queue.empty():
            empty = False
            self.logger.debug("Attempting to send all alerts waiting in the "
                              "alerts queue ...")

        # Try sending the alerts in the alerts queue one by one. If sending
        # fails, try re-sending max_attempts - 1 times with 10 seconds sleep in
        # between. If this still fails, stop sending alerts until the next alert
        # is received. If alert_validity_threshold seconds pass since the alert
        # was first raised, the alert is discarded. Important, remove an item
        # from the queue only if the sending was successful, so that if an
        # exception is raised, that message is not popped.
        while not self._alerts_queue.empty():
            alert = self._alerts_queue.queue[0]

            # Discard alert if alert_validity_threshold seconds passed since it
            # was last raised
            if (datetime.now().timestamp() - alert.timestamp) \
                    > self._alert_validity_threshold:
                self._alerts_queue.get()
                self._alerts_queue.task_done()
                continue

            attempts = 1
            status = self.pagerduty_channel.alert(alert)
            while status != RequestStatus.SUCCESS \
                    and attempts < self._max_attempts:
                self.logger.debug("Will re-try sending in 10 seconds. "
                                  "Attempts left: %s",
                                  self._max_attempts - attempts)
                self.rabbitmq.connection.sleep(10)
                status = self.pagerduty_channel.alert(alert)
                attempts += 1

            if status == RequestStatus.SUCCESS:
                self._alerts_queue.get()
                self._alerts_queue.task_done()
            else:
                self.logger.debug("Stopped sending alerts.")
                return

        if not empty:
            self.logger.debug("Successfully sent all data from the publishing "
                              "queue")

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating %s exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         self._pagerduty_alerts_handler_queue)
        self.rabbitmq.queue_declare(self._pagerduty_alerts_handler_queue, False,
                                    True, False, False)

        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", self._pagerduty_alerts_handler_queue,
                         ALERT_EXCHANGE, self._pagerduty_channel_routing_key)
        self.rabbitmq.queue_bind(self._pagerduty_alerts_handler_queue,
                                 ALERT_EXCHANGE,
                                 self._pagerduty_channel_routing_key)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self._alerts_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(self._pagerduty_alerts_handler_queue,
                                    self._process_alert, False, False, None)

        # Set producing configuration for heartbeat publishing
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def start(self) -> None:
        self._initialise_rabbitmq()
        while True:
            try:
                # Before listening for new alerts, send the alerts waiting to be
                # sent in the alerts queue.
                self._send_alerts()
                self._listen_for_data()
            except (AMQPConnectionError, AMQPChannelError) as e:
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
        rabbit, the opsgenie alerts handler only sends heartbeats. Alerts are
        sent through the third party channel.
        """
        pass
