import logging
from abc import ABC, abstractmethod

from src.utils.data import RequestStatus


class Channel(ABC):
    def __init__(self, channel_name: str, channel_id: str,
                 logger: logging.Logger) -> None:
        self._channel_name = channel_name
        self._channel_id = channel_id
        self._logger = logger

    def __str__(self) -> str:
        return self.channel_name

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abstractmethod
    def alert(self, *args) -> RequestStatus:
        pass
