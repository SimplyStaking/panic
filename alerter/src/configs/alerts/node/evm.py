from typing import Dict, Any


class EVMAlertsConfigsFactory:
    def __init__(self, parent_id: str, evm_node_is_down: Dict,
                 evm_block_syncing_block_height_difference: Dict,
                 evm_block_syncing_no_change_in_block_height: Dict) -> None:
        self._parent_id = parent_id
        self._evm_node_is_down = evm_node_is_down
        self._evm_block_syncing_block_height_difference = \
            evm_block_syncing_block_height_difference
        self._evm_block_syncing_no_change_in_block_height = \
            evm_block_syncing_no_change_in_block_height

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def evm_node_is_down(self) -> Dict:
        return self._evm_node_is_down

    @property
    def evm_block_syncing_block_height_difference(self) -> Dict:
        return self._evm_block_syncing_block_height_difference

    @property
    def evm_block_syncing_no_change_in_block_height(self) -> Dict:
        return self._evm_block_syncing_no_change_in_block_height
