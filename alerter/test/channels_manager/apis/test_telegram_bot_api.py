import unittest
from unittest import mock

import requests

from src.channels_manager.apis.telegram_bot_api import TelegramBotApi


class TestTelegramBotApi(unittest.TestCase):
    def setUp(self) -> None:
        self.test_bot_token = 'test_bot_token'
        self.test_bot_chat_id = 'test_bot_chat_id'
        self.test_base_url = \
            "https://api.telegram.org/bot" + self.test_bot_token
        self.test_message = "This is a test message"

        self.test_telegram_bot_api = TelegramBotApi(self.test_bot_token,
                                                    self.test_bot_chat_id)

    def tearDown(self) -> None:
        self.test_telegram_bot_api = None

    def test_bot_token_returns_bot_token(self) -> None:
        self.assertEqual(self.test_bot_token,
                         self.test_telegram_bot_api.bot_token)

    def test_bot_chat_id_returns_bot_chat_id(self) -> None:
        self.assertEqual(self.test_bot_chat_id,
                         self.test_telegram_bot_api.bot_chat_id)

    def test_base_url_initialised_correctly(self) -> None:
        self.assertEqual(self.test_base_url,
                         self.test_telegram_bot_api._base_url)

    '''
    In the tests below we will check that each request is performed correctly
    by checking that the correct parameters are passed to the request. Note,
    we cannot check that the request was actually successful because we would
    have to expose infrastructure details.
    '''

    @mock.patch.object(requests, "get")
    def test_send_message_sends_a_message_correctly(self, mock_get) -> None:
        data_dict = {
            'chat_id': self.test_bot_chat_id,
            'text': self.test_message,
            'parse_mode': "Markdown"
        }

        self.test_telegram_bot_api.send_message(self.test_message)

        mock_get.assert_called_once_with(self.test_base_url + "/sendMessage",
                                         data=data_dict, timeout=10)

    @mock.patch.object(requests, "get")
    def test_send_get_updates_sends_request_correctly(self, mock_get) -> None:
        self.test_telegram_bot_api.get_updates()

        mock_get.assert_called_once_with(self.test_base_url + "/getUpdates",
                                         timeout=10)

    @mock.patch.object(requests, "get")
    def test_send_get_me_sends_request_correctly(self, mock_get) -> None:
        self.test_telegram_bot_api.get_me()

        mock_get.assert_called_once_with(self.test_base_url + "/getMe",
                                         timeout=10)
