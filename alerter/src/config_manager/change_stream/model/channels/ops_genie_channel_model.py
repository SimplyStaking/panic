from src.config_manager.change_stream.model.channels.base_channel_model \
    import BaseChannelModel


class OpsGenieChannelModel(BaseChannelModel):
    """
    OpsGenie Model persisted on MongoDB
    """
    
    api_token: str = None
    eu: bool = None
    info: bool = None
    warning: bool = None
    critical: bool = None
    error: bool = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.api_token = tuple.api_token
        self.eu = tuple.eu
        self.info = tuple.info
        self.warning = tuple.warning
        self.critical = tuple.critical
        self.error = tuple.error
