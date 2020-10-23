import fnmatch
import logging
import os
from configparser import ConfigParser, \
    DuplicateSectionError, \
    DuplicateOptionError, \
    InterpolationError, \
    ParsingError, \
    MissingSectionHeaderError
from typing import Any, Dict, List, Optional, Callable

from watchdog.events import FileSystemEvent
from watchdog.observers.polling import PollingObserver

from alerter.src.config_manager.config_update_event_handler \
    import ConfigFileEventHandler
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.exceptions import MessageWasNotDeliveredException, \
    ConnectionNotInitializedException
from alerter.src.utils.routing_key import get_routing_key

LOGGER = logging.getLogger(__name__)


class ConfigManager:
    """
    This class reads all configurations and sends them over to the "config"
    topic in Rabbit MQ. Updated configs are sent as well
    """

    def __init__(self,
                 config_directory: str,
                 rabbit_api: RabbitMQApi,
                 file_patterns: Optional[List[str]] = None,
                 ignore_file_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True,
                 case_sensitive: bool = False,
                 output_rabbit_channel: str = "config"
                 ):
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
            file_patterns = ["*.ini"]

        self._config_directory = config_directory
        self._file_patterns = file_patterns
        self._rabbit = rabbit_api
        self._watching = False
        self._connected_to_rabbit = False

        self._event_handler = ConfigFileEventHandler(
            self._on_event_thrown,
            file_patterns,
            ignore_file_patterns,
            ignore_directories,
            case_sensitive
        )
        self._observer = PollingObserver()
        self._observer.schedule(self._event_handler, config_directory,
                                recursive=True)

        try:
            self._connect_to_rabbit()
            LOGGER.debug("Connected to Rabbit")
            self._rabbit.exchange_declare(
                output_rabbit_channel,
                "topic",
                False,
                True,
                False,
                False
            )

            LOGGER.debug("Declared exchange in Rabbit")
        except ConnectionNotInitializedException as cnie:
            # Should be impossible, but since exchange_declare and can throw it
            # we shall ensure to log that the error passed through here too.
            LOGGER.error(
                "Something went wrong that meant a connection was not made")
            LOGGER.error(cnie.message)
            raise cnie

    def __del__(self):
        self.stop_watching_config_files()

    def _connect_to_rabbit(self) -> None:
        if not self._connected_to_rabbit:
            LOGGER.info("Connecting to RabbitMQ")
            self._rabbit.connect_till_successful()
            self._connected_to_rabbit = True
            LOGGER.info("Connected to RabbitMQ")
        else:
            LOGGER.info("Already connected to RabbitMQ, will not connect again")

    def _disconnect_from_rabbit(self) -> None:
        if self._connected_to_rabbit:
            LOGGER.info("Disconnecting from RabbitMQ")
            self._rabbit.disconnect()
            self._connected_to_rabbit = False
            LOGGER.info("Disconnected from RabbitMQ")
        else:
            LOGGER.info("Already disconnected from RabbitMQ")

    def _send_config_to_rabbit_mq(self, config: Dict[str, Any],
                                  routing_key: str) -> None:
        LOGGER.debug("Sending %s to routing key %s", config, routing_key)

        try:
            LOGGER.debug("Attempting to send config to routing key %s",
                         routing_key)
            # We need to definitely send this
            self._rabbit.basic_publish_confirm("config", routing_key, config,
                                               mandatory=False,
                                               is_body_dict=True)
            LOGGER.info("Configuration update sent")
        except MessageWasNotDeliveredException as mwnde:
            LOGGER.error("Config was not successfully sent: %s",
                         mwnde.message)  # Should not get here
            raise mwnde
        except ConnectionNotInitializedException as cnie:
            # This should not happen but it can be thrown
            LOGGER.error("The connection to RabbitMQ is down")
            LOGGER.error(cnie.message)
            raise cnie

    def _on_event_thrown(self, event: FileSystemEvent) -> None:
        """
        When an event is thrown, it reads the config and sends it as a dict via
        rabbitmq to the topic exchange "config"
        with the routing key determined by the relative file path.
        :param event: The event passed by watchdog
        :return None
        """

        LOGGER.debug("Event thrown: %s", event)
        LOGGER.info("Detected a config %s in %s", event.event_type,
                    event.src_path)

        config = ConfigParser()

        LOGGER.debug("Reading configuration")
        try:
            config.read(event.src_path)
        except (
                DuplicateSectionError, DuplicateOptionError, InterpolationError,
                MissingSectionHeaderError, ParsingError
        ) as e:
            LOGGER.error(e.message)
            # When the config is invalid, we do nothing and discard this event.
            return None

        LOGGER.debug("Config read successfully")

        config_dict = {key: dict(config[key]) for key in config}
        LOGGER.debug("Config converted to dict: %s", config_dict)

        # Since the watcher is configured to watch files in
        # self._config_directory we only need check that (for get_routing_key)
        config_folder = os.path.normpath(self._config_directory)

        routing_key = get_routing_key(event.src_path, config_folder)
        LOGGER.debug("Sending config %s to RabbitMQ with routing key %s",
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
            event.event_type = "first run"
            self._on_event_thrown(event)

        LOGGER.info("Throwing first run event for all config files")
        self.foreach_config_file(do_first_run_event)

        if not self._watching:
            LOGGER.info("Starting config file observer")
            self._observer.start()
            self._watching = True
        else:
            LOGGER.info("File observer is already running")

        LOGGER.debug("Config file observer started")
        self._connect_to_rabbit()

    def stop_watching_config_files(self) -> None:
        """
        This method is used to stop the observer and join the threads
        """
        if self._watching:
            LOGGER.info("Stopping config file observer")
            self._observer.stop()
            self._observer.join()
            self._watching = False
            LOGGER.debug("Config file observer stopped")
        else:
            LOGGER.info("Config file observer already stopped")
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
