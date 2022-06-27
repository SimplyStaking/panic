import copy
from typing import Dict, Optional

from src.configs.alerts.node.evm import EVMNodeAlertsConfig
from src.configs.factory.configs_factory import ConfigsFactory
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class EVMNodeAlertsConfigsFactory(ConfigsFactory):
    """
    This class manages the alerts configs. The configs are indexed by the
    chain name, and it is expected that each chain has exactly one alerts
    config. NOTE: This class will only manage the EVM alerts residing in
    Chainlink chains' alerts_config.ini.
    """

    def __init__(self) -> None:
        super().__init__()

    def add_new_config(self, chain_name: str, sent_configs: Dict) -> None:
        # Check if all the parent_ids in the received configuration are the
        # same, if not there is some misconfiguration
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

        evm_node_alerts_config = EVMNodeAlertsConfig(
            parent_id=parent_ids.pop(),
            evm_node_is_down=filtered['evm_node_is_down'],
            evm_block_syncing_block_height_difference=filtered[
                'evm_block_syncing_block_height_difference'],
            evm_block_syncing_no_change_in_block_height=filtered[
                'evm_block_syncing_no_change_in_block_height']
        )

        self._configs[chain_name] = evm_node_alerts_config

    def remove_config(self, chain_name: str) -> None:
        if chain_name in self.configs:
            del self._configs[chain_name]

    def config_exists(self, chain_name: str) -> bool:
        """
        This function returns True if a configuration exists for a chain name.
        :param chain_name: The name of the chain in question
        :return: True if config exists
               : False otherwise
        """
        return (chain_name in self.configs
                and type(self.configs[chain_name]) == EVMNodeAlertsConfig)

    def get_parent_id(self, chain_name: str) -> Optional[str]:
        """
        This function returns the parent_id of a chain whose name is chain_name.
        :param chain_name: The name of the chain in question
        :return: The parent_id of the chain if chain_name in self.configs
               : None otherwise
        """
        if self.config_exists(chain_name):
            return self.configs[chain_name].parent_id
        else:
            return None

    def get_chain_name(self, parent_id: str) -> Optional[str]:
        """
        This function returns the chain name associated with the id.
        :param parent_id: The id of the chain in question
        :return: The name of the chain if there is a config having the given
               : parent_id
               : None otherwise
        """
        for chain_name, config in self.configs.items():
            if type(config) == EVMNodeAlertsConfig \
                    and config.parent_id == parent_id:
                return chain_name

        return None
