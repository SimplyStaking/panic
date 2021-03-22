import logging
import unittest
from datetime import datetime
from unittest import mock
from unittest.mock import call

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.email_api import EmailApi
from src.channels_manager.channels.email import EmailChannel
from src.utils.constants import EMAIL_HTML_TEMPLATE, EMAIL_TEXT_TEMPLATE
from src.utils.data import RequestStatus


class TestEmailChannel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_channel_name = 'test_email'
        self.test_channel_id = 'test_email_id12345'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.test_emails_to = ['test1@example.com', 'test2@example.com',
                               'test3@example.com']
        self.test_smtp = 'test smtp server'
        self.test_sender = 'test sender'
        self.test_username = 'test username'
        self.test_password = 'test password'
        self.test_port = 10

        self.test_email_api = EmailApi(self.test_smtp, self.test_sender,
                                       self.test_username, self.test_password,
                                       self.test_port)

        self.test_email_channel = EmailChannel(self.test_channel_name,
                                               self.test_channel_id,
                                               self.dummy_logger,
                                               self.test_emails_to,
                                               self.test_email_api)

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
        self.test_email_channel = None
        self.test_email_api = None
        self.test_alert = None

    def test__str__returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name, str(self.test_email_channel))

    def test_channel_name_returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         self.test_email_channel.channel_name)

    def test_channel_id_returns_channel_id(self) -> None:
        self.assertEqual(self.test_channel_id,
                         self.test_email_channel.channel_id)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_email_channel.logger)

    def test_emails_to_initialised_correctly(self) -> None:
        self.assertEqual(self.test_emails_to,
                         self.test_email_channel._emails_to)

    def test_email_api_initialised_correctly(self) -> None:
        self.assertEqual(self.test_email_api.__dict__,
                         self.test_email_channel._email_api.__dict__)

    @mock.patch.object(EmailApi, "send_email_with_html")
    def test_alert_sends_email_alert_correctly_to_all_addresses(
            self, mock_send_email_html) -> None:
        # In this test we will check that the emails to be sent are the expected
        # ones. We can do this by checking the arguments passed to
        # EmailApi.send_email_with_html.
        expected_subject = "PANIC {}".format(self.test_alert.severity)
        expected_html_email_message = EMAIL_HTML_TEMPLATE.format(
            alert_code=self.test_alert.alert_code.value,
            severity=self.test_alert.severity, message=self.test_alert.message,
            date_time=datetime.fromtimestamp(self.test_alert.timestamp),
            parent_id=self.test_alert.parent_id,
            origin_id=self.test_alert.origin_id
        )
        expected_plain_email_message = EMAIL_TEXT_TEMPLATE.format(
            alert_code=self.test_alert.alert_code.value,
            severity=self.test_alert.severity,
            message=self.test_alert.message,
            date_time=datetime.fromtimestamp(self.test_alert.timestamp),
            parent_id=self.test_alert.parent_id,
            origin_id=self.test_alert.origin_id
        )
        mock_send_email_html.return_value = None

        self.test_email_channel.alert(self.test_alert)

        self.assertEqual(3, len(mock_send_email_html.call_args_list))
        self.assertEqual(call(expected_subject, expected_html_email_message,
                              expected_plain_email_message,
                              self.test_emails_to[0]),
                         mock_send_email_html.call_args_list[0])
        self.assertEqual(call(expected_subject, expected_html_email_message,
                              expected_plain_email_message,
                              self.test_emails_to[1]),
                         mock_send_email_html.call_args_list[1])
        self.assertEqual(call(expected_subject, expected_html_email_message,
                              expected_plain_email_message,
                              self.test_emails_to[2]),
                         mock_send_email_html.call_args_list[2])

    @mock.patch.object(EmailApi, "send_email_with_html")
    def test_alert_returns_success_if_emails_sent_successfully(
            self, mock_send_email_html) -> None:
        mock_send_email_html.return_value = None
        actual_ret = self.test_email_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.SUCCESS, actual_ret)

    def test_alert_returns_failed_if_some_emails_not_sent(self) -> None:
        # By default this would trigger an exception because the smtp server
        # details and the e-mails are dummy.
        actual_ret = self.test_email_channel.alert(self.test_alert)
        self.assertEqual(RequestStatus.FAILED, actual_ret)
