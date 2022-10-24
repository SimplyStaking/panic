class CriticalThresholdSeverity:

    enabled: bool = None
    repeat_enabled: bool = None
    threshold: int = None
    repeat: int = None
    
    def tuple2obj(self, tuple):
        self.enabled = tuple.enabled
        self.repeat_enabled = tuple.repeat_enabled
        self.threshold = tuple.threshold
        self.repeat = tuple.repeat
