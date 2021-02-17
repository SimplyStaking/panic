import logging
import time
from typing import List, Dict, Optional

import pika.exceptions

from src.channels_manager.apis.email_api import EmailApi
from src.channels_manager.apis.opsgenie_api import OpsgenieApi
from src.channels_manager.apis.pagerduty_api import PagerDutyApi
from src.channels_manager.apis.telegram_bot_api import TelegramBotApi
from src.channels_manager.apis.twilio_api import TwilioApi
from src.channels_manager.channels import PagerDutyChannel
from src.channels_manager.channels.console import ConsoleChannel
from src.channels_manager.channels.email import EmailChannel
from src.channels_manager.channels.log import LogChannel
from src.channels_manager.channels.opsgenie import OpsgenieChannel
from src.channels_manager.channels.telegram import TelegramChannel
from src.channels_manager.channels.twilio import TwilioChannel
from src.channels_manager.handlers import EmailAlertsHandler
from src.channels_manager.handlers.console.alerts import ConsoleAlertsHandler
from src.channels_manager.handlers.handler import ChannelHandler
from src.channels_manager.handlers.log.alerts import LogAlertsHandler
from src.channels_manager.handlers.opsgenie.alerts import OpsgenieAlertsHandler
from src.channels_manager.handlers.pager_duty.alerts import \
    PagerDutyAlertsHandler
from src.channels_manager.handlers.telegram.alerts import TelegramAlertsHandler
from src.channels_manager.handlers.telegram.commands import \
    TelegramCommandsHandler
from src.channels_manager.handlers.twilio.alerts import TwilioAlertsHandler
from src.utils import env
from src.utils.constants import (RE_INITIALISE_SLEEPING_PERIOD,
                                 RESTART_SLEEPING_PERIOD,
                                 TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE,
                                 TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE,
                                 TWILIO_ALERTS_HANDLER_NAME_TEMPLATE,
                                 PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE,
                                 EMAIL_ALERTS_HANDLER_NAME_TEMPLATE,
                                 OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE,
                                 CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE,
                                 LOG_ALERTS_HANDLER_NAME_TEMPLATE)
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import (get_initialisation_error_message,
                                get_stopped_message)


def _initialise_channel_handler_logger(
        handler_display_name: str, handler_module_name: str) -> logging.Logger:
    # Try initialising the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            handler_logger = create_logger(
                env.CHANNEL_HANDLERS_LOG_FILE_TEMPLATE.format(
                    handler_display_name), handler_module_name,
                env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # handlers's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return handler_logger


def _initialise_alerts_logger() -> logging.Logger:
    # Try initialising the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            alerts_logger = create_logger(env.ALERTS_LOG_FILE, 'Alerts',
                                          env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = get_initialisation_error_message('Alerts Log File', e)
            # Use a dummy logger in this case because we cannot create the
            # logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return alerts_logger


def _initialise_telegram_alerts_handler(bot_token: str, bot_chat_id: str,
                                        channel_id: str, channel_name: str) \
        -> TelegramAlertsHandler:
    # Handler display name based on channel name
    handler_display_name = TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE.format(
        channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, TelegramAlertsHandler.__name__)

    # Try initialising handler until successful
    while True:
        try:
            telegram_bot = TelegramBotApi(bot_token, bot_chat_id)

            telegram_channel = TelegramChannel(
                channel_name, channel_id, handler_logger.getChild(
                    TelegramChannel.__name__), telegram_bot)

            rabbit_ip = env.RABBIT_IP
            queue_size = env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE
            telegram_alerts_handler = TelegramAlertsHandler(
                handler_display_name, handler_logger, rabbit_ip, queue_size,
                telegram_channel)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return telegram_alerts_handler


def start_telegram_alerts_handler(bot_token: str, bot_chat_id: str,
                                  channel_id: str, channel_name: str) -> None:
    telegram_alerts_handler = _initialise_telegram_alerts_handler(
        bot_token, bot_chat_id, channel_id, channel_name)
    start_handler(telegram_alerts_handler)


