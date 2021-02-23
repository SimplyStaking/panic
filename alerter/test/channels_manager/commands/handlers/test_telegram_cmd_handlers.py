import logging
import unittest
from datetime import datetime
from unittest import mock

from parameterized import parameterized
from pika.exceptions import AMQPConnectionError
from pymongo.errors import PyMongoError
from redis import RedisError
from telegram import Update, Message, Chat

from src.channels_manager.apis.telegram_bot_api import TelegramBotApi
from src.channels_manager.channels import TelegramChannel
from src.channels_manager.commands.handlers.telegram_cmd_handlers import (
    TelegramCommandHandlers)
from src.data_store.mongo import MongoApi
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env


class TestTelegramCommandHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.test_handler_name = 'test_telegram_command_handlers'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.test_kusama_chain_id = 'kusama1234'
        self.test_cosmos_chain_id = 'cosmos1234'
        self.test_associated_chains = {
            self.test_kusama_chain_id: 'Kusama',
            self.test_cosmos_chain_id: 'Cosmos'
        }
        self.test_channel_name = 'test_telegram_channel'
        self.test_channel_id = 'test_telegram_id12345'
        self.test_bot_token = 'test_bot_token'
        self.test_bot_chat_id = 'test_bot_chat_id'
        self.test_telegram_bot_api = TelegramBotApi(self.test_bot_token,
                                                    self.test_bot_chat_id)
        self.test_telegram_channel = TelegramChannel(
            self.test_channel_name, self.test_channel_id,
            self.dummy_logger.getChild(TelegramChannel.__name__),
            self.test_telegram_bot_api)
        self.test_rabbitmq = RabbitMQApi(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        self.test_redis = RedisApi(
            logger=self.dummy_logger.getChild(RedisApi.__name__),
            host=env.REDIS_IP, db=env.REDIS_DB, port=env.REDIS_PORT,
            namespace=env.UNIQUE_ALERTER_IDENTIFIER)
        self.test_mongo = MongoApi(
            logger=self.dummy_logger.getChild(MongoApi.__name__),
            host=env.DB_IP, db_name=env.DB_NAME, port=env.DB_PORT)

        self.test_telegram_command_handlers = TelegramCommandHandlers(
            self.test_handler_name, self.dummy_logger,
            self.test_associated_chains, self.test_telegram_channel,
            self.test_rabbitmq, self.test_redis, self.test_mongo)
        self.test_chat_object = Chat(1234, 'group')
        self.test_message_object = Message(1234, datetime.now(),
                                           self.test_chat_object)
        self.test_update = Update(123, self.test_message_object)
        self.test_str = "This is a test string message"

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_telegram_bot_api = None
        self.test_telegram_channel = None
        self.test_rabbitmq = None
        self.test_redis = None
        self.test_mongo = None
        self.test_telegram_command_handlers = None
        self.test_update = None
        self.test_message_object = None
        self.test_chat_object = None

    def test__str__returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         str(self.test_telegram_command_handlers))

    def test_handler_name_returns_handler_name(self) -> None:
        self.assertEqual(self.test_handler_name,
                         self.test_telegram_command_handlers.handler_name)

    def test_logger_returns_handler_logger(self) -> None:
        self.assertEqual(self.dummy_logger,
                         self.test_telegram_command_handlers.logger)

    def test_rabbitmq_returns_rabbitmq(self) -> None:
        self.assertEqual(self.test_rabbitmq,
                         self.test_telegram_command_handlers.rabbitmq)

    def test_redis_returns_redis(self) -> None:
        self.assertEqual(self.test_redis,
                         self.test_telegram_command_handlers.redis)

    def test_mongo_returns_mongo(self) -> None:
        self.assertEqual(self.test_mongo,
                         self.test_telegram_command_handlers.mongo)

    def test_associated_chains_returns_associated_chains(self) -> None:
        self.assertDictEqual(
            self.test_associated_chains,
            self.test_telegram_command_handlers.associated_chains)

    def test_telegram_channel_returns_telegram_channel(self) -> None:
        self.assertEqual(self.test_telegram_channel,
                         self.test_telegram_command_handlers.telegram_channel)

    @mock.patch.object(Message, "reply_text")
    def test_formatted_reply_replies_with_message_having_markdown_formatting(
            self, mock_reply_text) -> None:
        # In this test we will check that Update.message.reply_text() is called
        # with the correct parameters as there is no way of testing the actual
        # reply without exposing infrastructure details.
        mock_reply_text.return_value = None
        self.test_telegram_command_handlers.formatted_reply(self.test_update,
                                                            self.test_str)
        mock_reply_text.assert_called_once_with(self.test_str,
                                                parse_mode='Markdown')

    @mock.patch.object(RedisApi, "ping_unsafe")
    def test_redis_running_returns_true_if_redis_is_running(
            self, mock_ping_unsafe) -> None:
        # If redis is down an exception is always raised, therefore we can mock
        # that an exception is not raised when calling RedisApi.ping_unsafe
        mock_ping_unsafe.return_value = None
        actual_ret = self.test_telegram_command_handlers.redis_running()
        self.assertTrue(actual_ret)

    @mock.patch.object(RedisApi, "ping_unsafe")
    def test_redis_running_returns_true_if_redis_is_running(
            self, mock_ping_unsafe) -> None:
        # If redis is down an exception is always raised, therefore we can mock
        # that an exception is not raised when calling RedisApi.ping_unsafe
        mock_ping_unsafe.return_value = None
        actual_ret = self.test_telegram_command_handlers.redis_running()
        self.assertTrue(actual_ret)

    @parameterized.expand([
        (RedisError('test'),),
        (ConnectionResetError('test'),),
    ])
    @mock.patch.object(RedisApi, "ping_unsafe")
    def test_redis_running_returns_false_if_redis_down(
            self, exception, mock_ping_unsafe) -> None:
        # If redis is down then RedisApi.ping_unsafe will either raise a
        # RedisError or a ConnectionResetError. Therefore we can mock those
        # two cases
        mock_ping_unsafe.side_effect = exception
        actual_ret = self.test_telegram_command_handlers.redis_running()
        self.assertFalse(actual_ret)

    @mock.patch.object(RedisApi, "ping_unsafe")
    def test_redis_running_raises_exception_if_unexpected_err(
            self, mock_ping_unsafe) -> None:
        mock_ping_unsafe.side_effect = Exception('Unexpected Exception')
        self.assertRaises(Exception,
                          self.test_telegram_command_handlers.redis_running)

    @mock.patch.object(MongoApi, "ping_unsafe")
    def test_mongo_running_returns_true_if_mongo_is_running(
            self, mock_ping_unsafe) -> None:
        # If mongo is down an exception is always raised, therefore we can mock
        # that an exception is not raised when calling MongoApi.ping_unsafe
        mock_ping_unsafe.return_value = None
        actual_ret = self.test_telegram_command_handlers.mongo_running()
        self.assertTrue(actual_ret)

    @mock.patch.object(MongoApi, "ping_unsafe")
    def test_mongo_running_returns_false_if_mongo_down(
            self, mock_ping_unsafe) -> None:
        # If mongo is down then MongoApi.ping_unsafe will raise a PyMongoError.
        # Therefore we can mock that this exception is raised.
        mock_ping_unsafe.side_effect = PyMongoError('test')
        actual_ret = self.test_telegram_command_handlers.mongo_running()
        self.assertFalse(actual_ret)

    @mock.patch.object(MongoApi, "ping_unsafe")
    def test_mongo_running_raises_exception_if_unexpected_err(
            self, mock_ping_unsafe) -> None:
        mock_ping_unsafe.side_effect = Exception('Unexpected Exception')
        self.assertRaises(Exception,
                          self.test_telegram_command_handlers.mongo_running)

    @mock.patch.object(RabbitMQApi, "connect_unsafe")
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe")
    def test_rabbit_running_returns_true_if_rabbit_is_running(
            self, mock_disconnect_unsafe, mock_connect_unsafe) -> None:
        # If rabbit is down an exception is always raised, therefore we can mock
        # that an exception is not raised when calling
        # RabbitMQApi.connect_unsafe and RabbitMQApi.disconnect_unsafe
        mock_disconnect_unsafe.return_value = None
        mock_connect_unsafe.return_value = None
        actual_ret = self.test_telegram_command_handlers.rabbit_running()
        self.assertTrue(actual_ret)

    @mock.patch.object(RabbitMQApi, "connect_unsafe")
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe")
    def test_rabbit_running_returns_false_if_rabbit_down_when_connecting(
            self, mock_disconnect_unsafe, mock_connect_unsafe, ) -> None:
        # If rabbit is down then RabbitMQApi.connect_unsafe will raise an
        # AMQPConnectionError. Therefore we can mock that this exception is
        # raised.
        mock_connect_unsafe.side_effect = AMQPConnectionError('test')
        mock_disconnect_unsafe.return_value = None
        actual_ret = self.test_telegram_command_handlers.rabbit_running()
        self.assertFalse(actual_ret)

    @mock.patch.object(RabbitMQApi, "connect_unsafe")
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe")
    def test_rabbit_running_returns_false_if_rabbit_down_when_disconnecting(
            self, mock_disconnect_unsafe, mock_connect_unsafe) -> None:
        # If rabbit is down when calling RabbitMQApi.disconnect_unsafe then
        # AMQPConnectionError will be raised. Therefore we can mock that this
        # exception is raised.
        mock_disconnect_unsafe.side_effect = AMQPConnectionError('test')
        mock_connect_unsafe.return_value = None
        actual_ret = self.test_telegram_command_handlers.rabbit_running()
        self.assertFalse(actual_ret)

    @mock.patch.object(RabbitMQApi, "connect_unsafe")
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe")
    def test_rabbit_running_raises_exception_if_unexpected_err_when_connecting(
            self, mock_disconnect_unsafe, mock_connect_unsafe) -> None:
        mock_connect_unsafe.side_effect = Exception('Unexpected Exception')
        mock_disconnect_unsafe.return_value = None
        self.assertRaises(Exception,
                          self.test_telegram_command_handlers.rabbit_running)

    @mock.patch.object(RabbitMQApi, "connect_unsafe")
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe")
    def test_rabbit_running_raises_error_if_unexpected_err_when_disconnecting(
            self, mock_disconnect_unsafe, mock_connect_unsafe) -> None:
        mock_disconnect_unsafe.side_effect = Exception('Unexpected Exception')
        mock_connect_unsafe.return_value = None
        self.assertRaises(Exception,
                          self.test_telegram_command_handlers.rabbit_running)

    @mock.patch.object(TelegramCommandHandlers, "_authorise")
    @mock.patch.object(Message, "reply_text")
    def test_unknown_callback_no_default_message_if_unrecognized_user(
            self, mock_reply_text, mock_authorise) -> None:
        mock_authorise.return_value = False
        mock_reply_text.return_value = None
        self.test_telegram_command_handlers.unknown_callback(self.test_update,
                                                             None)
        mock_reply_text.assert_not_called()

    @mock.patch.object(TelegramCommandHandlers, "_authorise")
    @mock.patch.object(Message, "reply_text")
    def test_unknown_call_returns_default_message_if_recognized_user(
            self, mock_reply_text, mock_authorise) -> None:
        mock_authorise.return_value = True
        mock_reply_text.return_value = None
        self.test_telegram_command_handlers.unknown_callback(self.test_update,
                                                             None)
        mock_reply_text.assert_called_once_with(
            "I did not understand (Type /help)")

    @mock.patch.object(TelegramCommandHandlers, "_authorise")
    @mock.patch.object(Message, "reply_text")
    def test_ping_callback_does_not_return_PONG_if_unrecognized_user(
            self, mock_reply_text, mock_authorise) -> None:
        mock_authorise.return_value = False
        mock_reply_text.return_value = None
        self.test_telegram_command_handlers.ping_callback(self.test_update,
                                                          None)
        mock_reply_text.assert_not_called()

    @mock.patch.object(TelegramCommandHandlers, "_authorise")
    @mock.patch.object(Message, "reply_text")
    def test_ping_callback_returns_PONG_if_recognized_user(
            self, mock_reply_text, mock_authorise) -> None:
        mock_authorise.return_value = True
        mock_reply_text.return_value = None
        self.test_telegram_command_handlers.ping_callback(self.test_update,
                                                          None)
        mock_reply_text.assert_called_once_with("PONG!")

    def test_get_running_icon_returns_tick_if_running(self) -> None:
        actual_ret = self.test_telegram_command_handlers._get_running_icon(True)
        self.assertEqual(u'\U00002705', actual_ret)

    def test_get_running_icon_returns_cross_if_not_running(self) -> None:
        actual_ret = self.test_telegram_command_handlers._get_running_icon(
            False)
        self.assertEqual(u'\U0000274C', actual_ret)

    @parameterized.expand([
        (True, "- *Mongo*: {} \n".format(u'\U00002705')),
        (False, "- *Mongo*: {} \n".format(u'\U0000274C')),
    ])
    @mock.patch.object(TelegramCommandHandlers, "mongo_running")
    def test_get_mongo_based_status_returns_correct_status_if_no_unrec_except(
            self, mongo_is_running, expected_status_message,
            mock_mongo_running) -> None:
        # In this test we will check that the correct status message is returned
        # both if mongo is running or not running. Note that here we are
        # assuming that no unrecognized exceptions are raised.
        mock_mongo_running.return_value = mongo_is_running
        actual_status = \
            self.test_telegram_command_handlers._get_mongo_based_status()
        self.assertEqual(expected_status_message, actual_status)

    @mock.patch.object(TelegramCommandHandlers, "mongo_running")
    def test_get_mongo_based_status_returns_correct_status_if_unrec_exception(
            self, mock_mongo_running) -> None:
        mock_mongo_running.side_effect = Exception("Unrecognized Error")
        expected_status = "- Could not get Mongo status due to an " \
                          "unrecognized error. Check the logs to debug the " \
                          "issue.\n"
        actual_status = \
            self.test_telegram_command_handlers._get_mongo_based_status()
        self.assertEqual(expected_status, actual_status)

    @parameterized.expand([
        (True, "- *RabbitMQ*: {} \n".format(u'\U00002705')),
        (False, "- *RabbitMQ*: {} \n".format(u'\U0000274C')),
    ])
    @mock.patch.object(TelegramCommandHandlers, "rabbit_running")
    def test_get_rabbit_based_status_returns_correct_status_if_no_unrec_except(
            self, rabbit_is_running, expected_status_message,
            mock_rabbit_is_running) -> None:
        # In this test we will check that the correct status message is returned
        # both if rabbit is running or not running. Note that here we are
        # assuming that no unrecognized exceptions are raised.
        mock_rabbit_is_running.return_value = rabbit_is_running
        actual_status = \
            self.test_telegram_command_handlers._get_rabbit_based_status()
        self.assertEqual(expected_status_message, actual_status)

    @mock.patch.object(TelegramCommandHandlers, "rabbit_running")
    def test_get_rabbit_based_status_returns_correct_status_if_unrec_exception(
            self, mock_rabbit_running) -> None:
        mock_rabbit_running.side_effect = Exception("Unrecognized Error")
        expected_status = "- Could not get RabbitMQ status due to an " \
                          "unrecognized error. Check the logs to debug the " \
                          "issue.\n"
        actual_status = \
            self.test_telegram_command_handlers._get_rabbit_based_status()
        self.assertEqual(expected_status, actual_status)

    def test_get_muted_status_returns_correct_status(self) -> None:
        # TODO: We must test nothing muted, /muteall INFO CRITICAL, /mute INFO CRITICAL
        #     : /muteall INFO CRITICAL /mute INFO CRITICAL, /muteall INFO CRITICAL
        #     : /mute ERROR WARNING, previous case other way round. We try to
        #     : parametrize everything here and mock redis.
        pass

# TODO: In some tests we might need to clear redis before and after.
