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
                                 STORE_CONFIGS_ROUTING_KEY_CHAINS,
                                 GENERAL, CHAINS, REPOS_CONFIG, SYSTEMS_CONFIG)
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
        temp_data = {}
        monitored_list = []
        not_monitored_list = []
        key = ''
        parsed_routing_key = routing_key.split('.')
        if data:
            if parsed_routing_key[0] is GENERAL:
                if parsed_routing_key[1] is REPOS_CONFIG:
                    # Get a list of all the REPO ids from the config
                    for _, config_details in data.items():
                        if bool(config_details['monitor_repo']):
                            monitored_list.append(config_details['id'])
                        else:
                            not_monitored_list.append(config_details['id'])
                    # Load the currently saved data from REDIS
                    loaded_data = json.loads(self.redis.get(
                        Keys.get_chain_info(parsed_routing_key[0])).decode(
                            'utf-8'))
                    # These can be overwritten as it's only for general
                    if loaded_data:
                        temp_data = loaded_data
                        temp_data['monitored']['repos'] = monitored_list
                        temp_data['not_monitored']['repos'] = not_monitored_list
                    else:
                        temp_data = {
                            'general': 'GLOBAL',
                            'monitored': {
                                'repos': monitored_list,
                                'systems': []
                            },
                            'not_monitored': {
                                'repos': not_monitored_list,
                                'systems': []
                            }
                        }
                    self.redis.set(Keys.get_chain_info(parsed_routing_key[0]),
                                   json.dumps(temp_data))
                    print("SUCCESS REPOS")
                    print(self.redis.get(Keys.get_chain_info(
                        parsed_routing_key[0])))
                elif parsed_routing_key[1] is SYSTEMS_CONFIG:
                    # Get a list of all the System ids from the config
                    for _, config_details in data.items():
                        if bool(config_details['monitor_system']):
                            monitored_list.append(config_details['id'])
                        else:
                            not_monitored_list.append(config_details['id'])
                    # Load the currently saved data from REDIS
                    loaded_data = json.loads(self.redis.get(
                        Keys.get_chain_info(parsed_routing_key[0])).decode(
                            'utf-8'))
                    # These can be overwritten as it's only for general
                    if loaded_data:
                        temp_data = loaded_data
                        temp_data['monitored']['systems'] = monitored_list
                        temp_data['not_monitored']['systems'] = \
                            not_monitored_list
                    else:
                        temp_data = {
                            'general': 'GLOBAL',
                            'monitored': {
                                'repos': [],
                                'systems': monitored_list
                            },
                            'not_monitored': {
                                'repos': [],
                                'systems': not_monitored_list
                            }
                        }
                    self.redis.set(Keys.get_chain_info(parsed_routing_key[0]),
                                   json.dumps(temp_data))
                    print("SUCCESS SYSTEMS")
                    print(self.redis.get(Keys.get_chain_info(
                        parsed_routing_key[0])))
        else:
            print("BREAK")

    # {regen: id, monitored{ nodes[], repos[] , systems[]},not_monitored:
    # { nodes: [], repos:{}, systems:{}}
