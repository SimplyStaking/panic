import base64
import copy
import logging
from datetime import datetime
from http.client import IncompleteRead
from typing import List, Dict, Optional, Callable, Union

import pika
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.configs.nodes.cosmos import CosmosNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.cosmos import (
    CosmosMonitor, _REST_VERSION_COSMOS_SDK_0_42_6,
    _REST_VERSION_COSMOS_SDK_0_39_2, _VERSION_INCOMPATIBILITY_EXCEPTIONS)
from src.utils.constants.cosmos import (
    BOND_STATUS_BONDED, BOND_STATUS_UNBONDED, BOND_STATUS_UNBONDING,
    BOND_STATUS_INVALID)
from src.utils.constants.rabbitmq import (RAW_DATA_EXCHANGE,
                                          COSMOS_NODE_RAW_DATA_ROUTING_KEY)
from src.utils.cosmos import (
    bech32_to_address)
from src.utils.data import get_prometheus_metrics_data
from src.utils.exceptions import (
    NodeIsDownException, DataReadingException, InvalidUrlException,
    MetricNotFoundException, PANICException,
    CosmosSDKVersionIncompatibleException, CosmosRestServerApiCallException,
    IncorrectJSONRetrievedException, NoSyncedDataSourceWasAccessibleException,
    CannotConnectWithDataSourceException,
    CosmosRestServerDataCouldNotBeObtained, TendermintRPCCallException,
    TendermintRPCIncompatibleException, TendermintRPCDataCouldNotBeObtained)


