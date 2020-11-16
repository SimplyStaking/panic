import logging
import multiprocessing
import signal
import sys
from types import FrameType
from typing import Dict

from src.data_transformers.starters import start_system_data_transformer, \
    start_github_data_transformer
from src.utils.logging import log_and_print


class DataTransformersManager:
    def __init__(self, logger: logging.Logger, name: str):
        self._logger = logger
        self._name = name
        self._transformer_process_dict = {}

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
    def transformer_process_dict(self) -> Dict:
        return self._transformer_process_dict

    def manage(self) -> None:
        log_and_print('{} started.'.format(self), self.logger)

        # Start the system data transformer in a separate process if it is not
        # yet started or it is not alive. This must be done in case of a
        # restart of the manager.
        if 'System Data Transformer' not in self.transformer_process_dict or \
                not self.transformer_process_dict[
                    'System Data Transformer'].is_alive():
            log_and_print('Attempting to start the System Data Transformer.',
                          self.logger)
            system_data_transformer_process = multiprocessing.Process(
                target=start_system_data_transformer, args=())
            system_data_transformer_process.daemon = True
            system_data_transformer_process.start()
            self._transformer_process_dict['System Data Transformer'] = \
                system_data_transformer_process

        # Start the github data transformer in a separate process if it is not
        # yet started or it is not alive. This must be done in case of a
        # restart of the manager.
        if 'GitHub Data Transformer' not in self.transformer_process_dict or \
                not self.transformer_process_dict[
                    'System Data Transformer'].is_alive():
            log_and_print('Attempting to start the GitHub Data Transformer.',
                          self.logger)
            github_data_transformer_process = multiprocessing.Process(
                target=start_github_data_transformer, args=())
            github_data_transformer_process.daemon = True
            github_data_transformer_process.start()
            self._transformer_process_dict['GitHub Data Transformer'] = \
                github_data_transformer_process

        # Wait for all the processes to terminate before re-starting
        self.transformer_process_dict['System Data Transformer'].join()
        self.transformer_process_dict['GitHub Data Transformer'].join()

    # If termination signals are received, terminate all child process and exit
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print('{} is terminating. All the data transformers will be '
                      'stopped gracefully and then the {} process will '
                      'exit.'.format(self, self), self.logger)

        for transformer, process in self.transformer_process_dict.items():
            log_and_print('Terminating the process of {}'.format(transformer),
                          self.logger)
            process.terminate()
            process.join()

        log_and_print('{} terminated.'.format(self), self.logger)
        sys.exit()
