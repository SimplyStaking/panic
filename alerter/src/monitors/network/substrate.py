import copy
import logging
from ast import literal_eval
from datetime import datetime
from typing import List, Dict, Optional, Callable

import pika

from src.configs.nodes.substrate import SubstrateNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.substrate import (
    SubstrateMonitor, _VERSION_INCOMPATIBILITY_EXCEPTIONS)
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    NoSyncedDataSourceWasAccessibleException,
    SubstrateApiIsNotReachableException, DataReadingException,
    IncorrectJSONRetrievedException, SubstrateApiCallException,
    SubstrateNetworkDataCouldNotBeObtained, PANICException)


class SubstrateNetworkMonitor(SubstrateMonitor):
    """
    The SubstrateNetworkMonitor is able to monitor network related substrate
    metrics by obtaining data from the Substrate-API docker service. Currently,
    it is able to monitor governance and GRANDPA consensus health.
    """

    def __init__(
            self, monitor_name: str, data_sources: List[SubstrateNodeConfig],
            governance_addresses: List[str], parent_id: str, chain_name: str,
            logger: logging.Logger, monitor_period: int,
            rabbitmq: RabbitMQApi) -> None:
        super().__init__(monitor_name, data_sources, logger, monitor_period,
                         rabbitmq)
        self._governance_addresses = governance_addresses
        self._parent_id = parent_id
        self._chain_name = chain_name

    @property
    def governance_addresses(self) -> List[str]:
        return self._governance_addresses

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def chain_name(self) -> str:
        return self._chain_name

    def _get_websocket_indirect_data(self, source: SubstrateNodeConfig) -> Dict:
        """
        This function returns the metrics of the substrate network from the
        chosen nodes' websocket interface
        :param source: The data source
        :return: The websocket indirect metrics of the Substrate network
        """
        source_url = source.node_ws_url
        source_name = source.node_name
        if not source_url:
            return {
                'grandpa_stalled': None,
                'public_prop_count': None,
                'active_proposals': None,
                'referendum_count': None,
                'active_referendums': None,
                'all_referendums': None,
            }

        def retrieval_process() -> Dict:
            grandpa_stalled = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_grandpa_stalled, [source_url],
                source_name, False)
            public_prop_count = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_public_prop_count, [source_url],
                source_name, False)
            proposals = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_democracy_proposals,
                [source_url], source_name, False)
            referendum_count = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_referendum_count, [source_url],
                source_name, False)
            referendum_count = literal_eval(str(referendum_count['result']))
            referendums = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_democracy_referendums,
                [source_url], source_name, False)

            # Get info of every referendum to date
            referendum_info_of = {}
            for i in range(0, referendum_count):
                data = self.substrate_api_wrapper.execute_with_checks(
                    self.substrate_api_wrapper.get_referendum_info_of,
                    [source_url, i], source_name, False)
                referendum_info_of[i] = data['result']

            return {
                'grandpa_stalled': grandpa_stalled['result'],
                'public_prop_count': public_prop_count['result'],
                'active_proposals': proposals['result'],
                'referendum_count': referendum_count,
                'active_referendums': referendums['result'],
                'all_referendums': referendum_info_of
            }

        return self._execute_websocket_retrieval_with_exceptions(
            retrieval_process, source)

    def _get_websocket_data(self) -> (Dict, bool, Optional[Exception]):
        """
        This function attempts to retrieve the Websocket metrics.
        :return: If data retrieval successful :
                 ({indirect_data}, False, None)
               : If expected error raised while retrieving data:
                ({}, True, Raised_Error)
        """
        try:
            # Select an indirect node for indirect data retrieval and perform
            # the retrieval
            selected_indirect_node = self._select_websocket_node(
                self.data_sources)
            if selected_indirect_node is None:
                self.logger.error(
                    'No synced indirect Substrate websocket data source was '
                    'accessible.')
                return {}, True, NoSyncedDataSourceWasAccessibleException(
                    self.monitor_name, 'indirect Substrate websocket node')
            indirect_data = self._get_websocket_indirect_data(
                selected_indirect_node)

            self.logger.debug((indirect_data, False, None))
            return indirect_data, False, None
        except (SubstrateApiIsNotReachableException, DataReadingException,
                IncorrectJSONRetrievedException,
                SubstrateApiCallException) as e:
            if type(e) in _VERSION_INCOMPATIBILITY_EXCEPTIONS:
                # If we have an incompatibility issue raise a more meaningful
                # error
                self.logger.error('Substrate network data could not be '
                                  'obtained.')
                return {}, True, SubstrateNetworkDataCouldNotBeObtained()

            self.logger.debug(({}, True, e))
            return {}, True, e

    def _get_data(self) -> Dict:
        """
        This function retrieves the data from various data sources. Due to
        multiple data sources being processed, this function also returns some
        data retrieval information for further processing.
        :return: A dict containing all network metrics.
        """
        # TODO: If we add more interface data sources in the future we need to
        #     : change the `monitoring_enabled` field to the individual
        #     : monitor_<interface> switch
        retrieval_info = {
            'websocket': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self._get_websocket_data,
                'processing_function': self._process_retrieved_websocket_data,
                'monitoring_enabled': True
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
                    'parent_id': self.parent_id,
                    'chain_name': self.chain_name,
                    'time': datetime.now().timestamp(),
                    'governance_addresses': self.governance_addresses
                },
                'message': error.message,
                'code': error.code,
            }
        }

        return processed_data

    def _process_retrieved_websocket_data(self, data: Dict) -> Dict:
        """
        This function attempts to process the retrieved Substrate websocket data
        :param data: The retrieved Substrate websocket data
        :return: A dict with the retrieved data together with some meta-data
        """
        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'parent_id': self.parent_id,
                    'chain_name': self.chain_name,
                    'time': datetime.now().timestamp(),
                    'governance_addresses': self.governance_addresses

                },
                'data': copy.deepcopy(data),
            }
        }

        return processed_data

    @staticmethod
    def _process_retrieved_data(processing_fn: Callable, data: Dict) -> Dict:
        return processing_fn(data)

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY, body=data,
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

        # Only output the gathered data if at least one retrieval occurred and
        # there was no error in the entire retrieval process
        if data_retrieval_failed_list and not any(data_retrieval_failed_list):
            self.logger.debug(self._display_data(processed_data))

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)
