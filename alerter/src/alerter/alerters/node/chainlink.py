import copy
import json
import logging
from typing import Dict, List

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerters.alerter import Alerter
from src.configs.alerts.chainlink_node import ChainlinkNodeAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CL_NODE_ALERTER_INPUT_QUEUE_NAME,
    CL_NODE_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE,
    CONFIG_EXCHANGE, CL_NODE_ALERTER_CONFIGS_QUEUE_NAME,
    ALERTS_CONFIGS_ROUTING_KEY_CHAIN, ALERTS_CONFIGS_ROUTING_KEY_GEN,
    CL_NODE_ALERT_ROUTING_KEY)
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration


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
            cl_node_alerts_configs: Dict[str, ChainlinkNodeAlertsConfig],
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._cl_node_alerts_configs = cl_node_alerts_configs

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
        self._cl_node_alerting_state = {}

    @property
    def cl_node_alerts_configs(self) -> Dict:
        return self._cl_node_alerts_configs

    def _initialise_rabbitmq(self) -> None:
        # An alerter is both a consumer and producer, therefore we need to
        # initialise both the consuming and producing configurations.
        self.rabbitmq.connect_till_successful()

        # Set alerts consuming configuration
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(
            exchange=ALERT_EXCHANGE, exchange_type=TOPIC, passive=False,
            durable=True, auto_delete=False, internal=False)
        self.logger.info("Creating queue '%s'",
                         CL_NODE_ALERTER_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(CL_NODE_ALERTER_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", CL_NODE_ALERTER_INPUT_QUEUE_NAME,
                         ALERT_EXCHANGE, CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=CL_NODE_ALERTER_INPUT_QUEUE_NAME, exchange=ALERT_EXCHANGE,
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(
            queue=CL_NODE_ALERTER_INPUT_QUEUE_NAME,
            on_message_callback=self._process_data, auto_ack=False,
            exclusive=False, consumer_tag=None)

        # Set configs consuming configuration
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         CL_NODE_ALERTER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(CL_NODE_ALERTER_CONFIGS_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", CL_NODE_ALERTER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, ALERTS_CONFIGS_ROUTING_KEY_CHAIN)
        self.rabbitmq.queue_bind(CL_NODE_ALERTER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 ALERTS_CONFIGS_ROUTING_KEY_CHAIN)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", CL_NODE_ALERTER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, ALERTS_CONFIGS_ROUTING_KEY_GEN)
        self.rabbitmq.queue_bind(CL_NODE_ALERTER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 ALERTS_CONFIGS_ROUTING_KEY_GEN)
        self.logger.info("Declaring consuming intentions on %s",
                         CL_NODE_ALERTER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(CL_NODE_ALERTER_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        try:
            # Checking if the configuration is empty. If it is ignore it, if
            # not add it to the list of configurations. Note, if a configuration
            # was deleted it won't be used, so might as well not do anything.
            if bool(sent_configs):
                pass
                # TODO: Add new config

                # TODO: Create state here

            # TODO: Remove is needed?
        except Exception as e:
            # Otherwise log and reject the message
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    # TODO: Create state for node must be done when configs are received, just
    #     : in case some thresholds change.

    # TODO: When processing alerts check if config is available first, if not
    #     : skip alerts.

    def _place_latest_data_on_queue(self, data_list: List) -> None:
        # Place the latest alert data on the publishing queue. If the queue is
        # full, remove old data.
        for alert in data_list:
            self.logger.debug("Adding %s to the publishing queue.", alert)
            if self.publishing_queue.full():
                self.publishing_queue.get()
            self.publishing_queue.put({
                'exchange': ALERT_EXCHANGE,
                'routing_key': CL_NODE_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
