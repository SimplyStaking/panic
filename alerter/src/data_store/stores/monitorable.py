import json
import logging
from copy import deepcopy
from datetime import datetime
from typing import Dict, Tuple

import pika.exceptions

from src.data_store.mongo import MongoApi
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.monitorables import (
    MonitorableType, MONITORABLES_MONGO_COLLECTION, EMPTY_MONITORABLE_DATA)
from src.utils.constants.rabbitmq import (
    MONITORABLE_EXCHANGE, TOPIC, HEALTH_CHECK_EXCHANGE,
    MONITORABLE_STORE_INPUT_QUEUE_NAME, MONITORABLE_STORE_INPUT_ROUTING_KEY)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  ReceivedUnexpectedDataException)


class MonitorableStore(Store):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(name, logger, rabbitmq)
        self._redis = None
        self._mongo = MongoApi(logger=self.logger.getChild(MongoApi.__name__),
                               db_name=self.mongo_db, host=self.mongo_ip,
                               port=self.mongo_port)
        self._monitorables = {}

    @property
    def monitorables(self) -> Dict:
        return self._monitorables

    def _initialise_rabbitmq(self) -> None:
        """
        Initialise the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates a monitorable exchange of type `topic`, declares a queue named
        `monitorable_store_input_queue` and binds it to the monitorable exchange
        with a routing key `*.*` which should correspond to
        basechain.monitorable_type format, sent from the monitor managers.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent.
        """
        self.rabbitmq.connect_till_successful()
        self.logger.info("Creating exchange '%s'", MONITORABLE_EXCHANGE)
        self.rabbitmq.exchange_declare(MONITORABLE_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         MONITORABLE_STORE_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(MONITORABLE_STORE_INPUT_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", MONITORABLE_STORE_INPUT_QUEUE_NAME,
                         MONITORABLE_EXCHANGE,
                         MONITORABLE_STORE_INPUT_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=MONITORABLE_STORE_INPUT_QUEUE_NAME,
            exchange=MONITORABLE_EXCHANGE,
            routing_key=MONITORABLE_STORE_INPUT_ROUTING_KEY)
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=MONITORABLE_STORE_INPUT_QUEUE_NAME,
                                    on_message_callback=self._process_data,
                                    auto_ack=False, exclusive=False,
                                    consumer_tag=None)
        self.rabbitmq.start_consuming()

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        """
        Processes the data being received, from the queue. This data will be
        stored in Mongo as required. If successful, a heartbeat will be sent.
        """
        monitorable_data = json.loads(body)

        self.logger.debug("Received %s. Now processing this data.",
                          monitorable_data)

        processing_error = False
        try:
            self._process_mongo_store(method.routing_key, monitorable_data)
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

    def _process_mongo_store(self, routing_key: str,
                             received_data: Dict) -> None:

        # Helper function to extract data from the routing key.
        base_chain, monitorable_type = self._process_routing_key(routing_key)

        # If after processing the routing key there was a missing value
        # do not proceed with storing monitorables and raise error.
        if '' in [base_chain, monitorable_type]:
            raise ReceivedUnexpectedDataException(self.name)

        # Use local data if available, else try to get from mongo.
        if base_chain in self.monitorables:
            base_chain_data = self.monitorables[base_chain]
        else:
            base_chain_data = self.mongo.get_one(MONITORABLES_MONGO_COLLECTION,
                                                 {'_id': base_chain})
            if not base_chain_data:
                base_chain_data = {}
            else:
                del base_chain_data['_id']

        manager_name = received_data['manager_name']

        base_chain_data_copy = deepcopy(base_chain_data)
        for chain_id in base_chain_data_copy:
            # Clear manager name from all sources under chain and monitorable
            # type. This is done before updating the sources so that we can
            # keep track of removed sources.
            sources = base_chain_data[chain_id][monitorable_type.value]
            sources_copy = deepcopy(sources)
            for source_id in sources_copy:
                source = sources[source_id]
                if manager_name in source['manager_names']:
                    source['manager_names'].remove(manager_name)
                    if len(source['manager_names']) == 0:
                        del sources[source_id]

        # Update base_chain_data according to monitorable data.
        for source in received_data['sources']:
            chain_id = source['chain_id']
            chain_name = source['chain_name']
            if chain_id not in base_chain_data:
                base_chain_data[chain_id] = deepcopy(EMPTY_MONITORABLE_DATA)
                base_chain_data[chain_id]['chain_name'] = chain_name

            # Check sources/manager names and add if not found
            source_id = source['source_id']
            source_name = source['source_name']
            if source_id not in (
                    base_chain_data[chain_id][monitorable_type.value]):
                base_chain_data[chain_id][monitorable_type.value][
                    source_id] = {'name': source_name,
                                  'manager_names': [manager_name]}
            else:
                if manager_name not in (
                        base_chain_data[chain_id][monitorable_type.value][
                            source_id]['manager_names']):
                    base_chain_data[chain_id][
                        monitorable_type.value][source_id][
                        'manager_names'].append(manager_name)

        unique_chain_ids = list({source['chain_id'] for source in
                                 received_data['sources']})

        # Set list of sources to empty for chains which are no longer in
        # monitorable data for the given base chain and monitorable type.
        base_chain_data_copy = deepcopy(base_chain_data)
        for chain_id, chain in base_chain_data_copy.items():
            if chain_id not in unique_chain_ids:
                chain = base_chain_data[chain_id]
                chain_copy = base_chain_data_copy[chain_id]
                if sum([len(source['manager_names']) for field, sources in
                        chain.items() if field != 'chain_name' for source in
                        sources.values()]) == 0:
                    chain[monitorable_type.value] = {}
                    # Remove subchain from base chain data if it has no sources.
                    if sum([len(sources) for field, sources in
                            chain_copy.items() if field != 'chain_name']) == 0:
                        del base_chain_data[chain_id]

        update_result = self.mongo.replace_one(
            MONITORABLES_MONGO_COLLECTION,
            {'_id': base_chain},
            base_chain_data
        )

        while not update_result or not update_result.acknowledged:
            # If monitorable data was not stored successfully, keep trying
            # every 30 seconds. This operation blocks the Monitorable Store
            # from taking on other data from the queue since these would not be
            # stored successfully, too. Once the data is stored successfully,
            # other data is automatically retrieved from the queue.
            self.logger.error("Monitorable data was not stored in Mongo "
                              "successfully, retrying in 30 seconds.")
            # Use the BlockingConnection sleep to avoid dropped connections
            self.rabbitmq.connection.sleep(30)
            update_result = self.mongo.replace_one(
                MONITORABLES_MONGO_COLLECTION,
                {'_id': base_chain},
                base_chain_data
            )

        self.logger.debug("Updated {} monitorable data in MongoDB.".format(
            base_chain))

    def _process_routing_key(self, routing_key: str) -> Tuple[str,
                                                              MonitorableType]:
        """
        The following values need to be determined from the routing_key:
        `base_chain`: is the identifiable base chain e.g. general, cosmos,
        substrate or chainlink.
        `monitorable_type`: The monitorable type received, can be one of the
        following: SYSTEMS, NODES, GITHUB_REPOS, DOCKERHUB_REPOS, and CHAINS.
        """
        base_chain = ''
        monitorable_type = ''

        try:
            parsed_routing_key = routing_key.split('.')
            base_chain = parsed_routing_key[0].lower()
            monitorable_type = MonitorableType(parsed_routing_key[1])
        except KeyError as key_error:
            self._logger.error("Failed to process routing_key %s", routing_key)
            self._logger.exception(key_error)
        except ValueError as value_error:
            self._logger.error("Failed to process routing_key %s", routing_key)
            self._logger.exception(value_error)

        return base_chain, monitorable_type
