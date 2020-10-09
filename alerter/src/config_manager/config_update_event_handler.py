import logging
from typing import List, Optional, Callable

from watchdog.events import PatternMatchingEventHandler, FileSystemEvent

LOGGER = logging.getLogger(__name__)


class ConfigFileEventHandler(PatternMatchingEventHandler):

    def __init__(self,
                 callback: Callable[[FileSystemEvent], None],
                 patterns: List[str],
                 ignore_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True,
                 case_sensitive: bool = False
                 ):
        """

        :param callback: The function to call when a created, deleted or modified event is fired
        :param patterns: The file patterns to monitor
        :param ignore_patterns:
        :param ignore_directories:
        :param case_sensitive:
        """
        logging.debug(f"Instancing Config Update Event Handler with parameters: callback = {callback}, "
                      f"patterns = {patterns}, ignore_patterns = {ignore_patterns}, "
                      f"ignore_directories={ignore_directories}, case_sensitive={case_sensitive}")

        self._callback = callback
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)

    def on_created(self, event):
        super().on_created(event)

        what = 'directory' if event.is_directory else 'file'
        logging.debug(f"Event triggered: Created {what}: {event.src_path}")

        self._callback(event)

    def on_deleted(self, event):
        super().on_deleted(event)

        what = 'directory' if event.is_directory else 'file'
        logging.debug(f"Event triggered: Deleted {what}: {event.src_path}")

        self._callback(event)

    def on_modified(self, event):
        super().on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        logging.debug(f"Event triggered: Modified {what}: {event.src_path}")

        self._callback(event)
