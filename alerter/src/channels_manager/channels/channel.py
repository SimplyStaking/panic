# TODO: Handle sending exceptions in individual handlers and log errors. Also
#     : no backup channels, and add the alert to the sending queue in the
#     : handler

# TODO: We should infer the severity from the alert, and we must provide
#     : error handling of whether the alert was sent etc in the respective
#     : channels (also log there).

import logging
from abc import ABC, abstractmethod

from src.alerter.alerts.alert import Alert
from enum import Enum


class RequestStatus(Enum):
    SUCCESS = True
    FAILED = False


class Channel(ABC):
    def __init__(self, channel_name: str, logger: logging.Logger) -> None:
        self._channel_name = channel_name
        self._logger = logger

    def __str__(self) -> str:
        return self.channel_name

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abstractmethod
    def alert(self, alert: Alert) -> RequestStatus:
        pass
