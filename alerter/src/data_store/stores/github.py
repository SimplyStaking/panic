
import logging
import json
import pika
import pika.exceptions
from datetime import datetime
from typing import Dict, List, Optional
from alerter.src.utils.logging import log_and_print
from alerter.src.data_store.mongo.mongo_api import MongoApi
from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_store.redis.store_keys import Keys
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.utils.types import GithubDataType, GithubMonitorDataType
from alerter.src.data_store.stores.store import Store
from alerter.src.utils.exceptions import MessageWasNotDeliveredException

class GithubStore(Store):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def _initialize_store(self) -> None:
        """
        Initialize the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates an exchange named `store` of type `direct`
        Declares a queue named `github_store_queue` and binds it to exchange
        `store` with a routing key `github` meaning anything
        coming from the transformer with regads to github updates will be
        received here.
        """
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
        self.rabbitmq.start_consuming()

    def _process_data(self,
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties, body: bytes) -> None:
        """
        Processes the data being received, from the queue. One type of metric
        will be received here which is a github update if a new release
        of a repository has been detected and monitored. This only needs
        to be stored in redis.
        """
        github_data = json.loads(body.decode())
        try:
            self._process_redis_metrics_store(
                github_data['result']['data'],
                github_data['result']['meta_data']['repo_parent_id'],
                github_data['result']['meta_data']['repo_id']
            )
            self._process_mongo_store(
                github_data['result']['data'],
                github_data['result']['meta_data']
            )
            self._process_redis_monitor_store( \
                github_data['result']['meta_data'])
        except KeyError as e:
            self.logger.error('Error when reading github data, in data store.')
            self.logger.exception(e)
        except Exception as e:
            self.logger.exception(e)
            raise e
        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_redis_metrics_store(self,  github_data: GithubDataType,
        parent_id: str, repo_id: str) -> None:
        self.logger.debug(
            'Saving %s state: release_name=%s, tag_name=%s', repo_id,
            github_data['release_name'], github_data['tag_name']
        )
        self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
            Keys.get_github_release_name(repo_id):
                str(github_data['release_name']),
            Keys.get_github_tag_name(repo_id):
                str(github_data['tag_name']),
        })

    def _process_redis_monitor_store(self, monitor_data: \
        GithubMonitorDataType) -> None:
        self.logger.debug(
            'Saving %s state: _github_monitor_last_monitoring_round=%s',
            monitor_data['monitor_name'],
            monitor_data['last_monitored']
        )

        self.redis.set_multiple({
            Keys.get_github_monitor_last_monitoring_round(
                monitor_data['monitor_name']): \
                    str(monitor_data['last_monitored'])
        })

    def _process_mongo_store(self,  github_data: GithubDataType, monitor_data:
        GithubMonitorDataType) -> None:
        self.mongo.update_one(monitor_data['repo_parent_id'],
            {'doc_type': 'github', 'n_releases': {'$lt': 1000}},
            {'$push': { monitor_data['repo_id']: {
                'release_name': str(github_data['release_name']),
                'tag_name': str(github_data['tag_name']),
                'timestamp': str(monitor_data['last_monitored']),
                }
            },
                '$min': {'first': str(monitor_data['last_monitored'])},
                '$max': {'last': str(monitor_data['last_monitored'])},
                '$inc': {'n_releases': 1},
            }
        )

    def _begin_store(self) -> None:
        self._initialize_store()
        log_and_print('{} started.'.format(self), self.logger)
        while True:
            try:
                self._start_listening()
            except pika.exceptions.AMQPChannelError:
                # Error would have already been logged by RabbitMQ logger. If
                # there is a channel error, the RabbitMQ interface creates a new
                # channel, therefore perform another managing round without
                # sleeping
                continue
            except pika.exceptions.AMQPConnectionError as e:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                raise e
            except MessageWasNotDeliveredException as e:
                # Log the fact that the message could not be sent and re-try
                # another monitoring round without sleeping
                self.logger.exception(e)
                continue
            except Exception as e:
                self.logger.exception(e)
                raise e

