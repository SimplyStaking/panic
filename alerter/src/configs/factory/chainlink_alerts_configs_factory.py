import copy
from typing import Dict

from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.configs.factory.configs_factory import ConfigsFactory
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


class ChainlinkAlertsConfigsFactory(ConfigsFactory):
    """
    This class manages the alerts configs. The configs are indexed by the
    chain name, and it is expected that each chain has exactly one alerts
    config.
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
            parent_id=filtered['parent_id'],
            head_tracker_current_head=filtered[
                'head_tracker_current_head'],
            head_tracker_heads_in_queue=filtered[
                'head_tracker_heads_in_queue'],
            head_tracker_heads_received_total=filtered[
                'head_tracker_heads_received_total'],
            head_tracker_num_heads_dropped_total=filtered[
                'head_tracker_num_heads_dropped_total'],
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
