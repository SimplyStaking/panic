import logging
from configparser import ConfigParser
from typing import List, Union, Optional, Dict, Any

from watchdog.events import FileSystemEvent
from watchdog.observers import Observer

from alerter.src.config_manager.config_update_event_handler import ConfigFileEventHandler

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

        self._event_handler = ConfigFileEventHandler(self.__on_event_thrown, file_patterns, ignore_file_patterns,
                                                     ignore_directories, case_sensitive)
        self._observer = Observer()
        self._observer.schedule(self._event_handler, config_directory, recursive=True)

    def __send_config_to_rabbit_mq(self, config: Dict[str, Any]):
        pass

    def __on_event_thrown(self, event: FileSystemEvent) -> None:
        config = ConfigParser()
        config.read(event.src_path)
        config_dict = {key: dict(config[key]) for key in config}

        self.__send_config_to_rabbit_mq(config_dict)

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
