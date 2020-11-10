import logging
from multiprocessing import Process

import pika.exceptions
from src.alerter.alerters.github import GithubAlerter
from src.alerter.alerter_starters import start_github_alerter
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
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def github_alerter(self) -> GithubAlerter:
        return self._github_alerter

    def start_github_alerter_manager(self) -> None:
        log_and_print('{} started.'.format(self), self.logger)
        process = Process(target=start_github_alerter, args=())
        process.daemon = True
        process.start()
        process.join()
        log_and_print('{} stopped.'.format(self), self.logger)
