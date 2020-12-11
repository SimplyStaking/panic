import logging
import time

import pika.exceptions

from src.channels_manager.apis.telegram_bot_api import TelegramBotApi
from src.channels_manager.channels.telegram import TelegramChannel
from src.channels_manager.handlers.handler import ChannelHandler
from src.channels_manager.handlers.telegram.alerts import TelegramAlertsHandler
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


def _initialize_telegram_alerts_handler(bot_token: str, bot_chat_id: str,
                                        channel_id: str) \
        -> TelegramAlertsHandler:
    # Handler name based on channel id
    handler_name = "Telegram Alerts Handler ({})".format(channel_id)
    handler_logger = _initialize_channel_handler_logger(handler_name)

    # Try initializing handler until successful
    while True:
        try:
            telegram_bot = TelegramBotApi(bot_token, bot_chat_id)

            # Channel name based on channel id
            channel_name = 'Telegram Channel ({})'.format(channel_id)
            telegram_channel = TelegramChannel(channel_name, channel_id,
                                               handler_logger, telegram_bot)

            telegram_alerts_handler = TelegramAlertsHandler(
                handler_name, handler_logger, telegram_channel)
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
                                  channel_id: str) -> None:
    telegram_alerts_handler = _initialize_telegram_alerts_handler(
        bot_token, bot_chat_id, channel_id)
    start_handler(telegram_alerts_handler)


# TODO: Continue doing this for every handler

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
