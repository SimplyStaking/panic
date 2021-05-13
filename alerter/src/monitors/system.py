import copy
import json
import logging
from datetime import datetime
from http.client import IncompleteRead
from typing import Dict

import pika
import pika.exceptions
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.constants import RAW_DATA_EXCHANGE, SYSTEM_RAW_DATA_ROUTING_KEY
from src.utils.data import get_prometheus_metrics_data
from src.utils.exceptions import (MetricNotFoundException,
                                  SystemIsDownException, DataReadingException,
                                  PANICException, InvalidUrlException)


class SystemMonitor(Monitor):
    def __init__(self, monitor_name: str, system_config: SystemConfig,
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._system_config = system_config
        self._metrics_to_monitor = {
            'process_cpu_seconds_total': 'strict',
            'go_memstats_alloc_bytes': 'strict',
            'go_memstats_alloc_bytes_total': 'strict',
            'process_virtual_memory_bytes': 'strict',
            'process_max_fds': 'strict',
            'process_open_fds': 'strict',
            'node_cpu_seconds_total': 'strict',
            'node_filesystem_avail_bytes': 'strict',
            'node_filesystem_size_bytes': 'strict',
            'node_memory_MemTotal_bytes': 'strict',
            'node_memory_MemAvailable_bytes': 'strict',
            'node_network_transmit_bytes_total': 'strict',
            'node_network_receive_bytes_total': 'strict',
            'node_disk_io_time_seconds_total': 'strict'
        }

    @property
    def system_config(self) -> SystemConfig:
        return self._system_config

    @property
    def metrics_to_monitor(self) -> Dict[str, str]:
        return self._metrics_to_monitor

    def _display_data(self, data: Dict) -> str:
        # This function assumes that the data has been obtained and processed
        # successfully by the system monitor
        return "process_cpu_seconds_total={}, process_memory_usage={}, " \
               "virtual_memory_usage={}, open_file_descriptors={}, " \
               "system_cpu_usage={}, system_ram_usage={}, " \
               "system_storage_usage={}, network_transmit_bytes_total={}, " \
               "network_receive_bytes_total={}, disk_io_time_seconds_total={}" \
               "".format(data['process_cpu_seconds_total'],
                         data['process_memory_usage'],
                         data['virtual_memory_usage'],
                         data['open_file_descriptors'],
                         data['system_cpu_usage'],
                         data['system_ram_usage'],
                         data['system_storage_usage'],
                         data['network_transmit_bytes_total'],
                         data['network_receive_bytes_total'],
                         data['disk_io_time_seconds_total'])

    def _get_data(self) -> Dict:
        return get_prometheus_metrics_data(self.system_config.node_exporter_url,
                                           self.metrics_to_monitor, self.logger,
                                           verify=False)

    def _process_error(self, error: PANICException) -> Dict:
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'system_name': self.system_config.system_name,
                    'system_id': self.system_config.system_id,
                    'system_parent_id': self.system_config.parent_id,
                    'time': datetime.now().timestamp()
                },
                'message': error.message,
                'code': error.code,
            }
        }

        return processed_data

    def _process_retrieved_data(self, data: Dict) -> Dict:
        data_copy = copy.deepcopy(data)

        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'system_name': self.system_config.system_name,
                    'system_id': self.system_config.system_id,
                    'system_parent_id': self.system_config.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': {},
            }
        }

        # Add process CPU seconds total to the processed data
        process_cpu_seconds_total = data_copy['process_cpu_seconds_total']
        self.logger.debug("%s process_cpu_seconds_total: %s",
                          self.system_config, process_cpu_seconds_total)
        processed_data['result']['data']['process_cpu_seconds_total'] = \
            process_cpu_seconds_total

        # Add process memory usage percentage to the processed data
        process_memory_usage = (data_copy['go_memstats_alloc_bytes'] /
                                data_copy[
                                    'go_memstats_alloc_bytes_total']) * 100
        process_memory_usage = float("{:.2f}".format(process_memory_usage))
        self.logger.debug("%s process_memory_usage: %s", self.system_config,
                          process_memory_usage)
        processed_data['result']['data']['process_memory_usage'] = \
            process_memory_usage

        # Add virtual memory usage to the processed data
        virtual_memory_usage = data_copy['process_virtual_memory_bytes']
        self.logger.debug("%s virtual_memory_usage: %s", self.system_config,
                          virtual_memory_usage)
        processed_data['result']['data']['virtual_memory_usage'] = \
            virtual_memory_usage

        # Add open file descriptors percentage to the processed data
        open_file_descriptors = \
            (data_copy['process_open_fds'] / data_copy['process_max_fds']) * 100
        self.logger.debug("%s open_file_descriptors: %s", self.system_config,
                          open_file_descriptors)
        processed_data['result']['data']['open_file_descriptors'] = \
            open_file_descriptors

        # Add system CPU usage percentage to processed data
        # Find the system cpu usage by subtracting 100 from the percentage of
        # the time in idle mode
        node_cpu_seconds_idle = 0
        node_cpu_seconds_total = 0
        for _, data_subset in enumerate(data_copy['node_cpu_seconds_total']):
            if json.loads(data_subset)['mode'] == 'idle':
                node_cpu_seconds_idle += \
                    data_copy['node_cpu_seconds_total'][data_subset]
            node_cpu_seconds_total += \
                data_copy['node_cpu_seconds_total'][data_subset]

        system_cpu_usage = 100 - (
                (node_cpu_seconds_idle / node_cpu_seconds_total) * 100)
        system_cpu_usage = float("{:.2f}".format(system_cpu_usage))
        self.logger.debug("%s system_cpu_usage: %s", self.system_config,
                          system_cpu_usage)
        processed_data['result']['data']['system_cpu_usage'] = \
            system_cpu_usage

        # Add system RAM usage percentage to processed data
        system_ram_usage = ((data_copy['node_memory_MemTotal_bytes'] -
                             data_copy['node_memory_MemAvailable_bytes']) /
                            data_copy['node_memory_MemTotal_bytes']) * 100
        system_ram_usage = float("{:.2f}".format(system_ram_usage))
        self.logger.debug("%s system_ram_usage: %s", self.system_config,
                          system_ram_usage)
        processed_data['result']['data']['system_ram_usage'] = system_ram_usage

        # Add system storage usage percentage to processed data
        node_filesystem_avail_bytes = 0
        node_filesystem_size_bytes = 0
        for _, data_subset in enumerate(
                data_copy['node_filesystem_avail_bytes']):
            node_filesystem_avail_bytes += \
                data_copy['node_filesystem_avail_bytes'][data_subset]

        for _, data_subset in enumerate(
                data_copy['node_filesystem_size_bytes']):
            node_filesystem_size_bytes += \
                data_copy['node_filesystem_size_bytes'][data_subset]

        system_storage_usage = 100 - (
                (node_filesystem_avail_bytes / node_filesystem_size_bytes)
                * 100)
        system_storage_usage = float("{:.2f}".format(system_storage_usage))
        self.logger.debug("%s system_storage_usage: %s", self.system_config,
                          system_storage_usage)
        processed_data['result']['data']['system_storage_usage'] = \
            system_storage_usage

        # Add the node network transmit/received bytes total to the processed
        # data
        receive_bytes_total = 0
        transmit_bytes_total = 0
        for _, data_subset in enumerate(
                data_copy['node_network_receive_bytes_total']):
            receive_bytes_total += \
                data_copy['node_network_receive_bytes_total'][data_subset]

        for _, data_subset in enumerate(
                data_copy['node_network_transmit_bytes_total']):
            transmit_bytes_total += \
                data_copy['node_network_transmit_bytes_total'][data_subset]

        self.logger.debug("%s network_receive_bytes_total: %s, "
                          "network_transmit_bytes_total: %s",
                          self.system_config, receive_bytes_total,
                          transmit_bytes_total)
        processed_data['result']['data']['network_receive_bytes_total'] = \
            receive_bytes_total
        processed_data['result']['data']['network_transmit_bytes_total'] = \
            transmit_bytes_total

        # Add the time spent in seconds doing disk i/o to the processed data.
        disk_io_time_seconds_total = 0
        for _, data_subset in enumerate(
                data_copy['node_disk_io_time_seconds_total']):
            disk_io_time_seconds_total += \
                data_copy['node_disk_io_time_seconds_total'][data_subset]

        self.logger.debug("%s disk_io_time_seconds_total: %s",
                          self.system_config, disk_io_time_seconds_total)
        processed_data['result']['data']['disk_io_time_seconds_total'] = \
            disk_io_time_seconds_total

        return processed_data

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE, routing_key=SYSTEM_RAW_DATA_ROUTING_KEY,
            body=data, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.debug("Sent data to '%s' exchange", RAW_DATA_EXCHANGE)

    def _monitor(self) -> None:
        data_retrieval_exception = None
        data = None
        data_retrieval_failed = True
        try:
            data = self._get_data()
            data_retrieval_failed = False
        except (ReqConnectionError, ReadTimeout):
            data_retrieval_exception = SystemIsDownException(
                self.system_config.system_name)
            self.logger.error("Error when retrieving data from %s",
                              self.system_config.node_exporter_url)
            self.logger.exception(data_retrieval_exception)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError):
            data_retrieval_exception = DataReadingException(
                self.monitor_name, self.system_config.system_name)
            self.logger.error("Error when retrieving data from %s",
                              self.system_config.node_exporter_url)
            self.logger.exception(data_retrieval_exception)
        except (InvalidURL, InvalidSchema, MissingSchema):
            data_retrieval_exception = InvalidUrlException(
                self.system_config.node_exporter_url)
            self.logger.error("Error when retrieving data from %s",
                              self.system_config.node_exporter_url)
            self.logger.exception(data_retrieval_exception)
        except MetricNotFoundException as e:
            data_retrieval_exception = e
            self.logger.error("Error when retrieving data from %s",
                              self.system_config.node_exporter_url)
            self.logger.exception(data_retrieval_exception)

        try:
            processed_data = self._process_data(data_retrieval_failed,
                                                [data_retrieval_exception],
                                                [data])
        except Exception as error:
            self.logger.error("Error when processing data obtained from %s",
                              self.system_config.node_exporter_url)
            self.logger.exception(error)
            # Do not send data if we experienced processing errors
            return

        self._send_data(processed_data)

        if not data_retrieval_failed:
            # Only output the gathered data if there was no error
            self.logger.info(self._display_data(
                processed_data['result']['data']))

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)
