import multiprocessing
import logging
import time
import os

import pika.exceptions

from alerter.src.monitors.managers.github import GitHubMonitorsManager
from alerter.src.monitors.managers.manager import MonitorsManager
from alerter.src.monitors.managers.system import SystemMonitorsManager
from alerter.src.utils.logging import create_logger, log_and_print


def _initialize_monitors_manager_logger(manager_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            monitors_manager_logger = create_logger(
                'logs/managers/{}.log'.format(manager_name),
                # os.environ["MANAGERS_LOG_FILE_TEMPLATE"].format(manager_name),
                manager_name,
                # os.environ["LOGGING_LEVEL"],
                "INFO",
                rotating=True)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            # Use a dummy logger in this case because we cannot create the
            # managers's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            log_and_print('Re-attempting the initialization procedure',
                          logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return monitors_manager_logger


def _initialize_system_monitors_manager() -> SystemMonitorsManager:
    manager_name = "System Monitors Manager"

    system_monitors_manager_logger = _initialize_monitors_manager_logger(
        manager_name)

    # Attempt to initialize the system monitors manager
    while True:
        try:
            system_monitors_manager = SystemMonitorsManager(
                system_monitors_manager_logger, manager_name)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            log_and_print(msg, system_monitors_manager_logger)
            log_and_print('Re-attempting the initialization procedure',
                          system_monitors_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return system_monitors_manager


def _initialize_github_monitors_manager() -> GitHubMonitorsManager:
    manager_name = "GitHub Monitors Manager"

    github_monitors_manager_logger = _initialize_monitors_manager_logger(
        manager_name)

    # Attempt to initialize the github monitors manager
    while True:
        try:
            github_monitors_manager = GitHubMonitorsManager(
                github_monitors_manager_logger, manager_name)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            log_and_print(msg, github_monitors_manager_logger)
            log_and_print('Re-attempting the initialization procedure',
                          github_monitors_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return github_monitors_manager


def run_system_monitors_manager() -> None:
    system_monitors_manager = _initialize_system_monitors_manager()
    run_monitors_manager(system_monitors_manager)


def run_github_monitors_manager() -> None:
    github_monitors_manager = _initialize_github_monitors_manager()
    run_monitors_manager(github_monitors_manager)


def run_monitors_manager(manager: MonitorsManager) -> None:
    while True:
        try:
            manager.manage()
        except pika.exceptions.AMQPConnectionError:
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print('{} stopped.'.format(manager), manager.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            manager.rabbitmq.disconnect_till_successful()
            log_and_print('{} stopped.'.format(manager), manager.logger)


if __name__ == '__main__':
    # # Start the managers in a separate process
    # system_monitors_manager_process = multiprocessing.Process(
    #     target=run_system_monitors_manager, args=[])
    # system_monitors_manager_process.start()
    #
    # # If we don't wait for the processes to terminate the root process will exit
    # system_monitors_manager_process.join()

    # Start the managers in a separate process
    github_monitors_manager_process = multiprocessing.Process(
        target=run_github_monitors_manager, args=[])
    github_monitors_manager_process.start()

    # If we don't wait for the processes to terminate the root process will exit
    github_monitors_manager_process.join()

    print('The alerter is stopping.')

# TODO: Make sure that all queues and configs are declared before hand in the
#     : run alerter before start sending configs, as otherwise configs manager
#     : would not be able to send configs on start-up

# TODO: Test Github monitor process creation/deletion
# TODO: Test GitHub monitor manager exceptions
# TODO: Test GitHub monitor with system monitor on docker and source
# TODO: Add disk/io usage metrics

# TODO: Change env variables in run alerter, both managers, both specific
#     : managers, monitor, both specific monitors and monitor starters