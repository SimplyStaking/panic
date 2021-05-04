import json
import logging
from datetime import datetime
from typing import Dict, List, Union

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
        """
        This configuration object is useful as when COSMOS and SUBSTRATE nodes
        are added, they will have multiple monitorable sources and not just
        systems, therefore by storing them in a list and iterating through
        the dictionaries it is easier to bundle up the list of monitorable
        data.
        """ 
        self.helper_configuration = {
            REPOS_CONFIG: [{
                "id": 'id',
                "name_key": 'repo_name',
                "monitor_key": 'monitor_repo',
                "config_key": 'repos'
            }],
            SYSTEMS_CONFIG: [{
                "id": 'id',
                "name_key": 'name',
                "monitor_key": 'monitor_system',
                "config_key": 'systems'
            }],
            COSMOS: [{
                "id": 'id',
                "name_key": 'name',
                "monitor_key": 'monitor_system',
                "config_key": 'systems'
            }],
            SUBSTRATE: [{
                "id": 'id',
                "name_key": 'name',
                "monitor_key": 'monitor_system',
                "config_key": 'systems'
            }]
        }

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
            self._process_redis_store_chain_monitorables(method.routing_key,
                                                         config_data)
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
            # Store all the configuration under the routing_key
            self.logger.debug("Saving for %s the data=%s.", routing_key, data)
            self.redis.set(Keys.get_config(routing_key), json.dumps(data))
        else:
            self.logger.debug("Removing the saved config for key %s .",
                              routing_key)
            if self.redis.exists(Keys.get_config(routing_key)):
                self.redis.remove(Keys.get_config(routing_key))

    def _process_redis_store_chain_monitorables(self, routing_key: str,
                                                received_config: Dict) -> None:

        # Assign it to defaultdict so it's able to set nested keys
        data_for_store = defaultdict(dict)

        # Helper function to extract data from the routing key
        redis_store_key, source_name, config_type_key = \
            self._process_routing_key(routing_key)

        # If after processing the routing key there was a missing value
        # do not proceed with the storage of chain_monitorables
        if '' in [redis_store_key, source_name, config_type_key]:
            return

        # Load the currently saved data from REDIS if it exists
        if self.redis.exists(
                Keys.get_base_chain_monitorables_info(redis_store_key)):
            data_for_store = json.loads(self.redis.get(
                Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
                    'utf-8'))
        else:
            data_for_store = {}

        # Checking if we received data and if that data is useful.
        if received_config:
            data_for_store = self._sort_monitorable_configs(received_config,
                                                            config_type_key,
                                                            data_for_store,
                                                            source_name)

            self.redis.set(Keys.get_base_chain_monitorables_info(
                redis_store_key), json.dumps(dict(data_for_store)))
        else:
            # Check if the key exists
            if self.redis.exists(Keys.get_base_chain_monitorables_info(
                    redis_store_key)):

                # Delete the data corresponding to the routing key
                if data_for_store:
                    current_helper_config = \
                        self.helper_configuration[config_type_key]

                    for helper_keys in current_helper_config:
                        del data_for_store[source_name]['monitored'][
                            helper_keys['config_key']]
                        del data_for_store[source_name]['not_monitored'][
                            helper_keys['config_key']]

                    # If the monitored and not_monitored are empty then remove
                    # the chain from REDIS
                    if len(data_for_store[source_name]['monitored']) == 0 \
                        and len(data_for_store[source_name][
                            'not_monitored']) == 0:
                        self.redis.remove(
                            Keys.get_base_chain_monitorables_info(
                                redis_store_key))
                else:
                    # This shouldn't be the case but just incase delete the key
                    self.redis.remove(Keys.get_base_chain_monitorables_info(
                        redis_store_key))

    def _process_routing_key(self, routing_key: str) -> Union[str, str, str]:
        """
        The following values need to be determined from the routing_key:
        `redis_store_key`: is the identifiable base chain e.g GENERAl, COSMOS,
        SUBSTRATE.
        `source_name`: Name of the chain that is built on top of the base chain
        such as regen, moonbeam ...etc.
        `config_type_key`: The configuration type received the ones that are
        needed for this process are SYSTEMS, NODES, REPOS. If anything else
        is received it should be ignored.
        """
        redis_store_key = ''
        source_name = ''
        config_type_key = ''

        parsed_routing_key = routing_key.split('.')

        if parsed_routing_key[0] == GENERAL:
            redis_store_key = GENERAL
            source_name = GLOBAL
            # Determine the configuration that needs to be changed
            if parsed_routing_key[1] in [REPOS_CONFIG, SYSTEMS_CONFIG]:
                config_type_key = parsed_routing_key[1]
        elif parsed_routing_key[0] == CHAINS:
            redis_store_key = parsed_routing_key[1]
            source_name = parsed_routing_key[2]
            if parsed_routing_key[3] in [REPOS_CONFIG, SYSTEMS_CONFIG]:
                config_type_key = parsed_routing_key[3]
            elif parsed_routing_key[3] == NODES_CONFIG:
                config_type_key = parsed_routing_key[1]

        return redis_store_key, source_name, config_type_key

    def _sort_monitorable_configs(self, received_config: Dict,
                                  config_type_key: str, data_for_store: Dict,
                                  source_name: str
                                  ) -> Dict:
        """
        Using the received configuration together with the data which is
        retrieved from REDIS, a list of monitored and non_monitored sources
        are constructed. Choosing whether a source is monitored or not
        we go by the key `monitor_key`. To streamline this process we use
        `self.helper_configuration` which known store keys in the configs
        so that we have a generic sorting function instead of an if statement
        sort.
        """
        monitored_list = []
        not_monitored_list = []
        current_helper_config = self.helper_configuration[config_type_key]

        for helper_keys in current_helper_config:
            # Get a list of all the id's for the received data
            for _, config_details in received_config.items():
                if bool(config_details[helper_keys['monitor_key']]):
                    monitored_list.append({
                        config_details[helper_keys['id']]:
                        config_details[helper_keys['name_key']]})
                else:
                    not_monitored_list.append({
                        config_details[helper_keys['id']]:
                        config_details[helper_keys['name_key']]})

            # If we load data from REDIS we can overwrite it, no need for new
            # structure
            if data_for_store:
                data_for_store[source_name]['monitored'][
                    helper_keys['config_key']] = monitored_list
                data_for_store[source_name]['not_monitored'][
                    helper_keys['config_key']] = not_monitored_list
            else:
                data_for_store = {
                    source_name: {
                        'monitored': {
                            helper_keys['config_key']: monitored_list
                        },
                        'not_monitored': {
                            helper_keys['config_key']: not_monitored_list
                        }
                    }
                }

        return data_for_store
