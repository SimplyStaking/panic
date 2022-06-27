import copy
from abc import ABC, abstractmethod
from typing import Dict, Optional

from src.configs.alerts.network.substrate import SubstrateNetworkAlertsConfig
from src.configs.alerts.node.substrate import SubstrateNodeAlertsConfig
from src.configs.factory.configs_factory import ConfigsFactory
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration
from src.utils.types import SubstrateAlertsConfigs


class SubstrateAlertsConfigsFactory(ConfigsFactory, ABC):
    """
    This class manages the Substrate alerts configs. The configs are indexed by
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
                      config_type: SubstrateAlertsConfigs) -> bool:
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
                      config_type: SubstrateAlertsConfigs) -> Optional[str]:
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
                       config_type: SubstrateAlertsConfigs) -> Optional[str]:
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


class SubstrateNodeAlertsConfigsFactory(SubstrateAlertsConfigsFactory):
    """
    This class manages the node alerts configs. The configs are indexed by the
    chain name, and it is expected that each chain has exactly one alerts
    config.
    NOTE: This class will only manage the Substrate Node alerts residing in
    Substrate chains' alerts_config.ini.
    """

    def __init__(self) -> None:
        super().__init__()

    def add_new_config(self, chain_name: str, sent_configs: Dict) -> None:
        # Check if all the parent_ids in the received configuration are the
        # same, if not there is some misconfiguration.
        parent_ids = {
            configuration['parent_id']
            for configuration in sent_configs.values()
        }
        if len(parent_ids) != 1:
            raise ParentIdsMissMatchInAlertsConfiguration(
                "{}: add_new_config".format(self))

        filtered = {
            config['name']: copy.deepcopy(config)
            for config in sent_configs.values()
        }

        substrate_node_alerts_config = SubstrateNodeAlertsConfig(
            parent_id=parent_ids.pop(),
            cannot_access_validator=filtered['cannot_access_validator'],
            cannot_access_node=filtered['cannot_access_node'],
            no_change_in_best_block_height_validator=filtered[
                'no_change_in_best_block_height_validator'],
            no_change_in_best_block_height_node=filtered[
                'no_change_in_best_block_height_node'],
            no_change_in_finalized_block_height_validator=filtered[
                'no_change_in_finalized_block_height_validator'],
            no_change_in_finalized_block_height_node=filtered[
                'no_change_in_finalized_block_height_node'],
            validator_is_syncing=filtered['validator_is_syncing'],
            node_is_syncing=filtered['node_is_syncing'],
            not_active_in_session=filtered['not_active_in_session'],
            is_disabled=filtered['is_disabled'],
            not_elected=filtered['not_elected'],
            bonded_amount_change=filtered['bonded_amount_change'],
            no_heartbeat_did_not_author_block=filtered[
                'no_heartbeat_did_not_author_block'],
            offline=filtered['offline'],
            slashed=filtered['slashed'],
            payout_not_claimed=filtered['payout_not_claimed'],
            controller_address_change=filtered['controller_address_change'],
        )

        self._configs[chain_name] = substrate_node_alerts_config


class SubstrateNetworkAlertsConfigsFactory(SubstrateAlertsConfigsFactory):
    """
    This class manages the network alerts configs. The configs are indexed by
    the chain name, and it is expected that each chain has exactly one alerts
    config.
    NOTE: This class will only manage the Substrate Network alerts residing in
          Substrate chains' alerts_config.ini.
    """

    def __init__(self) -> None:
        super().__init__()

    def add_new_config(self, chain_name: str, sent_configs: Dict) -> None:
        # Check if all the parent_ids in the received configuration are the
        # same, if not there is some misconfiguration.
        parent_ids = {
            configuration['parent_id']
            for configuration in sent_configs.values()
        }
        if len(parent_ids) != 1:
            raise ParentIdsMissMatchInAlertsConfiguration(
                "{}: add_new_config".format(self))

        filtered = {
            config['name']: copy.deepcopy(config)
            for config in sent_configs.values()
        }

        substrate_network_alerts_config = SubstrateNetworkAlertsConfig(
            parent_id=parent_ids.pop(),
            grandpa_is_stalled=filtered['grandpa_is_stalled'],
            new_proposal=filtered['new_proposal'],
            new_referendum=filtered['new_referendum'],
            referendum_concluded=filtered['referendum_concluded'],
        )

        self._configs[chain_name] = substrate_network_alerts_config
