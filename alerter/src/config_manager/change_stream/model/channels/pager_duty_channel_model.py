from src.config_manager.change_stream.model.channels.base_channel_model \
    import BaseChannelModel


class PagerDutyChannelModel(BaseChannelModel):
    """
    PagerDuty Model persisted on MongoDB
    """

    integration_key: str = None
    info: bool = None
    warning: bool = None
    critical: bool = None
    error: bool = None    
  
    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.integration_key = tuple.integration_key
        self.info = tuple.info
        self.warning = tuple.warning
        self.critical = tuple.critical
        self.error = tuple.error
