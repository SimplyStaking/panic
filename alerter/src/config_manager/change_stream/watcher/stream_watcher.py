import logging
from time import sleep
from src.data_store.mongo import MongoApi


class StreamWatcher:
    """
    Watcher Manager for Mongo Change Stream
    """
    _mongo: MongoApi = None
    _db_name: str = None
    _stop: bool = True
    _logger: logging.Logger = None

    def __init__(self, mongo: MongoApi, logger: logging.Logger) -> None:

        self._db_name = mongo.db_name

        if self._db_name is None:
            raise RuntimeError("Please, inform the database name")

        self._mongo = mongo
        self._logger = logger

    def watch(self, collection: str, callback=None, token: str = None) -> None:
        """ 
        Watch tool for MongoDB change stream

        Args:
            collection (str): The name of aimed collection
            callback : The callback 
            token (str, optional): The OpLOG resume token given by MongoDB

        Raises:
            Exception: A PyMongoError which tries to reconnect again each 10s

        Returns:
            CollectionChangeStream: The MongoDb Change Stream
        """

        try:

            self._stop = True

            if callback is None:
                raise Exception(
                    'Please send a callback to consume the change stream!')

            watch = self._mongo.watch(collection, token)
            with watch as stream:

                # ensure that each consumes confirms
                self._stop = False
                
                info = 'Now watching the {} collection on database {}'.format(
                    collection.upper(), self._db_name.upper())
                
                self._logger.info(info)

                for change in stream:

                    # unwatch
                    if self._stop:
                        self._logger.info('Unwatching Change Stream...')
                        stream.close()
                        self._stop = True

                    # execute task
                    callback(change, self._mongo)

                    # token from oplog MongoDB
                    token = stream.resume_token

            # stop without Error
            self._stop = True

        except Exception as e:

            self._logger.exception(e)
            # wait for fixed connection or others issues
            self._stop = True
            sleep(10)
            self.watch(collection, callback, token)            

    def unwatch(self) -> None:
        """
        Stops the current watcher
        """
        self._stop = True

    def is_alive(self) -> bool:
        """
        Stops the current watcher
        """
        return not self._stop
