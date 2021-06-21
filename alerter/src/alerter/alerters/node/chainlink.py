import copy
import json
import logging
from typing import Dict, List

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerters.alerter import Alerter
from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.configs.factory.chainlink_alerts_configs_factory import \
    ChainlinkAlertsConfigsFactory
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CL_NODE_ALERTER_INPUT_QUEUE_NAME,
    CL_NODE_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE,
    CONFIG_EXCHANGE, CL_NODE_ALERTER_CONFIGS_QUEUE_NAME,
    ALERTS_CONFIGS_ROUTING_KEY_CHAIN, ALERTS_CONFIGS_ROUTING_KEY_GEN,
    CL_NODE_ALERT_ROUTING_KEY)
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration
from src.configs.factory.chainlink_alerts_configs_factory import \
    ChainlinkAlertsConfigsFactory


class ChainlinkNodeAlerter(Alerter):
    """
    We will have one chainlink node alerter for all chainlink nodes. Also the
    chainlink alerter doesn't have to restart if the configurations change, as
    we will be listening for all configs here. Ideally, this is to be done for
    every other alerter when refactoring.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            rabbitmq: RabbitMQApi,
            chainlink_alerts_configs_factory: ChainlinkAlertsConfigsFactory,
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = chainlink_alerts_configs_factory

        # TODO: Modify this comment when alerter is done
        """
        This dict is to be structured as follows:
        {
            <parent_id>: {
                <system_id>: {
                    warning_sent,
                    critical_sent,
                    limiters etc
                }
            }
        }
        Whenever a configuration reset happens, 
        """
        self._alerting_state = {}

    @property
    def alerts_configs_factory(self) -> ChainlinkAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_state(self) -> Dict:
        return self._alerting_state

    def _initialise_rabbitmq(self) -> None:
        pass

    def _create_alerting_state(self, parent_id: str, node_id: str) -> None:
        # TODO: First must create state for parent_id then node_id
        pass

    def _remove_chain_alerting_state(self, parent_id: str,
                                     node_id: str) -> None:
        pass

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def _place_latest_data_on_queue(self, data_list: List) -> None:
        pass

    def _process_data(self, *args) -> None:
        pass
