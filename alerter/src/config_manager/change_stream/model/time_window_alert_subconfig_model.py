import string

from src.config_manager.change_stream.helper.dict_helper import DictHelper
from src.config_manager.change_stream.model.base_model import BaseModel
from src.config_manager.change_stream.model.time_window_critical \
    import TimeWindowCritical
from src.config_manager.change_stream.model.time_window_warning_model \
    import TimeWindowWarning


class TimeWindowAlertSubconfigModel(BaseModel):
    """
    TimeWindowAlertSubconfig Model persisted on MongoDB
    """

    name: str = None
    value: str = None
    warning: TimeWindowWarning = None
    critical: TimeWindowCritical = None
    adornment: string = None
    enabled: bool = None
    
    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        self.name = tuple.name
        self.value = tuple.value
        self.warning = DictHelper.dict2obj(TimeWindowWarning, tuple.warning)
        self.critical = DictHelper.dict2obj(TimeWindowCritical, tuple.critical)
        self.adornment = tuple.adornment
        self.enabled = tuple.enabled
