import os
import pika
import pika.exceptions
import sys
import time
import logging
from multiprocessing import Process
from alerter.src.utils.logging import create_logger
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.data_store.store.manager import StoreManager
from alerter.src.utils.logging import log_and_print

def run_data_store() -> None:
    store_logger = create_logger('logs/store_logs.log', 'data_store', 'INFO',
        rotating=True)

    store_manager = StoreManager(store_logger)
    store_manager.start_store_manager()


if __name__ == '__main__':

    store_process = Process(target=run_data_store, args=())
    store_process.daemon = False
    store_process.start()
    store_process.join()