import logging
import unittest
from datetime import timedelta
from unittest import mock
from unittest.mock import call

from src.channels_manager.apis.email_api import EmailApi
from src.channels_manager.apis.opsgenie_api import OpsgenieApi
from src.channels_manager.apis.pagerduty_api import PagerDutyApi
from src.channels_manager.apis.slack_bot_api import SlackBotApi
from src.channels_manager.apis.telegram_bot_api import TelegramBotApi
from src.channels_manager.apis.twilio_api import TwilioApi
from src.channels_manager.channels import TelegramChannel, SlackChannel, \
    PagerDutyChannel
from src.channels_manager.channels.console import ConsoleChannel
from src.channels_manager.channels.email import EmailChannel
from src.channels_manager.channels.log import LogChannel
from src.channels_manager.channels.opsgenie import OpsgenieChannel
from src.channels_manager.channels.twilio import TwilioChannel
from src.channels_manager.commands.handlers.slack_cmd_handlers import (
    SlackCommandHandlers)
from src.channels_manager.commands.handlers.telegram_cmd_handlers import (
    TelegramCommandHandlers)
from src.channels_manager.handlers import (TelegramAlertsHandler,
                                           SlackAlertsHandler,
                                           EmailAlertsHandler)
from src.channels_manager.handlers.console.alerts import ConsoleAlertsHandler
from src.channels_manager.handlers.log.alerts import LogAlertsHandler
from src.channels_manager.handlers.opsgenie.alerts import OpsgenieAlertsHandler
from src.channels_manager.handlers.pagerduty.alerts import (
    PagerDutyAlertsHandler)
from src.channels_manager.handlers.slack.commands import (
    SlackCommandsHandler)
from src.channels_manager.handlers.starters import (
    _initialise_channel_handler_logger, _initialise_alerts_logger,
    _initialise_telegram_alerts_handler, start_telegram_alerts_handler,
    _initialise_telegram_commands_handler, start_telegram_commands_handler,
    _initialise_slack_alerts_handler, start_slack_alerts_handler,
    _initialise_slack_commands_handler, start_slack_commands_handler,
    _initialise_twilio_alerts_handler, start_twilio_alerts_handler,
    _initialise_pagerduty_alerts_handler, start_pagerduty_alerts_handler,
    _initialise_email_alerts_handler, start_email_alerts_handler,
    _initialise_opsgenie_alerts_handler, start_opsgenie_alerts_handler,
    _initialise_console_alerts_handler, start_console_alerts_handler,
    _initialise_log_alerts_handler, start_log_alerts_handler)
from src.channels_manager.handlers.telegram.commands import (
    TelegramCommandsHandler)
from src.channels_manager.handlers.twilio.alerts import TwilioAlertsHandler
from src.data_store.mongo import MongoApi
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.mongo import REPLICA_SET_HOSTS, REPLICA_SET_NAME
from src.utils.constants.names import (TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE,
                                       TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE,
                                       TELEGRAM_COMMAND_HANDLERS_NAME,
                                       SLACK_ALERTS_HANDLER_NAME_TEMPLATE,
                                       SLACK_COMMANDS_HANDLER_NAME_TEMPLATE,
                                       SLACK_COMMAND_HANDLERS_NAME,
                                       TWILIO_ALERTS_HANDLER_NAME_TEMPLATE,
                                       PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE,
                                       EMAIL_ALERTS_HANDLER_NAME_TEMPLATE,
                                       OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE,
                                       CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE,
                                       LOG_ALERTS_HANDLER_NAME_TEMPLATE)


