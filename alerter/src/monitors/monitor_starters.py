import time

import pika.exceptions

from alerter.src.configs.system import SystemConfig
from alerter.src.monitors.system import SystemMonitor
from alerter.src.utils.logging import create_logger, log_and_print


def _initialize_system_monitor(system_config: SystemConfig) -> SystemMonitor:
    # Monitor name based on system
    monitor_name = 'System monitor ({})'.format(system_config.system_name)

    # Try initializing a monitor until successful
    while True:
        try:
            SYSTEM_MONITOR_LOG_FILE_TEMPLATE = 'logs/monitors/{}.log'
            LOGGING_LEVEL = 'INFO'
            SYSTEM_MONITOR_PERIOD_SECONDS = '60'
            system_monitor_logger = create_logger(
                SYSTEM_MONITOR_LOG_FILE_TEMPLATE.format(monitor_name),
                monitor_name,
                LOGGING_LEVEL, rotating=True)
            system_monitor = SystemMonitor(
                monitor_name, system_config, system_monitor_logger,
                int(SYSTEM_MONITOR_PERIOD_SECONDS))
            log_and_print("Successfully initialized {}".format(monitor_name),
                          system_monitor.logger)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!'.format(
                monitor_name, e)
            log_and_print(msg, system_monitor.logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return system_monitor


def start_system_monitor(system_config: SystemConfig) -> None:
    system_monitor = _initialize_system_monitor(system_config)

    while True:
        try:
            log_and_print('{} started.'.format(system_monitor),
                          system_monitor.logger)
            system_monitor.start()
        except pika.exceptions.AMQPConnectionError:
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print('{} stopped.'.format(system_monitor),
                          system_monitor.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            system_monitor.rabbitmq.disconnect_till_successful()
            log_and_print('{} stopped.'.format(system_monitor),
                          system_monitor.logger)
