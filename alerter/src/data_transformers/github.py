import copy
import json
import logging
from datetime import datetime
from typing import Dict, Union

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis.redis_api import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_transformers.data_transformer import DataTransformer
from src.monitorables.repo import GitHubRepo
from src.monitorables.system import System
from src.utils.constants import RAW_DATA_EXCHANGE, STORE_EXCHANGE, \
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import ReceivedUnexpectedDataException, \
    MessageWasNotDeliveredException
from src.utils.types import convert_to_float_if_not_none, \
    convert_to_int_if_not_none


class GitHubDataTransformer(DataTransformer):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi) -> None:
        super().__init__(transformer_name, logger, redis)

    def _initialize_rabbitmq(self) -> None:
        # A data transformer is both a consumer and producer, therefore we need
        # to initialize both the consuming and producing configurations.

        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '{}' exchange".format(RAW_DATA_EXCHANGE))
        self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, 'direct', False, True,
                                       False, False)
        self.logger.info(
            "Creating queue 'github_data_transformer_raw_data_queue'")
        self.rabbitmq.queue_declare(
            'github_data_transformer_raw_data_queue', False, True, False,
            False)
        self.logger.info(
            "Binding queue 'github_data_transformer_raw_data_queue' to "
            "exchange '{}' with routing key 'github'".format(
                RAW_DATA_EXCHANGE))
        self.rabbitmq.queue_bind('github_data_transformer_raw_data_queue',
                                 RAW_DATA_EXCHANGE, 'github')

        # Pre-fetch count is 10 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.info('Declaring consuming intentions')
        self.rabbitmq.basic_consume('github_data_transformer_raw_data_queue',
                                    self._process_raw_data, False, False, None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '{}' exchange".format(STORE_EXCHANGE))
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, 'direct', False, True,
                                       False, False)
        self.logger.info("Creating '{}' exchange".format(ALERT_EXCHANGE))
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating '{}' exchange".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def load_state(self, repo: Union[System, GitHubRepo]) \
            -> Union[System, GitHubRepo]:
        # If Redis is down, the data passed as default will be stored as
        # the repo state.

        self.logger.debug("Loading the state of {} from Redis".format(repo))
        redis_hash = Keys.get_hash_parent(repo.parent_id)
        repo_id = repo.repo_id

        # Below, we will try and get the data stored in redis and store it
        # in the repo's state. If the data from Redis cannot be obtained, the
        # state won't be updated.

        # Load no_of_releases from Redis
        state_no_of_releases = repo.no_of_releases
        redis_no_of_releases = self.redis.hget(
            redis_hash, Keys.get_github_no_of_releases(repo_id),
            state_no_of_releases)
        no_of_releases = \
            convert_to_int_if_not_none(redis_no_of_releases, None)
        repo.set_no_of_releases(no_of_releases)

        # Load last_monitored from Redis
        state_last_monitored = repo.last_monitored
        redis_last_monitored = self.redis.hget(
            redis_hash, Keys.get_github_last_monitored(repo_id),
            state_last_monitored)
        last_monitored = \
            convert_to_float_if_not_none(redis_last_monitored, None)
        repo.set_last_monitored(last_monitored)

        self.logger.debug(
            "Restored %s state: _no_of_releases=%s, _last_monitored=%s", repo,
            no_of_releases, last_monitored)

        return repo

    def _update_state(self) -> None:
        self.logger.debug("Updating state ...")

        if 'result' in self.transformed_data:
            meta_data = self.transformed_data['result']['meta_data']
            metrics = self.transformed_data['result']['data']
            repo_id = meta_data['repo_id']
            parent_id = meta_data['repo_parent_id']
            repo_name = meta_data['repo_name']
            repo = self.state[repo_id]

            # Set repo details just in case the configs have changed
            repo.set_parent_id(parent_id)
            repo.set_repo_name(repo_name)

            # Save the new metrics
            repo.set_last_monitored(meta_data['last_monitored'])
            repo.set_no_of_releases(metrics['no_of_releases'])
        elif 'error' in self.transformed_data:
            meta_data = self.transformed_data['error']['meta_data']
            repo_name = meta_data['repo_name']
            repo_id = meta_data['repo_id']
            parent_id = meta_data['repo_parent_id']
            repo = self.state[repo_id]

            # Set repo details just in case the configs have changed
            repo.set_parent_id(parent_id)
            repo.set_repo_name(repo_name)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _update_state".format(self))

        self.logger.debug("State updated successfully")

    def _process_transformed_data_for_saving(self) -> None:
        self.logger.debug("Performing further processing for storage ...")

        if 'result' in self.transformed_data:
            td_meta_data = self.transformed_data['result']['meta_data']
            td_metrics = self.transformed_data['result']['data']
            no_of_releases = td_metrics['no_of_releases']

            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {
                        'no_of_releases': no_of_releases
                    }
                }
            }
        elif 'error' in self.transformed_data:
            processed_data = copy.deepcopy(self.transformed_data)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_saving".format(self))

        self._data_for_saving = processed_data

        self.logger.debug("Processing successful")

    def _process_transformed_data_for_alerting(self) -> None:
        self.logger.debug("Performing further processing for alerting ...")

        if 'result' in self.transformed_data:
            td_meta_data = self.transformed_data['result']['meta_data']
            td_repo_id = td_meta_data['repo_id']
            repo = self.state[td_repo_id]
            td_metrics = self.transformed_data['result']['data']

            processed_data = {
                'result': {
                    'meta_data': copy.deepcopy(td_meta_data),
                    'data': {}
                }
            }

            # Reformat the data in such a way that both the previous and current
            # states are sent to the alerter. Exclude the releases list, as the
            # previous list can be inferred.
            processed_data_metrics = processed_data['result']['data']
            for metric, value in td_metrics.items():
                if metric != 'releases':
                    processed_data_metrics[metric] = {}
                    processed_data_metrics[metric]['current'] = value

            # Add the previous state
            processed_data_metrics['no_of_releases']['previous'] = \
                repo.no_of_releases

            # Finally add the list of releases
            processed_data_metrics['releases'] = \
                copy.deepcopy(td_metrics['releases'])
        elif 'error' in self.transformed_data:
            processed_data = copy.deepcopy(self.transformed_data)
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_alerting".format(self))

        self._data_for_alerting = processed_data

        self.logger.debug("Processing successful.")

    def _transform_data(self, data: Dict) -> None:
        self.logger.debug("Performing data transformation on {} ..."
                          .format(data))

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

            # Transform the data by adding the no_of_releases and releases
            # metrics.
            td_metrics['no_of_releases'] = len(repo_metrics)
            td_metrics['releases'] = copy.deepcopy(repo_metrics)
        elif 'error' in data:
            # In case of errors in the sent messages only remove the
            # monitor_name from the meta data
            transformed_data = copy.deepcopy(data)
            del transformed_data['error']['meta_data']['monitor_name']
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _transform_data".format(self))

        self._transformed_data = transformed_data
        self._process_transformed_data_for_alerting()
        self._process_transformed_data_for_saving()
        self.logger.debug("Data transformation successful")

    def _place_latest_data_on_queue(self) -> None:
        self.logger.debug("Adding transformed data to the publishing queue ...")

        # Place the latest transformed data on the publishing queue. If the
        # queue is full, remove old data.
        if self.publishing_queue.full():
            self.publishing_queue.get()
            self.publishing_queue.get()
        self.publishing_queue.put({
            'exchange': STORE_EXCHANGE, 'routing_key': 'github',
            'data': copy.deepcopy(self.data_for_saving)})
        self.publishing_queue.put({
            'exchange': ALERT_EXCHANGE, 'routing_key': 'alerter.github',
            'data': copy.deepcopy(self.data_for_alerting)})

        self.logger.debug("Transformed data added to the publishing queue "
                          "successfully.")

    def _process_raw_data(self, ch: BlockingChannel,
                          method: pika.spec.Basic.Deliver,
                          properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        raw_data = json.loads(body)
        self.logger.info("Received {} from monitors. Now processing this data."
                         .format(raw_data))

        processing_error = False
        try:
            if 'result' in raw_data or 'error' in raw_data:
                response_index_key = 'result' if 'result' in raw_data \
                    else 'error'
                meta_data = raw_data[response_index_key]['meta_data']
                repo_id = meta_data['repo_id']
                repo_parent_id = meta_data['repo_parent_id']
                repo_name = meta_data['repo_name']

                if repo_id not in self.state:
                    new_repo = GitHubRepo(repo_name, repo_id, repo_parent_id)
                    loaded_repo = self.load_state(new_repo)
                    self._state[repo_id] = loaded_repo

                self._transform_data(raw_data)
                self._update_state()
                self.logger.info("Successfully processed {}".format(raw_data))
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _process_raw_data".format(self))
        except Exception as e:
            self.logger.error("Error when processing {}".format(raw_data))
            self.logger.exception(e)
            processing_error = True

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # Place the data on the publishing queue if there were no processing
        # errors. This is done after acknowledging the data, so that if
        # acknowledgement fails, the data is processed again and we do not have
        # duplication of data in the queue
        if not processing_error:
            self._place_latest_data_on_queue()

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()

            if not processing_error:
                heartbeat = {
                    'component_name': self.transformer_name,
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
