import os
from alerter.src.utils.logging import DUMMY_LOGGER
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi


if __name__ == '__main__':
    mongo_host = os.environ["DB_HOST"]
    mongo_port = int(os.environ["DB_PORT"])
    mongo_db = os.environ["DB_NAME"]
    mongo_api = MongoApi(DUMMY_LOGGER, mongo_db, mongo_host, mongo_port)
    print(mongo_api.get_all("installer_authentication"))
    print(mongo_api.ping_unsafe())

    redis_host = os.environ["REDIS_HOST"]
    redis_port = int(os.environ["REDIS_PORT"])
    redis_db = os.environ["REDIS_DB"]
    redis_api = RedisApi(DUMMY_LOGGER, redis_db, redis_host, redis_port,
                         namespace='test_alerter')
    print(redis_api.set_multiple({'test_key': 'test_value'}))
    print(redis_api.get('test_key'))
    print(redis_api.ping_unsafe())
