from src.config_manager.change_stream.model.channels.base_channel_model \
    import BaseChannelModel


class TwillioChannelModel(BaseChannelModel):
    """
    Twillio Model persisted on MongoDB
    """

    account_sid: str = None
    auth_token: str = None
    twilio_phone_number: str = None
    twilio_phone_numbers_to_dial: list[str] = []
    critical: bool = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.account_sid = tuple.account_sid
        self.auth_token = tuple.auth_token
        self.twilio_phone_number = tuple.twilio_phone_number
        self.twilio_phone_numbers_to_dial = tuple.twilio_phone_numbers_to_dial
        self.critical = tuple.critical
