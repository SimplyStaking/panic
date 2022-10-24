from src.config_manager.change_stream.model.channels.base_channel_model \
    import BaseChannelModel


class EmailChannelModel(BaseChannelModel):
    """
    Email Model persisted on MongoDB
    """
    
    smtp: str = None
    port: int = None
    email_from: str = None
    emails_to: list[str] = []
    username: str = None
    password: str = None
    info: bool = None
    warning: bool = None
    critical: bool = None
    error: bool = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.smtp = tuple.smtp
        self.port = tuple.port
        self.email_from = tuple.email_from
        self.emails_to = tuple.emails_to
        self.username = tuple.username
        self.password = tuple.password
        self.info = tuple.info
        self.warning = tuple.warning
        self.critical = tuple.critical
        self.error = tuple.error
