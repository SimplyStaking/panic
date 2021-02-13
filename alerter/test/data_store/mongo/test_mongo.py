import logging
import unittest
from datetime import timedelta
from time import sleep

from pymongo.errors import PyMongoError, OperationFailure, \
    ServerSelectionTimeoutError

from src.data_store.mongo.mongo_api import MongoApi
from src.utils import env


class TestMongoApiWithMongoOnline(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # Same as in setUp(), to avoid running all tests if Mongo is offline

        dummy_dummy_logger = logging.getdummy_logger('dummy')
        dummy_dummy_logger.disabled = True
        db = env.DB_NAME
        host = env.DB_IP
        port = env.DB_PORT
        user = ''
        password = ''
        mongo = MongoApi(logger=dummy_logger, db_name=db,
                         host=host, port=port, username=user,
                         password=password)

        # Ping Mongo
        try:
            mongo.ping_unsafe()
        except PyMongoError:
            raise Exception('Mongo is not online.')

    def setUp(self) -> None:
        self.dummy_logger = logging.getdummy_logger('dummy')
        self.dummy_dummy_logger.disabled = True
        self.db = env.DB_NAME
        self.host = env.DB_IP
        self.port = env.DB_PORT
        self.user = ''
        self.password = ''
        self.mongo = MongoApi(logger=self.dummy_logger,
                              db_name=self.db, host=self.host,
                              port=self.port,
                              username=self.user, password=self.password)

        # Ping Mongo
        try:
            self.mongo.ping_unsafe()
        except PyMongoError:
            self.fail('Mongo is not online.')

        # Clear test database
        self.mongo.drop_db()

        self.col1 = 'collection1'
        self.col2 = 'collection2'

        self.val1 = {'a': 'b', 'c': 'd'}
        self.val2 = {'e': 'f', 'g': 'h'}
        self.val3 = {'i': 'j'}
        self.val4 = {'k': 'l', 'm': {'n': ['o', 'p', True, False, 1, 2.1]}}

        self.time = timedelta(seconds=3)
        self.time_with_error_margin = timedelta(seconds=4)

        self.default_str = 'DEFAULT'
        self.default_int = 789
        self.default_bool = False

    def tearDown(self) -> None:
        self.mongo.drop_db()

    def test_insert_one_inserts_value_into_the_specified_collection(self):
        # Check that col1 is empty
        get_result = list(self.mongo._db[self.col1].find({}))
        self.assertEqual(len(get_result), 0)

        # Insert val1 into col1
        self.mongo.insert_one(self.col1, self.val1)

        # Check that value was added to col1
        get_result = list(self.mongo._db[self.col1].find({}))
        self.assertEqual(len(get_result), 1)
        self.assertEqual(dict(get_result[0]), self.val1)

    def test_insert_one_supports_more_complex_documents(self):
        # Check that col1 is empty
        get_result = list(self.mongo._db[self.col1].find({}))
        self.assertEqual(len(get_result), 0)

        # Insert val4 into col1
        self.mongo.insert_one(self.col1, self.val4)

        # Check that value was added to col1
        get_result = list(self.mongo._db[self.col1].find({}))
        self.assertEqual(len(get_result), 1)
        self.assertEqual(dict(get_result[0]), self.val4)

    def test_insert_many_inserts_all_values_into_the_specified_collection(self):
        # Check that col1 is empty
        get_result = list(self.mongo._db[self.col1].find({}))
        self.assertEqual(len(get_result), 0)

        # Insert val1, val2, and val3 into col1
        self.mongo.insert_many(self.col1, [self.val1, self.val2, self.val3])

        # Check that the values was added to col1
        get_result = list(self.mongo._db[self.col1].find({}))
        self.assertEqual(len(get_result), 3)
        self.assertEqual(dict(get_result[0]), self.val1)
        self.assertEqual(dict(get_result[1]), self.val2)
        self.assertEqual(dict(get_result[2]), self.val3)

    def test_get_all_returns_inserted_values_in_order_of_insert(self):
        # Check that col1 is empty
        get_result = self.mongo.get_all(self.col1)
        self.assertEqual(len(get_result), 0)

        # Insert val1, val2, and val3 into col1
        self.mongo._db[self.col1].insert_many([self.val1, self.val2, self.val3])

        # Check that the values was added to col1
        get_result = self.mongo.get_all(self.col1)
        self.assertEqual(len(get_result), 3)
        self.assertEqual(dict(get_result[0]), self.val1)
        self.assertEqual(dict(get_result[1]), self.val2)
        self.assertEqual(dict(get_result[2]), self.val3)

    def test_drop_collection_deletes_the_specified_collection(self):
        # Check that col1 and col2 are empty
        get_result1 = list(self.mongo._db[self.col1].find({}))
        get_result2 = list(self.mongo._db[self.col2].find({}))
        self.assertEqual(len(get_result1), 0)
        self.assertEqual(len(get_result2), 0)

        # Insert val1, val2, and val3 into col1 and val4 into col2
        self.mongo._db[self.col1].insert_many([self.val1, self.val2, self.val3])
        self.mongo._db[self.col2].insert_one(self.val4)

        # Check that col1 and col2 are not empty
        get_result1 = list(self.mongo._db[self.col1].find({}))
        get_result2 = list(self.mongo._db[self.col2].find({}))
        self.assertEqual(len(get_result1), 3)
        self.assertEqual(len(get_result2), 1)

        # Delete col1
        self.mongo.drop_collection(self.col1)

        # Check that col1 is back to being empty but col2 is not empty
        get_result1 = list(self.mongo._db[self.col1].find({}))
        get_result2 = list(self.mongo._db[self.col2].find({}))
        self.assertEqual(len(get_result1), 0)
        self.assertEqual(len(get_result2), 1)

    def test_drop_db_deletes_all_collections(self):
        # Check that col1 and col2 are empty
        get_result1 = list(self.mongo._db[self.col1].find({}))
        get_result2 = list(self.mongo._db[self.col2].find({}))
        self.assertEqual(len(get_result1), 0)
        self.assertEqual(len(get_result2), 0)

        # Insert val1, val2, and val3 into col1 and val4 into col2
        self.mongo._db[self.col1].insert_many([self.val1, self.val2, self.val3])
        self.mongo._db[self.col2].insert_one(self.val4)

        # Check that col1 and col2 are not empty
        get_result1 = list(self.mongo._db[self.col1].find({}))
        get_result2 = list(self.mongo._db[self.col2].find({}))
        self.assertEqual(len(get_result1), 3)
        self.assertEqual(len(get_result2), 1)

        # Drop db
        self.mongo.drop_db()

        # Check that col1 and col2 are back to being empty
        get_result1 = list(self.mongo._db[self.col1].find({}))
        get_result2 = list(self.mongo._db[self.col2].find({}))
        self.assertEqual(len(get_result1), 0)
        self.assertEqual(len(get_result2), 0)

    def test_ping_returns_true(self):
        self.assertTrue(self.mongo.ping_unsafe())

    def test_ping_auth_throws_value_error_for_empty_password(self):
        try:
            self.mongo.ping_auth(self.user, '')
            self.fail('Expected ValueError exception to be thrown.')
        except:
            pass

    def test_ping_auth_throws_operation_failure_for_wrong_password(self):
        try:
            self.mongo.ping_auth(self.user, 'incorrect_password')
            self.fail('Expected OperationFailure exception to be thrown.')
        except OperationFailure:
            pass


class TestMongoApiWithMongoOffline(unittest.TestCase):

    def setUp(self) -> None:
        self.dummy_logger = logging.getdummy_logger('dummy')
        self.db = TestUserConf.mongo_db_name
        self.host = 'dummyhost'
        self.port = TestUserConf.mongo_port
        self.user = TestUserConf.mongo_user
        self.password = TestUserConf.mongo_pass
        self.mongo = MongoApi(self.dummy_logger, self.db, self.host, self.port,
                              timeout_ms=1)
        # timeout_ms is set to 1ms to speed up tests. It cannot be 0 :p

        self.col1 = 'collection1'
        self.val1 = {'a': 'b', 'c': 'd'}
        self.val2 = {'e': 'f', 'g': 'h'}
        self.val3 = {'i': 'j'}

    def test_insert_one_throws_exception_first_time_round(self):
        try:
            self.mongo.insert_one(self.col1, self.val1)
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_insert_many_throws_exception_first_time_round(self):
        try:
            self.mongo.insert_many(self.col1, [self.val1, self.val2, self.val3])
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_get_all_throws_exception_first_time_round(self):
        try:
            self.mongo.get_all(self.col1)
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_drop_collection_throws_exception_first_time_round(self):
        try:
            self.mongo.drop_collection(self.col1)
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_drop_db_throws_exception_first_time_round(self):
        try:
            self.mongo.drop_db()
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_ping_unsafe_throws_exception_first_time_round(self):
        try:
            self.mongo.ping_unsafe()
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_ping_auth_throws_exception_first_time_round(self):
        try:
            self.mongo.ping_auth(username=self.user, password=self.password)
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_insert_one_returns_none_if_mongo_already_down(self):
        self.mongo._set_as_down()
        self.assertIsNone(self.mongo.insert_one(self.col1, self.val1))

    def test_insert_many_returns_none_if_mongo_already_down(self):
        self.mongo._set_as_down()
        documents = [self.val1, self.val2, self.val3]
        self.assertIsNone(self.mongo.insert_many(self.col1, documents))

    def test_get_all_returns_none_if_mongo_already_down(self):
        self.mongo._set_as_down()
        self.assertIsNone(self.mongo.get_all(self.col1))

    def test_drop_collection_returns_none_if_mongo_already_down(self):
        self.mongo._set_as_down()
        self.assertIsNone(self.mongo.drop_collection(self.col1))

    def test_drop_db_returns_none_if_mongo_already_down(self):
        self.mongo._set_as_down()
        self.assertIsNone(self.mongo.drop_db())

    def test_ping_unsafe_throws_exception_if_mongo_already_down(self):
        self.mongo._set_as_down()
        try:
            self.mongo.ping_unsafe()
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass

    def test_ping_auth_throws_exception_if_mongo_already_down(self):
        self.mongo._set_as_down()
        try:
            self.mongo.ping_auth(username=self.user, password=self.password)
            self.fail('Expected ServerSelectionTimeoutError to be thrown.')
        except ServerSelectionTimeoutError:
            pass


class TestMongoApiLiveAndDownFeaturesWithMongoOffline(unittest.TestCase):

    def setUp(self) -> None:
        self.dummy_logger = logging.getdummy_logger('dummy')
        self.db = TestUserConf.mongo_db_name
        self.host = TestUserConf.mongo_host
        self.port = TestUserConf.mongo_port
        self.live_check_time_interval = timedelta(seconds=3)
        self.live_check_time_interval_with_error_margin = timedelta(seconds=3.5)
        self.mongo = MongoApi(self.dummy_logger, self.db, self.host, self.port,
                              live_check_time_interval=
                              self.live_check_time_interval)

    def test_is_live_returns_true_by_default(self):
        self.assertTrue(self.mongo.is_live)

    def test_set_as_live_changes_is_live_to_true(self):
        self.mongo._is_live = False
        self.assertFalse(self.mongo.is_live)

        self.mongo._set_as_live()
        self.assertTrue(self.mongo._is_live)

    def test_set_as_live_leaves_is_live_as_true_if_already_true(self):
        self.mongo._is_live = True
        self.assertTrue(self.mongo.is_live)

        self.mongo._set_as_live()
        self.assertTrue(self.mongo._is_live)

    def test_set_as_down_changes_is_live_to_false(self):
        self.mongo._set_as_down()
        self.assertFalse(self.mongo.is_live)

    def test_set_as_down_leaves_is_live_as_false_if_already_false(self):
        self.mongo._is_live = False
        self.assertFalse(self.mongo.is_live)

        self.mongo._set_as_down()
        self.assertFalse(self.mongo.is_live)

    def test_allowed_to_use_by_default(self):
        # noinspection PyBroadException
        try:
            self.mongo._do_not_use_if_recently_went_down()
        except Exception:
            self.fail('Expected to be allowed to use Mongo.')

    def test_not_allowed_to_use_if_set_as_down_and_within_time_interval(self):
        self.mongo._set_as_down()
        # noinspection PyBroadException
        try:
            self.mongo._do_not_use_if_recently_went_down()
            self.fail('Expected to not be allowed to use Mongo.')
        except Exception:
            pass

    def test_allowed_to_use_if_set_as_down_and_within_time_interval(self):
        self.mongo._set_as_down()
        sleep(self.live_check_time_interval_with_error_margin.seconds)
        # noinspection PyBroadException
        try:
            self.mongo._do_not_use_if_recently_went_down()
        except Exception:
            self.fail('Expected to be allowed to use Mongo.')
