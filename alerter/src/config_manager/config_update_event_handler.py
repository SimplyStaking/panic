import logging
from typing import List, Optional, Callable

from watchdog.events import PatternMatchingEventHandler, FileSystemEvent


class ConfigFileEventHandler(PatternMatchingEventHandler):
    """
    Event handler based on the PatternMatchingEventHandler from watchdog
    """

    def __init__(self,
                 logger: logging.Logger,
                 callback: Callable[[FileSystemEvent], None],
                 patterns: List[str],
                 ignore_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True,
                 case_sensitive: bool = False
                 ):
        """
        :param callback: The function to call when a created, deleted or
            modified event is fired
        :param patterns: A list of file patterns to monitor.
        :param ignore_patterns: The file patterns to ignore. Defaults to None
        :param ignore_directories: Whether to ignore directories or not.
            Defaults to True
        :param case_sensitive: Whether the patterns given are case sensitive or
            not. Defaults to False
        """
        self._logger = logger
        self._logger.debug(
            "Instancing Config Update Event Handler with parameters: "
            "callback = %s, patterns = %s, ignore_patterns = %s,  "
            "ignore_directories = %s, case_sensitive = %s", callback, patterns,
            ignore_patterns, ignore_directories, case_sensitive
        )

        self._callback = callback
        super().__init__(patterns, ignore_patterns, ignore_directories,
                         case_sensitive)

    def on_created(self, event):
        super().on_created(event)

        what = 'directory' if event.is_directory else 'file'
        self._logger.debug("Event triggered: Created %s: %s", what,
                           event.src_path)

        self._callback(event)

    def on_modified(self, event):
        super().on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        self._logger.debug("Event triggered: Modified %s: %s", what,
                           event.src_path)

        self._callback(event)