class TestHandlerStarters(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.handler_display_name = 'Test Channel Handler'
        self.handler_module_name = 'TestChannelHandler'
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.telegram_channel_name = 'test_telegram_channel'
        self.telegram_channel_id = 'test_telegram_id12345'
        self.telegram_channel_logger = self.dummy_logger.getChild(
            'telegram_channel_logger')
        self.telegram_bot_token = '1111111111:AAA-11111111111111'
        self.telegram_bot_chat_id = 'test_bot_chat_id'
        self.telegram_base_url = "https://api.telegram.org/bot" + \
                                 self.telegram_bot_token
        self.telegram_bot_api = TelegramBotApi(
            self.telegram_bot_token, self.telegram_bot_chat_id)
        self.telegram_channel = TelegramChannel(
            self.telegram_channel_name, self.telegram_channel_id,
            self.telegram_channel_logger, self.telegram_bot_api)
        self.test_queue_size = 1000
        self.test_max_attempts = 5
        self.test_alert_validity_threshold = 300
        self.telegram_alerts_handler = TelegramAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.telegram_channel, self.test_queue_size, self.test_max_attempts,
            self.test_alert_validity_threshold)
        self.slack_channel_name = 'test_slack_channel'
        self.slack_channel_id = 'test_slack_id12345'
        self.slack_channel_logger = self.dummy_logger.getChild(
            'slack_channel_logger')
        self.slack_bot_token = \
            'xoxb-0123456789012-0123456789012-abcdefABCDEF012345abcdef'
        self.slack_app_token = 'xapp-0-ABCDEF01234-0123456789012' \
                               '-abcdefABCDEF012345abcdef'
        self.slack_bot_channel_id = 'slack_bot_channel_id'
        self.slack_bot_api = SlackBotApi(
            self.slack_bot_token,
            self.slack_app_token, self.slack_bot_channel_id)
        self.slack_channel = SlackChannel(
            self.slack_channel_name, self.slack_channel_id,
            self.slack_channel_logger, self.slack_bot_api)
        self.slack_alerts_handler = SlackAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.slack_channel, self.test_queue_size, self.test_max_attempts,
            self.test_alert_validity_threshold)
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
            host=REPLICA_SET_HOSTS, db_name=env.DB_NAME,
            replicaSet=REPLICA_SET_NAME)
        self.telegram_command_handlers_logger = self.dummy_logger.getChild(
            TelegramCommandHandlers.__name__)
        self.slack_command_handlers_logger = self.dummy_logger.getChild(
            SlackCommandHandlers.__name__)
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
        self.telegram_command_handlers = TelegramCommandHandlers(
            self.handler_display_name, self.telegram_command_handlers_logger,
            self.test_associated_chains, self.telegram_channel,
            self.cmd_handlers_rabbit, self.redis, self.mongo)
        self.telegram_commands_handler = TelegramCommandsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.telegram_channel, self.telegram_command_handlers)
        self.slack_command_handlers = SlackCommandHandlers(
            self.handler_display_name, self.slack_command_handlers_logger,
            self.test_associated_chains, self.slack_channel,
            self.cmd_handlers_rabbit, self.redis, self.mongo)
        self.slack_commands_handler = SlackCommandsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.slack_channel, self.slack_command_handlers, False)
        self.twilio_channel_name = 'test_twilio_channel'
        self.twilio_channel_id = 'test_twilio_id12345'
        self.twilio_channel_logger = self.dummy_logger.getChild(
            'twilio_channel')
        self.account_sid = 'test_account_sid'
        self.auth_token = 'test_auth_token'
        self.call_from = 'test_call_from_number'
        self.call_to = ['test_call_to_number_1',
                        'test_call_to_number_2', 'test_call_to_number_3']
        self.twiml = '<Response><Reject/></Response>'
        self.twiml_is_url = False
        self.twilio_api = TwilioApi(self.account_sid, self.auth_token)
        self.twilio_channel = TwilioChannel(
            self.twilio_channel_name, self.twilio_channel_id,
            self.twilio_channel_logger, self.twilio_api)
        self.twilio_alerts_handler = TwilioAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.twilio_channel, self.call_from, self.call_to, self.twiml,
            self.twiml_is_url, self.test_max_attempts,
            self.test_alert_validity_threshold)
        self.integration_key = 'test_integration_key'
        self.pagerduty_channel_name = 'test_pagerduty_channel'
        self.pagerduty_channel_id = 'test_pagerduty_id12345'
        self.pagerduty_channel_logger = self.dummy_logger.getChild('pagerduty')
        self.pagerduty_api = PagerDutyApi(self.integration_key)
        self.pagerduty_channel = PagerDutyChannel(
            self.pagerduty_channel_name, self.pagerduty_channel_id,
            self.pagerduty_channel_logger, self.pagerduty_api)
        self.pagerduty_alerts_handler = PagerDutyAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.pagerduty_channel, self.test_queue_size,
            self.test_max_attempts, self.test_alert_validity_threshold)
        self.email_channel_name = 'test_email_channel'
        self.email_channel_id = 'test_email1234'
        self.email_channel_logger = self.dummy_logger.getChild('email_channel')
        self.emails_to = ['test1@example.com', 'test2@example.com',
                          'test3@example.com']
        self.smtp = 'test smtp server'
        self.sender = 'test sender'
        self.username = 'test username'
        self.password = 'test password'
        self.port = 10
        self.email_api = EmailApi(self.smtp, self.sender, self.username,
                                  self.password, self.port)
        self.email_channel = EmailChannel(self.email_channel_name,
                                          self.email_channel_id,
                                          self.email_channel_logger,
                                          self.emails_to, self.email_api)
        self.email_alerts_handler = EmailAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.email_channel, self.test_queue_size, self.test_max_attempts,
            self.test_alert_validity_threshold)
        self.api_key = 'test api key'
        self.opsgenie_channel_name = 'test_opgenie_channel'
        self.opsgenie_channel_id = 'test_opsgenie_id12345'
        self.opsgenie_channel_logger = self.dummy_logger.getChild(
            'opsgenie_channel')
        self.eu_host = True
        self.opsgenie_api = OpsgenieApi(self.api_key, self.eu_host)
        self.opsgenie_channel = OpsgenieChannel(self.opsgenie_channel_name,
                                                self.opsgenie_channel_id,
                                                self.opsgenie_channel_logger,
                                                self.opsgenie_api)
        self.opsgenie_alerts_handler = OpsgenieAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.opsgenie_channel, self.test_queue_size, self.test_max_attempts,
            self.test_alert_validity_threshold)
        self.console_channel_name = 'test_console_channel'
        self.console_channel_id = 'test_console1234'
        self.console_channel_logger = self.dummy_logger.getChild(
            'console_channel')
        self.console_channel = ConsoleChannel(self.console_channel_name,
                                              self.console_channel_id,
                                              self.console_channel_logger)
        self.console_alerts_handler = ConsoleAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.console_channel)
        self.log_channel_name = 'test_logger_channel'
        self.log_channel_id = 'test_logger1234'
        self.log_channel_logger = self.dummy_logger.getChild('log_channel')
        self.alerts_logger = self.dummy_logger.getChild('alerts_logger')
        self.log_channel = LogChannel(self.log_channel_name,
                                      self.log_channel_id,
                                      self.log_channel_logger,
                                      self.alerts_logger)
        self.log_alerts_handler = LogAlertsHandler(
            self.handler_display_name, self.dummy_logger, self.rabbitmq,
            self.log_channel)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.telegram_channel_logger = None
        self.telegram_bot_api = None
        self.telegram_channel = None
        self.telegram_alerts_handler = None
        self.slack_channel_logger = None
        self.slack_bot_api = None
        self.slack_channel = None
        self.slack_alerts_handler = None
        self.cmd_handlers_rabbit = None
        self.redis = None
        self.mongo = None
        self.telegram_command_handlers_logger = None
        self.telegram_command_handlers = None
        self.telegram_commands_handler = None
        self.slack_command_handlers = None
        self.slack_commands_handler = None
        self.twilio_api = None
        self.twilio_channel = None
        self.twilio_alerts_handler = None
        self.pagerduty_api = None
        self.pagerduty_channel_logger = None
        self.pagerduty_channel = None
        self.pagerduty_alerts_handler = None
        self.email_api = None
        self.email_channel_logger = None
        self.email_channel = None
        self.email_alerts_handler = None
        self.opsgenie_api = None
        self.opsgenie_channel_logger = None
        self.opsgenie_channel = None
        self.opsgenie_alerts_handler = None
        self.console_channel_logger = None
        self.console_channel = None
        self.console_alerts_handler = None
        self.log_channel_logger = None
        self.alerts_logger = None
        self.log_channel = None
        self.log_alerts_handler = None

    @mock.patch("src.channels_manager.handlers.starters.create_logger")
    def test_initialise_channel_handler_logger_creates_and_returns_logger(
            self, mock_create_logger) -> None:
        # In this test we will check that _create_logger was called correctly,
        # and that the created logger is returned. The actual logic of logger
        # creation should be tested when testing _create_logger
        mock_create_logger.return_value = self.dummy_logger

        returned_logger = _initialise_channel_handler_logger(
            self.handler_display_name, self.handler_module_name)

        mock_create_logger.assert_called_once_with(
            env.CHANNEL_HANDLERS_LOG_FILE_TEMPLATE.format(
                self.handler_display_name), self.handler_module_name,
            env.LOGGING_LEVEL, True
        )

        self.assertEqual(self.dummy_logger, returned_logger)

    @mock.patch("src.channels_manager.handlers.starters.create_logger")
    def test_initialise_alerts_logger_creates_and_returns_logger(
            self, mock_create_logger) -> None:
        # In this test we will check that _create_logger was called correctly,
        # and that the created logger is returned. The actual logic of logger
        # creation should be tested when testing _create_logger
        mock_create_logger.return_value = self.dummy_logger

        returned_logger = _initialise_alerts_logger()

        mock_create_logger.assert_called_once_with(
            env.ALERTS_LOG_FILE, 'Alerts', env.LOGGING_LEVEL, True
        )

        self.assertEqual(self.dummy_logger, returned_logger)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.TelegramBotApi")
    @mock.patch("src.channels_manager.handlers.starters.TelegramChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.TelegramAlertsHandler")
    def test_initialise_telegram_alerts_handler_creates_TAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_telegram_channel,
            mock_bot_api, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_bot_api.return_value = self.telegram_bot_api
        mock_telegram_channel.return_value = self.telegram_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.telegram_alerts_handler
        mock_alerts_handler.__name__ = TelegramAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_telegram_channel.__name__ = TelegramChannel.__name__

        _initialise_telegram_alerts_handler(
            self.telegram_bot_token, self.telegram_bot_chat_id,
            self.telegram_channel_id,
            self.telegram_channel_name)

        handler_display_name = TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.telegram_channel_name)
        mock_init_logger.assert_called_once_with(handler_display_name,
                                                 TelegramAlertsHandler.__name__)
        mock_bot_api.assert_called_once_with(
            self.telegram_bot_token, self.telegram_bot_chat_id)
        mock_telegram_channel.assert_called_once_with(
            self.telegram_channel_name, self.telegram_channel_id,
            self.dummy_logger.getChild(TelegramChannel.__name__),
            self.telegram_bot_api)
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.telegram_channel, env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_telegram_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_telegram_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_tah) -> None:
        mock_init_tah.return_value = self.telegram_alerts_handler
        mock_start_handler.return_value = None

        start_telegram_alerts_handler(self.telegram_bot_token,
                                      self.telegram_bot_chat_id,
                                      self.telegram_channel_id,
                                      self.telegram_channel_name)

        mock_init_tah.assert_called_once_with(self.telegram_bot_token,
                                              self.telegram_bot_chat_id,
                                              self.telegram_channel_id,
                                              self.telegram_channel_name)
        mock_start_handler.assert_called_once_with(
            self.telegram_alerts_handler)

    @mock.patch("src.channels_manager.handlers.starters.MongoApi")
    @mock.patch("src.channels_manager.handlers.starters.RedisApi")
    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.TelegramBotApi")
    @mock.patch("src.channels_manager.handlers.starters.TelegramChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters."
                "TelegramCommandsHandler")
    @mock.patch("src.channels_manager.handlers.starters."
                "TelegramCommandHandlers")
    def test_initialise_telegram_commands_handler_creates_TCH_correctly(
            self, mock_command_handlers, mock_commands_handler, mock_rabbit,
            mock_telegram_channel, mock_bot_api, mock_init_logger, mock_redis,
            mock_mongo) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_bot_api.return_value = self.telegram_bot_api
        mock_telegram_channel.return_value = self.telegram_channel
        mock_rabbit.side_effect = [self.cmd_handlers_rabbit, self.rabbitmq]
        mock_commands_handler.return_value = self.telegram_commands_handler
        mock_commands_handler.__name__ = TelegramCommandsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_telegram_channel.__name__ = TelegramChannel.__name__
        mock_redis.return_value = self.redis
        mock_redis.__name__ = RedisApi.__name__
        mock_mongo.return_value = self.mongo
        mock_mongo.__name__ = MongoApi.__name__
        mock_command_handlers.return_value = self.telegram_command_handlers
        mock_command_handlers.__name__ = TelegramCommandHandlers.__name__

        _initialise_telegram_commands_handler(
            self.telegram_bot_token, self.telegram_bot_chat_id,
            self.telegram_channel_id,
            self.telegram_channel_name, self.test_associated_chains)

        handler_display_name = TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE.format(
            self.telegram_channel_name)
        mock_init_logger.assert_called_once_with(
            handler_display_name, TelegramCommandsHandler.__name__)
        mock_bot_api.assert_called_once_with(
            self.telegram_bot_token, self.telegram_bot_chat_id)
        mock_telegram_channel.assert_called_once_with(
            self.telegram_channel_name, self.telegram_channel_id,
            self.dummy_logger.getChild(TelegramChannel.__name__),
            self.telegram_bot_api)
        actual_rabbit_calls = mock_rabbit.call_args_list
        expected_rabbit_calls = [
            call(logger=self.telegram_command_handlers_logger.getChild(
                RabbitMQApi.__name__), host=env.RABBIT_IP),
            call(logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
                 host=env.RABBIT_IP),
        ]
        self.assertEqual(expected_rabbit_calls, actual_rabbit_calls)
        mock_redis.assert_called_once_with(
            logger=self.telegram_command_handlers_logger.getChild(
                RedisApi.__name__),
            host=env.REDIS_IP, db=env.REDIS_DB, port=env.REDIS_PORT,
            namespace=env.UNIQUE_ALERTER_IDENTIFIER)
        mock_mongo.assert_called_once_with(
            logger=self.telegram_command_handlers_logger.getChild(
                MongoApi.__name__),
            host=REPLICA_SET_HOSTS,  db_name=env.DB_NAME, port=env.DB_PORT)
        mock_command_handlers.assert_called_once_with(
            TELEGRAM_COMMAND_HANDLERS_NAME,
            self.telegram_command_handlers_logger,
            self.test_associated_chains, self.telegram_channel,
            self.cmd_handlers_rabbit, self.redis, self.mongo)
        mock_commands_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.telegram_channel, self.telegram_command_handlers)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_telegram_commands_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_telegram_commands_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_tch) -> None:
        mock_init_tch.return_value = self.telegram_commands_handler
        mock_start_handler.return_value = None

        start_telegram_commands_handler(self.telegram_bot_token,
                                        self.telegram_bot_chat_id,
                                        self.telegram_channel_id,
                                        self.telegram_channel_name,
                                        self.test_associated_chains)

        mock_init_tch.assert_called_once_with(self.telegram_bot_token,
                                              self.telegram_bot_chat_id,
                                              self.telegram_channel_id,
                                              self.telegram_channel_name,
                                              self.test_associated_chains)
        mock_start_handler.assert_called_once_with(
            self.telegram_commands_handler)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.SlackBotApi")
    @mock.patch("src.channels_manager.handlers.starters.SlackChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.SlackAlertsHandler")
    def test_initialise_slack_alerts_handler_creates_SAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_slack_channel,
            mock_bot_api, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_bot_api.return_value = self.slack_bot_api
        mock_slack_channel.return_value = self.slack_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.slack_alerts_handler
        mock_alerts_handler.__name__ = SlackAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_slack_channel.__name__ = SlackChannel.__name__

        _initialise_slack_alerts_handler(
            self.slack_bot_token, self.slack_app_token,
            self.slack_bot_channel_id, self.slack_channel_id,
            self.slack_channel_name)

        handler_display_name = SLACK_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.slack_channel_name)
        mock_init_logger.assert_called_once_with(handler_display_name,
                                                 SlackAlertsHandler.__name__)
        mock_bot_api.assert_called_once_with(
            self.slack_bot_token, self.slack_app_token,
            self.slack_bot_channel_id)
        mock_slack_channel.assert_called_once_with(
            self.slack_channel_name, self.slack_channel_id,
            self.dummy_logger.getChild(SlackChannel.__name__),
            self.slack_bot_api)
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.slack_channel, env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_slack_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_slack_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_sah) -> None:
        mock_init_sah.return_value = self.slack_alerts_handler
        mock_start_handler.return_value = None

        start_slack_alerts_handler(self.slack_bot_token,
                                   self.slack_app_token,
                                   self.slack_bot_channel_id,
                                   self.slack_channel_id,
                                   self.slack_channel_name)

        mock_init_sah.assert_called_once_with(self.slack_bot_token,
                                              self.slack_app_token,
                                              self.slack_bot_channel_id,
                                              self.slack_channel_id,
                                              self.slack_channel_name)
        mock_start_handler.assert_called_once_with(self.slack_alerts_handler)

    @mock.patch("src.channels_manager.handlers.starters.MongoApi")
    @mock.patch("src.channels_manager.handlers.starters.RedisApi")
    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.SlackBotApi")
    @mock.patch("src.channels_manager.handlers.starters.SlackChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters."
                "SlackCommandsHandler")
    @mock.patch("src.channels_manager.handlers.starters."
                "SlackCommandHandlers")
    def test_initialise_slack_commands_handler_creates_SCH_correctly(
            self, mock_command_handlers, mock_commands_handler, mock_rabbit,
            mock_slack_channel, mock_bot_api, mock_init_logger, mock_redis,
            mock_mongo) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_bot_api.return_value = self.slack_bot_api
        mock_slack_channel.return_value = self.slack_channel
        mock_rabbit.side_effect = [self.cmd_handlers_rabbit, self.rabbitmq]
        mock_commands_handler.return_value = self.slack_commands_handler
        mock_commands_handler.__name__ = SlackCommandsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_slack_channel.__name__ = SlackChannel.__name__
        mock_redis.return_value = self.redis
        mock_redis.__name__ = RedisApi.__name__
        mock_mongo.return_value = self.mongo
        mock_mongo.__name__ = MongoApi.__name__
        mock_command_handlers.return_value = self.slack_command_handlers
        mock_command_handlers.__name__ = SlackCommandHandlers.__name__

        _initialise_slack_commands_handler(
            self.slack_bot_token, self.slack_app_token,
            self.slack_bot_channel_id, self.slack_channel_id,
            self.slack_channel_name, self.test_associated_chains)

        handler_display_name = SLACK_COMMANDS_HANDLER_NAME_TEMPLATE.format(
            self.slack_channel_name)
        mock_init_logger.assert_called_once_with(
            handler_display_name, SlackCommandsHandler.__name__)
        mock_bot_api.assert_called_once_with(
            self.slack_bot_token, self.slack_app_token,
            self.slack_bot_channel_id)
        mock_slack_channel.assert_called_once_with(
            self.slack_channel_name, self.slack_channel_id,
            self.dummy_logger.getChild(SlackChannel.__name__),
            self.slack_bot_api)
        actual_rabbit_calls = mock_rabbit.call_args_list
        expected_rabbit_calls = [
            call(logger=self.slack_command_handlers_logger.getChild(
                RabbitMQApi.__name__), host=env.RABBIT_IP),
            call(logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
                 host=env.RABBIT_IP),
        ]
        self.assertEqual(expected_rabbit_calls, actual_rabbit_calls)
        mock_redis.assert_called_once_with(
            logger=self.slack_command_handlers_logger.getChild(
                RedisApi.__name__),
            host=env.REDIS_IP, db=env.REDIS_DB, port=env.REDIS_PORT,
            namespace=env.UNIQUE_ALERTER_IDENTIFIER)
        mock_mongo.assert_called_once_with(
            logger=self.slack_command_handlers_logger.getChild(
                MongoApi.__name__),
            host=REPLICA_SET_HOSTS, db_name=env.DB_NAME, port=env.DB_PORT)
        mock_command_handlers.assert_called_once_with(
            SLACK_COMMAND_HANDLERS_NAME,
            self.slack_command_handlers_logger,
            self.test_associated_chains, self.slack_channel,
            self.cmd_handlers_rabbit, self.redis, self.mongo)
        mock_commands_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.slack_channel, self.slack_command_handlers)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_slack_commands_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_slack_commands_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_sch) -> None:
        mock_init_sch.return_value = self.slack_commands_handler
        mock_start_handler.return_value = None

        start_slack_commands_handler(self.slack_bot_token,
                                     self.slack_bot_token,
                                     self.slack_bot_channel_id,
                                     self.slack_channel_id,
                                     self.slack_channel_name,
                                     self.test_associated_chains)

        mock_init_sch.assert_called_once_with(self.slack_bot_token,
                                              self.slack_bot_token,
                                              self.slack_bot_channel_id,
                                              self.slack_channel_id,
                                              self.slack_channel_name,
                                              self.test_associated_chains)
        mock_start_handler.assert_called_once_with(
            self.slack_commands_handler)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.TwilioApi")
    @mock.patch("src.channels_manager.handlers.starters.TwilioChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.TwilioAlertsHandler")
    def test_initialise_twilio_alerts_handler_creates_TAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_twilio_channel,
            mock_twilio_api, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_twilio_api.return_value = self.twilio_api
        mock_twilio_channel.return_value = self.twilio_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.twilio_alerts_handler
        mock_alerts_handler.__name__ = TwilioAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_twilio_channel.__name__ = TwilioChannel.__name__

        _initialise_twilio_alerts_handler(
            self.account_sid, self.auth_token, self.twilio_channel_id,
            self.twilio_channel_name, self.call_from, self.call_to, self.twiml,
            self.twiml_is_url)

        handler_display_name = TWILIO_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.twilio_channel_name)
        mock_init_logger.assert_called_once_with(handler_display_name,
                                                 TwilioAlertsHandler.__name__)
        mock_twilio_api.assert_called_once_with(self.account_sid,
                                                self.auth_token)
        mock_twilio_channel.assert_called_once_with(
            self.twilio_channel_name, self.twilio_channel_id,
            self.dummy_logger.getChild(TwilioChannel.__name__), self.twilio_api)
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.twilio_channel, self.call_from, self.call_to, self.twiml,
            self.twiml_is_url)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_twilio_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_twilio_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_tah) -> None:
        mock_init_tah.return_value = self.twilio_alerts_handler
        mock_start_handler.return_value = None

        start_twilio_alerts_handler(self.account_sid, self.auth_token,
                                    self.twilio_channel_id,
                                    self.twilio_channel_name, self.call_from,
                                    self.call_to, self.twiml, self.twiml_is_url)

        mock_init_tah.assert_called_once_with(self.account_sid, self.auth_token,
                                              self.twilio_channel_id,
                                              self.twilio_channel_name,
                                              self.call_from, self.call_to,
                                              self.twiml, self.twiml_is_url)
        mock_start_handler.assert_called_once_with(self.twilio_alerts_handler)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.PagerDutyApi")
    @mock.patch("src.channels_manager.handlers.starters.PagerDutyChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.PagerDutyAlertsHandler")
    def test_initialise_pagerduty_alerts_handler_creates_PAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_pagerduty_channel,
            mock_pagerduty_api, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_pagerduty_api.return_value = self.pagerduty_api
        mock_pagerduty_channel.return_value = self.pagerduty_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.pagerduty_alerts_handler
        mock_alerts_handler.__name__ = PagerDutyAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_pagerduty_channel.__name__ = PagerDutyChannel.__name__

        _initialise_pagerduty_alerts_handler(
            self.integration_key, self.pagerduty_channel_id,
            self.pagerduty_channel_name)

        handler_display_name = PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.pagerduty_channel_name)
        mock_init_logger.assert_called_once_with(
            handler_display_name, PagerDutyAlertsHandler.__name__)
        mock_pagerduty_api.assert_called_once_with(self.integration_key)
        mock_pagerduty_channel.assert_called_once_with(
            self.pagerduty_channel_name, self.pagerduty_channel_id,
            self.dummy_logger.getChild(PagerDutyChannel.__name__),
            self.pagerduty_api)
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.pagerduty_channel, env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_pagerduty_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_pagerduty_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_pah) -> None:
        mock_init_pah.return_value = self.pagerduty_alerts_handler
        mock_start_handler.return_value = None

        start_pagerduty_alerts_handler(self.integration_key,
                                       self.pagerduty_channel_id,
                                       self.pagerduty_channel_name)

        mock_init_pah.assert_called_once_with(self.integration_key,
                                              self.pagerduty_channel_id,
                                              self.pagerduty_channel_name)
        mock_start_handler.assert_called_once_with(
            self.pagerduty_alerts_handler)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.EmailApi")
    @mock.patch("src.channels_manager.handlers.starters.EmailChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.EmailAlertsHandler")
    def test_initialise_email_alerts_handler_creates_EAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_email_channel,
            mock_email_api, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_email_api.return_value = self.email_api
        mock_email_channel.return_value = self.email_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.email_alerts_handler
        mock_alerts_handler.__name__ = EmailAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_email_channel.__name__ = EmailChannel.__name__

        _initialise_email_alerts_handler(self.smtp, self.call_from,
                                         self.emails_to, self.email_channel_id,
                                         self.email_channel_name, self.username,
                                         self.password, self.port)

        handler_display_name = EMAIL_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.email_channel_name)
        mock_init_logger.assert_called_once_with(handler_display_name,
                                                 EmailAlertsHandler.__name__)
        mock_email_api.assert_called_once_with(self.smtp, self.call_from,
                                               self.username, self.password,
                                               self.port)
        mock_email_channel.assert_called_once_with(
            self.email_channel_name, self.email_channel_id,
            self.dummy_logger.getChild(EmailChannel.__name__), self.emails_to,
            self.email_api)
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.email_channel, env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_email_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_email_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_eah) -> None:
        mock_init_eah.return_value = self.email_alerts_handler
        mock_start_handler.return_value = None

        start_email_alerts_handler(self.smtp, self.call_from, self.emails_to,
                                   self.email_channel_id,
                                   self.email_channel_name, self.username,
                                   self.password, self.port)

        mock_init_eah.assert_called_once_with(
            self.smtp, self.call_from, self.emails_to, self.email_channel_id,
            self.email_channel_name, self.username, self.password, self.port)
        mock_start_handler.assert_called_once_with(self.email_alerts_handler)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.OpsgenieApi")
    @mock.patch("src.channels_manager.handlers.starters.OpsgenieChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.OpsgenieAlertsHandler")
    def test_initialise_opsgenie_alerts_handler_creates_OAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_opsgenie_channel,
            mock_opsgenie_api, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_opsgenie_api.return_value = self.opsgenie_api
        mock_opsgenie_channel.return_value = self.opsgenie_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.opsgenie_alerts_handler
        mock_alerts_handler.__name__ = OpsgenieAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_opsgenie_channel.__name__ = OpsgenieChannel.__name__

        _initialise_opsgenie_alerts_handler(self.api_key, self.eu_host,
                                            self.opsgenie_channel_id,
                                            self.opsgenie_channel_name)

        handler_display_name = OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.opsgenie_channel_name)
        mock_init_logger.assert_called_once_with(handler_display_name,
                                                 OpsgenieAlertsHandler.__name__)
        mock_opsgenie_api.assert_called_once_with(self.api_key, self.eu_host)
        mock_opsgenie_channel.assert_called_once_with(
            self.opsgenie_channel_name, self.opsgenie_channel_id,
            self.dummy_logger.getChild(OpsgenieChannel.__name__),
            self.opsgenie_api)
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.opsgenie_channel, env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_opsgenie_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_opsgenie_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_oah) -> None:
        mock_init_oah.return_value = self.opsgenie_alerts_handler
        mock_start_handler.return_value = None

        start_opsgenie_alerts_handler(self.api_key, self.eu_host,
                                      self.opsgenie_channel_id,
                                      self.opsgenie_channel_name)

        mock_init_oah.assert_called_once_with(self.api_key, self.eu_host,
                                              self.opsgenie_channel_id,
                                              self.opsgenie_channel_name)
        mock_start_handler.assert_called_once_with(
            self.opsgenie_alerts_handler)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.ConsoleChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.ConsoleAlertsHandler")
    def test_initialise_console_alerts_handler_creates_CAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_console_channel,
            mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_console_channel.return_value = self.console_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.console_alerts_handler
        mock_alerts_handler.__name__ = ConsoleAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_console_channel.__name__ = ConsoleChannel.__name__

        _initialise_console_alerts_handler(self.console_channel_id,
                                           self.console_channel_name)

        handler_display_name = CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.console_channel_name)
        mock_init_logger.assert_called_once_with(handler_display_name,
                                                 ConsoleAlertsHandler.__name__)
        mock_console_channel.assert_called_once_with(
            self.console_channel_name, self.console_channel_id,
            self.dummy_logger.getChild(ConsoleChannel.__name__))
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.console_channel)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_console_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_console_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_cah) -> None:
        mock_init_cah.return_value = self.console_alerts_handler
        mock_start_handler.return_value = None

        start_console_alerts_handler(self.console_channel_id,
                                     self.console_channel_name)

        mock_init_cah.assert_called_once_with(self.console_channel_id,
                                              self.console_channel_name)
        mock_start_handler.assert_called_once_with(self.console_alerts_handler)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_alerts_logger")
    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_channel_handler_logger")
    @mock.patch("src.channels_manager.handlers.starters.LogChannel")
    @mock.patch("src.channels_manager.handlers.starters.RabbitMQApi")
    @mock.patch("src.channels_manager.handlers.starters.LogAlertsHandler")
    def test_initialise_log_alerts_handler_creates_LAH_correctly(
            self, mock_alerts_handler, mock_rabbit, mock_log_channel,
            mock_init_handler_logger, mock_init_alerts_logger) -> None:
        mock_init_handler_logger.return_value = self.dummy_logger
        mock_init_alerts_logger.return_value = self.alerts_logger
        mock_log_channel.return_value = self.log_channel
        mock_rabbit.return_value = self.rabbitmq
        mock_alerts_handler.return_value = self.log_alerts_handler
        mock_alerts_handler.__name__ = LogAlertsHandler.__name__
        mock_rabbit.__name__ = RabbitMQApi.__name__
        mock_log_channel.__name__ = LogChannel.__name__

        _initialise_log_alerts_handler(self.log_channel_id,
                                       self.log_channel_name)

        handler_display_name = LOG_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.log_channel_name)
        mock_init_handler_logger.assert_called_once_with(
            handler_display_name, LogAlertsHandler.__name__)
        mock_init_alerts_logger.assert_called_once_with()
        mock_log_channel.assert_called_once_with(
            self.log_channel_name, self.log_channel_id,
            self.dummy_logger.getChild(LogChannel.__name__), self.alerts_logger)
        mock_rabbit.assert_called_once_with(
            logger=self.dummy_logger.getChild(RabbitMQApi.__name__),
            host=env.RABBIT_IP)
        mock_alerts_handler.assert_called_once_with(
            handler_display_name, self.dummy_logger, self.rabbitmq,
            self.log_channel)

    @mock.patch("src.channels_manager.handlers.starters."
                "_initialise_log_alerts_handler")
    @mock.patch("src.channels_manager.handlers.starters.start_handler")
    def test_start_log_alerts_handler_starts_handler_correctly(
            self, mock_start_handler, mock_init_lah) -> None:
        mock_init_lah.return_value = self.log_alerts_handler
        mock_start_handler.return_value = None

        start_log_alerts_handler(self.log_channel_id, self.log_channel_name)

        mock_init_lah.assert_called_once_with(self.log_channel_id,
                                              self.log_channel_name)
        mock_start_handler.assert_called_once_with(self.log_alerts_handler)
