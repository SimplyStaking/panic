import copy
from abc import ABC, abstractmethod
from typing import Dict, Optional

from src.configs.alerts.network.cosmos import CosmosNetworkAlertsConfig
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.configs.factory.configs_factory import ConfigsFactory
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration
from src.utils.types import CosmosAlertsConfigs


class CosmosAlertsConfigsFactory(ConfigsFactory, ABC):
    """
    This class manages the Cosmos alerts configs. The configs are indexed by
    the chain name, and it is expected that each chain has exactly one alerts
    config.
    """

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def add_new_config(self, *args) -> None:
        pass

    def remove_config(self, chain_name: str) -> None:
        if chain_name in self.configs:
            del self._configs[chain_name]

    def config_exists(self, chain_name: str,
                      config_type: CosmosAlertsConfigs) -> bool:
        """
        This function returns True if a configuration exists for a chain name.
        :param chain_name: The name of the chain in question
        :param config_type: The type of the configuration we need to have
        :return: True if config exists
               : False otherwise
        """
        return (chain_name in self.configs
                and type(self.configs[chain_name]) == config_type)

    def get_parent_id(self, chain_name: str,
                      config_type: CosmosAlertsConfigs) -> Optional[str]:
        """
        This function returns the parent_id of a chain whose name is chain_name.
        :param chain_name: The name of the chain in question
        :param config_type: The type of the configuration we need to have
        :return: The parent_id of the chain if chain_name in self.configs
               : None otherwise
        """
        if self.config_exists(chain_name, config_type):
            return self.configs[chain_name].parent_id
        else:
            return None

    def get_chain_name(self, parent_id: str,
                       config_type: CosmosAlertsConfigs) -> Optional[str]:
        """
        This function returns the chain name associated with the id.
        :param parent_id: The id of the chain in question
        :param config_type: The type of the configuration we need to have
        :return: The name of the chain if there is a config having the given
               : parent_id
               : None otherwise
        """
        for chain_name, config in self.configs.items():
            if type(config) == config_type and config.parent_id == parent_id:
                return chain_name

        return None


class CosmosNodeAlertsConfigsFactory(CosmosAlertsConfigsFactory):
    """
    This class manages the node alerts configs. The configs are indexed by the
    chain name, and it is expected that each chain has exactly one alerts
    config.
    NOTE: This class will only manage the Cosmos Node alerts residing in Cosmos
          chains' alerts_config.ini.
    """

    def __init__(self) -> None:
        super().__init__()

    def add_new_config(self, chain_name: str, sent_configs: Dict) -> None:
        # Check if all the parent_ids in the received configuration are the
        # same, if not there is some misconfiguration.
        parent_ids = {
            configuration['parent_id']
            for _, configuration in sent_configs.items()
        }
        if len(parent_ids) != 1:
            raise ParentIdsMissMatchInAlertsConfiguration(
                "{}: add_new_config".format(self))

        filtered = {
            config['name']: copy.deepcopy(config)
            for _, config in sent_configs.items()
        }

        cosmos_node_alerts_config = CosmosNodeAlertsConfig(
            parent_id=parent_ids.pop(),
            cannot_access_validator=filtered['cannot_access_validator'],
            cannot_access_node=filtered['cannot_access_node'],
            validator_not_active_in_session=filtered[
                'validator_not_active_in_session'],
            no_change_in_block_height_validator=filtered[
                'no_change_in_block_height_validator'],
            no_change_in_block_height_node=filtered[
                'no_change_in_block_height_node'],
            block_height_difference=filtered['block_height_difference'],
            cannot_access_prometheus_validator=filtered[
                'cannot_access_prometheus_validator'],
            cannot_access_prometheus_node=filtered[
                'cannot_access_prometheus_node'],
            cannot_access_cosmos_rest_validator=filtered[
                'cannot_access_cosmos_rest_validator'],
            cannot_access_cosmos_rest_node=filtered[
                'cannot_access_cosmos_rest_node'],
            cannot_access_tendermint_rpc_validator=filtered[
                'cannot_access_tendermint_rpc_validator'],
            cannot_access_tendermint_rpc_node=filtered[
                'cannot_access_tendermint_rpc_node'],
            missed_blocks=filtered['missed_blocks'],
            slashed=filtered['slashed'],
            node_is_syncing=filtered['node_is_syncing'],
            validator_is_syncing=filtered['validator_is_syncing'],
            validator_is_jailed=filtered['validator_is_jailed']
        )

        self._configs[chain_name] = cosmos_node_alerts_config


class CosmosNetworkAlertsConfigsFactory(CosmosAlertsConfigsFactory):
    """
    This class manages the network alerts configs. The configs are indexed by
    the chain name, and it is expected that each chain has exactly one alerts
    config.
    NOTE: This class will only manage the Cosmos Network alerts residing in
          Cosmos chains' alerts_config.ini.
    """

    def __init__(self) -> None:
        super().__init__()

    def add_new_config(self, chain_name: str, sent_configs: Dict) -> None:
        # Check if all the parent_ids in the received configuration are the
        # same, if not there is some misconfiguration.
        parent_ids = {
            configuration['parent_id']
            for _, configuration in sent_configs.items()
        }
        if len(parent_ids) != 1:
            raise ParentIdsMissMatchInAlertsConfiguration(
                "{}: add_new_config".format(self))

        filtered = {
            config['name']: copy.deepcopy(config)
            for _, config in sent_configs.items()
        }

        cosmos_network_alerts_config = CosmosNetworkAlertsConfig(
            parent_id=parent_ids.pop(), new_proposal=filtered['new_proposal'],
            proposal_concluded=filtered['proposal_concluded'],
        )

        self._configs[chain_name] = cosmos_network_alerts_config
