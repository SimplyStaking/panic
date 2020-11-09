import logging
from multiprocessing import Process

import pika.exceptions
from src.alerter.alerters.github import GithubAlerter
from src.utils.logging import log_and_print


class GithubAlerterManager:
    def __init__(self, logger: logging.Logger, name: str):
        self._name = name
        self._logger = logger
        self._github_alerter = GithubAlerter(logger, 'Github Alerter')

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    @property
    def github_alerter(self) -> GithubAlerter:
        return self._github_alerter

    @staticmethod
    def start_alerter(github_alerter: GithubAlerter) -> None:
        # while True:
        try:
            log_and_print('{} started.'.format(github_alerter),
                          github_alerter.logger)
            github_alerter._alert_classifier_process()
        except pika.exceptions.AMQPConnectionError:
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print('{} stopped.'.format(github_alerter),
                          github_alerter.logger)
        except Exception as e:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            github_alerter.rabbitmq.disconnect_till_successful()
            log_and_print('{} stopped. {}'.format(github_alerter, e),
                          github_alerter.logger)

    def start_github_alerter_manager(self) -> None:
        process = Process(target=self.start_alerter,
                          args=(self.github_alerter,))
        process.daemon = True
        process.start()
        process.join()
