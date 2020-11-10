import logging
import os
import time

import pika.exceptions
from src.alerter.alerters.alerter import Alerter
from src.alerter.alerters.system import SystemAlerter
from src.alerter.alerters.github import GithubAlerter
from src.configs.repo import RepoConfig
from src.configs.system_alerts import SystemAlertsConfig
from src.utils.logging import create_logger, log_and_print


def _initialize_alerter_logger(alerter_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            monitor_logger = create_logger(
                os.environ["ALERTERS_LOG_FILE_TEMPLATE"].format(alerter_name),
                alerter_name, os.environ["LOGGING_LEVEL"], rotating=True)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!'.format(
                alerter_name, e)
            # Use a dummy logger in this case because we cannot create the
            # monitor's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return monitor_logger


def _initialize_system_alerter(system_alerts_config: SystemAlertsConfig) \
                               -> SystemAlerter:
    # Alerter name based on system
    alerter_name = 'System alerter ({})'.format(system_alerts_config.parent)

    system_alerter_logger = _initialize_alerter_logger(alerter_name)

    # Try initializing a monitor until successful
    while True:
        try:
            system_alerter = SystemAlerter(alerter_name, system_alerts_config,
                                           system_alerter_logger)
            log_and_print("Successfully initialized {}".format(alerter_name),
                          system_alerter_logger)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!'.format(
                alerter_name, e)
            log_and_print(msg, system_alerter_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return system_alerter


def _initialize_github_alerter() -> GithubAlerter:

    alerter_name = 'Github alerter'

    github_alerter_logger = _initialize_alerter_logger(alerter_name)

    # Try initializing a monitor until successful
    while True:
        try:
            github_alerter = GithubAlerter(alerter_name, github_alerter_logger)
            log_and_print("Successfully initialized {}".format(alerter_name),
                          github_alerter_logger)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!'.format(
                alerter_name, e)
            log_and_print(msg, github_alerter_logger)
            time.sleep(10)  # sleep 10 seconds before trying again

    return github_alerter


def start_github_alerter() -> None:
    github_alerter = _initialize_github_alerter()
    start_alerter(github_alerter)


def start_system_alerter(system_alerts_config: SystemAlertsConfig) -> None:
    system_alerter = _initialize_system_alerter(system_alerts_config)
    start_alerter(system_alerter)


def start_alerter(alerter: Alerter) -> None:
    while True:
        try:
            log_and_print('{} started.'.format(alerter), alerter.logger)
            alerter.start_alert_classification()
        except pika.exceptions.AMQPConnectionError:
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print('{} stopped.'.format(alerter), alerter.logger)
        except Exception:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            alerter.rabbitmq.disconnect_till_successful()
            log_and_print('{} stopped.'.format(alerter), alerter.logger)
