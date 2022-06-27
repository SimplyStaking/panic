import json
import logging
from abc import ABC
from http.client import IncompleteRead
from typing import List, Dict, Optional, Callable

from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.api_wrappers.substrate import SubstrateApiWrapper
from src.configs.nodes.substrate import SubstrateNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils import env
from src.utils.exceptions import (
    ComponentNotGivenEnoughDataSourcesException, SubstrateApiCallException,
    SubstrateApiIsNotReachableException, DataReadingException,
    IncorrectJSONRetrievedException)

_VERSION_INCOMPATIBILITY_EXCEPTIONS = [IncorrectJSONRetrievedException]


class SubstrateMonitor(Monitor, ABC):
    def __init__(self, monitor_name: str,
                 data_sources: List[SubstrateNodeConfig],
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        # An exception is raised if the monitor is not given enough data
        # sources.
        if len(data_sources) == 0:
            raise ComponentNotGivenEnoughDataSourcesException(monitor_name,
                                                              'data_sources')

        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._data_sources = data_sources
        self._substrate_api_wrapper = SubstrateApiWrapper(
            env.SUBSTRATE_API_IP, env.SUBSTRATE_API_PORT, self.logger)

    @property
    def data_sources(self) -> List[SubstrateNodeConfig]:
        return self._data_sources

    @property
    def substrate_api_wrapper(self) -> SubstrateApiWrapper:
        return self._substrate_api_wrapper

    def _select_websocket_node(self, nodes: List[SubstrateNodeConfig]
                               ) -> Optional[SubstrateNodeConfig]:
        """
        This function returns the configuration of the selected node. A node is
        selected only if we can retrieve its syncing status from the
        Substrate-API service, and it is not syncing
        :param nodes: The list of nodes to select from
        :return: The node config of the selected node
                 None if no node is selected
        :raises: SubstrateApiIsNotReachableException if the Substrate-API
                 service cannot be reached
        """
        for node in nodes:
            ws_url = node.node_ws_url
            node_name = node.node_name
            try:
                api_ret = self.substrate_api_wrapper.execute_with_checks(
                    self.substrate_api_wrapper.get_system_health, [ws_url],
                    node_name, False)
                if not api_ret['result']['isSyncing']:
                    self.logger.debug('chosen %s.', ws_url)
                    return node
            except (ReqConnectionError, ReadTimeout, InvalidURL, InvalidSchema,
                    MissingSchema) as e:
                # This means that the Substrate API either cannot be reached due
                # to a connection issue or because the url is incorrect
                self.logger.error('Substrate API cannot be reached at %s',
                                  self.substrate_api_wrapper.api_url)
                self.logger.exception(e)
                raise SubstrateApiIsNotReachableException(
                    self.monitor_name, self.substrate_api_wrapper.api_url)
            except (IncompleteRead, ChunkedEncodingError, ProtocolError,
                    SubstrateApiCallException, KeyError) as e:
                # This means that there was an issue while reading data from
                # the API. This may indicate a connection hiccup or a failed
                # API call, therefore, re-try again with another node.
                self.logger.error("Error when trying to access %s", ws_url)
                self.logger.exception(e)

        return None

    def _execute_websocket_retrieval_with_exceptions(
            self, function: Callable, source: SubstrateNodeConfig) -> Dict:
        """
        This helper executes the Websocket data retrieval procedure with some
        exception handling.
        :param function: The Websocket data retrieval procedure
        :param source: The node configuration of the data source
        :return: Dict containing all retrieved metrics
        :raises: DataReadingException if data cannot be read from the source
               : CannotConnectWithDataSourceException if we cannot connect with
                 the data source (only for indirect/archive data retrieval)
               : NodeIsDownException if the node being monitored cannot be
                 directly accessed at the websocket endpoint
               : InvalidUrlException if the URL of the data source does not have
                 a valid schema
               : IncorrectJSONRetrievedException if the structure of the data
                 returned by the endpoints is not as expected. This could be
                 due to a Substrate API update
        """
        try:
            return function()
        except (ReqConnectionError, ReadTimeout, InvalidURL, InvalidSchema,
                MissingSchema) as e:
            # This means that the Substrate API either cannot be reached due
            # to a connection issue or because the url is incorrect
            self.logger.error(
                "Substrate-API cannot be reached at {}. Error: {}".format(
                    self.substrate_api_wrapper.api_url, e))
            self.logger.exception(e)
            raise SubstrateApiIsNotReachableException(
                self.monitor_name, self.substrate_api_wrapper.api_url)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError) as e:
            # This means that there was an issue while reading data from the
            # API, normally due to a connection hiccup.
            self.logger.error(
                "Issue while reading data from the Substrate-API at {}. "
                "Error: {}".format(self.substrate_api_wrapper.api_url, e))
            self.logger.exception(e)
            raise DataReadingException(self.monitor_name,
                                       self.substrate_api_wrapper.api_url)
        except KeyError as e:
            # This means that the retrieved data has an incorrect structure,
            # possibly meaning that PANIC is not compatible with the
            # node/network
            self.logger.error(
                'Data retrieved from {} is not compatible with PANIC.'.format(
                    source.node_name))
            self.logger.exception(e)
            raise IncorrectJSONRetrievedException('websocket', repr(e))

    def _display_data(self, data: Dict) -> str:
        """
        Simple 'json.dumps' of the data retrieved and processed by the
        monitor
        :param data: The retrieved and processed data by the monitor
        :return: A string representation of the data dict.
        """
        return json.dumps(data)
