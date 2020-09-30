import os
import pika
import sys


# from alerter.src.utils.logging import DUMMY_LOGGER
# from alerter.src.data_store.mongo.mongo_api import MongoApi
# from alerter.src.data_store.redis.redis_api import RedisApi
#
#


#
#
# if __name__ == '__main__':
#     mongo_host = os.environ["DB_HOST"]
#     mongo_port = int(os.environ["DB_PORT"])
#     mongo_db = os.environ["DB_NAME"]
#     mongo_api = MongoApi(DUMMY_LOGGER, mongo_db, mongo_host, mongo_port)
#     print(mongo_api.get_all("installer_authentication"))
#     print(mongo_api.ping_unsafe())
#
#     redis_host = os.environ["REDIS_HOST"]
#     redis_port = int(os.environ["REDIS_PORT"])
#     redis_db = os.environ["REDIS_DB"]
#     redis_api = RedisApi(DUMMY_LOGGER, redis_db, redis_host, redis_port,
#                          namespace='test_alerter')
#     print(redis_api.set_multiple({'test_key': 'test_value'}))
#     print(redis_api.get('test_key'))
#     print(redis_api.ping_unsafe())
#     print("Before")
#     rabbit_host = os.environ["RABBIT_HOST"]
#     connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host))
#     channel = connection.channel()
#     channel.queue_declare(queue='hello')
#     channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
#     print(" [x] Sent 'Hello World!'")
#     connection2 = pika.BlockingConnection(
#         pika.ConnectionParameters(rabbit_host))
#     channel2 = connection2.channel()
#     channel2.queue_declare(queue='hello')
#     channel2.basic_consume(queue='hello', auto_ack=True, on_message_callback=callback)
#     channel2.start_consuming()
#
#     # In the API we need to always open a connection and close it
#     connection.close()

def main():
    rabbit_host = os.environ["RABBIT_HOST"]
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbit_host))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(queue='hello', on_message_callback=callback,
                          auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    connection.close()


if __name__ == '__main__':
    try:
        rabbit_host = os.environ["RABBIT_HOST"]
        print(rabbit_host)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))
        channel = connection.channel()
        channel.queue_declare(queue='hello')
        channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
        print(" [x] Sent 'Hello World!'")
        connection.close()
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
