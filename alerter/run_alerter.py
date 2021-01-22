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
from src.channels_manager.manager import ChannelsManager
from src.config_manager import ConfigsManager
from src.data_store.stores.manager import StoreManager
from src.data_transformers.manager import DataTransformersManager
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.github import GitHubMonitorsManager
from src.monitors.managers.manager import MonitorsManager
from src.monitors.managers.system import SystemMonitorsManager
from src.utils import env
from src.utils.constants import (ALERT_ROUTER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                 GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 RE_INITIALIZE_SLEEPING_PERIOD,
                                 RESTART_SLEEPING_PERIOD,
                                 SYSTEM_ALERTERS_MANAGER_NAME,
                                 GITHUB_ALERTER_MANAGER_NAME,
                                 SYSTEM_MONITORS_MANAGER_NAME,
                                 GITHUB_MONITORS_MANAGER_NAME,
                                 DATA_TRANSFORMERS_MANAGER_NAME,
                                 CHANNELS_MANAGER_NAME, ALERT_ROUTER_NAME,
                                 CONFIGS_MANAGER_NAME, DATA_STORE_MANAGER_NAME)
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import (get_initialisation_error_message,
                                get_reattempting_message, get_stopped_message)


def _initialize_logger(component_display_name: str, component_module_name: str,
                       log_file_template: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            new_logger = create_logger(log_file_template.format(
                component_display_name), component_module_name,
                env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            # Use a dummy logger in this case because we cannot create the
            # manager's logger.
            dummy_logger = logging.getLogger('DUMMY_LOGGER')
            log_and_print(get_initialisation_error_message(
                component_display_name, e), dummy_logger)
            log_and_print(get_reattempting_message(component_display_name),
                          dummy_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return new_logger


def _initialize_system_alerters_manager() -> SystemAlertersManager:
    manager_display_name = SYSTEM_ALERTERS_MANAGER_NAME

    system_alerters_manager_logger = _initialize_logger(
        manager_display_name, SystemAlertersManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the system alerters manager
    while True:
        try:
            system_alerters_manager = SystemAlertersManager(
                system_alerters_manager_logger, manager_display_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(
                manager_display_name, e), system_alerters_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          system_alerters_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)
    return system_alerters_manager


def _initialize_github_alerter_manager() -> GithubAlerterManager:
    manager_display_name = GITHUB_ALERTER_MANAGER_NAME

    github_alerter_manager_logger = _initialize_logger(
        manager_display_name, GithubAlerterManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the system alerters manager
    while True:
        try:
            github_alerter_manager = GithubAlerterManager(
                github_alerter_manager_logger, manager_display_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(
                manager_display_name, e), github_alerter_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          github_alerter_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return github_alerter_manager


def _initialize_system_monitors_manager() -> SystemMonitorsManager:
    manager_display_name = SYSTEM_MONITORS_MANAGER_NAME

    system_monitors_manager_logger = _initialize_logger(
        manager_display_name, SystemMonitorsManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the system monitors manager
    while True:
        try:
            system_monitors_manager = SystemMonitorsManager(
                system_monitors_manager_logger, manager_display_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(
                manager_display_name, e), system_monitors_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          system_monitors_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return system_monitors_manager


def _initialize_github_monitors_manager() -> GitHubMonitorsManager:
    manager_display_name = GITHUB_MONITORS_MANAGER_NAME

    github_monitors_manager_logger = _initialize_logger(
        manager_display_name, GitHubMonitorsManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the github monitors manager
    while True:
        try:
            github_monitors_manager = GitHubMonitorsManager(
                github_monitors_manager_logger, manager_display_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(
                manager_display_name, e), github_monitors_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          github_monitors_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return github_monitors_manager


def _initialize_data_transformers_manager() -> DataTransformersManager:
    manager_display_name = DATA_TRANSFORMERS_MANAGER_NAME

    data_transformers_manager_logger = _initialize_logger(
        manager_display_name, DataTransformersManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the data transformers manager
    while True:
        try:
            data_transformers_manager = DataTransformersManager(
                data_transformers_manager_logger, manager_display_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(
                manager_display_name, e), data_transformers_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          data_transformers_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return data_transformers_manager


def _initialize_channels_manager() -> ChannelsManager:
    manager_display_name = CHANNELS_MANAGER_NAME

    channels_manager_logger = _initialize_logger(
        manager_display_name, ChannelsManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the data transformers manager
    while True:
        try:
            channels_manager = ChannelsManager(channels_manager_logger,
                                               manager_display_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(
                manager_display_name, e), channels_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          channels_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return channels_manager


def _initialize_alert_router() -> Tuple[AlertRouter, logging.Logger]:
    display_name = ALERT_ROUTER_NAME

    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            alert_router_logger = create_logger(env.ALERT_ROUTER_LOG_FILE,
                                                AlertRouter.__name__,
                                                env.LOGGING_LEVEL,
                                                rotating=True)
            break
        except Exception as e:
            # Use a dummy logger in this case because we cannot create the
            # manager's logger.
            dummy_logger = logging.getLogger('DUMMY_LOGGER')
            log_and_print(get_initialisation_error_message(
                display_name, e), dummy_logger)
            log_and_print(get_reattempting_message(display_name), dummy_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    rabbit_ip = env.RABBIT_IP
    redis_ip = env.REDIS_IP
    redis_db = env.REDIS_DB
    redis_port = env.REDIS_PORT
    unique_alerter_identifier = env.UNIQUE_ALERTER_IDENTIFIER

    while True:
        try:
            alert_router = AlertRouter(
                alert_router_logger, rabbit_ip, redis_ip, redis_db, redis_port,
                unique_alerter_identifier, env.ENABLE_CONSOLE_ALERTS
            )
            return alert_router, alert_router_logger
        except Exception as e:
            log_and_print(get_initialisation_error_message(display_name, e),
                          alert_router_logger)
            log_and_print(get_reattempting_message(display_name),
                          alert_router_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)


def _initialize_config_manager() -> Tuple[ConfigsManager, logging.Logger]:
    display_name = CONFIGS_MANAGER_NAME
    config_manager_logger = _initialize_logger(
        display_name, ConfigsManager.__name__, env.CONFIG_MANAGER_LOG_FILE
    )

    rabbit_ip = env.RABBIT_IP
    while True:
        try:
            config_manager = ConfigsManager(display_name, config_manager_logger,
                                            '../config', rabbit_ip)
            return config_manager, config_manager_logger
        except Exception as e:
            # This is already logged, we need to try again. This exception
            # should not happen, but if it does the program can't fully start
            # up
            log_and_print(get_initialisation_error_message(display_name, e),
                          config_manager_logger)
            log_and_print(get_reattempting_message(display_name),
                          config_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)


def _initialize_data_store_manager() -> StoreManager:
    manager_display_name = DATA_STORE_MANAGER_NAME

    data_store_manager_logger = _initialize_logger(
        manager_display_name, StoreManager.__name__,
        env.MANAGERS_LOG_FILE_TEMPLATE
    )

    # Attempt to initialize the data store manager
    while True:
        try:
            data_store_manager = StoreManager(
                data_store_manager_logger, manager_display_name)
            break
        except Exception as e:
            log_and_print(get_initialisation_error_message(
                manager_display_name, e), data_store_manager_logger)
            log_and_print(get_reattempting_message(manager_display_name),
                          data_store_manager_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return data_store_manager


def run_data_stores_manager() -> None:
    stores_manager = _initialize_data_store_manager()

    while True:
        try:
            stores_manager.start()
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
                stores_manager, RESTART_SLEEPING_PERIOD), stores_manager.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


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
    while True:
        try:
            manager.start()
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
                manager, RESTART_SLEEPING_PERIOD), manager.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


def run_alerters_manager(manager: AlertersManager) -> None:
    while True:
        try:
            manager.start()
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
                manager, RESTART_SLEEPING_PERIOD), manager.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


def run_data_transformers_manager() -> None:
    data_transformers_manager = _initialize_data_transformers_manager()

    while True:
        try:
            data_transformers_manager.start()
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
                data_transformers_manager, RESTART_SLEEPING_PERIOD),
                data_transformers_manager.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


def run_alert_router() -> None:
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
                alert_router, RESTART_SLEEPING_PERIOD), alert_router_logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


def run_config_manager() -> None:
    config_manager, config_manager_logger = _initialize_config_manager()

    while True:
        try:
            config_manager.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-initialize just break the loop.
            log_and_print(get_stopped_message(config_manager),
                          config_manager_logger)
        except Exception:
            config_manager.disconnect_from_rabbit()
            log_and_print(get_stopped_message(config_manager),
                          config_manager_logger)
            log_and_print("Restarting {} in {} seconds.".format(
                config_manager, RESTART_SLEEPING_PERIOD), config_manager_logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


def run_channels_manager() -> None:
    channels_manager = _initialize_channels_manager()

    while True:
        try:
            channels_manager.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-initialize just break the loop.
            log_and_print(get_stopped_message(channels_manager),
                          channels_manager.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            channels_manager.disconnect_from_rabbit()
            log_and_print(get_stopped_message(channels_manager),
                          channels_manager.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                channels_manager, RESTART_SLEEPING_PERIOD),
                channels_manager.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)


# If termination signals are received, terminate all child process and exit
def on_terminate(signum: int, stack: FrameType) -> None:
    def terminate_and_join_process(process: multiprocessing.Process, name: str):
        log_and_print("Terminating the {}".format(name), dummy_logger)
        process.terminate()
        process.join()

    dummy_logger = logging.getLogger('Dummy')

    log_and_print("The alerter is terminating. All components will be stopped "
                  "gracefully.", dummy_logger)

    terminate_and_join_process(config_manager_runner_process,
                               CONFIGS_MANAGER_NAME)

    terminate_and_join_process(system_monitors_manager_process,
                               SYSTEM_MONITORS_MANAGER_NAME)

    terminate_and_join_process(github_monitors_manager_process,
                               GITHUB_MONITORS_MANAGER_NAME)

    terminate_and_join_process(data_transformers_manager_process,
                               DATA_TRANSFORMERS_MANAGER_NAME)

    terminate_and_join_process(system_alerters_manager_process,
                               SYSTEM_ALERTERS_MANAGER_NAME)

    terminate_and_join_process(github_alerter_manager_process,
                               GITHUB_ALERTER_MANAGER_NAME)

    terminate_and_join_process(data_store_process,
                               DATA_STORE_MANAGER_NAME)

    terminate_and_join_process(alert_router_process, ALERT_ROUTER_NAME)

    terminate_and_join_process(channels_manager_process, CHANNELS_MANAGER_NAME)

    log_and_print("PANIC process terminated.", dummy_logger)

    log_and_print("The alerting and monitoring process has ended.",
                  dummy_logger)
    sys.exit()


def _initialise_and_declare_config_queues() -> None:
    # TODO: This can be refactored by storing the queue configurations in
    #     : constant.py so that it is easier to maintain.
    dummy_logger = logging.getLogger('Dummy')

    while True:
        try:
            rabbitmq = RabbitMQApi(dummy_logger, env.RABBIT_IP)
            log_and_print("Connecting with RabbitMQ to create and bind "
                          "configuration queues.", dummy_logger)
            ret = rabbitmq.connect()
            if ret == -1:
                log_and_print(
                    "RabbitMQ is temporarily unavailable. Re-trying in {} "
                    "seconds.".format(RE_INITIALIZE_SLEEPING_PERIOD),
                    dummy_logger)
                time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)
                continue

            # Config exchange declaration
            log_and_print("Creating {} exchange.".format(CONFIG_EXCHANGE),
                          dummy_logger)
            rabbitmq.exchange_declare(
                CONFIG_EXCHANGE, 'topic', False, True, False, False
            )

            # Alert router queues
            log_and_print("Creating queue '{}'".format(
                ALERT_ROUTER_CONFIGS_QUEUE_NAME), dummy_logger)
            rabbitmq.queue_declare(ALERT_ROUTER_CONFIGS_QUEUE_NAME, False, True,
                                   False, False)
            log_and_print("Binding queue '{}' to '{}' exchange with routing "
                          "key {}.".format(ALERT_ROUTER_CONFIGS_QUEUE_NAME,
                                           CONFIG_EXCHANGE, 'channels.*'),
                          dummy_logger)
            rabbitmq.queue_bind(ALERT_ROUTER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'channels.*')

            # System Alerters Manager queues
            log_and_print("Creating queue '{}'".format(
                SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME), dummy_logger)
            rabbitmq.queue_declare(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                   False, True, False, False)
            log_and_print(
                "Binding queue '{}' to '{}' exchange with routing "
                "key {}.".format(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'chains.*.*.alerts_config'),
                dummy_logger)
            rabbitmq.queue_bind(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'chains.*.*.alerts_config')
            log_and_print(
                "Binding queue '{}' to '{}' exchange with routing "
                "key {}.".format(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'general.alerts_config'),
                dummy_logger)
            rabbitmq.queue_bind(SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'general.alerts_config')

            # Channels manager queues
            log_and_print("Creating queue '{}'".format(
                CHANNELS_MANAGER_CONFIGS_QUEUE_NAME), dummy_logger)
            rabbitmq.queue_declare(CHANNELS_MANAGER_CONFIGS_QUEUE_NAME, False,
                                   True, False, False)
            log_and_print(
                "Binding queue '{}' to '{}' exchange with routing "
                "key {}.".format(CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'channels.*'),
                dummy_logger)
            rabbitmq.queue_bind(CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'channels.*')

            # GitHub Monitors Manager queues
            log_and_print("Creating queue '{}'".format(
                GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME), dummy_logger)
            rabbitmq.queue_declare(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                   False, True, False, False)
            log_and_print(
                "Binding queue '{}' to '{}' exchange with routing "
                "key {}.".format(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'chains.*.*.repos_config'),
                dummy_logger)
            rabbitmq.queue_bind(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'chains.*.*.repos_config')
            log_and_print(
                "Binding queue '{}' to '{}' exchange with routing "
                "key {}.".format(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'general.repos_config'),
                dummy_logger)
            rabbitmq.queue_bind(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'general.repos_config')

            # System Monitors Manager queues
            log_and_print("Creating queue '{}'".format(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME), dummy_logger)
            rabbitmq.queue_declare(SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                   False, True, False, False)
            log_and_print(
                "Binding queue '{}' to '{}' exchange with routing "
                "key {}.".format(SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'chains.*.*.nodes_config'),
                dummy_logger)
            rabbitmq.queue_bind(SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'chains.*.*.nodes_config')
            log_and_print(
                "Binding queue '{}' to '{}' exchange with routing "
                "key {}.".format(SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, 'general.systems_config'),
                dummy_logger)
            rabbitmq.queue_bind(SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                CONFIG_EXCHANGE, 'general.systems_config')

            ret = rabbitmq.disconnect()
            if ret == -1:
                log_and_print(
                    "RabbitMQ is temporarily unavailable. Re-trying in {} "
                    "seconds.".format(RE_INITIALIZE_SLEEPING_PERIOD),
                    dummy_logger)
                time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)
                continue

            log_and_print("Configuration queues initialisation procedure has "
                          "completed successfully. Disconnecting with "
                          "RabbitMQ.", dummy_logger)
            break
        except pika.exceptions.AMQPChannelError as e:
            log_and_print("Channel error while initializing the configuration "
                          "queues: {}. Re-trying in {} "
                          "seconds.".format(repr(e),
                                            RE_INITIALIZE_SLEEPING_PERIOD),
                          dummy_logger)
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)
        except pika.exceptions.AMQPConnectionError as e:
            log_and_print("RabbitMQ connection error while initializing the "
                          "configuration queues: {}. Re-trying in {} "
                          "seconds.".format(repr(e),
                                            RE_INITIALIZE_SLEEPING_PERIOD),
                          dummy_logger)
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)
        except Exception as e:
            log_and_print("Unexpected exception while initializing the "
                          "configuration queues: {}. Re-trying in {} "
                          "seconds.".format(repr(e),
                                            RE_INITIALIZE_SLEEPING_PERIOD),
                          dummy_logger)
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)


if __name__ == '__main__':
    # First initialize the config queues so that no config is lost if the
    # individual components
    _initialise_and_declare_config_queues()

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

    # Start the channels manager in a separate process
    channels_manager_process = multiprocessing.Process(
        target=run_channels_manager, args=())
    channels_manager_process.start()

    # Config manager must be the last to start since it immediately begins by
    # sending the configs. That being said, all previous processes need to wait
    # for the config manager too.
    config_manager_runner_process = multiprocessing.Process(
        target=run_config_manager, args=())
    config_manager_runner_process.start()

    signal.signal(signal.SIGTERM, on_terminate)
    signal.signal(signal.SIGINT, on_terminate)
    signal.signal(signal.SIGHUP, on_terminate)

    # If we don't wait for the processes to terminate the root process will
    # exit
    config_manager_runner_process.join()
    github_monitors_manager_process.join()
    system_monitors_manager_process.join()
    system_alerters_manager_process.join()
    github_alerter_manager_process.join()
    data_transformers_manager_process.join()
    data_store_process.join()
    alert_router_process.join()
    channels_manager_process.join()

    print("The alerting and monitoring process has ended.")
    sys.stdout.flush()
