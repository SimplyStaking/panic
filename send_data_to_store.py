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
    rabbitAPI.exchange_declare(exchange='store', exchange_type='direct',
            passive=False, durable=True, auto_delete=False, internal=False)
        
    try:
        github_dict = {
          'result':{
            'data' : {
              'release_name': 'newest_release',
              'tag_name': 'newest_tag',
            },
            'meta_data': {
              'monitor_name': 'monitor_name_1',
              'repo_name': 'chicken/tendermint',
              'repo_id': '1231-2321-120312031-3213213',
              'repo_parent_id': 'parent_id_12',
              'time': str(datetime.now().timestamp())
            }
          }
        }
        data_dict_1 = {
          'result': {
            'data': {
                'process_cpu_seconds_total': '123412',
                'process_memory_usage': '65',
                'virtual_memory_usage': '600',
                'open_file_descriptors': '70',
                'system_cpu_usage': '90',
                'system_ram_usage': '32',
                'system_storage_usage': '54',
                'system_network_transmit_bytes_per_second': '10',
                'system_network_receive_bytes_per_second': '20',
                'system_network_receive_bytes_total': '32',
                'system_network_transmit_bytes_total': '43',
                'system_disk_io_time_seconds_total': '65',
                'system_disk_io_time_seconds_in_interval': '76',
            },
            'meta_data': {
              'monitor_name': 'monitor_name_1',
              'system_name': 'system_config_1',
              'system_id': '1231-2321-120312031-3213213',
              'system_parent_id': 'parent_id_12',
              'time': str(datetime.now().timestamp())
            }
          }
        }
        alert_type_dict = {
          'result':{
            'data': {
                'parent_id': 'parent_id_12',
                'origin': 'system_config_2',
                'alert_name': 'Unexpected error',
                'severity': 'INFO',
                'message': 'Something bad happened, INFORMATIONAL ALERT',
                'timestamp': datetime.now().timestamp(),
            }
          }
        }
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='system',
            body=data_dict_1,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )
        # rabbitAPI.basic_publish_confirm(
        #     exchange='store', routing_key='transformer.system.metrics',
        #     body=data_dict_2,
        #     is_body_dict=True,
        #     properties=pika.BasicProperties(delivery_mode=2),
        #     mandatory=True
        # )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='github',
            body=github_dict,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=1),
            mandatory=True
        )
        # rabbitAPI.basic_publish_confirm(
        #     exchange='store', routing_key='transformer.system.monitor',
        #     body=system_monitor_dict,
        #     is_body_dict=True,
        #     properties=pika.BasicProperties(delivery_mode=2),
        #     mandatory=True
        # )
        rabbitAPI.basic_publish_confirm(
            exchange='store', routing_key='alert',
            body=alert_type_dict,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )

        # mongo_coll = mongo_api.get_all("akash")
        # for i in mongo_coll:
        #     print(mongo_coll)

        print('Message was published')
    except pika.exceptions.UnroutableError:
        print('Message was returned')
    print(" [x] Sent Messages ")
    rabbitAPI.disconnect()