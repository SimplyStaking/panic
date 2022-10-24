class WarningThresholdSeverity:
    enabled: bool = False
    threshold: int = 0
    
    def tuple2obj(self, tuple):
        self.threshold = tuple.threshold
        self.enabled = tuple.enabled
