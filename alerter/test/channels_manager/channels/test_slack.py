import logging
import unittest
from unittest import mock

from slack_sdk.web import SlackResponse

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.slack_bot_api import SlackBotApi
from src.channels_manager.channels import SlackChannel
from src.utils.data import RequestStatus


class TestSlackChannel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_channel_name = 'test_slack_channel'
        self.test_channel_id = 'test_slack_id12345'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.test_bot_token = 'test_bot_token'
        self.test_slack_channel_name = 'test_slack_channel_name'

        self.test_slack_bot_api = SlackBotApi(self.test_bot_token, self.test_slack_channel_name)
        self.test_slack_channel = SlackChannel(
            self.test_channel_name, self.test_channel_id, self.dummy_logger,
            self.test_slack_bot_api)

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
        self.test_slack_bot_api = None
        self.test_slack_channel = None
        self.test_alert = None

    def test__str__returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         str(self.test_slack_channel))

    def test_channel_name_returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         self.test_slack_channel.channel_name)

    def test_channel_id_returns_channel_id(self) -> None:
        self.assertEqual(self.test_channel_id,
                         self.test_slack_channel.channel_id)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_slack_channel.logger)

    def test__init__initialised_slack_api_correctly(self) -> None:
        self.assertEqual(self.test_slack_bot_api.__dict__,
                         self.test_slack_channel._slack_bot.__dict__)

    @mock.patch.object(SlackBotApi, "send_message")
    def test_alert_sends_an_alert_correctly(self, mock_send_message) -> None:
        # In this test we will check that PagerDutyApi.trigger() is called
        # with the correct parameters.
        expected_subject = "PANIC {}".format(self.test_alert.severity.upper())
        expected_message = '*{}*: `{}`'.format(expected_subject,
                                               self.test_alert.message)
        self.test_slack_channel.alert(self.test_alert)
        mock_send_message.assert_called_once_with(expected_message)

    @mock.patch.object(SlackBotApi, "send_message")
    def test_alert_returns_success_if_api_request_ok(self,
                                                     mock_send_message) -> None:
        mock_send_message.return_value = SlackResponse(
            client=None,
            http_verb="POST",
            api_url='',
            req_args={},
            data={'ok': True},
            headers={},
            status_code=200,
        )
        actual_ret = self.test_slack_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.SUCCESS, actual_ret)

    @mock.patch.object(SlackBotApi, "send_message")
    def test_alert_returns_failed_if_api_request_not_ok(
            self, mock_send_message) -> None:
        mock_send_message.return_value = 'invalid payload'
        actual_ret = self.test_slack_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)

    @mock.patch.object(SlackBotApi, "send_message")
    def test_alert_returns_failed_if_api_request_raises_exception(
            self, mock_send_message) -> None:
        mock_send_message.side_effect = Exception('test')
        actual_ret = self.test_slack_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)
