from abc import abstractmethod, ABC
from typing import Dict


class AlertingFactory(ABC):
    def __init__(self) -> None:
        self._alerting_state = {}

    @property
    def alerting_state(self) -> Dict:
        return self._alerting_state

    @abstractmethod
    def create_alerting_state(self, *args) -> None:
        pass
