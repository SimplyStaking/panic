import copy
import json
import logging
from typing import Dict, Tuple

from src.data_store.redis import RedisApi, Keys
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.data import VALID_CHAINLINK_SOURCES, \
    RAW_TO_TRANSFORMED_CHAINLINK_METRICS, INT_CHAINLINK_METRICS
from src.utils.constants.rabbitmq import (RAW_DATA_EXCHANGE,
                                          CL_NODE_DT_INPUT_QUEUE_NAME,
                                          CHAINLINK_NODE_RAW_DATA_ROUTING_KEY,
                                          STORE_EXCHANGE, ALERT_EXCHANGE,
                                          HEALTH_CHECK_EXCHANGE)
from src.utils.exceptions import (ReceivedUnexpectedDataException,
                                  NodeIsDownException)
from src.utils.types import Monitorable, convert_to_float, convert_to_int


class ChainlinkNodeDataTransformer(DataTransformer):
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
        self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'", CL_NODE_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(CL_NODE_DT_INPUT_QUEUE_NAME, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", CL_NODE_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE, CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(CL_NODE_DT_INPUT_QUEUE_NAME, RAW_DATA_EXCHANGE,
                                 CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(CL_NODE_DT_INPUT_QUEUE_NAME,
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

    def load_state(self, cl_node: Monitorable) -> Monitorable:
        # Below, we will try and get the data stored in redis and store it
        # in the cl_node's state. If the data from Redis cannot be obtained, the
        # state won't be updated.

        self.logger.debug("Loading the state of %s from Redis", cl_node)
        redis_hash = Keys.get_hash_parent(cl_node.parent_id)
        cl_node_id = cl_node.node_id

        # Load current_height from Redis
        state_current_height = cl_node.current_height
        redis_current_height = self.redis.hget(
            redis_hash, Keys.get_cl_node_current_height(cl_node_id),
            bytes(str(state_current_height), 'utf-8'))
        redis_current_height = 'None' if redis_current_height is None \
            else redis_current_height.decode("utf-8")
        current_height = convert_to_int(redis_current_height, None)
        cl_node.set_current_height(current_height)

        # Load eth_blocks_in_queue from Redis
        state_eth_blocks_in_queue = cl_node.eth_blocks_in_queue
        redis_eth_blocks_in_queue = self.redis.hget(
            redis_hash, Keys.get_cl_node_eth_blocks_in_queue(cl_node_id),
            bytes(str(state_eth_blocks_in_queue), 'utf-8'))
        redis_eth_blocks_in_queue = 'None' if \
            redis_eth_blocks_in_queue is None \
            else redis_eth_blocks_in_queue.decode("utf-8")
        eth_blocks_in_queue = convert_to_int(redis_eth_blocks_in_queue, None)
        cl_node.set_eth_blocks_in_queue(eth_blocks_in_queue)

        # Load total_block_headers_received from Redis
        state_total_block_headers_received = \
            cl_node.total_block_headers_received
        redis_total_block_headers_received = self.redis.hget(
            redis_hash,
            Keys.get_cl_node_total_block_headers_received(cl_node_id),
            bytes(str(state_total_block_headers_received), 'utf-8'))
        redis_total_block_headers_received = 'None' if \
            redis_total_block_headers_received is None \
            else redis_total_block_headers_received.decode("utf-8")
        total_block_headers_received = convert_to_int(
            redis_total_block_headers_received, None)
        cl_node.set_total_block_headers_dropped(total_block_headers_received)

        # Load total_block_headers_dropped from Redis
        state_total_block_headers_dropped = cl_node.total_block_headers_dropped
        redis_total_block_headers_dropped = self.redis.hget(
            redis_hash,
            Keys.get_cl_node_total_block_headers_dropped(cl_node_id),
            bytes(str(state_total_block_headers_dropped), 'utf-8'))
        redis_total_block_headers_dropped = 'None' if \
            redis_total_block_headers_dropped is None \
            else redis_total_block_headers_dropped.decode("utf-8")
        total_block_headers_dropped = convert_to_int(
            redis_total_block_headers_dropped, None)
        cl_node.set_total_block_headers_dropped(total_block_headers_dropped)

        # Load no_of_active_jobs from Redis
        state_no_of_active_jobs = cl_node.no_of_active_jobs
        redis_no_of_active_jobs = self.redis.hget(
            redis_hash, Keys.get_cl_node_no_of_active_jobs(cl_node_id),
            bytes(str(state_no_of_active_jobs), 'utf-8'))
        redis_no_of_active_jobs = 'None' if redis_no_of_active_jobs is None \
            else redis_no_of_active_jobs.decode("utf-8")
        no_of_active_jobs = convert_to_int(redis_no_of_active_jobs, None)
        cl_node.set_no_of_active_jobs(no_of_active_jobs)

        # Load max_pending_tx_delay from Redis
        state_max_pending_tx_delay = cl_node.max_pending_tx_delay
        redis_max_pending_tx_delay = self.redis.hget(
            redis_hash, Keys.get_cl_node_max_pending_tx_delay(cl_node_id),
            bytes(str(state_max_pending_tx_delay), 'utf-8'))
        redis_max_pending_tx_delay = 'None' \
            if redis_max_pending_tx_delay is None \
            else redis_max_pending_tx_delay.decode("utf-8")
        max_pending_tx_delay = convert_to_int(redis_max_pending_tx_delay, None)
        cl_node.set_max_pending_tx_delay(max_pending_tx_delay)

        # Load process_start_time_seconds from Redis
        state_process_start_time_seconds = cl_node.process_start_time_seconds
        redis_process_start_time_seconds = self.redis.hget(
            redis_hash, Keys.get_cl_node_process_start_time_seconds(cl_node_id),
            bytes(str(state_process_start_time_seconds), 'utf-8'))
        redis_process_start_time_seconds = 'None' \
            if redis_process_start_time_seconds is None \
            else redis_process_start_time_seconds.decode("utf-8")
        process_start_time_seconds = convert_to_float(
            redis_process_start_time_seconds, None)
        cl_node.set_process_start_time_seconds(process_start_time_seconds)

        # Load total_gas_bumps from Redis
        state_total_gas_bumps = cl_node.total_gas_bumps
        redis_total_gas_bumps = self.redis.hget(
            redis_hash, Keys.get_cl_node_total_gas_bumps(cl_node_id),
            bytes(str(state_total_gas_bumps), 'utf-8'))
        redis_total_gas_bumps = 'None' if redis_total_gas_bumps is None \
            else redis_total_gas_bumps.decode("utf-8")
        total_gas_bumps = convert_to_int(redis_total_gas_bumps, None)
        cl_node.set_total_gas_bumps(total_gas_bumps)

        # Load total_gas_bumps_exceeds_limit from Redis
        state_total_gas_bumps_exceeds_limit = \
            cl_node.total_gas_bumps_exceeds_limit
        redis_total_gas_bumps_exceeds_limit = self.redis.hget(
            redis_hash,
            Keys.get_cl_node_total_gas_bumps_exceeds_limit(cl_node_id),
            bytes(str(state_total_gas_bumps_exceeds_limit), 'utf-8'))
        redis_total_gas_bumps_exceeds_limit = 'None' if \
            redis_total_gas_bumps_exceeds_limit is None \
            else redis_total_gas_bumps_exceeds_limit.decode("utf-8")
        total_gas_bumps_exceeds_limit = convert_to_int(
            redis_total_gas_bumps_exceeds_limit, None)
        cl_node.set_total_gas_bumps_exceeds_limit(total_gas_bumps_exceeds_limit)

        # Load no_of_unconfirmed_txs from Redis
        state_no_of_unconfirmed_txs = cl_node.no_of_unconfirmed_txs
        redis_no_of_unconfirmed_txs = self.redis.hget(
            redis_hash, Keys.get_cl_node_no_of_unconfirmed_txs(cl_node_id),
            bytes(str(state_no_of_unconfirmed_txs), 'utf-8'))
        redis_no_of_unconfirmed_txs = 'None' if \
            redis_no_of_unconfirmed_txs is None \
            else redis_no_of_unconfirmed_txs.decode("utf-8")
        no_of_unconfirmed_txs = convert_to_int(redis_no_of_unconfirmed_txs,
                                               None)
        cl_node.set_no_of_unconfirmed_txs(no_of_unconfirmed_txs)

        # Load total_errored_job_runs from Redis
        state_total_errored_job_runs = cl_node.total_errored_job_runs
        redis_total_errored_job_runs = self.redis.hget(
            redis_hash, Keys.get_cl_node_total_errored_job_runs(cl_node_id),
            bytes(str(state_total_errored_job_runs), 'utf-8'))
        redis_total_errored_job_runs = 'None' if \
            redis_total_errored_job_runs is None \
            else redis_total_errored_job_runs.decode("utf-8")
        total_errored_job_runs = convert_to_int(redis_total_errored_job_runs,
                                                None)
        cl_node.set_total_errored_job_runs(total_errored_job_runs)

        # Load current_gas_price_info from Redis
        state_current_gas_price_info = cl_node.current_gas_price_info
        redis_current_gas_price_info = self.redis.hget(
            redis_hash, Keys.get_cl_node_current_gas_price_info(cl_node_id),
            bytes(json.dumps(state_current_gas_price_info), 'utf-8'))
        current_gas_price_info = {
            'percentile': None,
            'price': None,
        } if redis_current_gas_price_info is None \
            else json.loads(redis_current_gas_price_info.decode("utf-8"))
        cl_node.set_current_gas_price_info(current_gas_price_info['percentile'],
                                           current_gas_price_info['price'])

        # Load eth_balance_info from Redis
        state_eth_balance_info = cl_node.eth_balance_info
        redis_eth_balance_info = self.redis.hget(
            redis_hash, Keys.get_cl_node_eth_balance_info(cl_node_id),
            bytes(json.dumps(state_eth_balance_info), 'utf-8'))
        eth_balance_info = {} if redis_eth_balance_info is None \
            else json.loads(redis_eth_balance_info.decode("utf-8"))
        cl_node.set_eth_balance_info(eth_balance_info)

        # Load went_down_at from Redis
        state_went_down_at = cl_node.went_down_at
        redis_went_down_at = self.redis.hget(
            redis_hash, Keys.get_cl_node_went_down_at(cl_node_id),
            bytes(str(state_went_down_at), 'utf-8'))
        redis_went_down_at = 'None' if redis_went_down_at is None \
            else redis_went_down_at.decode("utf-8")
        went_down_at = convert_to_float(redis_went_down_at, None)
        cl_node.set_went_down_at(went_down_at)

        # Load last_prometheus_source_used from Redis
        state_last_prometheus_source_used = cl_node.last_prometheus_source_used
        redis_last_prometheus_source_used = self.redis.hget(
            redis_hash,
            Keys.get_cl_node_last_prometheus_source_used(cl_node_id),
            bytes(str(state_last_prometheus_source_used), 'utf-8'))
        last_prometheus_source_used = redis_last_prometheus_source_used.decode(
            'utf-8')
        cl_node.set_last_prometheus_source_used(last_prometheus_source_used)

        # Load last_monitored_prometheus from Redis
        state_last_monitored_prometheus = cl_node.last_monitored_prometheus
        redis_last_monitored_prometheus = self.redis.hget(
            redis_hash, Keys.get_cl_node_last_monitored_prometheus(cl_node_id),
            bytes(str(state_last_monitored_prometheus), 'utf-8'))
        redis_last_monitored_prometheus = 'None' if \
            redis_last_monitored_prometheus is None \
            else redis_last_monitored_prometheus.decode("utf-8")
        last_monitored_prometheus = convert_to_float(
            redis_last_monitored_prometheus, None)
        cl_node.set_last_monitored_prometheus(last_monitored_prometheus)

        self.logger.debug(
            "Restored %s state: _current_height=%s, _eth_blocks_in_queue=%s, "
            "_total_block_headers_received=%s, "
            "_total_block_headers_dropped=%s, _no_of_active_jobs=%s, "
            "_max_pending_tx_delay=%s, _process_start_time_seconds=%s, "
            "_total_gas_bumps=%s, _total_gas_bumps_exceeds_limit=%s, "
            "_no_of_unconfirmed_txs=%s, _total_errored_job_runs=%s, "
            "_current_gas_price_info=%s, _eth_balance_info=%s, "
            "_last_monitored_prometheus=%s, _last_prometheus_source_used=%s, "
            "_went_down_at=%s", cl_node, current_height, eth_blocks_in_queue,
            total_block_headers_received, total_block_headers_dropped,
            no_of_active_jobs, max_pending_tx_delay, process_start_time_seconds,
            total_gas_bumps, total_gas_bumps_exceeds_limit,
            no_of_unconfirmed_txs, total_errored_job_runs,
            current_gas_price_info, eth_balance_info, last_monitored_prometheus,
            last_prometheus_source_used, went_down_at)

        return cl_node

    def _update_state(self, transformed_data: Dict) -> None:
        self.logger.debug("Updating state ...")

        if transformed_data['prometheus']:
            if 'result' in transformed_data:
                meta_data = transformed_data['prometheus']['result'][
                    'meta_data']
                metrics = transformed_data['prometheus']['result']['data']
                node_id = meta_data['node_id']
                parent_id = meta_data['node_parent_id']
                node_name = meta_data['node_name']
                node = self.state[node_id]

                # Set node details just in case the configs have changed
                node.set_parent_id(parent_id)
                node.set_node_name(node_name)

                # Save the new metrics in process memory
                node.set_current_height(metrics['current_height'])
                node.set_eth_blocks_in_queue(metrics['eth_blocks_in_queue'])
                node.set_total_block_headers_received(
                    metrics['total_block_headers_received'])
                node.set_total_block_headers_dropped(
                    metrics['total_block_headers_dropped'])
                node.set_no_of_active_jobs(metrics['no_of_active_jobs'])
                node.set_max_pending_tx_delay(metrics['max_pending_tx_delay'])
                node.set_process_start_time_seconds(
                    metrics['process_start_time_seconds'])
                node.set_total_gas_bumps(metrics['total_gas_bumps'])
                node.set_total_gas_bumps_exceeds_limit(
                    metrics['total_gas_bumps_exceeds_limit'])
                node.set_no_of_unconfirmed_txs(metrics['no_of_unconfirmed_txs'])
                node.set_total_errored_job_runs(
                    metrics['total_errored_job_runs'])

                # If gas_updater_set_gas_price was disabled, set the metrics to
                # None
                if metrics['current_gas_price_info'] is None:
                    node.set_current_gas_price_info(None, None)
                else:
                    node.set_current_gas_price_info(metrics['percentile'],
                                                    metrics['price'])

                node.set_eth_balance_info(metrics['eth_balance_info'])
                node.set_last_monitored_prometheus(meta_data['last_monitored'])
                node.set_last_prometheus_source_used(
                    meta_data['last_source_used'])
                node.set_as_up()
            elif 'error' in transformed_data:
                meta_data = transformed_data['prometheus']['error']['meta_data']
                error_code = transformed_data['prometheus']['error']['code']
                node_id = meta_data['node_id']
                parent_id = meta_data['node_parent_id']
                node_name = meta_data['node_name']
                downtime_exception = NodeIsDownException(node_name)
                node = self.state[node_id]

                # Set node details just in case the configs have changed
                node.set_parent_id(parent_id)
                node.set_node_name(node_name)

                # To store which source errored if an error unrelated to
                # downtime is received. Reminder: In the monitor
                # last_source_used is not updated if a downtime error is
                # detected, as it means that no source was used.
                node.set_last_prometheus_source_used(
                    meta_data['last_source_used'])

                if error_code == downtime_exception.code:
                    new_went_down_at = transformed_data['prometheus']['error'][
                        'data']['went_down_at']
                    node.set_as_down(new_went_down_at)
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _update_state".format(self))
        else:
            # If no data source is enabled, then we shouldn't have received the
            # data in the first place.
            raise ReceivedUnexpectedDataException(
                "{}: _update_state".format(self))

        self.logger.debug("State updated successfully")

    def _process_transformed_data_for_saving(self,
                                             transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for storage ...")

        # We must check that the source's data is valid
        for source in VALID_CHAINLINK_SOURCES:
            if 'result' not in transformed_data[source] \
                    and 'error' not in transformed_data[source]:
                raise ReceivedUnexpectedDataException(
                    "{}: _process_transformed_data_for_saving".format(self))

        return copy.deepcopy(transformed_data)

    def _process_transformed_data_for_alerting(self,
                                               transformed_data: Dict) -> Dict:
        self.logger.debug("Performing further processing for alerting ...")

        if transformed_data['prometheus']:
            if 'result' in transformed_data:
                td_meta_data = transformed_data['prometheus']['result'][
                    'meta_data']
                td_node_id = td_meta_data['node_id']
                node = self.state[td_node_id]
                td_metrics = transformed_data['prometheus']['result']['data']

                processed_data = {
                    'prometheus': {
                        'result': {
                            'meta_data': copy.deepcopy(td_meta_data),
                            'data': {}
                        }
                    }
                }

                pd_meta_data = processed_data['prometheus']['result'][
                    'meta_data']
                pd_data = processed_data['prometheus']['result']['data']

                # Do current and previous for last_source_used
                pd_meta_data['last_source_used'] = {
                    'current': td_meta_data['last_source_used'],
                    'previous': node.last_prometheus_source_used
                }

                # Reformat the data in such a way that both the previous and
                # current states are sent to the alerter
                for metric, value in td_metrics.items():
                    pd_data[metric] = {}
                    pd_data[metric]['current'] = value

                pd_data['current_height']['previous'] = node.current_height
                pd_data['eth_blocks_in_queue'][
                    'previous'] = node.eth_blocks_in_queue
                pd_data['total_block_headers_received'][
                    'previous'] = node.total_block_headers_received
                pd_data['total_block_headers_dropped'][
                    'previous'] = node.total_block_headers_dropped
                pd_data['no_of_active_jobs'][
                    'previous'] = node.no_of_active_jobs
                pd_data['max_pending_tx_delay'][
                    'previous'] = node.max_pending_tx_delay
                pd_data['process_start_time_seconds'][
                    'previous'] = node.process_start_time_seconds
                pd_data['total_gas_bumps']['previous'] = node.total_gas_bumps
                pd_data['total_gas_bumps_exceeds_limit'][
                    'previous'] = node.total_gas_bumps_exceeds_limit
                pd_data['no_of_unconfirmed_txs'][
                    'previous'] = node.no_of_unconfirmed_txs
                pd_data['total_errored_job_runs'][
                    'previous'] = node.total_errored_job_runs
                pd_data['current_gas_price_info'][
                    'previous'] = node.current_gas_price_info
                pd_data['eth_balance_info']['previous'] = node.eth_balance_info
                pd_data['went_down_at']['previous'] = node.went_down_at
            elif 'error' in transformed_data:
                pass
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _process_transformed_data_for_alerting".format(self))
        else:
            raise ReceivedUnexpectedDataException(
                "{}: _process_transformed_data_for_alerting".format(self))

        # if 'result' in transformed_data:
        #     pass
        # elif 'error' in transformed_data:
        #     td_meta_data = transformed_data['error']['meta_data']
        #     td_error_code = transformed_data['error']['code']
        #     td_system_id = td_meta_data['system_id']
        #     td_system_name = td_meta_data['system_name']
        #     system = self.state[td_system_id]
        #     downtime_exception = SystemIsDownException(td_system_name)
        #
        #     processed_data = copy.deepcopy(transformed_data)
        #
        #     if td_error_code == downtime_exception.code:
        #         td_metrics = transformed_data['error']['data']
        #         processed_data_metrics = processed_data['error']['data']
        #
        #         for metric, value in td_metrics.items():
        #             processed_data_metrics[metric] = {}
        #             processed_data_metrics[metric]['current'] = value
        #
        #         processed_data_metrics['went_down_at']['previous'] = \
        #             system.went_down_at
        # else:
        #     raise ReceivedUnexpectedDataException(
        #         "{}: _process_transformed_data_for_alerting".format(self))

        self.logger.debug("Processing successful.")

        return processed_data

    def _transform_data(self, data: Dict) -> Tuple[Dict, Dict, Dict]:
        self.logger.debug("Performing data transformation on %s ...", data)

        if data['prometheus']:
            if 'result' in data:
                meta_data = data['prometheus']['result']['meta_data']
                node_metrics = data['prometheus']['result']['data']
                node_id = meta_data['node_id']
                node = self.state[node_id]
                transformed_data = copy.deepcopy(data)
                td_meta_data = transformed_data['prometheus']['result'][
                    'meta_data']
                td_node_metrics = transformed_data['prometheus']['result'][
                    'data']

                # First convert the raw metric names into the transformed names
                for raw_metric, transformed_metric in \
                        RAW_TO_TRANSFORMED_CHAINLINK_METRICS.items():
                    del td_node_metrics[raw_metric]
                    td_node_metrics[transformed_metric] = node_metrics[
                        raw_metric]

                # Convert the int metric values
                for transformed_metric in INT_CHAINLINK_METRICS:
                    td_node_metrics[transformed_metric] = convert_to_int(
                        td_node_metrics[transformed_metric], None)

                # If the metric is enabled, transform the
                # current_gas_price_info's percentile into the correct type.
                # Note that the raw value is a string.
                if td_node_metrics['current_gas_price_info']:
                    str_percentile = td_node_metrics['current_gas_price_info'][
                        'percentile']
                    td_node_metrics['current_gas_price_info'][
                        'percentile'] = convert_to_float(
                        str_percentile.replace('%', ''), None)

                # Add latest_usage to the eth_balance_info
                for eth_address, new_balance \
                        in node_metrics['ethereum_balances'].items():
                    if eth_address in node.eth_balance_info:
                        previous_balance = node.eth_balance_info[eth_address][
                            'balance']
                        new_info_dict = {
                            'balance': new_balance,
                            'latest_usage': previous_balance - new_balance if
                            previous_balance > new_balance else 0.0
                        }
                    else:
                        new_info_dict = {
                            'balance': new_balance,
                            'latest_usage': 0.0
                        }

                    td_node_metrics[eth_address] = new_info_dict

                # Transform the meta_data by deleting the monitor_name and
                # changing the time key to last_monitored key
                del td_meta_data['monitor_name']
                del td_meta_data['time']
                td_meta_data['last_monitored'] = meta_data['time']
                td_node_metrics['went_down_at'] = None
            elif 'error' in data:
                meta_data = data['prometheus']['error']['meta_data']
                error_code = data['prometheus']['error']['code']
                node_id = meta_data['node_id']
                node_name = meta_data['node_name']
                time_of_error = meta_data['time']
                node = self.state[node_id]
                downtime_exception = NodeIsDownException(node_name)

                # In case of non-downtime errors only remove the monitor_name
                # from the meta data
                transformed_data = copy.deepcopy(data)
                del transformed_data['prometheus']['error']['meta_data'][
                    'monitor_name']

                # If we have a downtime error, set went_down_at to the time of
                # error if the node was up. Otherwise, leave went_down_at as
                # stored in the node state
                if error_code == downtime_exception.code:
                    transformed_data['prometheus']['error']['data'] = {}
                    td_metrics = transformed_data['prometheus']['error']['data']
                    td_metrics['went_down_at'] = \
                        node.went_down_at if node.is_down else time_of_error
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _transform_data".format(self))
        else:
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

# TODO: In start check that system_ids and parent_ids of data are equal, all
#     : data is there (like prometheus etc (even if empty)).. also, check that
#     : at least one data is not empty ... so in other words do
#     : data validation. Check that keys are equal to prometheus, rpc etc
