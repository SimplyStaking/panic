import json
import logging
import multiprocessing
import os
import time
from typing import Dict

import pika
import pika.exceptions

from alerter.src.configs.system import SystemConfig
from alerter.src.monitors.managers.manager import MonitorManager
from alerter.src.monitors.system import SystemMonitor
from alerter.src.utils.configs import get_newly_added_configs, \
    get_modified_configs
from alerter.src.utils.logging import create_logger, log_and_print


class SystemMonitorsManager(MonitorManager):

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)
        self._general_systems_configs = {}
        self._chain_systems_configs = {}

    @property
    def general_systems_configs(self) -> Dict:
        return self._general_systems_configs

    @property
    def chain_systems_configs(self) -> Dict:
        return self._chain_systems_configs

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare('config', 'topic', False, True,
                                       False, False)
        self.rabbitmq.queue_declare('configs_queue', False, True, False, False)
        self.rabbitmq.queue_bind('configs_queue', 'config',
                                 'chains.*.*.systems_config.ini')
        self.rabbitmq.queue_bind('configs_queue', 'config',
                                 'general.systems_config.ini')

    def _listen_for_configs(self) -> None:
        self.rabbitmq.basic_consume('configs_queue', self._process_configs,
                                    False, False, None)
        self.rabbitmq.start_consuming()

    def _process_configs(
            self, ch, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        if method.routing_key == 'general.systems_config.ini':
            current_configs = self.general_systems_configs
            self._general_systems_configs = sent_configs
        else:
            current_configs = self.chain_systems_configs
            self._chain_systems_configs = sent_configs

        new_configs = get_newly_added_configs(sent_configs, current_configs)
        for config in new_configs:
            system_id = config['id']
            parent_id = config['parent_id']
            system_name = config['name']
            node_exporter_url = config['exporter_url']
            monitor_system = config['monitor_system']
            system_config = SystemConfig(system_id, parent_id, system_name,
                                         monitor_system, node_exporter_url)
            process = multiprocessing.Process(target=self._start_system_monitor,
                                              args=[system_config])
            # Kill children if parent is killed (Not with SIGKILL -9)
            # TODO: Need to test what happens if we stop service using systemctl
            process.daemon = True  # TODO: May need to check if to remove this
            # since we must manually kill as well
            process.start()
            self._config_process_dict[system_id] = process

        modified_configs = get_modified_configs(sent_configs, current_configs)
        for config in modified_configs:
            system_id = config['id']
            parent_id = config['parent_id']
            system_name = config['name']
            node_exporter_url = config['exporter_url']
            monitor_system = config['monitor_system']
            system_config = SystemConfig(system_id, parent_id, system_name,
                                         monitor_system, node_exporter_url)
            # TODO: Need to kill previous process, make sure to close rabbit
            #     : first, then terminate, then join. To close rabbitmq we may
            #     : require handling SIGTERM signals (see website). For
            #     : consumers we must also stop consuming rather than
            #     rabbit.close only
            process = multiprocessing.Process(target=self._start_system_monitor,
                                              args=[system_config])
            # Kill children if parent is killed (Not with SIGKILL -9)
            # TODO: Need to test what happens if we stop service using systemctl
            process.daemon = True  # TODO: May need to check if to remove this
            # since we must manually kill as well
            process.start()
            self._config_process_dict[system_id] = process

        # removed_configs = get_removed_configs(sent_configs,
        #                                       self.systems_configs)
        # TODO: When you close a process make sure to close all connections with
        #     : Rabbit, then terminate, then join. Also remove process from
        #     : config_process_dict

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _initialize_system_monitor(self, system_config: SystemConfig) \
            -> SystemMonitor:
        # Monitor name based on system
        monitor_name = 'System monitor ({})'.format(system_config.system_name)

        # Try initializing a monitor until successful
        while True:
            try:
                system_monitor_logger = create_logger(
                    os.environ["SYSTEM_MONITOR_LOG_FILE_TEMPLATE"],
                    system_config.system_name,
                    os.environ["LOGGING_LEVEL"], rotating=True)
                system_monitor = SystemMonitor(
                    monitor_name, system_config, system_monitor_logger,
                    os.environ["SYSTEM_MONITOR_PERIOD_SECONDS"])
                log_and_print("Successfully initialized {}"
                              .format(monitor_name), self.logger)
                break
            except Exception as e:
                msg = '!!! Error when initialising {}: {} !!!'.format(
                    monitor_name, e)
                log_and_print(msg, self.logger)
                time.sleep(10)  # sleep 10 seconds before trying again

        return system_monitor

    def _start_system_monitor(self, system_config: SystemConfig) -> None:
        system_monitor = self._initialize_system_monitor(system_config)

        while True:
            try:
                log_and_print('{} started.'.format(system_monitor), self.logger)
                system_monitor.start()
            except pika.exceptions.AMQPConnectionError:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                log_and_print('{} stopped.'.format(system_monitor), self.logger)
            except Exception:
                # Close the connection with RabbitMQ if we have an unexpected
                # exception, and start again
                system_monitor.close_rabbitmq_connection()
                log_and_print('{} stopped.'.format(system_monitor), self.logger)

    def manage(self) -> None:
        pass

# TODO: On the outside must handle when the manager stops, stop rabbit
#     : connectionS in that case and all individual monitors

# TODO: Must modify monitors creator, and pass monitoring period as a shared
#     : variable

# TODO: Error handling as we did for monitors
# TODO: Add more logging in manager and _rabbitmq_initialization function of
#     : the system monitor
# TODO: Must handle zombie processes if parent process is killed
