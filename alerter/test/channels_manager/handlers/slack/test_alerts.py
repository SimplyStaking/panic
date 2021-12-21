import copy
import json
import logging
import unittest
from datetime import timedelta, datetime
from queue import Queue
from unittest import mock
from unittest.mock import call

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.slack_bot_api import SlackBotApi
from src.channels_manager.channels import SlackChannel
from src.channels_manager.handlers import SlackAlertsHandler
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE)
from src.utils.data import RequestStatus
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit)


class TestSlackAlertsHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.test_handler_name = 'test_slack_alerts_handler'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.test_channel_name = 'test_slack_channel'
        self.test_channel_id = 'test_slack_id12345'
        self.test_channel_logger = self.dummy_logger.getChild('dummy_channel')
        self.test_bot_token = 'xoxb-XXXXXXXXXXXX-TTTTTTTTTTTTTT'
        self.test_app_token = 'xapp-Y-XXXXXXXXXXXX-TTTTTTTTTTTTT-LLLLLLLLLLLLL'
        self.test_bot_channel_id = 'test_bot_channel_id'
        self.test_api = SlackBotApi(self.test_bot_token, self.test_app_token,
                                    self.test_bot_channel_id)
        self.test_channel = SlackChannel(
            self.test_channel_name, self.test_channel_id,
            self.test_channel_logger, self.test_api)
        self.test_queue_size = 1000
        self.test_max_attempts = 5
        self.test_alert_validity_threshold = 300
        self.test_slack_alerts_handler = SlackAlertsHandler(
            self.test_handler_name, self.dummy_logger, self.rabbitmq,
            self.test_channel, self.test_queue_size,
            self.test_max_attempts, self.test_alert_validity_threshold)
        self.test_data_str = "this is a test string"
        self.test_rabbit_queue_name = 'Test Queue'
        self.test_timestamp = 45676565.556
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': self.test_timestamp,
        }
        self.test_system_name = 'test_system'
        self.test_percentage_usage = 50
        self.test_panic_severity = 'WARNING'
        self.test_parent_id = 'parent_1234'
        self.test_system_id = 'system_id32423'
        self.test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, self.test_timestamp,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        self.test_alerts_queue = Queue(self.test_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_slack_alerts_handler.rabbitmq)
        delete_queue_if_exists(self.test_slack_alerts_handler.rabbitmq,
                               self.test_rabbit_queue_name)
        delete_queue_if_exists(
            self.test_slack_alerts_handler.rabbitmq,
            self.test_slack_alerts_handler._slack_alerts_handler_queue)
        delete_exchange_if_exists(self.test_slack_alerts_handler.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_slack_alerts_handler.rabbitmq,
                                  ALERT_EXCHANGE)
        disconnect_from_rabbit(self.test_slack_alerts_handler.rabbitmq)

        self.dummy_logger = None
        self.test_channel_logger = None
        self.rabbitmq = None
        self.test_alert = None
        self.test_channel = None
        self.test_api = None
        self.test_slack_alerts_handler = None
        self.test_alerts_queue = None

    def test__str__returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         str(self.test_slack_alerts_handler))

    def test_handler_name_returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         self.test_slack_alerts_handler.handler_name)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_slack_alerts_handler._listen_for_data()
        mock_start_consuming.assert_called_once_with()

    def test_slack_channel_returns_associated_slack_channel(
            self) -> None:
        self.assertEqual(self.test_channel,
                         self.test_slack_alerts_handler.slack_channel)

    def test_alerts_queue_returns_the_alerts_queue(self) -> None:
        self.test_slack_alerts_handler._alerts_queue = self.test_alerts_queue
        self.assertEqual(self.test_alerts_queue,
                         self.test_slack_alerts_handler.alerts_queue)

    def test_init_initialises_handler_correctly(self) -> None:
        # In this test we will check that all fields that do not have a getter
        # were initialised correctly, as the previous tests test the getters.
        self.assertEqual(
            self.test_queue_size,
            self.test_slack_alerts_handler.alerts_queue.maxsize)
        self.assertEqual(self.test_max_attempts,
                         self.test_slack_alerts_handler._max_attempts)
        self.assertEqual(
            self.test_alert_validity_threshold,
            self.test_slack_alerts_handler._alert_validity_threshold)
        self.assertEqual(CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE.format(
            self.test_channel_id),
            self.test_slack_alerts_handler._slack_alerts_handler_queue)
        self.assertEqual(CHANNEL_HANDLER_INPUT_ROUTING_KEY_TEMPLATE.format(
            self.test_channel_id),
            self.test_slack_alerts_handler._slack_channel_routing_key)

    @mock.patch.object(RabbitMQApi, "basic_qos")
    def test_initialise_rabbitmq_initialises_rabbit_correctly(
            self, mock_basic_qos) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges and queues have not already been
            # declared
            connect_to_rabbit(self.rabbitmq)
            self.test_slack_alerts_handler.rabbitmq.queue_delete(
                self.test_slack_alerts_handler
                    ._slack_alerts_handler_queue)
            self.test_slack_alerts_handler.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            self.test_slack_alerts_handler.rabbitmq.exchange_delete(
                ALERT_EXCHANGE)
            disconnect_from_rabbit(self.rabbitmq)

            self.test_slack_alerts_handler._initialise_rabbitmq()

            # Perform checks that the connection has been opened and marked as
            # open, that the delivery confirmation variable is set and basic_qos
            # called successfully.
            self.assertTrue(
                self.test_slack_alerts_handler.rabbitmq.is_connected)
            self.assertTrue(
                self.test_slack_alerts_handler.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_slack_alerts_handler.rabbitmq.channel
                    ._delivery_confirmation)
            mock_basic_qos.assert_called_once_with(
                prefetch_count=self.test_queue_size / 5)

            # Check whether the producing exchanges have been created by
            # using passive=True. If this check fails an exception is raised
            # automatically.
            self.test_slack_alerts_handler.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, passive=True)

            # Check whether the consuming exchanges and queues have been
            # creating by sending messages with the same routing keys as for the
            # bindings. We will also check if the size of the queues is 0 to
            # confirm that basic_consume was called (it will store the msg in
            # the component memory immediately). If one of the exchanges or
            # queues is not created or basic_consume is not called, then either
            # an exception will be thrown or the queue size would be 1
            # respectively. Note when deleting the exchanges in the beginning we
            # also released every binding, hence there are no other queue binded
            # with the same routing key to any exchange at this point.
            self.test_slack_alerts_handler.rabbitmq.basic_publish_confirm(
                exchange=ALERT_EXCHANGE,
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_slack_alerts_handler.rabbitmq.queue_declare(
                self.test_slack_alerts_handler
                    ._slack_alerts_handler_queue, False, True, False, False)
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones set by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_slack_alerts_handler.rabbitmq.queue_delete(
                self.test_rabbit_queue_name)

            res = self.test_slack_alerts_handler.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_slack_alerts_handler.rabbitmq.queue_bind(
                queue=self.test_rabbit_queue_name,
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

            self.test_slack_alerts_handler._send_heartbeat(
                self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_slack_alerts_handler.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_slack_alerts_handler.rabbitmq.basic_get(
                self.test_rabbit_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_places_data_on_queue_if_no_processing_errors(
            self, mock_basic_ack, mock_place_alert, mock_send_alerts,
            mock_empty) -> None:
        # Setting it to non empty so that there is no attempt to send the
        # heartbeat
        mock_empty.return_value = False
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            args, _ = mock_place_alert.call_args
            self.assertEqual(self.test_alert.alert_data, args[0].alert_data)
            self.assertEqual(1, len(args))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_place_data_on_queue_if_processing_errors(
            self, mock_basic_ack, mock_place_alert, mock_send_alerts,
            mock_empty) -> None:
        # Setting it to non empty so that there is no attempt to send the
        # heartbeat
        mock_empty.return_value = False
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            data_to_send = copy.deepcopy(self.test_alert.alert_data)
            del data_to_send['message']
            body = json.dumps(data_to_send)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            mock_place_alert.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_sends_data_waiting_in_queue_if_processing_errors(
            self, mock_basic_ack, mock_place_alert, mock_send_alerts,
            mock_empty) -> None:
        # Setting it to non empty so that there is no attempt to send the
        # heartbeat
        mock_empty.return_value = False
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            data_to_send = copy.deepcopy(self.test_alert.alert_data)
            del data_to_send['message']
            body = json.dumps(data_to_send)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            mock_send_alerts.assert_called_once_with()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_sends_data_waiting_in_queue_if_no_processing_errors(
            self, mock_basic_ack, mock_place_alert, mock_send_alerts,
            mock_empty) -> None:
        # Setting it to non empty so that there is no attempt to send the
        # heartbeat
        mock_empty.return_value = False
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            mock_send_alerts.assert_called_once_with()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
        (PANICException, PANICException('test', 4000)),
    ])
    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_raises_exception_if_sending_data_from_queue_error(
            self, error_class, error_instance, mock_basic_ack, mock_place_alert,
            mock_send_alerts, mock_empty) -> None:
        # Setting it to non empty so that there is no attempt to send the
        # heartbeat
        mock_empty.return_value = False
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.side_effect = error_instance
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            self.assertRaises(error_class,
                              self.test_slack_alerts_handler._process_alert,
                              blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_heartbeat")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_sends_hb_if_data_sent_and_no_processing_errors(
            self, mock_basic_ack, mock_place_alert, mock_send_alerts,
            mock_send_heartbeat, mock_empty) -> None:
        # Setting it to non empty so that there is no attempt to send the
        # heartbeat
        mock_empty.return_value = True
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.return_value = None
        mock_send_heartbeat.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            expected_heartbeat = {
                'component_name': self.test_handler_name,
                'is_alive': True,
                'timestamp': datetime.now().timestamp()
            }
            mock_send_heartbeat.assert_called_once_with(expected_heartbeat)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_heartbeat")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_send_hb_if_not_all_data_sent_from_queue(
            self, mock_basic_ack, mock_place_alert, mock_send_alerts,
            mock_send_heartbeat, mock_empty) -> None:
        mock_empty.return_value = False
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.return_value = None
        mock_send_heartbeat.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # First test with a valid alert
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            # Test with an invalid alert dict
            invalid_alert = copy.deepcopy(self.test_alert.alert_data)
            del invalid_alert['message']
            body = json.dumps(invalid_alert)
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        args, _ = mock_basic_ack.call_args
        self.assertEqual(2, len(args))

    @parameterized.expand([(True,), (False,), ])
    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_heartbeat")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_send_hb_if_processing_error(
            self, is_queue_empty, mock_basic_ack, mock_place_alert,
            mock_send_alerts, mock_send_heartbeat, mock_empty) -> None:
        mock_empty.return_value = is_queue_empty
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.return_value = None
        mock_send_heartbeat.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            invalid_alert = copy.deepcopy(self.test_alert.alert_data)
            del invalid_alert['message']
            body = json.dumps(invalid_alert)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)

            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @parameterized.expand([
        (True, AMQPConnectionError, AMQPConnectionError('test'),),
        (True, AMQPChannelError, AMQPChannelError('test'),),
        (True, Exception, Exception('test'),),
        (True, PANICException, PANICException('test', 4000)),
        (False, AMQPConnectionError, AMQPConnectionError('test'),),
        (False, AMQPChannelError, AMQPChannelError('test'),),
        (False, Exception, Exception('test'),),
        (False, PANICException, PANICException('test', 4000)),
    ])
    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_heartbeat")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_send_hb_if_error_raised_when_sending_data(
            self, is_queue_empty, error_class, error_instance, mock_basic_ack,
            mock_place_alert, mock_send_alerts, mock_send_heartbeat,
            mock_empty) -> None:
        mock_empty.return_value = is_queue_empty
        mock_place_alert.return_value = None
        mock_basic_ack.return_value = None
        mock_send_alerts.side_effect = error_instance
        mock_send_heartbeat.return_value = None
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # Send with a valid alert
            self.assertRaises(error_class,
                              self.test_slack_alerts_handler._process_alert,
                              blocking_channel, method, properties, body)

            # Test with an invalid alert
            invalid_alert = copy.deepcopy(self.test_alert.alert_data)
            del invalid_alert['message']
            body = json.dumps(invalid_alert)
            self.assertRaises(error_class,
                              self.test_slack_alerts_handler._process_alert,
                              blocking_channel, method, properties, body)

            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        args, _ = mock_basic_ack.call_args
        self.assertEqual(2, len(args))

    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_heartbeat")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_raise_msg_not_delivered_exception(
            self, mock_basic_ack, mock_place_alert, mock_send_alerts,
            mock_send_heartbeat, mock_empty) -> None:
        mock_basic_ack.return_value = None
        mock_place_alert.return_value = None
        mock_send_alerts.return_value = None
        mock_empty.return_value = True
        mock_send_heartbeat.side_effect = MessageWasNotDeliveredException(
            'test')
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # This would raise a MessageWasNotDeliveredException if raised,
            # hence the test would fail
            self.test_slack_alerts_handler._process_alert(blocking_channel,
                                                          method, properties,
                                                          body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(Queue, "empty")
    @mock.patch.object(SlackAlertsHandler, "_send_heartbeat")
    @mock.patch.object(SlackAlertsHandler, "_send_alerts")
    @mock.patch.object(SlackAlertsHandler, "_place_alert_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_raises_error_if_raised_by_send_hb(
            self, exception_class, exception_instance, mock_basic_ack,
            mock_place_alert, mock_send_alerts, mock_send_heartbeat,
            mock_empty) -> None:
        # For this test we will check for channel, connection and unexpected
        # errors.
        mock_basic_ack.return_value = None
        mock_place_alert.return_value = None
        mock_send_alerts.return_value = None
        mock_send_heartbeat.side_effect = exception_instance
        mock_empty.return_value = True
        try:
            self.test_slack_alerts_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_slack_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=self.test_slack_alerts_handler
                    ._slack_channel_routing_key)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            self.assertRaises(exception_class,
                              self.test_slack_alerts_handler._process_alert,
                              blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    def test_place_alert_on_queue_places_alert_on_queue_if_queue_not_full(
            self) -> None:
        # Use a smaller queue in this case for simplicity
        test_queue = Queue(3)
        self.test_slack_alerts_handler._alerts_queue = test_queue
        test_queue.put('item1')
        test_queue.put('item2')

        self.test_slack_alerts_handler._place_alert_on_queue(
            self.test_alert)

        all_queue_items = list(test_queue.queue)
        self.assertEqual(['item1', 'item2', self.test_alert], all_queue_items)

    def test_place_alert_on_queue_removes_oldest_and_places_if_queue_full(
            self) -> None:
        # Use a smaller queue in this case for simplicity
        test_queue = Queue(3)
        self.test_slack_alerts_handler._alerts_queue = test_queue
        test_queue.put('item1')
        test_queue.put('item2')
        test_queue.put('item3')

        self.test_slack_alerts_handler._place_alert_on_queue(
            self.test_alert)

        all_queue_items = list(test_queue.queue)
        self.assertEqual(['item2', 'item3', self.test_alert], all_queue_items)

    @mock.patch.object(Queue, "empty")
    @mock.patch.object(Queue, "get")
    @mock.patch.object(logging, "debug")
    @mock.patch.object(logging, "info")
    @mock.patch.object(logging, "warning")
    @mock.patch.object(logging, "critical")
    @mock.patch.object(logging, "error")
    @mock.patch.object(logging, "exception")
    def test_send_alerts_does_nothing_if_queue_is_empty(
            self, mock_exception, mock_error, mock_critical, mock_warning,
            mock_info, mock_debug, mock_get, mock_empty) -> None:
        mock_empty.return_value = True

        self.test_slack_alerts_handler._send_alerts()

        mock_critical.assert_not_called()
        mock_info.assert_not_called()
        mock_warning.assert_not_called()
        mock_debug.assert_not_called()
        mock_get.assert_not_called()
        mock_exception.assert_not_called()
        mock_error.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch.object(SlackChannel, "alert")
    def test_send_alerts_discards_old_alerts_and_sends_the_recent(
            self, mock_alert) -> None:
        mock_alert.return_value = RequestStatus.SUCCESS
        test_alert_old1 = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity,
            datetime.now().timestamp() - self.test_alert_validity_threshold - 1,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_alert_recent1 = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity,
            datetime.now().timestamp() - self.test_alert_validity_threshold,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_alert_recent2 = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, datetime.now().timestamp(),
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_alert_recent3 = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity,
            datetime.now().timestamp() - self.test_alert_validity_threshold + 4,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_queue = Queue(4)
        self.test_slack_alerts_handler._alerts_queue = test_queue
        test_queue.put(test_alert_old1)
        test_queue.put(test_alert_recent1)
        test_queue.put(test_alert_recent2)
        test_queue.put(test_alert_recent3)

        self.test_slack_alerts_handler._send_alerts()

        self.assertTrue(self.test_slack_alerts_handler.alerts_queue.empty())
        expected_calls = [call(test_alert_recent1), call(test_alert_recent2),
                          call(test_alert_recent3)]
        actual_calls = mock_alert.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @parameterized.expand([
        ([RequestStatus.SUCCESS], 1,),
        ([RequestStatus.FAILED, RequestStatus.SUCCESS], 2,),
        ([RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.SUCCESS],
         3,),
        ([RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.FAILED,
          RequestStatus.SUCCESS], 4,),
        ([RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.FAILED,
          RequestStatus.FAILED, RequestStatus.SUCCESS], 5,),
        ([RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.FAILED,
          RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.SUCCESS],
         5,),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, "connection")
    @mock.patch.object(SlackChannel, "alert")
    def test_send_alerts_attempts_to_send_alert_for_up_to_max_attempts_times(
            self, alert_request_status_list, expected_no_calls, mock_alert,
            mock_connection) -> None:
        mock_alert.side_effect = alert_request_status_list
        mock_connection.return_value.sleep.return_value = None
        test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, datetime.now().timestamp(),
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_queue = Queue(4)
        self.test_slack_alerts_handler._alerts_queue = test_queue
        test_queue.put(test_alert)

        self.test_slack_alerts_handler._send_alerts()

        expected_calls = []
        for _ in range(expected_no_calls):
            expected_calls.append(call(test_alert))
        actual_calls = mock_alert.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @parameterized.expand([
        ([RequestStatus.SUCCESS],),
        ([RequestStatus.FAILED, RequestStatus.SUCCESS],),
        ([RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.SUCCESS],),
        ([RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.FAILED,
          RequestStatus.SUCCESS],),
        ([RequestStatus.FAILED, RequestStatus.FAILED, RequestStatus.FAILED,
          RequestStatus.FAILED, RequestStatus.SUCCESS],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, "connection")
    @mock.patch.object(SlackChannel, "alert")
    def test_send_alerts_removes_alert_if_it_was_successfully_sent(
            self, alert_request_status_list, mock_alert,
            mock_connection) -> None:
        mock_alert.side_effect = alert_request_status_list
        mock_connection.return_value.sleep.return_value = None
        test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, datetime.now().timestamp(),
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_queue = Queue(4)
        self.test_slack_alerts_handler._alerts_queue = test_queue
        test_queue.put(test_alert)

        self.test_slack_alerts_handler._send_alerts()

        self.assertTrue(self.test_slack_alerts_handler.alerts_queue.empty())

    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, "connection")
    @mock.patch.object(SlackChannel, "alert")
    def test_send_alerts_stops_sending_if_an_alert_is_not_successfully_sent(
            self, mock_alert, mock_connection) -> None:
        mock_alert.return_value = RequestStatus.FAILED
        mock_connection.return_value.sleep.return_value = None
        test_alert_1 = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, datetime.now().timestamp(),
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_alert_2 = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, datetime.now().timestamp() + 1,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )
        test_queue = Queue(4)
        self.test_slack_alerts_handler._alerts_queue = test_queue
        test_queue.put(test_alert_1)
        test_queue.put(test_alert_2)

        self.test_slack_alerts_handler._send_alerts()

        self.assertFalse(
            self.test_slack_alerts_handler.alerts_queue.empty())
        self.assertEqual(
            2, self.test_slack_alerts_handler.alerts_queue.qsize())
        self.assertEqual(
            test_alert_1,
            self.test_slack_alerts_handler.alerts_queue.queue[0])
        self.assertEqual(
            test_alert_2,
            self.test_slack_alerts_handler.alerts_queue.queue[1])
