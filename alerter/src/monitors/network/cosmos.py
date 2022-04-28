import copy
import logging
from datetime import datetime
from typing import List, Dict, Optional

import pika

from src.configs.nodes.cosmos import CosmosNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.cosmos import (
    CosmosMonitor, _REST_VERSION_COSMOS_SDK_0_42_6,
    _REST_VERSION_COSMOS_SDK_0_39_2, _VERSION_INCOMPATIBILITY_EXCEPTIONS)
from src.utils.constants.cosmos import (
    PROPOSAL_STATUS_UNSPECIFIED, PROPOSAL_STATUS_DEPOSIT_PERIOD,
    PROPOSAL_STATUS_VOTING_PERIOD, PROPOSAL_STATUS_PASSED,
    PROPOSAL_STATUS_REJECTED, PROPOSAL_STATUS_FAILED, PROPOSAL_STATUS_INVALID)
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, COSMOS_NETWORK_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    DataReadingException, InvalidUrlException, PANICException,
    CosmosSDKVersionIncompatibleException, CosmosRestServerApiCallException,
    IncorrectJSONRetrievedException, NoSyncedDataSourceWasAccessibleException,
    CannotConnectWithDataSourceException, CosmosNetworkDataCouldNotBeObtained)


class CosmosNetworkMonitor(CosmosMonitor):
    """
    The Cosmos network monitor supports the retrieval of Cosmos Rest Server
    data. Moreover, v0.42.6 and v0.39.2 of the Cosmos SDK are directly
    supported. If a data source has a different Cosmos SDK version, the
    monitor attempts to retrieve the data using all the supported versions
    just in case that version is still compatible, however, this might
    result into unexpected behaviour.

    Note that different chains might also carry different versions of
    Tendermint, resulting in different structures in the data retrieved. This
    must also be catered with in the implemented data retrievals. In
    development, only Tendermint versions for the latest Cosmos SDK chains were
    considered. The Tendermint versions used by the latest Cosmos SDK chains
    considered were v0.33.7, v0.33.8, v0.33.9, v0.34.11, v0.34.12.
    """

    def __init__(self, monitor_name: str, data_sources: List[CosmosNodeConfig],
                 parent_id: str, chain_name: str, logger: logging.Logger,
                 monitor_period: int, rabbitmq: RabbitMQApi) -> None:

        super().__init__(monitor_name, data_sources, logger, monitor_period,
                         rabbitmq)
        self._parent_id = parent_id
        self._chain_name = chain_name

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def chain_name(self) -> str:
        return self._chain_name

    @staticmethod
    def _parse_proposal(proposal: Dict) -> Dict:
        """
        This function parses the proposal retrieved from the source node and
        returns the corresponding value to be used by the PANIC components.
        Note that this function is compatible with both v0.39.2 and v0.42.6 of
        the Cosmos SDK.
        :param proposal: The proposal retrieved from the source node
        :return: The corresponding proposal to be used by the PANIC components
        :raises: KeyError if the structure of the proposal returned by the
                 endpoints is not as expected.
        """
        parsed_proposal = {
            'proposal_id': (
                proposal['proposal_id']
                if 'proposal_id' in proposal
                else proposal['id']
            ),
            'title': (
                proposal['content']['value']['title']
                if 'value' in proposal['content']
                else proposal['content']['title']
            ),
            'description': (
                proposal['content']['value']['description']
                if 'value' in proposal['content']
                else proposal['content']['description']
            )
        }

        status = (
            proposal['status']
            if 'status' in proposal
            else proposal['proposal_status']
        )

        if type(status) == str:
            status = status.lower()
        if status in [0, "proposal_status_unspecified", "unspecified"]:
            parsed_proposal['status'] = PROPOSAL_STATUS_UNSPECIFIED
        elif status in [1, "proposal_status_deposit_period", "deposit_period"]:
            parsed_proposal['status'] = PROPOSAL_STATUS_DEPOSIT_PERIOD
        elif status in [2, "proposal_status_voting_period", "voting_period"]:
            parsed_proposal['status'] = PROPOSAL_STATUS_VOTING_PERIOD
        elif status in [3, "proposal_status_passed", "passed"]:
            parsed_proposal['status'] = PROPOSAL_STATUS_PASSED
        elif status in [4, "proposal_status_rejected", "rejected"]:
            parsed_proposal['status'] = PROPOSAL_STATUS_REJECTED
        elif status in [5, "proposal_status_failed", "failed"]:
            parsed_proposal['status'] = PROPOSAL_STATUS_FAILED
        else:
            parsed_proposal['status'] = PROPOSAL_STATUS_INVALID

        parsed_proposal['final_tally_result'] = proposal['final_tally_result']
        parsed_proposal['submit_time'] = proposal['submit_time']
        parsed_proposal['deposit_end_time'] = proposal['deposit_end_time']
        parsed_proposal['total_deposit'] = proposal['total_deposit']
        parsed_proposal['voting_start_time'] = proposal['voting_start_time']
        parsed_proposal['voting_end_time'] = proposal['voting_end_time']

        return parsed_proposal

    def _get_cosmos_rest_v0_39_2_indirect_data(
            self, source: CosmosNodeConfig) -> Dict:
        """
        This function retrieves network specific metrics. To retrieve this
        data we use version v0.39.2 of the Cosmos SDK for the REST server.
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
        source_url = source.cosmos_rest_url
        source_name = source.node_name

        def retrieval_process() -> Dict:
            result = \
                self.cosmos_rest_server_api.execute_with_checks(
                    self.cosmos_rest_server_api.get_proposals_v0_39_2,
                    [source_url], source_name, _REST_VERSION_COSMOS_SDK_0_39_2)
            proposals = result['result']
            for i, proposal in enumerate(proposals):
                proposals[i] = self._parse_proposal(proposal)
            return {
                'proposals': proposals
            }

        return self._execute_cosmos_rest_retrieval_with_exceptions(
            retrieval_process, source_name, source_url,
            _REST_VERSION_COSMOS_SDK_0_39_2)

    def _get_cosmos_rest_v0_42_6_indirect_data(
            self, source: CosmosNodeConfig) -> Dict:
        """
        This function retrieves network specific metrics. To retrieve this
        data we use version v0.42.6 of the Cosmos SDK for the REST server.
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
        source_url = source.cosmos_rest_url
        source_name = source.node_name

        def retrieval_process() -> Dict:
            paginated_data = self._get_rest_data_with_pagination_keys(
                self.cosmos_rest_server_api.get_proposals_v0_42_6,
                [source_url, None], {}, source_name,
                _REST_VERSION_COSMOS_SDK_0_42_6)

            parsed_proposals = {'proposals': []}
            for page in paginated_data:
                for proposal in page['proposals']:
                    parsed_proposals['proposals'].append(
                        self._parse_proposal(proposal))

            return parsed_proposals

        return self._execute_cosmos_rest_retrieval_with_exceptions(
            retrieval_process, source_name, source_url,
            _REST_VERSION_COSMOS_SDK_0_42_6)

    def _get_cosmos_rest_indirect_data(self, source: CosmosNodeConfig,
                                       sdk_version: str) -> Dict:
        """
        This function returns the Cosmos REST indirect metrics of the network.
        :param source: The data source
        :param sdk_version: The cosmos sdk REST version used to get the data
        :return: The Cosmos REST indirect metrics
        """

        if not source.cosmos_rest_url:
            return {
                'proposals': None
            }

        if sdk_version == _REST_VERSION_COSMOS_SDK_0_39_2:
            return self._get_cosmos_rest_v0_39_2_indirect_data(source)
        elif sdk_version == _REST_VERSION_COSMOS_SDK_0_42_6:
            return self._get_cosmos_rest_v0_42_6_indirect_data(source)

        return {
            'proposals': None
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
        # Select indirect nodes for indirect data retrieval.
        selected_indirect_node = self._select_cosmos_rest_node(
            self.data_sources, sdk_version)
        if selected_indirect_node is None:
            self.logger.error('No synced indirect data source was accessible.')
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
                    'Cosmos network data could not be obtained.')
                return {}, True, CosmosNetworkDataCouldNotBeObtained()

            temp_last_rest_retrieval_version = other_supported_retrievals[0]
            retrieval_fn = supported_retrievals[
                other_supported_retrievals.pop(0)]
            data, data_retrieval_failed, data_retrieval_exception = \
                retrieval_fn()

        self._last_rest_retrieval_version = temp_last_rest_retrieval_version

        return data, data_retrieval_failed, data_retrieval_exception

    def _get_data(self) -> Dict:
        """
        This function retrieves cosmos network's specific metrics.
        :return: A dict containing all network metrics.
        """
        ret = self._get_cosmos_rest_data()

        # if we are to add more data sources, we need to generalize this
        # function similarly to the cosmos node monitor

        return {
            'cosmos_rest': {
                'data': ret[0],
                'data_retrieval_failed': ret[1],
                'data_retrieval_exception': ret[2]
            }
        }

    def _process_error(self, error: PANICException) -> Dict:
        """
        This function attempts to process the error which occurred when
        retrieving data.
        :param error: The detected error
        :return: A dict with the error data together with some meta-data
        """
        processed_data = {
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.monitor_name,
                        'parent_id': self.parent_id,
                        'chain_name': self.chain_name,
                        'time': datetime.now().timestamp(),
                    },
                    'message': error.message,
                    'code': error.code,
                }
            }
        }

        return processed_data

    def _process_retrieved_data(self, data: Dict) -> Dict:
        """
        This function attempts to process the retrieved Cosmos-REST data.
        :param data: The retrieved Cosmos-REST data
        :return: A dict with the retrieved data together with some meta-data
        """
        # Add some meta-data to the processed data
        processed_data = {
            'cosmos_rest': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.monitor_name,
                        'parent_id': self.parent_id,
                        'chain_name': self.chain_name,
                        'time': datetime.now().timestamp(),
                    },
                    'data': copy.deepcopy(data),
                }
            }
        }

        return processed_data

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=COSMOS_NETWORK_RAW_DATA_ROUTING_KEY, body=data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to '%s' exchange", RAW_DATA_EXCHANGE)

    def _monitor(self) -> None:

        # if more data sources, generalize to multiple sources.
        # see cosmos node monitor for logic
        retrieval_info = self._get_data()
        try:
            processed_data = self._process_data(
                retrieval_info['cosmos_rest']['data_retrieval_failed'],
                [retrieval_info['cosmos_rest']['data_retrieval_exception']],
                [retrieval_info['cosmos_rest']['data']],
            )
        except Exception as error:
            self.logger.error("Error when processing data: %s", error)
            self.logger.exception(error)
            # Do not send data if we experienced processing errors
            return

        self._send_data(processed_data)

        if not retrieval_info['cosmos_rest']['data_retrieval_failed']:
            # Only output the gathered data if there was no error
            self.logger.debug(self._display_data(processed_data))

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)
