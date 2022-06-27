from typing import Dict, Any


class SubstrateNodeAlertsConfig:
    def __init__(
            self, parent_id: str, cannot_access_validator: Dict,
            cannot_access_node: Dict,
            no_change_in_best_block_height_validator: Dict,
            no_change_in_best_block_height_node: Dict,
            no_change_in_finalized_block_height_validator: Dict,
            no_change_in_finalized_block_height_node: Dict,
            validator_is_syncing: Dict, node_is_syncing: Dict,
            not_active_in_session: Dict, is_disabled: Dict, not_elected: Dict,
            bonded_amount_change: Dict, no_heartbeat_did_not_author_block: Dict,
            offline: Dict, slashed: Dict, payout_not_claimed: Dict,
            controller_address_change: Dict
    ) -> None:
        self._parent_id = parent_id
        self._cannot_access_validator = cannot_access_validator
        self._cannot_access_node = cannot_access_node
        self._no_change_in_best_block_height_validator = (
            no_change_in_best_block_height_validator)
        self._no_change_in_best_block_height_node = (
            no_change_in_best_block_height_node)
        self._no_change_in_finalized_block_height_validator = (
            no_change_in_finalized_block_height_validator)
        self._no_change_in_finalized_block_height_node = (
            no_change_in_finalized_block_height_node)
        self._validator_is_syncing = validator_is_syncing
        self._node_is_syncing = node_is_syncing
        self._not_active_in_session = not_active_in_session
        self._is_disabled = is_disabled
        self._not_elected = not_elected
        self._bonded_amount_change = bonded_amount_change
        self._no_heartbeat_did_not_author_block = (
            no_heartbeat_did_not_author_block)
        self._offline = offline
        self._slashed = slashed
        self._payout_not_claimed = payout_not_claimed
        self._controller_address_change = controller_address_change

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
    def no_change_in_best_block_height_validator(self) -> Dict:
        return self._no_change_in_best_block_height_validator

    @property
    def no_change_in_best_block_height_node(self) -> Dict:
        return self._no_change_in_best_block_height_node

    @property
    def no_change_in_finalized_block_height_validator(self) -> Dict:
        return self._no_change_in_finalized_block_height_validator

    @property
    def no_change_in_finalized_block_height_node(self) -> Dict:
        return self._no_change_in_finalized_block_height_node

    @property
    def validator_is_syncing(self) -> Dict:
        return self._validator_is_syncing

    @property
    def node_is_syncing(self) -> Dict:
        return self._node_is_syncing

    @property
    def not_active_in_session(self) -> Dict:
        return self._not_active_in_session

    @property
    def is_disabled(self) -> Dict:
        return self._is_disabled

    @property
    def not_elected(self) -> Dict:
        return self._not_elected

    @property
    def bonded_amount_change(self) -> Dict:
        return self._bonded_amount_change

    @property
    def no_heartbeat_did_not_author_block(self) -> Dict:
        return self._no_heartbeat_did_not_author_block

    @property
    def offline(self) -> Dict:
        return self._offline

    @property
    def slashed(self) -> Dict:
        return self._slashed

    @property
    def payout_not_claimed(self) -> Dict:
        return self._payout_not_claimed

    @property
    def controller_address_change(self) -> Dict:
        return self._controller_address_change