class CosmosNodeMonitor(CosmosMonitor):
    """
    The node monitor supports the retrieval of prometheus, Cosmos Rest Server
    and Tendermint RPC data. In the case of the Rest Server, v0.42.6 and v0.39.2
    of the Cosmos SDK are directly supported. If a node or data source has a
    different Cosmos SDK version, the monitor attempts to retrieve the data
    using all the supported versions just in case that version is still
    compatible, however, this might result into unexpected behaviour.

    Note that different chains might also carry different versions of
    Tendermint, resulting in different structures in the data retrieved. This
    must also be catered with in the implemented data retrievals. In
    development, only Tendermint versions for the latest Cosmos SDK chains were
    considered. The Tendermint versions used by the latest Cosmos SDK chains
    considered were v0.33.7, v0.33.8, v0.33.9, v0.34.11, v0.34.12, v0.34.14.
    """

    def __init__(self, monitor_name: str, node_config: CosmosNodeConfig,
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi,
                 data_sources: List[CosmosNodeConfig]) -> None:

        super().__init__(monitor_name, data_sources, logger, monitor_period,
                         rabbitmq)
        self._node_config = node_config

        # If for archive data retrieval the selected data source is not an
        # archive node (could be that no archive node satisfied the selection
        # criteria or none were given by the user), the monitor won't go back
        # more than self._pruning_catchup_blocks due to a pruned state. In
        # cosmos this value is normally set to 100, however we will use 90 to
        # cater for some possible delays in the data retrieval process.
        self._pruning_catchup_blocks = 90

        # If the node is down for a long time, there might be a big discrepancy
        # between the last_height_monitored_<interface> and the current_height
        # and thus there might be a lot of data to retrieve + blocks to
        # traverse, possibly retrieving data which is no longer relevant.
        # Therefore, this variable will store the max number of blocks the
        # monitor goes back to (only if the node is archive as this is a large
        # number)
        self._max_catchup_blocks = 300

        # Construct list of archive nodes from data sources
        self._archive_nodes = [
            node for node in self.data_sources if node.is_archive_node
        ]

        # --------------------------- PROMETHEUS -------------------------------
        # tendermint_consensus_validator_power needs to be set as optional
        # because it is non-existent for nodes which are not in the validator
        # set.
        self._prometheus_metrics = {
            'tendermint_consensus_latest_block_height': 'strict',
            'tendermint_consensus_validator_power': 'optional',
        }

        # -------------------------- TENDERMINT RPC ---------------------------
        # This will store the last height that the monitor queried when
        # retrieving historical data from tendermint RPC
        self._last_height_monitored_tendermint = None

        # This will be obtained directly from the Tendermint RPC interface of
        # the node at each monitoring round if it is a validator
        self._validator_consensus_address = None

    @property
    def node_config(self) -> CosmosNodeConfig:
        return self._node_config

    @property
    def pruning_catchup_blocks(self) -> int:
        return self._pruning_catchup_blocks

    @property
    def max_catchup_blocks(self) -> int:
        return self._max_catchup_blocks

    @property
    def archive_nodes(self) -> List[CosmosNodeConfig]:
        return self._archive_nodes

    @property
    def prometheus_metrics(self) -> Dict[str, str]:
        return self._prometheus_metrics

    @property
    def last_height_monitored_tendermint(self) -> Optional[int]:
        return self._last_height_monitored_tendermint

    @property
    def validator_consensus_address(self) -> Optional[str]:
        return self._validator_consensus_address

    @staticmethod
    def _parse_validator_status(validator_status: Union[str, int]) -> str:
        """
        This function parses the validator status retrieved from the source node
        and returns the corresponding value to be used by the PANIC components.
        Note that this function is compatible with both v0.39.2 and v0.42.6 of
        the Cosmos SDK.
        :param validator_status: The status retrieved from the source node
        :return: The corresponding bonded status to be used by the PANIC
               : components
        """
        if validator_status in [2, "BOND_STATUS_BONDED"]:
            return BOND_STATUS_BONDED
        elif validator_status in [1, "BOND_STATUS_UNBONDING"]:
            return BOND_STATUS_UNBONDING
        elif validator_status in [0, "BOND_STATUS_UNBONDED"]:
            return BOND_STATUS_UNBONDED
        else:
            return BOND_STATUS_INVALID

    def _get_cosmos_rest_v0_39_2_indirect_data_validator(
            self, source: CosmosNodeConfig) -> Dict:
        """
        This function retrieves node specific metrics using a different node as
        data source. We do not use the node directly since the node may be
        offline or syncing, thus the data may be corrupt. Note that as a last
        resource the manager may supply the node itself as data source. To
        retrieve this data we use version v0.39.2 of the Cosmos SDK for the REST
        server. NOTE: In this function we are assuming that the node being
        monitored is a validator.
        :param source: The chosen data source
        :return: A dict containing all indirect metrics
        :raises: CosmosSDKVersionIncompatibleException if the Cosmos SDK version
                 of the source is not compatible with v0.39.2
               : CosmosRestServerApiCallException if an API call errors
               : DataReadingException if data cannot be read from the source
               : CannotConnectWithDataSourceException if we cannot connect with
                 the data source
               : InvalidUrlException if the URL of the data source does not have
                 a valid schema
               : IncorrectJSONRetrievedException if the structure of the data
                 returned by the endpoints is not as expected. This could be
                 both due to Tendermint or a Cosmos SDK update
        """
        operator_address = self.node_config.operator_address
        source_url = source.cosmos_rest_url
        source_name = source.node_name

        def retrieval_process() -> Dict:
            staking_validators = \
                self.cosmos_rest_server_api.execute_with_checks(
                    self.cosmos_rest_server_api.get_staking_validators_v0_39_2,
                    [source_url, operator_address, {}], source_name,
                    _REST_VERSION_COSMOS_SDK_0_39_2)
            bond_status = self._parse_validator_status(
                staking_validators['result']['status'])
            return {
                'bond_status': bond_status,

                # The 'jailed' keyword is normally exposed in staking/validators
                # for v0.39.2 of the Cosmos SDK only. If we encounter nodes on
                # this version which do not expose it we might need to use
                # slashing/signing_infos
                'jailed': staking_validators['result']['jailed'],
            }

        return self._execute_cosmos_rest_retrieval_with_exceptions(
            retrieval_process, source_name, source_url,
            _REST_VERSION_COSMOS_SDK_0_39_2)

    def _get_cosmos_rest_v0_42_6_indirect_data_validator(
            self, source: CosmosNodeConfig) -> Dict:
        """
        This function retrieves node specific metrics using a different node as
        data source. We do not use the node directly since the node may be
        offline or syncing, thus the data may be corrupt. Note that as a last
        resource the manager may supply the node itself as data source. To
        retrieve this data we use version v0.42.6 of the Cosmos SDK for the REST
        server. NOTE: In this function we are assuming that the node being
        monitored is a validator.
        :param source: The chosen data source
        :return: A dict containing all indirect metrics
        :raises: CosmosSDKVersionIncompatibleException if the Cosmos SDK version
                 of the source is not compatible with v0.42.6
               : CosmosRestServerApiCallException if an error occurs during an
                 API call
               : DataReadingException if data cannot be read from the source
               : CannotConnectWithDataSourceException if we cannot connect with
                 the data source
               : InvalidUrlException if the URL of the data source does not have
                 a valid schema
               : IncorrectJSONRetrievedException if the structure of the data
                 returned by the endpoints is not as expected. This could be
                 both due to a Tendermint or Cosmos SDK update
        """
        operator_address = self.node_config.operator_address
        source_url = source.cosmos_rest_url
        source_name = source.node_name

        def retrieval_process() -> Dict:
            staking_validators = \
                self.cosmos_rest_server_api.execute_with_checks(
                    self.cosmos_rest_server_api.get_staking_validators_v0_42_6,
                    [source_url, operator_address, {}], source_name,
                    _REST_VERSION_COSMOS_SDK_0_42_6)
            bond_status = self._parse_validator_status(
                staking_validators['validator']['status'])
            return {
                'bond_status': bond_status,

                # The 'jailed' keyword is normally exposed in
                # cosmos/staking/v1beta1/validators for v0.42.6 of the Cosmos
                # SDK only. If we encounter nodes on this version which do not
                # expose it we might need to use
                # /cosmos/slashing/v1beta1/signing_infos
                'jailed': staking_validators['validator']['jailed'],
            }

        return self._execute_cosmos_rest_retrieval_with_exceptions(
            retrieval_process, source_name, source_url,
            _REST_VERSION_COSMOS_SDK_0_42_6)

    def _get_cosmos_rest_indirect_data(self, source: CosmosNodeConfig,
                                       sdk_version: str) -> Dict:
        """
        This function returns the Cosmos REST indirect metrics of the node
        depending on whether the node is a validator or a non-validator. If the
        node is a non-validator, then default data is returned. If the node is
        a validator, the Cosmos REST retrieval function corresponding to version
        <sdk_version> is executed.
        :param source: The data source
        :param sdk_version: The cosmos sdk REST version used to get the data
        :return: The Cosmos REST indirect metrics
        """
        source_url = source.cosmos_rest_url
        if not source_url:
            return {
                'bond_status': None,
                'jailed': None
            }

        if self.node_config.is_validator:
            if sdk_version == _REST_VERSION_COSMOS_SDK_0_39_2:
                return self._get_cosmos_rest_v0_39_2_indirect_data_validator(
                    source)
            elif sdk_version == _REST_VERSION_COSMOS_SDK_0_42_6:
                return self._get_cosmos_rest_v0_42_6_indirect_data_validator(
                    source)
            else:
                return {
                    'bond_status': None,
                    'jailed': None
                }

        return {
            'bond_status': BOND_STATUS_UNBONDED,
            'jailed': False,
        }

    def _get_cosmos_rest_version_data(self, sdk_version: str) -> (
            Dict, bool, Optional[Exception]):
        """
        This function attempts to retrieve the Cosmos REST metrics. The REST
        version used to retrieve the data depends on the value of <sdk_version>.
        :param sdk_version: The REST Server cosmos sdk version to be used
        :return: If data retrieval successful :
                 ({indirect_data}, False, None)
               : If expected error raised while retrieving data:
                ({}, True, Raised_Error)
        """

        # First check if the node being monitored is online. This is being done
        # because no metrics are being retrieved directly from the node.
        node_reachable, err = self._cosmos_rest_reachable(
            self.node_config, sdk_version)
        if not node_reachable:
            return {}, True, err

        # Select indirect nodes for indirect data retrieval.
        selected_indirect_node = self._select_cosmos_rest_node(
            self.data_sources, sdk_version)
        if selected_indirect_node is None:
            self.logger.error(
                'No synced indirect Cosmos REST data source was accessible.')
            return {}, True, NoSyncedDataSourceWasAccessibleException(
                self.monitor_name, 'indirect Cosmos REST node')

        try:
            indirect_data = self._get_cosmos_rest_indirect_data(
                selected_indirect_node, sdk_version)
            return {**indirect_data}, False, None
        except (CosmosSDKVersionIncompatibleException,
                CosmosRestServerApiCallException,
                CannotConnectWithDataSourceException, DataReadingException,
                InvalidUrlException, IncorrectJSONRetrievedException) as e:
            return {}, True, e

    def _get_cosmos_rest_v0_39_2_data(self) -> (
            Dict, bool, Optional[Exception]):
        """
        This function calls self._get_cosmos_rest_version_data with
        _REST_VERSION_COSMOS_SDK_0_39_2
        :return: The return of self._get_cosmos_rest_version_data
        """
        return self._get_cosmos_rest_version_data(
            _REST_VERSION_COSMOS_SDK_0_39_2)

    def _get_cosmos_rest_v0_42_6_data(self) -> (
            Dict, bool, Optional[Exception]):
        """
        This function calls self._get_cosmos_rest_version_data with
        _REST_VERSION_COSMOS_SDK_0_42_6
        :return: The return of self._get_cosmos_rest_version_data
        """
        return self._get_cosmos_rest_version_data(
            _REST_VERSION_COSMOS_SDK_0_42_6)

    def _get_cosmos_rest_data(self) -> (Dict, bool, Optional[Exception]):
        """
        This function attempts to retrieve metrics from the Cosmos REST Server
        according to the Cosmos SDK version of the node used.
        :return: If data retrieval successful :
                 (data dict, False, None)
               : If expected error raised while retrieving data:
                 ({}, True, Raised_Error)
        """
        # A dict consisting of all supported retrieval functions
        supported_retrievals = {
            _REST_VERSION_COSMOS_SDK_0_39_2: self._get_cosmos_rest_v0_39_2_data,
            _REST_VERSION_COSMOS_SDK_0_42_6: self._get_cosmos_rest_v0_42_6_data,
        }

        # First check whether REST data can be obtained using the last REST
        # version used of the REST server to avoid possible errors.
        temp_last_rest_retrieval_version = self.last_rest_retrieval_version
        retrieval_fn = supported_retrievals[self.last_rest_retrieval_version]
        data, data_retrieval_failed, data_retrieval_exception = retrieval_fn()

        # If an exception related to Tendermint or Cosmos SDK version
        # incompatibility is raised, we attempt to retrieve the data using other
        # supported versions. Start by removing the retrieval which we already
        # performed and iterate one by one until successful
        del supported_retrievals[self.last_rest_retrieval_version]
        other_supported_retrievals = list(supported_retrievals)
        while (data_retrieval_failed and type(data_retrieval_exception) in
               _VERSION_INCOMPATIBILITY_EXCEPTIONS):
            if len(other_supported_retrievals) == 0:
                # If all retrievals failed due to a compatibility issue, then
                # raise a more meaningful error
                self.logger.error(
                    'Cosmos REST server data could not be obtained for '
                    '{}'.format(self.node_config.node_name))
                return {}, True, CosmosRestServerDataCouldNotBeObtained(
                    self.node_config.node_name)

            temp_last_rest_retrieval_version = other_supported_retrievals[0]
            retrieval_fn = supported_retrievals[
                other_supported_retrievals.pop(0)]
            data, data_retrieval_failed, data_retrieval_exception = \
                retrieval_fn()

        self._last_rest_retrieval_version = temp_last_rest_retrieval_version

        self.logger.debug(
            (data, data_retrieval_failed, data_retrieval_exception))
        return data, data_retrieval_failed, data_retrieval_exception

    def _get_tendermint_rpc_direct_data(self) -> Dict:
        """
        This function retrieves node specific metrics directly from the node
        being monitored. This data is obtained directly from the node as it
        cannot be obtained otherwise.
        :return: A dict containing all direct metrics
        :raises: TendermintRPCIncompatibleException if the Tendermint RPC
               : version of the node is not compatible with PANIC
               : TendermintRPCCallException if an API call errors
               : DataReadingException if data cannot be read from the node
               : NodeIsDownException if the node cannot be accessed at the
                 tendermint rpc endpoint
               : InvalidUrlException if the URL of the node does not have a
                 valid schema
               : IncorrectJSONRetrievedException if the structure of the data
                 returned by the endpoints is not as expected. This could be
                 both due to Tendermint RPC or Tendermint update.
        """
        node_url = self.node_config.tendermint_rpc_url
        node_name = self.node_config.node_name

        def retrieval_process() -> Dict:
            status = self.tendermint_rpc_api.execute_with_checks(
                self.tendermint_rpc_api.get_status, [node_url], node_name)
            ## check if mev_info is present in response
            if 'mev_info' not in status['result']:
                return {
                    'consensus_hex_address': status['result']['validator_info'][
                        'address'],
                    'is_syncing': status['result']['sync_info'][
                        'catching_up'],
                }
            return {
                'consensus_hex_address': status['result']['validator_info'][
                    'address'],
                'is_syncing': status['result']['sync_info'][
                    'catching_up'],
                'is_peered_with_sentinel' : status['result']['mev_info'][
                    'is_peered_with_sentinel'],
            }

        return self._execute_cosmos_tendermint_retrieval_with_exceptions(
            retrieval_process, node_name, node_url, True)

    def _determine_last_height_monitored_tendermint(
            self, current_last_height: int, current_height: int,
            is_source_archive: bool) -> int:
        """
        This function checks whether last_height_monitored_tendermint satisfies
        some conditions in order to determine its correct value for the upcoming
        monitoring round. These conditions are based on the current height of
        the chain and whether the source node is archive or not.
        NOTE: This check must be done before retrieving any archive Tendermint
              RPC data.
        :param current_last_height:
        The value of self._last_height_monitored_tendermint
        :param current_height:
        The current height of the chain
        :param is_source_archive:
        If the source being used is an archive node or not
        :return: The value of last_height_monitored_tendermint to be used in the
                 upcoming monitoring round
        """
        if current_last_height is None:
            # On start-up we need to start retrieving data from the current
            # block. Therefore, the last height monitored is current - 1
            return current_height - 1
        elif (current_height - current_last_height > self.max_catchup_blocks
              and is_source_archive):
            # If the monitor is not keeping up with the chain and the data
            # source is archive, skip some blocks.
            return current_height - self.max_catchup_blocks
        elif (current_height - current_last_height
              >= self.pruning_catchup_blocks and not is_source_archive):
            # If the monitor is not keeping up with the chain and the data
            # source is not archive, skip some blocks keeping in mind the
            # pruning state of the node. Note that we performed + 1 because for
            # Tendermint RPC data retrieval we are checking the block signatures
            # in a block, where these belong to the parent block. Due to this
            # fact we need to make sure that the state of the previous block is
            # not pruned.
            return current_height - self.pruning_catchup_blocks + 1

        return current_last_height

    @staticmethod
    def _parse_validators_list(paginated_validators: List[Dict]) -> List[Dict]:
        """
        Given a list of paginated validators info, this function will return
        one combined list of validators.
        :param paginated_validators: A paginated list of validators info
        :return: A combined list of validators.
        """
        validators = []
        for validators_info in paginated_validators:
            validators = validators + validators_info['result']['validators']

        return validators

    def _is_validator_active(self, validators: List[Dict]) -> bool:
        """
        Given a list of validators, this function will check if the validator
        being monitored is active
        :param validators: List of validators obtained from
                           TendermintRpcApi.get_validators
        :return: True if validator is in the list
               : False otherwise
        """
        if self.validator_consensus_address in [None, ""]:
            # If the validator does not have a consensus key assigned then it
            # cannot be active
            return False

        for validator_info in validators:
            if self.validator_consensus_address == validator_info['address']:
                return True

        return False

    def _validator_was_slashed(self, begin_block_events: List[Dict]) -> (
            bool, Optional[float]):
        """
        Given the begin_block_events returned by the
        TendermintRpcApi.get_block_results endpoint, this functions returns
        whether the validator was slashed or not, and the slashed amount if
        available.
        :param begin_block_events: The begin_block_events returned by the
        TendermintRpcApi.get_block_results endpoint
        :return: (True, None) If validator was slashed but no slashing amount
                 is available
                 (True, int) If validator was slashed and a slashing amount >= 0
                 is available
                 (False, None) If validator was not slashed
        """
        if self.validator_consensus_address in [None, ""]:
            # If the validator does not have a consensus key assigned then it
            # cannot be active, hence not slashed
            return False, None

        slashed = False
        slashed_amount = None
        for event in begin_block_events:
            # For every event, check if it is of type "slash", if yes check if
            # the HEX consensus address of the event matches that of the
            # validator. If it does, mark the validator as slashed and add the
            # slash fraction if available.
            if str.lower(event["type"]) == 'slash':
                event_address = None
                event_burned_coins = None
                attributes = event['attributes']
                for attribute in attributes:
                    if 'key' in attribute and 'value' in attribute:
                        decoded_key = base64.b64decode(attribute['key']).decode(
                            'utf-8')
                        decoded_value = base64.b64decode(
                            attribute['value']).decode('utf-8')
                        if str.lower(decoded_key) == "address":
                            event_address = bech32_to_address(decoded_value)
                        elif str.lower(decoded_key) == "burned_coins":
                            event_burned_coins = int(decoded_value)

                if event_address == self.validator_consensus_address:
                    slashed = True
                    if event_burned_coins is not None:
                        slashed_amount = (
                            event_burned_coins if slashed_amount is None
                            else slashed_amount + event_burned_coins
                        )

        return slashed, slashed_amount

    def _get_tendermint_rpc_archive_data_validator(
            self, source: CosmosNodeConfig) -> Dict:
        source_url = source.tendermint_rpc_url
        source_name = source.node_name

        def retrieval_process() -> Dict:
            """
            The aim of this function is to check whether the validator signed
            block block_being_checked - 1 and to check if the validator was
            slashed in the block being checked
            :return: List of metrics
            """
            latest_block = \
                self.tendermint_rpc_api.execute_with_checks(
                    self.tendermint_rpc_api.get_block, [source_url],
                    source_name)
            current_height = int(latest_block['result']['block']['header'][
                                     'height'])
            self._last_height_monitored_tendermint = \
                self._determine_last_height_monitored_tendermint(
                    self.last_height_monitored_tendermint, current_height,
                    source.is_archive_node)
            starting_height = self.last_height_monitored_tendermint + 1
            stopping_height = current_height + 1
            historical_data = []

            for height_to_monitor in range(starting_height, stopping_height):
                # Since the current block has signing info belonging to the
                # previous block, we must first check if the validator was
                # active in the previous block
                paginated_validators = \
                    self._get_tendermint_data_with_count(
                        self.tendermint_rpc_api.get_validators, [source_url],
                        {'height': height_to_monitor - 1}, source_name)
                validators_list = self._parse_validators_list(
                    paginated_validators)
                validator_was_active = self._is_validator_active(
                    validators_list)
                block_at_height = \
                    self.tendermint_rpc_api.execute_with_checks(
                        self.tendermint_rpc_api.get_block,
                        [source_url, {'height': height_to_monitor}],
                        source_name)

                # Check if the validator was slashed and get the slash amount
                # if it is provided
                block_results_at_height = \
                    self.tendermint_rpc_api.execute_with_checks(
                        self.tendermint_rpc_api.get_block_results,
                        [source_url, {'height': height_to_monitor}],
                        source_name)
                slashed, slashed_amount = self._validator_was_slashed(
                    block_results_at_height['result']['begin_block_events'])

                if validator_was_active:
                    previous_block_signatures = block_at_height['result'][
                        'block']['last_commit']['signatures']
                    non_null_signatures = filter(lambda x: x['signature'],
                                                 previous_block_signatures)
                    signed_validators = set(
                        map(lambda x: x['validator_address'],
                            non_null_signatures))

                    historical_data.append({
                        'height': height_to_monitor,
                        'active_in_prev_block': True,
                        'signed_prev_block':
                            (self.validator_consensus_address
                             in signed_validators),
                        'slashed': slashed,
                        'slashed_amount': slashed_amount
                    })
                else:
                    historical_data.append({
                        'height': height_to_monitor,
                        'active_in_prev_block': False,
                        'signed_prev_block': False,
                        'slashed': slashed,
                        'slashed_amount': slashed_amount
                    })

            self._last_height_monitored_tendermint = current_height

            # We need to reverse the historical data to show info about the
            # latest block first
            historical_data.reverse()
            return {'historical': historical_data}

        return self._execute_cosmos_tendermint_retrieval_with_exceptions(
            retrieval_process, source_name, source_url, False)

    def _get_tendermint_rpc_archive_data(self,
                                         source: CosmosNodeConfig) -> Dict:
        """
        This function returns the Tendermint RPC archive metrics of the node
        depending on whether the node is a validator or a non-validator.
        NOTE: If the node is a non-validator, then default data is returned.
        :param source: The data source
        :return: The Tendermint RPC archive metrics
        """
        source_url = source.tendermint_rpc_url
        if not source_url:
            return {
                'historical': None,
            }

        if self.node_config.is_validator:
            return self._get_tendermint_rpc_archive_data_validator(source)

        return {
            'historical': []
        }

    def _get_tendermint_rpc_data(self) -> (Dict, bool, Optional[Exception]):
        """
        This function attempts to retrieve the Tendermint RPC metrics.
        :return: If data retrieval successful :
                 ({archive_data}, False, None)
               : If expected error raised while retrieving data:
                ({}, True, Raised_Error)
        """
        try:
            # First get the data directly. This is done so that the consensus
            # address is saved and to check that the node is accessible.
            direct_data = self._get_tendermint_rpc_direct_data()
            if direct_data['consensus_hex_address'] not in ['', None]:
                self._validator_consensus_address = direct_data[
                    'consensus_hex_address']
                ## If the node is running mev-tendermint add the is_peered_with_sentinel field
                if 'is_peered_with_sentinel' in direct_data:
                    direct_data = {'is_syncing': direct_data['is_syncing'],
                                   'is_peered_with_sentinel':
                                       direct_data['is_peered_with_sentinel']}
                else:
                    direct_data = {'is_syncing': direct_data['is_syncing']}

            # Select archive node for archive data retrieval. If no archive
            # node is accessible, or given by the user, try getting data with
            # an indirect node just in case.
            selected_node = self._select_cosmos_tendermint_node(
                self.archive_nodes)
            if selected_node is None:
                selected_node = self._select_cosmos_tendermint_node(
                    self.data_sources)
                if selected_node is None:
                    self.logger.error(
                        'No synced archive/indirect Tendermint RPC data source '
                        'was accessible.')
                    return {}, True, NoSyncedDataSourceWasAccessibleException(
                        self.monitor_name,
                        'archive/indirect Tendermint RPC node')

            archive_data = self._get_tendermint_rpc_archive_data(selected_node)
            self.logger.debug((archive_data, False, None))
            return {**direct_data, **archive_data}, False, None

        except (TendermintRPCCallException, TendermintRPCIncompatibleException,
                DataReadingException, NodeIsDownException, InvalidUrlException,
                IncorrectJSONRetrievedException,
                CannotConnectWithDataSourceException) as e:
            if type(e) in _VERSION_INCOMPATIBILITY_EXCEPTIONS:
                # If we have an incompatibility issue raise a more meaningful
                # error
                self.logger.error(
                    'Tendermint RPC data could not be obtained for {}'.format(
                        self.node_config.node_name))
                return {}, True, TendermintRPCDataCouldNotBeObtained(
                    self.node_config.node_name)

            self.logger.debug(({}, True, e))
            return {}, True, e

    def _get_prometheus_data(self) -> (Dict, bool, Optional[Exception]):
        """
        This function attempts to retrieve the prometheus metrics from the node
        directly.
        If data retrieval is successful:
        data = Non empty data dict
        data_retrieval_failed = False
        and data_retrieval_exception = None.
        Otherwise:
        data = {},
        data_retrieval_failed = True,
        data_retrieval_exception = raised error
        :return: (data, data_retrieval_failed, data_retrieval_exception)
        """
        data = {}
        data_retrieval_failed = True
        data_retrieval_exception = None
        try:
            data = get_prometheus_metrics_data(self.node_config.prometheus_url,
                                               self.prometheus_metrics,
                                               self.logger, verify=False)
            data_retrieval_failed = False
        except (ReqConnectionError, ReadTimeout) as e:
            data_retrieval_exception = NodeIsDownException(
                self.node_config.node_name)
            self.logger.error(
                "Prometheus metrics could not be obtained from {}. Error: "
                "{}".format(self.node_config.prometheus_url, e))
            self.logger.exception(data_retrieval_exception)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError) as e:
            data_retrieval_exception = DataReadingException(
                self.monitor_name, self.node_config.prometheus_url)
            self.logger.error(
                "Prometheus metrics could not be obtained from {}. Error: "
                "{}".format(self.node_config.prometheus_url, e))
            self.logger.exception(data_retrieval_exception)
        except (InvalidURL, InvalidSchema, MissingSchema) as e:
            data_retrieval_exception = InvalidUrlException(
                self.node_config.prometheus_url)
            self.logger.error(
                "Prometheus metrics could not be obtained from {}. Error: "
                "{}".format(self.node_config.prometheus_url, e))
            self.logger.exception(data_retrieval_exception)
        except MetricNotFoundException as e:
            data_retrieval_exception = e
            self.logger.error(
                "Prometheus metrics could not be obtained from {}. Error: "
                "{}".format(self.node_config.prometheus_url, e))
            self.logger.exception(data_retrieval_exception)

        return data, data_retrieval_failed, data_retrieval_exception

    def _get_data(self) -> Dict:
        """
        This function retrieves the data from various data sources. Due to
        multiple data sources being processed, this function also returns some
        data retrieval information for further processing.
        :return: A dict containing all node metrics.
        """
        retrieval_info = {
            'prometheus': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self._get_prometheus_data,
                'processing_function': self._process_retrieved_prometheus_data,
                'monitoring_enabled': self.node_config.monitor_prometheus
            },
            'cosmos_rest': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self._get_cosmos_rest_data,
                'processing_function': self._process_retrieved_cosmos_rest_data,
                'monitoring_enabled': self.node_config.monitor_cosmos_rest
            },
            'tendermint_rpc': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self._get_tendermint_rpc_data,
                'processing_function':
                    self._process_retrieved_tendermint_rpc_data,
                'monitoring_enabled': self.node_config.monitor_tendermint_rpc
            }
        }

        for source, info in retrieval_info.items():
            if info['monitoring_enabled']:
                ret = info['get_function']()
                info['data'] = ret[0]
                info['data_retrieval_failed'] = ret[1]
                info['data_retrieval_exception'] = ret[2]

        return retrieval_info

    def _process_error(self, error: PANICException) -> Dict:
        """
        This function attempts to process the error which occurred when
        retrieving data
        :param error: The detected error
        :return: A dict with the error data together with some meta-data
        """
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_validator': self.node_config.is_validator,
                    'operator_address': self.node_config.operator_address
                },
                'message': error.message,
                'code': error.code,
            }
        }

        return processed_data

    def _process_retrieved_cosmos_rest_data(self, data: Dict) -> Dict:
        """
        This function attempts to process the retrieved Cosmos-REST data.
        :param data: The retrieved Cosmos-REST data
        :return: A dict with the retrieved data together with some meta-data
        """
        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_validator': self.node_config.is_validator,
                    'operator_address': self.node_config.operator_address,
                },
                'data': copy.deepcopy(data),
            }
        }

        return processed_data

    def _process_retrieved_tendermint_rpc_data(self, data: Dict) -> Dict:
        """
        This function attempts to process the retrieved Tendermint RPC data.
        :param data: The retrieved Tendermint RPC data
        :return: A dict with the retrieved data together with some meta-data
        """
        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_mev_tendermint_node': 'is_peered_with_sentinel' in data,
                    'is_validator': self.node_config.is_validator,
                    'operator_address': self.node_config.operator_address,
                },
                'data': copy.deepcopy(data),
            }
        }

        return processed_data

    def _process_retrieved_prometheus_data(self, data: Dict) -> Dict:
        """
        This function attempts to process the retrieved prometheus data. The
        processing is performed so that the data transformer can reason about
        the metric values easily.
        :param data: The retrieved prometheus data
        :return: A dict with the retrieved data together with some meta-data
        """
        data_copy = copy.deepcopy(data)

        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_validator': self.node_config.is_validator,
                    'operator_address': self.node_config.operator_address
                },
                'data': {},
            }
        }

        # One value subset metrics are prometheus metrics whose values need to
        # be indexed via one subset in order to be obtained. Note, some metrics
        # were set to be optional, so first we need to check if the value is
        # None.
        one_value_subset_metrics = [
            'tendermint_consensus_latest_block_height',
            'tendermint_consensus_validator_power',
        ]
        for metric in one_value_subset_metrics:
            value = None
            if data_copy[metric] is not None:
                for _, data_subset in enumerate(data_copy[metric]):
                    value = data_copy[metric][data_subset]
                    break
            self.logger.debug("%s %s: %s", self.node_config, metric, value)
            processed_data['result']['data'][metric] = value

        # If the tendermint_consensus_validator_power is None it means that the
        # metric could not be obtained, hence the node is not in the validator
        # set. This means that we can set the metric to 0 as the node has no
        # voting power.
        voting_power = processed_data['result']['data'][
            'tendermint_consensus_validator_power']
        if voting_power is None:
            self.logger.debug("%s %s converted to %s", self.node_config,
                              'tendermint_consensus_validator_power', 0)
            processed_data['result']['data'][
                'tendermint_consensus_validator_power'] = 0

        return processed_data

    @staticmethod
    def _process_retrieved_data(processing_fn: Callable, data: Dict) -> Dict:
        return processing_fn(data)

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY, body=data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to '%s' exchange", RAW_DATA_EXCHANGE)

    def _monitor(self) -> None:
        retrieval_info = self._get_data()
        processed_data = {}
        for source, info in retrieval_info.items():
            if info['monitoring_enabled']:
                try:
                    processed_data[source] = self._process_data(
                        info['data_retrieval_failed'],
                        [info['data_retrieval_exception']],
                        [info['processing_function'], info['data']],
                    )
                except Exception as error:
                    self.logger.error("Error when processing data: %s", error)
                    self.logger.exception(error)
                    # Do not send data if we experienced processing errors
                    return
            else:
                processed_data[source] = {}

        self._send_data(processed_data)

        data_retrieval_failed_list = [
            info['data_retrieval_failed']
            for _, info in retrieval_info.items() if info['monitoring_enabled']
        ]

        # Only output the gathered data if at least one retrieval occurred
        # and there was no error in the entire retrieval process
        if data_retrieval_failed_list and not any(data_retrieval_failed_list):
            self.logger.debug(self._display_data(processed_data))

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)
