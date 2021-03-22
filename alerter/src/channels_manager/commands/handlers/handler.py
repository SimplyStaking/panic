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
    def start_callback(self, *args) -> None:
        pass

    @abstractmethod
    def help_callback(self, *args) -> None:
        pass

    @abstractmethod
    def mute_callback(self, *args) -> None:
        pass

    @abstractmethod
    def muteall_callback(self, *args) -> None:
        pass

    @abstractmethod
    def unmuteall_callback(self, *args) -> None:
        pass

    @abstractmethod
    def unmute_callback(self, *args) -> None:
        pass

    @abstractmethod
    def status_callback(self, *args) -> None:
        pass

    @abstractmethod
    def ping_callback(self, *args) -> None:
        pass

    @abstractmethod
    def unknown_callback(self, *args) -> None:
        pass
