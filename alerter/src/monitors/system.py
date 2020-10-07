# TODO: Do not save in Redis from here (even is_alive key etc) these must be
#       sent to the data store through a channel. The timeout should then be
#       sent with the alive key by the data transformer to the data store.
#       loading from redis can still be done by some monitors (node)

# TODO: In other monitors we must deal with how we are going to handle Redis
#     : hashes
import logging

from alerter.src.moniterables.system import System
from alerter.src.monitors.monitor import Monitor


class SystemMonitor(Monitor):
    def __init__(self, monitor_name: str, system: System,
                 logger: logging.Logger) -> None:
        super().__init__(monitor_name, logger)
        self._system = system

    @property
    def system(self) -> System:
        return self._system

    def status(self) -> str:
        return self.system.status()

    def get_data(self) -> None:
        pass

