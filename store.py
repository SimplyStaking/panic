import os
import pika
import pika.exceptions
import sys
import time

from alerter.src.utils.logging import DUMMY_LOGGER
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

if __name__ == '__main__':

    # Testing rabbit
    # Sending message through RABBIT
    rabbit_host = os.environ["RABBIT_HOST"]
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host))
    channel = connection.channel()
    channel.queue_declare(queue='hello')
    channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
    print(" [x] Sent 'Hello World!'")
    connection.close()

    # Receving message from RABBIT
    connection2 = pika.BlockingConnection(
        pika.ConnectionParameters(rabbit_host))
    channel2 = connection2.channel()
    channel2.queue_declare(queue='hello')
    channel2.basic_consume(queue='hello', auto_ack=True, on_message_callback=callback)
    channel2.start_consuming()

    # In the API we need to always open a connection and close it
    connection2.close()