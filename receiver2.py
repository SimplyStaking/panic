# import os
# import pika
# import sys
#
# from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
# from alerter.src.utils.logging import DUMMY_LOGGER
#
#
# def main():
#     # Set durable to true so that if rabbitmq restarts the queue is not lost
#     # channel.queue_declare(queue='task_queue', durable=True)
#
#     rabbitAPI.exchange_declare(exchange='topic_logs', exchange_type='topic')
#     # Queue is deleted when connection is closed by exclusive flag
#     result = rabbitAPI.queue_declare(queue='', exclusive=True)
#     # Bind queue to exchange, result.method.queue contains the randomly created queue name
#     rabbitAPI.queue_bind(exchange='topic_logs',
#                          queue=result.method.queue, routing_key='white.*')
#
#     print(' [*] Waiting for messages. To exit press CTRL+C')
#
#     def callback(ch, method, properties, body):
#         print(" [x] Received %r" % body.decode())
#         # time.sleep(body.count(b'.'))
#         # print(" [x] Done")
#         # ch.basic_ack(delivery_tag=method.delivery_tag)
#
#     # By this code messages are deleted from rabbitmq when they are delivered
#     # channel.basic_consume(queue='hello', on_message_callback=callback,
#     #                       auto_ack=True)
#
#     # # Do not send next message unless current has been acknowledged
#     # channel.basic_qos(prefetch_count=1)
#     # channel.basic_consume(queue='task_queue', on_message_callback=callback)
#
#     rabbitAPI.basic_consume(
#         queue=result.method.queue, on_message_callback=callback, auto_ack=True)
#
#     rabbitAPI.start_consuming()
#     rabbitAPI.disconnect()
#
#
# if __name__ == '__main__':
#     try:
#         rabbitAPI = RabbitMQApi(DUMMY_LOGGER)
#         rabbitAPI.connect()
#         main()
#         rabbitAPI.disconnect()
#     except KeyboardInterrupt:
#         print('Interrupted')
#         try:
#             sys.exit(0)
#         except SystemExit:
#             os._exit(0)
from alerter.src.utils.data import *
from alerter.src.utils.logging import DUMMY_LOGGER

metrics_to_monitor = ['process_cpu_seconds_total',
                              'go_memstats_alloc_bytes',
                              'go_memstats_alloc_bytes_total',
                              'process_virtual_memory_bytes',
                              'process_max_fds',
                              'process_open_fds',
                              'node_cpu_seconds_total',
                              'node_filesystem_avail_bytes',
                              'node_filesystem_size_bytes',
                              'node_memory_MemTotal_bytes',
                              'node_memory_MemAvailable_bytes']
data = get_prometheus_metrics_data('http://172.16.152.35:9100/metrics', metrics_to_monitor, DUMMY_LOGGER)
node_cpu_seconds_idle = 0
node_cpu_seconds_total = 0
node_filesystem_avail_bytes = 0
node_filesystem_size_bytes = 0
print(data['node_filesystem_avail_bytes'])
print(data['node_filesystem_size_bytes'])
for i, j in enumerate(data['node_filesystem_avail_bytes']):
    node_filesystem_avail_bytes += \
        data['node_filesystem_avail_bytes'][j]

for i, j in enumerate(data['node_filesystem_size_bytes']):
    node_filesystem_size_bytes += \
        data['node_filesystem_size_bytes'][j]
print(node_cpu_seconds_idle)
print(node_cpu_seconds_total)