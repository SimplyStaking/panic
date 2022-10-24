from src.config_manager.change_stream.model.base_model import BaseModel

class GenericModel(BaseModel):
    """
    Generic Model persisted on MongoDB
    """

    SUB_CHAIN = '6265758cfdb17d641746dce4'
    EMAIL_CHANNEL = '626574fffdb17d641746dce0'
    OPSGENIE_CHANNEL = '62f0f9822bff1d0ead2d2df7'
    PAGERDUTY_CHANNEL = '62f0f9a52bff1d0ead2d2df8'
    SLACK_CHANNEL = '62f0f9b52bff1d0ead2d2df9'
    TELEGRAM_CHANNEL = '62f0f9c52bff1d0ead2d2dfa'
    TWILIO_CHANNEL = '62f0f9d52bff1d0ead2d2dfb'
    
    SEVERITY_INFO = '6265d085fdb17d641746dcef'
    SEVERITY_WARNING = '6265d08efdb17d641746dcf0'
    SEVERITY_ERROR = '6265d096fdb17d641746dcf1'
    SEVERITY_CRITICAL = '6265d0a7fdb17d641746dcf2'
    
    REPO_GIT = '628bdacb5c5ab4c82d151aa4'
    REPO_DOCKER = '628bdafa5c5ab4c82d151aa5'

    name: str = None
    value: str = None
    value: str = None
    description: str = None
    group: str = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.name = tuple.name
        self.value = tuple.value
        self.description = tuple.description
        self.group = tuple.group

