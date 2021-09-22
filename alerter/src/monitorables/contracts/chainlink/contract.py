from abc import abstractmethod, ABC
from typing import Any, Dict, List, Optional

from src.utils.exceptions import InvalidDictSchemaException


class ChainlinkContract(ABC):
    def __init__(self, proxy_address: str, aggregator_address: str,
                 version: int, parent_id: str, node_id: str) -> None:
        self._proxy_address = proxy_address
        self._aggregator_address = aggregator_address
        self._version = version
        self._parent_id = parent_id
        self._node_id = node_id  # The id of the chainlink node
        self._latest_round = None
        self._latest_answer = None
        self._latest_timestamp = None
        self._answered_in_round = None
        self._historical_rounds = []

        """
        _last_round_observed: This is a custom metric extrapolated from
        historical rounds. This is used to aid in alerting on missed price
        feed observations.
        """
        self._last_round_observed = None
        # This stores the timestamp of the last successful monitoring round.
        self._last_monitored = None

    def __str__(self) -> str:
        return self._proxy_address

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def proxy_address(self) -> str:
        return self._proxy_address

    @property
    def aggregator_address(self) -> str:
        return self._aggregator_address

    @property
    def version(self) -> int:
        return self._version

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def latest_round(self) -> Optional[int]:
        return self._latest_round

    @property
    def latest_answer(self) -> Optional[int]:
        return self._latest_answer

    @property
    def latest_timestamp(self) -> Optional[float]:
        return self._latest_timestamp

    @property
    def answered_in_round(self) -> Optional[int]:
        return self._answered_in_round

    @property
    def historical_rounds(self) -> List[Dict]:
        return self._historical_rounds

    @property
    def last_round_observed(self) -> Optional[int]:
        return self._last_round_observed

    @property
    def last_monitored(self) -> Optional[float]:
        return self._last_monitored

    def set_aggregator_address(self, aggregator_address: str) -> None:
        self._aggregator_address = aggregator_address

    def set_parent_id(self, parent_id: str) -> None:
        self._parent_id = parent_id

    def set_node_id(self, node_id: str) -> None:
        self._node_id = node_id

    def set_latest_round(self, latest_round: Optional[int]) -> None:
        self._latest_round = latest_round

    def set_latest_answer(self, latest_answer: Optional[int]) -> None:
        self._latest_answer = latest_answer

    def set_latest_timestamp(self, latest_timestamp: Optional[float]) -> None:
        self._latest_timestamp = latest_timestamp

    def set_answered_in_round(self, answered_in_round: Optional[int]) -> None:
        self._answered_in_round = answered_in_round

    def set_last_round_observed(self,
                                last_round_observed: Optional[int]) -> None:
        self._last_round_observed = last_round_observed

    @abstractmethod
    def historical_rounds_valid(self,
                                new_historical_rounds: List[Dict]) -> bool:
        pass

    def set_historical_rounds(self, historical_rounds: List[Dict]) -> None:
        """
        This function attempts to set historical_rounds only if it obeys the
        required schema. If the schema is not obeyed, then an
        InvalidDictSchemaException is raised by the function. The schema obeyed
        by historical rounds is different for each contract type.
        :param historical_rounds: The new value to be set
        :return: None
        """
        if self.historical_rounds_valid(historical_rounds):
            self._historical_rounds = historical_rounds
        else:
            raise InvalidDictSchemaException('historical_rounds')

    def set_last_monitored(self, last_monitored: Optional[float]) -> None:
        self._last_monitored = last_monitored

    @abstractmethod
    def reset(self) -> None:
        pass
