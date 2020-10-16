import logging
from time import sleep
from multiprocessing import Process
from alerter.src.data_store.store.alert import AlertStore
from alerter.src.data_store.store.github import GithubStore
from alerter.src.data_store.store.system import SystemStore

class StoreManager:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._system_store = SystemStore(self.logger)
        self._github_store = GithubStore(self.logger)
        self._alert_store = AlertStore(self.logger)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def system_store(self) -> SystemStore:
        return self._system_store
    
    @property
    def github_store(self) -> GithubStore:
        return self._github_store

    @property
    def alert_store(self) -> AlertStore:
        return self._alert_store
    
    """
        Starts all the store processes, these will initialize all the rabbitmq
        interfaces together with mongo client connections. All rabbit instances
        will then begin listening for incoming messages.

        Every 0.5 seconds the processes will be checked if they are alive,
        if not, the rabbitmq interfaces will re-initialize and start listening
        for changes again. If it fails to start, then it will re-attempt every
        10 seconds.
    """
    def start_store_manager(self) -> None:
        processes = []
        stores = [self.system_store, self.github_store, self.alert_store]
        for instance in stores:
            print("Initializing store")
            instance._initialize_store()
            process = Process(target=instance._start_listening, args=())
            process.start()
            print("Started process")
            processes.append((process, instance))

        while len(processes) > 0:
            for n in processes:
                (process, instance) = n
                sleep(0.5)
                if process.exitcode is None and not process.is_alive():
                    sleep(10)
                    process.join()
                    del processes[n]
                    print("Restart process after 10 seconds")
                # elif process.exitcode < 0:
                #     sleep(10)
                #     process.join()
                #     del processes[n]
                #     print("Restart process after 10 seconds")
                else:
                    process.join()
                    del processes[n]
                    print("Processes exited internally should be removed")
                    print("This shouldnt ever happen")