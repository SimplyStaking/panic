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
from src.alerter.managers.manager import AlertersManager
from src.configs.system_alerts import SystemAlertsConfig
from src.utils.constants import HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE, \
    SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration, \
    MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class SystemAlertersManager(AlertersManager):

    def __init__(self, logger: logging.Logger, manager_name: str) -> None:
        super().__init__(logger, manager_name)
        self._systems_alerts_configs = {}
        self._parent_id_process_dict = {}

    @property
    def systems_alerts_configs(self) -> Dict:
        return self._systems_alerts_configs

    @property
    def parent_id_process_dict(self) -> Dict:
        return self._parent_id_process_dict

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '{}' exchange".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue 'system_alerters_manager_ping_queue'")
        self.rabbitmq.queue_declare('system_alerters_manager_ping_queue',
                                    False, True, False, False)
        self.logger.info("Binding queue 'system_alerters_manager_ping_queue' "
                         "to exchange '{}' with routing key "
                         "'ping'".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.queue_bind('system_alerters_manager_ping_queue',
                                 HEALTH_CHECK_EXCHANGE, 'ping')
        self.logger.debug("Declaring consuming intentions on "
                          "'system_alerters_manager_ping_queue'")
        self.rabbitmq.basic_consume('system_alerters_manager_ping_queue',
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '{}'".format(CONFIG_EXCHANGE))
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue '{}'".format(
            SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME))
        self.rabbitmq.queue_declare(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                    False, True, False, False)
        self.logger.info(
            "Binding queue '{}' to exchange '{}' with routing key "
            "'chains.*.*.alerts_config'".format(
                SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE))
        self.rabbitmq.queue_bind(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'chains.*.*.alerts_config')
        self.logger.info(
            "Binding queue '{}' to exchange '{}' with routing key "
            "'general.alerts_config'".format(
                SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE))
        self.rabbitmq.queue_bind(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'general.alerts_config')
        self.logger.debug("Declaring consuming intentions on {}".format(
            SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME))
        self.rabbitmq.basic_consume(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

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
            "System alerter ({})".format(chain)
        self._parent_id_process_dict[parent_id]['process'] = process
        self._parent_id_process_dict[parent_id]['parent_id'] = parent_id
        self._parent_id_process_dict[parent_id]['chain'] = chain

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info("Received configs {}".format(sent_configs))

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        if method.routing_key == 'general.alerts_config':
            chain = 'general'
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        try:
            # Check if all the parent_ids in the received configuration
            # are the same
            parent_id = sent_configs['1']['parent_id']
            for i in sent_configs:
                if parent_id != sent_configs[i]['parent_id']:
                    raise ParentIdsMissMatchInAlertsConfiguration(
                        "{}: _process_data".format(self))

            filtered = {}
            for i in sent_configs:
                filtered[sent_configs[i]['name']] = copy.deepcopy(
                    sent_configs[i])

            system_alerts_config = SystemAlertsConfig(
                parent_id=parent_id,
                open_file_descriptors=filtered['open_file_descriptors'],
                system_cpu_usage=filtered['system_cpu_usage'],
                system_storage_usage=filtered['system_storage_usage'],
                system_ram_usage=filtered['system_ram_usage'],
                system_is_down=filtered['system_is_down'],
            )

            if parent_id in self.systems_alerts_configs:
                previous_process = \
                    self.parent_id_process_dict[parent_id]['process']
                previous_process.terminate()
                previous_process.join()

                log_and_print("Restarting the system alerter of {} with latest "
                              "configuration".format(chain), self.logger)

            self._create_and_start_alerter_process(
                system_alerts_config, parent_id, chain)
            self._systems_alerts_configs[parent_id] = system_alerts_config
        except Exception as e:
            self.logger.error("Error when processing {}".format(sent_configs))
            self.logger.exception(e)

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.debug("Received {}".format(data))

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
                    parent_id = process_details['parent_id']
                    chain = process_details['chain']
                    system_alerts_config = self.systems_alerts_configs[
                        parent_id]
                    self._create_and_start_alerter_process(system_alerts_config,
                                                           parent_id, chain)
            heartbeat['timestamp'] = datetime.now().timestamp()
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing {}".format(data))
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

    def manage(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialize_rabbitmq()
        while True:
            try:
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    # If termination signals are received, terminate all child process and
    # close the connection with rabbit mq before exiting
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print(
            "{} is terminating. Connections with RabbitMQ will be closed, and "
            "any running system alerters will be stopped gracefully. "
            "Afterwards the {} process will exit.".format(self, self),
            self.logger)
        self.rabbitmq.disconnect_till_successful()

        for _, process_details in self.parent_id_process_dict.items():
            log_and_print("Terminating the alerter process of {}".format(
                process_details['chain']), self.logger)
            process = process_details['process']
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
