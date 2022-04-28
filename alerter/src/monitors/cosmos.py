import copy
import json
import logging
from abc import ABC
from http.client import IncompleteRead
from typing import Dict, List, Optional, Callable, Any

from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.api_wrappers.cosmos import (
    CosmosRestServerApiWrapper, TendermintRpcApiWrapper)
from src.configs.nodes.cosmos import CosmosNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.exceptions import (
    IncorrectJSONRetrievedException, CosmosSDKVersionIncompatibleException,
    ComponentNotGivenEnoughDataSourcesException,
    CosmosRestServerApiCallException, CannotConnectWithDataSourceException,
    DataReadingException, InvalidUrlException,
    TendermintRPCIncompatibleException, TendermintRPCCallException,
    NodeIsDownException, PANICException)

_REST_VERSION_COSMOS_SDK_0_39_2 = 'v0.39.2'
_REST_VERSION_COSMOS_SDK_0_42_6 = 'v0.42.6'
_VERSION_INCOMPATIBILITY_EXCEPTIONS = [
    IncorrectJSONRetrievedException, CosmosSDKVersionIncompatibleException,
    TendermintRPCIncompatibleException
]


class CosmosMonitor(Monitor, ABC):
    def __init__(self, monitor_name: str, data_sources: List[CosmosNodeConfig],
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        # An exception is raised if the monitor is not given enough data
        # sources.
        if len(data_sources) == 0:
            raise ComponentNotGivenEnoughDataSourcesException(monitor_name,
                                                              'data_sources')

        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._data_sources = data_sources
        self._cosmos_rest_server_api = CosmosRestServerApiWrapper(self.logger)
        self._tendermint_rpc_api = TendermintRpcApiWrapper(self.logger)

        # This variable stores the latest REST version used to retrieve the
        # data. By default, it is set to v0.42.6 of the Cosmos SDK.
        self._last_rest_retrieval_version = _REST_VERSION_COSMOS_SDK_0_42_6

    @property
    def data_sources(self) -> List[CosmosNodeConfig]:
        return self._data_sources

    @property
    def cosmos_rest_server_api(self) -> CosmosRestServerApiWrapper:
        return self._cosmos_rest_server_api

    @property
    def tendermint_rpc_api(self) -> TendermintRpcApiWrapper:
        return self._tendermint_rpc_api

    @property
    def last_rest_retrieval_version(self) -> str:
        return self._last_rest_retrieval_version

    def _select_cosmos_rest_node(
            self, nodes: List[CosmosNodeConfig],
            sdk_version: str) -> Optional[CosmosNodeConfig]:
        """
        This function returns the configuration of the selected node. A node is
        selected only if its cosmos_rest_url is reachable and the node is
        synced. Note that this function is compatible with both v0.39.2 and
        v0.42.6 of the Cosmos SDK and any other versions compatible with these
        versions. In addition to this, it assumes that all the given data
        sources are compatible. If this is not the case, an incompatible node
        may be selected, resulting into a REST data retrieval failure.
        :param nodes: The list of nodes to select from
        :param sdk_version: The REST Server Cosmos SDK version being used
        :return: The node config of the selected node.
               : None if no node is selected.
        """
        for node in nodes:
            cosmos_rest_url = node.cosmos_rest_url
            try:
                api_ret = self.cosmos_rest_server_api.execute_with_checks(
                    self.cosmos_rest_server_api.get_syncing, [cosmos_rest_url],
                    node.node_name, sdk_version)
                if not api_ret['syncing']:
                    self.logger.debug('chosen %s.', cosmos_rest_url)
                    return node
            except (ReqConnectionError, ReadTimeout, InvalidURL, InvalidSchema,
                    MissingSchema, IncompleteRead, ChunkedEncodingError,
                    ProtocolError, CosmosSDKVersionIncompatibleException,
                    CosmosRestServerApiCallException, KeyError) as e:
                # If an expected error occurs we will log the error and re-try
                # again with another node.
                self.logger.debug("Error when trying to access %s: %s",
                                  cosmos_rest_url, e)

        return None

    def _select_cosmos_tendermint_node(
            self, nodes: List[CosmosNodeConfig]) -> Optional[CosmosNodeConfig]:
        """
        This function returns the configuration of the selected node. A node is
        selected only if its tendermint_rpc_url is reachable and the node is
        synced.
        :param nodes: The list of nodes to select from
        :return: The node config of the selected node.
               : None if no node is selected.
        """
        for node in nodes:
            tendermint_rpc_url = node.tendermint_rpc_url
            try:
                api_ret = self.tendermint_rpc_api.execute_with_checks(
                    self.tendermint_rpc_api.get_status, [tendermint_rpc_url],
                    node.node_name)
                syncing = api_ret['result']['sync_info']['catching_up']
                if not syncing:
                    self.logger.debug('chosen %s.', tendermint_rpc_url)
                    return node
            except (ReqConnectionError, ReadTimeout, InvalidURL, InvalidSchema,
                    MissingSchema, IncompleteRead, ChunkedEncodingError,
                    ProtocolError, TendermintRPCCallException,
                    TendermintRPCIncompatibleException, KeyError) as e:
                # If an expected error occurs we will log the error and re-try
                # again with another node.
                self.logger.debug("Error when trying to access %s: %s",
                                  tendermint_rpc_url, e)

        return None

    def _cosmos_rest_reachable(
            self, node: CosmosNodeConfig, sdk_version: str) -> (
            bool, PANICException):
        """
        The REST interface of a node is said to be reachable if some syncing
        data can be obtained successfully from the REST interface of the node
        without an exception being raised. Note that this function is compatible
        with versions v0.39.2 and v0.42.6 of the Cosmos SDK and any other
        version compatible with these two versions.
        :param node: The node whose cosmos_rest_url is to be tested
        :param sdk_version: The REST Server Cosmos SDK version being used
        :return: (True, None) if no exception raised
               : (False, NodeIsDownException) if connection error raised
               : (False, DataReadingException) if data read error raised
               : (False, InvalidUrlException) if invalid url error raised
               : (False, CosmosSDKVersionIncompatibleException)
                 if CosmosSDKVersionIncompatible Exception raised
               : (False, CosmosRestServerApiCallException) if
                 CosmosRestServerApiCallException raised
        :raise: Any unrecognized exception
        """
        data_retrieval_exception = None
        reachable = False
        cosmos_rest_url = node.cosmos_rest_url
        try:
            self.cosmos_rest_server_api.execute_with_checks(
                self.cosmos_rest_server_api.get_syncing, [cosmos_rest_url],
                node.node_name, sdk_version)
            reachable = True
        except (ReqConnectionError, ReadTimeout) as e:
            data_retrieval_exception = NodeIsDownException(node.node_name)
            self.logger.error("REST data could not be obtained from {}. Error: "
                              "{}".format(cosmos_rest_url, e))
            self.logger.exception(data_retrieval_exception)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError) as e:
            data_retrieval_exception = DataReadingException(self.monitor_name,
                                                            cosmos_rest_url)
            self.logger.error("REST data could not be obtained from {}. Error: "
                              "{}".format(cosmos_rest_url, e))
            self.logger.exception(data_retrieval_exception)
        except (InvalidURL, InvalidSchema, MissingSchema) as e:
            data_retrieval_exception = InvalidUrlException(cosmos_rest_url)
            self.logger.error("REST data could not be obtained from {}. Error: "
                              "{}".format(cosmos_rest_url, e))
            self.logger.exception(data_retrieval_exception)
        except (CosmosSDKVersionIncompatibleException,
                CosmosRestServerApiCallException) as e:
            data_retrieval_exception = e
            self.logger.error("REST data could not be obtained from {}. Error: "
                              "{}".format(cosmos_rest_url, e.message))
            self.logger.exception(data_retrieval_exception)

        return reachable, data_retrieval_exception

    def _execute_cosmos_rest_retrieval_with_exceptions(
            self, function: Callable[[], Dict], source_name: str,
            source_rest_url: str, sdk_version: str) -> Dict:
        """
        This helper executes the REST Data retrieval procedure with some
        exception handling.
        :param function: The REST Data retrieval procedure
        :param source_name: The name of the data source being used to retrieve
                          : the REST data
        :param source_rest_url: The Cosmos REST Url of the data source
        :param sdk_version: The REST Server Cosmos SDK version being used
        :return: Dict containing all retrieved metrics
        :raises: DataReadingException if data cannot be read from the source
               : CannotConnectWithDataSourceException if we cannot connect with
                 the data source
               : InvalidUrlException if the URL of the data source does not have
                 a valid schema
               : IncorrectJSONRetrievedException if the structure of the data
                 returned by the endpoints is not as expected. This could be
                 both due to a Tendermint update or a Cosmos SDK update
        """
        try:
            return function()
        except (ReqConnectionError, ReadTimeout) as e:
            self.logger.exception(e)
            self.logger.error("REST data could not be obtained from {}. Error: "
                              "{}".format(source_rest_url, e))
            raise CannotConnectWithDataSourceException(
                self.monitor_name, source_name, repr(e))
        except (IncompleteRead, ChunkedEncodingError, ProtocolError) as e:
            self.logger.exception(e)
            self.logger.error("REST data could not be obtained from {}. Error: "
                              "{}".format(source_rest_url, e))
            raise DataReadingException(self.monitor_name, source_rest_url)
        except (InvalidURL, InvalidSchema, MissingSchema) as e:
            self.logger.exception(e)
            self.logger.error("REST data could not be obtained from {}. Error: "
                              "{}".format(source_rest_url, e))
            raise InvalidUrlException(source_rest_url)
        except KeyError as e:
            # If a key error occurs while parsing the retrieved data, this
            # means that the source's cosmos sdk or Tendermint versions are
            # not compatible with either <sdk_version> of cosmos sdk or v0.33.7,
            # v0.33.8, v0.33.9, v0.34.11, v0.34.12 of Tendermint.
            self.logger.exception(e)
            self.logger.error(
                'The Cosmos SDK or Tendermint versions of data source {} are '
                'incompatible with version {} of the Cosmos SDK or v0.33.7, '
                'v0.33.8, v0.33.9, v0.34.11, v0.34.12 of Tendermint.'.format(
                    source_name, sdk_version))
            raise IncorrectJSONRetrievedException(
                'Cosmos REST Server {} Cosmos SDK'.format(sdk_version), repr(e))

    def _execute_cosmos_tendermint_retrieval_with_exceptions(
            self, function: Callable, source_name: str,
            source_tendermint_url: str, direct_retrieval: bool) -> Dict:
        """
        This helper executes the Tendermint RPC Data retrieval procedure with
        some exception handling.
        :param function: The Tendermint Data retrieval procedure
        :param source_name: The name of the data source being used to retrieve
                          : the Tendermint RPC data
        :param source_tendermint_url: The Tendermint RPC Url of the data source
        :param direct_retrieval: Whether the data retrieval procedure is being
                               : performed on the node being monitored (True) or
                               : using another node as data source (False)
        :return: Dict containing all retrieved metrics
        :raises: DataReadingException if data cannot be read from the source
               : CannotConnectWithDataSourceException if we cannot connect with
                 the data source (only for indirect/archive data retrieval)
               : NodeIsDownException if the node being monitored cannot be
                 directly accessed at the tendermint rpc endpoint
               : InvalidUrlException if the URL of the data source does not have
                 a valid schema
               : IncorrectJSONRetrievedException if the structure of the data
                 returned by the endpoints is not as expected. This could be
                 both due to a Tendermint or a Tendermint RPC update
        """
        try:
            return function()
        except (ReqConnectionError, ReadTimeout) as e:
            # If we are performing a direct data retrieval, this means that for
            # the Tendermint RPC retrieval the node is down. Otherwise, it means
            # that the indirect data source cannot be reached (Note, node
            # downtime would be tackled by the monitor dedicated to that node)
            self.logger.exception(e)
            self.logger.error("Tendermint RPC data could not be obtained from "
                              "{}. Error: {}".format(source_tendermint_url, e))
            if direct_retrieval:
                raise NodeIsDownException(source_name)
            else:
                raise CannotConnectWithDataSourceException(
                    self.monitor_name, source_name, repr(e))
        except (IncompleteRead, ChunkedEncodingError, ProtocolError) as e:
            self.logger.exception(e)
            self.logger.error("Tendermint RPC data could not be obtained from "
                              "{}. Error: {}".format(source_tendermint_url, e))
            raise DataReadingException(self.monitor_name, source_tendermint_url)
        except (InvalidURL, InvalidSchema, MissingSchema) as e:
            self.logger.exception(e)
            self.logger.error("Tendermint RPC data could not be obtained from "
                              "{}. Error: {}".format(source_tendermint_url, e))
            raise InvalidUrlException(source_tendermint_url)
        except KeyError as e:
            # If a key error occurs while parsing the retrieved data, this
            # means that the source's Tendermint or Tendermint RPC versions are
            # not compatible with PANIC
            self.logger.exception(e)
            self.logger.error(
                'The Tendermint or Tendermint RPC versions of data source {} '
                'are incompatible with PANIC'.format(source_name))
            raise IncorrectJSONRetrievedException('Cosmos Tendermint RPC',
                                                  repr(e))

    def _get_rest_data_with_pagination_keys(
            self, function, args: List[Any], params: Dict, node_name: str,
            sdk_version: str) -> List[Dict]:
        """
        This function caters for endpoints which make use the pagination field.
        This is done by updating the function arguments before passing the
        function to the cosmos_rest_server_api.execute_with_checks function.
        :param function: The wrapper call to execute
        :param args: The arguments to be passed to the API call
        :param params: The params that should also be passed as arguments. These
                       need to be specified independently because the callee may
                       specify params which are out of the scope of this
                       function. We will assume that params are the last
                       arguments to be passed to the API call
        :param node_name: The name of the data source
        :param sdk_version: The Cosmos SDK version being checked for
        :return: The data split into a number of pages
        :raises: KeyError if the structure of the data returned by the endpoints
                 is not as expected.
        """
        if params is None:
            params = {}

        pagination_key = 'invalid_key'
        paginated_data = []
        while pagination_key is not None:
            params = copy.deepcopy(params)  # To avoid side-effects
            if pagination_key != 'invalid_key':
                params['pagination.key'] = pagination_key
            new_args = args + [params]
            ret = self.cosmos_rest_server_api.execute_with_checks(function,
                                                                  new_args,
                                                                  node_name,
                                                                  sdk_version)
            paginated_data.append(ret)
            pagination_key = ret['pagination']['next_key']

        return paginated_data

    def _get_tendermint_data_with_count(
            self, function, args: List[Any], params: Dict,
            node_name: str) -> List[Dict]:
        """
        This function executes a Tendermint RPC API call with pages in mind. For
        Tendermint, some endpoints subdivide the data into a number of pages.
        These pages can be traversed by counting the number of entries in each
        page until we reach the total number of entries.
        :param function: The Tendermint RPC API call to execute
        :param args: The arguments to pass to the RPC call
        :param params: The params that should also be passed as arguments. These
                       need to be specified independently because the callee may
                       specify params which are out of the scope of this
                       function. We will assume that params are the last
                       arguments to be passed to the API call
        :param node_name: The name of the node used as data source
        :return: The data split into a number of pages
        :raises: KeyError if the structure of the data returned by the endpoints
                 is not as expected.
        """
        if params is None:
            params = {}

        counter = -1
        total = -1
        page = 1
        first_call = True
        data = []
        while counter < total or first_call:
            params = copy.deepcopy(params)  # To avoid side-effects
            params['page'] = page
            ret = self.tendermint_rpc_api.execute_with_checks(
                function, args + [params], node_name)
            data.append(ret)
            if first_call:
                # This check is done just in case an endpoint returns different
                # totals and for initialisation of both counter and total
                total = int(ret['result']['total'])
                counter = 0
                first_call = False
            counter += int(ret['result']['count'])
            page += 1

        return data

    def _display_data(self, data: Dict) -> str:
        """
        Simple json.dumps of the data retrieved and processed by the
        monitor
        :param data: The retrieved and processed data by the monitor
        :return: A string representation of the data dict.
        """
        return json.dumps(data)
