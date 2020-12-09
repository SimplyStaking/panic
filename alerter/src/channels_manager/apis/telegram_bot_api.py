from typing import Optional, Dict

import requests


class TelegramBotApi:
    def __init__(self, bot_token: str, bot_chat_id: Optional[str]) -> None:
        self._bot_token = bot_token
        self._bot_chat_id = bot_chat_id

        self._base_url = 'https://api.telegram.org/bot' + bot_token

    @property
    def bot_token(self) -> str:
        return self._bot_token

    @property
    def bot_chat_id(self) -> Optional[str]:
        return self._bot_chat_id

    def send_message(self, message: str) -> Dict:
        data = {
            'chat_id': self.bot_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        return requests.get(self._base_url + '/sendMessage',
                            data=data, timeout=10).json()

    def get_updates(self) -> Dict:
        return requests.get(self._base_url + '/getUpdates',
                            timeout=10).json()

    def get_me(self) -> Dict:
        return requests.get(self._base_url + '/getMe',
                            timeout=10).json()
