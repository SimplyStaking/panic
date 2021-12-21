import unittest
from unittest import mock

from parameterized import parameterized
from twilio.rest.api.v2010.account import CallList

from src.channels_manager.apis.twilio_api import TwilioApi


class TestTwilioApi(unittest.TestCase):
    def setUp(self) -> None:
        self.test_account_sid = 'test_account_sid'
        self.test_auth_token = 'test_auth_token'
        self.test_call_from = 'test_call_from_number'
        self.test_call_to = 'test_call_to_number'
        self.test_twiml = '<Response><Reject/></Response>'

        self.test_twilio_api = TwilioApi(self.test_account_sid,
                                         self.test_auth_token)

    def tearDown(self) -> None:
        self.test_twilio_api = None

    def test__init__creates_twilio_api_instance_correctly(self) -> None:
        # We cannot make two objects equal as __eq__ was not implemented, so
        # we need to check that the most important variables have been
        # initialised correctly.
        self.assertEqual(self.test_account_sid,
                         self.test_twilio_api._client.username)
        self.assertEqual(self.test_auth_token,
                         self.test_twilio_api._client.password)
        self.assertEqual(self.test_account_sid,
                         self.test_twilio_api._client.account_sid)

    """
    In the tests below we will check that the calls to Client.calls.create have 
    been done correctly. Note, we cannot perform the actual calls to avoid 
    exposing sensitive information.
    """

    @parameterized.expand([(False,), (True,), ])
    @mock.patch.object(CallList, "create")
    def test_dial_number_calls_successfully(self, twiml_is_url,
                                            mock_calls_create) -> None:
        # In these tests we will check that the calls to Client.calls.create
        # have been done correctly. Note, we cannot perform the actual calls to
        # avoid exposing sensitive information.
        self.test_twilio_api.dial_number(self.test_call_from, self.test_call_to,
                                         self.test_twiml, twiml_is_url)
        if twiml_is_url:
            mock_calls_create.assert_called_once_with(to=self.test_call_to,
                                                      from_=self.test_call_from,
                                                      url=self.test_twiml,
                                                      method="GET")
        else:
            mock_calls_create.assert_called_once_with(to=self.test_call_to,
                                                      from_=self.test_call_from,
                                                      twiml=self.test_twiml,
                                                      method="GET")
