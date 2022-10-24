from src.config_manager.change_stream.model.channels.base_channel_model \
    import BaseChannelModel


class SlackChannelModel(BaseChannelModel):
    """
    Slack Model persisted on MongoDB
    """

    app_token: str = None
    bot_token: str = None
    bot_channel_id: str = None
    commands: bool = None
    alerts: bool = None
    info: bool = None
    warning: bool = None
    critical: bool = None
    error: bool = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.app_token = tuple.app_token
        self.bot_token = tuple.bot_token
        self.bot_channel_id = tuple.bot_channel_id
        self.commands = tuple.commands
        self.alerts = tuple.alerts
        self.info = tuple.info
        self.warning = tuple.warning
        self.critical = tuple.critical
        self.error = tuple.error
