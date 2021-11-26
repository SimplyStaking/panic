import unittest
from unittest.mock import patch

from slack_sdk import WebClient

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

    @patch('slack_bolt.app.app.App.__init__')
    def test_initialize_app_successfully_initializes_app(self, mock_app) -> \
            None:
        mock_app.return_value = None
        result = self.test_slack_bot_api.initialize_app()

        self.assertTrue(result)
        mock_app.assert_called_once_with(token=self.test_bot_token)

    @patch('slack_sdk.WebClient.chat_postMessage')
    @patch('slack_bolt.app.app.App.__init__')
    def test_send_message_sends_a_message_correctly(self, mock_app,
                                                    mock_chat_postMessage) -> \
            None:
        mock_app.return_value = None
        # Mock slack app.
        self.test_slack_bot_api.initialize_app()
        # Create empty web client within slack app.
        self.test_slack_bot_api._app._client = WebClient()

        self.test_slack_bot_api.send_message(self.test_message)

        mock_chat_postMessage.assert_called_once_with(
            channel=self.test_bot_channel_id,
            text=self.test_message)
