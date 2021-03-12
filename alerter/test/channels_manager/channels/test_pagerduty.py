import logging
import unittest
from unittest import mock

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.pagerduty_api import PagerDutyApi
from src.channels_manager.channels import PagerDutyChannel
from src.utils.data import RequestStatus
from src.utils.types import PagerDutySeverities


class TestPagerDutyChannel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_channel_name = 'test_pagerduty_channel'
        self.test_channel_id = 'test_pagerduty_id12345'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.test_integration_key = 'test_integration_key'

        self.test_pagerduty_api = PagerDutyApi(self.test_integration_key)
        self.test_pagerduty_channel = PagerDutyChannel(self.test_channel_name,
                                                       self.test_channel_id,
                                                       self.dummy_logger,
                                                       self.test_pagerduty_api)

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
        self.test_pagerduty_api = None
        self.test_pagerduty_channel = None
        self.test_alert = None

    def test__str__returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         str(self.test_pagerduty_channel))

    def test_channel_name_returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         self.test_pagerduty_channel.channel_name)

    def test_channel_id_returns_channel_id(self) -> None:
        self.assertEqual(self.test_channel_id,
                         self.test_pagerduty_channel.channel_id)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_pagerduty_channel.logger)

    def test__init__initialised_pagerduty_api_correctly(self) -> None:
        self.assertEqual(self.test_pagerduty_api.__dict__,
                         self.test_pagerduty_channel._pager_duty_api.__dict__)

    @mock.patch.object(PagerDutyApi, "trigger")
    def test_alert_triggers_an_alert_correctly(self, mock_trigger) -> None:
        # In this test we will check that PagerDutyApi.trigger() is called
        # with the correct parameters.
        self.test_pagerduty_channel.alert(self.test_alert)
        mock_trigger.assert_called_once_with(
            self.test_alert.message, PagerDutySeverities.WARNING,
            self.test_alert.origin_id, self.test_alert.timestamp)

    @mock.patch.object(PagerDutyApi, "trigger")
    def test_alert_returns_success_if_trigger_request_successful(
            self, mock_trigger) -> None:
        mock_trigger.return_value = None
        actual_ret = self.test_pagerduty_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.SUCCESS, actual_ret)

    @mock.patch.object(PagerDutyApi, "trigger")
    def test_alert_returns_failed_if_trigger_request_unsuccessful(
            self, mock_trigger) -> None:
        mock_trigger.side_effect = Exception('test')
        actual_ret = self.test_pagerduty_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)
