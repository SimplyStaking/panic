from src.config_manager.change_stream.model.base_model import BaseModel

class SubChainModel(BaseModel):
    """
    SubChain Model persisted on MongoDB
    """

    name: str = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        self.name = tuple.name
