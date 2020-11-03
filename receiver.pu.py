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
rabbit_api = RabbitMQApi(DUMMY_LOGGER, host='localhost')
config = {
    'system_57bd37d6-5829-4f7d-85d8-3643eec50d2b': {
        'id': 'system_57bd37d6-5829-4f7d-85d8-3643eec50d2b',
        'parent_id': 'Cosmos',
        'name': 'test_system_1',
        'exporter_url': 'http://172.16.152.36:9100/metrics',
        'monitor_system': True,
    },
    'system_5675765-5829-4f7d-85d8-9d8fghd8ghdf8': {
        'id': 'system_5675765-5829-4f7d-85d8-9d8fghd8ghdf8',
        'parent_id': 'Cosmos',
        'name': 'test_system_2',
        'exporter_url': 'http://172.16.151.31:9100/metrics',
        'monitor_system': True,
    },
}
# config1 = {
#     'system_57bd37d6-5829-cosmos1-85d8-3643eec50d2b': {
#         'id': 'system_57bd37d6-5829-cosmos1-85d8-3643eec50d2b',
#         'parent_id': 'COSMOS',
#         'name': 'system_COSMOS_1',
#         'exporter_url': 'http://172.16.152.36:9100/metrics',
#         'monitor_system': True,
#     },
# }
# config2 = {
#     'system_57bd37d6-5829-substrate1-85d8-3643eec50d2b': {
#         'id': 'system_57bd37d6-5829-substrate1-85d8-3643eec50d2b',
#         'parent_id': 'SUBSTRATE',
#         'name': 'system_SUBSTRATE_1',
#         'exporter_url': 'http://172.16.152.36:9100/metrics',
#         'monitor_system': True,
#     },
#     'system_57bd37d6-5829-substrate2-85d8-3643eec50d2b': {
#         'id': 'system_57bd37d6-5829-substrate2-85d8-3643eec50d2b',
#         'parent_id': 'SUBSTRATE',
#         'name': 'system_SUBSTRATE_2',
#         'exporter_url': 'http://172.16.151.31:9100/metrics',
#         'monitor_system': True,
#     },
# }
# github_config = {
#     'repo_57bd37d6-5829-4f7d-85d8-3643eec50d2b': {
#         'id': 'repo_57bd37d6-5829-4f7d-85d8-3643eec50d2b',
#         'parent_id': 'GLOBAL',
#         'repo_name': 'paritytech/global1/',
#         'monitor_repo': True,
#     },
#     'repo_d33e51d3-7227-43da-965a-131f1caf4d15': {
#         'id': 'repo_d33e51d3-7227-43da-965a-131f1caf4d15',
#         'parent_id': 'GLOBAL',
#         'repo_name': 'paritytech/global2',
#         'monitor_repo': True,
#     },
#     'repo_5690uy90yh90h': {
#         'id': 'repo_5690uy90yh90h',
#         'parent_id': 'GLOBAL',
#         'repo_name': 'paritytech/global3',
#         'monitor_repo': True,
#     },
#     'repo_5690uy90fyh90h': {
#         'id': 'dahnina',
#         'parent_id': 'GLOBAL',
#         'repo_name': 'paritytech/global4',
#         'monitor_repo': False,
#     },
# }
# # github_config1 = {
# #     'repo_57bd37d6-cosmos-1-4f7d-85d8-3643eec50d2b': {
# #         'id': 'repo_57bd37d6-cosmos-1-4f7d-85d8-3643eec50d2b',
# #         'parent_id': 'akala',
# #         'repo_name': 'paritytech/polkadot/',
# #         'monitor_repo': True,
# #     },
# # }
# github_config2 = {
#     'repo_57bd37d6-substrate-1-4f7d-85d8-3643eec50d2b': {
#         'id': 'repo_57bd37d6-substrate-1-4f7d-85d8-3643eec50d2b',
#         'parent_id': 'kusama',
#         'repo_name': 'paritytech/substrate/',
#         'monitor_repo': True,
#     },
#     'repo_57bd37d6-substrate-2-4f7d-85d8-3643eec50d2b': {
#         'id': 'repo_57bd37d6-substrate-2-4f7d-85d8-3643eec50d2b',
#         'parent_id': 'kusama',
#         'repo_name': 'paritytech/polkadot/',
#         'monitor_repo': True,
#     },
# }
rabbit_api.connect_till_successful()
rabbit_api.confirm_delivery()
rabbit_api.exchange_declare('config', 'topic', False, True, False, False)
rabbit_api.queue_declare('system_monitors_manager_configs_queue', False, True, False, False)
rabbit_api.queue_declare('github_monitors_manager_configs_queue', False, True, False, False)
rabbit_api.exchange_declare('raw_data', 'direct', False, True, False, False)
result = rabbit_api.queue_declare(queue='', exclusive=True)
# rabbit_api.queue_bind(exchange='raw_data', queue=result.method.queue,
#                       routing_key='system')
# rabbit_api.queue_bind(exchange='raw_data', queue=result.method.queue,
#                       routing_key='github')
rabbit_api.basic_publish_confirm('config', 'general.systems_config.ini', config,
                                 True, pika.BasicProperties(delivery_mode=2),
                                 True)
# rabbit_api.basic_publish_confirm('config', 'chains.cosmos.akala.systems_config.ini', config1,
#                                  True, pika.BasicProperties(delivery_mode=2),
#                                  True)
# rabbit_api.basic_publish_confirm('config', 'chains.substrate.polkadot.systems_config.ini', config2,
#                                  True, pika.BasicProperties(delivery_mode=2),
#                                  True)
# rabbit_api.basic_publish_confirm('config', 'general.repos_config.ini', github_config,
#                                  True, pika.BasicProperties(delivery_mode=2),
#                                  True)
# # rabbit_api.basic_publish_confirm('config', 'chains.cosmos.akala.repos_config.ini', github_config1,
# #                                  True, pika.BasicProperties(delivery_mode=2),
# #                                  True)
# rabbit_api.basic_publish_confirm('config', 'chains.substrate.kusama.repos_config.ini', github_config2,
#                                  True, pika.BasicProperties(delivery_mode=2),
#                                  True)

print(' [*] Waiting for messages. To exit press CTRL+C')
sys.stdout.flush()


def callback(ch, method, properties, body):
    print(" [x] Received %r" % json.loads(body))
    sys.stdout.flush()


rabbit_api.exchange_declare('store', 'direct', False, True, False, False)
rabbit_api.exchange_declare('alert', 'topic', False, True, False, False)
rabbit_api.queue_bind(exchange='store', queue=result.method.queue,
                      routing_key='system')
rabbit_api.queue_bind(exchange='alert', queue=result.method.queue,
                      routing_key='alerter.system')
rabbit_api.basic_consume(queue=result.method.queue,
                         on_message_callback=callback, auto_ack=True)
rabbit_api.start_consuming()
# import logging
#
# from alerter.src.configs.system import SystemConfig
# from alerter.src.monitors.system import SystemMonitor
# from alerter.src.utils.data import get_prometheus
#
# print(get_prometheus('http://172.16.151.31:9100/metrics', logging.getLogger('DUMMY_LOGGER')))
# system_config = SystemConfig('test_system_id', 'test_parent_id', 'test_name', True, "http://172.16.151.31:9100/metrics")
# system_monitor = SystemMonitor('test_monitor', system_config, logging.getLogger('DUMMY_LOGGER'), 10)
# system_monitor._get_data()
# system_monitor._process_data_retrieval_successful()
# print(system_monitor.data)