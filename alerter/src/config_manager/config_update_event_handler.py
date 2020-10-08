from typing import List, Optional, Callable

from watchdog.events import PatternMatchingEventHandler, FileSystemEvent


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
        self._callback = callback
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)

    def on_created(self, event):
        super().on_created(event)
        self._callback(event)

    def on_deleted(self, event):
        super().on_deleted(event)
        self._callback(event)

    def on_modified(self, event):
        super().on_modified(event)
        self._callback(event)
