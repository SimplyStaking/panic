from typing import Optional

from src.monitorables.nodes.node import Node


class ChainlinkNode(Node):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        super().__init__(node_name, node_id, parent_id)

        # Metrics
        self._went_down_at = None
        self._current_height = None
        self._eth_blocks_in_queue = None
        self._total_block_headers_received = None
        self._total_block_headers_dropped = None
        self._no_of_active_jobs = None
        self._max_pending_transaction_delay = None
        self._process_start_time_seconds = None
        self._total_tx_gas_bumps = None
        self._total_gas_bumps_exceeds_limit = None
        self._no_of_unconfirmed_txs = None
        self._total_errored_job_runs = None
        self._current_gas_price = None
        self._eth_balance = None

        # Some meta-data
        self._last_prometheus_source_used = None
        self._last_monitored = None

        # TODO: In redis store entire dicts
        # TODO: current_gas_price store as it is
        # TODO: For eth_balance also store this dict:
        #     : { balance: Z, average_usage_hour: U, historical_usage_hour: [{timestamp: X, usage: Y}] }
        #     : Intervals of 5 mins. When balance comes, store it in balance .. calculate difference
        #     : from old and store in historical usage. Note that on top-up we set the data to zero
        #     : not to negative.
        # TODO: Set methods must be done according to how we are going to store
        #     : the data as dicts. For eth balance we need to do one for the
        #     : balance and one for the usage.

    @property
    def is_down(self) -> bool:
        return self._went_down_at is not None

    @property
    def went_down_at(self) -> Optional[float]:
        return self._went_down_at

    @property
    def current_height(self) -> Optional[int]:
        return self._current_height

    @property
    def eth_blocks_in_queue(self) -> Optional[int]:
        return self._eth_blocks_in_queue

    @property
    def total_block_headers_received(self) -> Optional[int]:
        return self._total_block_headers_received

    @property
    def total_block_headers_dropped(self) -> Optional[int]:
        return self._total_block_headers_dropped

    @property
    def no_of_active_jobs(self) -> Optional[int]:
        return self._no_of_active_jobs

    @property
    def max_pending_tansaction_delay(self) -> Optional[int]:
        return self._max_pending_transaction_delay

    @property
    def process_start_time_seconds(self) -> Optional[float]:
        return self._process_start_time_seconds

    @property
    def total_tx_gas_bumps(self) -> Optional[int]:
        return self._total_tx_gas_bumps

    @property
    def total_gas_bumps_exceeds_limit(self) -> Optional[int]:
        return self._total_gas_bumps_exceeds_limit

    @property
    def no_of_unconfirmed_txs(self) -> Optional[int]:
        return self._no_of_unconfirmed_txs

    @property
    def total_errored_job_runs(self) -> Optional[int]:
        return self._total_errored_job_runs

    """
        TODO
        self._current_gas_price = None
        self._eth_balance = None

        # Some meta-data
        self._last_prometheus_source_used = None
        self._last_monitored = None
    """


    def reset(self) -> None:
        """
        This method resets all metrics to their initial state
        :return: None
        """
        pass
