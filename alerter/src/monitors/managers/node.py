import copy
import json
import logging
import multiprocessing
from datetime import datetime
from typing import Dict, Type

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.configs.nodes.evm import EVMNodeConfig
from src.configs.nodes.node import NodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.manager import MonitorsManager
from src.monitors.monitor import Monitor
from src.monitors.node.chainlink import ChainlinkNodeMonitor
from src.monitors.node.evm import EVMNodeMonitor
from src.monitors.starters import start_node_monitor
from src.utils.configs import (get_newly_added_configs, get_modified_configs,
                               get_removed_configs)
from src.utils.constants.names import NODE_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, NODE_MON_MAN_HEARTBEAT_QUEUE_NAME, PING_ROUTING_KEY,
    CONFIG_EXCHANGE, NODE_MON_MAN_CONFIGS_QUEUE_NAME,
    NODES_CONFIGS_ROUTING_KEY_CHAINS, EVM_NODES_CONFIGS_ROUTING_KEY_CHAINS,
    TOPIC)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import str_to_bool


class NodeMonitorsManager(MonitorsManager):

    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)

        self._nodes_configs = {}

    @property
    def nodes_configs(self) -> Dict:
        return self._nodes_configs

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         NODE_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.queue_declare(NODE_MON_MAN_HEARTBEAT_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", NODE_MON_MAN_HEARTBEAT_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(NODE_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          NODE_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.basic_consume(NODE_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'", NODE_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(NODE_MON_MAN_CONFIGS_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", NODE_MON_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.rabbitmq.queue_bind(NODE_MON_MAN_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", NODE_MON_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, EVM_NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.rabbitmq.queue_bind(NODE_MON_MAN_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 EVM_NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          NODE_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(NODE_MON_MAN_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _create_and_start_monitor_process(
            self, node_config: NodeConfig, config_id: str,
            monitor_type: Type[Monitor]) -> None:
        log_and_print("Creating a new process for the monitor of {}".format(
            node_config.node_name), self.logger)
        process = multiprocessing.Process(target=start_node_monitor,
                                          args=(node_config, monitor_type))
        # Kill children if parent is killed
        process.daemon = True
        process.start()
        self._config_process_dict[config_id] = {}
        self._config_process_dict[config_id]['component_name'] = \
            NODE_MONITOR_NAME_TEMPLATE.format(node_config.node_name)
        self._config_process_dict[config_id]['process'] = process
        self._config_process_dict[config_id]['monitor_type'] = monitor_type
        self._config_process_dict[config_id]['node_config'] = node_config

    def _process_chainlink_node_configs(self, sent_configs: Dict,
                                        current_configs: Dict) -> Dict:
        """
        This function processes the new nodes configs for a particular chainlink
        chain. It creates/removes new processes, and it keeps a local copy of
        all changes being done step by step. This is done in this way so that if
        a sub-config is malformed or a process errors, we can keep track of what
        the new self._nodes_config should be.
        :param sent_configs:
        The new node configurations for a particular chainlink chain
        :param current_configs:
        The currently stored node configurations for a particular chainlink
        chain
        :return:
        The new nodes configuration for a particular chainlink chain based on
        the current configs and the new configs.
        """
        correct_nodes_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                node_id = config['id']
                parent_id = config['parent_id']
                node_name = config['name']
                node_prometheus_urls = config['node_prometheus_urls'].split(',')
                monitor_node = str_to_bool(config['monitor_node'])
                monitor_prometheus = str_to_bool(config['monitor_prometheus'])

                # Check if all `monitor_<source>` are false. If this is the case
                # or `monitor_node` is disabled do not start a monitor and move
                # to the next config.
                sources_enabled = [monitor_prometheus]
                if not monitor_node or not any(sources_enabled):
                    continue

                node_config = ChainlinkNodeConfig(
                    node_id, parent_id, node_name, monitor_node,
                    monitor_prometheus, node_prometheus_urls)
                self._create_and_start_monitor_process(node_config, config_id,
                                                       ChainlinkNodeMonitor)
                correct_nodes_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                node_id = config['id']
                parent_id = config['parent_id']
                node_name = config['name']
                node_prometheus_urls = config['node_prometheus_urls'].split(',')
                monitor_node = str_to_bool(config['monitor_node'])
                monitor_prometheus = str_to_bool(config['monitor_prometheus'])
                sources_enabled = [monitor_prometheus]
                node_config = ChainlinkNodeConfig(
                    node_id, parent_id, node_name, monitor_node,
                    monitor_prometheus, node_prometheus_urls)
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()

                # Check if all `monitor_<source>` are false. If this is the case
                # or `monitor_node` is disabled do not restart a monitor, but
                # delete the previous process from the system and move to the
                # next config.
                if not monitor_node or not any(sources_enabled):
                    del self.config_process_dict[config_id]
                    del correct_nodes_configs[config_id]
                    log_and_print("Killed the monitor of {} ".format(
                        modified_configs[config_id]['name']), self.logger)
                    continue

                log_and_print(
                    "The configuration for {} was modified. A new monitor with "
                    "the latest configuration will be started.".format(
                        modified_configs[config_id]['name']), self.logger)

                self._create_and_start_monitor_process(node_config, config_id,
                                                       ChainlinkNodeMonitor)
                correct_nodes_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                node_name = config['name']
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()
                del self.config_process_dict[config_id]
                del correct_nodes_configs[config_id]
                log_and_print("Killed the monitor of {} ".format(node_name),
                              self.logger)
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        return correct_nodes_configs

    def _process_evm_node_configs(self, sent_configs: Dict,
                                  current_configs: Dict) -> Dict:
        """
        This function processes the new evm nodes configs for a particular
        chain. It creates/removes new processes, and it keeps a local copy of
        all changes being done step by step. This is done in this way so that if
        a sub-config is malformed or a process errors, we can keep track of what
        the new self._nodes_config should be.
        :param sent_configs:
        The new evm node configurations for a particular chain
        :param current_configs:
        The currently stored evm nodes configurations for a particular chain
        :return:
        The new evm nodes configuration for a particular chain based on the
        current configs and the new configs.
        """
        correct_nodes_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                node_id = config['id']
                parent_id = config['parent_id']
                node_name = config['name']
                node_http_url = config['node_http_url']
                monitor_node = str_to_bool(config['monitor_node'])

                # If `monitor_node` is disabled do not start a monitor and move
                # to the next config.
                if not monitor_node:
                    continue

                node_config = EVMNodeConfig(node_id, parent_id, node_name,
                                            monitor_node, node_http_url)
                self._create_and_start_monitor_process(node_config, config_id,
                                                       EVMNodeMonitor)
                correct_nodes_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                node_id = config['id']
                parent_id = config['parent_id']
                node_name = config['name']
                node_http_url = config['node_http_url']
                monitor_node = str_to_bool(config['monitor_node'])
                node_config = EVMNodeConfig(node_id, parent_id, node_name,
                                            monitor_node, node_http_url)
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()

                # If `monitor_node` is disabled do not restart a monitor, but
                # delete the previous process from the system and move to the
                # next config.
                if not monitor_node:
                    del self.config_process_dict[config_id]
                    del correct_nodes_configs[config_id]
                    log_and_print("Killed the monitor of {} ".format(
                        modified_configs[config_id]['name']), self.logger)
                    continue

                log_and_print(
                    "The configuration for {} was modified. A new monitor with "
                    "the latest configuration will be started.".format(
                        modified_configs[config_id]['name']), self.logger)

                self._create_and_start_monitor_process(node_config, config_id,
                                                       EVMNodeMonitor)
                correct_nodes_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                node_name = config['name']
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()
                del self.config_process_dict[config_id]
                del correct_nodes_configs[config_id]
                log_and_print("Killed the monitor of {} ".format(node_name),
                              self.logger)
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        return correct_nodes_configs

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.debug("Received configs %s. Now processing.", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        config_type = parsed_routing_key[3]
        if chain in self.nodes_configs \
                and config_type in self.nodes_configs[chain]:
            current_configs = self.nodes_configs[chain][config_type]
        else:
            current_configs = {}

        updated_configs = {}
        if config_type == 'evm_nodes_config':
            updated_configs = self._process_evm_node_configs(
                sent_configs, current_configs)
        elif parsed_routing_key[1].lower() == 'chainlink':
            updated_configs = self._process_chainlink_node_configs(
                sent_configs, current_configs)

        if chain not in self._nodes_configs:
            self._nodes_configs[chain] = {}

        self._nodes_configs[chain][config_type] = updated_configs

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
                    node_config = process_details['node_config']
                    monitor_type = process_details['monitor_type']
                    self._create_and_start_monitor_process(
                        node_config, config_id, monitor_type)
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
