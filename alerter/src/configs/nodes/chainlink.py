from typing import List

from src.configs.nodes.node import NodeConfig
from src.utils.exceptions import EnabledSourceIsEmptyException


class ChainlinkNodeConfig(NodeConfig):
    def __init__(self, node_id: str, parent_id: str, node_name: str,
                 monitor_node: bool, monitor_prometheus: bool,
                 node_prometheus_urls: List[str]) -> None:
        super().__init__(node_id, parent_id, node_name, monitor_node)

        self._monitor_prometheus = monitor_prometheus
        self._node_prometheus_urls = [url for url in node_prometheus_urls
                                      if url.strip()]

    @property
    def node_prometheus_urls(self) -> List[str]:
        return self._node_prometheus_urls

    @property
    def monitor_prometheus(self) -> bool:
        return self._monitor_prometheus

    def set_node_prometheus_urls(self, node_prometheus_urls: List[str]) -> None:
        self._node_prometheus_urls = node_prometheus_urls

    def set_monitor_prometheus(self, monitor_prometheus: bool) -> None:
        self._monitor_prometheus = monitor_prometheus

    def enabled_sources_non_empty(self) -> bool:
        """
        This function will go through all the chainlink nodes' data sources. If
        some of them are enabled and empty this will raise an
        EnabledSourceIsEmptyException.
        :return: True if all enabled sources are non-empty
                 raises EnabledSourceIsEmptyException otherwise
        """
        sources = [{
            'name': 'node_prometheus_urls',
            'enabled': self.monitor_prometheus,
            'is_empty': len(self.node_prometheus_urls) == 0
        }]
        for source in sources:
            if source['enabled'] and source['is_empty']:
                raise EnabledSourceIsEmptyException(source['name'],
                                                    self.node_name)

        return True
