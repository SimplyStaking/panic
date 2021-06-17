import copy
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
        pass
        # sent_configs = json.loads(body)
        #
        # self.logger.info("Received configs %s", sent_configs)
        #
        # if 'DEFAULT' in sent_configs:
        #     del sent_configs['DEFAULT']
        #
        # if method.routing_key == ALERTS_CONFIGS_ROUTING_KEY_GEN:
        #     chain = 'general'
        # else:
        #     parsed_routing_key = method.routing_key.split('.')
        #     chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        #
        # try:
        #     """
        #     Send an internal alert to clear every metric from Redis for the
        #     chain in question, and terminate the process for the received
        #     config. Note that all this happens if a configuration is modified
        #     or deleted.
        #     """
        #     self._terminate_and_join_chain_alerter_processes(chain)
        #
        #     # Checking if we received a configuration, therefore we start the
        #     # process again
        #     if bool(sent_configs):
        #         # Check if all the parent_ids in the received configuration
        #         # are the same
        #         parent_id = sent_configs['1']['parent_id']
        #         for _, config in sent_configs.items():
        #             if parent_id != config['parent_id']:
        #                 raise ParentIdsMissMatchInAlertsConfiguration(
        #                     "{}: _process_data".format(self))
        #         filtered = {}
        #         for _, config in sent_configs.items():
        #             filtered[config['name']] = copy.deepcopy(config)
        #
        #         system_alerts_config = SystemAlertsConfig(
        #             parent_id=parent_id,
        #             open_file_descriptors=filtered['open_file_descriptors'],
        #             system_cpu_usage=filtered['system_cpu_usage'],
        #             system_storage_usage=filtered['system_storage_usage'],
        #             system_ram_usage=filtered['system_ram_usage'],
        #             system_is_down=filtered['system_is_down'],
        #         )
        #
        #         self._create_and_start_alerter_process(
        #             system_alerts_config, parent_id, chain)
        #         self._systems_alerts_configs[parent_id] = system_alerts_config
        # except MessageWasNotDeliveredException as e:
        #     # If the internal alert cannot be delivered, requeue the config
        #     # for re-processing.
        #     self.logger.error("Error when processing %s", sent_configs)
        #     self.logger.exception(e)
        #     self.rabbitmq.basic_nack(method.delivery_tag)
        #     return
        # except Exception as e:
        #     # Otherwise log and reject the message
        #     self.logger.error("Error when processing %s", sent_configs)
        #     self.logger.exception(e)
        #
        # self.rabbitmq.basic_ack(method.delivery_tag, False)

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
