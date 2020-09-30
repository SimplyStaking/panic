import os
import pika


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


rabbit_host = "192.168.10.57"
connection2 = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host))
channel2 = connection2.channel()
channel2.queue_declare(queue='hello')
channel2.basic_consume(queue='hello', auto_ack=True,
                       on_message_callback=callback)
channel2.start_consuming()
