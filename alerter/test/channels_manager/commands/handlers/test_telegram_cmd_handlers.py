import itertools
import json
import logging
import unittest
from datetime import datetime
from unittest import mock

from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError
from pymongo.errors import PyMongoError
from redis import RedisError
from telegram import Update, Message, Chat
from telegram.utils.helpers import escape_markdown

from src.channels_manager.apis.telegram_bot_api import TelegramBotApi
from src.channels_manager.channels import TelegramChannel
from src.channels_manager.commands.handlers.telegram_cmd_handlers import (
    TelegramCommandHandlers)
from src.data_store.mongo import MongoApi
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (SYSTEM_MONITORS_MANAGER_NAME,
                                 GITHUB_MONITORS_MANAGER_NAME,
                                 DATA_TRANSFORMERS_MANAGER_NAME,
                                 SYSTEM_ALERTERS_MANAGER_NAME,
                                 GITHUB_ALERTER_MANAGER_NAME,
                                 DATA_STORE_MANAGER_NAME, ALERT_ROUTER_NAME,
                                 CONFIGS_MANAGER_NAME, CHANNELS_MANAGER_NAME)


class TestTelegramCommandHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.test_handler_name = 'test_telegram_command_handlers'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
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
        self.test_hb_interval = 30
        self.test_grace_interval = 10
        self.test_manager_component = 'Manager_Component1'
        self.test_worker_component1 = 'Component1'
        self.test_worker_component2 = 'Component2'
        self.test_worker_component3 = 'Component3'

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

    @mock.patch.object(RedisApi, "hexists_unsafe")
    @mock.patch.object(RedisApi, "exists_unsafe")
    def test_get_muted_status_returns_correct_status_if_no_severity_muted(
            self, mock_exists_unsafe, mock_hexists_unsafe) -> None:
        mock_exists_unsafe.return_value = False
        mock_hexists_unsafe.return_value = False
        expected_status = ''
        expected_status += "- There is no severity which was muted using " \
                           "/muteall \n"
        for _, chain_name in self.test_associated_chains.items():
            chain_name = escape_markdown(chain_name)
            expected_status += "- {} has no alerts muted.\n".format(chain_name)

        actual_status = self.test_telegram_command_handlers._get_muted_status()

        self.assertEqual(expected_status, actual_status)

    @parameterized.expand([
        (json.dumps(
            {
                'INFO': True,
                'WARNING': True,
                'CRITICAL': True,
                'ERROR': True,
            }
        ).encode(),),
        (json.dumps(
            {
                'INFO': False,
                'WARNING': True,
                'CRITICAL': True,
                'ERROR': True,
            }
        ).encode(),),
        (json.dumps(
            {
                'INFO': True,
                'WARNING': False,
                'CRITICAL': True,
                'ERROR': True,
            }
        ).encode(),),
        (json.dumps(
            {
                'INFO': True,
                'WARNING': True,
                'CRITICAL': False,
                'ERROR': True,
            }
        ).encode(),),
        (json.dumps(
            {
                'INFO': True,
                'WARNING': True,
                'CRITICAL': True,
                'ERROR': False,
            }
        ).encode(),),
    ])
    @mock.patch.object(RedisApi, "hexists_unsafe")
    @mock.patch.object(RedisApi, "exists_unsafe")
    @mock.patch.object(RedisApi, "get_unsafe")
    def test_get_muted_status_return_correct_if_muteall_muted_severities_only(
            self, get_unsafe_ret, mock_get_unsafe, mock_exists_unsafe,
            mock_hexists_unsafe) -> None:
        mock_exists_unsafe.return_value = True
        mock_hexists_unsafe.return_value = False
        mock_get_unsafe.return_value = get_unsafe_ret
        all_chains_muted_severities = []
        for severity, severity_muted in json.loads(
                get_unsafe_ret.decode()).items():
            if severity_muted:
                all_chains_muted_severities.append(severity)
        expected_status = \
            "- All chains have {} alerts muted.\n".format(
                ', '.join(all_chains_muted_severities))

        actual_status = self.test_telegram_command_handlers._get_muted_status()

        self.assertEqual(expected_status, actual_status)

    @mock.patch.object(RedisApi, "hget_unsafe")
    @mock.patch.object(RedisApi, "hexists_unsafe")
    @mock.patch.object(RedisApi, "exists_unsafe")
    def test_get_muted_status_return_correct_if_mute_muted_severities_only(
            self, mock_exists_unsafe, mock_hexists_unsafe,
            mock_hget_unsafe) -> None:
        mock_exists_unsafe.return_value = False
        mock_hexists_unsafe.side_effect = [True, False, True]
        chain1_muted_severities = json.dumps({
            'INFO': False,
            'WARNING': True,
            'CRITICAL': True,
            'ERROR': True,
        }).encode()
        chain3_muted_severities = json.dumps({
            'INFO': True,
            'WARNING': False,
            'CRITICAL': False,
            'ERROR': False,
        }).encode()
        mock_hget_unsafe.side_effect = [chain1_muted_severities,
                                        chain3_muted_severities]

        actual_status = self.test_telegram_command_handlers._get_muted_status()

        expected_status = "- There is no severity which was muted using " \
                          "/muteall \n"

        # We must take care of the order of how severities are pasted in the
        # string because in the function we are using sets in this case. This is
        # important because sets may alter the order of a dict.
        chain1_severity_permutations = list(itertools.permutations(
            ['WARNING', 'CRITICAL', 'ERROR']))
        for permutation in chain1_severity_permutations:
            if ', '.join(permutation) in actual_status:
                expected_status += "- {} has {} alerts muted.\n".format(
                    escape_markdown(self.test_chain_1), ', '.join(permutation))
                break

        expected_status += "- {} has no alerts muted.\n".format(
            self.test_chain_2)
        expected_status += "- {} has {} alerts muted.\n".format(
            escape_markdown(self.test_chain_3), "INFO")

        self.assertEqual(expected_status, actual_status)

    @mock.patch.object(RedisApi, "hget_unsafe")
    @mock.patch.object(RedisApi, "hexists_unsafe")
    @mock.patch.object(RedisApi, "get_unsafe")
    @mock.patch.object(RedisApi, "exists_unsafe")
    def test_get_muted_status_return_correct_if_mute_and_muteall_severities(
            self, mock_exists_unsafe, mock_get_unsafe, mock_hexists_unsafe,
            mock_hget_unsafe) -> None:
        mock_exists_unsafe.return_value = True
        mock_get_unsafe.return_value = json.dumps({
            'INFO': False,
            'WARNING': True,
            'CRITICAL': True,
            'ERROR': False,
        }).encode()
        mock_hexists_unsafe.side_effect = [True, False, True]
        chain1_muted_severities = json.dumps({
            'INFO': False,
            'WARNING': True,
            'CRITICAL': True,
            'ERROR': True,
        }).encode()
        chain3_muted_severities = json.dumps({
            'INFO': True,
            'WARNING': False,
            'CRITICAL': False,
            'ERROR': False,
        }).encode()
        mock_hget_unsafe.side_effect = [chain1_muted_severities,
                                        chain3_muted_severities]

        actual_status = self.test_telegram_command_handlers._get_muted_status()

        expected_status = "- All chains have WARNING, CRITICAL alerts muted.\n"

        # We must take care of the order of how severities are pasted in the
        # string because in the function we are using sets in this case. This is
        # important because sets may alter the order of a dict.
        chain1_severity_permutations = list(itertools.permutations(
            ['WARNING', 'CRITICAL', 'ERROR']))
        for permutation in chain1_severity_permutations:
            if ', '.join(permutation) in actual_status:
                expected_status += "- {} has {} alerts muted.\n".format(
                    escape_markdown(self.test_chain_1), ', '.join(permutation))
                break
        chain3_severity_permutations = list(itertools.permutations(
            ['WARNING', 'CRITICAL', 'INFO']))
        for permutation in chain3_severity_permutations:
            if ', '.join(permutation) in actual_status:
                expected_status += "- {} has {} alerts muted.\n".format(
                    escape_markdown(self.test_chain_3), ', '.join(permutation))
                break

        self.assertEqual(expected_status, actual_status)

    @parameterized.expand([
        (RedisError('test'), None, RedisError),
        (None, RedisError('test'), RedisError),
        (ConnectionResetError('test'), None, ConnectionResetError),
        (None, ConnectionResetError('test'), ConnectionResetError),
        (Exception('test'), None, Exception),
        (None, Exception('test'), Exception),
    ])
    @mock.patch.object(RedisApi, "hexists_unsafe")
    @mock.patch.object(RedisApi, "exists_unsafe")
    def test_get_muted_status_raises_error_if_raised(
            self, exists_unsafe_error, hexists_unsafe_error, error_class,
            mock_exists_unsafe, mock_hexists_unsafe) -> None:
        # For this test we will check only for RedisError, ConnectionResetError
        # and a general exception because these are the most important cases.
        if exists_unsafe_error is None:
            mock_exists_unsafe.return_value = None
        else:
            mock_exists_unsafe.side_effect = exists_unsafe_error
        if hexists_unsafe_error is None:
            mock_hexists_unsafe.return_value = None
        else:
            mock_hexists_unsafe.side_effect = hexists_unsafe_error

        self.assertRaises(error_class,
                          self.test_telegram_command_handlers._get_muted_status)

    @freeze_time("2012-01-01")
    def test_get_manager_component_hb_status_returns_empty_string_if_hb_ok(
            self) -> None:
        # A heartbeat is defined to be "ok" if there are no dead processes and
        # the timestamp is within the grace interval. We will test for both
        # hb_timestamp < grace_interval + hb_interval,
        # hb_timestamp = hb_interval, and
        # hb_timestamp = hb_interval + grace_interval. Note we cannot use
        # parametrize.expand with frozen times together with freeze_time.
        test_heartbeat_1 = {
            'dead_processes': [],
            'running_processes': [self.test_worker_component1,
                                  self.test_worker_component2],
            'timestamp': datetime.now().timestamp(),
            'component_name': self.test_manager_component
        }
        test_heartbeat_2 = {
            'dead_processes': [],
            'running_processes': [self.test_worker_component1,
                                  self.test_worker_component2],
            'timestamp': datetime.now().timestamp() - self.test_hb_interval,
            'component_name': self.test_manager_component
        }
        test_heartbeat_3 = {
            'dead_processes': [],
            'running_processes': [self.test_worker_component1,
                                  self.test_worker_component2],
            'timestamp':
                datetime.now().timestamp() - self.test_hb_interval
                - self.test_grace_interval,
            'component_name': self.test_manager_component
        }

        actual_ret = self.test_telegram_command_handlers \
            ._get_manager_component_hb_status(test_heartbeat_1)
        self.assertEqual('', actual_ret)
        actual_ret = self.test_telegram_command_handlers \
            ._get_manager_component_hb_status(test_heartbeat_2)
        self.assertEqual('', actual_ret)
        actual_ret = self.test_telegram_command_handlers \
            ._get_manager_component_hb_status(test_heartbeat_3)
        self.assertEqual('', actual_ret)

    @parameterized.expand([(41, 1,), (60, 2,), (67, 2,), (89, 2,), (90, 3,), ])
    @freeze_time("2012-01-01")
    def test_get_manager_component_hb_status_return_correct_if_missed_hbs(
            self, hb_delay, expected_missed_hbs) -> None:
        # The component is declared to miss a HB if
        # hb_timestamp > hb_interval (30) + grace_interval (10)
        test_heartbeat = {
            'dead_processes': [],
            'running_processes': [self.test_worker_component1,
                                  self.test_worker_component2],
            'timestamp': datetime.now().timestamp() - hb_delay,
            'component_name': self.test_manager_component
        }

        actual_ret = self.test_telegram_command_handlers \
            ._get_manager_component_hb_status(test_heartbeat)
        expected_ret = \
            "- *{}*: {} - Missed {} heartbeats, either the health-checker " \
            "found problems when saving the heartbeat or the {} is running " \
            "into problems. Please check the logs.\n".format(
                escape_markdown(self.test_manager_component),
                self.test_telegram_command_handlers._get_running_icon(False),
                expected_missed_hbs,
                escape_markdown(self.test_manager_component))
        self.assertEqual(expected_ret, actual_ret)

    def test_get_manager_component_hb_status_ret_correct_if_some_processes_dead(
            self) -> None:
        test_heartbeat = {
            'dead_processes': [self.test_worker_component1,
                               self.test_worker_component2],
            'running_processes': [self.test_worker_component3],
            'timestamp': datetime.now().timestamp(),
            'component_name': self.test_manager_component
        }

        actual_ret = self.test_telegram_command_handlers \
            ._get_manager_component_hb_status(test_heartbeat)
        expected_ret = ''
        for worker_component in test_heartbeat['dead_processes']:
            worker_component = escape_markdown(worker_component)
            expected_ret += "- *{}*: {} - Not running. \n".format(
                worker_component,
                self.test_telegram_command_handlers._get_running_icon(False))
        self.assertEqual(expected_ret, actual_ret)

    @freeze_time("2012-01-01")
    def test_get_worker_component_hb_status_returns_empty_string_if_hb_ok(
            self) -> None:
        # A heartbeat is defined to be "ok" if the component is alive and
        # the timestamp is within the grace interval. We will test for both
        # hb_timestamp < grace_interval + hb_interval,
        # hb_timestamp = hb_interval, and
        # hb_timestamp = hb_interval + grace_interval. Note we cannot use
        # parametrize.expand with frozen times together with freeze_time.
        test_heartbeat_1 = {
            'is_alive': True,
            'timestamp': datetime.now().timestamp(),
            'component_name': self.test_worker_component1
        }
        test_heartbeat_2 = {
            'is_alive': True,
            'timestamp': datetime.now().timestamp() - self.test_hb_interval,
            'component_name': self.test_worker_component1
        }
        test_heartbeat_3 = {
            'is_alive': True,
            'timestamp':
                datetime.now().timestamp() - self.test_hb_interval
                - self.test_grace_interval,
            'component_name': self.test_worker_component1
        }

        actual_ret = self.test_telegram_command_handlers \
            ._get_worker_component_hb_status(test_heartbeat_1)
        self.assertEqual('', actual_ret)
        actual_ret = self.test_telegram_command_handlers \
            ._get_worker_component_hb_status(test_heartbeat_2)
        self.assertEqual('', actual_ret)
        actual_ret = self.test_telegram_command_handlers \
            ._get_worker_component_hb_status(test_heartbeat_3)
        self.assertEqual('', actual_ret)

    @parameterized.expand([(41, 1,), (60, 2,), (67, 2,), (89, 2,), (90, 3,), ])
    @freeze_time("2012-01-01")
    def test_get_worker_component_hb_status_return_correct_if_missed_hbs(
            self, hb_delay, expected_missed_hbs) -> None:
        # The component is declared to miss a HB if
        # hb_timestamp > hb_interval (30) + grace_interval (10)
        test_heartbeat = {
            'is_alive': True,
            'timestamp': datetime.now().timestamp() - hb_delay,
            'component_name': self.test_worker_component1
        }

        actual_ret = self.test_telegram_command_handlers \
            ._get_worker_component_hb_status(test_heartbeat)
        expected_ret = \
            "- *{}*: {} - Missed {} heartbeats, either the health-checker " \
            "found problems when saving the heartbeat or the {} is running " \
            "into problems. Please check the logs.\n".format(
                escape_markdown(self.test_worker_component1),
                self.test_telegram_command_handlers._get_running_icon(False),
                expected_missed_hbs,
                escape_markdown(self.test_worker_component1))
        self.assertEqual(expected_ret, actual_ret)

    def test_get_worker_component_hb_status_return_correct_if_process_dead(
            self) -> None:
        test_heartbeat = {
            'is_alive': False,
            'timestamp': datetime.now().timestamp(),
            'component_name': self.test_manager_component
        }

        actual_ret = self.test_telegram_command_handlers \
            ._get_worker_component_hb_status(test_heartbeat)
        expected_ret = "- *{}*: {} - Not running. \n".format(
            escape_markdown(self.test_manager_component),
            self.test_telegram_command_handlers._get_running_icon(False))
        self.assertEqual(expected_ret, actual_ret)

    def test_get_panic_components_status_return_correct_if_problems_in_HC(
            self) -> None:
        actual_ret = self.test_telegram_command_handlers \
            ._get_panic_components_status(True)
        expected_ret = "- *PANIC Components*: {} - Cannot get live status as " \
                       "there seems to be an issue with the Health " \
                       "Checker.\n".format(self.test_telegram_command_handlers
                                           ._get_running_icon(False))
        self.assertEqual(expected_ret, actual_ret)

    @mock.patch.object(TelegramCommandHandlers,
                       "_get_worker_component_hb_status")
    @mock.patch.object(TelegramCommandHandlers,
                       "_get_manager_component_hb_status")
    @mock.patch.object(RedisApi, "exists_unsafe")
    @mock.patch.object(RedisApi, "get_unsafe")
    def test_get_panic_components_status_return_correct_if_all_ok(
            self, mock_get_unsafe, mock_exists_unsafe, mock_manager_status,
            mock_worker_status) -> None:
        # The PANIC component's status is declared to be all ok if every
        # component in PANIC is running and sending HBs in a timely manner.
        # Note, here we are assuming that there are no problems with the Health
        # Checker
        mock_get_unsafe.return_value = json.dumps({}).encode()
        mock_exists_unsafe.return_value = True

        # If the HB is ok an '' is always sent. This was confirmed in a
        # previous test.
        mock_manager_status.return_value = ''
        mock_worker_status.return_value = ''

        actual_ret = self.test_telegram_command_handlers \
            ._get_panic_components_status(False)
        expected_ret = "- *PANIC Components*: {}\n".format(
            self.test_telegram_command_handlers._get_running_icon(True))
        self.assertEqual(expected_ret, actual_ret)

    @parameterized.expand([
        (
                {
                    SYSTEM_MONITORS_MANAGER_NAME: False,
                    GITHUB_MONITORS_MANAGER_NAME: False,
                    DATA_TRANSFORMERS_MANAGER_NAME: False,
                    SYSTEM_ALERTERS_MANAGER_NAME: False,
                    GITHUB_ALERTER_MANAGER_NAME: False,
                    DATA_STORE_MANAGER_NAME: False,
                    ALERT_ROUTER_NAME: False,
                    CONFIGS_MANAGER_NAME: False,
                    CHANNELS_MANAGER_NAME: False,
                },
        ),
        (
                {
                    SYSTEM_MONITORS_MANAGER_NAME: False,
                    GITHUB_MONITORS_MANAGER_NAME: False,
                    DATA_TRANSFORMERS_MANAGER_NAME: False,
                    SYSTEM_ALERTERS_MANAGER_NAME: False,
                    GITHUB_ALERTER_MANAGER_NAME: True,
                    DATA_STORE_MANAGER_NAME: True,
                    ALERT_ROUTER_NAME: True,
                    CONFIGS_MANAGER_NAME: True,
                    CHANNELS_MANAGER_NAME: True,
                },
        ),
    ])
    @mock.patch.object(TelegramCommandHandlers,
                       "_get_worker_component_hb_status")
    @mock.patch.object(TelegramCommandHandlers,
                       "_get_manager_component_hb_status")
    @mock.patch.object(RedisApi, "exists_unsafe")
    @mock.patch.object(RedisApi, "get_unsafe")
    def test_get_panic_components_status_return_correct_if_no_hbs_yet(
            self, components_hb_available_dict, mock_get_unsafe,
            mock_exists_unsafe, mock_manager_status,
            mock_worker_status) -> None:
        # We will test for both when there are no hbs yet for every component
        # and for some components only. Note, here we are assuming that there
        # are no problems with the Health Checker.
        mock_get_unsafe.return_value = json.dumps({}).encode()
        mock_exists_unsafe.side_effect = list(
            components_hb_available_dict.values())

        # We will assume that every hb is ok if it exists. The case when some
        # might not be ok will be tackled by the next test.
        mock_manager_status.return_value = ''
        mock_worker_status.return_value = ''

        actual_ret = self.test_telegram_command_handlers \
            ._get_panic_components_status(False)
        expected_ret = ''
        for component, hb_available in components_hb_available_dict.items():
            if not hb_available:
                expected_ret += \
                    "- *{}*: {} - No heartbeats yet.\n".format(
                        escape_markdown(component),
                        self.test_telegram_command_handlers._get_running_icon(
                            False))
        self.assertEqual(expected_ret, actual_ret)

    @parameterized.expand([
        (
                {
                    SYSTEM_MONITORS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    GITHUB_MONITORS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    DATA_TRANSFORMERS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    SYSTEM_ALERTERS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    GITHUB_ALERTER_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    DATA_STORE_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    ALERT_ROUTER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    CONFIGS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    CHANNELS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                },
        ),
        (
                {
                    SYSTEM_MONITORS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    GITHUB_MONITORS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    DATA_TRANSFORMERS_MANAGER_NAME: {
                        'hb_exists': False,
                        'hb_ok': False,
                    },
                    SYSTEM_ALERTERS_MANAGER_NAME: {
                        'hb_exists': False,
                        'hb_ok': False,
                    },
                    GITHUB_ALERTER_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': True,
                    },
                    DATA_STORE_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': True,
                    },
                    ALERT_ROUTER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    CONFIGS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                    CHANNELS_MANAGER_NAME: {
                        'hb_exists': True,
                        'hb_ok': False,
                    },
                },
        ),
    ])
    @mock.patch.object(TelegramCommandHandlers,
                       "_get_worker_component_hb_status")
    @mock.patch.object(TelegramCommandHandlers,
                       "_get_manager_component_hb_status")
    @mock.patch.object(RedisApi, "exists_unsafe")
    @mock.patch.object(RedisApi, "get_unsafe")
    def test_get_panic_components_status_return_correct_if_some_hbs_not_ok(
            self, components_hb_status_dict, mock_get_unsafe,
            mock_exists_unsafe, mock_manager_status,
            mock_worker_status) -> None:
        # A hb is declared to be not ok if it exceeds the grace_interval or
        # it implies that some processes are dead. We will test for both when
        # every hb is not ok and when there are no hbs mixed with ok hbs and
        # not ok hbs. Note, here we are assuming that there are no problems with
        # the Health Checker.
        mock_get_unsafe.return_value = json.dumps({}).encode()
        mock_exists_unsafe.side_effect = [
            value['hb_exists'] for value in list(
                components_hb_status_dict.values())
        ]
        manager_components = [SYSTEM_MONITORS_MANAGER_NAME,
                              GITHUB_MONITORS_MANAGER_NAME,
                              DATA_TRANSFORMERS_MANAGER_NAME,
                              SYSTEM_ALERTERS_MANAGER_NAME,
                              GITHUB_ALERTER_MANAGER_NAME,
                              DATA_STORE_MANAGER_NAME, CHANNELS_MANAGER_NAME]
        worker_components = [ALERT_ROUTER_NAME, CONFIGS_MANAGER_NAME]
        mock_manager_status.side_effect = [
            '' if components_hb_status_dict[component]['hb_ok']
            else '- *{}* problems with HB\n'.format(escape_markdown(component))
            for component in manager_components
            if components_hb_status_dict[component]['hb_exists']
        ]
        mock_worker_status.side_effect = [
            '' if components_hb_status_dict[component]['hb_ok']
            else '- *{}* problems with HB\n'.format(escape_markdown(component))
            for component in worker_components
            if components_hb_status_dict[component]['hb_exists']
        ]

        actual_ret = self.test_telegram_command_handlers \
            ._get_panic_components_status(False)
        expected_ret = ''
        for component, hb_status in components_hb_status_dict.items():
            if hb_status['hb_exists']:
                if not hb_status['hb_ok']:
                    expected_ret += '- *{}* problems with HB\n'.format(
                        escape_markdown(component))
            else:
                expected_ret += \
                    "- *{}*: {} - No heartbeats yet.\n".format(
                        escape_markdown(component),
                        self.test_telegram_command_handlers._get_running_icon(
                            False))
        self.assertEqual(expected_ret, actual_ret)
