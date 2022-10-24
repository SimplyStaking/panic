from src.config_manager.change_stream.model.base_model import BaseModel

class SystemSubconfigModel(BaseModel):
    """
    EVMNodes Model persisted on MongoDB
    """
    
    name: str = None
    monitor: bool = None
    exporter_url: str = None
    
    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        self.name = tuple.name
        self.monitor = tuple.monitor
        self.exporter_url = tuple.exporter_url
        
