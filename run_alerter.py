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
from alerter.src.data_store.stores.manager import StoreManager
from alerter.src.utils.logging import log_and_print

def _initialize_data_store_logger(data_store_name: str) -> logging.Logger:
    # Try initializing the logger until successful. This had to be done
    # separately to avoid instances when the logger creation failed and we
    # attempt to use it.
    while True:
        try:
            data_store_logger = create_logger(
                os.environ["DATA_STORE_LOG_FILE_TEMPLATE"].format( \
                    data_store_name),
                data_store_name, os.environ["LOGGING_LEVEL"], rotating=True)
            break
        except Exception as e:
            msg = '!!! Error when initialising {}: {} !!!' \
                .format(data_store_name, e)
            # Use a dummy logger in this case because we cannot create the
            # managers's logger.
            log_and_print(msg, logging.getLogger('DUMMY_LOGGER'))
            log_and_print('Re-attempting the initialization procedure',
                          logging.getLogger('DUMMY_LOGGER'))
            time.sleep(10)  # sleep 10 seconds before trying again

    return data_store_logger

def run_data_store() -> None:
    store_logger =_initialize_data_store_logger('data_store')

    store_manager = StoreManager(store_logger)
    store_manager.start_store_manager()


if __name__ == '__main__':

    store_process = Process(target=run_data_store, args=())
    store_process.start()
    store_process.join()