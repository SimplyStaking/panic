from abc import abstractmethod, ABC
from typing import Dict, Tuple


class ConfigsFactory(ABC):
    def __init__(self) -> None:
        self._configs = {}

    @property
    def configs(self) -> Dict:
        return self._configs

    @abstractmethod
    def add_new_config(self, chain_name: str, sent_configs: Dict
                       ) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def config_exists(self, chain_name: str) -> bool:
        pass

    @abstractmethod
    def remove_config(self, *args) -> None:
        pass
