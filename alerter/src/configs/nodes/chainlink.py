from typing import List

from src.configs.nodes.node import NodeConfig


class ChainlinkNodeConfig(NodeConfig):
    def __init__(self, node_id: str, parent_id: str, node_name: str,
                 monitor_node: bool, node_prometheus_urls: List[str],
                 ethereum_addresses: List[str]) -> None:
        super().__init__(node_id, parent_id, node_name, monitor_node)

        self._node_prometheus_urls = node_prometheus_urls
        self._ethereum_addresses = ethereum_addresses

    @property
    def node_prometheus_urls(self) -> List[str]:
        return self._node_prometheus_urls

    @property
    def ethereum_addresses(self) -> List[str]:
        return self._ethereum_addresses

    def set_node_prometheus_urls(self, node_prometheus_urls: List[str]) -> None:
        self._node_prometheus_urls = node_prometheus_urls

    def set_ethereum_addresses(self, ethereum_addresses: List[str]) -> None:
        self._ethereum_addresses = ethereum_addresses
