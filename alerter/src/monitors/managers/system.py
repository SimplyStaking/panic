import copy
import json
import logging
import multiprocessing
from datetime import datetime
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.manager import MonitorsManager
from src.monitors.starters import start_system_monitor
from src.utils.configs import (get_newly_added_configs, get_modified_configs,
                               get_removed_configs)
from src.utils.constants import (CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                                 SYS_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                 SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN,
                                 SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_SYS,
                                 SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_NODES,
                                 SYSTEM_MONITOR_NAME_TEMPLATE, PING_ROUTING_KEY)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import str_to_bool


class SystemMonitorsManager(MonitorsManager):
    BASE_CHAINS_WITH_SEPARATE_SYS_CONF = ['chainlink']

    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)

        self._systems_configs = {}

    @property
    def systems_configs(self) -> Dict:
        return self._systems_configs

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         SYS_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.queue_declare(SYS_MON_MAN_HEARTBEAT_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", SYS_MON_MAN_HEARTBEAT_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(SYS_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          PING_ROUTING_KEY)
        self.rabbitmq.basic_consume(SYS_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'", SYS_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(SYS_MON_MAN_CONFIGS_QUEUE_NAME, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE,
                         SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_SYS)
        self.rabbitmq.queue_bind(SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_SYS)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE,
                         SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_NODES)
        self.rabbitmq.queue_bind(SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_NODES)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN)
        self.rabbitmq.queue_bind(SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          SYS_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(SYS_MON_MAN_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _create_and_start_monitor_process(self, system_config: SystemConfig,
                                          config_id: str, chain: str) -> None:
        log_and_print("Creating a new process for the monitor of {}"
                      .format(system_config.system_name), self.logger)
        process = multiprocessing.Process(target=start_system_monitor,
                                          args=(system_config,))
        # Kill children if parent is killed
        process.daemon = True
        process.start()
        self._config_process_dict[config_id] = {}
        self._config_process_dict[config_id]['component_name'] = \
            SYSTEM_MONITOR_NAME_TEMPLATE.format(system_config.system_name)
        self._config_process_dict[config_id]['process'] = process
        self._config_process_dict[config_id]['chain'] = chain

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.debug("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        if method.routing_key == SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN:
            if 'general' in self.systems_configs:
                current_configs = self.systems_configs['general']
            else:
                current_configs = {}
            chain = 'general'
        else:
            parsed_routing_key = method.routing_key.split('.')
            base_chain = parsed_routing_key[1]
            specific_chain = parsed_routing_key[2]
            config_type = parsed_routing_key[3]
            chain = base_chain + ' ' + specific_chain

            # TODO: Reminder, when we merge !42 change nodes_config to one of
            #     : the constants in utils/constants. Also we can refactor all
            #     : general instances found here and in other modules.
            # For such chains the nodes_config.ini file has no system confs,
            # therefore ignore the contents and acknowledge the message.
            if base_chain.lower() in self.BASE_CHAINS_WITH_SEPARATE_SYS_CONF \
                    and config_type.lower() == 'nodes_config':
                self.rabbitmq.basic_ack(method.delivery_tag, False)
                return

            if chain in self.systems_configs:
                current_configs = self.systems_configs[chain]
            else:
                current_configs = {}

        # This contains all the correct latest system configs. All current
        # configs are correct configs, therefore start from the current and
        # modify as we go along according to the updates. This is done just in
        # case an error occurs.
        correct_systems_configs = copy.deepcopy(current_configs)

        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                system_id = config['id']
                parent_id = config['parent_id']
                system_name = config['name']
                node_exporter_url = config['exporter_url']
                monitor_system = str_to_bool(config['monitor_system'])

                # If we should not monitor the system, move to the next config
                if not monitor_system:
                    continue

                system_config = SystemConfig(system_id, parent_id, system_name,
                                             monitor_system, node_exporter_url)
                self._create_and_start_monitor_process(system_config, config_id,
                                                       chain)
                correct_systems_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                system_id = config['id']
                parent_id = config['parent_id']
                system_name = config['name']
                node_exporter_url = config['exporter_url']
                monitor_system = str_to_bool(config['monitor_system'])
                system_config = SystemConfig(system_id, parent_id, system_name,
                                             monitor_system, node_exporter_url)
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()

                # If we should not monitor the system, delete the previous process
                # from the system and move to the next config
                if not monitor_system:
                    del self.config_process_dict[config_id]
                    del correct_systems_configs[config_id]
                    log_and_print("Killed the monitor of {} ".format(
                        modified_configs[config_id]['name']), self.logger)
                    continue

                log_and_print(
                    "The configuration for {} was modified. A new monitor with "
                    "the latest configuration will be started.".format(
                        modified_configs[config_id]['name']), self.logger)
                self._create_and_start_monitor_process(system_config, config_id,
                                                       chain)
                correct_systems_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                system_name = config['name']
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()
                del self.config_process_dict[config_id]
                del correct_systems_configs[config_id]
                log_and_print("Killed the monitor of {} "
                              .format(system_name), self.logger)
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        # Must be done at the end in case of errors while processing
        if method.routing_key == SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN:
            self._systems_configs['general'] = correct_systems_configs
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            self._systems_configs[chain] = correct_systems_configs

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
            for config_id, process_details in self.config_process_dict.items():
                process = process_details['process']
                component_name = process_details['component_name']
                if process.is_alive():
                    heartbeat['running_processes'].append(component_name)
                else:
                    heartbeat['dead_processes'].append(component_name)
                    process.join()  # Just in case, to release resources

                    # Restart dead process
                    chain = process_details['chain']
                    config = self.systems_configs[chain][config_id]
                    system_id = config['id']
                    parent_id = config['parent_id']
                    system_name = config['name']
                    node_exporter_url = config['exporter_url']
                    monitor_system = str_to_bool(config['monitor_system'])
                    system_config = SystemConfig(system_id, parent_id,
                                                 system_name,
                                                 monitor_system,
                                                 node_exporter_url)
                    self._create_and_start_monitor_process(system_config,
                                                           config_id, chain)
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
