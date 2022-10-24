from src.config_manager.change_stream.model.base_model import BaseModel

class NodeSubconfigModel(BaseModel):
    """
    NodeSubconfig Model persisted on MongoDB
    """
    name: str = None
    node_prometheus_urls: str = None
    monitor_prometheus: bool = None
    monitor_node: bool = None
    evm_nodes_urls: str = None
    weiwatchers_url: str = None
    monitor_contracts: bool = None
    cosmos_rest_url: str = None
    monitor_cosmos_rest: bool = None
    prometheus_url: str = None
    exporter_url: str = None
    monitor_system: bool = None
    is_validator: bool = None
    is_archive_node: bool = None
    use_as_data_source: bool = None
    monitor_network: bool = None
    operator_address: str = None
    monitor_tendermint_rpc: bool = None
    tendermint_rpc_url: str = None
    node_ws_url: str = None
    stash_address: str = None
    governance_addresses: str = None
    
    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.name = tuple.name
        self.node_prometheus_urls = tuple.node_prometheus_urls
        self.monitor_prometheus = tuple.monitor_prometheus
        self.monitor_node = tuple.monitor_node
        self.evm_nodes_urls = tuple.evm_nodes_urls
        self.weiwatchers_url = tuple.weiwatchers_url
        self.monitor_contracts = tuple.monitor_contracts
        self.cosmos_rest_url = tuple.cosmos_rest_url
        self.monitor_cosmos_rest = tuple.monitor_cosmos_rest
        self.prometheus_url = tuple.prometheus_url
        self.exporter_url = tuple.exporter_url
        self.monitor_system = tuple.monitor_system
        self.is_validator = tuple.is_validator
        self.is_archive_node = tuple.is_archive_node
        self.use_as_data_source = tuple.use_as_data_source
        self.monitor_network = tuple.monitor_network
        self.operator_address = tuple.operator_address
        self.monitor_tendermint_rpc = tuple.monitor_tendermint_rpc
        self.tendermint_rpc_url = tuple.tendermint_rpc_url
        self.node_ws_url = tuple.node_ws_url
        self.stash_address = tuple.stash_address
        self.governance_addresses = tuple.governance_addresses