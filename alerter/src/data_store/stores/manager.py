import logging
import signal
import sys
from multiprocessing import Process
from types import FrameType

import pika.exceptions
from src.data_store.stores.alert import AlertStore
from src.data_store.stores.github import GithubStore
from src.data_store.stores.store import Store
from src.data_store.stores.system import SystemStore
from src.utils.logging import log_and_print


class StoreManager:
    def __init__(self, logger: logging.Logger, name: str):
        self._name = name
        self._logger = logger
        self._system_store = SystemStore(self._logger, "System Store")
        self._github_store = GithubStore(self._logger, "Github Store")
        self._alert_store = AlertStore(self._logger, "Alert Store")
        self._stores = [self.system_store, self.github_store, self.alert_store]
        self._process = {}
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
    def system_store(self) -> SystemStore:
        return self._system_store

    @property
    def github_store(self) -> GithubStore:
        return self._github_store

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def alert_store(self) -> AlertStore:
        return self._alert_store

    @staticmethod
    def start_store(store: Store) -> None:
        # while True:
        try:
            log_and_print('{} started.'.format(store), store.logger)
            store.begin_store()
        except pika.exceptions.AMQPConnectionError:
            # Error would have already been logged by RabbitMQ logger.
            # Since we have to re-connect just break the loop.
            log_and_print('{} stopped.'.format(store), store.logger)
        except Exception as e:
            # Close the connection with RabbitMQ if we have an unexpected
            # exception, and start again
            store.rabbitmq.disconnect_till_successful()
            log_and_print('{} stopped. {}'.format(store, e), store.logger)

    def start_store_manager(self) -> None:
        """
        Starts all the store processes, these will initialize all the rabbitmq
        interfaces together with mongo client connections. All rabbit instances
        will then begin listening for incoming messages.
        """
        processes = []
        for instance in self._stores:
            process = Process(target=self.start_store, args=(instance,))
            process.daemon = True
            process.start()
            self._process[instance] = process
            processes.append(process)

        for process in processes:
            process.join()

    # If termination signals are received, terminate all child process and exit
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print('{} is terminating. All the data store will be '
                      'stopped gracefully and then the {} process will '
                      'exit.'.format(self, self), self.logger)

        for store, process in self._process.items():
            log_and_print('Terminating the process of {}'.format(store),
                          self.logger)
            process.terminate()
            process.join()

        log_and_print('{} terminated.'.format(self), self.logger)
        sys.exit()
