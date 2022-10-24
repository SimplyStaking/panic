import bson

from src.config_manager.change_stream.model.base_chain_model \
    import BaseChainModel
from src.config_manager.change_stream.model.base_model import BaseModel
from src.config_manager.change_stream.model.contract_subconfig_model \
    import ContractSubconfigModel
from src.config_manager.change_stream.model.evm_nodes_model import EVMNodesModel
from src.config_manager.change_stream.model.generic_model import GenericModel
from src.config_manager.change_stream.model.node_subconfig_model \
    import NodeSubconfigModel
from src.config_manager.change_stream.model.severity_alert_subconfig_model \
    import SeverityAlertSubconfigModel
from src.config_manager.change_stream.model.sub_chain_model import SubChainModel
from src.config_manager.change_stream.model.system_subconfig_model \
    import SystemSubconfigModel
from src.config_manager.change_stream.model.threshold_alert_subconfig_model \
    import ThresholdAlertSubconfigModel
from src.config_manager.change_stream.model.time_window_alert_subconfig_model \
    import TimeWindowAlertSubconfigModel


class ConfigModel(BaseModel):
    """
    Config Model persisted on MongoDB
    """

    ready: bool = False
    config_type: bson.ObjectId = None
    base_chain: BaseChainModel = None
    sub_chain: SubChainModel = None
    contract: ContractSubconfigModel = None
    nodes: list[NodeSubconfigModel] = []
    evm_nodes: list[EVMNodesModel] = []
    systems: list[SystemSubconfigModel] = []
    repositories: list[GenericModel] = []
    threshold_alerts: list[ThresholdAlertSubconfigModel] = []
    severity_alerts: list[SeverityAlertSubconfigModel] = []
    time_window_alerts: list[TimeWindowAlertSubconfigModel] = []

    def tuple2obj(self, tuple):
        super().tuple2obj(tuple)

        self.ready = tuple.ready
        self.config_type = tuple.config_type
        self.base_chain = tuple.base_chain
        self.sub_chain = tuple.sub_chain
        self.contract = tuple.contract
        self.nodes = tuple.nodes
        self.evm_nodes = tuple.evm_nodes
        self.systems = tuple.systems
        self.repositories = tuple.repositories
        self.threshold_alerts = tuple.threshold_alerts
        self.severity_alerts = tuple.severity_alerts
        self.time_window_alerts = tuple.time_window_alerts
