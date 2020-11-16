import os
import pika
import time
import sys
import logging

from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi


def main():
    # Set durable to true so that if rabbitmq restarts the queue is not lost
    # channel.queue_declare(queue='task_queue', durable=True)

    rabbitAPI.exchange_declare(exchange='topic_logs', exchange_type='topic')

    rabbitAPI.basic_publish_confirm('topic_logs', 'black.hello', '1 message', properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
    rabbitAPI.basic_publish_confirm('topic_logs', 'black.hello', '2 message', properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
    rabbitAPI.basic_publish_confirm('topic_logs', 'black.hello', '3 message', properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
    rabbitAPI.basic_publish_confirm('topic_logs', 'black.hello', '4 message',
                                    properties=pika.BasicProperties(
                                        delivery_mode=2), mandatory=True)


if __name__ == '__main__':
    try:
        rabbitAPI = RabbitMQApi(logging.getLogger("Dummy"))
        rabbitAPI.connect_till_successful()
        main()
        rabbitAPI.disconnect()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)