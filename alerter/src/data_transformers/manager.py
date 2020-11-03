import logging
import multiprocessing

from src.data_transformers.starters import start_system_data_transformer
from src.utils.logging import log_and_print


class DataTransformersManager:
    def __init__(self, logger: logging.Logger, name: str):
        self._logger = logger
        self._name = name

    def __str__(self) -> str:
        return self.name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def name(self) -> str:
        return self._name

    def manage(self) -> None:
        log_and_print('{} started.'.format(self), self.logger)

        # Start the data transformers in a separate process
        log_and_print('Attempting to start the System Data Transformer.',
                      self.logger)
        system_data_transformer_process = multiprocessing.Process(
            target=start_system_data_transformer, args=())
        system_data_transformer_process.start()

        # Wait for all the processes to terminate before re-starting
        system_data_transformer_process.join()