def _initialise_telegram_commands_handler(
        bot_token: str, bot_chat_id: str, channel_id: str, channel_name: str,
        associated_chains: Dict) -> TelegramCommandsHandler:
    # Handler display name based on channel name
    handler_display_name = TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE.format(
        channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, TelegramCommandsHandler.__name__)

    # Try initialising handler until successful
    while True:
        try:
            telegram_bot = TelegramBotApi(bot_token, bot_chat_id)

            telegram_channel = TelegramChannel(
                channel_name, channel_id, handler_logger.getChild(
                    TelegramChannel.__name__), telegram_bot)

            telegram_commands_handler = TelegramCommandsHandler(
                handler_display_name, handler_logger, env.RABBIT_IP,
                env.REDIS_IP, env.REDIS_DB, env.REDIS_PORT,
                env.UNIQUE_ALERTER_IDENTIFIER, env.DB_IP, env.DB_NAME,
                env.DB_PORT, associated_chains, telegram_channel)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return telegram_commands_handler


def start_telegram_commands_handler(
        bot_token: str, bot_chat_id: str, channel_id: str, channel_name: str,
        associated_chains: Dict) -> None:
    telegram_commands_handler = _initialise_telegram_commands_handler(
        bot_token, bot_chat_id, channel_id, channel_name, associated_chains)
    start_handler(telegram_commands_handler)


def _initialise_twilio_alerts_handler(
        account_sid: str, auth_token: str, channel_id: str, channel_name: str,
        call_from: str, call_to: List[str], twiml: str, twiml_is_url: bool) \
        -> TwilioAlertsHandler:
    # Handler display name based on channel name
    handler_display_name = TWILIO_ALERTS_HANDLER_NAME_TEMPLATE.format(
        channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, TwilioAlertsHandler.__name__)

    # Try initialising handler until successful
    while True:
        try:
            twilio_api = TwilioApi(account_sid, auth_token)

            twilio_channel = TwilioChannel(
                channel_name, channel_id, handler_logger.getChild(
                    TwilioChannel.__name__), twilio_api)

            twilio_alerts_handler = TwilioAlertsHandler(
                handler_display_name, handler_logger, env.RABBIT_IP,
                twilio_channel, call_from, call_to, twiml, twiml_is_url)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return twilio_alerts_handler


def start_twilio_alerts_handler(
        account_sid: str, auth_token: str, channel_id: str, channel_name: str,
        call_from: str, call_to: List[str], twiml: str, twiml_is_url: bool) \
        -> None:
    twilio_alerts_handler = _initialise_twilio_alerts_handler(
        account_sid, auth_token, channel_id, channel_name, call_from, call_to,
        twiml, twiml_is_url)
    start_handler(twilio_alerts_handler)


def _initialise_pagerduty_alerts_handler(integration_key: str, channel_id: str,
                                         channel_name: str) \
        -> PagerDutyAlertsHandler:
    # Handler display name based on channel name
    handler_display_name = PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE.format(
        channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, PagerDutyAlertsHandler.__name__)

    # Try initialising handler until successful
    while True:
        try:
            pagerduty_api = PagerDutyApi(integration_key)
            pagerduty_channel = PagerDutyChannel(
                channel_name, channel_id, handler_logger.getChild(
                    PagerDutyChannel.__name__), pagerduty_api)

            pagerduty_alerts_handler = PagerDutyAlertsHandler(
                handler_display_name, handler_logger, env.RABBIT_IP,
                env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE, pagerduty_channel)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return pagerduty_alerts_handler


def start_pagerduty_alerts_handler(integration_key: str, channel_id: str,
                                   channel_name: str) -> None:
    pagerduty_alerts_handler = _initialise_pagerduty_alerts_handler(
        integration_key, channel_id, channel_name)
    start_handler(pagerduty_alerts_handler)


