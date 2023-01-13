from src.configs.nodes.node import NodeConfig


class CosmosNodeConfig(NodeConfig):
    def __init__(
            self, node_id: str, parent_id: str, node_name: str,
            monitor_node: bool, monitor_prometheus: bool, prometheus_url: str,
            monitor_cosmos_rest: bool, cosmos_rest_url: str,
            monitor_tendermint_rpc: bool, tendermint_rpc_url: str,
            is_validator: bool, is_archive_node: bool, use_as_data_source: bool,
            operator_address: str, is_mev_tendermint_node: bool = False) -> None:
        super().__init__(node_id, parent_id, node_name, monitor_node)

        self._monitor_prometheus = monitor_prometheus
        self._prometheus_url = prometheus_url
        self._monitor_cosmos_rest = monitor_cosmos_rest
        self._cosmos_rest_url = cosmos_rest_url
        self._monitor_tendermint_rpc = monitor_tendermint_rpc
        self._tendermint_rpc_url = tendermint_rpc_url
        self._is_validator = is_validator
        self._is_mev_tendermint_node = is_mev_tendermint_node
        self._is_archive_node = is_archive_node
        self._use_as_data_source = use_as_data_source
        self._operator_address = operator_address

    @property
    def monitor_prometheus(self) -> bool:
        return self._monitor_prometheus

    @property
    def prometheus_url(self) -> str:
        return self._prometheus_url

    @property
    def monitor_cosmos_rest(self) -> bool:
        return self._monitor_cosmos_rest

    @property
    def cosmos_rest_url(self) -> str:
        return self._cosmos_rest_url

    @property
    def monitor_tendermint_rpc(self) -> bool:
        return self._monitor_tendermint_rpc

    @property
    def tendermint_rpc_url(self) -> str:
        return self._tendermint_rpc_url

    @property
    def is_validator(self) -> bool:
        return self._is_validator

    @property
    def is_mev_tendermint_node(self) -> bool:
        return self._is_mev_tendermint_node

    @property
    def is_archive_node(self) -> bool:
        return self._is_archive_node

    @property
    def use_as_data_source(self) -> bool:
        return self._use_as_data_source

    @property
    def operator_address(self) -> str:
        return self._operator_address

    def set_monitor_prometheus(self, monitor_prometheus: bool) -> None:
        self._monitor_prometheus = monitor_prometheus

    def set_prometheus_url(self, prometheus_url: str) -> None:
        self._prometheus_url = prometheus_url

    def set_monitor_cosmos_rest(self, monitor_cosmos_rest: bool) -> None:
        self._monitor_cosmos_rest = monitor_cosmos_rest

    def set_cosmos_rest_url(self, cosmos_rest_url: str) -> None:
        self._cosmos_rest_url = cosmos_rest_url

    def set_monitor_tendermint_rpc(self, monitor_tendermint_rpc: bool) -> None:
        self._monitor_tendermint_rpc = monitor_tendermint_rpc

    def set_tendermint_rpc_url(self, tendermint_rpc_url: str) -> None:
        self._tendermint_rpc_url = tendermint_rpc_url

    def set_is_validator(self, is_validator: bool) -> None:
        self._is_validator = is_validator

    def set_is_mev_tendermint_node(self, is_mev_tendermint_node: bool) -> None:
        self._is_mev_tendermint_node = is_mev_tendermint_node

    def set_is_archive_node(self, is_archive_node: bool) -> None:
        self._is_archive_node = is_archive_node

    def set_use_as_data_source(self, use_as_data_source: bool) -> None:
        self._use_as_data_source = use_as_data_source

    def set_operator_address(self, operator_address: str) -> None:
        self._operator_address = operator_address
