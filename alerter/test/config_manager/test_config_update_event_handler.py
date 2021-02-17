import logging
import unittest
from unittest import mock

from parameterized import parameterized
from watchdog.events import (
    FileSystemEvent, FileDeletedEvent, FileModifiedEvent, FileCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent, DirCreatedEvent)

from src.config_manager.config_update_event_handler import (
    ConfigFileEventHandler
)


class TestConfigFileEventHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.callback = mock.Mock(return_value=None, autospec=True)
        self.config_logger = logging.getLogger("test_config")
        self.test_config_event_handler = ConfigFileEventHandler(
            self.config_logger, self.callback, ["*.ini"]
        )

    def test_initialised(self):
        self.assertIsNotNone(self.test_config_event_handler)

    @parameterized.expand([
        (FileCreatedEvent("test_src/test.ini"),),
        (DirCreatedEvent("test_src/"),),
    ])
    def test_on_created_triggers_callback(self, event: FileSystemEvent):
        self.test_config_event_handler.on_created(event)

        self.callback.assert_called_once_with(event)

    @parameterized.expand([
        (FileModifiedEvent("test_src/test.ini"),),
        (DirModifiedEvent("test_src/"),),
    ])
    def test_on_modified_triggers_callback(self, event: FileSystemEvent):
        self.test_config_event_handler.on_modified(event)

        self.callback.assert_called_once_with(event)

    @parameterized.expand([
        (FileDeletedEvent("test_src/test.ini"),),
        (DirDeletedEvent("test_src/"),),
    ])
    def test_on_deleted_triggers_callback(self, event: FileSystemEvent):
        self.test_config_event_handler.on_deleted(event)

        self.callback.assert_called_once_with(event)
