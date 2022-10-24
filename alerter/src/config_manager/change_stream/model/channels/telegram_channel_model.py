from src.config_manager.change_stream.model.channels.base_channel_model \
    import BaseChannelModel


class TelegramChannelModel(BaseChannelModel):
    """
    Telegram Model persisted on MongoDB
    """

    bot_token: str = None
    chat_id: int = None

    commands: bool = None
    alerts: bool = None
    info: bool = None
    warning: bool = None
    critical: bool = None
    error: bool = None
        
    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        
        self.bot_token = tuple.bot_token
        self.chat_id = tuple.chat_id
        
        self.commands = tuple.commands
        self.alerts = tuple.alerts
        self.info = tuple.info
        self.warning = tuple.warning
        self.critical = tuple.critical
        self.error = tuple.error
