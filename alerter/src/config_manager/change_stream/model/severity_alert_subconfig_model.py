from src.config_manager.change_stream.model.base_model import BaseModel
from src.config_manager.change_stream.model.generic_model import GenericModel

class SeverityAlertSubconfigModel(BaseModel):
    """
    SeverityAlertSubconfig Model persisted on MongoDB
    """

    name: str = None
    value: str = None
    type: GenericModel = None
    enabled: bool = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.name = tuple.name
        self.value = tuple.value
        self.type = tuple.type
        self.enabled = tuple.enabled
