from abc import abstractmethod, ABC
from typing import Any, Dict, List, Optional

from src.utils.exceptions import InvalidDictSchemaException

# todo: store proxy and aggrtergator address .. aggregator address can change,
#     : proxy no, version can change also and we need to cater for this in the
#     : transformer


class Contract(ABC):
    def __init__(self, address: str, version: int) -> None:
        self._address = address
        self._version = version
        self._latest_round = None
        self._latest_answer = None
        self._latest_timestamp = None
        self._answered_in_round = None
        self._historical_rounds = []

    def __str__(self) -> str:
        return self._address

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def address(self) -> str:
        return self._address

    @property
    def version(self) -> int:
        return self._version

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

    def set_latest_round(self, latest_round: Optional[int]) -> None:
        self._latest_round = latest_round

    def set_latest_answer(self, latest_answer: Optional[int]) -> None:
        self._latest_answer = latest_answer

    def set_latest_timestamp(self, latest_timestamp: Optional[float]) -> None:
        self._latest_timestamp = latest_timestamp

    def set_answered_in_round(self, answered_in_round: Optional[int]) -> None:
        self._answered_in_round = answered_in_round

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

    @abstractmethod
    def reset(self) -> None:
        pass
