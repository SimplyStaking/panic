import fnmatch
import logging
import os
import sys
import time
from configparser import (ConfigParser, DuplicateSectionError,
                          DuplicateOptionError, InterpolationError,
                          ParsingError)
from datetime import datetime
from types import FrameType
from typing import Any, Dict, List, Optional, Callable

import pika
from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPChannelError, AMQPConnectionError
from watchdog.events import FileSystemEvent
from watchdog.observers.polling import PollingObserver

from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 RE_INITIALIZE_SLEEPING_PERIOD)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  ConnectionNotInitializedException)
from src.utils import routing_key
from .config_update_event_handler import ConfigFileEventHandler
from ..abstract import PublisherComponent
from ..utils.logging import log_and_print

_FIRST_RUN_EVENT = 'first run'
_HEARTBEAT_ROUTING_KEY = 'heartbeat.worker'
CONFIG_PING_QUEUE = "config_ping_queue"


class ConfigsManager(PublisherComponent):
    """
    This class reads all configurations and sends them over to the "config"
    topic in Rabbit MQ. Updated configs are sent as well
    """

    def __init__(self, name: str, logger: logging.Logger, config_directory: str,
                 rabbit_ip: str, file_patterns: Optional[List[str]] = None,
                 ignore_file_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True, case_sensitive: bool = False):
        """
        Constructs the ConfigsManager instance
        :param config_directory: The ro99 ot config directory to watch.
            This is searched recursively.
        :param file_patterns: The file patterns in the directory to watch.
            Defaults to all ini files
        :param ignore_file_patterns: Any file patterns to ignore.
            Defaults to None
        :param ignore_directories: Whether changes in directories should be
            ignored. Default: True
        :param case_sensitive: Whether the patterns in `file_patterns` and
            `ignore_file_patterns` are case sensitive. Defaults to False
        """
        if not file_patterns:
            file_patterns = ['*.ini']

        self._name = name
        self._config_directory = config_directory
        self._file_patterns = file_patterns
        self._watching = False
        self._connected_to_rabbit = False

        logger.debug("Creating config RabbitMQ connection")
        self._config_rabbit = RabbitMQApi(
            logger.getChild("config_{}".format(RabbitMQApi.__name__)),
            host=rabbit_ip)

        super().__init__(logger, self._config_rabbit)

        self._logger.debug("Creating heartbeat RabbitMQ connection")
        self._heartbeat_rabbit = RabbitMQApi(
            logger.getChild("heartbeat_{}".format(RabbitMQApi.__name__)),
            host=rabbit_ip)

        self._event_handler = ConfigFileEventHandler(
            self._logger.getChild(ConfigFileEventHandler.__name__),
            self._on_event_thrown,
            file_patterns,
            ignore_file_patterns,
            ignore_directories,
            case_sensitive
        )
        self._observer = PollingObserver()
        self._observer.schedule(self._event_handler, config_directory,
                                recursive=True)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    def _initialise_rabbitmq(self) -> None:
        while True:
            try:
                self._connect_to_rabbit()
                self._logger.info("Connected to Rabbit")
                self._config_rabbit.confirm_delivery()
                self._logger.info("Enabled delivery confirmation on configs"
                                  "RabbitMQ channel")

                self._config_rabbit.exchange_declare(
                    CONFIG_EXCHANGE, 'topic', False, True, False, False
                )
                self._logger.info("Declared %s exchange in Rabbit",
                                  CONFIG_EXCHANGE)

                self._heartbeat_rabbit.confirm_delivery()
                self._logger.info("Enabled delivery confirmation on heartbeat"
                                  "RabbitMQ channel")

                self._heartbeat_rabbit.exchange_declare(
                    HEALTH_CHECK_EXCHANGE, 'topic', False, True, False, False
                )
                self._logger.info("Declared %s exchange in Rabbit",
                                  HEALTH_CHECK_EXCHANGE)

                self._logger.info(
                    "Creating and binding queue '%s' to exchange '%s' with "
                    "routing key '%s", CONFIG_PING_QUEUE, HEALTH_CHECK_EXCHANGE,
                    _HEARTBEAT_ROUTING_KEY)

                self._heartbeat_rabbit.queue_declare(CONFIG_PING_QUEUE, False,
                                                     True, False, False)
                self._logger.debug("Declared '%s' queue", CONFIG_PING_QUEUE)

                self._heartbeat_rabbit.queue_bind(CONFIG_PING_QUEUE,
                                                  HEALTH_CHECK_EXCHANGE,
                                                  'ping')
                self._logger.debug("Bound queue '%s' to exchange '%s'",
                                   CONFIG_PING_QUEUE, HEALTH_CHECK_EXCHANGE)

                # Pre-fetch count is set to 300
                prefetch_count = round(300)
                self._heartbeat_rabbit.basic_qos(prefetch_count=prefetch_count)
                self._logger.debug("Declaring consuming intentions")
                self._heartbeat_rabbit.basic_consume(CONFIG_PING_QUEUE,
                                                     self._process_ping,
                                                     True, False, None)
                break
            except (ConnectionNotInitializedException,
                    AMQPConnectionError) as connection_error:
                # Should be impossible, but since exchange_declare can throw
                # it we shall ensure to log that the error passed through here
                # too.
                self._logger.error(
                    "Something went wrong that meant a connection was not made")
                self._logger.error(connection_error.message)
                raise connection_error
            except AMQPChannelError:
                # This error would have already been logged by the RabbitMQ
                # logger and handled by RabbitMQ. As a result we don't need to
                # anything here, just re-try.
                time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    def _connect_to_rabbit(self) -> None:
        if not self._connected_to_rabbit:
            self._logger.info("Connecting to the config RabbitMQ")
            self._config_rabbit.connect_till_successful()
            self._logger.info("Connected to config RabbitMQ")
            self._logger.info("Connecting to the heartbeat RabbitMQ")
            self._heartbeat_rabbit.connect_till_successful()
            self._logger.info("Connected to heartbeat RabbitMQ")
            self._connected_to_rabbit = True
        else:
            self._logger.info(
                "Already connected to RabbitMQ, will not connect again")

    def disconnect_from_rabbit(self) -> None:
        if self._connected_to_rabbit:
            self._logger.info("Disconnecting from the config RabbitMQ")
            self._config_rabbit.disconnect_till_successful()
            self._logger.info("Disconnected from the config RabbitMQ")
            self._logger.info("Disconnecting from the heartbeat RabbitMQ")
            self._heartbeat_rabbit.disconnect_till_successful()
            self._logger.info("Disconnected from the heartbeat RabbitMQ")
            self._connected_to_rabbit = False
        else:
            self._logger.info("Already disconnected from RabbitMQ")

    def _send_heartbeat(self, data_to_send: dict) -> None:
        self._logger.debug("Sending heartbeat to the %s exchange",
                           HEALTH_CHECK_EXCHANGE)
        self._logger.debug("Sending %s", data_to_send)
        self._heartbeat_rabbit.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=_HEARTBEAT_ROUTING_KEY,
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self._logger.info("Sent heartbeat to %s exchange",
                          HEALTH_CHECK_EXCHANGE)

    def _process_ping(self, ch: BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:

        self._logger.debug("Received %s. Let's pong", body)
        try:
            heartbeat = {
                'component_name': self.name,
                'is_alive': self._observer.is_alive(),
                'timestamp': datetime.now().timestamp(),
            }

            self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as heartbeats must be
            # real-time
            self._logger.error("Error when sending heartbeat")
            self._logger.exception(e)

    def _send_data(self, config: Dict[str, Any], route_key: str) -> None:
        self._logger.debug("Sending %s with routing key %s", config, route_key)

        while True:
            try:
                self._logger.debug(
                    "Attempting to send config with routing key %s", route_key
                )
                # We need to definitely send this
                self._config_rabbit.basic_publish_confirm(
                    CONFIG_EXCHANGE, route_key, config, mandatory=True,
                    is_body_dict=True,
                    properties=BasicProperties(delivery_mode=2)
                )
                self._logger.info("Configuration update sent")
                break
            except MessageWasNotDeliveredException as mwnde:
                self._logger.error("Config was not successfully sent with "
                                   "routing key %s", route_key)
                self._logger.exception(mwnde)
                self._logger.info("Will attempt sending the config again with "
                                  "routing key %s", route_key)
            except (
                    ConnectionNotInitializedException, AMQPConnectionError
            ) as connection_error:
                # If the connection is not initialised or there is a connection
                # error, we need to restart the connection and try it again
                self._logger.error("There has been a connection error")
                self._logger.exception(connection_error)
                self._logger.info("Restarting the connection")
                self._connected_to_rabbit = False

                # Wait some time before reconnecting and then retrying
                time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)
                self._connect_to_rabbit()

                self._logger.info("Connection restored, will attempt sending "
                                  "the config with routing key %s", route_key)
            except AMQPChannelError:
                # This error would have already been logged by the RabbitMQ
                # logger and handled by RabbitMQ. Since a new channel is created
                # we need to re-initialize RabbitMQ
                self._initialise_rabbitmq()

    def _on_event_thrown(self, event: FileSystemEvent) -> None:
        """
        When an event is thrown, it reads the config and sends it as a dict via
        rabbitmq to the config exchange of type topic
        with the routing key determined by the relative file path.
        :param event: The event passed by watchdog
        :return None
        """

        self._logger.debug("Event thrown: %s", event)
        self._logger.info("Detected a config %s in %s", event.event_type,
                          event.src_path)

        if event.event_type == "deleted":
            self._logger.debug("Creating empty dict")
            config_dict = {}
        else:
            config = ConfigParser()

            self._logger.debug("Reading configuration")
            try:
                config.read(event.src_path)
            except (
                    DuplicateSectionError, DuplicateOptionError,
                    InterpolationError, ParsingError
            ) as e:
                self._logger.error(e.message)
                # When the config is invalid, we do nothing and discard this
                # event.
                return None

            self._logger.debug("Config read successfully")

            config_dict = {key: dict(config[key]) for key in config}
        self._logger.debug("Config converted to dict: %s", config_dict)
        # Since the watcher is configured to watch files in
        # self._config_directory we only need check that (for get_routing_key)
        config_folder = os.path.normpath(self._config_directory)

        key = routing_key.get_routing_key(event.src_path, config_folder)
        self._logger.debug("Sending config %s to RabbitMQ with routing key %s",
                           config_dict, key)
        self._send_data(config_dict, key)

    @property
    def config_directory(self) -> str:
        return self._config_directory

    @property
    def watching(self) -> bool:
        return self._watching

    @property
    def connected_to_rabbit(self) -> bool:
        return self._connected_to_rabbit

    def start(self) -> None:
        """
        This method is used to start rabbit and the observer and begin watching
        the config files. It also sends the configuration files for the first
        time
        :return None
        """
        log_and_print("{} started.".format(self), self._logger)

        self._initialise_rabbitmq()

        def do_first_run_event(name: str) -> None:
            event = FileSystemEvent(name)
            event.event_type = _FIRST_RUN_EVENT
            self._on_event_thrown(event)

        self._logger.info("Throwing first run event for all config files")
        self.foreach_config_file(do_first_run_event)

        if not self._watching:
            self._logger.info("Starting config file observer")
            self._observer.start()
            self._watching = True
        else:
            self._logger.info("File observer is already running")

        self._logger.debug("Config file observer started")
        self._connect_to_rabbit()
        self._heartbeat_rabbit.start_consuming()

    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        """
        This method is used to stop the observer and join the threads
        """
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self._logger)

        if self._watching:
            self._logger.info("Stopping config file observer")
            self._observer.stop()
            self._observer.join()
            self._watching = False
            self._logger.debug("Config file observer stopped")
        else:
            self._logger.info("Config file observer already stopped")
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self._logger)
        sys.exit()

    def foreach_config_file(self, callback: Callable[[str], None]) -> None:
        """
        Runs a function over all the files being watched by this class
        :param callback: The function to watch. Must accept a string for the
            file path as {config_directory} + {file path}
        :return: Nothing
        """
        for root, dirs, files in os.walk(self.config_directory):
            for name in files:
                if any([fnmatch.fnmatch(name, pattern) for pattern in
                        self._file_patterns]):
                    callback(os.path.join(root, name))
