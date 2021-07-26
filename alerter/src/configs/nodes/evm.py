from src.configs.nodes.node import NodeConfig


class EVMNodeConfig(NodeConfig):
    def __init__(self, node_id: str, parent_id: str, node_name: str,
                 monitor_node: bool, node_http_url: str) -> None:
        super().__init__(node_id, parent_id, node_name, monitor_node)

        self._node_http_url = node_http_url

    @property
    def node_http_url(self) -> str:
        return self._node_http_url

    def set_node_http_url(self, node_http_url: str) -> None:
        self._node_http_url = node_http_url
