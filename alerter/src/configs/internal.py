# This class will be used by a component to keep the current state of the
# internal config. The data will be obtained from Redis and stored using
# this class. Note: Data validation checking should be done by the configs
# manager, as it's job is to parse the data from the configs.


class InternalConfig:

    def __init__(self, system_monitor_period_seconds: int) -> None:

        # [monitoring_periods]
        self._system_monitor_period_seconds = system_monitor_period_seconds

    @property
    def system_monitor_period_seconds(self) -> int:
        return self._system_monitor_period_seconds

    def set_system_monitor_period_seconds(self, system_monitor_period_seconds) \
            -> None:
        self._system_monitor_period_seconds = system_monitor_period_seconds
