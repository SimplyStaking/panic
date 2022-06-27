from src.configs.nodes.node import NodeConfig


class SubstrateNodeConfig(NodeConfig):
    def __init__(self, node_id: str, parent_id: str, node_name: str,
                 monitor_node: bool, node_ws_url: str, use_as_data_source: bool,
                 is_validator: bool, is_archive_node: bool,
                 stash_address: str) -> None:
        super().__init__(node_id, parent_id, node_name, monitor_node)

        # Note that unlike for cosmos we don't have a `self._monitor_ws_url`
        # attribute. This is because we currently have only 1 data source. If
        # more data sources are added in the future we need to add these
        # attributes.
        self._node_ws_url = node_ws_url
        self._use_as_data_source = use_as_data_source
        self._is_validator = is_validator
        self._is_archive_node = is_archive_node
        self._stash_address = stash_address

    @property
    def node_ws_url(self) -> str:
        return self._node_ws_url

    @property
    def use_as_data_source(self) -> bool:
        return self._use_as_data_source

    @property
    def is_validator(self) -> bool:
        return self._is_validator

    @property
    def is_archive_node(self) -> bool:
        return self._is_archive_node

    @property
    def stash_address(self) -> str:
        return self._stash_address

    def set_node_ws_url(self, node_ws_url: str) -> None:
        self._node_ws_url = node_ws_url

    def set_use_as_data_source(self, use_as_data_source: bool) -> None:
        self._use_as_data_source = use_as_data_source

    def set_is_validator(self, is_validator: bool) -> None:
        self._is_validator = is_validator

    def set_is_archive_node(self, is_archive_node: bool) -> None:
        self._is_archive_node = is_archive_node

    def set_stash_address(self, stash_address: str) -> None:
        self._stash_address = stash_address
