import string

from src.config_manager.change_stream.model.base_model import BaseModel


class ContractSubconfigModel(BaseModel):
    """
    ContractSubconfig Model persisted on MongoDB
    """
    name: string = None
    url: string = None
    monitor: bool = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.name = tuple.name
        self.url = tuple.url
        self.monitor = tuple.monitor
