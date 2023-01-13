from typing import Dict, Any


class CosmosNodeAlertsConfig:
    def __init__(
            self, parent_id: str, cannot_access_validator: Dict,
            cannot_access_node: Dict, validator_not_active_in_session: Dict,
            no_change_in_block_height_validator: Dict,
            no_change_in_block_height_node: Dict, block_height_difference: Dict,
            cannot_access_prometheus_validator: Dict,
            cannot_access_prometheus_node: Dict,
            cannot_access_cosmos_rest_validator: Dict,
            cannot_access_cosmos_rest_node: Dict,
            cannot_access_tendermint_rpc_validator: Dict,
            cannot_access_tendermint_rpc_node: Dict, missed_blocks: Dict,
            slashed: Dict, node_is_syncing: Dict, validator_is_syncing: Dict, validator_is_jailed: Dict,
            node_is_peered_with_sentinel: Dict = None, validator_is_peered_with_sentinel: Dict = None,
            ) -> None:
        self._parent_id = parent_id
        self._cannot_access_validator = cannot_access_validator
        self._cannot_access_node = cannot_access_node
        self._validator_not_active_in_session = validator_not_active_in_session
        self._no_change_in_block_height_validator = (
            no_change_in_block_height_validator)
        self._no_change_in_block_height_node = no_change_in_block_height_node
        self._block_height_difference = block_height_difference
        self._cannot_access_prometheus_validator = (
            cannot_access_prometheus_validator)
        self._cannot_access_prometheus_node = cannot_access_prometheus_node
        self._cannot_access_cosmos_rest_validator = (
            cannot_access_cosmos_rest_validator)
        self._cannot_access_cosmos_rest_node = cannot_access_cosmos_rest_node
        self._cannot_access_tendermint_rpc_validator = (
            cannot_access_tendermint_rpc_validator)
        self._cannot_access_tendermint_rpc_node = (
            cannot_access_tendermint_rpc_node)
        self._missed_blocks = missed_blocks
        self._slashed = slashed
        self._node_is_syncing = node_is_syncing
        self._validator_is_syncing = validator_is_syncing
        self._validator_is_jailed = validator_is_jailed
        self._node_is_peered_with_sentinel = node_is_peered_with_sentinel
        self._validator_is_peered_with_sentinel = validator_is_peered_with_sentinel

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def cannot_access_validator(self) -> Dict:
        return self._cannot_access_validator

    @property
    def cannot_access_node(self) -> Dict:
        return self._cannot_access_node

    @property
    def validator_not_active_in_session(self) -> Dict:
        return self._validator_not_active_in_session

    @property
    def no_change_in_block_height_validator(self) -> Dict:
        return self._no_change_in_block_height_validator

    @property
    def no_change_in_block_height_node(self) -> Dict:
        return self._no_change_in_block_height_node

    @property
    def block_height_difference(self) -> Dict:
        return self._block_height_difference

    @property
    def cannot_access_prometheus_validator(self) -> Dict:
        return self._cannot_access_prometheus_validator

    @property
    def cannot_access_prometheus_node(self) -> Dict:
        return self._cannot_access_prometheus_node

    @property
    def cannot_access_cosmos_rest_validator(self) -> Dict:
        return self._cannot_access_cosmos_rest_validator

    @property
    def cannot_access_cosmos_rest_node(self) -> Dict:
        return self._cannot_access_cosmos_rest_node

    @property
    def cannot_access_tendermint_rpc_validator(self) -> Dict:
        return self._cannot_access_tendermint_rpc_validator

    @property
    def cannot_access_tendermint_rpc_node(self) -> Dict:
        return self._cannot_access_tendermint_rpc_node

    @property
    def missed_blocks(self) -> Dict:
        return self._missed_blocks

    @property
    def slashed(self) -> Dict:
        return self._slashed

    @property
    def node_is_syncing(self) -> Dict:
        return self._node_is_syncing

    @property
    def validator_is_syncing(self) -> Dict:
        return self._validator_is_syncing

    @property
    def node_is_peered_with_sentinel(self) -> Dict:
        return self._node_is_peered_with_sentinel

    @property
    def validator_is_peered_with_sentinel(self) -> Dict:
        return self._validator_is_peered_with_sentinel

    @property
    def validator_is_jailed(self) -> Dict:
        return self._validator_is_jailed
