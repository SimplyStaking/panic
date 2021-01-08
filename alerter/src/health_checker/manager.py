import logging
import multiprocessing
import signal
import sys
import time
from types import FrameType
from typing import Dict

from src.health_checker.starters import start_heartbeat_handler, \
    start_ping_publisher
from src.utils.constants import HEARTBEAT_HANDLER_NAME, PING_PUBLISHER_NAME
from src.utils.logging import log_and_print


class HealthCheckerManager:
    def __init__(self, logger: logging.Logger, name: str):
        self._logger = logger
        self._name = name
        self._component_process_dict = {}

        # Handle termination signals by stopping the manager gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def name(self) -> str:
        return self._name

    @property
    def component_process_dict(self) -> Dict:
        return self._component_process_dict

    def manage(self) -> None:
        while True:
            # Start the heartbeat handler in a separate process if it is not
            # yet started or it is not alive.
            if HEARTBEAT_HANDLER_NAME not in self.component_process_dict or \
                    not self.component_process_dict[
                        HEARTBEAT_HANDLER_NAME].is_alive():

                # To avoid having unreleased resources
                if HEARTBEAT_HANDLER_NAME in self.component_process_dict:
                    self.component_process_dict[HEARTBEAT_HANDLER_NAME].join()

                log_and_print("Attempting to start the {}.".format(
                    HEARTBEAT_HANDLER_NAME), self.logger)
                heartbeat_handler_process = multiprocessing.Process(
                    target=start_heartbeat_handler, args=())
                heartbeat_handler_process.daemon = True
                heartbeat_handler_process.start()
                self.component_process_dict[HEARTBEAT_HANDLER_NAME] = \
                    heartbeat_handler_process

            # Start the ping publisher in a separate process if it is not
            # yet started or it is not alive.
            if PING_PUBLISHER_NAME not in self.component_process_dict or \
                    not self.component_process_dict[
                        PING_PUBLISHER_NAME].is_alive():

                # To avoid having unreleased resources
                if PING_PUBLISHER_NAME in self.component_process_dict:
                    self.component_process_dict[PING_PUBLISHER_NAME].join()

                log_and_print("Attempting to start the {}.".format(
                    PING_PUBLISHER_NAME), self.logger)
                ping_publisher_process = multiprocessing.Process(
                    target=start_ping_publisher, args=())
                ping_publisher_process.daemon = True
                ping_publisher_process.start()
                self.component_process_dict[PING_PUBLISHER_NAME] = \
                    ping_publisher_process

            self.logger.debug("Sleeping for %s seconds.", 10)
            time.sleep(10)

    # If termination signals are received, terminate all child process and exit
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. All sub-processes will be stopped "
                      "gracefully and then the {} process will "
                      "exit.".format(self, self), self.logger)

        for component, process in self.component_process_dict.items():
            log_and_print("Terminating the process of {}".format(component),
                          self.logger)
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
