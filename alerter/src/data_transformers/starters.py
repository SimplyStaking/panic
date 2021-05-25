import logging
import time
from typing import TypeVar, Type

import pika.exceptions

from src.data_store.redis import RedisApi
from src.data_transformers.data_transformer import DataTransformer
from src.data_transformers.github import GitHubDataTransformer
from src.data_transformers.system import SystemDataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (SYSTEM_DATA_TRANSFORMER_NAME,
                                       GITHUB_DATA_TRANSFORMER_NAME)
from src.utils.constants.starters import (RE_INITIALISE_SLEEPING_PERIOD,
                                          RESTART_SLEEPING_PERIOD)
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import (get_initialisation_error_message,
                                get_stopped_message)

# Restricts the generic to DataTransformer or subclasses
T = TypeVar('T', bound=DataTransformer)


def _initialise_transformer_logger(
        transformer_display_name: str,
        transformer_module_name: str) -> logging.Logger:
    # Try initialising the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            transformer_logger = create_logger(
                env.TRANSFORMERS_LOG_FILE_TEMPLATE.format(
                    transformer_display_name), transformer_module_name,
                env.LOGGING_LEVEL, True)
            break
        except Exception as e:
            msg = get_initialisation_error_message(transformer_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # transformer's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return transformer_logger


def _initialise_transformer_redis(
        transformer_name: str, transformer_logger: logging.Logger) -> RedisApi:
    # Try initialising the Redis API until successful. This had to be done
    # separately to avoid instances when Redis creation failed and we
    # attempt to use it.
    while True:
        try:
            redis = RedisApi(logger=transformer_logger.getChild(
                RedisApi.__name__), db=env.REDIS_DB, host=env.REDIS_IP,
                port=env.REDIS_PORT, namespace=env.UNIQUE_ALERTER_IDENTIFIER)
            break
        except Exception as e:
            msg = get_initialisation_error_message(transformer_name, e)
            log_and_print(msg, transformer_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return redis


def _initialise_data_transformer(data_transformer_type: Type[T],
                                 data_transformer_display_name: str) -> T:
    transformer_logger = _initialise_transformer_logger(
        data_transformer_display_name, data_transformer_type.__name__)
    redis = _initialise_transformer_redis(data_transformer_display_name,
                                          transformer_logger)

    # Try initialising the transformer until successful
    while True:
        try:
            rabbitmq = RabbitMQApi(
                logger=transformer_logger.getChild(RabbitMQApi.__name__),
                host=env.RABBIT_IP)
            data_transformer = data_transformer_type(
                data_transformer_display_name, transformer_logger, redis,
                rabbitmq, env.DATA_TRANSFORMER_PUBLISHING_QUEUE_SIZE)
            log_and_print("Successfully initialised {}".format(
                data_transformer_display_name), transformer_logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(
                data_transformer_display_name, e)
            log_and_print(msg, transformer_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return data_transformer


def start_system_data_transformer() -> None:
    system_data_transformer = _initialise_data_transformer(
        SystemDataTransformer, SYSTEM_DATA_TRANSFORMER_NAME)
    start_transformer(system_data_transformer)


def start_github_data_transformer() -> None:
    github_data_transformer = _initialise_data_transformer(
        GitHubDataTransformer, GITHUB_DATA_TRANSFORMER_NAME)
    start_transformer(github_data_transformer)


def start_transformer(transformer: DataTransformer) -> None:
    while True:
        try:
            log_and_print("{} started.".format(transformer), transformer.logger)
            transformer.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            log_and_print(get_stopped_message(transformer), transformer.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            transformer.disconnect_from_rabbit()
            log_and_print(get_stopped_message(transformer), transformer.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                transformer, RESTART_SLEEPING_PERIOD), transformer.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)
