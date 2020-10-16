import os
import pika
import pika.exceptions
import sys
import time
import logging
import multiprocessing as mp
from alerter.src.utils.logging import create_logger
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.data_store.store.manager import StoreManager

# TODO this file is to be removed after the alert_router is implemented
# together with the datastore, until then it is used to test the store
if __name__ == '__main__':
    DUMMY_LOGGER = logging.getLogger('dummy')
    store_manager = StoreManager(DUMMY_LOGGER)
    store_manager.start_store_manager()
    # # Initialize Mongo with environmental variables
    # mongo_host = os.environ["DB_IP"]
    # mongo_port = int(os.environ["DB_PORT"])
    # mongo_db = os.environ["DB_NAME"]
    # mongo_api = MongoApi(DUMMY_LOGGER, mongo_db, mongo_host, mongo_port)
    # print(mongo_api.get_all("installer_authentication"))
    # print(mongo_api.ping_unsafe())

    # # Initialize Redis with environmental variables
    redis_host = os.environ["REDIS_IP"]
    redis_port = int(os.environ["REDIS_PORT"])
    redis_db = os.environ["REDIS_DB"]
    redis_api = RedisApi(DUMMY_LOGGER, redis_db, redis_host, redis_port,
                         namespace='panic_alerter')
    # print(redis_api.set_multiple({'test_key': 'test_value'}))
    print(redis_api.get('gh1_'))
    print(redis_api.ping_unsafe())

    # # Testing rabbit with Rabbit Interface
    # rabbit_host = os.environ["RABBIT_IP"]
    # rabbitAPI = RabbitMQApi(DUMMY_LOGGER, rabbit_host)
    # rabbitAPI.connect()
    # rabbitAPI.confirm_delivery()

    # Create the datastore and begin listening to incoming requests from rabbit
    # system_store = SystemStore(DUMMY_LOGGER)
    # github_store = GithubStore(DUMMY_LOGGER)
    # alert_store = AlertStore(DUMMY_LOGGER)

    # system_store._initialize_rabbitmq()
    # github_store._initialize_rabbitmq()
    # alert_store._initialize_rabbitmq()

    # # Start individual proceses for these sexies
    # p1 = mp.Process(target=system_store._start_listening, args=())
    # p2 = mp.Process(target=github_store._start_listening, args=())
    # p3 = mp.Process(target=alert_store._start_listening, args=())

    # p1.start()
    # p2.start()
    # p3.start()
    # system_store._start_listening()
    # github_store._start_listening()
    # alert_store._start_listening()
