import logging
import json

# # # consumer
# def main():
#     # Set durable to true so that if rabbitmq restarts the queue is not lost
#     # channel.queue_declare(queue='task_queue', durable=True)
#
#     monitor.rabbitmq.exchange_declare('raw_data', 'direct', False, True, False, False)
#     # Queue is deleted when connection is closed by exclusive flag
#     result = monitor.rabbitmq.queue_declare(queue='', exclusive=True)
#     # Bind queue to exchange, result.method.queue contains the randomly created queue name
#     monitor.rabbitmq.queue_bind(exchange='raw_data', queue=result.method.queue, routing_key='system')
#
#     print(' [*] Waiting for messages. To exit press CTRL+C')
#
#     def callback(ch, method, properties, body):
#         print(" [x] Received %r" % json.loads(body))
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
#     monitor.rabbitmq.basic_consume(
#         queue=result.method.queue, on_message_callback=callback, auto_ack=True)
#
#     monitor.rabbitmq.start_consuming()
#
#
# if __name__ == '__main__':
#     system = System('test_system', 'http://172.16.152.36:9100/metrics',
#                     SystemType.BLOCKCHAIN_NODE_SYSTEM, 'test_chain')
#     redis = RedisApi(DUMMY_LOGGER, 10)
#     monitor = SystemMonitor('test_monitor', system, DUMMY_LOGGER, redis)
#     monitor.rabbitmq.connect_till_successful()
#     main()
#
#
# # publisher
# system = System('test_system', 'http://172.16.152.36:9100/metrics',
#                 SystemType.BLOCKCHAIN_NODE_SYSTEM, 'test_chain')
# redis = RedisApi(DUMMY_LOGGER, 10)
# monitor = SystemMonitor('test_monitor', system, DUMMY_LOGGER, redis)
# monitor.rabbitmq.connect_till_successful()
# monitor.rabbitmq.confirm_delivery()
# monitor.rabbitmq.exchange_declare('raw_data', 'direct', False, True, False,
#                                   False)
# monitor.send_data()

from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
import pika
import sys

DUMMY_LOGGER = logging.getLogger('dummy')
rabbit_api = RabbitMQApi(DUMMY_LOGGER, '172.18.0.6')
# config = {
#     'system_57bd37d6-5829-4f7d-85d8-3643eec50d2b': {
#         'id': 'system_57bd37d6-5829-4f7d-85d8-3643eec50d2b',
#         'parent_id': 'GLOBAL',
#         'name': 'system_1',
#         'exporter_url': 'http://172.16.152.36:9100/metrics',
#         'monitor_system': True,
#     },
#     'system_5675765-5829-4f7d-85d8-9d8fghd8ghdf8': {
#         'id': 'system_5675765-5829-4f7d-85d8-9d8fghd8ghdf8',
#         'parent_id': 'GLOBAL',
#         'name': 'system_3',
#         'exporter_url': 'http://172.16.151.31:9100/metrics',
#         'monitor_system': False,
#     },
# }
config1 = {
    'system_57bd37d6-5829-cosmos1-85d8-3643eec50d2b': {
        'id': 'system_57bd37d6-5829-cosmos1-85d8-3643eec50d2b',
        'parent_id': 'COSMOS',
        'name': 'system_COSMOS_1',
        'exporter_url': 'http://172.16.152.36:9100/metrics',
        'monitor_system': True,
    },
}
config2 = {
    'system_57bd37d6-5829-substrate1-85d8-3643eec50d2b': {
        'id': 'system_57bd37d6-5829-substrate1-85d8-3643eec50d2b',
        'parent_id': 'SUBSTRATE',
        'name': 'system_SUBSTRATE_1',
        'exporter_url': 'http://172.16.152.36:9100/metrics',
        'monitor_system': True,
    },
    'system_57bd37d6-5829-substrate2-85d8-3643eec50d2b': {
        'id': 'system_57bd37d6-5829-substrate2-85d8-3643eec50d2b',
        'parent_id': 'SUBSTRATE',
        'name': 'system_SUBSTRATE_2',
        'exporter_url': 'http://172.16.151.31:9100/metrics',
        'monitor_system': True,
    },
}
rabbit_api.connect_till_successful()
rabbit_api.confirm_delivery()
rabbit_api.exchange_declare('config', 'topic', False, True, False, False)
rabbit_api.queue_declare('monitor_manager_configs_queue', False, True, False, False)
rabbit_api.exchange_declare('raw_data', 'direct', False, True, False, False)
result = rabbit_api.queue_declare(queue='', exclusive=True)
rabbit_api.queue_bind(exchange='raw_data', queue=result.method.queue,
                      routing_key='system')
# rabbit_api.basic_publish_confirm('config', 'general.systems_config.ini', config,
#                                  True, pika.BasicProperties(delivery_mode=2),
#                                  True)
# rabbit_api.basic_publish_confirm('config', 'chains.cosmos.akala.systems_config.ini', config1,
#                                  True, pika.BasicProperties(delivery_mode=2),
#                                  True)
rabbit_api.basic_publish_confirm('config', 'chains.substrate.polkadot.systems_config.ini', config2,
                                 True, pika.BasicProperties(delivery_mode=2),
                                 True)

print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] Received %r" % json.loads(body))
    sys.stdout.flush()


rabbit_api.basic_consume(queue=result.method.queue,
                         on_message_callback=callback, auto_ack=True)
rabbit_api.start_consuming()
