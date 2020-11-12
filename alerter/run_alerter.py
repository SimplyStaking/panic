import logging
import multiprocessing
import signal
import sys
import os
import time
import pika.exceptions

from types import FrameType
from src.config_manager import ConfigManager
from src.monitors.managers.github import GitHubMonitorsManager
from src.monitors.managers.manager import MonitorsManager
from src.monitors.managers.system import SystemMonitorsManager
from src.alerter.managers.system import SystemAlertersManager
from src.alerter.managers.github import GithubAlerterManager
from src.alerter.managers.manager import AlertersManager
from src.data_store.stores.manager import StoreManager
from src.utils.exceptions import ConnectionNotInitializedException
from src.utils.logging import create_logger, log_and_print


def _initialize_logger(log_name: str, os_env_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            new_logger = create_logger(
                os.environ[os_env_name].format(log_name), log_name,
                os.environ["LOGGING_LEVEL"], rotating=True
            )
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(log_name, e)
            # Use a dummy logger in this case because we cannot create the
            # managers's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            log_and_print('Re-attempting the initialization procedure',
                          logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return new_logger


def _initialize_system_alerters_manager() -> SystemAlertersManager:
    manager_name = "System Alerters Manager"

    system_alerters_manager_logger = _initialize_logger(
        manager_name,
        "MANAGERS_LOG_FILE_TEMPLATE"
    )

    # Attempt to initialize the system alerters manager
    while True:
        try:
            system_alerters_manager = SystemAlertersManager(
                system_alerters_manager_logger, manager_name)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            log_and_print(msg, system_alerters_manager_logger)
            log_and_print('Re-attempting the initialization procedure',
                          system_alerters_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return system_alerters_manager


def _initialize_github_alerter_manager() -> GithubAlerterManager:
    manager_name = "Github Alerter Manager"

    github_alerter_manager_logger = _initialize_logger(
        manager_name,
        "MANAGERS_LOG_FILE_TEMPLATE"
    )

    # Attempt to initialize the system alerters manager
    while True:
        try:
            github_alerter_manager = GithubAlerterManager(
                github_alerter_manager_logger, manager_name)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            log_and_print(msg, github_alerter_manager_logger)
            log_and_print('Re-attempting the initialization procedure',
                          github_alerter_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return github_alerter_manager


def _initialize_system_monitors_manager() -> SystemMonitorsManager:
    manager_name = "System Monitors Manager"

    system_monitors_manager_logger = _initialize_logger(
        manager_name,
        "MANAGERS_LOG_FILE_TEMPLATE"
    )

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

    github_monitors_manager_logger = _initialize_logger(
        manager_name,
        "MANAGERS_LOG_FILE_TEMPLATE"
    )

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


def _initialize_config_manager() -> ConfigManager:
    config_manager_logger = _initialize_logger(
        ConfigManager.__name__,
        "CONFIG_MANAGER_LOG_FILE"
    )

    rabbit_ip = os.environ["RABBIT_IP"]
    while True:
        try:
            cm = ConfigManager(config_manager_logger, "./config", rabbit_ip)
            return cm
        except ConnectionNotInitializedException:
            # This is already logged, we need to try again. This exception
            # should not happen, but if it does the program can't fully start
            # up
            config_manager_logger.info("Trying to set up the configurations "
                                       "manager again")
            continue


def _initialize_data_store_manager() -> StoreManager:
    manager_name = "Data Store Manager"

    data_store_manager_logger = _initialize_logger(
        manager_name,
        "DATA_STORE_LOG_FILE_TEMPLATE"
    )

    # Attempt to initialize the github monitors manager
    while True:
        try:
            data_store_manager = StoreManager(
                data_store_manager_logger, manager_name)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            log_and_print(msg, data_store_manager_logger)
            log_and_print('Re-attempting the initialization procedure',
                          data_store_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return data_store_manager


def run_data_store() -> None:
    store_manager = _initialize_data_store_manager()
    store_manager.start_store_manager()


def run_system_monitors_manager() -> None:
    system_monitors_manager = _initialize_system_monitors_manager()
    run_monitors_manager(system_monitors_manager)


def run_github_monitors_manager() -> None:
    github_monitors_manager = _initialize_github_monitors_manager()
    run_monitors_manager(github_monitors_manager)


def run_system_alerters_manager() -> None:
    system_alerters_manager = _initialize_system_alerters_manager()
    run_alerters_manager(system_alerters_manager)


def run_github_alerters_manager() -> None:
    manager = _initialize_github_alerter_manager()
    while True:
        try:
            manager.start_github_alerter_manager()
        except pika.exceptions.AMQPConnectionError:
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print('{} stopped.'.format(manager), manager.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            manager.rabbitmq.disconnect_till_successful()
            log_and_print('{} stopped.'.format(manager), manager.logger)


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


def run_alerters_manager(manager: AlertersManager) -> None:
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


def run_config_manager(command_queue: multiprocessing.Queue) -> None:
    config_manager = _initialize_config_manager()
    config_manager.start_watching_config_files()

    # We wait until something is sent to this queue
    command_queue.get()
    config_manager.stop_watching_config_files()


# If termination signals are received, terminate all child process and exit
def on_terminate(signum: int, stack: FrameType) -> None:
    dummy_logger = logging.getLogger('Dummy')

    log_and_print('PANIC is terminating. All components will be stopped '
                  'gracefully.', dummy_logger)

    log_and_print('Terminating the System Monitors Manager', dummy_logger)
    system_monitors_manager_process.terminate()
    system_monitors_manager_process.join()

    log_and_print('Terminating the GitHub Monitors Manager', dummy_logger)
    github_monitors_manager_process.terminate()
    github_monitors_manager_process.join()

    log_and_print('Terminating the System Alerters Manager', dummy_logger)
    system_alerters_manager_process.terminate()
    system_alerters_manager_process.join()

    log_and_print('Terminating the Github Alerter Manager', dummy_logger)
    github_alerter_manager_process.terminate()
    github_alerter_manager_process.join()

    log_and_print('Terminating the Data Store Process', dummy_logger)
    data_store_process.terminate()
    data_store_process.join()

    log_and_print('PANIC process terminated.', dummy_logger)
    sys.exit()


if __name__ == '__main__':
    # Start the managers in a separate process
    system_monitors_manager_process = multiprocessing.Process(
        target=run_system_monitors_manager, args=())
    system_monitors_manager_process.start()

    github_monitors_manager_process = multiprocessing.Process(
        target=run_github_monitors_manager, args=())
    github_monitors_manager_process.start()

    # Start the alerters in a separate process
    system_alerters_manager_process = multiprocessing.Process(
        target=run_system_alerters_manager, args=())
    system_alerters_manager_process.start()

    github_alerter_manager_process = multiprocessing.Process(
        target=run_github_alerters_manager, args=())
    github_alerter_manager_process.start()

    # Start the data store in a separate process
    data_store_process = multiprocessing.Process(target=run_data_store,
                                                 args=[])
    data_store_process.start()

    # Config manager must be the last to start since it immediately begins by
    # sending the configs. That being said, all previous processes need to wait
    # for the config manager too.
    config_stop_queue = multiprocessing.Queue()
    config_manager_runner_process = multiprocessing.Process(
        target=run_config_manager, args=(config_stop_queue,)
    )
    config_manager_runner_process.start()

    signal.signal(signal.SIGTERM, on_terminate)
    signal.signal(signal.SIGINT, on_terminate)
    signal.signal(signal.SIGHUP, on_terminate)

    # If we don't wait for the processes to terminate the root process will
    # exit
    github_monitors_manager_process.join()
    system_monitors_manager_process.join()
    system_alerters_manager_process.join()
    github_alerter_manager_process.join()
    data_store_process.join()

    # To stop the config watcher, we send something in the stop queue, this way
    # We can ensure the watchers and connections are stopped properly
    config_stop_queue.put("STOP")
    config_manager_runner_process.join()

    print('The alerter is stopping.')
    sys.stdout.flush()

# TODO: Make sure that all queues and configs are declared before hand in the
#     : run alerter before start sending configs, as otherwise configs manager
#     : would not be able to send configs on start-up
