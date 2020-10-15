import os
import pika
import pika.exceptions
import sys
import time
from datetime import datetime
from configparser import ConfigParser
from alerter.src.utils.logging import DUMMY_LOGGER
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi

# TODO this file should be removed after the alert_router is implemented
# together with the data store, until then this should be kept as reference
# first run run_test_data_store.py and then run this to test that data is being
# sent and stored
if __name__ == '__main__':
    # Initialize Mongo with environmental variables
    mongo_host = os.environ["DB_HOST"]
    mongo_port = int(os.environ["DB_PORT"])
    mongo_db = os.environ["DB_NAME"]
    mongo_api = MongoApi(DUMMY_LOGGER, mongo_db, mongo_host, mongo_port)

    # Testing rabbit with Rabbit Interface
    rabbit_host = os.environ["RABBIT_HOST"]
    rabbitAPI = RabbitMQApi(DUMMY_LOGGER, rabbit_host)
    rabbitAPI.connect()
    rabbitAPI.confirm_delivery()
    rabbitAPI.exchange_declare(exchange='store', exchange_type='topic')
    try:
        github_dict = {
            'name': 'cosmos/cosmos',
            'prev_no_of_releases': '20',
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
            'system_monitor_network_transmit_bytes_total_2': '3000',
        }
        alert_type_dict = {
            'doc_name': 'node_config_1',
            'chain_name': 'akash',
            'alert_name': 'Unexpected error',
            'severity': 'INFO',
            'message': 'Something bad happened, INFORMATIONAL ALERT',
            'timestamp': datetime.now().timestamp(),
        }
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.system.state',
            body=data_dict_1,
            mandatory=True
        )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='transformer.system.state',
            body=data_dict_2,
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
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='alert_router',
            body=alert_type_dict,
            mandatory=True
        )

        mongo_coll = mongo_api.get_all("akash")
        print(len(mongo_coll))
        print(mongo_coll[len(mongo_coll)-1])

        print('Message was published')
    except pika.exceptions.UnroutableError:
        print('Message was returned')
    print(" [x] Sent Messages ")
    rabbitAPI.disconnect()