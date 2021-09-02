import json
import logging
from datetime import datetime
from typing import Dict

import pika

from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis import Keys
from src.data_store.stores.store import Store
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.rabbitmq import (
    STORE_EXCHANGE, TOPIC, CL_CONTRACT_STORE_INPUT_QUEUE_NAME,
    CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  NodeIsDownException,
                                  ReceivedUnexpectedDataException)


class ChainlinkContractStore(Store):
    def __init__(self, name: str, logger: logging.Logger,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(name, logger, rabbitmq)
        self._mongo = MongoApi(logger=self.logger.getChild(MongoApi.__name__),
                               db_name=self.mongo_db, host=self.mongo_ip,
                               port=self.mongo_port)

    def _initialise_rabbitmq(self) -> None:
        """
        Initialise the necessary data for rabbitmq to be able to reach the data
        store as well as appropriately communicate with it.

        Creates a store exchange of type `topic`
        Declares a queue named `cl_contract_store_input_queue` and binds it
        to the store exchange with a routing key
        `transformed_data.contract.cl` meaning anything coming from the
        transformer with regards to chainlink contract data will be received
        here.

        The HEALTH_CHECK_EXCHANGE is also declared so that whenever a successful
        store round occurs, a heartbeat is sent
        """
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange=STORE_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare(CL_CONTRACT_STORE_INPUT_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.rabbitmq.queue_bind(
            queue=CL_CONTRACT_STORE_INPUT_QUEUE_NAME, exchange=STORE_EXCHANGE,
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)

        # Set producing configuration for heartbeat
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.basic_consume(queue=CL_CONTRACT_STORE_INPUT_QUEUE_NAME,
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
        saved in Mongo and Redis as required. If successful, a heartbeat will be
        sent.
        """
        node_data = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.", node_data)

        processing_error = False
        try:
            self._process_redis_store(node_data)
            self._process_mongo_store(node_data)
        except Exception as e:
            self.logger.error("Error when processing %s", node_data)
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
            pass
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_redis_store".format(self))

    def _process_redis_result_store(self, data: Dict) -> None:
        meta_data = data['meta_data']
        node_name = meta_data['node_name']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        for proxy_address, contract_data in metrics.items():
            if(int(contract_data['contractVersion']) == 3):
                self.logger.debug(
                    "Saving %s state for node %s : _contractVersion=%s, "
                    "_aggregatorAddress=%s, _latestRound=%s, "
                    "_latestAnswer=%s, _latestTimestamp=%s, "
                    "_answeredInRound=%s, _withdrawablePayment=%s, "
                    "_last_monitored=%s, _historicalRounds=%s",
                    proxy_address, node_name,
                    str(contract_data['contractVersion']),
                    str(contract_data['aggregatorAddress']),
                    str(contract_data['latestRound']),
                    str(contract_data['latestAnswer']),
                    str(contract_data['latestTimestamp']),
                    str(contract_data['answeredInRound']),
                    str(contract_data['withdrawablePayment']),
                    meta_data['last_monitored'],
                    contract_data['historicalRounds'])

                self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
                    Keys.get_cl_contract_version(node_id, proxy_address):
                        str(contract_data['contractVersion']),
                    Keys.get_cl_contract_aggregator_address(
                        node_id, proxy_address):
                        str(contract_data['aggregatorAddress']),
                    Keys.get_cl_contract_latest_round(
                        node_id, proxy_address):
                        str(contract_data['latestRound']),
                    Keys.get_cl_contract_latest_answer(
                        node_id, proxy_address):
                        str(contract_data['latestAnswer']),
                    Keys.get_cl_contract_latest_timestamp(
                        node_id, proxy_address):
                        str(contract_data['latestTimestamp']),
                    Keys.get_cl_contract_answered_in_round(
                        node_id, proxy_address):
                        str(contract_data['answeredInRound']),
                    Keys.get_cl_contract_withdrawable_payment(
                        node_id, proxy_address):
                        str(contract_data['withdrawablePayment']),
                    Keys.get_cl_contract_historical_rounds(
                        node_id, proxy_address):
                        json.dumps(contract_data['historicalRounds']),
                    Keys.get_cl_contract_last_monitored(
                        node_id, proxy_address):
                        str(meta_data['last_monitored']),
                })
            elif (int(contract_data['contractVersion']) == 4):
                self.logger.debug(
                    "Saving %s state for node %s : _contractVersion=%s, "
                    "_aggregatorAddress=%s, _latestRound=%s, "
                    "_latestAnswer=%s, _latestTimestamp=%s, "
                    "_answeredInRound=%s, _owedPayment=%s, "
                    "_last_monitored=%s, _historicalRounds=%s",
                    proxy_address, node_name,
                    str(contract_data['contractVersion']),
                    str(contract_data['aggregatorAddress']),
                    str(contract_data['latestRound']),
                    str(contract_data['latestAnswer']),
                    str(contract_data['latestTimestamp']),
                    str(contract_data['answeredInRound']),
                    str(contract_data['owedPayment']),
                    meta_data['last_monitored'],
                    contract_data['historicalRounds'])

                self.redis.hset_multiple(Keys.get_hash_parent(parent_id), {
                    Keys.get_cl_contract_version(node_id, proxy_address):
                        str(contract_data['contractVersion']),
                    Keys.get_cl_contract_aggregator_address(
                        node_id, proxy_address):
                        str(contract_data['aggregatorAddress']),
                    Keys.get_cl_contract_latest_round(
                        node_id, proxy_address):
                        str(contract_data['latestRound']),
                    Keys.get_cl_contract_latest_answer(
                        node_id, proxy_address):
                        str(contract_data['latestAnswer']),
                    Keys.get_cl_contract_latest_timestamp(
                        node_id, proxy_address):
                        str(contract_data['latestTimestamp']),
                    Keys.get_cl_contract_answered_in_round(
                        node_id, proxy_address):
                        str(contract_data['answeredInRound']),
                    Keys.get_cl_contract_owed_payment(
                        node_id, proxy_address):
                        str(contract_data['owedPayment']),
                    Keys.get_cl_contract_historical_rounds(
                        node_id, proxy_address):
                        json.dumps(contract_data['historicalRounds']),
                    Keys.get_cl_contract_last_monitored(
                        node_id, proxy_address):
                        str(meta_data['last_monitored']),
                })

    def _process_mongo_store(self, data: Dict) -> None:
        if 'result' in data:
            self._process_mongo_result_store(data['result'])
        elif 'error' in data:
            pass
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_mongo_store".format(self))

    def _process_mongo_result_store(self, data: Dict) -> None:
        """
        Updating mongo with contract metrics using a time-based document with
        360 entries per hour per node, assuming each contract monitoring round
        is 10 seconds.

        Collection is the parent identifier of the contract, a document will
        keep incrementing with new contract metrics until it's the next hour at
        which point mongo will create a new document and repeat the process.

        Document type will always be contract, as only contract metrics are
        going to be stored in this document.

        Timestamp is the time of when these metrics were extracted.

        $inc increments n_entries by one each time an entry is added
        """

        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']
        time_now = datetime.now()

        for proxy_address, contract_data in metrics.items():
            if(int(contract_data['contractVersion']) == 3):
                self.mongo.update_one(
                    parent_id,
                    {'doc_type': 'contract', 'd': time_now.hour},
                    {
                        '$push': {
                            proxy_address: {
                                'node_id': str(node_id),
                                'node_name': str(node_name),
                                'contractVersion': str(contract_data[
                                    'contractVersion']),
                                'aggregatorAddress': str(contract_data[
                                    'aggregatorAddress']),
                                'latestRound': str(contract_data[
                                    'latestRound']),
                                'latestAnswer': str(contract_data[
                                    'latestAnswer']),
                                'latestTimestamp': str(contract_data[
                                    'latestTimestamp']),
                                'answeredInRound': str(contract_data[
                                    'answeredInRound']),
                                'withdrawablePayment': str(contract_data[
                                    'withdrawablePayment']),
                                'historicalRounds': json.dumps(
                                    contract_data['historicalRounds']),
                                'timestamp': meta_data['last_monitored'],
                            }
                        },
                        '$inc': {'n_entries': 1},
                    }
                )
            elif (int(contract_data['contractVersion'] == 4)):
                self.mongo.update_one(
                    parent_id,
                    {'doc_type': 'contract', 'd': time_now.hour},
                    {
                        '$push': {
                            proxy_address: {
                                'node_id': str(node_id),
                                'node_name': str(node_name),
                                'contractVersion': str(contract_data[
                                    'contractVersion']),
                                'aggregatorAddress': str(contract_data[
                                    'aggregatorAddress']),
                                'latestRound': str(contract_data[
                                    'latestRound']),
                                'latestAnswer': str(contract_data[
                                    'latestAnswer']),
                                'latestTimestamp': str(contract_data[
                                    'latestTimestamp']),
                                'answeredInRound': str(contract_data[
                                    'answeredInRound']),
                                'owedPayment': str(contract_data[
                                    'owedPayment']),
                                'historicalRounds': json.dumps(
                                    contract_data['historicalRounds']),
                                'timestamp': meta_data['last_monitored'],
                            }
                        },
                        '$inc': {'n_entries': 1},
                    }
                )
