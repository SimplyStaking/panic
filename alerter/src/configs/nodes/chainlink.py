from typing import List


class ChainlinkNodeConfig:
    def __init__(self, node_id: str, parent_id: str, node_name: str,
                 monitor_node: bool, node_prometheus_urls: List[str],
                 ethereum_addresses: List[str]) -> None:
        self._node_id = node_id
        self._parent_id = parent_id
        self._node_name = node_name
        self._monitor_node = monitor_node
        self._node_prometheus_urls = node_prometheus_urls
        self._ethereum_addresses = ethereum_addresses

    def __str__(self) -> str:
        return self.node_name

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def node_name(self) -> str:
        return self._node_name

    @property
    def monitor_node(self) -> bool:
        return self._monitor_node

    @property
    def node_prometheus_urls(self) -> List[str]:
        return self._node_prometheus_urls

    @property
    def ethereum_addresses(self) -> List[str]:
        return self._ethereum_addresses

    def set_node_id(self, node_id: str) -> None:
        self._node_id = node_id

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_node_name(self, node_name: str) -> None:
        self._node_name = node_name

    def set_monitor_node(self, monitor_node: bool) -> None:
        self._monitor_node = monitor_node

    def set_node_prometheus_urls(self, node_prometheus_urls: List[str]) -> None:
        self._node_prometheus_urls = node_prometheus_urls

    def set_ethereum_addresses(self, ethereum_addresses: List[str]) -> None:
        self._ethereum_addresses = ethereum_addresses
