import json
import logging
import time
from datetime import datetime
from http.client import IncompleteRead
from typing import Optional, List

import pika
import pika.exceptions
from requests.exceptions import ConnectionError as ReqConnectionError, \
    ReadTimeout, ChunkedEncodingError
from urllib3.exceptions import ProtocolError

from alerter.src.configs.system import SystemConfig
from alerter.src.monitors.monitor import Monitor
from alerter.src.utils.data import get_prometheus_metrics_data
from alerter.src.utils.exceptions import MetricNotFoundException, \
    SystemIsDownException, DataReadingException, PANICException, \
    MessageWasNotDeliveredException


class SystemMonitor(Monitor):
    def __init__(self, monitor_name: str, system_config: SystemConfig,
                 logger: logging.Logger, monitor_period: int) -> None:
        super().__init__(monitor_name, logger, monitor_period)
        self._system_config = system_config
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
                                    'node_memory_MemAvailable_bytes',
                                    'node_network_transmit_bytes_total',
                                    'node_network_receive_bytes_total']
        self._process_cpu_seconds_total = None  # Seconds
        self._process_memory_usage = None  # Percentage
        self._virtual_memory_usage = None  # Bytes
        self._open_file_descriptors = None  # Percentage
        self._system_cpu_usage = None  # Percentage
        self._system_ram_usage = None  # Percentage
        self._system_storage_usage = None  # Percentage
        self._network_receive_bytes_total = None
        self._network_transmit_bytes_total = None

    @property
    def system_config(self) -> SystemConfig:
        return self._system_config

    @property
    def metrics_to_monitor(self) -> List:
        return self._metrics_to_monitor

    @property
    def process_cpu_seconds_total(self) -> Optional[float]:
        return self._process_cpu_seconds_total

    @property
    def process_memory_usage(self) -> Optional[float]:
        return self._process_memory_usage

    @property
    def virtual_memory_usage(self) -> Optional[float]:
        return self._virtual_memory_usage

    @property
    def open_file_descriptors(self) -> Optional[float]:
        return self._open_file_descriptors

    @property
    def system_cpu_usage(self) -> Optional[float]:
        return self._system_cpu_usage

    @property
    def system_ram_usage(self) -> Optional[float]:
        return self._system_ram_usage

    @property
    def system_storage_usage(self) -> Optional[float]:
        return self._system_storage_usage

    @property
    def network_receive_bytes_total(self) -> Optional[float]:
        return self._network_receive_bytes_total

    @property
    def network_transmit_bytes_total(self) -> Optional[float]:
        return self._network_transmit_bytes_total

    def status(self) -> str:
        return "process_cpu_seconds_total={}, " \
               "process_memory_usage={}, virtual_memory_usage={}, " \
               "open_file_descriptors={}, system_cpu_usage={}, " \
               "system_ram_usage={}, system_storage_usage={}, " \
               "network_transmit_bytes_total={}, " \
               "network_receive_bytes_total={}" \
               "".format(self.process_cpu_seconds_total,
                         self.process_memory_usage, self.virtual_memory_usage,
                         self.open_file_descriptors, self.system_cpu_usage,
                         self.system_ram_usage, self.system_storage_usage,
                         self.network_transmit_bytes_total,
                         self.network_receive_bytes_total)

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info('Setting delivery confirmation on RabbitMQ channel')
        self.rabbitmq.confirm_delivery()
        self.logger.info('Creating \'raw_data\' exchange')
        self.rabbitmq.exchange_declare('raw_data', 'direct', False, True, False,
                                       False)

    def _get_data(self) -> None:
        self._data = get_prometheus_metrics_data(
            self.system_config.node_exporter_url, self.metrics_to_monitor,
            self.logger)

    def _process_data_retrieval_failed(self, error: PANICException) -> None:
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'system_name': self.system_config.system_name,
                    'system_id': self.system_config.system_id,
                    'system_parent_id': self.system_config.parent_id,
                    'time': str(datetime.now().timestamp())
                },
                'message': error.message,
                'code': error.code,
            }
        }

        self._data = processed_data

    def _process_data_retrieval_successful(self) -> None:
        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'system_name': self.system_config.system_name,
                    'system_id': self.system_config.system_id,
                    'system_parent_id': self.system_config.parent_id,
                    'time': str(datetime.now().timestamp())
                },
                'data': {},
            }
        }

        # Add process CPU seconds total to the processed data
        process_cpu_seconds_total = self.data['process_cpu_seconds_total']
        self.logger.debug('%s process_cpu_seconds_total: %s',
                          self.system_config, process_cpu_seconds_total)
        processed_data['result']['data']['process_cpu_seconds_total'] = \
            process_cpu_seconds_total
        self._process_cpu_seconds_total = process_cpu_seconds_total

        # Add process memory usage percentage to the processed data
        process_memory_usage = (self.data['go_memstats_alloc_bytes'] /
                                self.data[
                                    'go_memstats_alloc_bytes_total']) * 100
        process_memory_usage = float("{:.2f}".format(process_memory_usage))
        self.logger.debug('%s process_memory_usage: %s', self.system_config,
                          process_memory_usage)
        processed_data['result']['data']['process_memory_usage'] = \
            process_memory_usage
        self._process_memory_usage = process_memory_usage

        # Add virtual memory usage to the processed data
        virtual_memory_usage = self.data['process_virtual_memory_bytes']
        self.logger.debug('%s virtual_memory_usage: %s', self.system_config,
                          virtual_memory_usage)
        processed_data['result']['data']['virtual_memory_usage'] = \
            virtual_memory_usage
        self._virtual_memory_usage = virtual_memory_usage

        # Add open file descriptors percentage to the processed data
        open_file_descriptors = \
            (self.data['process_open_fds'] / self.data['process_max_fds']) * 100
        self.logger.debug('%s open_file_descriptors: %s', self.system_config,
                          open_file_descriptors)
        processed_data['result']['data']['open_file_descriptors'] = \
            open_file_descriptors
        self._open_file_descriptors = open_file_descriptors

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
        self.logger.debug('%s system_cpu_usage: %s', self.system_config,
                          system_cpu_usage)
        processed_data['result']['data']['system_cpu_usage'] = \
            system_cpu_usage
        self._system_cpu_usage = system_cpu_usage

        # Add system RAM usage percentage to processed data
        system_ram_usage = ((self.data['node_memory_MemTotal_bytes'] -
                             self.data['node_memory_MemAvailable_bytes']) /
                            self.data['node_memory_MemTotal_bytes']) * 100
        system_ram_usage = float("{:.2f}".format(system_ram_usage))
        self.logger.debug('%s system_ram_usage: %s', self.system_config,
                          system_ram_usage)
        processed_data['result']['data']['system_ram_usage'] = system_ram_usage
        self._system_ram_usage = system_ram_usage

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
        self.logger.debug('%s system_storage_usage: %s', self.system_config,
                          system_storage_usage)
        processed_data['result']['data']['system_storage_usage'] = \
            system_storage_usage
        self._system_storage_usage = system_storage_usage

        # Add the node network transmit/received bytes total and their per
        # second variants to the processed data
        receive_bytes_total = 0
        transmit_bytes_total = 0
        for i, j in enumerate(self.data['node_network_receive_bytes_total']):
            receive_bytes_total += \
                self.data['node_network_receive_bytes_total'][j]

        for i, j in enumerate(self.data['node_network_transmit_bytes_total']):
            transmit_bytes_total += \
                self.data['node_network_transmit_bytes_total'][j]

        self.logger.debug('%s network_receive_bytes_total: %s, '
                          'network_transmit_bytes_total: %s',
                          self.system_config, receive_bytes_total,
                          transmit_bytes_total)
        processed_data['result']['data']['network_receive_bytes_total'] = \
            receive_bytes_total
        processed_data['result']['data']['network_transmit_bytes_total'] = \
            transmit_bytes_total
        self._network_receive_bytes_total = receive_bytes_total
        self._network_transmit_bytes_total = transmit_bytes_total

        self._data = processed_data

    def _send_data(self) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange='raw_data', routing_key='system', body=self.data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug('Sent data to raw_data exchange')

    def _monitor(self) -> None:
        data_retrieval_exception = Exception()
        try:
            self._get_data()
            self._data_retrieval_failed = False
        except (ReqConnectionError, ReadTimeout):
            self._data_retrieval_failed = True
            data_retrieval_exception = SystemIsDownException(
                self.system_config.system_name)
            self.logger.error('Error when retrieving data from {}'
                              .format(self.system_config.node_exporter_url))
            self.logger.exception(data_retrieval_exception)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError):
            self._data_retrieval_failed = True
            data_retrieval_exception = DataReadingException(
                self.monitor_name, self.system_config.system_name)
            self.logger.error('Error when retrieving data from {}'
                              .format(self.system_config.node_exporter_url))
            self.logger.exception(data_retrieval_exception)
        except MetricNotFoundException as e:
            self._data_retrieval_failed = True
            data_retrieval_exception = e
            self.logger.error('Error when retrieving data from {}'
                              .format(self.system_config.node_exporter_url))
            self.logger.exception(data_retrieval_exception)
        self._process_data(data_retrieval_exception)
        self._send_data()

    def start(self) -> None:
        self._initialize_rabbitmq()
        while True:
            try:
                self._monitor()
            except pika.exceptions.AMQPChannelError:
                # Error would have already been logged by RabbitMQ logger. If
                # there is a channel error, the RabbitMQ interface creates a new
                # channel, therefore perform another monitoring round without
                # sleeping
                continue
            except MessageWasNotDeliveredException as e:
                # Log the fact that the message could not be sent and re-try
                # another monitoring round without sleeping
                self.logger.exception(e)
                continue
            except pika.exceptions.AMQPConnectionError as e:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

            self.logger.info(self.status())

            self.logger.debug('Sleeping for %s seconds.', self.monitor_period)
            time.sleep(self.monitor_period)
