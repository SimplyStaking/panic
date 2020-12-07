from logging import Logger
from types import FrameType

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.channels_manager.managers import ChannelManager


class EmailChannelManager(ChannelManager):
    def __init__(self, logger: Logger, rabbit_ip: str):
        super().__init__(logger, rabbit_ip)

    def _initialise_rabbit(self) -> None:
        pass

    def _process_config(self, ch: BlockingChannel,
                        method: pika.spec.Basic.Deliver,
                        properties: pika.spec.BasicProperties,
                        body: bytes) -> None:
        pass

    def _process_ping(self, ch: BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        pass

    def manage(self) -> None:
        pass

    def start(self) -> None:
        pass

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        pass