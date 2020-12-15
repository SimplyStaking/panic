import logging
import time
from typing import List, Dict, Optional

import pika.exceptions

from src.channels_manager.apis.telegram_bot_api import TelegramBotApi
from src.channels_manager.apis.twilio_api import TwilioApi
from src.channels_manager.channels import PagerDutyChannel
from src.channels_manager.channels.console import ConsoleChannel
from src.channels_manager.channels.email import EmailChannel
from src.channels_manager.channels.log import LogChannel
from src.channels_manager.channels.telegram import TelegramChannel
from src.channels_manager.channels.twilio import TwilioChannel
from src.channels_manager.handlers import EmailAlertsHandler
from src.channels_manager.handlers.console.alerts import ConsoleAlertsHandler
from src.channels_manager.handlers.handler import ChannelHandler
from src.channels_manager.handlers.log.alerts import LogAlertsHandler
from src.channels_manager.handlers.pager_duty.alerts import \
    PagerDutyAlertsHandler
from src.channels_manager.handlers.telegram.alerts import TelegramAlertsHandler
from src.channels_manager.handlers.telegram.commands import \
    TelegramCommandsHandler
from src.channels_manager.handlers.twilio.alerts import TwilioAlertsHandler
from src.utils import env
from src.utils.logging import create_logger, log_and_print


def _initialize_channel_handler_logger(handler_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            handler_logger = create_logger(
                env.CHANNEL_HANDLERS_LOG_FILE_TEMPLATE.format(handler_name),
                handler_name, env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(handler_name,
                                                                  e)
            # Use a dummy logger in this case because we cannot create the
            # handlers's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return handler_logger


def _initialize_alerts_logger() -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            alerts_logger = create_logger(env.ALERTS_LOG_FILE, 'alerts',
                                          env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = "!!! Error when initialising Alerts Log File: {} " \
                  "!!!".format(e)
            # Use a dummy logger in this case because we cannot create the
            # logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return alerts_logger


def _initialize_telegram_alerts_handler(bot_token: str, bot_chat_id: str,
                                        channel_id: str, channel_name: str) \
        -> TelegramAlertsHandler:
    # Handler name based on channel name
    handler_name = "Telegram Alerts Handler ({})".format(channel_name)
    handler_logger = _initialize_channel_handler_logger(handler_name)

    # Try initializing handler until successful
    while True:
        try:
            telegram_bot = TelegramBotApi(bot_token, bot_chat_id)

            telegram_channel = TelegramChannel(channel_name, channel_id,
                                               handler_logger, telegram_bot)

            rabbit_ip = env.RABBIT_IP
            queue_size = env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE
            telegram_alerts_handler = TelegramAlertsHandler(
                handler_name, handler_logger, rabbit_ip, queue_size,
                telegram_channel)
            log_and_print("Successfully initialized {}".format(handler_name),
                          handler_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                handler_name, e)
            log_and_print(msg, handler_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return telegram_alerts_handler


def start_telegram_alerts_handler(bot_token: str, bot_chat_id: str,
                                  channel_id: str, channel_name: str) -> None:
    telegram_alerts_handler = _initialize_telegram_alerts_handler(
        bot_token, bot_chat_id, channel_id, channel_name)
    start_handler(telegram_alerts_handler)


def _initialize_telegram_commands_handler(
        bot_token: str, bot_chat_id: str, channel_id: str, channel_name: str,
        associated_chains: Dict) -> TelegramCommandsHandler:
    # Handler name based on channel name
    handler_name = "Telegram Commands Handler ({})".format(channel_name)
    handler_logger = _initialize_channel_handler_logger(handler_name)

    # Try initializing handler until successful
    while True:
        try:
            telegram_bot = TelegramBotApi(bot_token, bot_chat_id)

            telegram_channel = TelegramChannel(channel_name, channel_id,
                                               handler_logger, telegram_bot)

            telegram_commands_handler = TelegramCommandsHandler(
                handler_name, handler_logger, env.RABBIT_IP, env.REDIS_IP,
                env.REDIS_DB, env.REDIS_PORT, env.UNIQUE_ALERTER_IDENTIFIER,
                env.DB_IP, env.DB_NAME, env.DB_PORT, associated_chains,
                telegram_channel)
            log_and_print("Successfully initialized {}".format(handler_name),
                          handler_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                handler_name, e)
            log_and_print(msg, handler_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return telegram_commands_handler


def start_telegram_commands_handler(
        bot_token: str, bot_chat_id: str, channel_id: str, channel_name: str,
        associated_chains: Dict) -> None:
    telegram_commands_handler = _initialize_telegram_commands_handler(
        bot_token, bot_chat_id, channel_id, channel_name, associated_chains)
    start_handler(telegram_commands_handler)


def _initialize_twilio_alerts_handler(
        account_sid: str, auth_token: str, channel_id: str, channel_name: str,
        call_from: str, call_to: List[str], twiml: str, twiml_is_url: bool) \
        -> TwilioAlertsHandler:
    # Handler name based on channel name
    handler_name = "Twilio Alerts Handler ({})".format(channel_name)
    handler_logger = _initialize_channel_handler_logger(handler_name)

    # Try initializing handler until successful
    while True:
        try:
            twilio_api = TwilioApi(account_sid, auth_token)

            twilio_channel = TwilioChannel(channel_name, channel_id,
                                           handler_logger, twilio_api)

            twilio_alerts_handler = TwilioAlertsHandler(
                handler_name, handler_logger, env.RABBIT_IP, twilio_channel,
                call_from, call_to, twiml, twiml_is_url)
            log_and_print("Successfully initialized {}".format(handler_name),
                          handler_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                handler_name, e)
            log_and_print(msg, handler_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return twilio_alerts_handler


def start_twilio_alerts_handler(
        account_sid: str, auth_token: str, channel_id: str, channel_name: str,
        call_from: str, call_to: List[str], twiml: str, twiml_is_url: bool) \
        -> None:
    twilio_alerts_handler = _initialize_twilio_alerts_handler(
        account_sid, auth_token, channel_id, channel_name, call_from, call_to,
        twiml, twiml_is_url)
    start_handler(twilio_alerts_handler)


def _initialize_pagerduty_alerts_handler(integration_key: str, channel_id: str,
                                         channel_name: str) \
        -> PagerDutyAlertsHandler:
    # Handler name based on channel name
    handler_name = "PagerDuty Alerts Handler ({})".format(channel_name)
    handler_logger = _initialize_channel_handler_logger(handler_name)

    # Try initializing handler until successful
    while True:
        try:
            pagerduty_channel = PagerDutyChannel(
                channel_name, channel_id, handler_logger, integration_key)

            pagerduty_alerts_handler = PagerDutyAlertsHandler(
                handler_name, handler_logger, env.RABBIT_IP,
                env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE, pagerduty_channel)
            log_and_print("Successfully initialized {}".format(handler_name),
                          handler_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                handler_name, e)
            log_and_print(msg, handler_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return pagerduty_alerts_handler


def start_pagerduty_alerts_handler(integration_key: str, channel_id: str,
                                   channel_name: str) -> None:
    pagerduty_alerts_handler = _initialize_pagerduty_alerts_handler(
        integration_key, channel_id, channel_name)
    start_handler(pagerduty_alerts_handler)


def _initialize_email_alerts_handler(
        smtp: str, email_from: str, emails_to: List[str],
        channel_id: str, channel_name: str, username: Optional[str],
        password: Optional[str]) -> EmailAlertsHandler:
    # Handler name based on channel name
    handler_name = "Email Alerts Handler ({})".format(channel_name)
    handler_logger = _initialize_channel_handler_logger(handler_name)

    # Try initializing handler until successful
    while True:
        try:
            email_channel = EmailChannel(
                channel_name, channel_id, handler_logger, smtp, email_from,
                emails_to, username, password)

            email_alerts_handler = EmailAlertsHandler(
                handler_name, handler_logger, env.RABBIT_IP,
                env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE, email_channel)
            log_and_print("Successfully initialized {}".format(handler_name),
                          handler_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                handler_name, e)
            log_and_print(msg, handler_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return email_alerts_handler


def start_email_alerts_handler(
        smtp: str, email_from: str, emails_to: List[str], channel_id: str,
        channel_name: str, username: Optional[str],
        password: Optional[str]) -> None:
    email_alerts_handler = _initialize_email_alerts_handler(
        smtp, email_from, emails_to, channel_id, channel_name, username,
        password)
    start_handler(email_alerts_handler)


def _initialize_console_alerts_handler(channel_id: str, channel_name: str) \
        -> ConsoleAlertsHandler:
    # Handler name based on channel name
    handler_name = "Console Alerts Handler ({})".format(channel_name)
    handler_logger = _initialize_channel_handler_logger(handler_name)

    # Try initializing handler until successful
    while True:
        try:
            console_channel = ConsoleChannel(channel_name, channel_id,
                                             handler_logger)

            console_alerts_handler = ConsoleAlertsHandler(
                handler_name, handler_logger, env.RABBIT_IP, console_channel)
            log_and_print("Successfully initialized {}".format(handler_name),
                          handler_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                handler_name, e)
            log_and_print(msg, handler_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return console_alerts_handler


def start_console_alerts_handler(channel_id: str, channel_name: str) -> None:
    console_alerts_handler = _initialize_console_alerts_handler(channel_id,
                                                                channel_name)
    start_handler(console_alerts_handler)


def _initialize_log_alerts_handler(channel_id: str, channel_name: str) \
        -> LogAlertsHandler:
    # Handler name based on channel name
    handler_name = "Log Alerts Handler ({})".format(channel_name)
    handler_logger = _initialize_channel_handler_logger(handler_name)
    alerts_logger = _initialize_alerts_logger()

    # Try initializing handler until successful
    while True:
        try:
            log_channel = LogChannel(channel_name, channel_id, handler_logger,
                                     alerts_logger)

            log_alerts_handler = LogAlertsHandler(handler_name, handler_logger,
                                                  env.RABBIT_IP, log_channel)
            log_and_print("Successfully initialized {}".format(handler_name),
                          handler_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                handler_name, e)
            log_and_print(msg, handler_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return log_alerts_handler


def start_log_alerts_handler(channel_id: str, channel_name: str) -> None:
    log_alerts_handler = _initialize_log_alerts_handler(channel_id,
                                                        channel_name)
    start_handler(log_alerts_handler)


def start_handler(handler: ChannelHandler) -> None:
    while True:
        try:
            log_and_print("{} started.".format(handler), handler.logger)
            handler.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print("{} stopped.".format(handler), handler.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            handler.rabbitmq.disconnect_till_successful()
            log_and_print("{} stopped.".format(handler), handler.logger)
