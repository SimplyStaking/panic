import logging
from types import FrameType

from src.channels_manager.handlers import ChannelHandler


class PagerDutyAlertsHandler(ChannelHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 rabbit_ip: str, queue_size: int, config: PagerDutyChannelConfig,
                 max_attempts: int = 6, alert_validity_threshold: int = 600):
        super().__init__(handler_name, logger)

    def start(self) -> None:
        pass

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        pass
