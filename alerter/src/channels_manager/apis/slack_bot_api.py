from slack_bolt import App
from slack_bolt.error import BoltError
from slack_sdk.web import SlackResponse


class SlackBotApi:
    def __init__(self, bot_token: str, bot_channel_name: str) -> None:
        self._bot_token = bot_token
        self._bot_channel_name = bot_channel_name
        self._slack_channel_id = None
        self._app = None

    @property
    def bot_token(self) -> str:
        return self._bot_token

    @property
    def bot_channel_name(self) -> str:
        return self._bot_channel_name

    def initialize_app(self) -> bool:
        # Initialize Slack Bolt App and get channel ID
        try:
            self._app = App(token=self.bot_token)
            for channel in self._app.client.conversations_list().get('channels', []):
                if channel['name'] == 'panic-notifications':
                    self._slack_channel_id = channel['id']
                    break
        except BoltError:
            return False

        return self._slack_channel_id is not None

    def send_message(self, message: str) -> SlackResponse:
        if self._app is None or self._slack_channel_id is None:
            if not self.initialize_app():
                return SlackResponse(
                    client=None,
                    http_verb="POST",
                    api_url='',
                    req_args={},
                    data={'ok': False,
                          'error': 'Invalid Slack token or Slack channel name'},
                    headers={},
                    status_code=500,
                )

        return self._app.client.chat_postMessage(channel=self._slack_channel_id, text=message)
