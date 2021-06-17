import copy
import json
import logging
import multiprocessing
import sys
from datetime import datetime
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerter_starters import start_system_alerter
from src.alerter.alerts.internal_alerts import (ComponentResetAllChains,
                                                ComponentResetChains)
from src.alerter.managers.manager import AlertersManager
from src.configs.system_alerts import SystemAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.names import CHAINLINK_ALERTER
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE,
    CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME,
    CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME, PING_ROUTING_KEY,
    ALERTERS_MAN_CONFIGS_ROUTING_KEY_CHAIN,
    SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_GEN, ALERT_EXCHANGE,
    SYSTEM_ALERT_ROUTING_KEY, TOPIC,
    CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME,
    CHAINLINK_ALERT_ROUTING_KEY)
from src.utils.exceptions import (ParentIdsMissMatchInAlertsConfiguration,
                                  MessageWasNotDeliveredException)
from src.utils.logging import log_and_print
from src.configs.factory.alerts_configs_factory import AlertsConfigFactory

"""
Design
Chainlink Alerter Manager should keep track of the configs received as well as
attempt to restart the Chainlink Alerter if down with the configuration state
that is held by the manager.

The Chainlink alerter should be started with no configuration state and should
then update its configs accordingly. We could also start with a config state
if there is, no reason we shouldnt.
"""


class ChainlinkAlerterManager(AlertersManager):
    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)
        self._chainlink_alerts_configs = {}
        self._alerter_process_dict = {}
        self.alerts_config_factory = AlertsConfigFactory()

    @property
    def chainlink_alerts_configs(self) -> Dict:
        return self._chainlink_alerts_configs

    @property
    def alerter_process_dict(self) -> Dict:
        return self._alerter_process_dict

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions for the health checker component
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.queue_declare(CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.info("Declaring consuming intentions on "
                         "'%s'", CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.basic_consume(CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        # Setting up routing keys and queues for configuration consumption
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE,
                         ALERTERS_MAN_CONFIGS_ROUTING_KEY_CHAIN)
        self.rabbitmq.queue_bind(CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 ALERTERS_MAN_CONFIGS_ROUTING_KEY_CHAIN)

        self.logger.info("Declaring consuming intentions on %s",
                         CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(
            CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME,
            self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        # Declare exchange to send data to
        self.rabbitmq.exchange_declare(exchange=ALERT_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)

        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _start_alerter_process(
            self, chainlink_alerts_configs: ChainlinkAlertsConfigs) -> None:
        """
        Start the Chainlink Alerter process with an empty or an updated
        configuration.
        """
        # @note There should be a message here to reset the data store data for it
        # @note maybe we should check if there is currently a chainlink alerter
        # process that is already running and attempt to terminate it
        log_and_print("Attempting to start the {}.".format(
            CHAINLINK_ALERTER), self.logger)
        chainlink_alerter_process = multiprocessing.Process(
            target=start_chainlink_alerter,
            args=(chainlink_alerts_configs))
        chainlink_alerter_process.daemon = True
        chainlink_alerter_process.start()

        self._alerter_process_dict[CHAINLINK_ALERTER] = \
            chainlink_alerter_process

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        parsed_routing_key = method.routing_key.split('.')
        if parsed_routing_key[1] != 'chainlink':
            return

        try:
            """
            We must check if the received config is new or a modified version
            of something that is processed. If it is new then add it to config
            store otherwise for the modified config, we must reset the metrics
            and update the object.
            """

            """
            We should put it into a config object and store that config object
            in a dictionary of object, We can store those dictionaries inside
            the the network type e.g ethereuem.
            """

            # Create the configuration object
            self._chainlink_alerts_configs[parsed_routing_key[2]] =

            # Checking if we received a configuration, therefore we start the
            # process again
            if bool(sent_configs):
                # Check if all the parent_ids in the received configuration
                # are the same
                parent_id = sent_configs['1']['parent_id']
                for _, config in sent_configs.items():
                    if parent_id != config['parent_id']:
                        raise ParentIdsMissMatchInAlertsConfiguration(
                            "{}: _process_data".format(self))
                filtered = {}
                for _, config in sent_configs.items():
                    filtered[config['name']] = copy.deepcopy(config)

                system_alerts_config = SystemAlertsConfig(
                    parent_id=parent_id,
                    open_file_descriptors=filtered['open_file_descriptors'],
                    system_cpu_usage=filtered['system_cpu_usage'],
                    system_storage_usage=filtered['system_storage_usage'],
                    system_ram_usage=filtered['system_ram_usage'],
                    system_is_down=filtered['system_is_down'],
                )

                self._create_and_start_alerter_process(
                    system_alerts_config, parent_id, chain)
                self._systems_alerts_configs[parent_id] = system_alerts_config
        except Exception as e:
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    # If termination signals are received, terminate all child process and exit
    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and the Chainlink alerter will be "
                      "stopped gracefully. Afterwards the {} process will "
                      "exit.".format(self, self), self.logger)

        # Check if the alerter process is actually still there.
        if CHAINLINK_ALERTER in self.alerter_process_dict:
            chainlink_alerter_process = \
                self.alerter_process_dict[CHAINLINK_ALERTER]
            chainlink_alerter_process.terminate()
            chainlink_alerter_process.join()

            alert = ComponentResetAllChains(type(self).__name__,
                                            datetime.now().timestamp(),
                                            type(self).__name__,
                                            type(self).__name__)
            self._push_latest_data_to_queue_and_send(alert.alert_data)

        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _push_latest_data_to_queue_and_send(self, alert: Dict) -> None:
        self._push_to_queue(
            data=copy.deepcopy(alert), exchange=ALERT_EXCHANGE,
            routing_key=CHAINLINK_ALERT_ROUTING_KEY,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True
        )
        self._send_data()
