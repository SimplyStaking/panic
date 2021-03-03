import json
import logging
from datetime import datetime
from typing import Dict

import pika.exceptions

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.store import Store
from src.utils.constants import (CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 STORE_CONFIGS_QUEUE_NAME,
                                 STORE_CONFIGS_ROUTING_KEY_CHAINS)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)


class ConfigStore(Store):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(name, logger, rabbitmq)

    def _initialise_rabbitmq(self) -> None:
        """
        Initialise the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates a config exchange of type `topic`
        Declares a queue named `github_store_queue` and binds it to the store
        exchange with a routing key `github` meaning anything
        coming from the transformer with regards to github updates will be
        received here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'", STORE_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(STORE_CONFIGS_QUEUE_NAME, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", STORE_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, '#')
        self.rabbitmq.queue_bind(queue=STORE_CONFIGS_QUEUE_NAME,
                                 exchange=CONFIG_EXCHANGE,
                                 routing_key='#')
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=STORE_CONFIGS_QUEUE_NAME,
                                    on_message_callback=self._process_data,
                                    auto_ack=False,
                                    exclusive=False, consumer_tag=None)
        self.rabbitmq.start_consuming()
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        """
        Processes the data being received, from the queue. This data will be
        stored in Redis as required. If successful, a heartbeat will be sent.
        """
        config_data = json.loads(body.decode())

        if 'DEFAULT' in config_data:
            del config_data['DEFAULT']

        self.logger.debug("Received %s. Now processing this data.", config_data)

        processing_error = False
        try:
            self._process_redis_store(method.routing_key, config_data)
        except KeyError as e:
            self.logger.error("Error when parsing %s.", config_data)
            self.logger.exception(e)
            processing_error = True
        except ReceivedUnexpectedDataException as e:
            self.logger.error("Error when processing %s", config_data)
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
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
            except MessageWasNotDeliveredException as e:
                self.logger.exception(e)
            except Exception as e:
                # For any other exception raise it.
                raise e

    def _process_redis_store(self, routing_key: str, data: Dict) -> None:
        if 'general' in routing_key[0]:
            if 'systems_config' in routing_key[1]:
                self._process_redis_config_system(routing_key[0], data)
            elif 'alerts_config' in routing_key[1]:
                self._process_redis_config_alerts(routing_key[0], data)
            elif 'repos_config' in routing_key[1]:
                self._process_redis_config_repos(routing_key[0], data)
        elif 'chains' in routing_key[0]:
            if 'nodes_config' in routing_key[1]:
                self._process_redis_config_nodes(routing_key[0], data)
            elif 'alerts_config' in routing_key[1]:
                self._process_redis_config_alerts(routing_key[0], data)
            elif 'repos_config' in routing_key[1]:
                self._process_redis_config_repos(routing_key[0], data)
        elif 'channels' in routing_key[0]:
            if 'opsgenie_config' in routing_key[1]:
                
            elif 'pagerduty_config' in routing_key[1]:
            elif 'telegram_config' in routing_key[1]:
            elif 'email_config' in routing_key[1]:

                self._process_redis_config_channel(data)

    def _process_redis_config_system(self, parent_id: str, data: Dict) -> None:
        for key, value in data.items():
            self.logger.debug(
                "Saving %s state: config=%s", key, value
            )

            self.redis.hset(Keys.get_hash_parent(parent_id), {
                Keys.get_config_chain_system(key): value
            })

    def _process_redis_config_alerts(self, parent_id: str, data: Dict) -> None:
        for key, value in data.items():
            self.logger.debug(
                "Saving %s state: config=%s", key, value
            )

            self.redis.hset(Keys.get_hash_parent(parent_id), {
                Keys.get_config_chain_alerts(key): value
            })

    def _process_redis_config_repos(self, parent_id: str, data: Dict) -> None:
        for key, value in data.items():
            self.logger.debug(
                "Saving %s state: config=%s", key, value
            )

            self.redis.hset(Keys.get_hash_parent(parent_id), {
                Keys.get_config_chain_repo(key): value
            })

    def _process_redis_config_channel(self, parent_id: str, data: Dict) -> None:
        for key, value in data.items():
            self.logger.debug(
                "Saving %s state: config=%s", key, value
            )

            self.redis.hset(Keys.get_hash_parent(parent_id), {
                Keys.get_config_chain_repo(key): value
            })

    def _process_redis_config_nodes(self, parent_id: str, data: Dict) -> None:
        for key, value in data.items():
            self.logger.debug(
                "Saving %s state: config=%s", key, value
            )

            self.redis.hset(Keys.get_hash_parent(parent_id), {
                Keys.get_config_chain_node(key): value
            })
