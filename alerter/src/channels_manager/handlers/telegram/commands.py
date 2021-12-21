import logging
import sys
from datetime import datetime
from types import FrameType
from typing import Dict

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater

from src.alerter.alerts.alert import Alert
from src.channels_manager.channels.telegram import TelegramChannel
from src.channels_manager.commands.handlers.telegram_cmd_handlers import (
    TelegramCommandHandlers)
from src.channels_manager.handlers.handler import ChannelHandler
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          PING_ROUTING_KEY,
                                          CHAN_CMDS_HAN_HB_QUEUE_NAME_TEMPLATE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          TOPIC)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class TelegramCommandsHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi, telegram_channel: TelegramChannel,
                 cmd_handlers: TelegramCommandHandlers) -> None:
        super().__init__(handler_name, logger, rabbitmq)

        self._telegram_channel = telegram_channel
        self._telegram_commands_handler_queue = \
            CHAN_CMDS_HAN_HB_QUEUE_NAME_TEMPLATE.format(
                self.telegram_channel.channel_id)
        self._cmd_handlers = cmd_handlers

        command_specific_handlers = [
            CommandHandler('start', self.cmd_handlers.start_callback),
            CommandHandler('mute', self.cmd_handlers.mute_callback),
            CommandHandler('unmute', self.cmd_handlers.unmute_callback),
            CommandHandler('muteall', self.cmd_handlers.muteall_callback),
            CommandHandler('unmuteall', self.cmd_handlers.unmuteall_callback),
            CommandHandler('status', self.cmd_handlers.status_callback),
            CommandHandler('ping', self.cmd_handlers.ping_callback),
            CommandHandler('help', self.cmd_handlers.help_callback),
            MessageHandler(Filters.command, self.cmd_handlers.unknown_callback)
        ]

        # Set up updater
        self._updater = Updater(token=telegram_channel.telegram_bot.bot_token,
                                use_context=True)

        for handler in command_specific_handlers:
            self._updater.dispatcher.add_handler(handler)

    @property
    def cmd_handlers(self) -> TelegramCommandHandlers:
        return self._cmd_handlers

    @property
    def telegram_channel(self) -> TelegramChannel:
        return self._telegram_channel

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         self._telegram_commands_handler_queue)
        self.rabbitmq.queue_declare(self._telegram_commands_handler_queue,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", self._telegram_commands_handler_queue,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(self._telegram_commands_handler_queue,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          self._telegram_commands_handler_queue)
        self.rabbitmq.basic_consume(self._telegram_commands_handler_queue,
                                    self._process_ping, True, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _send_heartbeat(self, data_to_send: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent heartbeat to %s exchange",
                          HEALTH_CHECK_EXCHANGE)

    def _start_handling(self, run_in_background: bool = False) -> None:
        # Start polling
        if not self._updater.running:
            self.logger.info("Started handling commands.")
            self._updater.start_polling(drop_pending_updates=True)

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        if not run_in_background:
            self._updater.idle(stop_signals=[])

    def _stop_handling(self) -> None:
        # This is useful only when the Updater is set to run in background
        self._updater.stop()
        self.logger.info("Stopped handling commands.")

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.debug("Received %s", data)

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.handler_name
            heartbeat['is_alive'] = self._updater.running
            heartbeat['timestamp'] = datetime.now().timestamp()

            # If updater is not running, try to restart it.
            if not self._updater.running:
                self._start_handling(run_in_background=True)
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing %s", data)
            self.logger.exception(e)
            return

        # Send heartbeat if processing was successful
        try:
            self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as there is no use in
            # re-trying to send a heartbeat
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it.
            raise e

    def start(self) -> None:
        self._initialise_rabbitmq()
        while True:
            try:
                self._start_handling(run_in_background=True)
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings.
                raise e
            except Exception as e:
                self.logger.exception(e)
                self._stop_handling()
                raise e

    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will "
                      "exit.".format(self), self.logger)
        self.disconnect_from_rabbit()
        self.cmd_handlers.rabbitmq.disconnect_till_successful()
        self._stop_handling()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _send_data(self, alert: Alert) -> None:
        """
        We are not implementing the _send_data function because with respect to
        rabbit, the telegram commands handler only sends heartbeats.
        """
        pass
