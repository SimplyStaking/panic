import logging
import os
import time
from typing import Union

import pika.exceptions

from src.data_store.redis import RedisApi
from src.health_checker.heartbeat_handler import HeartbeatHandler
from src.health_checker.ping_publisher import PingPublisher
from src.utils.logging import create_logger, log_and_print

HealthCheckerComponentType = Union[HeartbeatHandler, PingPublisher]


def _initialize_health_checker_logger(component_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            component_logger = create_logger(
                os.environ['HEALTH_CHECKER_LOG_FILE_TEMPLATE'].format(
                    component_name), component_name,
                os.environ['LOGGING_LEVEL'], rotating=True)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                component_name, e)
            # Use a dummy logger in this case because we cannot create the
            # transformer's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return component_logger


def _initialize_component_redis(
        component_name: str, component_logger: logging.Logger) -> RedisApi:
    # Try initializing the Redis API until successful. This had to be done
    # separately to avoid instances when Redis creation failed and we
    # attempt to use it.
    while True:
        try:
            redis_db = int(os.environ['REDIS_DB'])
            redis_port = int(os.environ['REDIS_PORT'])
            redis_host = os.environ['REDIS_IP']
            unique_alerter_identifier = os.environ['UNIQUE_ALERTER_IDENTIFIER']

            redis = RedisApi(logger=component_logger, db=redis_db,
                             host=redis_host, port=redis_port,
                             namespace=unique_alerter_identifier)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                component_name, e)
            log_and_print(msg, component_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return redis


def _initialize_heartbeat_handler() -> HeartbeatHandler:
    component_name = 'Heartbeat Handler'

    logger = _initialize_health_checker_logger(component_name)
    redis = _initialize_component_redis(component_name, logger)

    # Try initializing the heartbeat handler until successful
    while True:
        try:
            heartbeat_handler = HeartbeatHandler(logger, redis, component_name)
            log_and_print("Successfully initialized {}".format(component_name),
                          logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                component_name, e)
            log_and_print(msg, logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return heartbeat_handler


def _initialize_ping_publisher() -> PingPublisher:
    component_name = 'Ping Publisher'

    logger = _initialize_health_checker_logger(component_name)
    redis = _initialize_component_redis(component_name, logger)

    # Try initializing the ping publisher until successful
    while True:
        try:
            ping_publisher = PingPublisher(30, logger, redis, component_name)
            log_and_print("Successfully initialized {}".format(component_name),
                          logger)
            break
        except Exception as e:
            msg = "!!! Error when initialising {}: {} !!!".format(
                component_name, e)
            log_and_print(msg, logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return ping_publisher


def start_heartbeat_handler() -> None:
    heartbeat_handler = _initialize_heartbeat_handler()
    start_health_checker_component(heartbeat_handler)


def start_ping_publisher() -> None:
    ping_publisher = _initialize_ping_publisher()
    start_health_checker_component(ping_publisher)


def start_health_checker_component(component: HealthCheckerComponentType) \
        -> None:
    sleep_period = 10

    while True:
        try:
            log_and_print("{} started.".format(component), component.logger)
            component.start()
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError):
            # Error would have already been logged by RabbitMQ logger.
            log_and_print("{} stopped.".format(component), component.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            component.rabbitmq.disconnect_till_successful()
            log_and_print("{} stopped.".format(component), component.logger)
            log_and_print("Restarting {} in {} seconds.".format(
                component, sleep_period), component.logger)
            time.sleep(sleep_period)
