import logging
from datetime import timedelta
from typing import Dict, List, Optional, Any

from pymongo import MongoClient
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult

from alerter.src.utils.timing import TimedTaskLimiter
from alerter.src.utils.logging import log_and_print


class MongoApi:
    def __init__(self, logger: logging.Logger, db_name: str,
                 host: str = 'localhost', port: int = 27017,
                 username: str = '', password: str = '',
                 live_check_time_interval: timedelta = timedelta(seconds=60),
                 timeout_ms: int = 10000) \
            -> None:
        self._logger = logger
        self._db_name = db_name
        if password == '':
            self._client = MongoClient(
                host=host, port=port, connectTimeoutMS=timeout_ms,
                socketTimeoutMS=timeout_ms, serverSelectionTimeoutMS=timeout_ms)
        else:
            self._client = MongoClient(
                host=host, port=port, connectTimeoutMS=timeout_ms,
                socketTimeoutMS=timeout_ms, serverSelectionTimeoutMS=timeout_ms,
                username=username, password=password)

        # The live check limiter means that we don't wait for connection
        # errors to occur to be able to continue, thus speeding everything up
        self._live_check_limiter = TimedTaskLimiter(live_check_time_interval)
        self._is_live = True  # This is necessary to initialise the variable
        self._set_as_live()

        self._logger.info('Mongo initialised.')

    @property
    def _db(self):
        return self._client[self._db_name]

    @property
    def is_live(self) -> bool:
        return self._is_live

    def _set_as_live(self) -> None:
        if not self._is_live:
            self._logger.info('Mongo is now accessible again.')
        self._is_live = True

    def _set_as_down(self) -> None:
        # If Mongo is live or if we can check whether it is live (because the
        # live check time interval has passed), reset the live check limiter
        # so that usage of Mongo is skipped for as long as the time interval
        if self._is_live or self._live_check_limiter.can_do_task():
            self._live_check_limiter.did_task()
            self._logger.warning('Mongo is unusable for some reason. Stopping '
                                 'usage temporarily to improve performance.')
        self._is_live = False

    def _do_not_use_if_recently_went_down(self) -> bool:
        # If Mongo is not live and cannot check if it is live return true
        return not self._is_live and not self._live_check_limiter.can_do_task()

    def _safe(self, function, args: List[Any], default_return: Any):
        # Calls the function with the provided arguments and performs exception
        # handling as well as returns a specified default if mongo is running
        # into difficulties. Exceptions are raised to the calling function.
        try:
            if self._do_not_use_if_recently_went_down():
                return default_return
            ret = function(*args)
            self._set_as_live()
            return ret
        except Exception as e:
            self._logger.error('Mongo error in %s: %s', function.__name__, e)
            self._set_as_down()
            return default_return

    def insert_one(self, collection: str, document: Dict) \
            -> Optional[InsertOneResult]:
        return self._safe(
            lambda col, doc: self._db[col].insert_one(doc),
            [collection, document], None)

    def insert_many(self, collection: str, documents: List[Dict]) \
            -> Optional[InsertManyResult]:
        return self._safe(
            lambda col, doc: self._db[col].insert_many(doc),
            [collection, documents], None)

    def update_one(self, collection: str, query: Dict, document: Dict) \
          -> Optional[UpdateResult]:
        return self._safe(
            lambda col, q, doc: self._db[col].update_one(q, doc, upsert=True),
                [collection, query, document], None)

    def get_all(self, collection: str) -> Optional[List[Dict]]:
        return self._safe(
            lambda col: list(self._db[col].find({})),
            [collection], None)

    def drop_collection(self, collection: str) -> Optional[Dict]:
        return self._safe(
            lambda col: self._db.drop_collection(col),
            [collection], None)

    def drop_db(self) -> None:
        return self._safe(
            lambda: self._client.drop_database(self._db.name),
            [], None)

    def ping_unsafe(self):
        return self._db.command('ping')

    def ping_auth(self, username: str, password: str):
        return self._db.authenticate(username, password, "admin")
