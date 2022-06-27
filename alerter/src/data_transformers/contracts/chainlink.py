import copy
import json
import logging
from datetime import datetime
from typing import Union, Type, Dict, Tuple

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis import Keys
from src.data_store.redis.redis_api import RedisApi
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.contracts.chainlink.v3 import V3ChainlinkContract
from src.monitorables.contracts.chainlink.v4 import V4ChainlinkContract
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, STORE_EXCHANGE, RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    TOPIC, CL_CONTRACTS_DT_INPUT_QUEUE_NAME,
    CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY,
    CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from src.utils.types import convert_to_int, convert_to_float, ChainlinkContract


class ChainlinkContractsDataTransformer(DataTransformer):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi, rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0) -> None:
        super().__init__(transformer_name, logger, redis, rabbitmq,
                         max_queue_size)

    def _initialise_rabbitmq(self) -> None:
        # A data transformer is both a consumer and producer, therefore we need
        # to initialise both the consuming and producing configurations.

        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '%s' exchange", RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         CL_CONTRACTS_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(CL_CONTRACTS_DT_INPUT_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", CL_CONTRACTS_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE,
                         CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(CL_CONTRACTS_DT_INPUT_QUEUE_NAME,
                                 RAW_DATA_EXCHANGE,
                                 CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(CL_CONTRACTS_DT_INPUT_QUEUE_NAME,
                                    self._process_raw_data, False, False, None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", STORE_EXCHANGE)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _load_number_state(self, state_type: Union[Type[float], Type[int]],
                           cl_contract: ChainlinkContract) -> None:
        """
        This function will attempt to load a Chainlink contract's number metrics
        from redis. If the data from Redis cannot be obtained, the state won't
        be updated.
        :param state_type: What type of number metrics we want to obtain
        :param cl_contract: The Chainlink contract in question
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(cl_contract.parent_id)
        node_id = cl_contract.node_id
        proxy_address = cl_contract.proxy_address
        if state_type == int:
            metric_attributes = cl_contract.get_int_metric_attributes()
            convert_fn = convert_to_int
        else:
            metric_attributes = cl_contract.get_float_metric_attributes()
            convert_fn = convert_to_float

        # We iterate over the number metric attributes and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode, and then convert to int/float. Note, since
        # an error may occur when obtaining the data, the default value must
        # also be passed as bytes(str()).
        for attribute in metric_attributes:
            state_value = eval('cl_contract.' + attribute)
            redis_key = eval('Keys.get_cl_contract' + attribute +
                             '(node_id, proxy_address)')
            default_value = bytes(str(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            processed_redis_value = 'None' if redis_value is None \
                else redis_value.decode("utf-8")
            new_value = convert_fn(processed_redis_value, None)
            eval("cl_contract.set" + attribute + '(new_value)')

    def _load_list_state(self, cl_contract: ChainlinkContract) -> None:
        """
        This function will attempt to load a Chainlink contract's list metrics
        from redis. If the data from Redis cannot be obtained, the state won't
        be updated.
        :param cl_contract: The Chainlink contract in question
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(cl_contract.parent_id)
        node_id = cl_contract.node_id
        proxy_address = cl_contract.proxy_address
        metric_attributes = cl_contract.get_list_metric_attributes()

        for attribute in metric_attributes:
            state_value = eval('cl_contract.' + attribute)
            redis_key = eval('Keys.get_cl_contract' + attribute +
                             '(node_id, proxy_address)')
            default_value = bytes(json.dumps(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            new_value = [] if redis_value is None else json.loads(
                redis_value.decode("utf-8"))
            eval("cl_contract.set" + attribute + '(new_value)')

    def load_state(self, cl_contract: ChainlinkContract) -> ChainlinkContract:
        """
        This function attempts to load the state of a Chainlink contract from
        redis. If the data from Redis cannot be obtained, the state won't be
        updated.
        :param cl_contract: The Chainlink Contract whose state we are interested
                          : in
            :return: The loaded Chainlink Contract
        """
        self.logger.debug("Loading the state of %s from Redis", cl_contract)

        self._load_number_state(int, cl_contract)
        self._load_number_state(float, cl_contract)
        self._load_list_state(cl_contract)

        loaded_metrics_list = [
            '{}={}'.format(key, val)
            for key, val in cl_contract.__dict__.items()
        ]
        loaded_metrics_str = ', '.join(loaded_metrics_list)

        self.logger.debug("Restored %s state: %s", cl_contract,
                          loaded_metrics_str)

        return cl_contract

    def _update_state(self, transformed_data: Dict) -> None:
        self.logger.debug("Updating state ...")

        if 'result' in transformed_data:
            meta_data = transformed_data['result']['meta_data']
            metrics = transformed_data['result']['data']
            node_id = meta_data['node_id']
            parent_id = meta_data['node_parent_id']

            # We need to update the state for every node and contract
            for proxy_address, contract_data in metrics.items():
                cl_contract: ChainlinkContract = self.state[node_id][
                    proxy_address]

                # Set some contract details
                cl_contract.set_aggregator_address(
                    contract_data['aggregatorAddress'])
                cl_contract.set_parent_id(parent_id)
                cl_contract.set_latest_round(contract_data['latestRound'])
                cl_contract.set_latest_answer(contract_data['latestAnswer'])
                cl_contract.set_latest_timestamp(
                    contract_data['latestTimestamp'])
                cl_contract.set_answered_in_round(
                    contract_data['answeredInRound'])
                cl_contract.set_historical_rounds(
                    contract_data['historicalRounds'])
                cl_contract.set_last_round_observed(
                    contract_data['lastRoundObserved'])

                # Set payment details depending on the version of the contract
                if cl_contract.version == 3:
                    cl_contract.set_withdrawable_payment(
                        contract_data['withdrawablePayment'])
                elif cl_contract.version == 4:
                    cl_contract.set_owed_payment(contract_data['owedPayment'])

                cl_contract.set_last_monitored(meta_data['last_monitored'])
        elif 'error' in transformed_data:
            pass
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _update_state".format(self))

        self.logger.debug("State updated successfully")

    def _process_transformed_data_for_saving(self,
                                             transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for storage ...")

        if 'result' in transformed_data or 'error' in transformed_data:
            processed_data = copy.deepcopy(transformed_data)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_saving".format(self))

        self.logger.debug("Processing successful")

        return processed_data

    def _process_transformed_data_for_alerting(self,
                                               transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for alerting ...")

        if 'result' in transformed_data:
            td_meta_data = transformed_data['result']['meta_data']
            td_metrics = transformed_data['result']['data']
            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {}
                }
            }
            processed_data_metrics = processed_data['result']['data']
            node_id = td_meta_data['node_id']
            ignore_metrics = ['contractVersion', 'aggregatorAddress',
                              'description']

            for proxy_address, contract_data in td_metrics.items():
                cl_contract: ChainlinkContract = self.state[node_id][
                    proxy_address]
                processed_data_metrics[proxy_address] = {}

                # Reformat the data in such a way that both the previous and
                # current states are sent to the alerter. We will not record
                # previous values for contractVersion, aggregatorAddress,
                # and description as this data is not used for alerting.
                for metric, value in contract_data.items():
                    if metric not in ignore_metrics:
                        processed_data_metrics[proxy_address][metric] = {}
                        processed_data_metrics[proxy_address][metric][
                            'current'] = value

                # Add the current value of the ignored metrics
                for ignored_metric in ignore_metrics:
                    processed_data_metrics[proxy_address][
                        ignored_metric] = td_metrics[proxy_address][
                        ignored_metric]

                # Add the previous value
                processed_data_metrics[proxy_address]['latestRound'][
                    'previous'] = cl_contract.latest_round
                processed_data_metrics[proxy_address]['latestAnswer'][
                    'previous'] = cl_contract.latest_answer
                processed_data_metrics[proxy_address]['latestTimestamp'][
                    'previous'] = cl_contract.latest_timestamp
                processed_data_metrics[proxy_address]['answeredInRound'][
                    'previous'] = cl_contract.answered_in_round
                processed_data_metrics[proxy_address]['historicalRounds'][
                    'previous'] = copy.deepcopy(cl_contract.historical_rounds)
                processed_data_metrics[proxy_address]['lastRoundObserved'][
                    'previous'] = cl_contract.last_round_observed

                if cl_contract.version == 3:
                    processed_data_metrics[proxy_address][
                        'withdrawablePayment'][
                        'previous'] = cl_contract.withdrawable_payment
                elif cl_contract.version == 4:
                    processed_data_metrics[proxy_address]['owedPayment'][
                        'previous'] = cl_contract.owed_payment
        elif 'error' in transformed_data:
            processed_data = copy.deepcopy(transformed_data)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_alerting".format(self))

        self.logger.debug("Processing successful.")

        return processed_data

    def _transform_data(self, data: Dict) -> Tuple[Dict, Dict, Dict]:
        self.logger.debug("Performing data transformation on %s ...", data)

        if 'result' in data:
            meta_data = data['result']['meta_data']
            transformed_data = copy.deepcopy(data)
            td_meta_data = transformed_data['result']['meta_data']
            td_metrics = transformed_data['result']['data']

            # Transform the meta_data by changing the time key to
            # last_monitored key.
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']

            # Calculate the deviation of the node's answer from the consensus
            # answer for each contract
            for proxy_address, contract_data in td_metrics.items():
                historical_rounds = contract_data['historicalRounds']
                temp_rounds = []
                for i in range(len(historical_rounds)):
                    temp_rounds.append(historical_rounds[i])
                    node_submission = historical_rounds[i]['nodeSubmission']
                    round_answer = historical_rounds[i]['roundAnswer']
                    if None in [node_submission, round_answer]:
                        temp_rounds[i]['deviation'] = None
                    else:
                        temp_rounds[i]['deviation'] = convert_to_float(abs(
                            ((round_answer - node_submission) /
                             round_answer) * 100), None)
                td_metrics[proxy_address]['historicalRounds'] = temp_rounds
        elif 'error' in data:
            transformed_data = copy.deepcopy(data)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _transform_data".format(self))

        data_for_alerting = self._process_transformed_data_for_alerting(
            transformed_data)
        data_for_saving = self._process_transformed_data_for_saving(
            transformed_data)

        self.logger.debug("Data transformation successful")

        return transformed_data, data_for_alerting, data_for_saving

    def _place_latest_data_on_queue(
            self, data_for_alerting: Dict, data_for_saving: Dict) -> None:
        self._push_to_queue(data_for_alerting, ALERT_EXCHANGE,
                            CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

        self._push_to_queue(data_for_saving, STORE_EXCHANGE,
                            CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

    def _create_state_entry(self, node_id: str, proxy_address: str,
                            parent_id: str, version: str,
                            aggregator_address: str) -> bool:
        """
        This function attempts to create an entry in the state which stores the
        contract data for a node. This function creates a new state only if
        there is no entry for the inputted node_id and proxy_address, the only
        exception being if the contract versions are not equal.
        :param node_id: The id of the node in question
        :param proxy_address: The proxy address of the contract
        :param parent_id: The chain on which the contract resides
        :param version: The contract version
        :param aggregator_address: The aggregator address
        :return: True if a new state is created
               : False otherwise
        """
        state_created = False
        if node_id in self.state and proxy_address in self.state[node_id]:
            old_cl_contract: ChainlinkContract = copy.deepcopy(
                self.state[node_id][proxy_address])
            if version != old_cl_contract.version:
                if version == 3:
                    self.state[node_id][proxy_address] = V3ChainlinkContract(
                        proxy_address, aggregator_address, parent_id, node_id)
                    state_created = True
                elif version == 4:
                    self.state[node_id][proxy_address] = V4ChainlinkContract(
                        proxy_address, aggregator_address, parent_id, node_id)
                    state_created = True
        else:
            if node_id not in self.state:
                self.state[node_id] = {}

            if version == 3:
                self.state[node_id][proxy_address] = V3ChainlinkContract(
                    proxy_address, aggregator_address, parent_id, node_id)
                state_created = True
            elif version == 4:
                self.state[node_id][proxy_address] = V4ChainlinkContract(
                    proxy_address, aggregator_address, parent_id, node_id)
                state_created = True

        return state_created

    def _process_raw_data(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        raw_data = json.loads(body)
        self.logger.debug("Received %s from monitors. Now processing this "
                          "data.", raw_data)

        processing_error = False
        transformed_data = {}
        data_for_alerting = {}
        data_for_saving = {}
        try:
            if 'result' in raw_data:
                meta_data = raw_data['result']['meta_data']
                node_id = meta_data['node_id']
                parent_id = meta_data['node_parent_id']
                data = raw_data['result']['data']

                for proxy_address, contract_details in data.items():
                    aggregator_address = contract_details['aggregatorAddress']
                    version = contract_details['contractVersion']
                    state_created = self._create_state_entry(
                        node_id, proxy_address, parent_id, version,
                        aggregator_address)
                    if state_created:
                        cl_contract: ChainlinkContract = self.state[node_id][
                            proxy_address]
                        self.load_state(cl_contract)

                transformed_data, data_for_alerting, data_for_saving = \
                    self._transform_data(raw_data)
            elif 'error' in raw_data:
                transformed_data, data_for_alerting, data_for_saving = \
                    self._transform_data(raw_data)
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _process_raw_data".format(self))
        except Exception as e:
            self.logger.error("Error when processing %s", raw_data)
            self.logger.exception(e)
            processing_error = True

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # We want to update the state after the data is acknowledged, otherwise
        # if acknowledgement fails the state would be erroneous when processing
        # the data again. Note, only update the state if there were no
        # processing errors.
        if not processing_error:
            try:
                self._update_state(transformed_data)
                self.logger.debug("Successfully processed %s", raw_data)
            except Exception as e:
                self.logger.error("Error when processing %s", raw_data)
                self.logger.exception(e)
                processing_error = True

        # Place the data on the publishing queue if there were no processing
        # errors. This is done after acknowledging the data, so that if
        # acknowledgement fails, the data is processed again and we do not have
        # duplication of data in the queue
        if not processing_error:
            self._place_latest_data_on_queue(
                data_for_alerting, data_for_saving)

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()

            if not processing_error:
                heartbeat = {
                    'component_name': self.transformer_name,
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as message is residing in the
            # publisher queue.
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it.
            raise e
