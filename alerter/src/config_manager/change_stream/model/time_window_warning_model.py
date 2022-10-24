from src.config_manager.change_stream.model.warning_threshold_severity_model \
    import WarningThresholdSeverity


class TimeWindowWarning(WarningThresholdSeverity):
    time_window: int = 0

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)
        self.time_window = tuple.time_window
