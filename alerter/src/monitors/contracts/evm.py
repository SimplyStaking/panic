import logging
from http.client import IncompleteRead
from typing import List, Dict, Optional

from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError
from web3 import Web3

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.constants.data import WEI_WATCHERS_URL_TEMPLATE
from src.utils.data import get_json
from src.utils.exceptions import ComponentNotGivenEnoughDataSourcesException


class EVMContractsMonitor(Monitor):
    """
    The EVMContractsMonitor is able to monitor contracts of an EVM based chain.
    For now, only chainlink chains are supported.
    """

    def __init__(self, monitor_name: str, chain_name: str, evm_nodes: List[str],
                 node_configs: List[ChainlinkNodeConfig],
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        # An exception is raised if the monitor is not given enough data
        # sources. The callee must also make sure that the given node_configs
        # have valid prometheus urls, and that prometheus is enabled.
        if len(evm_nodes) == 0 or len(node_configs) == 0:
            field = 'data_sources' if len(
                evm_nodes) == 0 else 'node_configs'
            raise ComponentNotGivenEnoughDataSourcesException(
                monitor_name, field)

        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._node_configs = node_configs

        # Construct the Web3 interfaces
        self._evm_node_w3_interface = {}
        for evm_node_url in evm_nodes:
            self._evm_node_w3_interface[evm_node_url] = Web3(Web3.HTTPProvider(
                evm_node_url, request_kwargs={'timeout': 2}))

        # Construct the wei-watchers url. This url will be used to get all
        # chain contracts. Note, for ethereum no chain is supplied to the url.
        url_chain_name = '' if chain_name == 'ethereum' else chain_name
        self._contracts_url = WEI_WATCHERS_URL_TEMPLATE.format(url_chain_name)

    @property
    def node_configs(self) -> List[ChainlinkNodeConfig]:
        return self._node_configs

    @property
    def evm_node_w3_interface(self) -> Dict[str, Web3]:
        return self._evm_node_w3_interface

    @property
    def contracts_url(self) -> str:
        return self._contracts_url

    def get_chain_contracts(self) -> Dict:
        """
        This functions retrieves all the chain contracts along with some data.
        :return: A list of chain contracts together with data.
        """
        return get_json(self._contracts_url, self.logger, None, True)

    def select_node(self) -> Optional[str]:
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
                self.logger.error("Error when trying to access %s", node_url)
                self.logger.exception(e)

        return None

    # def _get_data(self) -> Dict:
    #     return {
    #         'current_height': self.w3_interface.eth.block_number
    #     }

    #
    # def _display_data(self, data: Dict) -> str:
    #     # This function assumes that the data has been obtained and processed
    #     # successfully by the node monitor
    #     return "current_height={}".format(data['current_height'])
    #
    #
    # def _process_error(self, error: PANICException) -> Dict:
    #     processed_data = {
    #         'error': {
    #             'meta_data': {
    #                 'monitor_name': self.monitor_name,
    #                 'node_name': self.node_config.node_name,
    #                 'node_id': self.node_config.node_id,
    #                 'node_parent_id': self.node_config.parent_id,
    #                 'time': datetime.now().timestamp()
    #             },
    #             'message': error.message,
    #             'code': error.code,
    #         }
    #     }
    #
    #     return processed_data
    #
    # def _process_retrieved_data(self, data: Dict) -> Dict:
    #     # Add some meta-data to the processed data
    #     processed_data = {
    #         'result': {
    #             'meta_data': {
    #                 'monitor_name': self.monitor_name,
    #                 'node_name': self.node_config.node_name,
    #                 'node_id': self.node_config.node_id,
    #                 'node_parent_id': self.node_config.parent_id,
    #                 'time': datetime.now().timestamp()
    #             },
    #             'data': copy.deepcopy(data),
    #         }
    #     }
    #
    #     return processed_data
    #
    # def _send_data(self, data: Dict) -> None:
    #     self.rabbitmq.basic_publish_confirm(
    #         exchange=RAW_DATA_EXCHANGE,
    #         routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY, body=data,
    #         is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
    #         mandatory=True)
    #     self.logger.debug("Sent data to '%s' exchange", RAW_DATA_EXCHANGE)
    #
    # def _monitor(self) -> None:
    #     data_retrieval_exception = None
    #     data = None
    #     data_retrieval_failed = True
    #     try:
    #         data = self._get_data()
    #         data_retrieval_failed = False
    #     except (ReqConnectionError, ReadTimeout):
    #         data_retrieval_exception = NodeIsDownException(
    #             self.node_config.node_name)
    #         self.logger.error("Error when retrieving data from %s",
    #                           self.node_config.node_http_url)
    #         self.logger.exception(data_retrieval_exception)
    #     except (IncompleteRead, ChunkedEncodingError, ProtocolError):
    #         data_retrieval_exception = DataReadingException(
    #             self.monitor_name, self.node_config.node_name)
    #         self.logger.error("Error when retrieving data from %s",
    #                           self.node_config.node_http_url)
    #         self.logger.exception(data_retrieval_exception)
    #     except (InvalidURL, InvalidSchema, MissingSchema):
    #         data_retrieval_exception = InvalidUrlException(
    #             self.node_config.node_http_url)
    #         self.logger.error("Error when retrieving data from %s",
    #                           self.node_config.node_http_url)
    #         self.logger.exception(data_retrieval_exception)
    #
    #     try:
    #         processed_data = self._process_data(data_retrieval_failed,
    #                                             [data_retrieval_exception],
    #                                             [data])
    #     except Exception as error:
    #         self.logger.error("Error when processing data obtained from %s",
    #                           self.node_config.node_http_url)
    #         self.logger.exception(error)
    #         # Do not send data if we experienced processing errors
    #         return
    #
    #     self._send_data(processed_data)
    #
    #     if not data_retrieval_failed:
    #         # Only output the gathered data if there was no error
    #         self.logger.info(self._display_data(
    #             processed_data['result']['data']))
    #
    #     # Send a heartbeat only if the entire round was successful
    #     heartbeat = {
    #         'component_name': self.monitor_name,
    #         'is_alive': True,
    #         'timestamp': datetime.now().timestamp()
    #     }
    #     self._send_heartbeat(heartbeat)

# TODO: Add chain_name and list of evm nodes. Aggregate list of evm urls
#     : in manager. Check if equal.
# TODO: Manager should not start contracts monitor if list of evm nodes
#     : empty or list of chainlink node configs empty. For every node config
#     : we must also check that prometheus is enabled, and the list of
#     : http sources is non empty.
