import logging
import time
from typing import Union

import pika.exceptions

from src.data_store.redis import RedisApi
from src.health_checker.heartbeat_handler import HeartbeatHandler
from src.health_checker.ping_publisher import PingPublisher
from src.utils import env
from src.utils.constants.names import (HEARTBEAT_HANDLER_NAME,
                                       PING_PUBLISHER_NAME)
from src.utils.constants.starters import (RE_INITIALISE_SLEEPING_PERIOD,
                                          RESTART_SLEEPING_PERIOD)
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import (get_initialisation_error_message,
                                get_stopped_message)

HealthCheckerComponentType = Union[HeartbeatHandler, PingPublisher]


def _initialise_health_checker_logger(
        component_display_name: str, component_module_name: str) \
        -> logging.Logger:
    # Try initialising the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            component_logger = create_logger(
                env.HEALTH_CHECKER_LOG_FILE_TEMPLATE.format(
                    component_display_name), component_module_name,
                env.LOGGING_LEVEL, rotating=True)
            break
        except Exception as e:
            msg = get_initialisation_error_message(component_display_name, e)
            # Use a dummy logger in this case because we cannot create the
            # transformer's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return component_logger


def _initialise_component_redis(component_display_name: str,
                                component_logger: logging.Logger) -> RedisApi:
    # Try initialising the Redis API until successful. This had to be done
    # separately to avoid instances when Redis creation failed and we
    # attempt to use it.
    while True:
        try:
            redis_db = env.REDIS_DB
            redis_port = env.REDIS_PORT
            redis_host = env.REDIS_IP
            unique_alerter_identifier = env.UNIQUE_ALERTER_IDENTIFIER

            redis = RedisApi(
                logger=component_logger.getChild(RedisApi.__name__),
                db=redis_db, host=redis_host, port=redis_port,
                namespace=unique_alerter_identifier)
            break
        except Exception as e:
            msg = get_initialisation_error_message(component_display_name, e)
            log_and_print(msg, component_logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return redis


def _initialise_heartbeat_handler() -> HeartbeatHandler:
    component_display_name = HEARTBEAT_HANDLER_NAME

    logger = _initialise_health_checker_logger(component_display_name,
                                               HeartbeatHandler.__name__)
    redis = _initialise_component_redis(component_display_name, logger)

    # Try initialising the heartbeat handler until successful
    while True:
        try:
            heartbeat_handler = HeartbeatHandler(logger, redis,
                                                 component_display_name)
            log_and_print("Successfully initialised {}".format(
                component_display_name), logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(component_display_name, e)
            log_and_print(msg, logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return heartbeat_handler


def _initialise_ping_publisher() -> PingPublisher:
    component_display_name = PING_PUBLISHER_NAME

    logger = _initialise_health_checker_logger(component_display_name,
                                               PingPublisher.__name__)
    redis = _initialise_component_redis(component_display_name, logger)

    # Try initialising the ping publisher until successful
    while True:
        try:
            ping_publisher = PingPublisher(30, logger, redis,
                                           component_display_name)
            log_and_print("Successfully initialised {}".format(
                component_display_name), logger)
            break
        except Exception as e:
            msg = get_initialisation_error_message(component_display_name, e)
            log_and_print(msg, logger)
            # sleep before trying again
            time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

    return ping_publisher


def start_heartbeat_handler() -> None:
    heartbeat_handler = _initialise_heartbeat_handler()
    start_health_checker_component(heartbeat_handler)


def start_ping_publisher() -> None:
    ping_publisher = _initialise_ping_publisher()
    start_health_checker_component(ping_publisher)


def start_health_checker_component(component: HealthCheckerComponentType) \
        -> None:
    while True:
        try:
            log_and_print("{} started.".format(component), component.logger)
            component.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            log_and_print(get_stopped_message(component), component.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            component.disconnect_from_rabbit()
            log_and_print(get_stopped_message(component), component.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                component, RESTART_SLEEPING_PERIOD), component.logger)
            time.sleep(RESTART_SLEEPING_PERIOD)
