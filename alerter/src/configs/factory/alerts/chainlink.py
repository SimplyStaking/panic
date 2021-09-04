import copy
from typing import Dict, Optional

from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.configs.factory.configs_factory import ConfigsFactory
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class ChainlinkAlertsConfigsFactory(ConfigsFactory):
    """
    This class manages the alerts configs. The configs are indexed by the
    chain name, and it is expected that each chain has exactly one alerts
    config. NOTE: This class does not manage the EVM alerts residing in
    Chainlink chains' alerts_config.ini
    """

    def __init__(self) -> None:
        super().__init__()

    def add_new_config(self, chain_name: str, sent_configs: Dict) -> None:
        # Check if all the parent_ids in the received configuration are the
        # same, if not there is some misconfiguration
        parent_id = sent_configs['1']['parent_id']
        for _, config in sent_configs.items():
            if parent_id != config['parent_id']:
                raise ParentIdsMissMatchInAlertsConfiguration(
                    "{}: _process_configs".format(self))

        filtered = {}
        for _, config in sent_configs.items():
            filtered[config['name']] = copy.deepcopy(config)

        cl_node_alerts_config = ChainlinkNodeAlertsConfig(
            parent_id=parent_id,
            head_tracker_current_head=filtered[
                'head_tracker_current_head'],
            head_tracker_heads_received_total=filtered[
                'head_tracker_heads_received_total'],
            max_unconfirmed_blocks=filtered['max_unconfirmed_blocks'],
            process_start_time_seconds=filtered[
                'process_start_time_seconds'],
            tx_manager_gas_bump_exceeds_limit_total=filtered[
                'tx_manager_gas_bump_exceeds_limit_total'],
            unconfirmed_transactions=filtered[
                'unconfirmed_transactions'],
            run_status_update_total=filtered['run_status_update_total'],
            eth_balance_amount=filtered['eth_balance_amount'],
            eth_balance_amount_increase=filtered[
                'eth_balance_amount_increase'],
            node_is_down=filtered['node_is_down']
        )

        self._configs[chain_name] = cl_node_alerts_config

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
                and type(self.configs[chain_name]) == ChainlinkNodeAlertsConfig)

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
            if type(config) == ChainlinkNodeAlertsConfig \
                    and config.parent_id == parent_id:
                return chain_name

        return None
