import bson

from src.config_manager.change_stream.model.base_model import BaseModel


class BaseConfigModel(BaseModel):
    """
    BaseConfig Model persisted on MongoDB
    """

    config_type: bson.ObjectId = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        self.config_type = tuple.config_type



