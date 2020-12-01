import logging
from abc import ABC, abstractmethod


class CommandHandler(ABC):

    def __init__(self, handler_name: str, logger: logging.Logger) -> None:
        self._logger = logger
        self._handler_name = handler_name

    def __str__(self) -> str:
        return self.handler_name

    @property
    def handler_name(self) -> str:
        return self._handler_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abstractmethod
    def start_callback(self) -> None:
        pass

    @abstractmethod
    def help_callback(self) -> None:
        pass

    @abstractmethod
    def mute_callback(self) -> None:
        pass

    @abstractmethod
    def unmute_callback(self) -> None:
        pass

    @abstractmethod
    def snooze_callback(self) -> None:
        pass

    @abstractmethod
    def unsnooze_callback(self) -> None:
        pass

    @abstractmethod
    def health_callback(self) -> None:
        pass

    @abstractmethod
    def ping_callback(self) -> None:
        pass

    @abstractmethod
    def unknown_callback(self) -> None:
        pass
