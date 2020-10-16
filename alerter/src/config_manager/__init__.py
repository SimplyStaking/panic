import logging
import os
from configparser import ConfigParser, \
                         DuplicateSectionError, \
                         DuplicateOptionError, \
                         InterpolationError, \
                         ParsingError, \
                         MissingSectionHeaderError
from typing import Any, Dict, List, Optional

from watchdog.events import FileSystemEvent
from watchdog.observers import Observer

from alerter.src.config_manager.config_update_event_handler import ConfigFileEventHandler
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.exceptions import MessageWasNotDeliveredException, ConnectionNotInitializedException

LOGGER = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self,
                 config_directory: str,
                 file_patterns: Optional[List[str]] = None,
                 ignore_file_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True,
                 case_sensitive: bool = False,
                 output_rabbit_channel: str = "config"
                 ):
        """
        Constructs the ConfigManager instance
        :param config_directory: The root config directory to watch. This is searched recursively.
        :param file_patterns: The file patterns in the directory to watch. Defaults to all ini files
        :param ignore_file_patterns: Any file patterns to ignore. Defaults to None
        :param ignore_directories: Whether changes in directories should be ignored. Default: True
        :param case_sensitive: Whether the patterns in `file_patterns` and `ignore_file_patterns` are case sensitive. Default: False
        """
        if not file_patterns:
            file_patterns = ["*.ini"]

        self._config_directory = config_directory
        self._event_handler = ConfigFileEventHandler(self._on_event_thrown, file_patterns, ignore_file_patterns,
                                                     ignore_directories, case_sensitive)
        self._observer = Observer()
        self._observer.schedule(self._event_handler, config_directory, recursive=True)

        self._rabbit = RabbitMQApi(logging.getLogger(RabbitMQApi.__name__))

        try:
            self._rabbit.connect_till_successful()
            self._rabbit.exchange_declare(output_rabbit_channel, 'topic', False, True, False, False)
            self._rabbit.disconnect()
        except ConnectionNotInitializedException as cnie:
            # This should not happen at all, but since exchange_declare and disconnect can throw it
            # we shall ensure to log that the error passed through here too.
            LOGGER.error("Something went wrong that meant a connection was not made")
            LOGGER.error(cnie.message)
            raise cnie

    def _send_config_to_rabbit_mq(self, config: Dict[str, Any], routing_key: str) -> None:
        LOGGER.debug("Sending %s to routing key %s", config, routing_key)
        LOGGER.debug("Connecting to RabbitMQ")
        self._rabbit.connect_till_successful()
        LOGGER.debug("Connection successful")

        try:
            LOGGER.debug("Attempting to send config to routing key %s", routing_key)
            # We need to definitely send this
            self._rabbit.basic_publish_confirm("config", routing_key, config, mandatory=True, is_body_dict=True)
            LOGGER.info("Configuration update sent")
            self._rabbit.disconnect()
        except MessageWasNotDeliveredException as mwnde:
            LOGGER.error("Config was not successfully sent: %s", mwnde.message)  # Should not get here
            raise mwnde
        except ConnectionNotInitializedException as cnie:
            # This should not happen but it can be thrown
            LOGGER.error("Something went wrong that meant a connection was not made")
            LOGGER.error(cnie.message)
            raise cnie

        LOGGER.debug("Disconnected form RabbitMQ")

    def _on_event_thrown(self, event: FileSystemEvent) -> None:
        LOGGER.debug("Event thrown: %s", event)
        LOGGER.info("Detected a config %s in %s", event.event_type, event.src_path)

        config = ConfigParser()

        LOGGER.debug("Reading configuration")
        try:
            config.read(event.src_path)
        except (
                DuplicateSectionError, DuplicateOptionError, InterpolationError, MissingSectionHeaderError, ParsingError
        ) as e:
            LOGGER.error(e.message)
            # When the config is invalid, we will do, nothing and discard this event.
            return None

        LOGGER.debug("Config read successfully")

        config_dict = {key: dict(config[key]) for key in config}
        LOGGER.debug("Config converted to dict: %s", config_dict)

        # Since the watcher is configured to watch files in self._config_directory
        # We only need check that
        config_folder = os.path.normpath(self._config_directory)

        path_list = []
        head = (os.path.normpath(event.src_path).split(config_folder, 1))[1]

        while True:
            head, tail = os.path.split(head)
            if not tail:
                break

            path_list.append(tail)

        routing_key = ".".join(reversed(path_list))
        LOGGER.debug("Sending config %s to RabbitMQ with routing key %s", config_dict, routing_key)
        self._send_config_to_rabbit_mq(config_dict, routing_key)

    def start_watching_config_files(self) -> None:
        """
        This method is used to start the observer and begin watching the files
        """
        LOGGER.info("Starting config file observer")
        self._observer.start()
        LOGGER.debug("Config file observer started")

    def stop_watching_config_files(self) -> None:
        """
        This method is used to stop the observer and join the threads
        """
        LOGGER.info("Stopping config file observer")
        self._observer.stop()
        self._observer.join()
        LOGGER.debug("Config file observer stopped")
