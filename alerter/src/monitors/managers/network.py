import copy
import json
import logging
import multiprocessing
from datetime import datetime
from typing import Dict, Optional, List, Callable, Any

import pika.spec
from pika.adapters.blocking_connection import BlockingChannel

from src.configs.nodes.cosmos import CosmosNodeConfig
from src.configs.nodes.node import NodeConfig
from src.configs.nodes.substrate import SubstrateNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.manager import (
    MonitorsManager)
from src.monitors.starters import (
    start_cosmos_network_monitor, start_substrate_network_monitor)
from src.utils.configs import (
    parse_cosmos_node_config, parse_substrate_node_config)
from src.utils.constants.monitorables import MonitorableType
from src.utils.constants.names import (
    COSMOS_NETWORK_MONITOR_NAME_TEMPLATE,
    SUBSTRATE_NETWORK_MONITOR_NAME_TEMPLATE)
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, TOPIC, NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME,
    PING_ROUTING_KEY, CONFIG_EXCHANGE, NETWORK_MON_MAN_CONFIGS_QUEUE_NAME,
    NODES_CONFIGS_ROUTING_KEY_CHAINS, MONITORABLE_EXCHANGE)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import str_to_bool, CONFIGS_WITH_VALIDATORS


class NetworkMonitorsManager(MonitorsManager):
    def __init__(self, logger: logging.Logger, manager_name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, manager_name, rabbitmq)

        self._network_configs = {}

    @property
    def network_configs(self) -> Dict:
        return self._network_configs

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.queue_declare(NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.basic_consume(NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         NETWORK_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(NETWORK_MON_MAN_CONFIGS_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", NETWORK_MON_MAN_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.rabbitmq.queue_bind(NETWORK_MON_MAN_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 NODES_CONFIGS_ROUTING_KEY_CHAINS)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          NETWORK_MON_MAN_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(NETWORK_MON_MAN_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Creating exchange '%s'", MONITORABLE_EXCHANGE)
        self.rabbitmq.exchange_declare(MONITORABLE_EXCHANGE, TOPIC, False, True,
                                       False, False)

        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    @staticmethod
    def _determine_data_sources_for_monitor(
            sent_configs: Dict,
            config_parser: Callable[[Dict], CONFIGS_WITH_VALIDATORS]) \
            -> List[CONFIGS_WITH_VALIDATORS]:
        """
        Given the configurations sent and a config parsing function, this
        function will determine the data sources to be given to the Network
        Monitor. This function computes the list of data sources as follows:
        [non_validator_data_sources, validator_data_sources]
        :param sent_configs: The configurations sent
        :param config_parser: A function taking the configurations sent as
                              parameter and returns an object representing the
                              parsed configurations
        :return: A list of configurations in the following format:
                 [non_validator_data_sources, validator_data_sources]
        """
        validator_data_sources = []
        non_validator_data_sources = []
        for _, config_data in sent_configs.items():
            # For each configuration, check if use_as_data_source is enabled and
            # classify if the data source is a validator or not.
            data_source_config = config_parser(config_data)
            if data_source_config.use_as_data_source:
                (validator_data_sources.append(data_source_config)
                 if data_source_config.is_validator
                 else non_validator_data_sources.append(data_source_config))

        return [*non_validator_data_sources, *validator_data_sources]

    def extract_same_value_field(
            self, sent_configs: Dict, field_name: str,
            value_parser: Callable[[Any], Any]) -> (bool, Any):
        """
        This function returns the value of a field in the config if that field
        has the same value across all sub-configurations
        :param sent_configs: The configurations sent
        :param field_name: The name of the field
        :param value_parser: A callable that should be used whenever parsing the
                             value from the config
        :return: (True, field_value) if the field has the same value across all
                  sub-configs
               : (False, None) otherwise
        """
        value_list = [
            value_parser(config[field_name])
            for config in sent_configs.values()
        ]
        value_set = set(value_list)
        if len(value_set) == 1:
            return True, value_list[0]
        else:
            self.logger.error(
                "The following config does not have identical {}: {}".format(
                    field_name, json.dumps(sent_configs)))
            return False, None

    def _extract_network_monitoring_fields_from_configs(
            self, configs: Dict,
            config_parser: Callable[[Dict], CONFIGS_WITH_VALIDATORS]) -> (
            Optional[str], List[CONFIGS_WITH_VALIDATORS], Optional[bool]):
        """
        Given the received configurations and a function which parses the
        individual sub-configs, this function is able to extract some
        common fields which are needed for monitoring networks
        :param configs: The received configurations without the DEFAULT key
        :return: (parent_id, data_sources, monitor_network)
        """
        _, parent_id = self.extract_same_value_field(configs, 'parent_id',
                                                     lambda x: x)
        _, monitor_network = self.extract_same_value_field(
            configs, 'monitor_network', str_to_bool)
        data_sources = self._determine_data_sources_for_monitor(
            configs, config_parser)

        return parent_id, data_sources, monitor_network

    def _extract_network_monitoring_fields_from_cosmos_configs(
            self, configs: Dict) -> (
            Optional[str], List[CosmosNodeConfig], Optional[bool]):
        """
        Given the received configurations this function is able to extract some
        fields which are needed for monitoring Cosmos networks
        :param configs: The received configurations without the DEFAULT key
        :return: (parent_id, data_sources, monitor_network)
        """
        return self._extract_network_monitoring_fields_from_configs(
            configs, parse_cosmos_node_config)

    def _extract_network_monitoring_fields_from_substrate_configs(
            self, configs: Dict) -> (
            Optional[str], List[SubstrateNodeConfig], Optional[bool],
            Optional[str]):
        """
        Given the received configurations this function is able to extract some
        fields which are needed for monitoring Substrate networks
        :param configs: The received configurations without the DEFAULT key
        :return: (parent_id, data_sources, monitor_network,
                  governance_addresses)
        """
        parent_id, data_sources, monitor_network = \
            self._extract_network_monitoring_fields_from_configs(
                configs, parse_substrate_node_config)
        gov_addrs_parsed, governance_addresses = self.extract_same_value_field(
            configs, 'governance_addresses', lambda x: x)

        if gov_addrs_parsed:
            governance_addresses = governance_addresses.split(',')

        return parent_id, data_sources, monitor_network, governance_addresses

    def _create_and_start_network_monitor_process(
            self, data_sources: List[NodeConfig], parent_id: str,
            chain: str, base_chain: str, sub_chain: str, starter_fn: Callable,
            network_monitor_name_template: str, *args) -> None:
        """
        This function creates and starts a network monitor process for a
        particular chain
        :param data_sources: The nodes to be used to obtain network metrics
        such as governance proposals
        :param parent_id: The ID of the chain
        :param chain: The name of the chain in the format
                    : "BASE_CHAIN SPECIFIC_CHAIN"
        :param base_chain: The name of the base chain
        :param sub_chain: The name of the sub chain
        :param starter_fn: The network monitor starter function
        :param args: any other arguments that need to be passed to the starter
        :return: Nothing
        """
        log_and_print("Creating a new process for the network monitor of "
                      "{}".format(chain), self.logger)
        process = multiprocessing.Process(
            target=starter_fn, args=(data_sources, parent_id, sub_chain, *args))

        # Kills children if parent is killed
        process.daemon = True
        process.start()
        self._config_process_dict[chain] = {}
        self._config_process_dict[chain][
            'component_name'] = network_monitor_name_template.format(sub_chain)
        self._config_process_dict[chain]['process'] = process
        self._config_process_dict[chain]['data_sources'] = data_sources
        self._config_process_dict[chain]['parent_id'] = parent_id
        self._config_process_dict[chain]['base_chain'] = base_chain
        self._config_process_dict[chain]['sub_chain'] = sub_chain
        self._config_process_dict[chain]['starter_fn'] = starter_fn
        self._config_process_dict[chain][
            'network_monitor_name_template'] = network_monitor_name_template
        self._config_process_dict[chain]['args'] = args

    def _process_cosmos_node_configs(
            self, sent_configs: Dict, current_configs: Dict, chain: str,
            base_chain: str, sub_chain: str) -> Dict:
        correct_configs = copy.deepcopy(current_configs)
        try:
            parent_id, data_sources, monitor_network = \
                self._extract_network_monitoring_fields_from_cosmos_configs(
                    sent_configs)
            potential_configs = {
                'parent_id': parent_id,
                'data_sources': data_sources,
                'monitor_network': monitor_network
            }

            if current_configs:
                # If there is a Cosmos Network Monitor running for the chain
                # check if the configurations have been modified. If yes first
                # terminate the monitor, if no it means that we can return as
                # the current state is the correct one.
                if potential_configs != current_configs:
                    previous_process = self.config_process_dict[chain][
                        'process']
                    previous_process.terminate()
                    previous_process.join()
                    del self.config_process_dict[chain]
                    correct_configs = {}
                    log_and_print("Killed the network monitor of {}".format(
                        chain), self.logger)
                else:
                    # This case may occur if config keys which are irrelevant
                    # for contract monitoring are modified
                    return correct_configs

            # Check if potentially there could be any Cosmos Network Monitor
            # that could be started for the chain. This is True if valid
            # monitoring fields can be parsed from the config and
            # monitor_network = True.
            if None not in [parent_id, monitor_network] and monitor_network:
                self._create_and_start_network_monitor_process(
                    data_sources, parent_id, chain, base_chain, sub_chain,
                    start_cosmos_network_monitor,
                    COSMOS_NETWORK_MONITOR_NAME_TEMPLATE)
                correct_configs = potential_configs

        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue.
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        self.process_and_send_monitorable_data(base_chain)

        return correct_configs

    def _process_substrate_node_configs(
            self, sent_configs: Dict, current_configs: Dict, chain: str,
            base_chain: str, sub_chain: str) -> Dict:
        correct_configs = copy.deepcopy(current_configs)
        try:
            parent_id, data_sources, monitor_network, governance_addresses = \
                self._extract_network_monitoring_fields_from_substrate_configs(
                    sent_configs)
            potential_configs = {
                'parent_id': parent_id,
                'data_sources': data_sources,
                'monitor_network': monitor_network,
                'governance_addresses': governance_addresses
            }

            if current_configs:
                # If there is a Substrate Network Monitor running for the chain
                # check if the configurations have been modified. If yes first
                # terminate the monitor, if no it means that we can return as
                # the current state is the correct one.
                if potential_configs != current_configs:
                    previous_process = self.config_process_dict[chain][
                        'process']
                    previous_process.terminate()
                    previous_process.join()
                    del self.config_process_dict[chain]
                    correct_configs = {}
                    log_and_print("Killed the network monitor of {}".format(
                        chain), self.logger)
                else:
                    # This case may occur if config keys which are irrelevant
                    # for contract monitoring are modified
                    return correct_configs

            # Check if potentially there could be any Substrate Network Monitor
            # that could be started for the chain. This is True if valid
            # monitoring fields can be parsed from the config and
            # monitor_network = True.
            if None not in [parent_id, monitor_network,
                            governance_addresses] and monitor_network:
                self._create_and_start_network_monitor_process(
                    data_sources, parent_id, chain, base_chain, sub_chain,
                    start_substrate_network_monitor,
                    SUBSTRATE_NETWORK_MONITOR_NAME_TEMPLATE,
                    governance_addresses)
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
        if chain in self.network_configs:
            current_configs = self.network_configs[chain]
        else:
            current_configs = {}

        updated_configs = {}
        if parsed_routing_key[1].lower() == 'cosmos':
            updated_configs = self._process_cosmos_node_configs(
                sent_configs, current_configs, chain, base_chain, sub_chain)
        elif parsed_routing_key[1].lower() == 'substrate':
            updated_configs = self._process_substrate_node_configs(
                sent_configs, current_configs, chain, base_chain, sub_chain)

        self._network_configs[chain] = updated_configs

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def process_and_send_monitorable_data(
            self, base_chain: str, _: MonitorableType = None) -> None:
        self.process_and_send_networks_monitorable_data(base_chain)

    def process_and_send_networks_monitorable_data(self, base_chain: str):
        """
        This function processes the required networks monitorable data which
        is then sent to RabbitMQ. This is done by using the config process
        dict and formed based on the base chain. This function overrides the
        send_monitorable_data function found in the MonitorsManager (parent).
        :param base_chain: The name of the base chain that has monitorable data
        """
        monitorable_data = {'manager_name': self._name, 'sources': []}
        for chain, source_data in self.config_process_dict.items():
            if base_chain == source_data['base_chain']:
                monitorable_data['sources'].append({
                    'chain_id': source_data['parent_id'],
                    'chain_name': source_data['sub_chain'],
                    'source_id': source_data['parent_id'],
                    'source_name': chain
                })

        routing_key = '{}.{}'.format(base_chain, MonitorableType.CHAINS.value)
        self.send_monitorable_data(routing_key, monitorable_data)

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
                    data_sources = process_details['data_sources']
                    parent_id = process_details['parent_id']
                    base_chain = process_details['base_chain']
                    sub_chain = process_details['sub_chain']
                    starter_fn = process_details['starter_fn']
                    network_monitor_name_template = process_details[
                        'network_monitor_name_template']
                    args = process_details['args']
                    self._create_and_start_network_monitor_process(
                        data_sources, parent_id, chain_name, base_chain,
                        sub_chain, starter_fn, network_monitor_name_template,
                        *args)
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
