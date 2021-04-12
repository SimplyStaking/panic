import logging
from typing import List, Dict

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.data import get_prometheus_metrics_data


class ChainlinkNodeMonitor(Monitor):
    def __init__(self, monitor_name: str, node_config: ChainlinkNodeConfig,
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._node_config = node_config
        self._metrics_to_monitor = ['head_tracker_current_head',
                                    ]

    @property
    def node_config(self) -> ChainlinkNodeConfig:
        return self._node_config

    @property
    def metrics_to_monitor(self) -> List[str]:
        return self._metrics_to_monitor

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
        # TODO: Need to cater for multiple urls. If a downtime related exception
        #     : is raised, catch it here and re-try. If no more urls available
        #     : raise downtime. If other alert raise it immediately and don't
        #     : try again. Otherwise return the data.
        return get_prometheus_metrics_data(
            'https://172.16.152.160:1000/metrics',
            self.metrics_to_monitor, self.logger)


metrics_to_monitor = ['head_tracker_current_head']
print(get_prometheus_metrics_data('https://172.16.152.160:1000/metrics',
                                  metrics_to_monitor,
                                  logging.getLogger('Dummy'), False))
