from abc import abstractmethod, ABC
from typing import Any


class Network(ABC):
    def __init__(self, parent_id: str, chain_name: str) -> None:
        self._parent_id = parent_id
        self._chain_name = chain_name

    def __str__(self) -> str:
        return self._chain_name

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def chain_name(self) -> str:
        return self._chain_name

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_chain_name(self, chain_name: str) -> None:
        self._chain_name = chain_name

    @abstractmethod
    def reset(self) -> None:
        pass
