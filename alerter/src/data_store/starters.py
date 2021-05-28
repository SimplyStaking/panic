import logging
import time
from typing import TypeVar, Type

import pika.exceptions

from src.data_store.stores.alert import AlertStore
from src.data_store.stores.config import ConfigStore
from src.data_store.stores.github import GithubStore
from src.data_store.stores.store import Store
from src.data_store.stores.system import SystemStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (CONFIG_STORE_NAME, SYSTEM_STORE_NAME,
                                       GITHUB_STORE_NAME, ALERT_STORE_NAME)
from src.utils.constants.starters import (RE_INITIALISE_SLEEPING_PERIOD,
                                          RESTART_SLEEPING_PERIOD)
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import (get_initialisation_error_message,
                                get_stopped_message)

T = TypeVar('T', bound=Store)  # Restricts the generic to Store or subclasses


def _initialise_store_logger(
        store_display_name: str, store_module_name: str) -> logging.Logger:
    # Try initialising the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            store_logger = create_logger(
                env.DATA_STORE_LOG_FILE_TEMPLATE.format(store_display_name),
                store_module_name, env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = get_initialisation_error_message(store_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # transformer's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return store_logger


def _initialise_store(store_type: Type[T], store_display_name: str) -> T:
    store_logger = _initialise_store_logger(store_display_name,
                                            store_type.__name__)

    # Try initialising the store until successful
    while True:
        try:
            rabbitmq = RabbitMQApi(
                logger=store_logger.getChild(RabbitMQApi.__name__),
                host=env.RABBIT_IP)
            store = store_type(store_display_name, store_logger, rabbitmq)
            log_and_print("Successfully initialised {}".format(
                store_display_name), store_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(store_display_name, e)
            log_and_print(msg, store_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return store


def start_config_store() -> None:
    config_store = _initialise_store(ConfigStore, CONFIG_STORE_NAME)
    start_store(config_store)


def start_system_store() -> None:
    system_store = _initialise_store(SystemStore, SYSTEM_STORE_NAME)
    start_store(system_store)


def start_github_store() -> None:
    github_store = _initialise_store(GithubStore, GITHUB_STORE_NAME)
    start_store(github_store)


def start_alert_store() -> None:
    alert_store = _initialise_store(AlertStore, ALERT_STORE_NAME)
    start_store(alert_store)


def start_store(store: Store) -> None:
    while True:
        try:
            log_and_print("{} started.".format(store), store.logger)
            store.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            log_and_print(get_stopped_message(store), store.logger)
        except Exception as e:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            store.disconnect_from_rabbit()
            log_and_print("Restarting {} in {} seconds.".format(
                store, RESTART_SLEEPING_PERIOD), store.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)
