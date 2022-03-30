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
from src.monitors.starters import start_chainlink_contracts_monitor
from src.utils.constants.monitorables import MonitorableType
from src.utils.constants.names import CL_CONTRACTS_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY, CONFIG_EXCHANGE,
    NODES_CONFIGS_ROUTING_KEY_CHAINS, TOPIC,
    CONTRACT_MON_MAN_HEARTBEAT_QUEUE_NAME, CONTRACT_MON_MAN_CONFIGS_QUEUE_NAME)
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
        import fields which are needed for monitoring Chainlink contracts
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
        parent_ids_list = [config['parent_id']
                           for _, config in configs.items()]
        parent_ids_set = set(parent_ids_list)
        if len(parent_ids_set) == 1:
            parent_id = parent_ids_list[0]
        else:
            self.logger.error("The following config does not have identical "
                              "parent_ids: {}".format(json.dumps(configs)))

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
                "weiwatchers_urls: {}".format(json.dumps(configs)))

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
                              "evm_node_urls: {}".format(json.dumps(configs)))

        # Extract the valid sub-configurations. A sub-configuration is valid
        # if monitoring is set, and there are valid prometheus url entries.
        valid_node_configs = []
        for _, config in configs.items():
            conf_node_id = config['id']
            conf_parent_id = config['parent_id']
            conf_node_name = config['name']
            conf_node_prometheus_urls = config['node_prometheus_urls'].split(
                ',')
            conf_monitor_node = str_to_bool(config['monitor_node'])
            conf_monitor_prometheus = str_to_bool(config['monitor_prometheus'])
            conf_monitor_contracts = str_to_bool(config['monitor_contracts'])

            if self._sub_chainlink_config_to_be_monitored(
                    conf_monitor_contracts, conf_monitor_prometheus):
                node_config = ChainlinkNodeConfig(
                    conf_node_id, conf_parent_id, conf_node_name,
                    conf_monitor_node, conf_monitor_prometheus,
                    conf_node_prometheus_urls)
                try:
                    node_config.enabled_sources_non_empty()
                    valid_node_configs.append(node_config)
                except EnabledSourceIsEmptyException as e:
                    self.logger.error(e.message)
                    self.logger.exception(e)
            else:
                self.logger.error(
                    "The following config was not enabled for contracts "
                    "monitoring: {}".format(json.dumps(configs)))
        if valid_node_configs:
            cl_node_configs = valid_node_configs
        else:
            self.logger.error("The following config does not have valid "
                              "chainlink node configs for contracts "
                              "monitoring: {}".format(json.dumps(configs)))

        return parent_id, weiwatchers_url, evm_nodes_urls, cl_node_configs

    def _create_and_start_chainlink_contracts_monitor_process(
            self, weiwatchers_url: str, evm_nodes: List[str],
            node_configs: List[ChainlinkNodeConfig], parent_id: str,
            full_chain_name: str, base_chain: str, sub_chain: str) -> None:
        """
        This function creates and starts a Chainlink contracts monitor process
        for a particular chain
        :param weiwatchers_url: The weiwatchers server url to be used
        :param evm_nodes: The evm nodes that will be used as data sources to
                        : obtain the contract metrics
        :param node_configs: The configurations of the nodes whose contract
                           : metrics should be retrieved for
        :param parent_id: The ID of the chain
        :param full_chain_name: The full name of the chain
        :param base_chain: The name of the base chain
        :param sub_chain: The name of the sub chain
        """
        log_and_print("Creating a new process for the Chainlink contracts "
                      "monitor of {}".format(full_chain_name), self.logger)
        process = multiprocessing.Process(
            target=start_chainlink_contracts_monitor,
            args=(weiwatchers_url, evm_nodes, node_configs, sub_chain,
                  parent_id,))

        # Kills children if parent is killed
        process.daemon = True
        process.start()
        self._config_process_dict[full_chain_name] = {}
        self._config_process_dict[full_chain_name][
            'component_name'] = CL_CONTRACTS_MONITOR_NAME_TEMPLATE.format(
            sub_chain)
        self._config_process_dict[full_chain_name]['process'] = process
        self._config_process_dict[full_chain_name][
            'weiwatchers_url'] = weiwatchers_url
        self._config_process_dict[full_chain_name]['evm_nodes'] = evm_nodes
        self._config_process_dict[full_chain_name][
            'node_configs'] = node_configs
        self._config_process_dict[full_chain_name]['parent_id'] = parent_id
        self._config_process_dict[full_chain_name]['base_chain'] = base_chain
        self._config_process_dict[full_chain_name]['sub_chain'] = sub_chain

    def _process_chainlink_node_configs(
            self, sent_configs: Dict, current_configs: Dict,
            full_chain_name: str, base_chain: str, sub_chain: str) -> Dict:
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
                # If there is a Chainlink Contracts Monitor running for the
                # chain check if the configurations have been modified. If yes
                # first terminate the monitor, if no it means that we can return
                # as the current state is the correct one
                if potential_configs != current_configs:
                    previous_process = \
                        self.config_process_dict[full_chain_name][
                            'process']
                    previous_process.terminate()
                    previous_process.join()
                    del self.config_process_dict[full_chain_name]
                    correct_configs = {}
                    log_and_print("Killed the Chainlink Contracts monitor of "
                                  "{}".format(full_chain_name), self.logger)
                else:
                    # This case may occur if config keys which are irrelevant
                    # for contract monitoring are modified
                    return correct_configs

            # Check if potentially there could be any Chainlink Contracts
            # Monitor that could be started for the chain. This is True if valid
            # monitoring fields can be parsed from the config
            if None not in [parent_id, weiwatchers_url, evm_nodes_urls,
                            cl_node_configs]:
                self._create_and_start_chainlink_contracts_monitor_process(
                    weiwatchers_url, evm_nodes_urls, cl_node_configs,
                    parent_id, full_chain_name, base_chain, sub_chain
                )
                correct_configs = potential_configs

        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue.
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        self.process_and_send_monitorable_data(base_chain)

        return correct_configs

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.debug("Received configs %s. Now processing.", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        base_chain = parsed_routing_key[1]
        sub_chain = parsed_routing_key[2]
        if chain in self.contracts_configs:
            current_configs = self.contracts_configs[chain]
        else:
            current_configs = {}

        updated_configs = {}
        if parsed_routing_key[1].lower() == 'chainlink':
            updated_configs = self._process_chainlink_node_configs(
                sent_configs, current_configs, chain, base_chain, sub_chain)

        self._contracts_configs[chain] = updated_configs

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def process_and_send_monitorable_data(
            self, base_chain: str, _: MonitorableType = None) -> None:
        self.process_and_send_contracts_monitorable_data(base_chain)

    def process_and_send_contracts_monitorable_data(
            self, base_chain: str):
        """
        This function processes the required contracts monitorable data which
        is then sent to RabbitMQ. This is done by using the config process
        dict and formed based on the base chain. This function overrides the
        send_monitorable_data function found in the MonitorsManager (parent).
        :param base_chain: The name of the base chain that has monitorable data
        """
        monitorable_data_nodes = {'manager_name': self._name, 'sources': []}
        monitorable_data_chains = {'manager_name': self._name, 'sources': []}
        for chain, source_data in self.config_process_dict.items():
            if base_chain == source_data['base_chain']:
                for node_config in source_data['node_configs']:
                    monitorable_data_nodes['sources'].append({
                        'chain_id': source_data['parent_id'],
                        'chain_name': source_data['sub_chain'],
                        'source_id': node_config.node_id,
                        'source_name': node_config.node_name
                    })

                monitorable_data_chains['sources'].append({
                    'chain_id': source_data['parent_id'],
                    'chain_name': source_data['sub_chain'],
                    'source_id': source_data['parent_id'],
                    'source_name': chain
                })

        routing_key_nodes = '{}.{}'.format(base_chain,
                                           MonitorableType.NODES.value)
        routing_key_chains = '{}.{}'.format(base_chain,
                                            MonitorableType.CHAINS.value)
        self.send_monitorable_data(routing_key_nodes,
                                   monitorable_data_nodes)
        self.send_monitorable_data(routing_key_chains,
                                   monitorable_data_chains)

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
            for chain, process_details in self.config_process_dict.items():
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
                    base_chain = process_details['base_chain']
                    sub_chain = process_details['sub_chain']
                    self._create_and_start_chainlink_contracts_monitor_process(
                        weiwatchers_url, evm_nodes, node_configs, parent_id,
                        chain, base_chain, sub_chain)
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
