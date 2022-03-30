import copy
import json
import logging
from datetime import datetime
from typing import Dict, Tuple

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis.redis_api import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.repo import DockerHubRepo
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, STORE_EXCHANGE, ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    DOCKERHUB_DT_INPUT_QUEUE_NAME, DOCKERHUB_RAW_DATA_ROUTING_KEY,
    DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY, TOPIC)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from src.utils.types import (convert_to_float, Monitorable)


class DockerHubDataTransformer(DataTransformer):
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
        self.logger.info("Creating queue '%s'", DOCKERHUB_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(DOCKERHUB_DT_INPUT_QUEUE_NAME, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", DOCKERHUB_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE, DOCKERHUB_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(DOCKERHUB_DT_INPUT_QUEUE_NAME,
                                 RAW_DATA_EXCHANGE,
                                 DOCKERHUB_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug('Declaring consuming intentions')
        self.rabbitmq.basic_consume(DOCKERHUB_DT_INPUT_QUEUE_NAME,
                                    self._process_raw_data,
                                    False, False, None)

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

    def load_state(self, repo: Monitorable) -> Monitorable:
        # Below, we will try and get the data stored in redis and store it
        # in the repo's state. If the data from Redis cannot be obtained, the
        # state won't be updated.

        self.logger.debug("Loading the state of %s from Redis", repo)
        redis_hash = Keys.get_hash_parent(repo.parent_id)
        repo_id = repo.repo_id

        # Load tags from Redis
        state_tags = repo.tags
        default_state_tags = None if state_tags is None else bytes(json.dumps(
            state_tags), 'utf-8')
        redis_tags = self.redis.hget(redis_hash,
                                     Keys.get_dockerhub_last_tags(repo_id),
                                     default_state_tags)
        tags = None if redis_tags is None else json.loads(
            redis_tags.decode('utf-8'))
        repo.set_tags(tags)

        # Load last_monitored from Redis
        state_last_monitored = repo.last_monitored
        redis_last_monitored = self.redis.hget(
            redis_hash, Keys.get_dockerhub_last_monitored(repo_id),
            bytes(str(state_last_monitored), 'utf-8'))
        redis_last_monitored = 'None' if redis_last_monitored is None \
            else redis_last_monitored.decode("utf-8")
        last_monitored = convert_to_float(redis_last_monitored, None)
        repo.set_last_monitored(last_monitored)

        self.logger.debug(
            "Restored %s state: last_monitored=%s, tags=%s", repo,
            last_monitored, tags)

        return repo

    def _update_state(self, transformed_data: Dict) -> None:
        self.logger.debug("Updating state ...")

        if 'result' in transformed_data:
            meta_data = transformed_data['result']['meta_data']
            metrics = transformed_data['result']['data']
            repo_id = meta_data['repo_id']
            parent_id = meta_data['repo_parent_id']
            repo_namespace = meta_data['repo_namespace']
            repo_name = meta_data['repo_name']
            repo = self.state[repo_id]

            # Set repo details just in case the configs have changed
            repo.set_parent_id(parent_id)
            repo.set_repo_namespace(repo_namespace)
            repo.set_repo_name(repo_name)

            # Save the new metrics
            repo.set_last_monitored(meta_data['last_monitored'])
            repo.set_tags(metrics['tags'])
        elif 'error' in transformed_data:
            meta_data = transformed_data['error']['meta_data']
            repo_namespace = meta_data['repo_namespace']
            repo_name = meta_data['repo_name']
            repo_id = meta_data['repo_id']
            parent_id = meta_data['repo_parent_id']
            repo = self.state[repo_id]

            # Set repo details just in case the configs have changed
            repo.set_parent_id(parent_id)
            repo.set_repo_namespace(repo_namespace)
            repo.set_repo_name(repo_name)

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
            td_repo_id = td_meta_data['repo_id']
            repo = self.state[td_repo_id]
            td_metrics = transformed_data['result']['data']

            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {}
                }
            }

            # Reformat the data in such a way that both the previous and current
            # states are sent to the alerter.
            processed_data_metrics = processed_data['result']['data']
            for metric, value in td_metrics.items():
                if metric == 'tags':
                    processed_data_metrics['current'] = {}
                    processed_data_metrics['current'] = value

                    # Add the previous tags state
                    processed_data_metrics['previous'] = (
                        copy.deepcopy(repo.tags))

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
            repo_metrics = data['result']['data']

            transformed_data = {
                'result': {
                    'meta_data': copy.deepcopy(meta_data),
                    'data': {},
                }
            }
            td_meta_data = transformed_data['result']['meta_data']
            td_metrics = transformed_data['result']['data']

            # Transform the meta_data by deleting the monitor_name and changing
            # the time key to last_monitored key
            del td_meta_data['monitor_name']
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']
            td_metrics['tags'] = copy.deepcopy(repo_metrics)

        elif 'error' in data:
            # In case of errors in the sent messages only remove the
            # monitor_name from the meta data
            transformed_data = copy.deepcopy(data)
            del transformed_data['error']['meta_data']['monitor_name']
        else:
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
                            DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)
        self._push_to_queue(data_for_saving, STORE_EXCHANGE,
                            DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY,
                            pika.BasicProperties(delivery_mode=2), True)

    def _process_raw_data(self, ch: BlockingChannel,
                          method: pika.spec.Basic.Deliver,
                          properties: pika.spec.BasicProperties,
                          body: bytes) -> None:
        raw_data = json.loads(body)
        self.logger.debug("Received %s from monitors. Now processing this "
                          "data.", raw_data)

        processing_error = False
        transformed_data = {}
        data_for_alerting = {}
        data_for_saving = {}
        try:
            if 'result' in raw_data or 'error' in raw_data:
                response_index_key = 'result' if 'result' in raw_data \
                    else 'error'
                meta_data = raw_data[response_index_key]['meta_data']
                repo_id = meta_data['repo_id']
                repo_parent_id = meta_data['repo_parent_id']
                repo_namespace = meta_data['repo_namespace']
                repo_name = meta_data['repo_name']

                if repo_id not in self.state:
                    new_repo = DockerHubRepo(repo_namespace, repo_name, repo_id,
                                             repo_parent_id)
                    loaded_repo = self.load_state(new_repo)
                    self._state[repo_id] = loaded_repo

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
