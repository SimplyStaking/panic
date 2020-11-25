import logging
from abc import ABC

from src.abstract import Component


class ChannelHandler(Component, ABC):
    def __init__(self, handler_name: str, logger: logging.Logger) -> None:
        super().__init__()
        self._handler_name = handler_name
        self._logger = logger

    def __str__(self) -> str:
        return self.handler_name

    @property
    def handler_name(self) -> str:
        return self._handler_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger
