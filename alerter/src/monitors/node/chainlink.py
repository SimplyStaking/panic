import logging
from typing import List, Dict

from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout)

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.data import get_prometheus_metrics_data
from src.utils.exceptions import (NoMonitoringSourceGivenException,
                                  NodeIsDownException)


class ChainlinkNodeMonitor(Monitor):
    def __init__(self, monitor_name: str, node_config: ChainlinkNodeConfig,
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        if len(node_config.node_prometheus_urls) == 0:
            raise NoMonitoringSourceGivenException(node_config.node_name)

        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._node_config = node_config
        self._metrics_to_monitor = ['head_tracker_current_head',
                                    'head_tracker_heads_in_queue',
                                    'head_tracker_heads_received_total',
                                    'head_tracker_num_heads_dropped_total',
                                    'job_subscriber_subscriptions',
                                    'max_unconfirmed_blocks',
                                    'process_start_time_seconds',
                                    'tx_manager_num_gas_bumps_total'
                                    'tx_manager_gas_bump_exceeds_limit_total'
                                    'unconfirmed_transactions'
                                    'run_status_update_total'
                                    ]
        self._last_source_used = node_config.node_prometheus_urls[0]

    @property
    def node_config(self) -> ChainlinkNodeConfig:
        return self._node_config

    @property
    def metrics_to_monitor(self) -> List[str]:
        return self._metrics_to_monitor

    @property
    def last_source_used(self) -> str:
        return self._last_source_used

    # def _display_data(self, data: Dict) -> str:
    #     # This function assumes that the data has been obtained and processed
    #     # successfully by the system monitor
    #     return "process_cpu_seconds_total={}, process_memory_usage={}, " \
    #            "virtual_memory_usage={}, open_file_descriptors={}, " \
    #            "system_cpu_usage={}, system_ram_usage={}, " \
    #            "system_storage_usage={}, network_transmit_bytes_total={}, " \
    #            "network_receive_bytes_total={}, disk_io_time_seconds_total={}" \
    #            "".format(data['process_cpu_seconds_total'],
    #                      data['process_memory_usage'],
    #                      data['virtual_memory_usage'],
    #                      data['open_file_descriptors'],
    #                      data['system_cpu_usage'],
    #                      data['system_ram_usage'],
    #                      data['system_storage_usage'],
    #                      data['network_transmit_bytes_total'],
    #                      data['network_receive_bytes_total'],
    #                      data['disk_io_time_seconds_total'])

    def _get_data(self) -> Dict:
        """
        This method will try to get all the metrics from the chainlink node
        which is online. It first tries to get the metrics from the last source
        used, if it fails, it tries to get the data from the back-up nodes.
        If it can't connect with any node, it will raise a NodeIsDownException.
        If it connected with a node, and the node raised another error, it will
        raise that error because it means that the correct node was selected but
        another issue was found.
        :return: A Dict containing all the metric values.
        """
        try:
            return get_prometheus_metrics_data(self.last_source_used,
                                               self.metrics_to_monitor,
                                               self.logger)
        except (ReqConnectionError, ReadTimeout):
            self.logger.debug("Could not connect with %s. Will try to obtain "
                              "the metrics from another backup source.",
                              self.last_source_used)

        for source in self.node_config.node_prometheus_urls:
            try:
                data = get_prometheus_metrics_data(source,
                                                   self.metrics_to_monitor,
                                                   self.logger)
                self._last_source_used = source
                return data
            except (ReqConnectionError, ReadTimeout):
                self.logger.debug(
                    "Could not connect with %s. Will try to obtain "
                    "the metrics from another backup source.",
                    self.last_source_used)

        raise NodeIsDownException(self.node_config.node_name)
