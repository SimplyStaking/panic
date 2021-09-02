import logging
from src.message_broker.rabbitmq import RabbitMQApi
from src.alerter.alerters.alerter import Alerter


class EVMNodeAlerter(Alerter):
    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            evm_alerts_configs_factory: EVMAlertsConfigsFactory,
            rabbitmq: RabbitMQApi, max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)
        