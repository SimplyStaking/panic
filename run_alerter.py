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

if __name__ == '__main__':
    # Logger initialisation
    logger_monitor_store = create_logger('logs/store_logger.log',
        'store_logger', 'DEBUG', rotating=True)

    store_manager = StoreManager(logger_monitor_store)

    process = Process(target=store_manager.start_store_manager,
        args=())
    process.daemon = False
    process.start()
    process.join()