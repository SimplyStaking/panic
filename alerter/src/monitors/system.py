# TODO: Do not save in Redis from here (even is_alive key etc) these must be
#       sent to the data store through a channel. The timeout should then be
#       sent with the alive key by the data transformer to the data store.
#       loading from redis can still be done by some monitors (node)

# TODO: In other monitors we must deal with how we are going to handle Redis
#     : hashes
import json
import logging
from datetime import datetime
from typing import List

from alerter.src.moniterables.system import System
from alerter.src.monitors.monitor import Monitor
from alerter.src.utils.data import get_prometheus_metrics_data


class SystemMonitor(Monitor):
    def __init__(self, monitor_name: str, system: System,
                 logger: logging.Logger) -> None:
        super().__init__(monitor_name, logger)
        self._system = system
        self._metrics_to_monitor = ['process_cpu_seconds_total',
                                    'go_memstats_alloc_bytes',
                                    'go_memstats_alloc_bytes_total',
                                    'process_virtual_memory_bytes',
                                    'process_max_fds',
                                    'process_open_fds',
                                    'node_cpu_seconds_total',
                                    'node_filesystem_avail_bytes',
                                    'node_filesystem_size_bytes',
                                    'node_memory_MemTotal_bytes',
                                    'node_memory_MemAvailable_bytes']

    @property
    def system(self) -> System:
        return self._system

    @property
    def metrics_to_monitor(self) -> List:
        return self._metrics_to_monitor

    def status(self) -> str:
        return self.system.status()

    def get_data(self) -> None:
        self._data = get_prometheus_metrics_data(
            self.system.node_exporter_url, self._metrics_to_monitor,
            self.logger)

    def process_data(self) -> None:
        # Add some meta-data to the processed data
        processed_data = {
            'monitor_name': self.monitor_name,
            'system_type':
                'general' if self.system.is_general_system
                else 'blockchain_node',
            'chain': self.system.chain,
            'time': str(datetime.now().timestamp())
        }

        # Add process CPU seconds total to the processed data
        process_cpu_seconds_total = self.data['process_cpu_seconds_total']
        self.logger.debug('%s process_cpu_seconds_total: %s', self.system,
                          process_cpu_seconds_total)
        self.system.set_process_cpu_seconds_total(process_cpu_seconds_total)
        processed_data['process_cpu_seconds_total'] = process_cpu_seconds_total

        # Add process memory usage percentage to the processed data
        process_memory_usage = (self.data['go_memstats_alloc_bytes'] /
                                self.data[
                                    'go_memstats_alloc_bytes_total']) * 100
        process_memory_usage = float("{:.2f}".format(process_memory_usage))
        self.logger.debug('%s process_memory_usage: %s', self.system,
                          process_memory_usage)
        self.system.set_process_memory_usage(process_memory_usage)
        processed_data['process_memory_usage'] = process_memory_usage

        # Add virtual memory usage to the processed data
        virtual_memory_usage = self.data['process_virtual_memory_bytes']
        self.logger.debug('%s virtual_memory_usage: %s', self.system,
                          virtual_memory_usage)
        self.system.set_virtual_memory_usage(virtual_memory_usage)
        processed_data['virtual_memory_usage'] = virtual_memory_usage

        # Add open file descriptors percentage to the processed data
        open_file_descriptors = \
            (self.data['process_open_fds'] / self.data['process_max_fds']) * 100
        self.logger.debug('%s open_file_descriptors: %s', self.system,
                          open_file_descriptors)
        self.system.set_open_file_descriptors(open_file_descriptors)
        processed_data['open_file_descriptors'] = open_file_descriptors

        # Add system CPU usage percentage to processed data
        # Find the system cpu usage by subtracting 100 from the percentage of
        # the time in idle mode
        node_cpu_seconds_idle = 0
        node_cpu_seconds_total = 0
        for i, j in enumerate(self.data['node_cpu_seconds_total']):
            if json.loads(j)['mode'] == 'idle':
                node_cpu_seconds_idle += self.data['node_cpu_seconds_total'][j]
            node_cpu_seconds_total += self.data['node_cpu_seconds_total'][j]

        system_cpu_usage = 100 - (
                (node_cpu_seconds_idle / node_cpu_seconds_total) * 100)
        system_cpu_usage = float("{:.2f}".format(system_cpu_usage))
        self.logger.debug('%s system_cpu_usage: %s', self.system,
                          system_cpu_usage)
        self.system.set_system_cpu_usage(system_cpu_usage)
        processed_data['system_cpu_usage'] = system_cpu_usage

        # Add system RAM usage percentage to processed data
        system_ram_usage = ((self.data['node_memory_MemTotal_bytes'] -
                             self.data['node_memory_MemAvailable_bytes']) /
                            self.data['node_memory_MemTotal_bytes']) * 100
        system_ram_usage = float("{:.2f}".format(system_ram_usage))
        self.logger.debug('%s system_ram_usage: %s', self.system,
                          system_ram_usage)
        self.system.set_system_ram_usage(system_ram_usage)
        processed_data['system_ram_usage'] = system_ram_usage

        # Add system storage usage percentage to processed data
        node_filesystem_avail_bytes = 0
        node_filesystem_size_bytes = 0
        for i, j in enumerate(self.data['node_filesystem_avail_bytes']):
            node_filesystem_avail_bytes += \
                self.data['node_filesystem_avail_bytes'][j]

        for i, j in enumerate(self.data['node_filesystem_size_bytes']):
            node_filesystem_size_bytes += \
                self.data['node_filesystem_size_bytes'][j]

        system_storage_usage = 100 - (
                (node_filesystem_avail_bytes / node_filesystem_size_bytes)
                * 100)
        system_storage_usage = float("{:.2f}".format(system_storage_usage))
        self.logger.debug('%s system_storage_usage: %s', self.system,
                          system_storage_usage)
        self.system.set_system_storage_usage(system_storage_usage)
        processed_data['system_storage_usage'] = system_storage_usage

        self._data = processed_data

# TODO: Include network usage also to counter DDOS (receive_bytes add 3,
#     : transmit_bytes add 3)
#     : (current-old)/(time period)
