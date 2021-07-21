from typing import Dict, Any


class ChainlinkNodeAlertsConfig:
    def __init__(self, parent_id: str, head_tracker_current_head: Dict,
                 head_tracker_heads_in_queue: Dict,
                 head_tracker_heads_received_total: Dict,
                 head_tracker_num_heads_dropped_total: Dict,
                 max_unconfirmed_blocks: Dict,
                 process_start_time_seconds: Dict,
                 tx_manager_gas_bump_exceeds_limit_total: Dict,
                 unconfirmed_transactions: Dict,
                 run_status_update_total: Dict, eth_balance_amount: Dict,
                 eth_balance_amount_increase: Dict, node_is_down: Dict) -> None:
        self._parent_id = parent_id
        self._head_tracker_current_head = head_tracker_current_head
        self._head_tracker_heads_in_queue = head_tracker_heads_in_queue
        self._head_tracker_heads_received_total = \
            head_tracker_heads_received_total
        self._head_tracker_num_heads_dropped_total = \
            head_tracker_num_heads_dropped_total
        self._max_unconfirmed_blocks = max_unconfirmed_blocks
        self._process_start_time_seconds = process_start_time_seconds
        self._tx_manager_gas_bump_exceeds_limit_total = \
            tx_manager_gas_bump_exceeds_limit_total
        self._unconfirmed_transactions = unconfirmed_transactions
        self._run_status_update_total = run_status_update_total
        self._eth_balance_amount = eth_balance_amount
        self._eth_balance_amount_increase = eth_balance_amount_increase
        self._node_is_down = node_is_down

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def head_tracker_current_head(self) -> Dict:
        return self._head_tracker_current_head

    @property
    def head_tracker_heads_in_queue(self) -> Dict:
        return self._head_tracker_heads_in_queue

    @property
    def head_tracker_heads_received_total(self) -> Dict:
        return self._head_tracker_heads_received_total

    @property
    def head_tracker_num_heads_dropped_total(self) -> Dict:
        return self._head_tracker_num_heads_dropped_total

    @property
    def max_unconfirmed_blocks(self) -> Dict:
        return self._max_unconfirmed_blocks

    @property
    def process_start_time_seconds(self) -> Dict:
        return self._process_start_time_seconds

    @property
    def tx_manager_gas_bump_exceeds_limit_total(self) -> Dict:
        return self._tx_manager_gas_bump_exceeds_limit_total

    @property
    def unconfirmed_transactions(self) -> Dict:
        return self._unconfirmed_transactions

    @property
    def run_status_update_total(self) -> Dict:
        return self._run_status_update_total

    @property
    def eth_balance_amount(self) -> Dict:
        return self._eth_balance_amount

    @property
    def eth_balance_amount_increase(self) -> Dict:
        return self._eth_balance_amount_increase

    @property
    def node_is_down(self) -> Dict:
        return self._node_is_down
