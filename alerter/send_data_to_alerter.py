import os
import pika
import pika.exceptions
import sys
import time
import logging
from datetime import datetime
from configparser import ConfigParser
from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis.redis_api import RedisApi
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi

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
    rabbitAPI.exchange_declare(exchange='alerter', exchange_type='direct',
                               passive=False, durable=True, auto_delete=False,
                               internal=False)

    try:
        github_data = {
            "result": {
              "meta_data": {
                "repo_name": "tendermint/tendermint/",
                "repo_id": "repo_d33e51d3-7227-43da-965a-131f1caf4d15",
                "repo_parent_id": "GLOBAL",
                "last_monitored": "1604782938.807853"
              },
              "data": {
                "no_of_releases": {
                  "current": 30,
                  "previous": None
                },
                "releases": {
                  "0": {
                    "release_name": "v0.33.8 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.8"
                  },
                  "1": {
                    "release_name": "v0.32.13 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.13"
                  },
                  "2": {
                    "release_name": "v0.33.7 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.7"
                  },
                  "3": {
                    "release_name": "v0.33.6 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.6"
                  },
                  "4": {
                    "release_name": "v0.33.5 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.5"
                  },
                  "5": {
                    "release_name": "v0.32.12 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.12"
                  },
                  "6": {
                    "release_name": "v0.32.11 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.11"
                  },
                  "7": {
                    "release_name": "v0.33.4 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.4"
                  },
                  "8": {
                    "release_name": "v0.32.10 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.10"
                  },
                  "9": {
                    "release_name": "v0.33.3 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.3"
                  },
                  "10": {
                    "release_name": "v0.31.12 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.31.12"
                  },
                  "11": {
                    "release_name": "v0.33.2 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.2"
                  },
                  "12": {
                    "release_name": "v0.33.1 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.1"
                  },
                  "13": {
                    "release_name": "v0.33.0 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.33.0"
                  },
                  "14": {
                    "release_name": "v0.32.9 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.9"
                  },
                  "15": {
                    "release_name": "v0.32.8 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.8"
                  },
                  "16": {
                    "release_name": "v0.32.7 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.7"
                  },
                  "17": {
                    "release_name": "v0.31.11 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.31.11"
                  },
                  "18": {
                    "release_name": "v0.31.10 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.31.10"
                  },
                  "19": {
                    "release_name": "v0.32.6 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.6"
                  },
                  "20": {
                    "release_name": "v0.31.9 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.31.9"
                  },
                  "21": {
                    "release_name": "v0.32.5 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.5"
                  },
                  "22": {
                    "release_name": "v0.32.4 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.4"
                  },
                  "23": {
                    "release_name": "v0.32.3 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.3"
                  },
                  "24": {
                    "release_name": "v0.32.2 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.2"
                  },
                  "25": {
                    "release_name": "v0.31.8 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.31.8"
                  },
                  "26": {
                    "release_name": "v0.32.1 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.1"
                  },
                  "27": {
                    "release_name": "v0.32.0 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.32.0"
                  },
                  "28": {
                    "release_name": "v0.31.7 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.31.7"
                  },
                  "29": {
                    "release_name": "v0.31.6 (WARNING: ALPHA SOFTWARE)",
                    "tag_name": "v0.31.6"
                  }
                }
              }
            }
          }
        github_data_error = {
          "error": {
            "meta_data": {
              "repo_name": "tendermint/tendermin1t/",
              "repo_id": "repo_d33e51d3-7227-43da-965a-131f1caf4d15",
              "repo_parent_id": "GLOBAL",
              "time": "1604783550.075771"
            },
            "message": "Error in API Call: Not Found",
            "code": 5007
          }
        }
        github_transformer_data = {
          'result': {
              'meta_data': {
                  'repo_id': 'repo_id_1',
                  'repo_parent_id': 'repo_parent_id',
                  'repo_name': 'repo_name',
                  'last_monitored': str(datetime.now().timestamp())
              },
              'data': {
                'no_of_releases': 12,
                'releases': 10,
              }
          }
        }
        transformer_data_decrease = {
          'result': {
              'meta_data': {
                  'monitor_name': 'monitor_name_1',
                  'system_name': 'system_config_1',
                  'system_id': '1231-2321-120312031-3213213',
                  'system_parent_id': 'parent_id_12',
                  'timestamp': str(datetime.now().timestamp())
              },
              'data': {
                  'process_cpu_seconds_total':
                      {'current': 60, 'previous': 110},
                  'process_memory_usage':
                      {'current': 60, 'previous': 110},
                  'virtual_memory_usage':
                      {'current': 60, 'previous': 110},
                  'open_file_descriptors':
                      {'current': 60, 'previous': 110},
                  'system_cpu_usage':
                      {'current': 60, 'previous': 110},
                  'system_ram_usage':
                      {'current': 60, 'previous': 110},
                  'system_storage_usage':
                      {'current': 60, 'previous': 110},
                  'network_receive_bytes_total':
                      {'current': 60, 'previous': 110},
                  'network_transmit_bytes_total':
                      {'current': 60, 'previous': 110},
                  'disk_io_time_seconds_total':
                      {'current': 60, 'previous': 110},
                  'network_transmit_bytes_per_second':
                      {'current': 60, 'previous': 110},
                  'network_receive_bytes_per_second':
                      {'current': 60, 'previous': 110},
                  'disk_io_time_seconds_in_interval':
                      {'current': 60, 'previous': 110},
                  'went_down_at':
                      {'current': 60, 'previous': 110},
              }
            }
        }
        system_data_error = {
          "error": {
            "meta_data": {
              "system_name": "system_main_2",
              "system_id": "system_73a16131-a974-4283-9d64-93af38328e53",
              "system_parent_id": "GLOBAL",
              "time": 1604783549.751823
            },
            "message": "Invalid URL http://172.16.151.40:91100/metrics",
            "code": 5008
          }
        }
        # rabbitAPI.basic_publish_confirm(
        #     exchange='alerter',
        #     routing_key='alerter.system.general',
        #     body=transformer_data_decrease,
        #     is_body_dict=True,
        #     properties=pika.BasicProperties(delivery_mode=2),
        #     mandatory=True
        # )
        rabbitAPI.basic_publish_confirm(
            exchange='alerter',
            routing_key='alerter.system.general',
            body=system_data_error,
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
        # rabbitAPI.basic_publish_confirm(
        #     exchange='store', routing_key='github',
        #     body=github_dict,
        #     is_body_dict=True,
        #     properties=pika.BasicProperties(delivery_mode=1),
        #     mandatory=True
        # )
        # rabbitAPI.basic_publish_confirm(
        #     exchange='store', routing_key='transformer.system.monitor',
        #     body=system_monitor_dict,
        #     is_body_dict=True,
        #     properties=pika.BasicProperties(delivery_mode=2),
        #     mandatory=True
        # )
        # rabbitAPI.basic_publish_confirm(
        #     exchange='store', routing_key='alert',
        #     body=alert_type_dict,
        #     is_body_dict=True,
        #     properties=pika.BasicProperties(delivery_mode=2),
        #     mandatory=True
        # )

        # mongo_coll = mongo_api.get_all("akash")
        # for i in mongo_coll:
        #     print(mongo_coll)

        print('Message was published')
    except pika.exceptions.UnroutableError:
        print('Message was returned')
    print(" [x] Sent Messages ")
    rabbitAPI.disconnect()
