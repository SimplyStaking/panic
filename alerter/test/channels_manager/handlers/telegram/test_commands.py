import json
import logging
import unittest
from datetime import timedelta, datetime
from unittest import mock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.telegram_bot_api import TelegramBotApi
from src.channels_manager.channels import TelegramChannel
from src.channels_manager.commands.handlers.telegram_cmd_handlers import (
    TelegramCommandHandlers)
from src.channels_manager.handlers.telegram.commands import (
    TelegramCommandsHandler)
from src.data_store.mongo import MongoApi
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          PING_ROUTING_KEY,
                                          CHAN_CMDS_HAN_HB_QUEUE_NAME_TEMPLATE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.exceptions import MessageWasNotDeliveredException
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit)


class TestTelegramCommandsHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.test_handler_name = 'test_telegram_commands_handler'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.test_channel_name = 'test_telegram_channel'
        self.test_channel_id = 'test_telegram_id12345'
        self.test_channel_logger = self.dummy_logger.getChild('dummy_channel')
        self.test_bot_token = '1111111111:AAA-11111111111111'
        self.test_bot_chat_id = 'test_bot_chat_id'
        self.test_base_url = \
            "https://api.telegram.org/bot" + self.test_bot_token
        self.test_api = TelegramBotApi(self.test_bot_token,
                                       self.test_bot_chat_id)
        self.test_channel = TelegramChannel(
            self.test_channel_name, self.test_channel_id,
            self.test_channel_logger, self.test_api)
        self.cmd_handlers_rabbit = RabbitMQApi(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.redis = RedisApi(
            logger=self.dummy_logger.getChild(RedisApi.__name__),
            host=env.REDIS_IP, db=env.REDIS_DB, port=env.REDIS_PORT,
            namespace=env.UNIQUE_ALERTER_IDENTIFIER)
        self.mongo = MongoApi(
            logger=self.dummy_logger.getChild(MongoApi.__name__),
            host=env.DB_IP, db_name=env.DB_NAME, port=env.DB_PORT)
        self.test_command_handlers_logger = self.dummy_logger.getChild(
            'command_handlers')
        self.test_chain_1 = 'Kusama'
        self.test_chain_2 = 'Cosmos'
        self.test_chain_3 = 'Test_Chain'
        self.test_chain1_id = 'kusama1234'
        self.test_chain2_id = 'cosmos1234'
        self.test_chain3_id = 'test_chain11123'
        self.test_associated_chains = {
            self.test_chain1_id: self.test_chain_1,
            self.test_chain2_id: self.test_chain_2,
            self.test_chain3_id: self.test_chain_3
        }
        self.test_telegram_command_handlers = TelegramCommandHandlers(
            self.test_handler_name, self.test_command_handlers_logger,
            self.test_associated_chains, self.test_channel,
            self.cmd_handlers_rabbit, self.redis, self.mongo)
        self.test_telegram_commands_handler = TelegramCommandsHandler(
            self.test_handler_name, self.dummy_logger, self.rabbitmq,
            self.test_channel, self.test_telegram_command_handlers)
        self.test_data_str = "this is a test string"
        self.test_rabbit_queue_name = 'Test Queue'
        self.test_timestamp = 45676565.556
        self.test_heartbeat = {
            'component_name': 'Test Component',
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
        connect_to_rabbit(self.test_telegram_commands_handler.rabbitmq)
        delete_queue_if_exists(self.test_telegram_commands_handler.rabbitmq,
                               self.test_rabbit_queue_name)
        delete_queue_if_exists(
            self.test_telegram_commands_handler.rabbitmq,
            self.test_telegram_commands_handler
                ._telegram_commands_handler_queue)
        delete_exchange_if_exists(self.test_telegram_commands_handler.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.test_telegram_commands_handler.rabbitmq)

        self.dummy_logger = None
        self.test_channel_logger = None
        self.test_command_handlers_logger = None
        self.rabbitmq = None
        self.cmd_handlers_rabbit = None
        self.test_alert = None
        self.test_channel = None
        self.test_api = None
        self.redis = None
        self.mongo = None
        self.test_telegram_commands_handler._updater.stop()
        self.test_telegram_commands_handler._updater = None
        self.test_telegram_command_handlers._rabbit = None
        self.test_telegram_command_handlers._mongo = None
        self.test_telegram_command_handlers._redis = None
        self.test_telegram_command_handlers = None
        self.test_telegram_commands_handler = None

    def test__str__returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         str(self.test_telegram_commands_handler))

    def test_handler_name_returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         self.test_telegram_commands_handler.handler_name)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_telegram_commands_handler._listen_for_data()
        mock_start_consuming.assert_called_once_with()

    def test_cmd_handlers_returns_associated_command_handlers(self) -> None:
        self.assertEqual(self.test_telegram_command_handlers,
                         self.test_telegram_commands_handler.cmd_handlers)

    def test_telegram_channel_returns_associated_telegram_channel(self) -> None:
        self.assertEqual(self.test_channel,
                         self.test_telegram_commands_handler.telegram_channel)

    def test_init_initialises_handler_correctly(self) -> None:
        # In this test we will check that all fields that do not have a getter
        # were initialised correctly, as the previous tests test the getters.
        expected_updater = Updater(token=self.test_bot_token, use_context=True)
        expected_command_specific_handlers = [
            CommandHandler('start',
                           self.test_telegram_command_handlers.start_callback),
            CommandHandler('mute',
                           self.test_telegram_command_handlers.mute_callback),
            CommandHandler('unmute',
                           self.test_telegram_command_handlers.unmute_callback),
            CommandHandler(
                'muteall',
                self.test_telegram_command_handlers.muteall_callback),
            CommandHandler(
                'unmuteall',
                self.test_telegram_command_handlers.unmuteall_callback),
            CommandHandler('status',
                           self.test_telegram_command_handlers.status_callback),
            CommandHandler('ping',
                           self.test_telegram_command_handlers.ping_callback),
            CommandHandler('help',
                           self.test_telegram_command_handlers.help_callback),
            MessageHandler(Filters.command,
                           self.test_telegram_command_handlers.unknown_callback)
        ]
        actual_command_specific_handlers = \
            self.test_telegram_commands_handler._updater.dispatcher.handlers[0]
        self.assertEqual(CHAN_CMDS_HAN_HB_QUEUE_NAME_TEMPLATE.format(
            self.test_channel_id),
            self.test_telegram_commands_handler
                ._telegram_commands_handler_queue)
        self.assertEqual(expected_updater.bot.token,
                         self.test_telegram_commands_handler._updater.bot.token)
        self.assertTrue(
            self.test_telegram_commands_handler._updater.dispatcher.use_context)
        for i in range(len(actual_command_specific_handlers)):
            if type(actual_command_specific_handlers[i]) == CommandHandler:
                self.assertEqual(expected_command_specific_handlers[i].callback,
                                 actual_command_specific_handlers[i].callback)
                self.assertEqual(expected_command_specific_handlers[i].command,
                                 actual_command_specific_handlers[i].command)
            elif type(actual_command_specific_handlers[i]) == MessageHandler:
                self.assertEqual(expected_command_specific_handlers[i].callback,
                                 actual_command_specific_handlers[i].callback)

    def test_initialise_rabbitmq_initialises_rabbit_correctly(self) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges and queues have not already been
            # declared
            connect_to_rabbit(self.rabbitmq)
            self.test_telegram_commands_handler.rabbitmq.queue_delete(
                self.test_telegram_commands_handler
                    ._telegram_commands_handler_queue)
            self.test_telegram_commands_handler.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            disconnect_from_rabbit(self.rabbitmq)

            self.test_telegram_commands_handler._initialise_rabbitmq()

            # Perform checks that the connection has been opened and marked as
            # open, that the delivery confirmation variable is set and basic_qos
            # called successfully.
            self.assertTrue(
                self.test_telegram_commands_handler.rabbitmq.is_connected)
            self.assertTrue(
                self.test_telegram_commands_handler.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_telegram_commands_handler.rabbitmq.channel
                    ._delivery_confirmation)

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
            self.test_telegram_commands_handler.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=PING_ROUTING_KEY, body=self.test_data_str,
                is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_telegram_commands_handler.rabbitmq.queue_declare(
                self.test_telegram_commands_handler
                    ._telegram_commands_handler_queue, False, True, False,
                False)
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones set by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_telegram_commands_handler._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_telegram_commands_handler.rabbitmq.queue_delete(
                self.test_rabbit_queue_name)

            res = self.test_telegram_commands_handler.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_telegram_commands_handler.rabbitmq.queue_bind(
                queue=self.test_rabbit_queue_name,
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

            self.test_telegram_commands_handler._send_heartbeat(
                self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_telegram_commands_handler.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_telegram_commands_handler.rabbitmq.basic_get(
                self.test_rabbit_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([(True,), (False,), ])
    @mock.patch.object(Updater, "start_polling")
    @mock.patch.object(Updater, "idle")
    def test_start_handling_starts_polling_if_updater_not_running(
            self, run_in_background, mock_idle, mock_start_polling) -> None:
        mock_idle.return_value = None
        mock_start_polling.return_value = None
        self.test_telegram_commands_handler._updater.running = False
        self.test_telegram_commands_handler._start_handling(run_in_background)
        mock_start_polling.assert_called_once_with(drop_pending_updates=True)

    @parameterized.expand([(True,), (False,), ])
    @mock.patch.object(Updater, "start_polling")
    @mock.patch.object(Updater, "idle")
    def test_start_handling_does_not_start_polling_if_updater_is_running(
            self, run_in_background, mock_idle, mock_start_polling) -> None:
        mock_idle.return_value = None
        mock_start_polling.return_value = None
        self.test_telegram_commands_handler._updater.running = True
        self.test_telegram_commands_handler._start_handling(run_in_background)
        mock_start_polling.assert_not_called()

    @parameterized.expand([(True,), (False,), ])
    @mock.patch.object(Updater, "start_polling")
    @mock.patch.object(Updater, "idle")
    def test_start_handling_blocks_if_updater_not_running_in_the_background(
            self, running, mock_idle, mock_start_polling) -> None:
        mock_idle.return_value = None
        mock_start_polling.return_value = None
        self.test_telegram_commands_handler._updater.running = running
        self.test_telegram_commands_handler._start_handling(False)
        mock_idle.assert_called_once_with(stop_signals=[])

    @parameterized.expand([(True,), (False,), ])
    @mock.patch.object(Updater, "start_polling")
    @mock.patch.object(Updater, "idle")
    def test_start_handling_does_not_block_if_updater_running_in_the_background(
            self, running, mock_idle, mock_start_polling) -> None:
        mock_idle.return_value = None
        mock_start_polling.return_value = None
        self.test_telegram_commands_handler._updater.running = running
        self.test_telegram_commands_handler._start_handling(True)
        mock_idle.assert_not_called()

    @mock.patch.object(Updater, "stop")
    def test_stop_handling_stops_handling(self, mock_stop_handling) -> None:
        mock_stop_handling.return_value = None
        self.test_telegram_commands_handler._stop_handling()
        mock_stop_handling.assert_called_once_with()

    @freeze_time("2012-01-01")
    @mock.patch.object(TelegramCommandsHandler, "_send_heartbeat")
    def test_process_ping_sends_correct_heartbeat_if_updater_is_running(
            self, mock_send_hb) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat. The actual sending was already tested above.
        mock_send_hb.return_value = None
        self.test_telegram_commands_handler._updater.running = True
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_telegram_commands_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_telegram_commands_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_telegram_commands_handler._process_ping(blocking_channel,
                                                              method,
                                                              properties, body)

            expected_hb = {
                'component_name': self.test_handler_name,
                'is_alive': True,
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(TelegramCommandsHandler, "_start_handling")
    @mock.patch.object(TelegramCommandsHandler, "_send_heartbeat")
    def test_process_ping_sends_correct_heartbeat_if_updater_is_not_running(
            self, mock_send_hb, mock_start_handling) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat. The actual sending was already tested above.
        mock_send_hb.return_value = None
        mock_start_handling.return_value = None
        self.test_telegram_commands_handler._updater.running = False
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_telegram_commands_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_telegram_commands_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_telegram_commands_handler._process_ping(blocking_channel,
                                                              method,
                                                              properties, body)

            expected_hb = {
                'component_name': self.test_handler_name,
                'is_alive': False,
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(TelegramCommandsHandler, "_start_handling")
    @mock.patch.object(TelegramCommandsHandler, "_send_heartbeat")
    def test_process_ping_restarts_updater_if_it_is_dead(
            self, mock_send_hb, mock_start_handling) -> None:
        mock_send_hb.return_value = None
        mock_start_handling.return_value = None
        self.test_telegram_commands_handler._updater.running = False
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_telegram_commands_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_telegram_commands_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_telegram_commands_handler._process_ping(blocking_channel,
                                                              method,
                                                              properties, body)

            mock_start_handling.assert_called_once_with(run_in_background=True)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(TelegramCommandsHandler, "_start_handling")
    @mock.patch.object(TelegramCommandsHandler, "_send_heartbeat")
    def test_process_ping_does_not_restart_updater_if_it_is_alive(
            self, mock_send_hb, mock_start_handling) -> None:
        mock_send_hb.return_value = None
        mock_start_handling.return_value = None
        self.test_telegram_commands_handler._updater.running = True
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_telegram_commands_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_telegram_commands_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_telegram_commands_handler._process_ping(blocking_channel,
                                                              method,
                                                              properties, body)

            mock_start_handling.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(TelegramCommandsHandler, "_start_handling")
    @mock.patch.object(TelegramCommandsHandler, "_send_heartbeat")
    def test_process_ping_does_not_send_heartbeat_if_error_when_computing_hb(
            self, mock_send_hb, mock_start_handling) -> None:
        # In this case an exception may only be raised if the updater is
        # restarted.
        mock_send_hb.return_value = None
        mock_start_handling.side_effect = Exception('test')
        self.test_telegram_commands_handler._updater.running = False
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_telegram_commands_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_telegram_commands_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_telegram_commands_handler._process_ping(blocking_channel,
                                                              method,
                                                              properties, body)

            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(TelegramCommandsHandler, "_send_heartbeat")
    def test_process_ping_does_not_raise_msg_was_not_delivered_exception(
            self, mock_send_hb) -> None:
        # In this case an exception may only be raised if the updater is
        # restarted.
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test')
        self.test_telegram_commands_handler._updater.running = True
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_telegram_commands_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_telegram_commands_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_telegram_commands_handler._process_ping(blocking_channel,
                                                              method,
                                                              properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(TelegramCommandsHandler, "_send_heartbeat")
    def test_process_ping_raises_error_if_raised_by_send_heartbeat(
            self, exception_class, exception_instance,
            mock_send_heartbeat) -> None:
        # For this test we will check for channel, connection and unexpected
        # errors.
        mock_send_heartbeat.side_effect = exception_instance
        self.test_telegram_commands_handler._updater.running = True
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_telegram_commands_handler._initialise_rabbitmq()
            blocking_channel = \
                self.test_telegram_commands_handler.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.assertRaises(
                exception_class,
                self.test_telegram_commands_handler._process_ping,
                blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
