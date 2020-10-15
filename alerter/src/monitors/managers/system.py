import logging
import json
import os
import time
from typing import Dict
import pika
import pika.exceptions

from alerter.src.configs.system import SystemConfig
from alerter.src.moniterables.system import System
from alerter.src.monitors.managers.manager import MonitorManager
from alerter.src.monitors.system import SystemMonitor
from alerter.src.utils.logging import create_logger, log_and_print


class SystemMonitorsManager(MonitorManager):

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)
        # TODO: Must have a process [id, name] and chain general configs field
        self._systems_configs = {}
        self._processes_systems_config = {} # TODO: create getter for this

    @property
    def systems_configs(self) -> Dict[SystemConfig]:
        return self._systems_configs

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
        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _initialize_system_monitor(self, system: System) -> SystemMonitor:
        # Monitor name based on system
        monitor_name = 'System monitor ({})'.format(system.name)

        # Try initializing a monitor until successful
        while True:
            try:
                system_monitor_logger = create_logger(
                    os.environ["SYSTEM_MONITOR_LOG_FILE_TEMPLATE"], system.name,
                    os.environ["LOGGING_LEVEL"], rotating=True)
                system_monitor = SystemMonitor(monitor_name, system,
                                               system_monitor_logger,
                                               self.redis)
                log_and_print("Successfully initialized {}"
                              .format(monitor_name), self.logger)
                break
            except Exception as e:
                msg = '!!! Error when initialising {}: {} !!!'.format(
                    monitor_name, e)
                log_and_print(msg, self.logger)
                time.sleep(10)  # sleep 10 seconds before trying again

        return system_monitor

    def _start_system_monitor(self, system: System) -> None:
        system_monitor = self._initialize_system_monitor(system)

        while True:
            try:
                log_and_print('{} started.'.format(system_monitor), self.logger)
                system_monitor.start()
            except pika.exceptions.AMQPConnectionError as e:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                log_and_print('{} stopped.'.format(system_monitor), self.logger)
            except Exception as e:
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