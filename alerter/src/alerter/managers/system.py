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
from src.utils.constants.names import SYSTEM_ALERTER_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE,
    SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
    SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME, PING_ROUTING_KEY,
    SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_CHAIN,
    SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_GEN, ALERT_EXCHANGE,
    SYSTEM_ALERT_ROUTING_KEY, TOPIC)
from src.utils.exceptions import (ParentIdsMissMatchInAlertsConfiguration,
                                  MessageWasNotDeliveredException)
from src.utils.logging import log_and_print


class SystemAlertersManager(AlertersManager):

    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)
        self._systems_alerts_configs = {}
        self._parent_id_process_dict = {}

    @property
    def systems_alerts_configs(self) -> Dict:
        return self._systems_alerts_configs

    @property
    def parent_id_process_dict(self) -> Dict:
        return self._parent_id_process_dict

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.queue_declare(SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.info("Declaring consuming intentions on "
                         "'%s'", SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.basic_consume(SYS_ALERTERS_MAN_HEARTBEAT_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE,
                         SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_CHAIN)
        self.rabbitmq.queue_bind(SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_CHAIN)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE,
                         SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_GEN)
        self.rabbitmq.queue_bind(SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_GEN)
        self.logger.info("Declaring consuming intentions on %s",
                         SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(SYS_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
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

    def _terminate_and_join_chain_alerter_processes(
            self, chain: str) -> None:
        # Go through all the processes and find the chain whose
        # process should be terminated
        for parent_id, parent_info in list(
                self._parent_id_process_dict.items()):

            if self._parent_id_process_dict[parent_id]['chain'] == chain:
                # Terminate the process and join it
                self._parent_id_process_dict[parent_id]['process'].terminate()
                self._parent_id_process_dict[parent_id]['process'].join()
                # Delete key from process and configs as they aren't needed
                # anymore
                del self._parent_id_process_dict[parent_id]
                del self._systems_alerts_configs[parent_id]
                log_and_print("Terminating alerter process for chain "
                              "{}".format(chain), self.logger)

                # Send an internal alert to reset all the REDIS metrics for
                # this chain
                alert = ComponentResetChains(chain,
                                             datetime.now().timestamp(),
                                             parent_id,
                                             type(self).__name__)
                self._push_latest_data_to_queue_and_send(alert.alert_data)

    def _create_and_start_alerter_process(
            self, system_alerts_config: SystemAlertsConfig, parent_id: str,
            chain: str) -> None:
        process = multiprocessing.Process(target=start_system_alerter,
                                          args=(system_alerts_config, chain))
        process.daemon = True
        log_and_print("Creating a new process for the system alerter "
                      "of {}".format(chain), self.logger)
        process.start()
        self._parent_id_process_dict[parent_id] = {}
        self._parent_id_process_dict[parent_id]['component_name'] = \
            SYSTEM_ALERTER_NAME_TEMPLATE.format(chain)
        self._parent_id_process_dict[parent_id]['process'] = process
        self._parent_id_process_dict[parent_id]['chain'] = chain

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        if method.routing_key == SYS_ALERTERS_MAN_CONFIGS_ROUTING_KEY_GEN:
            chain = 'general'
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        try:
            """
            Send an internal alert to clear every metric from Redis for the
            chain in question, and terminate the process for the received
            config. Note that all this happens if a configuration is modified
            or deleted.
            """
            self._terminate_and_join_chain_alerter_processes(chain)

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
            for parent_id, process_details in \
                    self.parent_id_process_dict.items():
                process = process_details['process']
                component_name = process_details['component_name']
                if process.is_alive():
                    heartbeat['running_processes'].append(component_name)
                else:
                    heartbeat['dead_processes'].append(component_name)
                    process.join()  # Just in case, to release resources

                    # Restart dead process
                    chain = process_details['chain']
                    system_alerts_config = self.systems_alerts_configs[
                        parent_id]
                    self._create_and_start_alerter_process(
                        system_alerts_config, parent_id, chain)
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

    def start(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialise_rabbitmq()
        while True:
            try:
                # Send an internal alert to reset system alert REDIS metrics
                # for all chains.
                alert = ComponentResetAllChains(type(self).__name__,
                                                datetime.now().timestamp(),
                                                type(self).__name__,
                                                type(self).__name__)
                self._push_latest_data_to_queue_and_send(alert.alert_data)
                # `listen_for_data()` is called after the initial alert is sent
                # as it's a blocking function.
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

    # If termination signals are received, terminate all child process and
    # close the connection with rabbit mq before exiting
    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print(
            "{} is terminating. Connections with RabbitMQ will be closed, and "
            "any running system alerters will be stopped gracefully. "
            "Afterwards the {} process will exit.".format(self, self),
            self.logger)
        self.disconnect_from_rabbit()

        for _, process_details in self.parent_id_process_dict.items():
            log_and_print("Terminating the alerter process of {}".format(
                process_details['chain']), self.logger)
            process = process_details['process']
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _push_latest_data_to_queue_and_send(self, alert: Dict) -> None:
        self._push_to_queue(
            data=copy.deepcopy(alert), exchange=ALERT_EXCHANGE,
            routing_key=SYSTEM_ALERT_ROUTING_KEY,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True
        )
        self._send_data()
