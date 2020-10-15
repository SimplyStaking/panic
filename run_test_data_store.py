import os
import pika
import pika.exceptions
import sys
import time

from alerter.src.utils.logging import DUMMY_LOGGER
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.data_store.store.store import Store

# TODO this file is to be removed after the alert_router is implemented
# together with the datastore, until then it is used to test the store
if __name__ == '__main__':
    # Initialize Mongo with environmental variables
    mongo_host = os.environ["DB_HOST"]
    mongo_port = int(os.environ["DB_PORT"])
    mongo_db = os.environ["DB_NAME"]
    mongo_api = MongoApi(DUMMY_LOGGER, mongo_db, mongo_host, mongo_port)
    print(mongo_api.get_all("installer_authentication"))
    print(mongo_api.ping_unsafe())

    # Initialize Redis with environmental variables
    redis_host = os.environ["REDIS_HOST"]
    redis_port = int(os.environ["REDIS_PORT"])
    redis_db = os.environ["REDIS_DB"]
    redis_api = RedisApi(DUMMY_LOGGER, redis_db, redis_host, redis_port,
                         namespace='test_alerter')
    print(redis_api.set_multiple({'test_key': 'test_value'}))
    print(redis_api.get('test_key'))
    print(redis_api.ping_unsafe())

    # Testing rabbit with Rabbit Interface
    rabbit_host = os.environ["RABBIT_HOST"]
    rabbitAPI = RabbitMQApi(DUMMY_LOGGER, rabbit_host)
    rabbitAPI.connect()
    rabbitAPI.confirm_delivery()

    # Create the datastore and begin listening to incoming requests from rabbit
    store = Store(DUMMY_LOGGER, redis_api, mongo_api, rabbitAPI)
    store.start_store()