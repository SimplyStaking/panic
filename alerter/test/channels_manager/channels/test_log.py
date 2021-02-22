import logging
import unittest
from unittest import mock
from unittest.mock import call

from parameterized import parameterized

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.channels.log import LogChannel
from src.utils.alert import Severity
from src.utils.data import RequestStatus
from test.utils.test_utils import assert_not_called_with


class TestLogChannel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_channel_name = 'test_log_channel'
        self.test_channel_id = 'test_log_id12345'
        self.dummy_logger_channel = logging.getLogger('Dummy_Channel_Logger')
        self.dummy_logger_channel.disabled = True
        self.dummy_logger_alerts = logging.getLogger('Dummy_Alerts_Logger')
        self.dummy_logger_alerts.disabled = True

        self.test_log_channel = LogChannel(self.test_channel_name,
                                           self.test_channel_id,
                                           self.dummy_logger_channel,
                                           self.dummy_logger_alerts)

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
        self.dummy_logger_alerts = None
        self.dummy_logger_channel = None
        self.test_log_channel = None
        self.test_alert = None

    def test__str__returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name, str(self.test_log_channel))

    def test_channel_name_returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         self.test_log_channel.channel_name)

    def test_channel_id_returns_channel_id(self) -> None:
        self.assertEqual(self.test_channel_id, self.test_log_channel.channel_id)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger_channel,
                         self.test_log_channel.logger)

    def test__init__initialised_alerts_logger_correctly(self) -> None:
        self.assertEqual(self.dummy_logger_alerts,
                         self.test_log_channel._alerts_logger)

    @parameterized.expand([
        (Severity.INFO,),
        (Severity.WARNING,),
        (Severity.CRITICAL,),
        (Severity.ERROR,),
    ])
    @mock.patch.object(logging.Logger, "error")
    @mock.patch.object(logging.Logger, "warning")
    @mock.patch.object(logging.Logger, "critical")
    @mock.patch.object(logging.Logger, "info")
    def test_alert_logs_alert_correctly(
            self, alert_severity, mock_logger_info, mock_logger_critical,
            mock_logger_warning, mock_logger_error) -> None:
        # This test will be performed by checking that the correct parameters
        # have been passed to the appropriate logger function.
        self.test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            alert_severity.value, self.test_last_monitored,
            alert_severity.value, self.test_parent_id, self.test_system_id
        )
        expected_msg = "PANIC {} - {}".format(alert_severity.value,
                                              self.test_alert.message)

        self.test_log_channel.alert(self.test_alert)

        if alert_severity == Severity.INFO:
            mock_logger_info.assert_has_calls([call(expected_msg)])
            assert_not_called_with(mock_logger_error, [call(expected_msg)])
            assert_not_called_with(mock_logger_warning, [call(expected_msg)])
            assert_not_called_with(mock_logger_critical, [call(expected_msg)])
        elif alert_severity == Severity.WARNING:
            mock_logger_warning.assert_has_calls([call(expected_msg)])
            assert_not_called_with(mock_logger_error, [call(expected_msg)])
            assert_not_called_with(mock_logger_info, [call(expected_msg)])
            assert_not_called_with(mock_logger_critical, [call(expected_msg)])
        elif alert_severity == Severity.CRITICAL:
            mock_logger_critical.assert_has_calls([call(expected_msg)])
            assert_not_called_with(mock_logger_error, [call(expected_msg)])
            assert_not_called_with(mock_logger_warning, [call(expected_msg)])
            assert_not_called_with(mock_logger_info, [call(expected_msg)])
        elif alert_severity == Severity.ERROR:
            mock_logger_error.assert_has_calls([call(expected_msg)])
            assert_not_called_with(mock_logger_info, [call(expected_msg)])
            assert_not_called_with(mock_logger_warning, [call(expected_msg)])
            assert_not_called_with(mock_logger_critical, [call(expected_msg)])

    @parameterized.expand([
        (Severity.INFO,),
        (Severity.WARNING,),
        (Severity.CRITICAL,),
        (Severity.ERROR,),
    ])
    @mock.patch.object(logging.Logger, "error")
    @mock.patch.object(logging.Logger, "warning")
    @mock.patch.object(logging.Logger, "critical")
    @mock.patch.object(logging.Logger, "info")
    def test_alert_returns_success_if_logging_successful(
            self, alert_severity, mock_logger_info, mock_logger_critical,
            mock_logger_warning, mock_logger_error) -> None:
        mock_logger_info.return_value = None
        mock_logger_critical.return_value = None
        mock_logger_warning.return_value = None
        mock_logger_error.return_value = None
        self.test_alert._severity = alert_severity.value

        actual_ret = self.test_log_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.SUCCESS, actual_ret)

    @parameterized.expand([
        (Severity.INFO.value,),
        (Severity.WARNING.value,),
        (Severity.CRITICAL.value,),
        (Severity.ERROR.value,),
        ('BAD_SEVERITY',)
    ])
    @mock.patch.object(logging.Logger, "exception")
    @mock.patch.object(logging.Logger, "error")
    @mock.patch.object(logging.Logger, "warning")
    @mock.patch.object(logging.Logger, "critical")
    @mock.patch.object(logging.Logger, "info")
    def test_alert_returns_failed_if_logging_fails(
            self, alert_severity, mock_logger_info, mock_logger_critical,
            mock_logger_warning, mock_logger_error,
            mock_logger_exception) -> None:
        if alert_severity == Severity.INFO.value:
            mock_logger_info.side_effect = Exception('test')
        elif alert_severity == Severity.WARNING.value:
            mock_logger_warning.side_effect = Exception('test')
        elif alert_severity == Severity.CRITICAL.value:
            mock_logger_critical.side_effect = Exception('test')
        elif alert_severity == Severity.ERROR.value:
            mock_logger_error.side_effect = [Exception('test'), None]
        mock_logger_info.return_value = None
        mock_logger_critical.return_value = None
        mock_logger_warning.return_value = None
        mock_logger_error.return_value = None
        mock_logger_exception.return_value = None
        self.test_alert._severity = alert_severity

        actual_ret = self.test_log_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)
