from src.config_manager.change_stream.model.base_config_model \
    import BaseConfigModel
from src.config_manager.change_stream.model.config_model import ConfigModel
from src.config_manager.change_stream.model.generic_model import GenericModel


class BaseChannelModel(BaseConfigModel):
    """
    BaseChannel Model for every channel persisted on MongoDB
    """

    EMAIL = '626573a7fdb17d641746dcdb'
    TELEGRAM = '62656ebafdb17d641746dcda'
    OPS_GENIE = '626573d6fdb17d641746dcdc'
    PAGER_DUTY = '626573fefdb17d641746dcdd'
    TWILLIO = '62657442fdb17d641746dcde'
    SLACK = '62657450fdb17d641746dcdf'

    name: str = None
    type: GenericModel = None
    configs: list[ConfigModel] = []

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.name = tuple.name
        self.type = tuple.type
        self.config_type = tuple.config_type
        self.configs = tuple.configs
