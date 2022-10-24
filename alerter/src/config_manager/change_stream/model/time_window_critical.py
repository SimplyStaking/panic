from src.config_manager.change_stream.model.critical_threshold_severity \
    import CriticalThresholdSeverity

class TimeWindowCritical(CriticalThresholdSeverity):
    time_window: int = 0

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        self.time_window = tuple.time_window
