import logging
import unittest
from unittest import mock

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.channels.console import ConsoleChannel
from src.utils.data import RequestStatus


class TestConsole(unittest.TestCase):
    def setUp(self) -> None:
        self.test_channel_name = 'test_console'
        self.test_channel_id = 'test_console_id12345'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True

        self.test_console_channel = ConsoleChannel(self.test_channel_name,
                                                   self.test_channel_id,
                                                   self.dummy_logger)

        self.test_system_name = 'test_system'
        self.test_percentage_usage = 50
        self.test_panic_severity = 'WARNING'
        self.test_last_monitored = 45
        self.test_parent_id = 'parent_1234'
        self.test_system_id = 'system_id32423'
        self.test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_panic_severity, self.test_last_monitored,
            self.test_panic_severity, self.test_parent_id, self.test_system_id
        )

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_console_channel = None
        self.test_alert = None

    def test__str__returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name, str(self.test_console_channel))

    def test_channel_name_returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         self.test_console_channel.channel_name)

    def test_channel_id_returns_channel_id(self) -> None:
        self.assertEqual(self.test_channel_id,
                         self.test_console_channel.channel_id)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_console_channel.logger)

    @mock.patch("builtins.print")
    @mock.patch("sys.stdout.flush")
    def test_alert_prints_an_alert_correctly(self, mock_flush,
                                             mock_print) -> None:
        # In this test we will check that the message to be printed is the
        # expected one. We can do this by checking that the message argument
        # passed to print() is the one that we expect.
        expected_msg = "PANIC {} - {}".format(self.test_alert.severity.upper(),
                                              self.test_alert.message)

        self.test_console_channel.alert(self.test_alert)
        mock_flush.assert_called_once()
        mock_print.assert_called_once_with(expected_msg)

    @mock.patch("builtins.print")
    @mock.patch("sys.stdout.flush")
    def test_alert_returns_success_if_alert_printed_successfully(
            self, mock_flush, mock_print) -> None:
        mock_flush.return_value = None
        mock_print.return_value = None

        actual_ret = self.test_console_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.SUCCESS, actual_ret)

    @mock.patch("builtins.print")
    @mock.patch("sys.stdout.flush")
    def test_alert_returns_failed_if_alert_was_not_printed(
            self, mock_flush, mock_print) -> None:
        mock_flush.return_value = None
        mock_print.side_effect = Exception('test')

        actual_ret = self.test_console_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)
