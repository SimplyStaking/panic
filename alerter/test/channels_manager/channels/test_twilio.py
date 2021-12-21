import logging
import unittest
from unittest import mock

from src.channels_manager.apis.twilio_api import TwilioApi
from src.channels_manager.channels.twilio import TwilioChannel
from src.utils.data import RequestStatus


class TestTwilioChannel(unittest.TestCase):
    def setUp(self) -> None:
        self.test_channel_name = 'test_twilio_channel'
        self.test_channel_id = 'test_twilio_id12345'
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.test_account_sid = 'test_account_sid'
        self.test_auth_token = 'test_auth_token'
        self.test_call_from = 'test_call_from_number'
        self.test_call_to = 'test_call_to_number'
        self.test_twiml = '<Response><Reject/></Response>'

        self.test_twilio_api = TwilioApi(self.test_account_sid,
                                         self.test_auth_token)
        self.test_twilio_channel = TwilioChannel(
            self.test_channel_name, self.test_channel_id, self.dummy_logger,
            self.test_twilio_api)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_twilio_api = None
        self.test_twilio_channel = None

    def test__str__returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name, str(self.test_twilio_channel))

    def test_channel_name_returns_channel_name(self) -> None:
        self.assertEqual(self.test_channel_name,
                         self.test_twilio_channel.channel_name)

    def test_channel_id_returns_channel_id(self) -> None:
        self.assertEqual(self.test_channel_id,
                         self.test_twilio_channel.channel_id)

    def test_logger_returns_logger(self) -> None:
        self.assertEqual(self.dummy_logger, self.test_twilio_channel.logger)

    def test__init__initialised_twilio_api_correctly(self) -> None:
        self.assertEqual(self.test_twilio_api.__dict__,
                         self.test_twilio_channel._twilio_api.__dict__)

    @mock.patch.object(TwilioApi, "dial_number")
    def test_alert_calls_correctly(self, mock_dial_number) -> None:
        # In this test we will check that TwilioApi.dial_number() is called
        # with the correct parameters.
        self.test_twilio_channel.alert(self.test_call_from, self.test_call_to,
                                       self.test_twiml, False)
        mock_dial_number.assert_called_once_with(self.test_call_from,
                                                 self.test_call_to,
                                                 self.test_twiml, False)

    @mock.patch.object(TwilioApi, "dial_number")
    def test_alert_returns_success_if_call_request_successful(
            self, mock_dial_number) -> None:
        mock_dial_number.return_value = None
        actual_ret = self.test_twilio_channel.alert(self.test_call_from,
                                                    self.test_call_to,
                                                    self.test_twiml, False)
        self.assertEqual(RequestStatus.SUCCESS, actual_ret)

    def test_alert_returns_failed_if_call_request_fails(self) -> None:
        # Since the twilio credentials are dummy, the call request will fail
        # automatically.
        actual_ret = self.test_twilio_channel.alert(self.test_call_from,
                                                    self.test_call_to,
                                                    self.test_twiml, False)
        self.assertEqual(RequestStatus.FAILED, actual_ret)
