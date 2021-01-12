import logging
import time

import pika.exceptions

from src.configs.repo import RepoConfig
from src.configs.system import SystemConfig
from src.monitors.github import GitHubMonitor
from src.monitors.monitor import Monitor
from src.monitors.system import SystemMonitor
from src.utils import env
from src.utils.constants import RE_INITIALIZE_SLEEPING_PERIOD, \
    RESTART_SLEEPING_PERIOD, SYSTEM_MONITOR_NAME_TEMPLATE, \
    GITHUB_MONITOR_NAME_TEMPLATE
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import get_initialisation_error_message, \
    get_stopped_message


def _initialize_monitor_logger(monitor_display_name: str,
                               monitor_module_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            monitor_logger = create_logger(
                env.MONITORS_LOG_FILE_TEMPLATE.format(monitor_display_name),
                monitor_module_name, env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = get_initialisation_error_message(monitor_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # monitor's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return monitor_logger


def _initialize_system_monitor(system_config: SystemConfig) -> SystemMonitor:
    # Monitor display name based on system
    monitor_display_name = SYSTEM_MONITOR_NAME_TEMPLATE.format(
        system_config.system_name)

    system_monitor_logger = _initialize_monitor_logger(monitor_display_name,
                                                       SystemMonitor.__name__)

    # Try initializing a monitor until successful
    while True:
        try:
            system_monitor = SystemMonitor(
                monitor_display_name, system_config, system_monitor_logger,
                int(env.SYSTEM_MONITOR_PERIOD_SECONDS)
            )
            log_and_print("Successfully initialized {}".format(
                monitor_display_name), system_monitor_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(monitor_display_name, e)
            log_and_print(msg, system_monitor_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return system_monitor


def _initialize_github_monitor(repo_config: RepoConfig) -> GitHubMonitor:
    # Monitor display name based on repo name. The '/' are replaced with spaces,
    # and the last space is removed.
    monitor_display_name = GITHUB_MONITOR_NAME_TEMPLATE.format(
        repo_config.repo_name.replace('/', ' ')[:-1])

    github_monitor_logger = _initialize_monitor_logger(monitor_display_name,
                                                       GitHubMonitor.__name__)

    # Try initializing a monitor until successful
    while True:
        try:
            github_monitor = GitHubMonitor(
                monitor_display_name, repo_config, github_monitor_logger,
                int(env.GITHUB_MONITOR_PERIOD_SECONDS)
            )
            log_and_print("Successfully initialized {}".format(
                monitor_display_name), github_monitor_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(monitor_display_name, e)
            log_and_print(msg, github_monitor_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return github_monitor


def start_system_monitor(system_config: SystemConfig) -> None:
    system_monitor = _initialize_system_monitor(system_config)
    start_monitor(system_monitor)


def start_github_monitor(repo_config: RepoConfig) -> None:
    github_monitor = _initialize_github_monitor(repo_config)
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
