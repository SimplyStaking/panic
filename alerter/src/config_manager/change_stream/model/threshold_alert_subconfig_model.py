import string

from src.config_manager.change_stream.helper.dict_helper import DictHelper
from src.config_manager.change_stream.model.base_model import BaseModel
from src.config_manager.change_stream.model.critical_threshold_severity \
    import CriticalThresholdSeverity
from src.config_manager.change_stream.model.warning_threshold_severity_model \
    import WarningThresholdSeverity


class ThresholdAlertSubconfigModel(BaseModel):
    """
    ThresholdAlertSubconfig Model persisted on MongoDB
    """
    name: str = None
    value: str = None
    warning: WarningThresholdSeverity = None
    critical: CriticalThresholdSeverity = None
    adornment: string = None
    enabled: bool = None

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        if (tuple.warning):
            self.warning = DictHelper.dict2obj(WarningThresholdSeverity,
                                               tuple.warning)

        if (tuple.critical):
            self.critical = DictHelper.dict2obj(CriticalThresholdSeverity,
                                                tuple.critical)

        self.name = tuple.name
        self.value = tuple.value
        self.adornment = tuple.adornment
        self.enabled = tuple.enabled
