import logging
import os
import time

import pika.exceptions

from alerter.src.configs.repo import RepoConfig
from alerter.src.configs.system import SystemConfig
from alerter.src.monitors.github import GitHubMonitor
from alerter.src.monitors.monitor import Monitor
from alerter.src.monitors.system import SystemMonitor
from alerter.src.utils.logging import create_logger, log_and_print


def _initialize_monitor_logger(monitor_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            monitor_logger = create_logger(
                os.environ["MONITORS_LOG_FILE_TEMPLATE"].format(monitor_name),
                monitor_name, os.environ["LOGGING_LEVEL"], rotating=True)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!'.format(
                monitor_name, e)
            # Use a dummy logger in this case because we cannot create the
            # monitor's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return monitor_logger


def _initialize_system_monitor(system_config: SystemConfig) -> SystemMonitor:
    # Monitor name based on system
    monitor_name = 'System monitor ({})'.format(system_config.system_name)

    system_monitor_logger = _initialize_monitor_logger(monitor_name)

    # Try initializing a monitor until successful
    while True:
        try:
            system_monitor = SystemMonitor(
                monitor_name, system_config, system_monitor_logger,
                int(os.environ["SYSTEM_MONITOR_PERIOD_SECONDS"]))
            log_and_print("Successfully initialized {}".format(monitor_name),
                          system_monitor_logger)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!'.format(
                monitor_name, e)
            log_and_print(msg, system_monitor_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return system_monitor


def _initialize_github_monitor(repo_config: RepoConfig) -> GitHubMonitor:
    # Monitor name based on repo name. The '/' are replaced with spaces, and the
    # last space is removed.
    monitor_name = 'GitHub monitor ({})'.format(
        repo_config.repo_name.replace('/', ' ')[:-1])

    github_monitor_logger = _initialize_monitor_logger(monitor_name)

    # Try initializing a monitor until successful
    while True:
        try:
            github_monitor = GitHubMonitor(
                monitor_name, repo_config, github_monitor_logger,
                int(os.environ["GITHUB_MONITOR_PERIOD_SECONDS"]))
            log_and_print("Successfully initialized {}".format(monitor_name),
                          github_monitor_logger)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!'.format(
                monitor_name, e)
            log_and_print(msg, github_monitor_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

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
            log_and_print('{} started.'.format(monitor), monitor.logger)
            monitor.start()
        except pika.exceptions.AMQPConnectionError:
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print('{} stopped.'.format(monitor), monitor.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            monitor.rabbitmq.disconnect_till_successful()
            log_and_print('{} stopped.'.format(monitor), monitor.logger)
