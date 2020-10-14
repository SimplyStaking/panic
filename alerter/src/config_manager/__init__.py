import logging
import os
from configparser import ConfigParser
from typing import List, Union, Optional, Dict, Any

from watchdog.events import FileSystemEvent
from watchdog.observers import Observer

from alerter.src.config_manager.config_update_event_handler import ConfigFileEventHandler
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.exceptions import MessageWasNotDeliveredException

LOGGER = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self,
                 config_directory: str,
                 file_patterns: Optional[List[str]] = None,
                 ignore_file_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True,
                 case_sensitive: bool = False
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

        self._event_handler = ConfigFileEventHandler(self._on_event_thrown, file_patterns, ignore_file_patterns,
                                                     ignore_directories, case_sensitive)
        self._observer = Observer()
        self._observer.schedule(self._event_handler, config_directory, recursive=True)

        self._rabbit = RabbitMQApi()

    def _send_config_to_rabbit_mq(self, config: Dict[str, Any], routing_key: str) -> None:
        LOGGER.debug("Connecting to RabbitMQ")
        self._rabbit.connect_till_successful()
        LOGGER.debug("Connection successful")

        try:
            LOGGER.debug("Attempting to send config")
            # We need to definitely send this
            self._rabbit.basic_publish_confirm("config", routing_key, config, mandatory=True)
        except MessageWasNotDeliveredException as mwnde:
            LOGGER.info("Config was not successfully sent")  # Should not get here
            raise mwnde
        self._rabbit.disconnect()
        LOGGER.debug("Disconnected form RabbitMQ")

    def _on_event_thrown(self, event: FileSystemEvent) -> None:
        config = ConfigParser()
        config.read(event.src_path)
        config_dict = {key: dict(config[key]) for key in config}

        split_src = os.path.split(event.src_path)

        # if "config" in split_src:
        #     os.path.
        #
        # routing_key =
        print(event.src_path)
        print(split_src)
        # self._send_config_to_rabbit_mq(config_dict)

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
