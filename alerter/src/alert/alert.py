from src.alert import Channel


class Alert:
    def __init__(self, channel: Channel, alert_message: str):
        self._channel = channel
        self._alert_message = alert_message

    @property
    def channel(self) -> Channel:
        return self._channel

    @property
    def alert_message(self) -> str:
        return self._alert_message
