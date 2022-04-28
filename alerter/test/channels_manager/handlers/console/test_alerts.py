import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPChannelError, AMQPConnectionError

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.channels.console import ConsoleChannel
from src.channels_manager.handlers.console.alerts import (
    ConsoleAlertsHandler)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, CONSOLE_HANDLER_INPUT_ROUTING_KEY)
from src.utils.data import RequestStatus
from src.utils.exceptions import MessageWasNotDeliveredException
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit)


class TestConsoleAlertsHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.test_handler_name = 'test_console_alerts_handler'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.test_channel_name = 'test_console_channel'
        self.test_channel_id = 'test_console1234'
        self.test_channel_logger = self.dummy_logger.getChild('dummy_channel')
        self.test_channel = ConsoleChannel(self.test_channel_name,
                                           self.test_channel_id,
                                           self.test_channel_logger)
        self.test_console_alerts_handler = ConsoleAlertsHandler(
            self.test_handler_name, self.dummy_logger, self.rabbitmq,
            self.test_channel)
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

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_console_alerts_handler.rabbitmq)
        delete_queue_if_exists(self.test_console_alerts_handler.rabbitmq,
                               self.test_rabbit_queue_name)
        delete_queue_if_exists(
            self.test_console_alerts_handler.rabbitmq,
            self.test_console_alerts_handler._console_alerts_handler_queue)
        delete_exchange_if_exists(self.test_console_alerts_handler.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_console_alerts_handler.rabbitmq,
                                  ALERT_EXCHANGE)
        disconnect_from_rabbit(self.test_console_alerts_handler.rabbitmq)

        self.dummy_logger = None
        self.test_channel_logger = None
        self.rabbitmq = None
        self.test_channel = None
        self.test_console_alerts_handler = None
        self.test_alert = None

    def test__str__returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         str(self.test_console_alerts_handler))

    def test_handler_name_returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         self.test_console_alerts_handler.handler_name)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_console_alerts_handler._listen_for_data()
        mock_start_consuming.assert_called_once_with()

    def test_console_channel_returns_associated_console_channel(self) -> None:
        self.assertEqual(self.test_channel,
                         self.test_console_alerts_handler.console_channel)

    def test_init_initialises_handler_correctly(self) -> None:
        # In this test we will check that all fields that do not have a getter
        # were initialised correctly, as the previous tests test the getters.
        self.assertEqual(CHAN_ALERTS_HAN_INPUT_QUEUE_NAME_TEMPLATE.format(
            self.test_channel_id),
            self.test_console_alerts_handler._console_alerts_handler_queue)

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
            self.test_console_alerts_handler.rabbitmq.queue_delete(
                self.test_console_alerts_handler._console_alerts_handler_queue)
            self.test_console_alerts_handler.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            self.test_console_alerts_handler.rabbitmq.exchange_delete(
                ALERT_EXCHANGE)
            disconnect_from_rabbit(self.rabbitmq)

            self.test_console_alerts_handler._initialise_rabbitmq()

            # Perform checks that the connection has been opened and marked as
            # open, that the delivery confirmation variable is set and basic_qos
            # called successfully.
            self.assertTrue(
                self.test_console_alerts_handler.rabbitmq.is_connected)
            self.assertTrue(
                self.test_console_alerts_handler.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_console_alerts_handler.rabbitmq.channel
                    ._delivery_confirmation)
            mock_basic_qos.assert_called_once_with(prefetch_count=200)

            # Check whether the producing exchanges have been created by
            # using passive=True. If this check fails an exception is raised
            # automatically.
            self.test_console_alerts_handler.rabbitmq.exchange_declare(
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
            self.test_console_alerts_handler.rabbitmq.basic_publish_confirm(
                exchange=ALERT_EXCHANGE,
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_console_alerts_handler.rabbitmq.queue_declare(
                self.test_console_alerts_handler._console_alerts_handler_queue,
                False, True, False, False)
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones set by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_console_alerts_handler.rabbitmq.queue_delete(
                self.test_rabbit_queue_name)

            res = self.test_console_alerts_handler.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_console_alerts_handler.rabbitmq.queue_bind(
                queue=self.test_rabbit_queue_name,
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

            self.test_console_alerts_handler._send_heartbeat(
                self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_console_alerts_handler.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_console_alerts_handler.rabbitmq.basic_get(
                self.test_rabbit_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(ConsoleChannel, "alert")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_sends_alert_to_console_if_no_processing_errors(
            self, mock_basic_ack, mock_alert) -> None:
        mock_basic_ack.return_value = None

        # Setting it to failed so that there is no attempt to send the heartbeat
        mock_alert.return_value = RequestStatus.FAILED
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()
            blocking_channel = self.test_console_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_console_alerts_handler._process_alert(blocking_channel,
                                                            method, properties,
                                                            body)

            args, _ = mock_alert.call_args
            self.assertEqual(self.test_alert.alert_data, args[0].alert_data)
            self.assertEqual(1, len(args))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(ConsoleChannel, "alert")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_send_alert_to_console_if_processing_errors(
            self, mock_basic_ack, mock_alert) -> None:
        mock_basic_ack.return_value = None

        # Setting it to failed so that there is no attempt to send the heartbeat
        mock_alert.return_value = RequestStatus.FAILED
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()
            blocking_channel = self.test_console_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY)
            data_to_send = copy.deepcopy(self.test_alert.alert_data)
            del data_to_send['message']
            body = json.dumps(data_to_send)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_console_alerts_handler._process_alert(blocking_channel,
                                                            method, properties,
                                                            body)

            mock_alert.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(ConsoleAlertsHandler, "_send_heartbeat")
    @mock.patch.object(ConsoleChannel, "alert")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_sends_hb_if_no_process_err_and_alert_sent_to_console(
            self, mock_basic_ack, mock_alert, mock_send_heartbeat) -> None:
        mock_basic_ack.return_value = None
        mock_alert.return_value = RequestStatus.SUCCESS
        mock_send_heartbeat.return_value = None
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()
            blocking_channel = self.test_console_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_console_alerts_handler._process_alert(blocking_channel,
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

    @parameterized.expand([(RequestStatus.SUCCESS,), (RequestStatus.FAILED,), ])
    @mock.patch.object(ConsoleAlertsHandler, "_send_heartbeat")
    @mock.patch.object(ConsoleChannel, "alert")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_send_hb_if_processing_error(
            self, alert_return, mock_basic_ack, mock_alert,
            mock_send_heartbeat) -> None:
        mock_basic_ack.return_value = None
        mock_alert.return_value = alert_return
        mock_send_heartbeat.return_value = None
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()
            blocking_channel = self.test_console_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY)
            data_to_send = copy.deepcopy(self.test_alert.alert_data)
            del data_to_send['message']
            body = json.dumps(data_to_send)
            properties = pika.spec.BasicProperties()

            # Send alert
            self.test_console_alerts_handler._process_alert(blocking_channel,
                                                            method, properties,
                                                            body)

            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()

    @mock.patch.object(ConsoleAlertsHandler, "_send_heartbeat")
    @mock.patch.object(ConsoleChannel, "alert")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_send_hb_if_alert_was_not_sent(
            self, mock_basic_ack, mock_alert, mock_send_heartbeat) -> None:
        mock_basic_ack.return_value = None
        mock_alert.return_value = RequestStatus.FAILED
        mock_send_heartbeat.return_value = None
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()
            blocking_channel = self.test_console_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # First test with valid alert
            self.test_console_alerts_handler._process_alert(blocking_channel,
                                                            method, properties,
                                                            body)

            # Test with an invalid alert dict
            invalid_alert = copy.deepcopy(self.test_alert.alert_data)
            del invalid_alert['message']
            body = json.dumps(invalid_alert)
            self.test_console_alerts_handler._process_alert(blocking_channel,
                                                            method, properties,
                                                            body)

            mock_send_heartbeat.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        args, _ = mock_basic_ack.call_args
        self.assertEqual(2, len(args))

    @mock.patch.object(ConsoleAlertsHandler, "_send_heartbeat")
    @mock.patch.object(ConsoleChannel, "alert")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_does_not_raise_msg_not_delivered_exception(
            self, mock_basic_ack, mock_alert, mock_send_heartbeat) -> None:
        mock_basic_ack.return_value = None
        mock_alert.return_value = RequestStatus.SUCCESS
        mock_send_heartbeat.side_effect = MessageWasNotDeliveredException(
            'test')
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()
            blocking_channel = self.test_console_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            # This would raise a MessageWasNotDeliveredException if raised,
            # hence the test would fail
            self.test_console_alerts_handler._process_alert(blocking_channel,
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
    @mock.patch.object(ConsoleAlertsHandler, "_send_heartbeat")
    @mock.patch.object(ConsoleChannel, "alert")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_alert_raises_error_if_raised_by_send_hb(
            self, exception_class, exception_instance, mock_basic_ack,
            mock_alert, mock_send_heartbeat) -> None:
        # For this test we will check for channel, connection and unexpected
        # errors.
        mock_basic_ack.return_value = None
        mock_alert.return_value = RequestStatus.SUCCESS
        mock_send_heartbeat.side_effect = exception_instance
        try:
            self.test_console_alerts_handler._initialise_rabbitmq()
            blocking_channel = self.test_console_alerts_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=CONSOLE_HANDLER_INPUT_ROUTING_KEY)
            body = json.dumps(self.test_alert.alert_data)
            properties = pika.spec.BasicProperties()

            self.assertRaises(exception_class,
                              self.test_console_alerts_handler._process_alert,
                              blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_basic_ack.assert_called_once()
