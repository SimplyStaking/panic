import logging
import sys
from datetime import datetime
from types import FrameType
from typing import Dict, Optional, Any

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel
from slack_bolt import Ack, Say, App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.alerter.alerts.alert import Alert
from src.channels_manager.channels.slack import SlackChannel
from src.channels_manager.commands.handlers.slack_cmd_handlers import (
    SlackCommandHandlers)
from src.channels_manager.handlers.handler import ChannelHandler
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          PING_ROUTING_KEY,
                                          CHAN_CMDS_HAN_HB_QUEUE_NAME_TEMPLATE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          TOPIC)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class SlackCommandsHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi, slack_channel: SlackChannel,
                 cmd_handlers: SlackCommandHandlers,
                 token_verification_enabled: bool = True) -> None:
        super().__init__(handler_name, logger, rabbitmq)

        self._slack_channel = slack_channel
        self._slack_commands_handler_queue = \
            CHAN_CMDS_HAN_HB_QUEUE_NAME_TEMPLATE.format(
                self.slack_channel.channel_id)
        self._cmd_handlers = cmd_handlers
        self._app = App(token=self.slack_channel.slack_bot.bot_token,
                        token_verification_enabled=token_verification_enabled)

        @self.app.command("/start")
        def start_callback(ack: Ack, say: Say,
                           command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.start_callback(ack, say, command)

        @self.app.command("/panicmute")
        def mute_callback(ack: Ack, say: Say,
                          command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.mute_callback(ack, say, command)

        @self.app.command("/unmute")
        def unmute_callback(ack: Ack, say: Say,
                            command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.unmute_callback(ack, say, command)

        @self.app.command("/muteall")
        def muteall_callback(ack: Ack, say: Say,
                             command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.muteall_callback(ack, say, command)

        @self.app.command("/unmuteall")
        def unmuteall_callback(ack: Ack, say: Say,
                               command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.unmuteall_callback(ack, say, command)

        @self.app.command("/panicstatus")
        def status_callback(ack: Ack, say: Say,
                            command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.status_callback(ack, say, command)

        @self.app.command("/ping")
        def ping_callback(ack: Ack, say: Say,
                          command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.ping_callback(ack, say, command)

        @self.app.command("/help")
        def help_callback(ack: Ack, say: Say,
                          command: Optional[Dict[str, Any]]) -> None:
            self.cmd_handlers.help_callback(ack, say, command)

        # This is used to ignore other events (messages)
        # since they are not currently required.
        @self.app.event("message")
        def invalid_callback():
            pass

        # Set up socket handler
        self._socket_handler = SocketModeHandler(self.app,
                                                 self.slack_channel.slack_bot.
                                                 app_token)
        self._socket_handler_started = False

    @property
    def cmd_handlers(self) -> SlackCommandHandlers:
        return self._cmd_handlers

    @property
    def slack_channel(self) -> SlackChannel:
        return self._slack_channel

    @property
    def app(self) -> App:
        return self._app

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         self._slack_commands_handler_queue)
        self.rabbitmq.queue_declare(self._slack_commands_handler_queue,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", self._slack_commands_handler_queue,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(self._slack_commands_handler_queue,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          self._slack_commands_handler_queue)
        self.rabbitmq.basic_consume(self._slack_commands_handler_queue,
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

    def _start_handling(self) -> None:
        if not self._socket_handler_started:
            self.logger.info("Started handling commands.")
            self._socket_handler.start()
            self._socket_handler_started = True

    def _stop_handling(self) -> None:
        self._socket_handler.close()
        self._socket_handler_started = False
        self.logger.info("Stopped handling commands.")

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.debug("Received %s", data)

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.handler_name
            heartbeat['is_alive'] = self._socket_handler_started
            heartbeat['timestamp'] = datetime.now().timestamp()

            # If socket handler is not running, try to restart it.
            if not self._socket_handler_started:
                self._start_handling()
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
                self._start_handling()
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
        rabbit, the slack commands handler only sends heartbeats.
        """
        pass
