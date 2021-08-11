import copy
import json
import logging
import multiprocessing
from datetime import datetime
from typing import Dict, List, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.manager import MonitorsManager
from src.monitors.starters import start_evm_contracts_monitor
from src.utils.constants.names import EVM_CONTRACTS_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY,
    CONFIG_EXCHANGE, NODES_CONFIGS_ROUTING_KEY_CHAINS, TOPIC,
    CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME,
    CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME)
from src.utils.exceptions import (EnabledSourceIsEmptyException,
                                  MessageWasNotDeliveredException)
from src.utils.logging import log_and_print
from src.utils.types import str_to_bool


class ContractMonitorsManager(MonitorsManager):

    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)

        self._contracts_configs = {}

    @property
    def contracts_configs(self) -> Dict:
        return self._contracts_configs

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.queue_declare(CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.basic_consume(CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.rabbitmq.queue_bind(CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    @staticmethod
    def _sub_chainlink_config_to_be_monitored(monitor_contracts: bool,
                                              monitor_prometheus: bool) -> bool:
        """
        This method checks that the sub-configuration was set to be monitored
        :param monitor_contracts: The value of monitor_contracts switch
        :param monitor_prometheus: The value of monitor_prometheus switch
        :return: True if both switches are set, False otherwise
        """
        return monitor_contracts and monitor_prometheus

    def _extract_monitoring_fields_from_chainlink_configs(
            self, configs: Dict) -> (
            Optional[str], Optional[str], Optional[List[str]],
            Optional[List[ChainlinkNodeConfig]]):
        """
        Given the received configurations this function is able to extract some
        import fields which are needed for monitoring EVM contracts
        :param configs: The received configurations without the DEFAULT key
        :return: (parent_id, weiwatchers_url, evm_nodes_urls,
                  chainlink_node_configs)
        """
        parent_id = None
        weiwatchers_url = None
        evm_nodes_urls = None
        cl_node_configs = None

        # Extract parent_id from configs. Return None if not all parent_ids are
        # equal.
        parent_ids_list = [config['parent_id'] for _, config in configs.items()]
        parent_ids_set = set(parent_ids_list)
        if len(parent_ids_set) == 1:
            parent_id = parent_ids_list[0]
        else:
            self.logger.error("The following config does not have identical "
                              "parent_ids: %s".format(json.dumps(configs)))

        # Extract weiwatchers_url from configs. Return None if not all
        # weiwatchers_urls are equal.
        weiwatchers_url_list = [
            config['weiwatchers_url'] for _, config in configs.items()
        ]
        weiwatchers_url_set = set(weiwatchers_url_list)
        if len(weiwatchers_url_set) == 1:
            weiwatchers_url = weiwatchers_url_list[0]
        else:
            self.logger.error(
                "The following config does not have identical "
                "weiwatchers_urls: %s".format(json.dumps(configs)))

        # Extract evm_nodes_urls from configs. Return None if not all
        # evm_nodes_urls are equal.
        evm_nodes_urls_list = [
            config['evm_nodes_urls'] for _, config in configs.items()
        ]
        evm_nodes_urls_set = set(evm_nodes_urls_list)
        if len(evm_nodes_urls_set) == 1:
            evm_nodes_urls = evm_nodes_urls_list[0].split(',')
        else:
            self.logger.error("The following config does not have identical "
                              "evm_node_urls: %s".format(json.dumps(configs)))

        # Extract the valid sub-configurations. A sub-configuration is valid
        # if monitoring is set, and there are valid prometheus url entries.
        valid_node_configs = []
        for _, config in configs.items():
            node_id = config['id']
            parent_id = config['parent_id']
            node_name = config['name']
            node_prometheus_urls = config['node_prometheus_urls'].split(',')
            monitor_node = str_to_bool(config['monitor_node'])
            monitor_prometheus = str_to_bool(config['monitor_prometheus'])
            monitor_contracts = str_to_bool(config['monitor_contracts'])

            if self._sub_chainlink_config_to_be_monitored(monitor_contracts,
                                                          monitor_prometheus):
                node_config = ChainlinkNodeConfig(
                    node_id, parent_id, node_name, monitor_node,
                    monitor_prometheus, node_prometheus_urls)
                try:
                    node_config.enabled_sources_non_empty()
                    valid_node_configs.append(node_config)
                except EnabledSourceIsEmptyException as e:
                    self.logger.error(e.message)
                    self.logger.exception(e)
            else:
                self.logger.error(
                    "The following config was not enabled for contracts "
                    "monitoring: %s".format(json.dumps(configs)))
        if valid_node_configs:
            cl_node_configs = valid_node_configs
        else:
            self.logger.error("The following config does not have valid "
                              "chainlink node configs for contracts "
                              "monitoring: %s".format(json.dumps(configs)))

        return parent_id, weiwatchers_url, evm_nodes_urls, cl_node_configs

    def _create_and_start_evm_contracts_monitor_process(
            self, weiwatchers_url: str, evm_nodes: List[str],
            node_configs: List[ChainlinkNodeConfig], parent_id: str,
            chain_name: str) -> None:
        """
        This function creates and starts and EVM contracts monitor process for
        a particular chain
        :param weiwatchers_url: The weiwatchers server url to be used
        :param evm_nodes: The evm nodes that will be used as data sources to
                        : obtain the contract metrics
        :param node_configs: The configurations of the nodes whose contract
                           : metrics should be retrieved for
        :param parent_id: The ID of the chain
        :param chain_name: The name of the chain
        :return:
        """
        log_and_print("Creating a new process for the EVM contracts monitor of "
                      "{}".format(chain_name), self.logger)
        process = multiprocessing.Process(
            target=start_evm_contracts_monitor,
            args=(weiwatchers_url, evm_nodes, node_configs, parent_id,))
        # Kills children if parent is killed
        process.daemon = True
        process.start()
        self._config_process_dict[chain_name] = {}
        self._config_process_dict[chain_name]['component_name'] = \
            EVM_CONTRACTS_MONITOR_NAME_TEMPLATE.format(parent_id)
        self._config_process_dict[chain_name]['process'] = process
        self._config_process_dict[chain_name][
            'weiwatchers_url'] = weiwatchers_url
        self._config_process_dict[chain_name]['evm_nodes'] = evm_nodes
        self._config_process_dict[chain_name]['node_configs'] = node_configs
        self._config_process_dict[chain_name]['parent_id'] = parent_id
        self._config_process_dict[chain_name]['chain_name'] = chain_name

    def _process_chainlink_node_configs(
            self, sent_configs: Dict, current_configs: Dict,
            chain_name: str) -> Dict:
        correct_configs = copy.deepcopy(current_configs)
        try:
            parent_id, weiwatchers_url, evm_nodes_urls, cl_node_configs = \
                self._extract_monitoring_fields_from_chainlink_configs(
                    sent_configs)
            potential_configs = {
                'parent_id': parent_id,
                'weiwatchers_url': weiwatchers_url,
                'evm_nodes_urls': evm_nodes_urls,
                'chainlink_node_configs': cl_node_configs
            }

            if current_configs:
                # If there is an EVM Contracts Monitor running for the chain
                # check if the configurations have been modified. If yes first
                # terminate the monitor.
                if potential_configs != current_configs:
                    previous_process = self.config_process_dict[chain_name][
                        'process']
                    previous_process.terminate()
                    previous_process.join()
                    del self.config_process_dict[chain_name]
                    correct_configs = {}
                    log_and_print("Killed the EVM Contracts monitor of "
                                  "%s".format(chain_name), self.logger)

            # Check if potentially there could be any EVM Contracts Monitor that
            # could be started for the chain. This is True if valid monitoring
            # fields can be parsed from the config
            if None not in [parent_id, weiwatchers_url, evm_nodes_urls,
                            cl_node_configs]:
                self._create_and_start_evm_contracts_monitor_process(
                    weiwatchers_url, evm_nodes_urls, cl_node_configs,
                    parent_id, chain_name
                )
                correct_configs[chain_name] = potential_configs

        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue.
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        return correct_configs

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info("Received configs %s. Now processing.", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        if chain in self.contracts_configs:
            current_configs = self.contracts_configs[chain]
        else:
            current_configs = {}

        updated_configs = {}
        if parsed_routing_key[1].lower() == 'chainlink':
            updated_configs = self._process_chainlink_node_configs(
                sent_configs, current_configs, chain)

        self._contracts_configs[chain] = updated_configs

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
            for chain_name, process_details in self.config_process_dict.items():
                process = process_details['process']
                component_name = process_details['component_name']
                if process.is_alive():
                    heartbeat['running_processes'].append(component_name)
                else:
                    heartbeat['dead_processes'].append(component_name)
                    process.join()  # Just in case, to release resources

                    # Restart dead process
                    weiwatchers_url = process_details['weiwatchers_url']
                    evm_nodes = process_details['evm_nodes']
                    node_configs = process_details['node_configs']
                    parent_id = process_details['parent_id']
                    self._create_and_start_evm_contracts_monitor_process(
                        weiwatchers_url, evm_nodes, node_configs, parent_id,
                        chain_name
                    )
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
