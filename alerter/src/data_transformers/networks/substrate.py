import copy
import json
import logging
from ast import literal_eval
from datetime import datetime
from typing import Dict, Tuple

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis import RedisApi, Keys
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.networks.substrate import SubstrateNetwork
from src.utils.constants.data import VALID_SUBSTRATE_NETWORK_SOURCES
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, STORE_EXCHANGE, ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    SUBSTRATE_NETWORK_DT_INPUT_QUEUE_NAME,
    SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY,
    SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from src.utils.substrate import (get_load_number_state_helper_network,
                                 get_load_list_of_dicts_state_helper_network,
                                 get_load_bool_state_helper_network)
from src.utils.types import str_to_bool_strict


class SubstrateNetworkTransformer(DataTransformer):
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
        self.rabbitmq.exchange_declare(
            RAW_DATA_EXCHANGE, 'topic', False, True, False, False)
        self.logger.info("Creating queue '%s'",
                         SUBSTRATE_NETWORK_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            SUBSTRATE_NETWORK_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", SUBSTRATE_NETWORK_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE,
                         SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            SUBSTRATE_NETWORK_DT_INPUT_QUEUE_NAME, RAW_DATA_EXCHANGE,
            SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(SUBSTRATE_NETWORK_DT_INPUT_QUEUE_NAME,
                                    self._process_raw_data, False, False, None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", STORE_EXCHANGE)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def _load_boolean_state(self, substrate_network: SubstrateNetwork) -> None:
        """
        This function will attempt to load a network's boolean metrics from
        redis. If the data from Redis cannot be obtained, the state won't be
        updated.
        :param substrate_network: The network state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(substrate_network.parent_id)
        loading_helper = get_load_bool_state_helper_network(substrate_network)

        # We iterate over each metric configuration and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode, and then convert to int/float. Note, since
        # an error may occur when obtaining the data, the default value must
        # also be passed as bytes(str()).
        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            set_fn = configuration['setter']
            default_value = bytes(str(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            processed_redis_value = ('None'
                                     if redis_value is None
                                     else redis_value.decode("utf-8"))
            new_value = (
                None if redis_value == 'None'
                else str_to_bool_strict(processed_redis_value, state_value)
            )
            set_fn(new_value)

    def _load_number_state(self, substrate_network: SubstrateNetwork) -> None:
        """
        This function will attempt to load a network's number metrics from redis
        If the data from Redis cannot be obtained, the state won't be updated.
        :param substrate_network: The network state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(substrate_network.parent_id)
        loading_helper = get_load_number_state_helper_network(substrate_network)

        # We iterate over each metric configuration and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode, and then convert to int/float. Note, since
        # an error may occur when obtaining the data, the default value must
        # also be passed as bytes(str()).
        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            convert_fn = configuration['convert_fn']
            set_fn = configuration['setter']
            default_value = bytes(str(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            processed_redis_value = ('None'
                                     if redis_value is None
                                     else redis_value.decode("utf-8"))
            new_value = convert_fn(processed_redis_value, state_value)
            set_fn(new_value)

    def _load_list_of_dicts_state(
            self, substrate_network: SubstrateNetwork) -> None:
        """
        This function will attempt to load a network's dict metrics from redis.
        If the data from Redis cannot be obtained, the state won't be updated.
        :param substrate_network: The network state to load
        :return: Nothing
        """
        redis_hash = Keys.get_hash_parent(substrate_network.parent_id)
        loading_helper = get_load_list_of_dicts_state_helper_network(
            substrate_network)

        # We iterate over each metric configuration and attempt to load from
        # redis. We are saving metrics in the following format b"value", so
        # first we need to decode, and then convert to json. Note, since an
        # error may occur when obtaining the data, the default value must also
        # be passed as bytes(json.dumps()).
        for configuration in loading_helper:
            state_value = configuration['state_value']
            redis_key = configuration['redis_key']
            set_fn = configuration['setter']
            default_value = bytes(json.dumps(state_value), 'utf-8')
            redis_value = self.redis.hget(redis_hash, redis_key, default_value)
            new_value = (
                state_value if redis_value is None
                else json.loads(redis_value.decode("utf-8"))
            )
            set_fn(new_value)

    def load_state(
            self, substrate_network: SubstrateNetwork) -> SubstrateNetwork:
        self.logger.debug("Loading the state of %s from Redis",
                          substrate_network)

        self._load_boolean_state(substrate_network)
        self._load_number_state(substrate_network)
        self._load_list_of_dicts_state(substrate_network)

        self.logger.debug(
            "Restored %s state: _grandpa_stalled=%s, _public_prop_count=%s, "
            "_active_proposals=%s, _referendum_count=%s, "
            "referendums=%s, _last_monitored_websocket=%s",
            substrate_network, substrate_network.grandpa_stalled,
            substrate_network.public_prop_count,
            substrate_network.active_proposals,
            substrate_network.referendum_count,
            substrate_network.referendums,
            substrate_network.last_monitored_websocket
        )

        return substrate_network

    def _update_websocket_state(self, websocket_data: Dict) -> None:
        if 'result' in websocket_data:
            meta_data = websocket_data['result']['meta_data']
            metrics = websocket_data['result']['data']
            parent_id = meta_data['parent_id']
            chain_name = meta_data['chain_name']
            network: SubstrateNetwork = self.state[parent_id]

            # Set network details just in case the configs have changed, and the
            # new metrics
            network.set_parent_id(parent_id)
            network.set_chain_name(chain_name)
            network.set_grandpa_stalled(metrics['grandpa_stalled'])
            network.set_public_prop_count(metrics['public_prop_count'])
            network.set_active_proposals(metrics['active_proposals'])
            network.set_referendum_count(metrics['referendum_count'])
            network.set_referendums(metrics['referendums'])
            network.set_last_monitored_websocket(meta_data['last_monitored'])
        elif 'error' in websocket_data:
            meta_data = websocket_data['error']['meta_data']
            parent_id = meta_data['parent_id']
            chain_name = meta_data['chain_name']
            network: SubstrateNetwork = self.state[parent_id]

            # Set network details just in case the configs have changed
            network.set_parent_id(parent_id)
            network.set_chain_name(chain_name)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _update_websocket_state".format(self))

    def _update_state(self, transformed_data: Dict) -> None:
        self.logger.debug("Updating state ...")
        processing_performed = False
        update_helper = {
            'websocket': self._update_websocket_state,
        }

        for data_type, update_fn in update_helper.items():
            if data_type in transformed_data and transformed_data[data_type]:
                processing_performed = True
                update_fn(transformed_data[data_type])

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _update_state".format(self))

        self.logger.debug("State updated successfully")

    def _process_transformed_data_for_saving(self,
                                             transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for storage ...")
        processing_performed = False

        # We must check that the source's data is valid
        for source in VALID_SUBSTRATE_NETWORK_SOURCES:
            if source in transformed_data and transformed_data[source]:
                if ('result' in transformed_data[source]
                        or 'error' in transformed_data[source]):
                    processing_performed = True
                else:
                    raise ReceivedUnexpectedDataException(
                        "{}: _process_transformed_data_for_saving".format(self))

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_saving".format(self))

        return copy.deepcopy(transformed_data)

    def _process_transformed_websocket_data_for_alerting(
            self, transformed_substrate_network_data: Dict) -> Dict:
        if 'result' in transformed_substrate_network_data:
            td_meta_data = transformed_substrate_network_data['result'][
                'meta_data']
            td_parent_id = td_meta_data['parent_id']
            network: SubstrateNetwork = self.state[td_parent_id]
            td_metrics = transformed_substrate_network_data['result']['data']

            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {}
                }
            }
            pd_data = processed_data['result']['data']

            # Reformat the data in such a way that both the previous and current
            # states are sent to the alerter
            for metric, value in td_metrics.items():
                pd_data[metric] = {}
                if metric == 'active_proposals':
                    active_proposals = copy.deepcopy(value)
                    for proposal in active_proposals:
                        if 'seconds' in proposal:
                            del proposal['seconds']
                    pd_data[metric]['current'] = active_proposals
                elif metric == 'referendums':
                    referendums = copy.deepcopy(value)
                    for referendum in referendums:
                        if 'data' in referendum and referendum['data'] and (
                                'votes' in referendum['data']):
                            del referendum['data']['votes']
                    pd_data[metric]['current'] = referendums
                else:
                    pd_data[metric]['current'] = value

            # Add previous for each metric
            pd_data['grandpa_stalled']['previous'] = network.grandpa_stalled
            pd_data['public_prop_count']['previous'] = network.public_prop_count
            prev_active_proposals = copy.deepcopy(network.active_proposals)
            if prev_active_proposals:
                for proposal in prev_active_proposals:
                    if 'seconds' in proposal:
                        del proposal['seconds']
            pd_data['active_proposals']['previous'] = prev_active_proposals
            pd_data['referendum_count']['previous'] = network.referendum_count
            prev_referendums = copy.deepcopy(network.referendums)
            for referendum in prev_referendums:
                if 'data' in referendum and referendum['data'] and (
                        'votes' in referendum['data']):
                    del referendum['data']['votes']
            pd_data['referendums']['previous'] = prev_referendums
        elif 'error' in transformed_substrate_network_data:
            processed_data = copy.deepcopy(transformed_substrate_network_data)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_websocket_data_for_alerting".format(
                    self))

        return processed_data

    def _process_transformed_data_for_alerting(
            self, transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for alerting ...")
        processing_performed = False
        processing_helper = {
            'websocket': self._process_transformed_websocket_data_for_alerting,
        }
        processed_data = {
            'websocket': {},
        }

        for data_type, processing_fn in processing_helper.items():
            if data_type in transformed_data and transformed_data[data_type]:
                processing_performed = True
                processed_data[data_type] = processing_fn(
                    transformed_data[data_type])

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_alerting".format(self))

        self.logger.debug("Processing successful.")

        return processed_data

    def _transform_websocket_data(self, substrate_network_data: Dict) -> Dict:
        if 'result' in substrate_network_data:
            meta_data = substrate_network_data['result']['meta_data']
            transformed_data = copy.deepcopy(substrate_network_data)
            td_meta_data = transformed_data['result']['meta_data']
            del td_meta_data['monitor_name']
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']

            td_data = transformed_data['result']['data']
            td_data['grandpa_stalled'] = td_data['grandpa_stalled'] is not None

            gov_addresses = meta_data['governance_addresses']

            td_data['public_prop_count'] = literal_eval(str(
                td_data['public_prop_count']))

            active_proposals = []
            for proposal in td_data['active_proposals']:
                index = literal_eval(str(proposal['index'])) if (
                        'index' in proposal) else None
                balance = literal_eval(str(proposal['balance'])) if (
                        'balance' in proposal) else None
                image = None
                if 'image' in proposal:
                    proposal_image = proposal['image']
                    image = {
                        'at': literal_eval(str(proposal_image['at']))
                        if 'at' in proposal_image else None,
                        'balance': literal_eval(str(proposal_image['balance']))
                        if 'balance' in proposal_image else None
                    }
                image_hash = proposal['imageHash'] if (
                        'imageHash' in proposal) else None
                proposer = proposal['proposer'] if (
                        'proposer' in proposal) else None
                seconds = proposal['seconds'] if 'seconds' in proposal else []
                seconded = {
                    gov_add: any(sec for sec in seconds if sec == gov_add)
                    for gov_add in gov_addresses
                }
                active_proposals.append({
                    'index': index,
                    'balance': balance,
                    'image': image,
                    'imageHash': image_hash,
                    'proposer': proposer,
                    'seconds': seconds,
                    'seconded': seconded
                })

            td_data['active_proposals'] = active_proposals
            td_data['active_proposals'].sort(key=lambda prop: prop['index'])

            td_data['referendum_count'] = literal_eval(str(
                td_data['referendum_count']))

            referendums = []

            for index, referendum in td_data['all_referendums'].items():
                if referendum:
                    for status, data in referendum.items():
                        approved = None if status == 'finished' else False
                        if status == 'finished' and 'approved' in data:
                            approved = data['approved']
                        end = data['end'] if 'end' in data else None
                        data_to_store = None

                        if status == 'ongoing':
                            data_to_store = {
                                'proposalHash': data['proposalHash'] if (
                                        'proposalHash' in data) else None,
                                'threshold': data['threshold'] if (
                                        'threshold' in data) else None,
                                'delay': (data['delay'] if 'delay' in data
                                          else None),
                                'voteCount': None,
                                'voteCountAye': None,
                                'voteCountNay': None,
                                'isPassing': None,
                                'votes': [],
                                'voted': {}
                            }

                            active_ref = next(
                                (ref for ref in td_data['active_referendums']
                                 if ref['imageHash'] == data['proposalHash']),
                                None)
                            if active_ref:
                                vote_count = active_ref['voteCount'] if (
                                        'voteCount' in active_ref) else None
                                vote_count_aye = active_ref['voteCountAye'] if (
                                        'voteCountAye' in active_ref) else None
                                vote_count_nay = active_ref['voteCountNay'] if (
                                        'voteCountNay' in active_ref) else None
                                is_passing = active_ref['isPassing'] if (
                                        'isPassing' in active_ref) else None
                                votes = []
                                voted = {
                                    gov_add: False for gov_add in gov_addresses
                                }
                                for vote in active_ref['votes']:
                                    account_id = vote['accountId'] if (
                                            'accountId' in vote) else None
                                    is_delegating = vote['isDelegating'] if (
                                            'isDelegating' in vote) else None
                                    vote_vote = vote['vote'] if (
                                            'vote' in vote) else None
                                    if vote_vote:
                                        vote_vote = False if literal_eval(
                                            str(vote_vote)) == 0 else True
                                    balance = vote['balance'] if (
                                            'balance' in vote) else None
                                    if balance:
                                        balance = literal_eval(str(balance))
                                    votes.append({
                                        "accountId": account_id,
                                        "isDelegating": is_delegating,
                                        "vote": vote_vote,
                                        "balance": balance
                                    })
                                    matched_address = next(
                                        (gov_add for gov_add in gov_addresses
                                         if gov_add == vote['accountId']), None)
                                    if matched_address:
                                        voted[matched_address] = True

                                data_to_store = {
                                    **data_to_store,
                                    **{
                                        'voteCount': vote_count,
                                        'voteCountAye': vote_count_aye,
                                        'voteCountNay': vote_count_nay,
                                        'isPassing': is_passing,
                                        'votes': votes,
                                        'voted': voted
                                    }
                                }

                        referendums.append({
                            'index': int(index), 'status': status,
                            'approved': approved, 'end': end,
                            'data': data_to_store
                        })

            referendums.sort(key=lambda ref: ref['index'])
            td_data['referendums'] = referendums

            del td_data['all_referendums']
            del td_data['active_referendums']
        elif 'error' in substrate_network_data:
            transformed_data = copy.deepcopy(substrate_network_data)
            del transformed_data['error']['meta_data']['monitor_name']
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _transform_websocket_data".format(self))

        return transformed_data

    def _transform_data(self, data: Dict) -> Tuple[Dict, Dict, Dict]:
        self.logger.debug("Performing data transformation on %s ...", data)
        processing_performed = False
        transformation_helper = {
            'websocket': self._transform_websocket_data,
        }
        transformed_data = {
            'websocket': {},
        }

        for data_type, transformation_fn in transformation_helper.items():
            if data_type in data and data[data_type]:
                processing_performed = True
                transformed_data[data_type] = transformation_fn(data[data_type])

        if not processing_performed:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _transform_data".format(self))

        data_for_alerting = self._process_transformed_data_for_alerting(
            transformed_data)
        data_for_saving = self._process_transformed_data_for_saving(
            transformed_data)

        self.logger.debug("Data transformation successful")

        return transformed_data, data_for_alerting, data_for_saving

    def _place_latest_data_on_queue(self, data_for_alerting: Dict,
                                    data_for_saving: Dict) -> None:
        self._push_to_queue(data_for_alerting, ALERT_EXCHANGE,
                            SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

        self._push_to_queue(data_for_saving, STORE_EXCHANGE,
                            SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

    def _validate_and_parse_raw_data_sources(
            self, raw_data: Dict) -> Tuple[str, str]:
        """
        This method checks the following things about the raw_data:
        1. Only valid sources are inside the raw_data
        2. All valid sources are inside the raw_data
        3. At least one source is not empty
        4. All source's data is indexed by 'result' or 'error' and all data
           has a 'parent_id', and 'chain_name'
        5. All parent_ids, and chain_names are equal across all
           sources
        :param raw_data: The raw_data being received from the monitor
        :return: parent_id, chain_name       : If valid raw_data
               : Raises ReceivedUnexpectedDataException   : otherwise
        """

        # Check that raw_data has all the valid sources and no other sources
        if set(raw_data.keys()) != set(VALID_SUBSTRATE_NETWORK_SOURCES):
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        list_of_sources_values = [value for source, value in raw_data.items()]

        # Check that at least one value is not empty
        if all(not value for value in list_of_sources_values):
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        # If all non-empty source data is not indexed by 'result' or 'error', or
        # some non-empty source data does not have `parent_id` or `chain_name`,
        # a  ReceivedUnexpectedDataException is raised.
        try:
            list_of_parent_ids = []
            list_of_chain_names = []
            for value in list_of_sources_values:
                if value:
                    response_index_key = (
                        'result' if 'result' in value
                        else 'error'
                    )
                    list_of_parent_ids.append(
                        value[response_index_key]['meta_data']['parent_id'])
                    list_of_chain_names.append(
                        value[response_index_key]['meta_data']['chain_name'])
        except KeyError:
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        # Check that all parent_ids and chain_names are equal. If a list has
        # identical elements, then when converted to a set there must be only 1
        # element in the set
        if (
                len(set(list_of_parent_ids)) != 1 or
                len(set(list_of_chain_names)) != 1
        ):
            raise ReceivedUnexpectedDataException(
                "{}: validate_and_parse_raw_data_sources".format(self))

        return list_of_parent_ids[0], list_of_chain_names[0]

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
            parent_id, chain_name = self._validate_and_parse_raw_data_sources(
                raw_data)

            if parent_id not in self.state:
                new_network = SubstrateNetwork(parent_id, chain_name)
                loaded_network = self.load_state(new_network)
                self._state[parent_id] = loaded_network

            transformed_data, data_for_alerting, data_for_saving = (
                self._transform_data(raw_data))
        except Exception as e:
            self.logger.error("Error when processing %s", raw_data)
            self.logger.exception(e)
            processing_error = True

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # We want to update the state after the data is acknowledged, otherwise
        # if acknowledgement fails the state would be erroneous when processing
        # the data again. Note, only update the state if there were no
        # processing errors. IMP: We are allowed to update the state before
        # sending the data because deep copies where constructed when computing
        # data_for_alerting, data_for_saving and transformed_data.
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
            self._place_latest_data_on_queue(data_for_alerting, data_for_saving)

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
