import logging
from multiprocessing import Process

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
    def alert_store(self) -> AlertStore:
        return self._alert_store

    def start_store(self, store: Store) -> None:
        # while True:
        try:
            log_and_print('{} started.'.format(store), store.logger)
            store._begin_store()
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
        stores = [self.system_store, self.github_store, self.alert_store]
        for instance in stores:
            process = Process(target=self.start_store, args=[instance])
            process.daemon = True
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
