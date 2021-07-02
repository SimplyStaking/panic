from abc import abstractmethod, ABC
from typing import Dict


class ConfigsFactory(ABC):
    def __init__(self) -> None:
        self._configs = {}

    @property
    def configs(self) -> Dict:
        return self._configs

    @abstractmethod
    def add_new_config(self, *args) -> None:
        pass

    @abstractmethod
    def remove_config(self, *args) -> None:
        pass
