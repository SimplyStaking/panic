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
from src.channels_manager.channels.opsgenie import OpsgenieChannel
from src.channels_manager.handlers import ChannelHandler
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import ALERT_EXCHANGE
from src.utils.data import RequestStatus
from src.utils.exceptions import ConnectionNotInitializedException
from src.utils.logging import log_and_print


class OpsgenieAlertHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 rabbit_ip: str, queue_size: int,
                 opsgenie_channel: OpsgenieChannel, max_attempts: int = 6,
                 alert_validity_threshold: int = 600):
        self._alerts_queue = Queue(queue_size)
        self._rabbit = RabbitMQApi(logger=logger.getChild(RabbitMQApi.__name__),
                                   host=rabbit_ip)
        self._opsgenie_channel = opsgenie_channel
        self._max_attempts = max_attempts
        self._alert_validity_threshold = alert_validity_threshold
        self._opsgenie_channel_queue_name = \
            "opsgenie_{}_alerts_handler_queue".format(
                self._opsgenie_channel.channel_id)

        super().__init__(handler_name, logger)

    def _process_alert(self, ch: BlockingChannel,
                       method: pika.spec.Basic.Deliver,
                       properties: pika.spec.BasicProperties,
                       body: bytes) -> None:
        alert_json = json.loads(body)
        self.logger.info("Received and processing alert: %s", alert_json)
        processing_error = False
        try:
            # We check that everything is in the alert dict
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
        self._rabbit.basic_ack(method.delivery_tag, False)

        # Place the data on the alerts queue if there were no processing errors.
        # This is done after acknowledging the data, so that if acknowledgement
        # fails, the data is processed again and we do not have duplication of
        # data in the queue
        if not processing_error:
            self._place_data_on_queue(alert)

        # Send any data waiting in the queue, if any
        self._send_data()

    def _place_data_on_queue(self, alert: Alert) -> None:
        self.logger.debug("Adding %s to the alerts queue ...",
                          alert.alert_code.name)

        # Place the alert on the alerts queue. If the queue is full, remove old
        # data first.
        if self._alerts_queue.full():
            self._alerts_queue.get()
        self._alerts_queue.put(alert)

        self.logger.debug("%s added to the alerts queue",
                          alert.alert_code.name)

    def _send_data(self) -> None:
        empty = True
        if not self._alerts_queue.empty():
            empty = False
            self.logger.info("Attempting to send all alerts waiting in the "
                             "alerts queue ...")

        # Try sending the alerts in the alerts queue one by one. If sending
        # fails, try re-sending three times in a space of 1 minute. If this
        # still fails, stop sending alerts until the next alert is received. If
        # 10 minutes pass since the alert was first raised, the alert is
        # discarded. Important, remove an item from the queue only if the
        # sending was successful, so that if an exception is raised, that
        # message is not popped
        while not self._alerts_queue.empty():
            alert = self._alerts_queue.queue[0]

            # Discard alert if 10 minutes passed since it was last raised
            if (datetime.now().timestamp() - alert.timestamp) \
                    > self._alert_validity_threshold:
                self._alerts_queue.get()
                self._alerts_queue.task_done()
                continue

            attempts = 0
            status = self._opsgenie_channel.alert(alert)
            while status != RequestStatus.SUCCESS \
                    and attempts <= self._max_attempts:
                self.logger.info(
                    "Will re-trying sending in 10 seconds. "
                    "Attempts left: %s", self._max_attempts - attempts)
                self._rabbit.connection.sleep(10)
                status = self._opsgenie_channel.alert(alert)
                attempts += 1

            if status == RequestStatus.SUCCESS:
                self._alerts_queue.get()
                self._alerts_queue.task_done()
            else:
                self.logger.info("Stopped sending alerts.")
                return

        if not empty:
            self.logger.info("Successfully sent all data from the publishing "
                             "queue")

    def _initialise_rabbitmq(self) -> None:
        opsgenie_routing_key = "channel.{}".format(
            self._opsgenie_channel.channel_id)

        self._rabbit.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating %s exchange", ALERT_EXCHANGE)
        self._rabbit.exchange_declare(ALERT_EXCHANGE, 'topic', False, True,
                                      False, False)
        self.logger.info(
            "Creating queue '%s'", self._opsgenie_channel_queue_name)
        self._rabbit.queue_declare(self._opsgenie_channel_queue_name, False,
                                   True, False, False)

        self.logger.info(
            "Binding queue '%s' to exchange '%s' with routing key 'channel.%s'",
            self._opsgenie_channel_queue_name, ALERT_EXCHANGE,
            opsgenie_routing_key
        )
        self._rabbit.queue_bind(self._opsgenie_channel_queue_name,
                                ALERT_EXCHANGE, opsgenie_routing_key)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self._alerts_queue.maxsize / 5)
        self._rabbit.basic_qos(prefetch_count=prefetch_count)
        self.logger.info("Declaring consuming intentions")
        self._rabbit.basic_consume(self._opsgenie_channel_queue_name,
                                   self._process_alert, False, False, None)

    def _listen_for_data(self) -> None:
        self._rabbit.start_consuming()

    def disconnect(self):
        self._rabbit.disconnect_till_successful()

    def start(self) -> None:
        self._initialise_rabbitmq()
        while True:
            try:
                # Before listening for new alerts, send the data waiting to be
                # sent in the alerts queue.
                self._send_data()
                self._listen_for_data()
            except (AMQPConnectionError, AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and the '{}' queue will be deleted. Afterwards, "
                      "the process will exit."
                      .format(self, self._opsgenie_channel_queue_name),
                      self.logger)

        # Try to delete the queue before exiting to avoid cases when the alert
        # router is still sending data to this queue. This is done until
        # successful
        while True:
            try:
                self._rabbit.perform_operation_till_successful(
                    self._rabbit.queue_delete,
                    [self._opsgenie_channel_queue_name, False, False], -1)
                break
            except ConnectionNotInitializedException:
                self._logger.info(
                    "Connection was not yet initialized, therefore no need to "
                    "delete the '%s' queue.",
                    self._opsgenie_channel_queue_name)
                break
            except pika.exceptions.AMQPChannelError as e:
                self._logger.exception(e)
                self._logger.info("Will re-try deleting the '%s' queue.",
                                  self._opsgenie_channel_queue_name)
            except pika.exceptions.AMQPConnectionError as e:
                self._logger.exception(e)
                self._logger.info(
                    "Will re-connect again and re-try deleting the '%s' queue.",
                    self._opsgenie_channel_queue_name)
                self._rabbit.connect_till_successful()
            except Exception as e:
                self._logger.exception(e)
                self._logger.info(
                    "Unexpected exception while trying to delete the '%s' "
                    "queue. Will not continue re-trying deleting the queue.",
                    self._opsgenie_channel_queue_name)
                break

        self._rabbit.disconnect_till_successful()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
