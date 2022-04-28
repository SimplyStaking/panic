import copy
import json
import logging
import sys
from datetime import datetime
from multiprocessing import Process
from types import FrameType
from typing import Dict

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerter_starters import (
    start_cosmos_node_alerter, start_cosmos_network_alerter)
from src.alerter.alerters.network.cosmos import CosmosNetworkAlerter
from src.alerter.alerters.node.cosmos import CosmosNodeAlerter
from src.alerter.alerts.internal_alerts import ComponentResetAlert
from src.alerter.managers.manager import AlertersManager
from src.configs.alerts.network.cosmos import CosmosNetworkAlertsConfig
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.configs.factory.alerts.cosmos_alerts import (
    CosmosNodeAlertsConfigsFactory, CosmosNetworkAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.names import (
    COSMOS_NODE_ALERTER_NAME, COSMOS_NETWORK_ALERTER_NAME)
from src.utils.constants.rabbitmq import (
    COSMOS_NODE_ALERT_ROUTING_KEY, HEALTH_CHECK_EXCHANGE, TOPIC,
    COSMOS_ALERTERS_MAN_HB_QUEUE_NAME, PING_ROUTING_KEY, CONFIG_EXCHANGE,
    COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME, COSMOS_ALERTS_CONFIGS_ROUTING_KEY,
    ALERT_EXCHANGE, COSMOS_NETWORK_ALERT_ROUTING_KEY)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class CosmosAlertersManager(AlertersManager):
    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)
        self._node_alerts_config_factory = CosmosNodeAlertsConfigsFactory()
        self._network_alerts_config_factory = \
            CosmosNetworkAlertsConfigsFactory()
        self._alerter_process_dict = {}
        self._configs_processor_helper = {
            COSMOS_NODE_ALERTER_NAME: {
                'alerterClass': CosmosNodeAlerter,
                'configsClass': CosmosNodeAlertsConfig,
                'factory': self.node_alerts_config_factory,
                'routing_key': COSMOS_NODE_ALERT_ROUTING_KEY,
                'starter': start_cosmos_node_alerter,
            },
            COSMOS_NETWORK_ALERTER_NAME: {
                'alerterClass': CosmosNetworkAlerter,
                'configsClass': CosmosNetworkAlertsConfig,
                'factory': self.network_alerts_config_factory,
                'routing_key': COSMOS_NETWORK_ALERT_ROUTING_KEY,
                'starter': start_cosmos_network_alerter,
            }
        }

    @property
    def alerter_process_dict(self) -> Dict:
        return self._alerter_process_dict

    @property
    def node_alerts_config_factory(self) -> CosmosNodeAlertsConfigsFactory:
        return self._node_alerts_config_factory

    @property
    def network_alerts_config_factory(
            self) -> CosmosNetworkAlertsConfigsFactory:
        return self._network_alerts_config_factory

    @property
    def configs_processor_helper(self) -> Dict:
        return self._configs_processor_helper

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions for the health checker component
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         COSMOS_ALERTERS_MAN_HB_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            COSMOS_ALERTERS_MAN_HB_QUEUE_NAME, False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", COSMOS_ALERTERS_MAN_HB_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(COSMOS_ALERTERS_MAN_HB_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.info("Declaring consuming intentions on '%s'",
                         COSMOS_ALERTERS_MAN_HB_QUEUE_NAME)
        self.rabbitmq.basic_consume(COSMOS_ALERTERS_MAN_HB_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        # Setting up routing keys and queues for configuration consumption
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME, False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, COSMOS_ALERTS_CONFIGS_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
            COSMOS_ALERTS_CONFIGS_ROUTING_KEY)

        self.logger.info("Declaring consuming intentions on %s",
                         COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(COSMOS_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)

        # Declare exchange to send data to
        self.rabbitmq.exchange_declare(
            exchange=ALERT_EXCHANGE, exchange_type=TOPIC, passive=False,
            durable=True, auto_delete=False, internal=False)
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

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

            for alerter, process in self.alerter_process_dict.items():
                if process.is_alive():
                    heartbeat['running_processes'].append(alerter)
                else:
                    heartbeat['dead_processes'].append(alerter)
                    process.join()  # Just in case, to release resources

            # Restart dead process
            if len(heartbeat['dead_processes']) > 0:
                self._create_and_start_alerter_processes()

            heartbeat['timestamp'] = datetime.now().timestamp()
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

    def _create_and_start_alerter_processes(self) -> None:
        """
        Start the Cosmos Alerters in a separate process if they are not yet
        started, or they are not alive. This must be done in case of a restart
        of the manager.
        """
        for alerter_name, alerter_details in \
                self.configs_processor_helper.items():
            if (alerter_name not in self.alerter_process_dict or
                    not self.alerter_process_dict[alerter_name].is_alive()):
                """
                We must clear out all the metrics which are found in Redis.
                Sending this alert to the alert router and then the data store
                will achieve this. This is sent on startup of the manager and if
                the alerter process is deemed to be dead.
                """
                alert = ComponentResetAlert(
                    alerter_name, datetime.now().timestamp(),
                    alerter_details['alerterClass'].__name__)
                self._push_latest_data_to_queue_and_send(
                    alert.alert_data, alerter_details['routing_key'])

                """
                Start the Alerter process with the factory being updated by this
                manager. This factory should hold all the configurations, if
                any.
                """
                log_and_print("Attempting to start the {}.".format(
                    alerter_name), self.logger)
                alerter_process = Process(target=alerter_details['starter'],
                                          args=(alerter_details['factory'],))
                alerter_process.daemon = True
                alerter_process.start()

                self._alerter_process_dict[alerter_name] = alerter_process

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.debug("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        parsed_routing_key = method.routing_key.split('.')
        chain_name = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        try:
            """
            If we received a config then we must add it to the config factories,
            which store all the alert configurations.
            If the received dictionary is empty then delete the configuration
            which is saved under the routing_key.

            We also check if the configuration has been updated, if it has then
            the metrics in Redis need to be reset.
            """
            if bool(sent_configs):
                for alerter_name, alerter_details in \
                        self.configs_processor_helper.items():
                    configs_factory = alerter_details['factory']
                    alerter_class = alerter_details['alerterClass']
                    configs_class = alerter_details['configsClass']
                    configs_factory.add_new_config(chain_name, sent_configs)
                    parent_id = configs_factory.get_parent_id(chain_name,
                                                              configs_class)
                    alert = ComponentResetAlert(
                        alerter_name, datetime.now().timestamp(),
                        alerter_class.__name__, parent_id, chain_name
                    )
                    self._push_latest_data_to_queue_and_send(
                        alert.alert_data, alerter_details['routing_key'])
            else:
                for _, alerter_details in self.configs_processor_helper.items():
                    configs_factory = alerter_details['factory']
                    configs_factory.remove_config(chain_name)

        except Exception as e:
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def start(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialise_rabbitmq()
        while True:
            try:
                # Empty the queue so that on restart we don't send multiple
                # reset alerts.
                if not self.publishing_queue.empty():
                    self.publishing_queue.queue.clear()

                self._create_and_start_alerter_processes()
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    # If termination signals are received, terminate all child process and exit
    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print(
            "{} is terminating. Connections with RabbitMQ will be closed, and "
            "the Cosmos alerters will be stopped gracefully. Afterwards the "
            "{} process will exit.".format(self, self), self.logger)

        for alerter, process in self.alerter_process_dict.items():
            log_and_print("Terminating the process of {}".format(alerter),
                          self.logger)
            process.terminate()
            process.join()
        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _push_latest_data_to_queue_and_send(self, alert: Dict,
                                            routing_key: str) -> None:
        self._push_to_queue(
            data=copy.deepcopy(alert), exchange=ALERT_EXCHANGE,
            routing_key=routing_key,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True
        )
        self._send_data()
