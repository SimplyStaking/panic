import json
import logging
from datetime import datetime
from typing import Dict, List

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
                         CONFIG_EXCHANGE, STORE_CONFIGS_ROUTING_KEY_CHAINS)
        self.rabbitmq.queue_bind(queue=STORE_CONFIGS_QUEUE_NAME,
                                 exchange=CONFIG_EXCHANGE,
                                 routing_key=STORE_CONFIGS_ROUTING_KEY_CHAINS)
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=STORE_CONFIGS_QUEUE_NAME,
                                    on_message_callback=self._process_data,
                                    auto_ack=False,
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
        config_data = json.loads(body.decode())

        if 'DEFAULT' in config_data:
            del config_data['DEFAULT']

        self.logger.debug("Received %s. Now processing this data.", config_data)

        processing_error = False
        try:
            self._process_data_sort(method.routing_key.split('.'), config_data)
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

    def _process_data_sort(self, routing_key: List[str], data: Dict) -> None:
        if routing_key[0] in ['general', 'channels']:
            if routing_key[1] in ['systems_config', 'alerts_config',
                                  'repos_config', 'opsgenie_config',
                                  'pagerduty_config', 'telegram_config',
                                  'email_config', 'twilio_config']:
                self._process_redis_store(routing_key[0], routing_key[1], data)
        elif 'chains' == routing_key[0]:
            if routing_key[3] in ['nodes_config', 'alerts_config',
                                  'repos_config']:
                chain_path = routing_key[1] + '.' + routing_key[2]
                self._process_redis_store(chain_path, routing_key[3], data)

    def _process_redis_store(self, parent_id: str, config_type: str,
                             data: Dict) -> None:
        if data:
            self.logger.debug(
                    "Saving for %s the config %s the data=%s.",
                    parent_id, config_type, data
                )

            self.redis.hset(Keys.get_hash_parent(parent_id),
                            Keys.get_config(config_type),
                            json.dumps(data))
        else:
            self.logger.debug(
                    "Removing for %s the config %s.",
                    parent_id, config_type
                )
            if self.redis.hexists(Keys.get_hash_parent(parent_id),
                                  Keys.get_config(config_type)):

                self.redis.hremove(Keys.get_hash_parent(parent_id),
                                   Keys.get_config(config_type))
