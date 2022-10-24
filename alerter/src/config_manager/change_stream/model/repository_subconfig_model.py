from src.config_manager.change_stream.model.base_model import BaseModel

class RepositorySubconfigModel(BaseModel):
    """
    RepositorySubconfig Model persisted on MongoDB
    """
        
    name: str = None
    monitor: bool = None
    value: str = None
    namespace: str = None
    type: str = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.name = tuple.name
        self.monitor = tuple.monitor
        self.value = tuple.value
        self.namespace = tuple.namespace
        self.type = tuple.type
