
import logging
import json
import pika
import pika.exceptions
from datetime import datetime
from typing import Dict, List, Optional
from alerter.src.utils.exceptions import UnknownRoutingKeyException
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_store.redis.store_keys import Keys
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.types import GithubDataType, GithubMonitorDataType
from alerter.src.data_store.store.store import Store

class GithubStore(Store):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    """
        Initialize the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates an exchange named `store` of type `direct`
        Declares a queue named `github_store_queue` and binds it to exchange
        `store` with a routing key `github` meaning anything
        coming from the transformer with regads to github updates will be
        received here.
    """
    def _initialize_store(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange='store', exchange_type='direct',
            passive=False, durable=True, auto_delete=False, internal=False)
        self.rabbitmq.queue_declare('github_store_queue', passive=False, \
            durable=True, exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(queue='github_store_queue', exchange='store',
            routing_key='github')

    def _start_listening(self) -> None:
        self._mongo = MongoApi(logger=self.logger, db_name=self.mongo_db, \
            host=self.mongo_ip, port=self.mongo_port)
        self.rabbitmq.basic_consume(queue='github_store_queue', \
            on_message_callback=self._process_data, auto_ack=False, \
                exclusive=False, consumer_tag=None)
        while True:
            try:
                self.rabbitmq.start_consuming()       
            except pika.exceptions.AMQPChannelError:
                continue
            except pika.exceptions.AMQPConnectionError as e:
                raise e
            except Exception as e:
                self.logger.error(e)
                raise e

    """
        Processes the data being received, from the queue. One type of metric
        will be received here which is a github update if a new release
        of a repository has been detected and monitored. This only needs
        to be stored in redis.
    """
    def _process_data(self, ch, method: pika.spec.Basic.Deliver, \
        properties: pika.spec.BasicProperties, body: bytes) -> None:
        github_data = json.loads(body.decode())
        if method.routing_key == 'github':
            self._process_redis_metrics_store(github_data['result']['data'])
            self._process_redis_monitor_store( \
                github_data['result']['meta_data'])
        else:
            raise UnknownRoutingKeyException(
                'Received an unknown routing key {} from the transformer.' \
                    .format(method.routing_key))
        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_redis_metrics_store(self,  github_data: GithubDataType) \
        -> None:
        key = Keys.get_github_releases(github_data['name'])
        self.logger.debug('Saving github monitor state: %s=%s', key,
            github_data['current_no_of_releases'])
        self.redis.set(key, github_data['current_no_of_releases'])
    
    def _process_redis_monitor_store(self, monitor_data: \
        GithubMonitorDataType) -> None:
        self.logger.debug(
            'Saving %s state: _github_monitor_last_monitoring_round=%s',
            monitor_data['name'],
            monitor_data['github_monitor_last_monitoring_round']
        )

        self.redis.set_multiple({
            Keys.get_github_monitor_last_monitoring_round(monitor_data['name']):
                monitor_data['github_monitor_last_monitoring_round']
        })

    """
        Updating mongo with github metrics using a time-based document with 60
        entries per hour per github, assuming each github monitoring round is
        60 seconds.

        Collection is the name of the chain, a document will keep incrementing
        with new github metrics until it's the next hour at which point mongo
        will create a new document and repeat the process.

        Document type will always be github, as only github metrics are going
        to be stored in this document.

        $inc increments n_metrics by one each time a metric is added
    """
    def _process_mongo_store(self, github_data: GithubDataType) -> None:
        time_now = datetime.now()
        self.mongo.update_one(github_data['chain_name'],
            {'doc_type': 'github', 'd': time_now.hour },
            {'$push': { github_data['name'] : {
                'process_cpu_seconds_total': \
                    github_data['process_cpu_seconds_total'],
                'process_memory_usage': system['process_memory_usage'],
                'virtual_memory_usage': system['virtual_memory_usage'],
                'open_file_descriptors': \
                    system['open_file_descriptors'],
                'system_cpu_usage': system['system_cpu_usage'],
                'system_ram_usage': system['system_ram_usage'],
                'system_storage_usage': system['system_storage_usage'],
                'system_network_transmit_bytes_per_second': \
                    system['system_network_transmit_bytes_per_second'],
                'system_network_receive_bytes_per_second': \
                    system['system_network_receive_bytes_per_second'],
                'timestamp': time_now.timestamp(),
                }
            },
                '$inc': {'n_metrics': 1},
            }
        )