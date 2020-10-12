import os
import pika
import pika.exceptions
import sys
import time

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
    rabbitAPI.exchange_declare(exchange='topic_logs', exchange_type='topic')
    # Queue is deleted when connection is closed by exclusive flag
    result = rabbitAPI.queue_declare(queue='', exclusive=True)

    # Bind queue to exchange, result.method.queue contains the randomly created queue name
    rabbitAPI.queue_bind(exchange='topic_logs',
                         queue=result.method.queue, routing_key='black.*')
    rabbitAPI.basic_consume(
      queue=result.method.queue, on_message_callback=callback, auto_ack=True)

    rabbitAPI.start_consuming()
    rabbitAPI.disconnect()