import os
import pika
import pika.exceptions
import sys
import time
import logging
from datetime import datetime
from configparser import ConfigParser
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi

# TODO this file should be removed after the alert_router is implemented
# together with the data store, until then this should be kept as reference
# first run run_test_data_store.py and then run this to test that data is being
# sent and stored
if __name__ == '__main__':
    DUMMY_LOGGER = logging.getLogger('dummy')
    # Initialize Mongo with environmental variables
    mongo_host = os.environ["DB_IP"]
    mongo_port = int(os.environ["DB_PORT"])
    mongo_db = os.environ["DB_NAME"]
    mongo_api = MongoApi(DUMMY_LOGGER, mongo_db, mongo_host, mongo_port)

    # print(mongo_api.ping_unsafe())
    # Testing rabbit with Rabbit Interface
    rabbit_host = os.environ["RABBIT_IP"]
    rabbitAPI = RabbitMQApi(DUMMY_LOGGER, rabbit_host)
    rabbitAPI.connect()
    rabbitAPI.confirm_delivery()
    rabbitAPI.exchange_declare(exchange='store', exchange_type='topic',
            passive=False, durable=True, auto_delete=False, internal=False)
        
    try:
        github_dict = {
            'name': 'cosmos/cosmos',
            'prev_no_of_releases': '80',
        }
        data_dict_1 = {
            'chain_name': 'akash',
            'name': 'system_config_1',
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
        data_dict_2 = {
            'chain_name': 'akash',
            'name': 'system_config_2',
            'process_cpu_seconds_total': '123412',
            'process_memory_usage': '65',
            'virtual_memory_usage': '600',
            'open_file_descriptors': '70',
            'system_cpu_usage': '20',
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
            'system_monitor_network_transmit_bytes_total_2': '3000',
        }
        alert_type_dict = {
            'chain_name': 'akash',
            'origin': 'system_config_2',
            'alert_name': 'Unexpected error',
            'severity': 'INFO',
            'message': 'Something bad happened, INFORMATIONAL ALERT',
            'timestamp': datetime.now().timestamp(),
        }
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.system.metrics',
            body=data_dict_1,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.system.metrics',
            body=data_dict_2,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.github',
            body=github_dict,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.system.monitor',
            body=system_monitor_dict,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='alert_route',
            body=alert_type_dict,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )

        mongo_coll = mongo_api.get_all("akash")
        for i in mongo_coll:
            print(mongo_coll)

        print('Message was published')
    except pika.exceptions.UnroutableError:
        print('Message was returned')
    print(" [x] Sent Messages ")
    rabbitAPI.disconnect()