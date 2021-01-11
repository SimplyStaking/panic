import logging
import multiprocessing
import signal
import sys
import time
from types import FrameType
from typing import Tuple

import pika.exceptions

from src.alert_router.alert_router import AlertRouter
from src.alerter.managers.github import GithubAlerterManager
from src.alerter.managers.manager import AlertersManager
from src.alerter.managers.system import SystemAlertersManager
from src.config_manager import ConfigManager
from src.data_store.stores.manager import StoreManager
from src.data_transformers.manager import DataTransformersManager
from src.monitors.managers.github import GitHubMonitorsManager
from src.monitors.managers.manager import MonitorsManager
from src.monitors.managers.system import SystemMonitorsManager
from src.utils import env
from src.utils.exceptions import ConnectionNotInitializedException
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import get_initialisation_error_message, \
    get_reattempting_message, get_stopped_message


def _initialize_logger(log_name: str, log_file_template: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            new_logger = create_logger(
                log_file_template.format(log_name), log_name, env.LOGGING_LEVEL,
                rotating=True)
            break
        except Exception as e:
            # Use a dummy logger in this case because we cannot create the
            # manager's logger.
            dummy_logger = logging.getLogger('DUMMY_LOGGER')
            log_and_print(get_initialisation_error_message(log_name, e),
                          dummy_logger)
            log_and_print(get_reattempting_message(log_name),
                          dummy_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return new_logger


def _initialize_system_alerters_manager() -> SystemAlertersManager:
    manager_name = "System Alerters Manager"

    system_alerters_manager_logger = _initialize_logger(
        manager_name, env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the system alerters manager
    while True:
        try:
            system_alerters_manager = SystemAlertersManager(
                system_alerters_manager_logger, manager_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(manager_name, e),
                          system_alerters_manager_logger)
            log_and_print(get_reattempting_message(manager_name),
                          system_alerters_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again
    return system_alerters_manager


def _initialize_github_alerter_manager() -> GithubAlerterManager:
    manager_name = "GitHub Alerter Manager"

    github_alerter_manager_logger = _initialize_logger(
        manager_name, env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the system alerters manager
    while True:
        try:
            github_alerter_manager = GithubAlerterManager(
                github_alerter_manager_logger, manager_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(manager_name, e),
                          github_alerter_manager_logger)
            log_and_print(get_reattempting_message(manager_name),
                          github_alerter_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return github_alerter_manager


def _initialize_system_monitors_manager() -> SystemMonitorsManager:
    manager_name = 'System Monitors Manager'

    system_monitors_manager_logger = _initialize_logger(
        manager_name, env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the system monitors manager
    while True:
        try:
            system_monitors_manager = SystemMonitorsManager(
                system_monitors_manager_logger, manager_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(manager_name, e),
                          system_monitors_manager_logger)
            log_and_print(get_reattempting_message(manager_name),
                          system_monitors_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return system_monitors_manager


def _initialize_github_monitors_manager() -> GitHubMonitorsManager:
    manager_name = 'GitHub Monitors Manager'

    github_monitors_manager_logger = _initialize_logger(
        manager_name, env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the github monitors manager
    while True:
        try:
            github_monitors_manager = GitHubMonitorsManager(
                github_monitors_manager_logger, manager_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(manager_name, e),
                          github_monitors_manager_logger)
            log_and_print(get_reattempting_message(manager_name),
                          github_monitors_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return github_monitors_manager


def _initialize_data_transformers_manager() -> DataTransformersManager:
    manager_name = 'Data Transformers Manager'

    data_transformers_manager_logger = _initialize_logger(
        manager_name, env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the data transformers manager
    while True:
        try:
            data_transformers_manager = DataTransformersManager(
                data_transformers_manager_logger, manager_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(manager_name, e),
                          data_transformers_manager_logger)
            log_and_print(get_reattempting_message(manager_name),
                          data_transformers_manager_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return data_transformers_manager


def _initialize_alert_router() -> Tuple[AlertRouter, logging.Logger]:
    alert_router_logger = create_logger(
        env.ALERT_ROUTER_LOG_FILE, AlertRouter.__name__, env.LOGGING_LEVEL,
        rotating=True
    )

    rabbit_ip = env.RABBIT_IP

    alert_router = AlertRouter(alert_router_logger, rabbit_ip,
                               env.ENABLE_CONSOLE_ALERTS)
    return alert_router, alert_router_logger


def _initialize_config_manager() -> ConfigManager:
    sleep_period = 10
    config_manager_logger = _initialize_logger(
        ConfigManager.__name__, env.CONFIG_MANAGER_LOG_FILE
    )

    rabbit_ip = env.RABBIT_IP
    while True:
        try:
            cm = ConfigManager(config_manager_logger, '../config', rabbit_ip)
            return cm
        except ConnectionNotInitializedException:
            # This is already logged, we need to try again. This exception
            # should not happen, but if it does the program can't fully start
            # up
            config_manager_logger.info("Trying to set up the configurations "
                                       "manager again in %s seconds.",
                                       sleep_period)
            time.sleep(sleep_period)


def _initialize_data_store_manager() -> StoreManager:
    manager_name = "Data Store Manager"

    data_store_manager_logger = _initialize_logger(
        manager_name, env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the data store manager
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


def run_data_stores_manager() -> None:
    sleep_period = 10
    stores_manager = _initialize_data_store_manager()

    while True:
        try:
            stores_manager.manage()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-initialize just break the loop.
            log_and_print(get_stopped_message(stores_manager),
                          stores_manager.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            stores_manager.disconnect_from_rabbit()
            log_and_print(get_stopped_message(stores_manager),
                          stores_manager.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                stores_manager, sleep_period), stores_manager.logger)
            time.sleep(sleep_period)


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
    github_alerter_manager = _initialize_github_alerter_manager()
    run_alerters_manager(github_alerter_manager)


def run_monitors_manager(manager: MonitorsManager) -> None:
    sleep_period = 10

    while True:
        try:
            manager.manage()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-initialize just break the loop.
            log_and_print(get_stopped_message(manager), manager.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            manager.disconnect_from_rabbit()
            log_and_print(get_stopped_message(manager), manager.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                manager, sleep_period), manager.logger)
            time.sleep(sleep_period)


def run_alerters_manager(manager: AlertersManager) -> None:
    sleep_period = 10

    while True:
        try:
            manager.manage()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-initialize just break the loop.
            log_and_print(get_stopped_message(manager), manager.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            manager.disconnect_from_rabbit()
            log_and_print(get_stopped_message(manager), manager.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                manager, sleep_period), manager.logger)
            time.sleep(sleep_period)


def run_data_transformers_manager() -> None:
    sleep_period = 10
    data_transformers_manager = _initialize_data_transformers_manager()

    while True:
        try:
            data_transformers_manager.manage()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-initialize just break the loop.
            log_and_print(get_stopped_message(data_transformers_manager),
                          data_transformers_manager.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            data_transformers_manager.disconnect_from_rabbit()
            log_and_print(get_stopped_message(data_transformers_manager),
                          data_transformers_manager.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                data_transformers_manager, sleep_period),
                data_transformers_manager.logger)
            time.sleep(sleep_period)


def run_alert_router() -> None:
    sleep_period = 10
    alert_router, alert_router_logger = _initialize_alert_router()

    while True:
        try:
            alert_router.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-initialize just break the loop.
            log_and_print(get_stopped_message(alert_router),
                          alert_router_logger)
        except Exception:
            alert_router.disconnect_from_rabbit()
            log_and_print(get_stopped_message(alert_router),
                          alert_router_logger)
            log_and_print("Restarting {} in {} seconds.".format(
                alert_router, sleep_period), alert_router_logger)
            time.sleep(sleep_period)


def run_config_manager(command_queue: multiprocessing.Queue) -> None:
    config_manager = _initialize_config_manager()
    config_manager.start_watching_config_files()

    # We wait until something is sent to this queue
    command_queue.get()
    config_manager.stop_watching_config_files()


# If termination signals are received, terminate all child process and exit
def on_terminate(signum: int, stack: FrameType) -> None:
    def terminate_and_join_process(process: multiprocessing.Process, name: str):
        log_and_print("Terminating the {}".format(name), dummy_logger)
        process.terminate()
        process.join()

    dummy_logger = logging.getLogger('Dummy')

    log_and_print("The alerter is terminating. All components will be stopped "
                  "gracefully.", dummy_logger)

    terminate_and_join_process(system_monitors_manager_process,
                               "System Monitors Manager")

    terminate_and_join_process(github_monitors_manager_process,
                               "GitHub Monitors Manager")

    terminate_and_join_process(data_transformers_manager_process,
                               "Data Transformers Manager")

    terminate_and_join_process(system_alerters_manager_process,
                               "System Alerters Manager")

    terminate_and_join_process(github_alerter_manager_process,
                               "Github Alerter Manager")

    terminate_and_join_process(data_store_process, "Data Store Process")

    terminate_and_join_process(alert_router_process, "Alert Router")

    log_and_print("PANIC process terminated.", dummy_logger)

    # TODO: Need to add configs manager here when Mark finishes the
    #     : modifications

    log_and_print("The alerting and monitoring process has ended.",
                  dummy_logger)
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

    data_transformers_manager_process = multiprocessing.Process(
        target=run_data_transformers_manager, args=())
    data_transformers_manager_process.start()

    # Start the data store in a separate process
    data_store_process = multiprocessing.Process(target=run_data_stores_manager,
                                                 args=())
    data_store_process.start()

    # Start the alert router in a separate process
    alert_router_process = multiprocessing.Process(target=run_alert_router,
                                                   args=())
    alert_router_process.start()

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
    data_transformers_manager_process.join()
    data_store_process.join()
    alert_router_process.join()

    # To stop the config watcher, we send something in the stop queue, this way
    # We can ensure the watchers and connections are stopped properly
    config_stop_queue.put('STOP')
    config_manager_runner_process.join()

    print("The alerting and monitoring process has ended.")
    sys.stdout.flush()

    # TODO: Make sure that all queues and configs are declared before hand in
    #     : the run alerter before start sending configs, as otherwise configs
    #     : manager would not be able to send configs on start-up. Therefore
    #     : start the config manager last. Similarly, components must be started
    #     : from left to right according to the design (to avoid message not
    #     : delivered exceptions). Also, to fully solve these problems, we
    #     : should perform checks in the run alerter to see if a queue/exchange
    #     : has been created
