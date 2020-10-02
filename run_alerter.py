import os
import pika
import pika.exceptions
import sys
import time


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

# Messages will be lost if a queue is not bound to an exchange


# TODO: Acknowledgements are important, but what happens if they are re-queud in
#       case a system fails? Is past data important? Maybe this is component
#       dependent? For monitors no but for channel manager yes for example

# If one consumer is present on the queue and the consumer dies, the messages
# are received in order.

# RabbitMQ does not let you create the same queue with different parameters.

# IMPORTANT: Becareful of buffers, always do flush

# Giving a queue a name is important when you want to sharethe queue between
# consumers and producers
if __name__ == '__main__':
    rabbit_host = "localhost"
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbit_host))
    channel = connection.channel()
    channel.confirm_delivery()
    channel.exchange_declare(exchange='topic_logs',
                             exchange_type='topic')
    try:
        channel.basic_publish(
            exchange='topic_logs', routing_key='black.cat', body='black cat',
            properties=pika.BasicProperties(delivery_mode=2,
                                            # make message persistent
                                            ), mandatory=True,
        )
        print('Message was published')
        channel.basic_publish(
            exchange='topic_logs', routing_key='black.mouse',
            body='black mouse',
            properties=pika.BasicProperties(delivery_mode=2,
                                            # make message persistent
                                            ), mandatory=True,
        )
        print('Message was published')
        channel.basic_publish(
            exchange='topic_logs', routing_key='white.cat', body='white cat',
            properties=pika.BasicProperties(delivery_mode=2,
                                            # make message persistent
                                            ),
        )
        time.sleep(10)
        print('Message was published')
        # Short time window where message not yet saved to disk and rabbitmq
        # stops. See publisher guarantees to solve this.
        channel.basic_publish(
            exchange='topic_logs', routing_key='white.mouse',
            body='white mouse',
            properties=pika.BasicProperties(delivery_mode=2,
                                            # make message persistent
                                            ),
        )
        print('Message was published')
    except pika.exceptions.UnroutableError:
        print('Message was returned')
    print(" [x] Sent Messages ")
    connection.close()

# TODO: May need to combine what we learned in acknowledgements tutorial with
#       direct/topic exchanges, even recovery (we might need to name queues)
# TODO: Basic consume in wrapper must take a function that needs to be computed
# TODO: QOS value should be between 100-300
# TODO: Publisher confirms
# TODO: Error handling in each function
# TODO: IMPORTANT: Error re-connection, qos, ack, mandatory true, topics etc,
#     : exception handling in each function
# TODO: Connection.close is imp
# TODO: For mandatory=true to work, the queue must already be bounded, no queue it will fail (so there must already be a consumer) mandatory=true will not fail if the message is delivered to the consumer .. without it it only confirms that it was delviered to the exchange
# TODO: Implement pika with authentication as well
