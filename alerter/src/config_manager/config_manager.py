import fnmatch
import logging
import os
import time
from configparser import ConfigParser, DuplicateSectionError, \
    DuplicateOptionError, InterpolationError, ParsingError
from typing import Any, Dict, List, Optional, Callable

from pika import BasicProperties
from pika.exceptions import AMQPChannelError, AMQPConnectionError
from watchdog.events import FileSystemEvent
from watchdog.observers.polling import PollingObserver

from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import CONFIG_EXCHANGE
from src.utils.exceptions import MessageWasNotDeliveredException, \
    ConnectionNotInitializedException
from src.utils.routing_key import get_routing_key
from .config_update_event_handler import ConfigFileEventHandler

_FIRST_RUN_EVENT = 'first run'


class ConfigManager:
    """
    This class reads all configurations and sends them over to the "config"
    topic in Rabbit MQ. Updated configs are sent as well
    """

    def __init__(self, logger: logging.Logger, config_directory: str,
                 rabbit_ip: str, file_patterns: Optional[List[str]] = None,
                 ignore_file_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True, case_sensitive: bool = False):
        """
        Constructs the ConfigManager instance
        :param config_directory: The root config directory to watch.
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

        self._logger = logger
        self._config_directory = config_directory
        self._file_patterns = file_patterns
        self._watching = False
        self._connected_to_rabbit = False

        self._rabbit = RabbitMQApi(logger.getChild('rabbitmq'), host=rabbit_ip)

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

        self._initialize_rabbitmq()

    def _initialize_rabbitmq(self) -> None:
        while True:
            try:
                self._connect_to_rabbit()
                self._logger.debug("Connected to Rabbit")
                self._rabbit.confirm_delivery()
                self._logger.debug("Just set delivery confirmation on RabbitMQ "
                                   "channel")
                self._rabbit.exchange_declare(
                    CONFIG_EXCHANGE, 'topic', False, True, False, False
                )
                self._logger.debug("Declared {} exchange in Rabbit".format(
                    CONFIG_EXCHANGE))
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
                continue

    def __del__(self):
        self.stop_watching_config_files()

    def _connect_to_rabbit(self) -> None:
        if not self._connected_to_rabbit:
            self._logger.info("Connecting to RabbitMQ")
            self._rabbit.connect_till_successful()
            self._connected_to_rabbit = True
            self._logger.info("Connected to RabbitMQ")
        else:
            self._logger.info(
                "Already connected to RabbitMQ, will not connect again")

    def _disconnect_from_rabbit(self) -> None:
        if self._connected_to_rabbit:
            self._logger.info("Disconnecting from RabbitMQ")
            self._rabbit.disconnect_till_successful()
            self._connected_to_rabbit = False
            self._logger.info("Disconnected from RabbitMQ")
        else:
            self._logger.info("Already disconnected from RabbitMQ")

    def _send_config_to_rabbit_mq(self, config: Dict[str, Any],
                                  routing_key: str) -> None:
        self._logger.debug("Sending %s to routing key %s", config, routing_key)

        while True:
            try:
                self._logger.debug(
                    "Attempting to send config to routing key %s", routing_key
                )
                # We need to definitely send this
                self._rabbit.basic_publish_confirm(
                    CONFIG_EXCHANGE, routing_key, config, mandatory=True,
                    is_body_dict=True,
                    properties=BasicProperties(delivery_mode=2)
                )
                self._logger.info("Configuration update sent")
                break
            except MessageWasNotDeliveredException as mwnde:
                self._logger.error("Config was not successfully sent")
                self._logger.exception(mwnde)
                self._logger.info("Will attempt sending the config again")
            except (
                    ConnectionNotInitializedException, AMQPConnectionError
            ) as connection_error:
                # If the connection is not initalized or there is a connection
                # error, we need to restart the connection and try it again
                self._logger.error("There has been a connection error")
                self._logger.exception(connection_error)
                self._logger.info("Restarting the connection")
                self._connected_to_rabbit = False

                # Wait 5 seconds before reconnecting and then retrying
                time.sleep(5)
                self._connect_to_rabbit()

                self._logger.info("Connection restored, will attempt again")
            except AMQPChannelError:
                # This error would have already been logged by the RabbitMQ
                # logger and handled by RabbitMQ. Since a new channel is created
                # we need to re-initialize RabbitMQ
                self._initialize_rabbitmq()

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

        config = ConfigParser()

        self._logger.debug("Reading configuration")
        try:
            config.read(event.src_path)
            # TODO (Mark) PANIC-278 - Implement schema check
        except (
                DuplicateSectionError, DuplicateOptionError, InterpolationError,
                ParsingError
        ) as e:
            self._logger.error(e.message)
            # When the config is invalid, we do nothing and discard this event.
            return None

        self._logger.debug("Config read successfully")

        config_dict = {key: dict(config[key]) for key in config}
        self._logger.debug("Config converted to dict: %s", config_dict)

        # Since the watcher is configured to watch files in
        # self._config_directory we only need check that (for get_routing_key)
        config_folder = os.path.normpath(self._config_directory)

        routing_key = get_routing_key(event.src_path, config_folder)
        self._logger.debug("Sending config %s to RabbitMQ with routing key %s",
                           config_dict, routing_key)
        self._send_config_to_rabbit_mq(config_dict, routing_key)

    @property
    def config_directory(self) -> str:
        return self._config_directory

    @property
    def watching(self) -> bool:
        return self._watching

    @property
    def connected_to_rabbit(self) -> bool:
        return self._connected_to_rabbit

    def start_watching_config_files(self) -> None:
        """
        This method is used to start the observer and begin watching the files
        It also sends the configuration files for the first time
        :return None
        """

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

    def stop_watching_config_files(self) -> None:
        """
        This method is used to stop the observer and join the threads
        """
        if self._watching:
            self._logger.info("Stopping config file observer")
            self._observer.stop()
            self._observer.join()
            self._watching = False
            self._logger.debug("Config file observer stopped")
        else:
            self._logger.info("Config file observer already stopped")
        self._disconnect_from_rabbit()

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
