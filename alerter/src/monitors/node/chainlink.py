import copy
import json
import logging
from collections import ChainMap, defaultdict
from datetime import datetime, timedelta
from http.client import IncompleteRead
from typing import Dict, Callable

import pika
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.monitor import Monitor
from src.utils.constants.data import CHAINLINK_CHAINS_URL
from src.utils.constants.rabbitmq import (RAW_DATA_EXCHANGE,
                                          CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
from src.utils.data import get_prometheus_metrics_data, get_json
from src.utils.exceptions import (NodeIsDownException, PANICException,
                                  DataReadingException, InvalidUrlException,
                                  MetricNotFoundException)
from src.utils.timing import TimedTaskLimiter


class ChainlinkNodeMonitor(Monitor):
    def __init__(self, monitor_name: str, node_config: ChainlinkNodeConfig,
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        node_config.enabled_sources_non_empty()

        super().__init__(monitor_name, logger, monitor_period, rabbitmq)
        self._node_config = node_config
        self._prometheus_metrics = {
            'head_tracker_current_head': 'strict',
            'head_tracker_heads_received_total': 'strict',
            'max_unconfirmed_blocks': 'strict',
            'process_start_time_seconds': 'strict',
            'tx_manager_num_gas_bumps_total': 'optional',
            'tx_manager_gas_bump_exceeds_limit_total': 'optional',
            'unconfirmed_transactions': 'strict',
            'gas_updater_set_gas_price': 'optional',
            'eth_balance': 'strict',
            'run_status_update_total': 'optional',
        }
        self._last_prometheus_source_used = node_config.node_prometheus_urls[0]
        self._currency_symbol_limiter = TimedTaskLimiter(timedelta(hours=24))
        self._currency_symbol = ''

    @property
    def node_config(self) -> ChainlinkNodeConfig:
        return self._node_config

    @property
    def prometheus_metrics(self) -> Dict[str, str]:
        return self._prometheus_metrics

    @property
    def last_prometheus_source_used(self) -> str:
        return self._last_prometheus_source_used

    @property
    def currency_symbol_limiter(self) -> TimedTaskLimiter:
        return self._currency_symbol_limiter

    @property
    def currency_symbol(self) -> str:
        return self._currency_symbol

    def _display_data(self, data: Dict) -> str:
        # This function attempts to display all metric values. If a particular
        # source is disabled, then that metric will not appear in the data, so
        # by default 'Disabled' is outputted
        data_defaultdict = defaultdict(lambda: 'Disabled')
        for metric, value in data.items():
            data_defaultdict[metric] = value

        return (
            "head_tracker_current_head={}, "
            "head_tracker_heads_received_total={}, max_unconfirmed_blocks={}, "
            "process_start_time_seconds={}, tx_manager_num_gas_bumps_total={}, "
            "tx_manager_gas_bump_exceeds_limit_total={}, "
            "unconfirmed_transactions={}, gas_updater_set_gas_price={}, "
            "balance={}, run_status_update_total_errors={}"
            "".format(
                data_defaultdict['head_tracker_current_head'],
                data_defaultdict['head_tracker_heads_received_total'],
                data_defaultdict['max_unconfirmed_blocks'],
                data_defaultdict['process_start_time_seconds'],
                data_defaultdict['tx_manager_num_gas_bumps_total'],
                data_defaultdict['tx_manager_gas_bump_exceeds_limit_total'],
                data_defaultdict['unconfirmed_transactions'],
                data_defaultdict['gas_updater_set_gas_price'],
                data_defaultdict['balance'],
                data_defaultdict['run_status_update_total_errors'])
        )

    def _get_prometheus_data(self) -> Dict:
        """
        This method will try to get all prometheus metrics from the reachable
        source. It first tries to get the metrics from the last prometheus
        source used, if it fails, it tries to get the data from another source.
        If it can't connect with any source, it will raise a
        NodeIsDownException.
        If it connected with a source, and the source raised another error, it
        will raise that error because it means that the correct source was
        selected but another issue was found.
        :return: A Dict containing all the metric values.
        """
        try:
            return get_prometheus_metrics_data(self.last_prometheus_source_used,
                                               self.prometheus_metrics,
                                               self.logger, verify=False)
        except (ReqConnectionError, ReadTimeout):
            self.logger.debug("Could not connect with %s. Will try to obtain "
                              "the metrics from another source.",
                              self.last_prometheus_source_used)

        for source in self.node_config.node_prometheus_urls:
            try:
                data = get_prometheus_metrics_data(source,
                                                   self.prometheus_metrics,
                                                   self.logger, verify=False)
                self._last_prometheus_source_used = source
                return data
            except (ReqConnectionError, ReadTimeout):
                self.logger.debug(
                    "Could not connect with %s. Will try to obtain "
                    "the metrics from another source.",
                    self.last_prometheus_source_used)
            except Exception as e:
                # We need to set the last_prometheus_source_used because in this
                # case the node is online, but something bad happened.
                self._last_prometheus_source_used = source
                raise e

        raise NodeIsDownException(self.node_config.node_name)

    def _get_data(self) -> Dict:
        retrieval_info = {
            'prometheus': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self._get_prometheus_data,
                'processing_function': self._process_retrieved_prometheus_data,
                'last_source_used_var': 'self._last_prometheus_source_used',
                'monitoring_enabled_var': 'self.node_config._monitor_prometheus'
            }
        }
        for source, info in retrieval_info.items():
            if eval(info['monitoring_enabled_var']):
                try:
                    info['data'] = info['get_function']()
                    info['data_retrieval_failed'] = False
                except NodeIsDownException as e:
                    info['data_retrieval_exception'] = e
                    self.logger.error(
                        "Metrics could not be obtained from any {} "
                        "source.".format(source))
                    self.logger.exception(info['data_retrieval_exception'])
                except (IncompleteRead, ChunkedEncodingError, ProtocolError):
                    info['data_retrieval_exception'] = DataReadingException(
                        self.monitor_name, eval(info['last_source_used_var']))
                    self.logger.error("Error when retrieving data from %s",
                                      eval(info['last_source_used_var']))
                    self.logger.exception(info['data_retrieval_exception'])
                except (InvalidURL, InvalidSchema, MissingSchema):
                    info['data_retrieval_exception'] = InvalidUrlException(
                        eval(info['last_source_used_var']))
                    self.logger.error("Error when retrieving data from %s",
                                      eval(info['last_source_used_var']))
                    self.logger.exception(info['data_retrieval_exception'])
                except MetricNotFoundException as e:
                    info['data_retrieval_exception'] = e
                    self.logger.error("Error when retrieving data from %s",
                                      eval(info['last_source_used_var']))
                    self.logger.exception(info['data_retrieval_exception'])
        return retrieval_info

    def _process_error(self, error: PANICException,
                       last_source_used: str) -> Dict:
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'last_source_used': last_source_used,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp()
                },
                'message': error.message,
                'code': error.code,
            }
        }

        return processed_data

    def _process_retrieved_prometheus_data(self, data: Dict) -> Dict:
        data_copy = copy.deepcopy(data)

        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'last_source_used': self.last_prometheus_source_used,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': {},
            }
        }

        # The Chainlink team is pushing towards having multi-chain chainlink
        # nodes. Although this change is not being suggested to node operators
        # yet, the prometheus endpoint already supports multi-chains. From our
        # side for now we will still assume that each node supports only one
        # chain, thus for each metric we will consider the first value we find.

        # These are metrics with one value which are multi-node compatible
        one_value_multi_node_compatible_metrics = {
            'head_tracker_current_head',
            'head_tracker_heads_received_total',
            'max_unconfirmed_blocks',
            'tx_manager_num_gas_bumps_total',
            'tx_manager_gas_bump_exceeds_limit_total',
            'unconfirmed_transactions',
        }
        for metric in one_value_multi_node_compatible_metrics:
            processed_data['result']['data'][metric] = (
                None if data_copy[metric] is None
                else data_copy[metric][list(data_copy[metric])[0]]
            )
            self.logger.debug("%s %s: %s", self.node_config, metric,
                              processed_data['result']['data'][metric])

        # These are metrics with one value which are not multi-node compatible
        one_value_metrics = {'process_start_time_seconds'}
        for metric in one_value_metrics:
            self.logger.debug("%s %s: %s", self.node_config, metric,
                              data_copy[metric])
            processed_data['result']['data'][metric] = data_copy[metric]

        # Add gas_updater_set_gas_price info to the processed data. Note we will
        # process the first percentile object we find.
        processed_data['result']['data']['gas_updater_set_gas_price'] = {}
        set_gas_price_dict = processed_data['result']['data'][
            'gas_updater_set_gas_price']
        if data_copy['gas_updater_set_gas_price'] is not None:
            for _, data_subset in enumerate(
                    data_copy['gas_updater_set_gas_price']):
                data_subset_json = json.loads(data_subset)
                if "percentile" in data_subset_json:
                    set_gas_price_dict["percentile"] = data_subset_json[
                        "percentile"]
                    set_gas_price_dict["price"] = data_copy[
                        'gas_updater_set_gas_price'][data_subset]
                    break
        else:
            processed_data['result']['data']['gas_updater_set_gas_price'] = None
        self.logger.debug("%s gas_updater_set_gas_price: %s", self.node_config,
                          processed_data['result']['data'][
                              'gas_updater_set_gas_price'])

        # Add the balance to the processed data. We will monitor the first
        # account we find.
        processed_data['result']['data']['balance'] = {}
        balance_dict = processed_data['result']['data']['balance']
        for _, data_subset in enumerate(data_copy['eth_balance']):
            data_subset_json = json.loads(data_subset)
            if "account" in data_subset_json:
                address = data_subset_json['account']
                balance_dict['address'] = address
                balance_dict['balance'] = data_copy['eth_balance'][data_subset]
                if "evmChainID" in data_subset_json:
                    evm_chain_id = int(data_subset_json['evmChainID'])
                    if self.currency_symbol_limiter.can_do_task():
                        self._currency_symbol = self._get_currency_symbol(
                            evm_chain_id)
                        if self.currency_symbol:
                            self.currency_symbol_limiter.did_task()
                balance_dict['symbol'] = self.currency_symbol
                break
        self.logger.debug("%s balance: %s", self.node_config,
                          processed_data['result']['data']['balance'])

        # Add the number of error job runs to the processed data
        no_of_error_job_runs = 0
        # If its None then there are no error job runs
        if data_copy['run_status_update_total'] is not None:
            for _, data_subset in enumerate(
                    data_copy['run_status_update_total']):
                data_subset_json = json.loads(data_subset)
                if ('status' in data_subset_json
                        and data_subset_json['status'] == 'errored'):
                    no_of_error_job_runs += 1

        self.logger.debug("%s run_status_update_total_errors: %s",
                          self.node_config, no_of_error_job_runs)
        processed_data['result']['data'][
            'run_status_update_total_errors'] = no_of_error_job_runs

        return processed_data

    def _process_retrieved_data(self, processing_fn: Callable,
                                data: Dict) -> Dict:
        return processing_fn(data)

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY, body=data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to '%s' exchange", RAW_DATA_EXCHANGE)

    def _monitor(self) -> None:
        retrieval_info = self._get_data()
        processed_data = {}
        for source, info in retrieval_info.items():
            if eval(info['monitoring_enabled_var']):
                try:
                    processed_data[source] = self._process_data(
                        info['data_retrieval_failed'],
                        [info['data_retrieval_exception'],
                         eval(info['last_source_used_var'])],
                        [info['processing_function'], info['data']],
                    )
                except Exception as error:
                    self.logger.error(
                        "Error when processing data obtained from %s",
                        eval(info['last_source_used_var']))
                    self.logger.exception(error)
                    # Do not send data if we experienced processing errors
                    return
            else:
                processed_data[source] = {}

        self._send_data(processed_data)

        # Can't use list comprehension due to eval losing self.
        data_retrieval_failed_list = []
        for _, info in retrieval_info.items():
            if eval(info['monitoring_enabled_var']):
                data_retrieval_failed_list.append(
                    info['data_retrieval_failed'])

        # ChainMap combines multiple dicts into 1. Note if there are same keys
        # in different dicts, the first occurrence is used. This should never
        # happen in our case.
        all_processed_data = dict(ChainMap(
            *[
                data['result']['data']
                for _, data in processed_data.items()
                if 'result' in data
            ]
        ))

        # Only output the gathered data if at least one retrieval occurred
        # and there was no error in the entire retrieval process
        if data_retrieval_failed_list and not any(data_retrieval_failed_list):
            self.logger.debug(self._display_data(all_processed_data))

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)

    def _get_currency_symbol(self, chain_id: int) -> str:
        """
        This function gets a list of chains from an endpoint, finds the chain
        with the ID passed as a parameter and returns the currency symbol of
        said chain.
        :param chain_id: The ID of the chain of which we need to return the
        currency symbol for.
        :return: The currency symbol for the given chain ID
        """
        currency_symbol = ''

        try:
            chains = get_json(CHAINLINK_CHAINS_URL, self.logger)
            self.logger.debug("Retrieved chains data from endpoint: %s",
                              CHAINLINK_CHAINS_URL)

            found_chain = next(chain for chain in chains
                               if chain['chainId'] == chain_id)
            currency_symbol = found_chain['nativeCurrency']['symbol']
        except Exception as e:
            self.logger.exception(e)

        return currency_symbol
