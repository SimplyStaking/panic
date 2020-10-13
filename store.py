import os
import pika
import pika.exceptions
import sys
import time

from configparser import ConfigParser
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
    rabbitAPI.exchange_declare(exchange='store', exchange_type='topic')
    try:
        github_dict = {
            'repo_name': 'cosmos/cosmos',
            'prev_no_of_releases': '20',
        }
        data_dict = {
            'name': 'system_e5af2f6a-6e50-4dc8-aa6f-6b5ad61875a3',
            'process_cpu_seconds_total': '123412',
            'process_memory_usage': '65',
            'virtual_memory_usage': '600',
            'open_file_descriptors': '70',
            'system_cpu_usage': '90',
            'system_ram_usage': '32',
            'system_storage_usage': '54',
            'system_network_transmit_bytes_per_second': '10',
            'system_network_receive_bytes_per_second': '20',
        }
        system_monitor_dict = {
            'name': 'system_e5af2f6a-6e50-4dc8-aa6f-6b5ad61875a3',
            'system_monitor_alive': '20',
            'system_monitor_last_network_inspection': '20',
            'system_monitor_network_receive_bytes_total': '3000',
            'system_monitor_network_transmit_bytes_total': '3000',
        }
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.system.state',
            body=data_dict,
            mandatory=True
        )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.github.state',
            body=github_dict,
            mandatory=True
        )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.system.monitor',
            body=system_monitor_dict,
            mandatory=True
        )
        # print('Message was published')
    except pika.exceptions.UnroutableError:
        print('Message was returned')
    print(" [x] Sent Messages ")
    rabbitAPI.disconnect()