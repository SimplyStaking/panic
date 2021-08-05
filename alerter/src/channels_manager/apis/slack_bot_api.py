import requests


class SlackBotApi:
    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    @property
    def webhook_url(self) -> str:
        return self._webhook_url

    def send_message(self, message: str) -> str:
        data = {
            'text': message,
            'type': "mrkdwn"
        }

        return requests.post(self.webhook_url, json=data,
                             timeout=10, headers={'Connection': 'close'}).text
