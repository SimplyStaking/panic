import logging
import multiprocessing
import os
import time

import pika.exceptions

from src.config_manager import ConfigManager
from src.data_transformers.manager import DataTransformersManager
from src.monitors.managers.github import GitHubMonitorsManager
from src.monitors.managers.manager import MonitorsManager
from src.monitors.managers.system import SystemMonitorsManager
from src.data_store.stores.manager import StoreManager
from src.utils.exceptions import ConnectionNotInitializedException
from src.utils.logging import create_logger, log_and_print


def _initialize_data_store_logger(data_store_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            data_store_logger = create_logger(
                os.environ["DATA_STORE_LOG_FILE_TEMPLATE"].format(
                    data_store_name),
                data_store_name, os.environ["LOGGING_LEVEL"], rotating=True)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(data_store_name, e)
            # Use a dummy logger in this case because we cannot create the
            # managers's logger.
            dummy_logger = logging.getLogger('DUMMY_LOGGER')
            log_and_print(msg, dummy_logger)
            log_and_print('Re-attempting initialization procedure of {}'
                          .format(data_store_name), dummy_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return data_store_logger


def _initialize_manager_logger(manager_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            manager_logger = create_logger(
                # os.environ["MANAGERS_LOG_FILE_TEMPLATE"].format(manager_name),
                'logs/managers/{}.log'.format(manager_name),
                manager_name,
                # os.environ["LOGGING_LEVEL"],
                'INFO',
                rotating=True)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            # Use a dummy logger in this case because we cannot create the
            # managers's logger.
            dummy_logger = logging.getLogger('DUMMY_LOGGER')
            log_and_print(msg, dummy_logger)
            log_and_print('Re-attempting initialization procedure of {}'
                          .format(manager_name), dummy_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return manager_logger


def _initialize_system_monitors_manager() -> SystemMonitorsManager:
    manager_name = "System Monitors Manager"

    system_monitors_manager_logger = _initialize_manager_logger(manager_name)

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
            log_and_print('Re-attempting initialization procedure of {}'
                          .format(manager_name),
                          system_monitors_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return system_monitors_manager


def _initialize_github_monitors_manager() -> GitHubMonitorsManager:
    manager_name = "GitHub Monitors Manager"

    github_monitors_manager_logger = _initialize_manager_logger(manager_name)

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
            log_and_print('Re-attempting initialization procedure of {}'
                          .format(manager_name),
                          github_monitors_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return github_monitors_manager


def _initialize_data_transformers_manager() -> DataTransformersManager:
    manager_name = "Data Transformers Manager"

    data_transformers_manager_logger = _initialize_manager_logger(manager_name)

    # Attempt to initialize the data transformers manager
    while True:
        try:
            data_transformers_manager = DataTransformersManager(
                data_transformers_manager_logger, manager_name)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(manager_name, e)
            log_and_print(msg, data_transformers_manager_logger)
            log_and_print('Re-attempting initialization procedure of {}'
                          .format(manager_name),
                          data_transformers_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return data_transformers_manager


def _initialize_config_manager() -> ConfigManager:
    config_manager_logger = create_logger(
        os.environ["CONFIG_MANAGER_LOG_FILE"], ConfigManager.__name__,
        os.environ["LOGGING_LEVEL"], rotating=True
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


def run_data_store() -> None:
    store_logger = _initialize_data_store_logger('data_store')

    store_manager = StoreManager(store_logger)
    store_manager.start_store_manager()


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


def run_data_transformers_manager() -> None:
    data_transformers_manager = _initialize_data_transformers_manager()

    while True:
        try:
            data_transformers_manager.manage()
        except Exception as e:
            data_transformers_manager.logger.exception(e)
            log_and_print('{} stopped.'.format(data_transformers_manager),
                          data_transformers_manager.logger)


def run_config_manager(command_queue: multiprocessing.Queue) -> None:
    config_manager = _initialize_config_manager()
    config_manager.start_watching_config_files()

    # We wait until something is sent to this queue
    command_queue.get()
    config_manager.stop_watching_config_files()


if __name__ == '__main__':
    # Start the managers in a separate process
    system_monitors_manager_process = multiprocessing.Process(
        target=run_system_monitors_manager, args=())
    system_monitors_manager_process.start()

    github_monitors_manager_process = multiprocessing.Process(
        target=run_github_monitors_manager, args=())
    github_monitors_manager_process.start()

    data_transformers_manager_process = multiprocessing.Process(
        target=run_data_transformers_manager, args=())
    data_transformers_manager_process.start()

    # # Start the data store in a separate process
    # data_store_process = multiprocessing.Process(target=run_data_store, args=())
    # data_store_process.start()
    #
    # # Config manager must be the last to start since it immediately begins by
    # # sending the configs. That being said, all previous processes need to wait
    # # for the config manager too.
    # config_stop_queue = multiprocessing.Queue()
    # config_manager_runner_process = multiprocessing.Process(
    #     target=run_config_manager, args=(config_stop_queue,)
    # )
    # config_manager_runner_process.start()

    # If we don't wait for the processes to terminate the root process will exit
    github_monitors_manager_process.join()
    system_monitors_manager_process.join()
    # data_store_process.join()

    # To stop the config watcher, we send something in the stop queue, this way
    # We can ensure the watchers and connections are stopped properly
    # config_stop_queue.put("STOP")
    # config_manager_runner_process.join()

    print('The alerter is stopping.')

# TODO: Make sure that all queues and configs are declared before hand in the
#     : run alerter before start sending configs, as otherwise configs manager
#     : would not be able to send configs on start-up. Therefore start the
#     : config manager last. Similarly, components must be started from left
#     : to right accoriding to the design (to avoid message not delivered
#     : exceptions). Also, to fully solve these problems, we should perform
#     : checks in the run alerter to see if a queue/exchange has been created

# TODO: Test system data transformer integrated with the data
#     : store, configs manager and monitor. Test both from source and docker.
