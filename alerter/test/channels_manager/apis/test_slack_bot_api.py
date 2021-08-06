import unittest
from unittest import mock

import requests

from src.channels_manager.apis.slack_bot_api import SlackBotApi


class TestSlackBotApi(unittest.TestCase):
    def setUp(self) -> None:
        self.test_bot_webhook_url = 'test_bot_webhook_url'
        self.test_message = "This is a test message"

        self.test_slack_bot_api = SlackBotApi(self.test_bot_webhook_url)

    def tearDown(self) -> None:
        self.test_slack_bot_api = None

    def test_webhook_url_returns_webhook_url(self) -> None:
        self.assertEqual(self.test_bot_webhook_url,
                         self.test_slack_bot_api.webhook_url)

    '''
    In the tests below we will check that each request is performed correctly
    by checking that the correct parameters are passed to the request. Note,
    we cannot check that the request was actually successful because we would
    have to expose infrastructure details.
    '''

    @mock.patch.object(requests, "post")
    def test_send_message_sends_a_message_correctly(self, mock_post) -> None:
        data_dict = {
            'text': self.test_message,
            'type': "mrkdwn"
        }

        self.test_slack_bot_api.send_message(self.test_message)

        mock_post.assert_called_once_with(self.test_bot_webhook_url,
                                          json=data_dict, timeout=10,
                                          headers={'Connection': 'close'})
