import logging
from src.message_broker.rabbitmq import RabbitMQApi
from src.alerter.alerters.alerter import Alerter
from src.alerter.factory.evm_node_alerting_factory.py import \
    EVMNodeAlertingFactory


class EVMNodeAlerter(Alerter):
    """
    We will have one alerter for all evm nodes. The evm alerter
    doesn't have to restart if the configurations change, as it will be
    listening for both data and configs in the same queue.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            evm_alerts_configs_factory: EVMAlertsConfigsFactory,
            rabbitmq: RabbitMQApi, max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = evm_alerts_configs_factory
        self._alerting_factory = EVMNodeAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> EVMAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_factory(self) -> EVMNodeAlertingFactory:
        return self._alerting_factory