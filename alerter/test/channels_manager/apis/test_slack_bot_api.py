import unittest
from unittest import mock

import requests

from src.channels_manager.apis.slack_bot_api import SlackBotApi


class TestSlackBotApi(unittest.TestCase):
    def setUp(self) -> None:
        self.test_bot_token = 'test_bot_token'
        self.test_slack_channel_name = 'test_slack_channel_name'
        self.test_message = "This is a test message"

        self.test_slack_bot_api = SlackBotApi(self.test_bot_token, self.test_slack_channel_name)

    def tearDown(self) -> None:
        self.test_slack_bot_api = None

    def test_bot_token_returns_bot_token(self) -> None:
        self.assertEqual(self.test_bot_token,
                         self.test_slack_bot_api.bot_token)

    def test_slack_channel_name_returns_slack_channel_name(self) -> None:
        self.assertEqual(self.test_slack_channel_name,
                         self.test_slack_bot_api.bot_channel_name)
