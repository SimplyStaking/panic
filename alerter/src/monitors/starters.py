import logging
import time
from typing import TypeVar, Type, Union

import pika.exceptions

from src.configs.repo import RepoConfig
from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.github import GitHubMonitor
from src.monitors.monitor import Monitor
from src.monitors.system import SystemMonitor
from src.utils import env
from src.utils.constants import (RE_INITIALISE_SLEEPING_PERIOD,
                                 RESTART_SLEEPING_PERIOD,
                                 SYSTEM_MONITOR_NAME_TEMPLATE,
                                 GITHUB_MONITOR_NAME_TEMPLATE)
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import (get_initialisation_error_message,
                                get_stopped_message)

# Restricts the generic to Monitor or subclasses
T = TypeVar('T', bound=Monitor)


def _initialise_monitor_logger(monitor_display_name: str,
                               monitor_module_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            monitor_logger = create_logger(
                env.MONITORS_LOG_FILE_TEMPLATE.format(monitor_display_name),
                monitor_module_name, env.LOGGING_LEVEL, True)
            break
        except Exception as e:
            msg = get_initialisation_error_message(monitor_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # monitor's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return monitor_logger


def _initialise_monitor(monitor_type: Type[T], monitor_display_name: str,
                        monitoring_period: int,
                        config: Union[SystemConfig, RepoConfig]) -> T:
    monitor_logger = _initialise_monitor_logger(monitor_display_name,
                                                monitor_type.__name__)

    # Try initialising the monitor until successful
    while True:
        try:
            rabbitmq = RabbitMQApi(
                logger=monitor_logger.getChild(RabbitMQApi.__name__),
                host=env.RABBIT_IP)
            monitor = monitor_type(monitor_display_name, config, monitor_logger,
                                   monitoring_period, rabbitmq)
            log_and_print("Successfully initialized {}".format(
                monitor_display_name), monitor_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(monitor_display_name, e)
            log_and_print(msg, monitor_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return monitor


def start_system_monitor(system_config: SystemConfig) -> None:
    # Monitor display name based on system
    monitor_display_name = SYSTEM_MONITOR_NAME_TEMPLATE.format(
        system_config.system_name)
    system_monitor = _initialise_monitor(SystemMonitor, monitor_display_name,
                                         env.SYSTEM_MONITOR_PERIOD_SECONDS,
                                         system_config)
    start_monitor(system_monitor)


def start_github_monitor(repo_config: RepoConfig) -> None:
    # Monitor display name based on repo name. The '/' are replaced with spaces,
    # and the last space is removed.
    monitor_display_name = GITHUB_MONITOR_NAME_TEMPLATE.format(
        repo_config.repo_name.replace('/', ' ')[:-1])
    github_monitor = _initialise_monitor(GitHubMonitor, monitor_display_name,
                                         env.GITHUB_MONITOR_PERIOD_SECONDS,
                                         repo_config)
    start_monitor(github_monitor)


def start_monitor(monitor: Monitor) -> None:
    while True:
        try:
            log_and_print("{} started.".format(monitor), monitor.logger)
            monitor.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            log_and_print(get_stopped_message(monitor), monitor.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            monitor.disconnect_from_rabbit()
            log_and_print(get_stopped_message(monitor), monitor.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                monitor, RESTART_SLEEPING_PERIOD), monitor.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)
