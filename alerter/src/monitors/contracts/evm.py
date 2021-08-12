import copy
import json
import logging
from datetime import datetime
from datetime import timedelta
from http.client import IncompleteRead
from typing import List, Dict, Optional, Tuple

import pika
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError
from web3 import Web3
from web3.exceptions import ContractLogicError

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.constants.abis import V3, V4
from src.utils.constants.rabbitmq import (RAW_DATA_EXCHANGE,
                                          EVM_CONTRACTS_RAW_DATA_ROUTING_KEY)
from src.utils.data import get_json, get_prometheus_metrics_data
from src.utils.exceptions import (ComponentNotGivenEnoughDataSourcesException,
                                  MetricNotFoundException, PANICException,
                                  CouldNotRetrieveContractsException,
                                  NoSyncedDataSourceWasAccessibleException)
from src.utils.timing import TimedTaskLimiter

_PROMETHEUS_RETRIEVAL_TIME_PERIOD = 86400
_WEI_WATCHERS_RETRIEVAL_TIME_PERIOD = 86400


class EVMContractsMonitor(Monitor):
    """
    The EVMContractsMonitor is able to monitor contracts of an EVM based chain.
    For now, only chainlink chains are supported.
    """

    def __init__(self, monitor_name: str, weiwatchers_url: str,
                 evm_nodes: List[str], node_configs: List[ChainlinkNodeConfig],
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        # An exception is raised if the monitor is not given enough data
        # sources. The callee must also make sure that the given node_configs
        # have valid prometheus urls, and that prometheus and contracts
        # monitoring is enabled.
        if len(evm_nodes) == 0 or len(node_configs) == 0:
            field = 'evm_nodes' if len(evm_nodes) == 0 else 'node_configs'
            raise ComponentNotGivenEnoughDataSourcesException(
                monitor_name, field)

        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._node_configs = node_configs
        self._contracts_url = weiwatchers_url

        # Construct the Web3 interfaces
        self._evm_node_w3_interface = {}
        for evm_node_url in evm_nodes:
            self._evm_node_w3_interface[evm_node_url] = Web3(Web3.HTTPProvider(
                evm_node_url, request_kwargs={'timeout': 2}))

        # This dict stores the eth address of a chainlink node indexed by the
        # node id. The eth address is obtained from prometheus.
        self._node_eth_address = {}

        # This list stores a list of chain contracts data obtained from the wei
        # watchers link
        self._contracts_data = []

        # This dict stores a list of contract addresses that each node
        # participates on, indexed by the node id. The contracts addresses are
        # also filtered out according to their version.
        self._node_contracts = {}

        # This dict stores the last block height monitored for a node and
        # contract pair. This will be used to monitored round submissions.
        # This dict should have the following structure:
        # {<node_id>: {<contract_address>: <last_block_monitored>}}
        self._last_block_monitored = {}

        # Data retrieval limiters
        self._wei_watchers_retrieval_limiter = TimedTaskLimiter(
            timedelta(seconds=float(_WEI_WATCHERS_RETRIEVAL_TIME_PERIOD)))
        self._eth_address_retrieval_limiter = TimedTaskLimiter(
            timedelta(seconds=float(_PROMETHEUS_RETRIEVAL_TIME_PERIOD)))

    @property
    def node_configs(self) -> List[ChainlinkNodeConfig]:
        return self._node_configs

    @property
    def evm_node_w3_interface(self) -> Dict[str, Web3]:
        return self._evm_node_w3_interface

    @property
    def contracts_url(self) -> str:
        return self._contracts_url

    @property
    def node_eth_address(self) -> Dict[str, str]:
        return self._node_eth_address

    @property
    def contracts_data(self) -> List[Dict]:
        return self._contracts_data

    @property
    def node_contracts(self) -> Dict:
        return self._node_contracts

    @property
    def last_block_monitored(self) -> Dict:
        return self._last_block_monitored

    @property
    def wei_watchers_retrieval_limiter(self) -> TimedTaskLimiter:
        return self._wei_watchers_retrieval_limiter

    @property
    def eth_address_retrieval_limiter(self) -> TimedTaskLimiter:
        return self._eth_address_retrieval_limiter

    def _get_chain_contracts(self) -> List[Dict]:
        """
        This functions retrieves all the chain contracts along with some data.
        :return: A list of chain contracts together with data.
        """
        return get_json(self.contracts_url, self.logger, None, True)

    def _store_chain_contracts(self, contracts_data: List[Dict]) -> None:
        """
        This function stores the contracts data in the state
        :param contracts_data: The retrieved contracts data
        :return: None
        """
        self._contracts_data = contracts_data

    def _get_nodes_eth_address(self) -> Tuple[Dict, bool]:
        """
        This function attempts to get all the Ethereum addresses associated with
        each node from the prometheus endpoints. For each node it attempts to
        connect with the online source to get the eth address, however if the
        required data cannot be obtained from any source, the node is not added
        to the output dict, and the second element in the tuple is set to True
        indicating that the dict does not contain all node ids.
        :return: A tuple with the following structure:
                ({ node_id: node_eth_address }, bool)
        """
        metrics_to_retrieve = {
            'eth_balance': 'strict',
        }
        node_eth_address = {}
        error_occurred = False
        for node_config in self.node_configs:
            for prom_url in node_config.node_prometheus_urls:
                try:
                    metrics = get_prometheus_metrics_data(
                        prom_url, metrics_to_retrieve, self.logger,
                        verify=False)
                    for _, data_subset in enumerate(metrics['eth_balance']):
                        if "account" in json.loads(data_subset):
                            eth_address = json.loads(data_subset)['account']
                            node_eth_address[node_config.node_id] = eth_address
                            break
                    break
                except (ReqConnectionError, ReadTimeout, InvalidURL,
                        InvalidSchema, MissingSchema, IncompleteRead,
                        ChunkedEncodingError, ProtocolError) as e:
                    # If these errors are raised it may still be that another
                    # source can be accessed
                    self.logger.debug("Error when trying to access %s",
                                      prom_url)
                    self.logger.debug(e)
                except MetricNotFoundException as e:
                    # If these errors are raised then we can't get valid data
                    # from any node, as only 1 node is online at the same time.
                    self.logger.error("Error when trying to access %s",
                                      prom_url)
                    self.logger.exception(e)
                    break

            # If no ethereum address was added for a node, then an error has
            # occurred
            if node_config.node_id not in node_eth_address:
                error_occurred = True

        return node_eth_address, error_occurred

    def _store_nodes_eth_addresses(self, node_eth_address: Dict) -> None:
        """
        This function stores the node's associated ethereum addresses obtained
        from prometheus in the state
        :param node_eth_address: A dict associating a node's ID to it's ethereum
                               : address obtained from prometheus
        :return: None
        """
        self._node_eth_address = node_eth_address

    def _select_node(self) -> Optional[str]:
        """
        This function returns the url of the selected node. A node is selected
        if the HttpProvider is connected and the node is not syncing.
        :return: The url of the selected node.
               : None if no node is selected.
        """
        for node_url, w3_interface in self._evm_node_w3_interface.items():
            try:
                if w3_interface.isConnected() and not w3_interface.eth.syncing:
                    return node_url
            except (ReqConnectionError, ReadTimeout, IncompleteRead,
                    ChunkedEncodingError, ProtocolError, InvalidURL,
                    InvalidSchema, MissingSchema) as e:
                self.logger.debug("Error when trying to access %s", node_url)
                self.logger.debug(e)

        return None

    def _filter_contracts_by_node(self, selected_node: str) -> Dict:
        """
        This function checks which contracts a node participates on.
        :param selected_node: The evm node selected to retrieve the data from
        :return: A dict indexed by the node_id were each value is another dict
               : containing a list of v3 and v4 contracts the node participates
               : on
        """
        w3_interface = self.evm_node_w3_interface[selected_node]
        node_contracts = {}
        for node_id, eth_address in self._node_eth_address.items():
            transformed_eth_address = w3_interface.toChecksumAddress(
                eth_address)
            v3_participating_contracts = []
            v4_participating_contracts = []
            for contract_data in self._contracts_data:
                contract_address = contract_data['contractAddress']
                contract_version = contract_data['contractVersion']
                if contract_version == 3:
                    contract = w3_interface.eth.contract(
                        address=contract_address, abi=V3)
                    oracles = contract.functions.getOracles().call()
                    if transformed_eth_address in oracles:
                        v3_participating_contracts.append(contract_address)
                elif contract_version == 4:
                    contract = w3_interface.eth.contract(
                        address=contract_address, abi=V4)
                    transmitters = contract.functions.transmitters().call()
                    if transformed_eth_address in transmitters:
                        v4_participating_contracts.append(contract_address)

            node_contracts[node_id] = {}
            node_contracts[node_id]['v3'] = v3_participating_contracts
            node_contracts[node_id]['v4'] = v4_participating_contracts

        return node_contracts

    def _store_node_contracts(self, node_contracts: Dict) -> None:
        """
        This function stores the retrieved node_contracts inside the state.
        :param node_contracts: The retrieved node_contracts
        :return: None
        """
        self._node_contracts = node_contracts

    def _get_v3_data(self, w3_interface: Web3, node_eth_address: str,
                     node_id: str) -> Dict:
        """
        This function attempts to retrieve the v3 contract metrics for a node
        using an evm node as data source.
        :param w3_interface: The web3 interface used to get the data
        :param node_eth_address: The ethereum address of the node the metrics
                               : are associated with.
        :param node_id: The id of the node the metrics are associated with.
        :return: A dict with the following structure:
        {
            <v3_contract_address>: {
                'contractVersion': 3,
                'latestRound': int,
                'latestAnswer': int,
                'latestTimestamp': float,
                'answeredInRound': int
                'withdrawablePayment': int,
                'historicalRounds': {
                    'roundId': int,
                    'roundAnswer': int/None (if round consensus not reached
                                             yet),
                    'roundTimestamp': float/None (if round consensus not reached
                                                  yet),
                    'answeredInRound': int/None (if round consensus not reached
                                                 yet)
                    'nodeSubmission': int
                }
            }
        }
        """

        # If this is the case, then the node has no associated contracts stored
        if node_id not in self.node_contracts:
            return {}

        # This is the case for the first monitoring round
        if node_id not in self.last_block_monitored:
            self._last_block_monitored[node_id] = {}

        data = {}
        v3_contracts = self.node_contracts[node_id]['v3']
        for contract_address in v3_contracts:
            contract = w3_interface.eth.contract(address=contract_address,
                                                 abi=V3)
            transformed_eth_address = w3_interface.toChecksumAddress(
                node_eth_address)

            # Get all SubmissionReceived events related to the node in question
            # from the last block height not monitored until the current block
            # height. Note fromBlock and toBlock are inclusive.
            current_block_height = w3_interface.eth.get_block('latest')[
                'number']
            first_block_to_monitor = self.last_block_monitored[node_id][
                                         contract_address] + 1 \
                if contract_address in self.last_block_monitored[node_id] \
                else current_block_height
            event_filter = contract.events.SubmissionReceived.createFilter(
                fromBlock=first_block_to_monitor, toBlock=current_block_height,
                argument_filters={'oracle': transformed_eth_address})
            events = event_filter.get_all_entries()
            latest_round_data = contract.functions.latestRoundData().call()

            # Construct the latest round data
            data[contract_address] = {
                'contractVersion': 3,
                'latestRound': latest_round_data[0],
                'latestAnswer': latest_round_data[1],
                'latestTimestamp': latest_round_data[3],
                'answeredInRound': latest_round_data[4],
                'withdrawablePayment': contract.functions.withdrawablePayment(
                    transformed_eth_address).call(),
                'historicalRounds': []
            }

            # Construct the historical data
            historical_rounds = data[contract_address]['historicalRounds']
            for event in events:
                round_id = event['args']['round']
                round_answer = None
                round_timestamp = None
                answered_in_round = None
                consensus_reached = True

                # In v3 contracts we may encounter a scenario where a node
                # submitted their answer but consensus is not reached yet on
                # the price. If this happens, the last block height processed is
                # set to 1 - the block no of this event. This is done so that in
                # the next monitoring round we re-check the round again to see
                # if a consensus was reached. Note, if a consensus is not
                # reached, the node software establishes the round price to the
                # price of the previous round, so eventually no round processing
                # is stuck. Note, until consensus is reached, round data will
                # still be shown with roundAnswer, roundTimestamp and
                # answeredInRound set to None.
                try:
                    round_data = contract.functions.getRoundData(
                        round_id).call()
                    round_answer = round_data[1]
                    round_timestamp = round_data[3]
                    answered_in_round = round_data[4]
                except ContractLogicError as e:
                    self.logger.error('Error when retrieving round %s data. It '
                                      'may be that no consensus is reached '
                                      'yet.')
                    self.logger.exception(e)
                    consensus_reached = False

                historical_rounds.append({
                    'roundId': round_id,
                    'roundAnswer': round_answer,
                    'roundTimestamp': round_timestamp,
                    'answeredInRound': answered_in_round,
                    'nodeSubmission': event['args']['submission']
                })

                if not consensus_reached:
                    current_block_height = event['blockNumber'] - 1
                    break

            self._last_block_monitored[node_id][
                contract_address] = current_block_height

        return data

    def _get_v4_data(self, w3_interface: Web3, node_eth_address: str,
                     node_id: str) -> Dict:
        """
        This function attempts to retrieve the v4 contract metrics for a node
        using an evm node as data source.
        :param w3_interface: The web3 interface used to get the data
        :param node_eth_address: The ethereum address of the node the metrics
                               : are associated with.
        :param node_id: The id of the node the metrics are associated with.
        :return: A dict with the following structure:
        {
            <v4_contract_address>: {
                'contractVersion': 4,
                'latestRound': int,
                'latestAnswer': int,
                'latestTimestamp': float,
                'answeredInRound': int
                'owedPayment': int,
                'historicalRounds': {
                    'roundId': int,
                    'roundAnswer': int,
                    'roundTimestamp': float,
                    'answeredInRound': int,
                    'nodeSubmission': int,
                    'noOfObservations': int,
                    'noOfTransmitters': int
                }
            }
        }
        """

        # If this is the case, then the node has no associated contracts stored
        if node_id not in self.node_contracts:
            return {}

        # This is the case for the first monitoring round
        if node_id not in self.last_block_monitored:
            self._last_block_monitored[node_id] = {}

        data = {}
        v4_contracts = self.node_contracts[node_id]['v4']
        for contract_address in v4_contracts:
            contract = w3_interface.eth.contract(address=contract_address,
                                                 abi=V4)
            transformed_eth_address = w3_interface.toChecksumAddress(
                node_eth_address)

            # Get all NewTransmission events related to the node in question
            # from the last block height not monitored until the current block
            # height. Note fromBlock and toBlock are inclusive.
            current_block_height = w3_interface.eth.get_block('latest')[
                'number']
            first_block_to_monitor = self.last_block_monitored[node_id][
                                         contract_address] + 1 \
                if contract_address in self.last_block_monitored[node_id] \
                else current_block_height
            event_filter = contract.events.NewTransmission.createFilter(
                fromBlock=first_block_to_monitor, toBlock=current_block_height)
            events = event_filter.get_all_entries()
            latest_round_data = contract.functions.latestRoundData().call()
            transmitters = contract.functions.transmitters().call()

            try:
                node_transmitter_index = transmitters.index(
                    transformed_eth_address)
            except ValueError:
                # If the node is no longer a transmitter of this contract,
                # move on to the next contract
                self.logger.warning("Node %s is no longer participating on "
                                    "contract %s", node_id, contract_address)
                continue

            # Construct the latest round data
            data[contract_address] = {
                'contractVersion': 4,
                'latestRound': latest_round_data[0],
                'latestAnswer': latest_round_data[1],
                'latestTimestamp': latest_round_data[3],
                'answeredInRound': latest_round_data[4],
                'owedPayment': contract.functions.owedPayment(
                    transformed_eth_address).call(),
                'historicalRounds': []
            }

            # Construct the historical data
            historical_rounds = data[contract_address]['historicalRounds']
            for event in events:
                round_id = event['args']['aggregatorRoundId']
                round_data = contract.functions.getRoundData(round_id).call()
                observers_list = list(event['args']['observers'])

                try:
                    answer_index = observers_list.index(node_transmitter_index)
                    node_submission = event['args']['observations'][
                        answer_index]
                except ValueError:
                    self.logger.warning("Node %s did not send an answer in "
                                        "round %s for contract %s", node_id,
                                        round_id, contract_address)
                    node_submission = None

                historical_rounds.append({
                    'roundId': round_id,
                    'roundAnswer': round_data[1],
                    'roundTimestamp': round_data[3],
                    'answeredInRound': round_data[4],
                    'nodeSubmission': node_submission,
                    'noOfObservations': len(event['args']['observations']),
                    'noOfTransmitters': len(transmitters),
                })

            self._last_block_monitored[node_id][
                contract_address] = current_block_height

        return data

    def _get_data(self, w3_interface: Web3, node_eth_address: str,
                  node_id: str) -> Dict:
        """
        This function retrieves the contracts' v3 and v4 metrics data for a
        single node using an evm node as data source.
        :param w3_interface: The web3 interface associated with the evm node
                           : used as data source
        :param node_eth_address: The Ethereum address of the node
        :param node_id: The identifier of the node
        :return: A dict containing all contract metrics
        """
        v3_data = self._get_v3_data(w3_interface, node_eth_address, node_id)
        v4_data = self._get_v4_data(w3_interface, node_eth_address, node_id)
        return {**v3_data, **v4_data}

    def _display_data(self, data: Dict) -> str:
        # This function assumes that the data has been obtained and processed
        # successfully by the node monitor
        return json.dumps(data)

    def _process_error(self, error: PANICException, parent_id: str) -> Dict:
        """
        This function attempts to process the error which occurred when
        retrieving data. Note that since an error will only be generated for an
        entire group of nodes, there is no node specific meta_data added.
        :param error: The detected error
        :param parent_id: The ID of the chain
        :return: A dict with the error data together with some meta data
        """
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'parent_id': parent_id,
                    'time': datetime.now().timestamp()
                },
                'message': error.message,
                'code': error.code,
            }
        }

        return processed_data

    def _process_retrieved_data(self, data: Dict,
                                node_config: ChainlinkNodeConfig) -> Dict:
        """
        This function attempts to process the retrieved data for any node.
        :param data: The retrieved data
        :param node_config: The configuration of the node in question
        :return: A dict with the retrieved data together with some meta data
        """
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': node_config.node_name,
                    'node_id': node_config.node_id,
                    'node_parent_id': node_config.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': copy.deepcopy(data),
            }
        }

        return processed_data

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=EVM_CONTRACTS_RAW_DATA_ROUTING_KEY, body=data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to '%s' exchange", RAW_DATA_EXCHANGE)

    def _get_node_config_by_node_id(
            self, node_id: str) -> Optional[ChainlinkNodeConfig]:
        """
        Given a node_id, this function attempts to return the first node
        configuration it finds with the queried node_id.
        :param node_id: The node id to be matched
        :return: A node config from self.node_configs having node id node_id
        """
        for node_config in self.node_configs:
            if node_id == node_config.node_id:
                return node_config

        return None

    def _monitor(self) -> None:
        data_retrieval_failed = False
        data_retrieval_exception = None
        re_filter = False
        try:
            # Retrieve the contracts data every time period.
            if self.wei_watchers_retrieval_limiter.can_do_task():
                contracts_data = self._get_chain_contracts()
                self._store_chain_contracts(contracts_data)
                self.wei_watchers_retrieval_limiter.did_task()
                re_filter = True
        except (ReqConnectionError, ReadTimeout, IncompleteRead,
                ChunkedEncodingError, ProtocolError, InvalidURL, InvalidSchema,
                MissingSchema) as e:
            data_retrieval_failed = True
            data_retrieval_exception = CouldNotRetrieveContractsException(
                self.monitor_name, self.contracts_url)
            self.logger.error(data_retrieval_exception.message)
            self.logger.exception(e)

        # Retrieve the eth address of the node every time period
        if self.eth_address_retrieval_limiter.can_do_task():
            node_eth_address, error_occurred = self._get_nodes_eth_address()
            self._store_nodes_eth_addresses(node_eth_address)
            re_filter = True

            # If an error occurred we want to get the eth address again in the
            # next monitoring round
            if not error_occurred:
                self.eth_address_retrieval_limiter.did_task()

        if not data_retrieval_failed:
            # Select an evm node for contract metrics retrieval if no data
            # retrieval error already occurred.
            selected_node_url = self._select_node()
            if selected_node_url is None:
                # If no url was selected, then no synced evm node was
                # accessible. Hence, raise a meaningful error. Here we are
                # assuming that all nodes have the same parent_id
                data_retrieval_exception = \
                    NoSyncedDataSourceWasAccessibleException(self.monitor_name,
                                                             'EVM node')
                try:
                    processed_data = self._process_error(
                        data_retrieval_exception,
                        self.node_configs[0].parent_id,
                    )
                except Exception as error:
                    # Do not send data if we experienced processing errors
                    self.logger.error("Could not process error %r",
                                      data_retrieval_exception)
                    self.logger.exception(error)
                    return

                self._send_data(processed_data)
            else:
                # If a url was selected, we need to retrieve the contract's
                # metrics
                if re_filter:
                    # If contracts or eth addresses were retrieved in this
                    # round, then we must do the re-filtering.
                    node_contracts = self._filter_contracts_by_node(
                        selected_node_url)
                    self._store_node_contracts(node_contracts)

                w3_interface = self.evm_node_w3_interface[selected_node_url]
                for node_id, node_eth_address in self.node_eth_address.items():
                    try:
                        data = self._get_data(w3_interface, node_eth_address,
                                              node_id)
                    except (ReqConnectionError, ReadTimeout, IncompleteRead,
                            ChunkedEncodingError, ProtocolError, InvalidURL,
                            InvalidSchema, MissingSchema) as e:
                        self.logger.error("Could not retrieve contract metrics"
                                          "from %s for node %s",
                                          selected_node_url, node_id)
                        self.logger.exception(e)
                        continue

                    try:
                        node_config = self._get_node_config_by_node_id(node_id)
                        processed_data = self._process_retrieved_data(
                            data, node_config
                        )
                    except Exception as error:
                        # Do not send data if we experienced processing errors,
                        # and move on to the next node
                        self.logger.error("Could not process data %s", data)
                        self.logger.exception(error)
                        continue

                    self._send_data(processed_data)

                    self.logger.info(self._display_data(processed_data))
        else:
            # If an error occurred before retrieving any metrics, process the
            # error and send it. Here we are assuming that all nodes have the
            # same parent_id
            try:
                processed_data = self._process_error(
                    data_retrieval_exception, self.node_configs[0].parent_id,
                )
            except Exception as error:
                # Do not send data if we experienced processing errors
                self.logger.error("Could not process error %r",
                                  data_retrieval_exception)
                self.logger.exception(error)
                return

            self._send_data(processed_data)

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)
