import logging
import time

import pika.exceptions

from src.data_store.redis import RedisApi
from src.data_transformers.data_transformer import DataTransformer
from src.data_transformers.github import GitHubDataTransformer
from src.data_transformers.system import SystemDataTransformer
from src.utils import env
from src.utils.constants import RE_INITIALIZE_SLEEPING_PERIOD, \
    RESTART_SLEEPING_PERIOD
from src.utils.logging import create_logger, log_and_print


def _initialize_transformer_logger(
        transformer_display_name: str,
        transformer_module_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            transformer_logger = create_logger(
                env.TRANSFORMERS_LOG_FILE_TEMPLATE.format(
                    transformer_display_name), transformer_module_name,
                env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                transformer_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # transformer's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return transformer_logger


def _initialize_transformer_redis(
        transformer_name: str, transformer_logger: logging.Logger) -> RedisApi:
    # Try initializing the Redis API until successful. This had to be done
    # separately to avoid instances when Redis creation failed and we
    # attempt to use it.
    while True:
        try:
            redis_db = int(env.REDIS_DB)
            redis_port = int(env.REDIS_PORT)
            redis_host = env.REDIS_IP
            unique_alerter_identifier = env.UNIQUE_ALERTER_IDENTIFIER

            redis = RedisApi(logger=transformer_logger.getChild(
                RedisApi.__name__), db=redis_db, host=redis_host,
                port=redis_port, namespace=unique_alerter_identifier)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                transformer_name, e)
            log_and_print(msg, transformer_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return redis


def _initialize_system_data_transformer() -> SystemDataTransformer:
    transformer_display_name = 'System Data Transformer'

    transformer_logger = _initialize_transformer_logger(
        transformer_display_name, SystemDataTransformer.__name__)
    redis = _initialize_transformer_redis(transformer_display_name,
                                          transformer_logger)

    # Try initializing the system data transformer until successful
    while True:
        try:
            system_data_transformer = SystemDataTransformer(
                transformer_display_name, transformer_logger, redis)
            log_and_print("Successfully initialized {}"
                          .format(transformer_display_name), transformer_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                transformer_display_name, e)
            log_and_print(msg, transformer_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return system_data_transformer


def _initialize_github_data_transformer() -> GitHubDataTransformer:
    transformer_display_name = 'GitHub Data Transformer'

    transformer_logger = _initialize_transformer_logger(
        transformer_display_name, GitHubDataTransformer.__name__)
    redis = _initialize_transformer_redis(transformer_display_name,
                                          transformer_logger)

    # Try initializing the github data transformer until successful
    while True:
        try:
            github_data_transformer = GitHubDataTransformer(
                transformer_display_name, transformer_logger, redis)
            log_and_print("Successfully initialized {}"
                          .format(transformer_display_name), transformer_logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                transformer_display_name, e)
            log_and_print(msg, transformer_logger)
            # sleep before trying again
            time.sleep(RE_INITIALIZE_SLEEPING_PERIOD)

    return github_data_transformer


def start_system_data_transformer() -> None:
    system_data_transformer = _initialize_system_data_transformer()
    start_transformer(system_data_transformer)


def start_github_data_transformer() -> None:
    github_data_transformer = _initialize_github_data_transformer()
    start_transformer(github_data_transformer)


def start_transformer(transformer: DataTransformer) -> None:
    while True:
        try:
            log_and_print("{} started.".format(transformer), transformer.logger)
            transformer.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            log_and_print("{} stopped.".format(transformer), transformer.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            transformer.rabbitmq.disconnect_till_successful()
            log_and_print("{} stopped.".format(transformer), transformer.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                transformer, RESTART_SLEEPING_PERIOD), transformer.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)
