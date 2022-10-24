import bson

from src.config_manager.change_stream.model.base_model import BaseModel


class BaseChainModel(BaseModel):
    """
    BaseChain Model persisted on MongoDB
    """

    COSMOS_ID = '62e143f9f161ba55e6db29cb'
    SUBSTRATE_ID = '62e240b6f161ba55e6db2a0d'
    CHAINLINK_ID = '62e2430cf161ba55e6db2a0e'
    GENERAL_ID = '62e24786f161ba55e6db2a1d'

    name: str = None
    value: str = None
    sources: list[bson.ObjectId] = []
    threshold_alerts: list[bson.ObjectId] = []
    severity_alerts: list[bson.ObjectId] = []
    time_window_alerts: list[bson.ObjectId] = []

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        self.name = tuple.name
        self.value = tuple.value
