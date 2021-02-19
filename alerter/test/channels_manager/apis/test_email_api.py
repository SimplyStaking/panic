import smtplib
import unittest
from datetime import datetime
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest import mock

from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAboveThresholdAlert)
from src.channels_manager.apis.email_api import EmailApi
from src.utils.constants import EMAIL_HTML_TEMPLATE, EMAIL_TEXT_TEMPLATE


class TestMonitorStarters(unittest.TestCase):
    def setUp(self) -> None:
        self.test_smtp = 'test smtp server'
        self.test_sender = 'test sender'
        self.test_username = 'test username'
        self.test_password = 'test password'
        self.test_port = 10
        self.test_message = 'This is a test alert'
        self.test_subject = 'Test Alert'
        self.test_sender = 'PANIC alerter'
        self.test_receiver = 'test@email.com'

        self.test_email_api = EmailApi(self.test_smtp, self.test_sender,
                                       self.test_username, self.test_password,
                                       self.test_port)

        self.test_system_name = 'test system'
        self.test_percentage_usage = 50
        self.test_severity = 'WARNING'
        self.test_last_monitored = 45.5
        self.test_parent_id = 'chain123'
        self.test_system_id = 'system123'
        self.test_alert = OpenFileDescriptorsIncreasedAboveThresholdAlert(
            self.test_system_name, self.test_percentage_usage,
            self.test_severity, self.test_last_monitored, self.test_severity,
            self.test_parent_id, self.test_system_id
        )

        self.test_msg = EmailMessage()
        self.test_msg.set_content("{}\nDate - {}".format(self.test_message,
                                                         datetime.now()))
        self.test_msg['Subject'] = self.test_subject
        self.test_msg['From'] = self.test_sender
        self.test_msg['To'] = self.test_receiver

        # No host and port are given to avoid creating an smtp session
        self.test_smtp_interface = smtplib.SMTP()

    def tearDown(self) -> None:
        self.test_email_api = None
        self.test_alert = None
        self.test_msg = None
        self.test_smtp_interface = None

    def test__init__creates_a_correct_email_api_instance(self) -> None:
        expected_instance_variables = {
            '_smtp': self.test_email_api._smtp,
            '_sender': self.test_email_api._sender,
            '_username': self.test_email_api._username,
            '_password': self.test_email_api._password,
            '_port': self.test_email_api._port,
        }
        self.assertDictEqual(expected_instance_variables,
                             self.test_email_api.__dict__)

    @freeze_time("2012-01-01")
    @mock.patch.object(EmailApi, "_send_smtp")
    def test_send_email_sends_the_correct_message(self, mock_send_smtp) -> None:
        # In this test we will check that the self._send_smtp function was
        # called with the correct message as there is no other way of testing
        # whether the e-mail was actually sent without exposing infrastructure
        # details.
        mock_send_smtp.return_value = None

        expected_msg = EmailMessage()
        expected_msg.set_content("{}\nDate - {}".format(self.test_message,
                                                        datetime.now()))
        expected_msg['Subject'] = self.test_subject
        expected_msg['From'] = self.test_sender
        expected_msg['To'] = self.test_receiver

        self.test_email_api.send_email(self.test_subject, self.test_message,
                                       self.test_receiver)

        args, _ = mock_send_smtp.call_args
        self.assertEqual(1, len(args))
        mock_send_smtp.assert_called_once()

        # By the as_string function we will get the formatted e-mail as string
        self.assertEqual(expected_msg.as_string(), args[0].as_string())

    @freeze_time("2012-01-01")
    @mock.patch.object(EmailApi, "_send_smtp")
    def test_send_email_with_html_sends_the_correct_message(
            self, mock_send_smtp) -> None:
        # In this test we will check that the self._send_smtp function was
        # called with the correct message as there is no other way of testing
        # whether the e-mail was actually sent without exposing infrastructure
        # details.
        mock_send_smtp.return_value = None
        html_wrapper = """\
        <html>
            <head></head>
            <body>
                {message}
                <p>Date - {timestamp}</p>
            </body>
        </html>"""
        html_email_message = EMAIL_HTML_TEMPLATE.format(
            alert_code=self.test_alert.alert_code.value,
            severity=self.test_alert.severity,
            message=self.test_alert.message,
            date_time=datetime.fromtimestamp(self.test_alert.timestamp),
            parent_id=self.test_alert.parent_id,
            origin_id=self.test_alert.origin_id
        )
        plain_email_message = EMAIL_TEXT_TEMPLATE.format(
            alert_code=self.test_alert.alert_code.value,
            severity=self.test_alert.severity,
            message=self.test_alert.message,
            date_time=datetime.fromtimestamp(self.test_alert.timestamp),
            parent_id=self.test_alert.parent_id,
            origin_id=self.test_alert.origin_id
        )
        expected_msg = MIMEMultipart('alternative')
        expected_msg['Subject'] = self.test_subject
        expected_msg['From'] = self.test_sender
        expected_msg['To'] = self.test_receiver
        part1 = MIMEText("{}\nDate - {}".format(plain_email_message,
                                                datetime.now()), 'plain')
        part2 = MIMEText(
            html_wrapper.format(message=html_email_message,
                                timestamp=datetime.now()), 'html')
        expected_msg.attach(part1)
        expected_msg.attach(part2)

        self.test_email_api.send_email_with_html(self.test_subject,
                                                 html_email_message,
                                                 plain_email_message,
                                                 self.test_receiver)

        args, _ = mock_send_smtp.call_args
        self.assertEqual(1, len(args))
        mock_send_smtp.assert_called_once()

        # This must be done because boundaries are auto-generated
        expected_msg.set_boundary('test_boundary')
        args[0].set_boundary('test_boundary')

        # By the as_string function we will get the formatted e-mail as string
        self.assertEqual(expected_msg.as_string(), args[0].as_string())

    @parameterized.expand([('test_username',), (None,), ])
    @mock.patch.object(smtplib.SMTP, "send_message")
    @mock.patch.object(smtplib.SMTP, "quit")
    @mock.patch.object(smtplib.SMTP, "starttls")
    @mock.patch.object(smtplib.SMTP, "login")
    @mock.patch.object(smtplib, "SMTP")
    def test_send_smtp_sends_a_message_correctly(
            self, username, mock_smtp_init, mock_login, mock_starttls,
            mock_quit, mock_send_message) -> None:
        # In this test we will check that function calls to send a message were
        # called correctly. Note, we cannot check whether the e-mail was
        # actually sent without exposing infrastructure details. This test is
        # parametrized to test for when login occurs and when login does not
        # occur
        mock_smtp_init.return_value = self.test_smtp_interface
        mock_quit.return_value = None
        mock_send_message.return_value = None
        mock_login.return_value = None
        mock_starttls.return_value = None

        # When the username is None no login is performed
        self.test_email_api._username = username

        self.test_email_api._send_smtp(self.test_msg)

        # Check that the SMTP interface initialisation was performed correctly.
        mock_smtp_init.assert_called_once_with(self.test_smtp, self.test_port)

        # Check that send_message was called correctly.
        mock_send_message.assert_called_once_with(self.test_msg)

        # Check that quit was called correctly.
        args, _ = mock_quit.call_args
        self.assertEqual(0, len(args))
        mock_quit.assert_called_once()

    @mock.patch.object(smtplib.SMTP, "send_message")
    @mock.patch.object(smtplib.SMTP, "quit")
    @mock.patch.object(smtplib.SMTP, "starttls")
    @mock.patch.object(smtplib.SMTP, "login")
    @mock.patch.object(smtplib, "SMTP")
    def test_send_smtp_logs_in_if_user_and_pass_not_None_and_user_not_empty(
            self, mock_smtp_init, mock_login, mock_starttls, mock_quit,
            mock_send_message) -> None:
        mock_smtp_init.return_value = self.test_smtp_interface
        mock_quit.return_value = None
        mock_send_message.return_value = None
        mock_login.return_value = None
        mock_starttls.return_value = None

        self.test_email_api._send_smtp(self.test_msg)

        # Check that the starttls function was called correctly.
        args, _ = mock_starttls.call_args
        self.assertEqual(0, len(args))
        mock_starttls.assert_called_once()

        # Check that the login function was called correctly.
        mock_login.assert_called_once_with(self.test_username,
                                           self.test_password)
        args, _ = mock_login.call_args
        self.assertEqual(1, mock_login.call_count)
        self.assertEqual(2, len(args))
        self.assertEqual(self.test_username, args[0])
        self.assertEqual(self.test_password, args[1])

    @parameterized.expand([
        (None, 'test_password'),
        ('test_username', None),
        (None, None,),
        ('', 'test_pass'),
        ('', ''),
        ('', None,),
    ])
    @mock.patch.object(smtplib.SMTP, "send_message")
    @mock.patch.object(smtplib.SMTP, "quit")
    @mock.patch.object(smtplib.SMTP, "starttls")
    @mock.patch.object(smtplib.SMTP, "login")
    @mock.patch.object(smtplib, "SMTP")
    def test_send_smtp_no_log_in_if_username_or_password_None_or_username_empty(
            self, username, password, mock_smtp_init, mock_login, mock_starttls,
            mock_quit, mock_send_message) -> None:
        mock_smtp_init.return_value = self.test_smtp_interface
        mock_quit.return_value = None
        mock_send_message.return_value = None
        mock_login.return_value = None
        mock_starttls.return_value = None

        # Set the username and password according to the parametrization
        self.test_email_api._username = username
        self.test_email_api._password = password

        self.test_email_api._send_smtp(self.test_msg)

        # Check that the starttls function was not called.
        mock_starttls.assert_not_called()

        # Check that the login function was not called.
        mock_login.assert_not_called()
