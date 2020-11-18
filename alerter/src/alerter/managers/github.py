import logging
import signal
import sys
from multiprocessing import Process
from types import FrameType
from typing import Dict

import pika.exceptions
from src.alerter.alerter_starters import start_github_alerter
from src.alerter.alerters.github import GithubAlerter
from src.utils.logging import log_and_print


class GithubAlerterManager:
    def __init__(self, logger: logging.Logger, name: str):
        self._name = name
        self._logger = logger
        self._github_alerter = GithubAlerter(logger, 'Github Alerter')
        self._process_holder = {}
        # Handle termination signals by stopping the manager gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

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

    @property
    def process_holder(self) -> Dict:
        return self._process_holder

    def start_github_alerter_manager(self) -> None:
        log_and_print('{} started.'.format(self), self.logger)
        process = Process(target=start_github_alerter, args=())
        process.daemon = True
        process.start()
        self._process_holder['github'] = process
        process.join()
        del self._process_holder['github']
        log_and_print("{} stopped.".format(self), self.logger)

    # If termination signals are received, terminate all child process and exit
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. The github alerter will be "
                      "stopped gracefully and then the {} process will "
                      "exit.".format(self, self), self.logger)
        process = self._process_holder['github']
        log_and_print("Terminating the process of {}".format(process),
                      self.logger)
        process.terminate()
        process.join()
        del self._process_holder['github']
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
