import string

from src.config_manager.change_stream.model.base_model import BaseModel


class EVMNodesModel(BaseModel):
    """
    EVMNodes Model persisted on MongoDB
    """
    
    name: string = None
    monitor: bool = None
    node_http_url: string = None
    
    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.name = tuple.name
        self.monitor = tuple.monitor
        self.node_http_url = tuple.node_http_url        
