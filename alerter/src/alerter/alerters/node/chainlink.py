import logging
from typing import Dict

from src.alerter.alerters.alerter import Alerter
from src.message_broker.rabbitmq import RabbitMQApi


class ChainlinkNodeAlerter(Alerter):
    def __init__(self, alerter_name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi, max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._cl_node_alerts_config = {}

    @property
    def cl_node_alerts_config(self) -> Dict:
        return self._cl_node_alerts_config
