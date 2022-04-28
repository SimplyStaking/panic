import copy
import json
import logging
import multiprocessing
from datetime import datetime
from typing import Dict, Optional, List

import pika.spec
from pika.adapters.blocking_connection import BlockingChannel

from src.configs.nodes.cosmos import CosmosNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.manager import MonitorsManager
from src.monitors.starters import start_cosmos_network_monitor
from src.utils.configs import parse_cosmos_node_config
from src.utils.constants.monitorables import MonitorableType
from src.utils.constants.names import COSMOS_NETWORK_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, TOPIC, NETWORK_MON_MAN_HEARTBEAT_QUEUE_NAME,
    PING_ROUTING_KEY, CONFIG_EXCHANGE, NETWORK_MON_MAN_CONFIGS_QUEUE_NAME,
    NODES_CONFIGS_ROUTING_KEY_CHAINS, MONITORABLE_EXCHANGE)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import str_to_bool


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

    def _extract_network_monitoring_fields_from_cosmos_configs(
            self, configs: Dict) -> (
            Optional[str], Optional[List[CosmosNodeConfig]], Optional[bool]):
        """
        Given the received configurations this function is able to extract some
        import fields which are needed for monitoring Cosmos networks
        :param configs: The received configurations without the DEFAULT key
        :return: (parent_id, data_sources, monitor_network)
        """
        parent_id = None
        data_sources = None
        monitor_network = None

        # Extract parent_id from configs. Return None if not all parent_ids are
        # equal.
        parent_ids_list = [config['parent_id'] for _, config in configs.items()]
        parent_ids_set = set(parent_ids_list)
        if len(parent_ids_set) == 1:
            parent_id = parent_ids_list[0]
        else:
            self.logger.error("The following config does not have identical "
                              "parent_ids: {}".format(json.dumps(configs)))

        # Extract monitor_network from configs. Return None if not all
        # monitor_network fields are equal.
        monitor_networks_list = [
            str_to_bool(config['monitor_network'])
            for _, config in configs.items()
        ]
        monitor_networks_set = set(monitor_networks_list)
        if len(monitor_networks_set) == 1:
            monitor_network = monitor_networks_list[0]
        else:
            self.logger.error("The following config does not have identical "
                              "monitor_network: {}".format(json.dumps(configs)))

        # Construct the data_sources. None is returned if there are no valid
        # data sources.
        non_validators: List[CosmosNodeConfig] = []
        validators: List[CosmosNodeConfig] = []
        for _, config in configs.items():
            cosmos_node_config = parse_cosmos_node_config(config)
            if cosmos_node_config.use_as_data_source:
                if str_to_bool(config['is_validator']):
                    validators.append(cosmos_node_config)
                else:
                    non_validators.append(cosmos_node_config)

        valid_data_sources: List[CosmosNodeConfig] = non_validators + validators
        if valid_data_sources:
            data_sources = valid_data_sources
        else:
            self.logger.error("The following config does not have valid data "
                              "sources for network monitoring: "
                              "{}".format(json.dumps(configs)))

        return parent_id, data_sources, monitor_network

    def _create_and_start_cosmos_network_monitor_process(
            self, data_sources: List[CosmosNodeConfig], parent_id: str,
            chain: str, base_chain: str, sub_chain: str) -> None:
        """
        This function creates and starts a Cosmos network monitor process
        for a particular chain
        :param data_sources: The nodes to be used to obtain network metrics
        such as governance proposals.
        :param parent_id: The ID of the chain
        :param chain: The name of the chain in the format
                    : "BASE_CHAIN SPECIFIC_CHAIN"
        :param base_chain: The name of the base chain
        :param sub_chain: The name of the sub chain
        :return: Nothing
        """
        log_and_print("Creating a new process for the network monitor of "
                      "{}".format(chain), self.logger)
        process = multiprocessing.Process(
            target=start_cosmos_network_monitor,
            args=(data_sources, parent_id, sub_chain,))

        # Kills children if parent is killed
        process.daemon = True
        process.start()
        self._config_process_dict[chain] = {}
        self._config_process_dict[chain][
            'component_name'] = COSMOS_NETWORK_MONITOR_NAME_TEMPLATE.format(
            sub_chain)
        self._config_process_dict[chain]['process'] = process
        self._config_process_dict[chain]['data_sources'] = data_sources
        self._config_process_dict[chain]['parent_id'] = parent_id
        self._config_process_dict[chain]['base_chain'] = base_chain
        self._config_process_dict[chain]['sub_chain'] = sub_chain

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
            if None not in [parent_id, data_sources,
                            monitor_network] and monitor_network:
                self._create_and_start_cosmos_network_monitor_process(
                    data_sources, parent_id, chain, base_chain, sub_chain
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
        if chain in self.network_configs:
            current_configs = self.network_configs[chain]
        else:
            current_configs = {}

        updated_configs = {}
        if parsed_routing_key[1].lower() == 'cosmos':
            updated_configs = self._process_cosmos_node_configs(
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
                    self._create_and_start_cosmos_network_monitor_process(
                        data_sources, parent_id, chain_name, base_chain,
                        sub_chain
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
