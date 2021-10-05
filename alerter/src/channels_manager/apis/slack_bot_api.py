from slack_bolt import App
from slack_bolt.error import BoltError
from slack_sdk.web import SlackResponse


class SlackBotApi:
    def __init__(self, bot_token: str, app_token: str, bot_channel_id: str) \
            -> None:
        self._bot_token = bot_token
        self._app_token = app_token
        self._bot_channel_id = bot_channel_id
        self._app = None

    @property
    def bot_token(self) -> str:
        return self._bot_token

    @property
    def app_token(self) -> str:
        return self._app_token

    @property
    def bot_channel_id(self) -> str:
        return self._bot_channel_id

    def initialize_app(self) -> bool:
        # Initialize Slack Bolt App
        try:
            self._app = App(token=self.bot_token)
        except BoltError:
            return False

        return True

    def send_message(self, message: str) -> SlackResponse:
        if self._app is None:
            if not self.initialize_app():
                return SlackResponse(
                    client=None,
                    http_verb="POST",
                    api_url='',
                    req_args={},
                    data={'ok': False,
                          'error': 'Invalid Slack bot token'},
                    headers={},
                    status_code=500,
                )

        return self._app.client.chat_postMessage(channel=self.bot_channel_id,
                                                 text=message)
