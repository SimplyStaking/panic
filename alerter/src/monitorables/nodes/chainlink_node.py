from datetime import datetime
from typing import Optional, Dict, Union, List

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
        self._max_pending_tx_delay = None
        self._process_start_time_seconds = None
        self._total_tx_gas_bumps = None
        self._total_gas_bumps_exceeds_limit = None
        self._no_of_unconfirmed_txs = None
        self._total_errored_job_runs = None
        self._current_gas_price_info = {
            'percentile': None,
            'price': None,
        }
        self._eth_balance_info = {}

        # Some meta-data
        self._last_prometheus_source_used = None
        self._last_monitored_prometheus = None

        # TODO: In redis store entire dicts
        # TODO: current_gas_price store as it is
        # TODO: For eth_balance also store this dict:
        #     : { balance: Z, average_usage_hour: U, historical_usage_hour: [{timestamp: X, usage: Y}] }
        #     : Intervals of 5 mins. When balance comes, store it in balance .. calculate difference
        #     : from old and store in historical usage. Note that on top-up we set the data to zero
        #     : not to negative, or do not set any data.
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
    def max_pending_tx_delay(self) -> Optional[int]:
        return self._max_pending_tx_delay

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

    @property
    def current_gas_price_info(self) -> Dict[str, Optional[float]]:
        return self._current_gas_price_info

    @property
    def eth_balance_info(self) \
            -> Dict[str, Dict[str, Union[float, List[Dict[str, float]]]]]:
        return self._eth_balance_info

    def get_eth_balance(self, eth_address: str) -> Optional[float]:
        if eth_address in self._eth_balance_info:
            return self._eth_balance_info[eth_address]['balance']
        else:
            return None

    def get_average_usage_hour(self, eth_address: str) -> Optional[float]:
        if eth_address in self._eth_balance_info:
            return self._eth_balance_info[eth_address]['average_usage_hour']
        else:
            return None

    @property
    def get_last_prometheus_source_used(self) -> Optional[str]:
        return self._last_prometheus_source_used

    @property
    def last_monitored_prometheus(self) -> Optional[float]:
        return self._last_monitored_prometheus

    def set_went_down_at(self, went_down_at: Optional[float]) -> None:
        self._went_down_at = went_down_at

    def set_as_down(self, downtime: Optional[float]) -> None:
        if downtime is None:
            self.set_went_down_at(datetime.now().timestamp())
        else:
            self.set_went_down_at(downtime)

    def set_as_up(self) -> None:
        self.set_went_down_at(None)

    def set_current_height(self, new_height: Optional[int]) -> None:
        self._current_height = new_height

    def set_eth_blocks_in_queue(
            self, new_eth_blocks_in_queue: Optional[int]) -> None:
        self._eth_blocks_in_queue = new_eth_blocks_in_queue

    def set_total_block_headers_received(
            self, new_total_block_headers_received: Optional[int]) -> None:
        self._total_block_headers_received = new_total_block_headers_received

    def set_total_block_headers_dropped(
            self, new_total_block_headers_dropped: Optional[int]) -> None:
        self._total_block_headers_dropped = new_total_block_headers_dropped

    def set_no_of_active_jobs(
            self, new_no_of_active_jobs: Optional[int]) -> None:
        self._no_of_active_jobs = new_no_of_active_jobs

    def set_max_pending_tx_delay(
            self, new_max_pending_tx_delay: Optional[int]) -> None:
        self._max_pending_tx_delay = new_max_pending_tx_delay

    def set_process_start_time_seconds(
            self, new_process_start_time_seconds: Optional[float]) -> None:
        self._process_start_time_seconds = new_process_start_time_seconds

    def set_total_tx_gas_bumps(
            self, new_total_tx_gas_bumps: Optional[int]) -> None:
        self._total_tx_gas_bumps = new_total_tx_gas_bumps

    def set_total_gas_bumps_exceeds_limit(
            self, new_total_gas_bumps_exceeds_limit: Optional[int]) -> None:
        self._total_gas_bumps_exceeds_limit = new_total_gas_bumps_exceeds_limit

    def set_no_of_unconfirmed_txs(
            self, new_no_of_unconfirmed_txs: Optional[int]) -> None:
        self._no_of_unconfirmed_txs = new_no_of_unconfirmed_txs

    def set_total_errored_jobs_runs(
            self, new_total_errored_jobs_runs: Optional[int]) -> None:
        self._total_errored_job_runs = new_total_errored_jobs_runs

    def set_current_gas_price_info(self, new_percentile: Optional[float],
                                   new_price: Optional[float]) -> None:
        self._current_gas_price_info['percentile'] = new_percentile
        self._current_gas_price_info['price'] = new_price

    @staticmethod
    def _new_eth_balance_info_valid(new_eth_balance_info: Dict) -> bool:
        if new_eth_balance_info == {}:
            return True

        if not ('balance' in new_eth_balance_info
                and isinstance(new_eth_balance_info['balance'], float)):
            return False

        if not ('average_usage_hour' in new_eth_balance_info
                and isinstance(new_eth_balance_info['average_usage_hour'],
                               float)):
            return False

        if 'historical_usage_hour' in new_eth_balance_info and isinstance(
                new_eth_balance_info['historical_usage_hour'], List):
            for historical_data in \
                    new_eth_balance_info['historical_usage_hour']:
                if not isinstance(historical_data, Dict):
                    return False

                if not ('timestamp' in historical_data and isinstance(
                        historical_data['timestamp'], float)):
                    return False

                if not ('usage' in historical_data and isinstance(
                        historical_data['usage'], float)):
                    return False
        else:
            return False

        return True

    def set_eth_balance_info(
            self, new_eth_balance_info: Dict[str, Dict[str, Union[float, List[
                Dict[str, float]]]]]) -> None:
        if self._new_eth_balance_info_valid(new_eth_balance_info):
            self._eth_balance_info = new_eth_balance_info
        else:
            pass

        # TODO: Check if valid dict. If yes set it if not raise an error.
        pass

    def last_prometheus_source_used(
            self, new_last_prometheus_source_used: Optional[str]) -> None:
        self._last_prometheus_source_used = new_last_prometheus_source_used

    def set_last_monitored_prometheus(
            self, new_last_monitored_prometheus: Optional[float]) -> None:
        self._last_monitored_prometheus = new_last_monitored_prometheus

    def reset(self) -> None:
        """
        This method resets all metrics to their initial state
        :return: None
        """
        pass
