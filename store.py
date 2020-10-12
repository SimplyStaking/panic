import os
import pika
import pika.exceptions
import sys
import time

from configparser import ConfigParser
from alerter.src.utils.logging import DUMMY_LOGGER
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

if __name__ == '__main__':
    # Testing rabbit with Rabbit Interface
    rabbit_host = os.environ["RABBIT_HOST"]
    rabbitAPI = RabbitMQApi(DUMMY_LOGGER, rabbit_host)
    rabbitAPI.connect()
    rabbitAPI.confirm_delivery()
    rabbitAPI.exchange_declare(exchange='config', exchange_type='topic')

    try:
        # Load the configuration file.
        config = ConfigParser()
        config.read('config/channels/email_config.ini')
        config_dict = {key: dict(config[key]) for key in config}
        config_dict.pop('DEFAULT', None)
        rabbitAPI.basic_publish_confirm(
            exchange='config', routing_key='config.email', body=config_dict,
            mandatory=True
        )
        # print('Message was published')
    except pika.exceptions.UnroutableError:
        print('Message was returned')
    print(" [x] Sent Messages ")
    rabbitAPI.disconnect()