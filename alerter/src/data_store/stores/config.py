import json
import logging
from datetime import datetime
from typing import Dict

import pika.exceptions
from collections import defaultdict

from src.data_store.redis.store_keys import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants import (CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 STORE_CONFIGS_QUEUE_NAME,
                                 STORE_CONFIGS_ROUTING_KEY_CHAINS,
                                 GENERAL, CHAINS, REPOS_CONFIG, SYSTEMS_CONFIG,
                                 NODES_CONFIG, COSMOS, SUBSTRATE, GLOBAL)
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
        Declares a queue named `store_configs_queue` and binds it to the config
        exchange with a routing key `#` meaning anything
        coming from the config manager will be accepted here

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

        self.logger.debug("Received %s. Now processing this data.", config_data)

        if 'DEFAULT' in config_data:
            del config_data['DEFAULT']

        processing_error = False
        try:
            self._process_redis_store(method.routing_key, config_data)
            self._process_redis_store_ids(method.routing_key, config_data)
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
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
            except MessageWasNotDeliveredException as e:
                self.logger.exception(e)
            except Exception as e:
                # For any other exception raise it.
                raise e

    def _process_redis_store(self, routing_key: str, data: Dict) -> None:
        if data:
            # Store all the config under the routing_key
            self.logger.debug("Saving for %s the data=%s.", routing_key, data)
            self.redis.set(Keys.get_config(routing_key), json.dumps(data))
        else:
            self.logger.debug("Removing the saved config for key %s .",
                              routing_key)
            if self.redis.exists(Keys.get_config(routing_key)):
                self.redis.remove(Keys.get_config(routing_key))

    def _process_redis_store_ids(self, routing_key: str, data: Dict) -> None:
        temp_data = defaultdict(dict)
        monitored_list = []
        not_monitored_list = []
        redis_store_key = ''
        source_name = ''
        config_type_key = ''
        monitor_source_key = ''
        parsed_routing_key = routing_key.split('.')

        # First determine the key that is going to be used for REDIS
        if parsed_routing_key[0] is GENERAL:
            redis_store_key = GENERAL
            source_name = GLOBAL
            # Determine the configuration that needs to be changed
            if parsed_routing_key[1] in [REPOS_CONFIG, SYSTEMS_CONFIG]:
                config_type_key = parsed_routing_key[1].replace("_config",
                                                                "")
            else:
                # If the second part of the parsing key is invalid leave
                return
        elif parsed_routing_key[0] is CHAINS:
            redis_store_key = parsed_routing_key[1]
            source_name = parsed_routing_key[2]
            # Determine the configuration that needs to be changed
            if parsed_routing_key[3] in [REPOS_CONFIG, SYSTEMS_CONFIG,
                                         NODES_CONFIG]:
                # Determine the configuration that needs to be changed
                config_type_key = parsed_routing_key[3].replace("_config",
                                                                "")
            else:
                # If the last part of the routing key is invalid leave
                return
        else:
            return

        # Create the key that is used to determine if the source
        # should be monitored or not
        monitor_key = 'monitor_' + config_type_key[:-1]

        # Load the currently saved data from REDIS
        loaded_data = json.loads(self.redis.get(Keys.get_chain_info(
            redis_store_key).decode('utf-8')))

        # Checking if we received data and if that data is useful.
        if data:
            # Get a list of all the id's for the received data
            for _, config_details in data.items():
                if bool(config_details[monitor_key]):
                    monitored_list.append(config_details['id'])
                else:
                    not_monitored_list.append(config_details['id'])

            # If we load data from REDIS we can overwrite it, no need for new
            # structure
            if loaded_data:
                temp_data = loaded_data
                temp_data[source_name]['monitored'][config_type_key] = \
                    monitored_list
                temp_data[source_name]['not_monitored'][config_type_key] = \
                    not_monitored_list
            else:
                temp_data = {
                    source_name: {
                        'monitored': {
                            config_type_key: monitored_list
                        },
                        'not_monitored': {
                            config_type_key: not_monitored_list
                        }
                    }
                }
            self.redis.set(Keys.get_chain_info(redis_store_key),
                           json.dumps(dict(temp_data)))
        else:
            # Check if the key exists
            if self.redis.exists(Keys.get_chain_info(redis_store_key)):
                # Delete the data corresponding to the routing key
                if loaded_data:
                    # Since there is data check what needs to be overwritten
                    
                else:
                    # This shouldn't be the case but just incase delete the key
                    self.redis.remove(Keys.get_chain_info(redis_store_key))
