import logging
import unittest
from typing import Type
from unittest import mock

from parameterized import parameterized
from watchdog.events import (
    FileSystemEvent, FileDeletedEvent, FileModifiedEvent, FileCreatedEvent,
    FileMovedEvent, DirDeletedEvent,
    DirModifiedEvent, DirMovedEvent, DirCreatedEvent)

from src.config_manager.config_update_event_handler import (
    ConfigFileEventHandler
)


class TestConfigFileEventHandler(unittest.TestCase):
    """
    The two functions are tested with all types of events. While in practice
    this shouldn't be the case, it's good to see that they can handle all
    possibilities.
    """
    def setUp(self) -> None:
        self.callback = mock.Mock(return_value=None, autospec=True)
        self.config_logger = logging.getLogger("test_config")
        self.test_config_event_handler = ConfigFileEventHandler(
            self.config_logger, self.callback, ["*.ini"]
        )

    def test_initialised(self):
        self.assertIsNotNone(self.test_config_event_handler)

    @parameterized.expand([
        (FileDeletedEvent("test_src/test.ini"),),
        (FileModifiedEvent("test_src/test.ini"),),
        (FileCreatedEvent("test_src/test.ini"),),
        (FileMovedEvent("test_src/test.ini", "test_src_2/test.ini"),),
        (DirDeletedEvent("test_src/"),),
        (DirModifiedEvent("test_src/"),),
        (DirCreatedEvent("test_src/"),),
        (DirMovedEvent("test_src/", "test_src_2"),),
    ])
    def test_on_created_triggers_callback(self, event: FileSystemEvent):
        self.test_config_event_handler.on_created(event)

        self.callback.assert_called_once_with(event)

    @parameterized.expand([
        (FileDeletedEvent("test_src/test.ini"),),
        (FileModifiedEvent("test_src/test.ini"),),
        (FileCreatedEvent("test_src/test.ini"),),
        (FileMovedEvent("test_src/test.ini", "test_src_2/test.ini"),),
        (DirDeletedEvent("test_src/"),),
        (DirModifiedEvent("test_src/"),),
        (DirCreatedEvent("test_src/"),),
        (DirMovedEvent("test_src/", "test_src_2"),),
    ])
    def test_on_modified(self, event: FileSystemEvent):
        self.test_config_event_handler.on_modified(event)

        self.callback.assert_called_once_with(event)
