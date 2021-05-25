import json
import logging
from datetime import datetime
from typing import Dict

import pika.exceptions

from src.data_store.redis.store_keys import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 GITHUB_STORE_INPUT_QUEUE_NAME,
                                 GITHUB_TRANSFORMED_DATA_ROUTING_KEY, TOPIC)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)


class GithubStore(Store):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(name, logger, rabbitmq)

    def _initialise_rabbitmq(self) -> None:
        """
        Initialise the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates a store exchange of type `topic`
        Declares a queue named `github_store_input_queue` and binds it to the
        store exchange with a routing key `transformed_data.github` meaning
        anything coming from the transformer with regards to github updates will
        be received here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(GITHUB_STORE_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(
            queue=GITHUB_STORE_INPUT_QUEUE_NAME, exchange=STORE_EXCHANGE,
            routing_key=GITHUB_TRANSFORMED_DATA_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(
            queue=GITHUB_STORE_INPUT_QUEUE_NAME,
            on_message_callback=self._process_data, auto_ack=False,
            exclusive=False, consumer_tag=None)
        self.rabbitmq.start_consuming()

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        """
        Processes the data being received, from the queue. This data will be
        stored in Redis as required. If successful, a heartbeat will be sent.
        """
        github_data = json.loads(body.decode())
        self.logger.debug("Received %s. Now processing this data.", github_data)

        processing_error = False
        try:
            self._process_redis_store(github_data)
        except KeyError as e:
            self.logger.error("Error when parsing %s.", github_data)
            self.logger.exception(e)
            processing_error = True
        except ReceivedUnexpectedDataException as e:
            self.logger.error("Error when processing %s", github_data)
            self.logger.exception(e)
            processing_error = True
        except Exception as e:
            self.logger.exception(e)
            processing_error = True

        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # Send a heartbeat only if there were no errors
        if not processing_error:
            try:
                heartbeat = {
                    'component_name': self.name,
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
            except MessageWasNotDeliveredException as e:
                self.logger.exception(e)
            except Exception as e:
                # For any other exception raise it.
                raise e

    def _process_redis_store(self, data: Dict) -> None:
        if 'result' in data:
            self._process_redis_result_store(data['result'])
        elif 'error' in data:
            # No need to store anything if the index key is `error`
            return
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_redis_store".format(self))

    def _process_redis_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        repo_name = meta_data['repo_name']
        repo_id = meta_data['repo_id']
        parent_id = meta_data['repo_parent_id']
        metrics = data['data']

        self.logger.debug(
            "Saving %s state: _no_of_releases=%s, _last_monitored=%s",
            repo_name, metrics['no_of_releases'], meta_data['last_monitored']
        )

        self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
            Keys.get_github_no_of_releases(repo_id):
                str(metrics['no_of_releases']),
            Keys.get_github_last_monitored(repo_id):
                str(meta_data['last_monitored']),
        })
