from abc import abstractmethod, ABC
from typing import Any


class Node(ABC):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        self._node_name = node_name
        self._node_id = node_id
        self._parent_id = parent_id

    def __str__(self) -> str:
        return self._node_name

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def node_name(self) -> str:
        return self._node_name

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def parent_id(self) -> str:
        return self._parent_id

    def set_node_name(self, node_name: str) -> None:
        self._node_name = node_name

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    @abstractmethod
    def reset(self) -> None:
        pass