def _initialise_email_alerts_handler(
        smtp: str, email_from: str, emails_to: List[str],
        channel_id: str, channel_name: str, username: Optional[str],
        password: Optional[str]) -> EmailAlertsHandler:
    # Handler display name based on channel name
    handler_display_name = EMAIL_ALERTS_HANDLER_NAME_TEMPLATE.format(
        channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, EmailAlertsHandler.__name__)

    # Try initialising handler until successful
    while True:
        try:
            email_api = EmailApi(smtp, email_from, username, password)
            email_channel = EmailChannel(
                channel_name, channel_id, handler_logger.getChild(
                    EmailChannel.__name__), emails_to, email_api)

            email_alerts_handler = EmailAlertsHandler(
                handler_display_name, handler_logger, env.RABBIT_IP,
                env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE, email_channel)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return email_alerts_handler


def start_email_alerts_handler(
        smtp: str, email_from: str, emails_to: List[str], channel_id: str,
        channel_name: str, username: Optional[str],
        password: Optional[str]) -> None:
    email_alerts_handler = _initialise_email_alerts_handler(
        smtp, email_from, emails_to, channel_id, channel_name, username,
        password)
    start_handler(email_alerts_handler)


def _initialise_opsgenie_alerts_handler(api_key: str, eu_host: bool,
                                        channel_id: str, channel_name: str) \
        -> OpsgenieAlertsHandler:
    # Handler display name based on channel name
    handler_display_name = OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE.format(
        channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, OpsgenieAlertsHandler.__name__)

    # Try initialising handler until successful
    while True:
        try:
            opsgenie_api = OpsgenieApi(api_key, eu_host)

            opsgenie_channel = OpsgenieChannel(
                channel_name, channel_id, handler_logger.getChild(
                    OpsgenieChannel.__name__), opsgenie_api)

            opsgenie_alerts_handler = OpsgenieAlertsHandler(
                handler_display_name, handler_logger, env.RABBIT_IP,
                env.CHANNELS_MANAGER_PUBLISHING_QUEUE_SIZE, opsgenie_channel)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return opsgenie_alerts_handler


def start_opsgenie_alerts_handler(api_key: str, eu_host: bool, channel_id: str,
                                  channel_name: str) -> None:
    opsgenie_alerts_handler = _initialise_opsgenie_alerts_handler(
        api_key, eu_host, channel_id, channel_name)
    start_handler(opsgenie_alerts_handler)


def _initialise_console_alerts_handler(channel_id: str, channel_name: str) \
        -> ConsoleAlertsHandler:
    # Handler display name based on channel name
    handler_display_name = CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE.format(
        channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, ConsoleAlertsHandler.__name__)

    # Try initialising handler until successful
    while True:
        try:
            console_channel = ConsoleChannel(
                channel_name, channel_id,
                handler_logger.getChild(ConsoleChannel.__name__))

            console_alerts_handler = ConsoleAlertsHandler(
                handler_display_name, handler_logger, env.RABBIT_IP,
                console_channel)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return console_alerts_handler


def start_console_alerts_handler(channel_id: str, channel_name: str) -> None:
    console_alerts_handler = _initialise_console_alerts_handler(channel_id,
                                                                channel_name)
    start_handler(console_alerts_handler)


def _initialise_log_alerts_handler(channel_id: str, channel_name: str) \
        -> LogAlertsHandler:
    # Handler display name based on channel name
    handler_display_name = LOG_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
    handler_logger = _initialise_channel_handler_logger(
        handler_display_name, LogAlertsHandler.__name__)
    alerts_logger = _initialise_alerts_logger()

    # Try initialising handler until successful
    while True:
        try:
            log_channel = LogChannel(
                channel_name, channel_id,
                handler_logger.getChild(LogChannel.__name__), alerts_logger)

            log_alerts_handler = LogAlertsHandler(
                handler_display_name, handler_logger, env.RABBIT_IP,
                log_channel)
            log_and_print("Successfully initialised {}".format(
                handler_display_name), handler_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(handler_display_name, e)
            log_and_print(msg, handler_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return log_alerts_handler


def start_log_alerts_handler(channel_id: str, channel_name: str) -> None:
    log_alerts_handler = _initialise_log_alerts_handler(channel_id,
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
            log_and_print(get_stopped_message(handler), handler.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            handler.disconnect_from_rabbit()
            log_and_print(get_stopped_message(handler), handler.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                handler, RESTART_SLEEPING_PERIOD), handler.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)
