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

from src.alerter.alerter_starters import start_chainlink_alerter
from src.alerter.alerters.node.chainlink import ChainlinkAlerter
from src.alerter.alerts.internal_alerts import ComponentResetAlert
from src.alerter.managers.manager import AlertersManager
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.names import CHAINLINK_ALERTER
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE,
    CHAINLINK_ALERTER_MANAGER_CONFIGS_QUEUE_NAME,
    CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME, PING_ROUTING_KEY,
    ALERTERS_MAN_CONFIGS_ROUTING_KEY_CHAIN, ALERT_EXCHANGE, TOPIC,
    CHAINLINK_ALERTER_MAN_HEARTBEAT_QUEUE_NAME,
    CHAINLINK_ALERT_ROUTING_KEY)
from src.utils.exceptions import (ParentIdsMissMatchInAlertsConfiguration,
                                  MessageWasNotDeliveredException)
from src.utils.logging import log_and_print
from src.configs.factory.chainlink_alerts_configs_factory import \
    ChainlinkAlertsConfigFactory


class ChainlinkAlerterManager(AlertersManager):
    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)
        self._alerts_config_factory = ChainlinkAlertsConfigFactory()
        self._alerter_process_dict = {}

    @property
    def alerter_process_dict(self) -> Dict:
        return self._alerter_process_dict

    @property
    def alerts_config_factory(self) -> ChainlinkAlertsConfigFactory:
        return self._alerts_config_factory

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
        self._start_alerter_process()

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.debug("Received %s", data)

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.name
            heartbeat['running_processes'] = []
            heartbeat['dead_processes'] = []
            chainlink_alerter_process = \
                self.alerter_process_dict[CHAINLINK_ALERTER]

            if chainlink_alerter_process.is_alive():
                heartbeat['running_processes'].append(CHAINLINK_ALERTER)
            else:
                heartbeat['dead_processes'].append(CHAINLINK_ALERTER)
                chainlink_alerter_process.join()  # Release resources
            heartbeat['timestamp'] = datetime.now().timestamp()

            # Restart dead alerter
            if len(heartbeat['dead_processes']) != 0:
                self._start_alerter_process()
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing %s", data)
            self.logger.exception(e)
            return

        # Send heartbeat if processing was successful
        try:
            self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as there is no use in
            # re-trying to send a heartbeat
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it.
            raise e

    def _start_alerter_process(self) -> None:
        """
        We must clear out all the metrics which are found in Redis.
        Sending this alert to the alert router and then the data store will
        achieve this. This is sent on startup of the manager and if the alerter
        process is deemed to be dead.
        """
        alert = ComponentResetAlert(CHAINLINK_ALERTER,
                                    datetime.now().timestamp(),
                                    ChainlinkAlerter.__name__)
        self._push_latest_data_to_queue_and_send(alert.alert_data)

        """
        Start the Chainlink Alerter process with the saved factory object.
        This factory object should hold all the configurations, if any.
        """
        log_and_print("Attempting to start the {}.".format(
            CHAINLINK_ALERTER), self.logger)
        chainlink_alerter_process = multiprocessing.Process(
            target=start_chainlink_alerter,
            args=(self.alerts_config_factory))
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
        chain_name = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        try:
            """
            If we received a config then we must create a new chainlink node
            alerts configuration object and store it under the routing_key.
            If the received dictionary is empty then delete the configuration
            pre-taining to the routing_key.

            We also check if the configuration has been updated, if it has then
            the metrics in Redis need to be reset.
            """
            if bool(sent_configs):
                config_updated, parent_id = \
                    self.alerts_config_factory.add_new_config(chain_name,
                                                              sent_configs)
                if config_updated:
                    alert = ComponentResetAlert(CHAINLINK_ALERTER,
                                                datetime.now().timestamp(),
                                                ChainlinkAlerter.__name__,
                                                parent_id,
                                                chain_name
                                                )
                    self._push_latest_data_to_queue_and_send(alert.alert_data)
            else:
                self.alerts_config_factory.remove_config(chain_name)

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

            alert = ComponentResetAlert(CHAINLINK_ALERTER,
                                        datetime.now().timestamp(),
                                        ChainlinkAlerter.__name__)
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
