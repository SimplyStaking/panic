import unittest

from src.channels_manager.apis.slack_bot_api import SlackBotApi


class TestSlackBotApi(unittest.TestCase):
    def setUp(self) -> None:
        self.test_bot_token = 'xoxb-XXXXXXXXXXXX-TTTTTTTTTTTTTT'
        self.test_app_token = 'xapp-Y-XXXXXXXXXXXX-TTTTTTTTTTTTT-LLLLLLLLLLLLL'
        self.test_bot_channel_id = 'test_bot_channel_id'
        self.test_message = "This is a test message"

        self.test_slack_bot_api = SlackBotApi(
            self.test_bot_token, self.test_app_token, self.test_bot_channel_id)

    def tearDown(self) -> None:
        self.test_slack_bot_api = None

    def test_bot_token_returns_bot_token(self) -> None:
        self.assertEqual(self.test_bot_token,
                         self.test_slack_bot_api.bot_token)

    def test_app_token_returns_bot_token(self) -> None:
        self.assertEqual(self.test_app_token,
                         self.test_slack_bot_api.app_token)

    def test_bot_channel_id_returns_bot_channel_id(self) -> None:
        self.assertEqual(self.test_bot_channel_id,
                         self.test_slack_bot_api.bot_channel_id)
