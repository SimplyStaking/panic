import logging
from typing import List

from web3 import Web3

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.exceptions import ComponentNotGivenEnoughDataSourcesException


class EVMContractsMonitor(Monitor):
    """
    The EVMContractsMonitor is able to monitor contracts of an EVM based chain.
    For now, only chainlink chains are supported.
    """

    # TODO: Add chain_name and list of evm nodes. Aggregate list of evm urls
    #     : in manager. Check if equal.
    # TODO: Manager should not start contracts monitor if list of evm nodes
    #     : empty or list of chainlink node configs empty. For every node config
    #     : we must also check that prometheus is enabled, and the list of
    #     : http sources is non empty.
    def __init__(self, monitor_name: str, chain_name: str,
                 evm_nodes: List[str],
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
        self._chain_name = chain_name
        self._evm_nodes = evm_nodes
        self._node_configs = node_configs

        # This interface performs RPC requests, therefore no connection needs
        # to be managed. We can just perform the requests immediately and catch
        # errors.
        # TODO: Must perform interface management, construct wei-watchers list
        #     : etc.
        self._w3_interface = Web3(Web3.HTTPProvider(
            self.node_config.node_http_url, request_kwargs={'timeout': 2}))

        # TODO: Need to check that contracts_monitoring is enabled.
        # TODO: Do not use syncing nodes

    # @property
    # def node_config(self) -> EVMNodeConfig:
    #     return self._node_config
    #
    # @property
    # def w3_interface(self) -> Web3:
    #     return self._w3_interface
    #
    # def _display_data(self, data: Dict) -> str:
    #     # This function assumes that the data has been obtained and processed
    #     # successfully by the node monitor
    #     return "current_height={}".format(data['current_height'])
    #
    # def _get_data(self) -> Dict:
    #     return {
    #         'current_height': self.w3_interface.eth.block_number
    #     }
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
