from datetime import datetime
from typing import Optional, Dict, List, Union

from schema import Schema, Or

from src.monitorables.nodes.node import Node
from src.utils.exceptions import InvalidDictSchemaException


class ChainlinkNode(Node):
    def __init__(self, node_name: str, node_id: str, parent_id: str) -> None:
        super().__init__(node_name, node_id, parent_id)

        # Metrics
        self._went_down_at_prometheus = None
        self._current_height = None
        self._total_block_headers_received = None
        self._max_pending_tx_delay = None
        self._process_start_time_seconds = None
        self._total_gas_bumps = None
        self._total_gas_bumps_exceeds_limit = None
        self._no_of_unconfirmed_txs = None
        self._total_errored_job_runs = None
        self._current_gas_price_info = {
            'percentile': None,
            'price': None,
        }
        self._eth_balance_info = {}

        # This variable stores the url of the source used to get prometheus node
        # data. Note that this had to be done because multiple prometheus
        # sources can be associated with the same node, where at the same time
        # only one source is available, and sources switch from time to time.
        self._last_prometheus_source_used = None

        # This stores the timestamp of the last successful monitoring round.
        self._last_monitored_prometheus = None

    @property
    def is_down_prometheus(self) -> bool:
        return self._went_down_at_prometheus is not None

    @property
    def went_down_at_prometheus(self) -> Optional[float]:
        return self._went_down_at_prometheus

    @property
    def current_height(self) -> Optional[int]:
        return self._current_height

    @property
    def total_block_headers_received(self) -> Optional[int]:
        return self._total_block_headers_received

    @property
    def max_pending_tx_delay(self) -> Optional[int]:
        return self._max_pending_tx_delay

    @property
    def process_start_time_seconds(self) -> Optional[float]:
        return self._process_start_time_seconds

    @property
    def total_gas_bumps(self) -> Optional[int]:
        return self._total_gas_bumps

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
    def eth_balance_info(self) -> Dict[str, Union[str, float]]:
        return self._eth_balance_info

    @property
    def last_prometheus_source_used(self) -> Optional[str]:
        return self._last_prometheus_source_used

    @property
    def last_monitored_prometheus(self) -> Optional[float]:
        return self._last_monitored_prometheus

    @staticmethod
    def get_int_prometheus_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing integer prometheus
               : metrics.
        """
        return [
            'current_height',
            'total_block_headers_received',
            'max_pending_tx_delay', 'total_gas_bumps',
            'total_gas_bumps_exceeds_limit', 'no_of_unconfirmed_txs',
            'total_errored_job_runs'
        ]

    @staticmethod
    def get_float_prometheus_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing float prometheus
               : metrics.
        """
        return [
            'went_down_at_prometheus', 'process_start_time_seconds',
            'last_monitored_prometheus'
        ]

    @staticmethod
    def get_dict_prometheus_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing dict prometheus
               : metrics.
        """
        return ['current_gas_price_info', 'eth_balance_info']

    @staticmethod
    def get_str_prometheus_metric_attributes() -> List[str]:
        """
        :return: A list of all variable names representing string prometheus
               : metrics.
        """
        return ['last_prometheus_source_used']

    def get_all_prometheus_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing prometheus metrics
        """
        str_prometheus_metric_attributes = \
            self.get_str_prometheus_metric_attributes()
        int_prometheus_metric_attributes = \
            self.get_int_prometheus_metric_attributes()
        float_prometheus_metric_attributes = \
            self.get_float_prometheus_metric_attributes()
        dict_prometheus_metric_attributes = \
            self.get_dict_prometheus_metric_attributes()
        return [
            *str_prometheus_metric_attributes,
            *int_prometheus_metric_attributes,
            *float_prometheus_metric_attributes,
            *dict_prometheus_metric_attributes
        ]

    def get_int_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing int metrics.
        """
        int_prometheus_metric_attributes = \
            self.get_int_prometheus_metric_attributes()
        return [*int_prometheus_metric_attributes]

    def get_float_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing float metrics.
        """
        float_prometheus_metric_attributes = \
            self.get_float_prometheus_metric_attributes()
        return [*float_prometheus_metric_attributes]

    def get_dict_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing dict metrics.
        """
        dict_prometheus_metric_attributes = \
            self.get_dict_prometheus_metric_attributes()
        return [*dict_prometheus_metric_attributes]

    def get_str_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing str metrics.
        """
        str_prometheus_metric_attributes = \
            self.get_str_prometheus_metric_attributes()
        return [*str_prometheus_metric_attributes]

    def get_all_metric_attributes(self) -> List[str]:
        """
        :return: A list of all variable names representing metrics
        """
        prometheus_metric_attributes = \
            self.get_all_prometheus_metric_attributes()
        return [*prometheus_metric_attributes]

    def set_went_down_at_prometheus(
            self, went_down_at_prometheus: Optional[float]) -> None:
        self._went_down_at_prometheus = went_down_at_prometheus

    def set_prometheus_as_down(self, downtime: Optional[float]) -> None:
        """
        This function sets the node's prometheus interface as down. It sets the
        time that the interface was initially down to the parameter 'downtime'
        if it is not None, otherwise it sets it to the current timestamp.
        :param downtime:
        :return:
        """
        if downtime is None:
            self.set_went_down_at_prometheus(datetime.now().timestamp())
        else:
            self.set_went_down_at_prometheus(downtime)

    def set_prometheus_as_up(self) -> None:
        """
        This function sets a node's prometheus interface as up. A node's
        interface is said to be up if went_down_at_prometheus is None.
        :return: None
        """
        self.set_went_down_at_prometheus(None)

    def set_current_height(self, new_height: Optional[int]) -> None:
        self._current_height = new_height

    def set_total_block_headers_received(
            self, new_total_block_headers_received: Optional[int]) -> None:
        self._total_block_headers_received = new_total_block_headers_received

    def set_max_pending_tx_delay(
            self, new_max_pending_tx_delay: Optional[int]) -> None:
        self._max_pending_tx_delay = new_max_pending_tx_delay

    def set_process_start_time_seconds(
            self, new_process_start_time_seconds: Optional[float]) -> None:
        self._process_start_time_seconds = new_process_start_time_seconds

    def set_total_gas_bumps(self, new_total_gas_bumps: Optional[int]) -> None:
        self._total_gas_bumps = new_total_gas_bumps

    def set_total_gas_bumps_exceeds_limit(
            self, new_total_gas_bumps_exceeds_limit: Optional[int]) -> None:
        self._total_gas_bumps_exceeds_limit = new_total_gas_bumps_exceeds_limit

    def set_no_of_unconfirmed_txs(
            self, new_no_of_unconfirmed_txs: Optional[int]) -> None:
        self._no_of_unconfirmed_txs = new_no_of_unconfirmed_txs

    def set_total_errored_job_runs(
            self, new_total_errored_job_runs: Optional[int]) -> None:
        self._total_errored_job_runs = new_total_errored_job_runs

    def set_current_gas_price_info(self, new_percentile: Optional[float],
                                   new_price: Optional[float]) -> None:
        """
        This method sets the current_gas_price_info dict based on the new
        percentile and price. This is done in this way to protect the Dict
        schema.
        :param new_percentile: The new percentile to be stored
        :param new_price: The new gas to be stored
        :return: None
        """
        self._current_gas_price_info['percentile'] = new_percentile
        self._current_gas_price_info['price'] = new_price

    @staticmethod
    def _new_eth_balance_info_valid(new_eth_balance_info: Dict) -> bool:
        """
        This method checks that the new eth_balance_info dict obeys the required
        schema.
        :param new_eth_balance_info: The dict to check
        :return: True if the dict obeys the required schema
               : False otherwise
        """
        schema = Schema(Or({
            'address': str,
            'balance': float,
            'latest_usage': float,
        }, {}))
        return schema.is_valid(new_eth_balance_info)

    def set_eth_balance_info(
            self, new_eth_balance_info: Dict[str, Union[str, float]]) -> None:
        """
        This method sets the new_eth_balance_info. It first checks that the new
        dict obeys the required schema. If not, an InvalidDictSchemaException is
        raised.
        :param new_eth_balance_info: The new eth_balance_info to store. 
        :return: None
        """""
        if self._new_eth_balance_info_valid(new_eth_balance_info):
            self._eth_balance_info = new_eth_balance_info
        else:
            raise InvalidDictSchemaException('new_eth_balance_info')

    def set_last_prometheus_source_used(
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
        self.set_went_down_at_prometheus(None)
        self.set_current_height(None)
        self.set_total_block_headers_received(None)
        self.set_max_pending_tx_delay(None)
        self.set_process_start_time_seconds(None)
        self.set_total_gas_bumps(None)
        self.set_total_gas_bumps_exceeds_limit(None)
        self.set_no_of_unconfirmed_txs(None)
        self.set_total_errored_job_runs(None)
        self.set_current_gas_price_info(None, None)
        self.set_eth_balance_info({})
        self.set_last_prometheus_source_used(None)
        self.set_last_monitored_prometheus(None)
