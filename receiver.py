import os
import pika
import logging
import sys
import time

from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi


def main():
    # Set durable to true so that if rabbitmq restarts the queue is not lost
    # channel.queue_declare(queue='task_queue', durable=True)

    rabbitAPI.exchange_declare(exchange='topic_logs', exchange_type='topic')
    # Queue is deleted when connection is closed by exclusive flag
    result = rabbitAPI.queue_declare(queue='test_queue', durable=True)
    # Bind queue to exchange, result.method.queue contains the randomly created queue name
    rabbitAPI.queue_bind(exchange='topic_logs',
                         queue=result.method.queue, routing_key='black.*')

    print(' [*] Waiting for messages. To exit press CTRL+C')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body.decode())
        time.sleep(10)
        # time.sleep(body.count(b'.'))
        print(" [x] Done")
        try:
            rabbitAPI.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            time.sleep(10)

    # By this code messages are deleted from rabbitmq when they are delivered
    # channel.basic_consume(queue='hello', on_message_callback=callback,
    #                       auto_ack=True)

    # # Do not send next message unless current has been acknowledged
    rabbitAPI.basic_qos(prefetch_count=2)
    # channel.basic_consume(queue='task_queue', on_message_callback=callback)

    rabbitAPI.basic_consume(
        queue=result.method.queue, on_message_callback=callback, auto_ack=False)

    rabbitAPI.start_consuming()
    # rabbitAPI.disconnect()


if __name__ == '__main__':
    while True:
        try:
            rabbitAPI = RabbitMQApi(logging.getLogger('Dummy'))
            rabbitAPI.connect()
            main()
            rabbitAPI.disconnect()
        except Exception:
            print('Interrupted')
            continue