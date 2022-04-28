import logging
from abc import ABC, abstractmethod
from typing import Any


class ApiWrapper(ABC):
    """
    This class acts as an abstract class for the API wrappers
    """

    def __init__(self, logger: logging.Logger, verify: bool = False,
                 timeout: int = 10) -> None:
        self._logger = logger
        self._verify = verify
        self._timeout = timeout

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def verify(self) -> bool:
        return self._verify

    @property
    def timeout(self) -> int:
        return self._timeout

    @abstractmethod
    def execute_with_checks(self, *args) -> Any:
        pass
