import signal
from abc import ABC, abstractmethod
from types import FrameType


class Component(ABC):
    """
    We define all the methods a component of this system must have.
    """

    def __init__(self):
        # Handle termination signals by stopping the monitor gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        pass
