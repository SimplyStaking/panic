import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from queue import Queue
from unittest import mock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.data_store.redis import RedisApi
from src.data_transformers.node.chainlink import ChainlinkNodeDataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.nodes.chainlink_node import ChainlinkNode
from src.utils import env
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE, STORE_EXCHANGE, ALERT_EXCHANGE,
    CL_NODE_DT_INPUT_QUEUE_NAME, CHAINLINK_NODE_RAW_DATA_ROUTING_KEY,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.exceptions import (PANICException, NodeIsDownException,
                                  ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from test.utils.utils import (connect_to_rabbit, disconnect_from_rabbit,
                              delete_exchange_if_exists, delete_queue_if_exists,
                              save_chainlink_node_to_redis)


class TestChainlinkNodeDataTransformer(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.test_data_str = 'test_data'
        self.transformer_name = 'test_chainlink_node_data_transformer'
        self.max_queue_size = 1000
        self.test_publishing_queue = Queue(self.max_queue_size)
        self.test_rabbit_queue_name = 'Test Queue'
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': self.test_last_monitored,
        }
        self.test_exception = PANICException('test_exception', 1)
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.invalid_transformed_data = {'bad_key': 'bad_value'}
        self.test_monitor_name = 'test_monitor_name'

        # Rabbit instance
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        # Redis Instance
        self.redis_db = env.REDIS_DB
        self.redis_host = env.REDIS_IP
        self.redis_port = env.REDIS_PORT
        self.redis_namespace = env.UNIQUE_ALERTER_IDENTIFIER
        self.redis = RedisApi(self.dummy_logger, self.redis_db,
                              self.redis_host, self.redis_port, '',
                              self.redis_namespace,
                              self.connection_check_time_interval)

        # Some dummy state
        self.test_chainlink_node_name = 'test_chainlink_node'
        self.test_chainlink_node_id = 'test_chainlink_node_id345834t8h3r5893h8'
        self.test_chainlink_node_parent_id = 'test_chainlink_node_parent_id34fg'
        self.test_chainlink_node = ChainlinkNode(
            self.test_chainlink_node_name, self.test_chainlink_node_id,
            self.test_chainlink_node_parent_id)
        self.test_node_is_down_exception = NodeIsDownException(
            self.test_chainlink_node.node_name)
        self.test_state = {
            self.test_chainlink_node_id: self.test_chainlink_node
        }
        self.test_went_down_at_prometheus = None
        self.test_current_height = 50000000000
        self.test_eth_blocks_in_queue = 3
        self.test_total_block_headers_received = 454545040
        self.test_total_block_headers_dropped = 4
        self.test_no_of_active_jobs = 10
        self.test_max_pending_tx_delay = 6
        self.test_process_start_time_seconds = 345474.4
        self.test_total_gas_bumps = 11
        self.test_total_gas_bumps_exceeds_limit = 13
        self.test_no_of_unconfirmed_txs = 7
        self.test_total_errored_job_runs = 15
        self.test_current_gas_price_info = {
            'percentile': 50.5,
            'price': 22.0,
        }
        self.test_eth_balance_info = {
            'address': 'address1', 'balance': 34.4, 'latest_usage': 5.0,
        }
        self.test_last_prometheus_source_used = "prometheus_source_1"
        self.test_last_monitored_prometheus = 45.666786
        self.test_chainlink_node.set_went_down_at_prometheus(
            self.test_went_down_at_prometheus)
        self.test_chainlink_node.set_current_height(self.test_current_height)
        self.test_chainlink_node.set_eth_blocks_in_queue(
            self.test_eth_blocks_in_queue)
        self.test_chainlink_node.set_total_block_headers_received(
            self.test_total_block_headers_received)
        self.test_chainlink_node.set_total_block_headers_dropped(
            self.test_total_block_headers_dropped)
        self.test_chainlink_node.set_no_of_active_jobs(
            self.test_no_of_active_jobs)
        self.test_chainlink_node.set_max_pending_tx_delay(
            self.test_max_pending_tx_delay)
        self.test_chainlink_node.set_process_start_time_seconds(
            self.test_process_start_time_seconds)
        self.test_chainlink_node.set_total_gas_bumps(self.test_total_gas_bumps)
        self.test_chainlink_node.set_total_gas_bumps_exceeds_limit(
            self.test_total_gas_bumps_exceeds_limit)
        self.test_chainlink_node.set_no_of_unconfirmed_txs(
            self.test_no_of_unconfirmed_txs)
        self.test_chainlink_node.set_total_errored_job_runs(
            self.test_total_errored_job_runs)
        self.test_chainlink_node.set_current_gas_price_info(
            self.test_current_gas_price_info['percentile'],
            self.test_current_gas_price_info['price'])
        self.test_chainlink_node.set_eth_balance_info(
            self.test_eth_balance_info)
        self.test_chainlink_node.set_last_prometheus_source_used(
            self.test_last_prometheus_source_used)
        self.test_chainlink_node.set_last_monitored_prometheus(
            self.test_last_monitored_prometheus)

        # Whenever we need to use a new state we use the below
        self.test_chainlink_node_new = ChainlinkNode(
            self.test_chainlink_node_name, self.test_chainlink_node_id,
            self.test_chainlink_node_parent_id)
        self.test_went_down_at_prometheus_new = None
        self.test_current_height_new = 50000000001
        self.test_eth_blocks_in_queue_new = 4
        self.test_total_block_headers_received_new = 454545041
        self.test_total_block_headers_dropped_new = 5
        self.test_no_of_active_jobs_new = 11
        self.test_max_pending_tx_delay_new = 7
        self.test_process_start_time_seconds_new = 345476.4
        self.test_total_gas_bumps_new = 13
        self.test_total_gas_bumps_exceeds_limit_new = 14
        self.test_no_of_unconfirmed_txs_new = 8
        self.test_total_errored_job_runs_new = 16
        self.test_current_gas_price_info_new = {
            'percentile': 52.5,
            'price': 24.0,
        }
        self.test_eth_balance_info_new = {
            'address': 'address1', 'balance': 44.4, 'latest_usage': 0.0,
        }
        self.test_last_prometheus_source_used_new = "prometheus_source_2"
        self.test_last_monitored_prometheus_new = 47.666786
        self.test_chainlink_node_new.set_went_down_at_prometheus(
            self.test_went_down_at_prometheus_new)
        self.test_chainlink_node_new.set_current_height(
            self.test_current_height_new)
        self.test_chainlink_node_new.set_eth_blocks_in_queue(
            self.test_eth_blocks_in_queue_new)
        self.test_chainlink_node_new.set_total_block_headers_received(
            self.test_total_block_headers_received_new)
        self.test_chainlink_node_new.set_total_block_headers_dropped(
            self.test_total_block_headers_dropped_new)
        self.test_chainlink_node_new.set_no_of_active_jobs(
            self.test_no_of_active_jobs_new)
        self.test_chainlink_node_new.set_max_pending_tx_delay(
            self.test_max_pending_tx_delay_new)
        self.test_chainlink_node_new.set_process_start_time_seconds(
            self.test_process_start_time_seconds_new)
        self.test_chainlink_node_new.set_total_gas_bumps(
            self.test_total_gas_bumps_new)
        self.test_chainlink_node_new.set_total_gas_bumps_exceeds_limit(
            self.test_total_gas_bumps_exceeds_limit_new)
        self.test_chainlink_node_new.set_no_of_unconfirmed_txs(
            self.test_no_of_unconfirmed_txs_new)
        self.test_chainlink_node_new.set_total_errored_job_runs(
            self.test_total_errored_job_runs_new)
        self.test_chainlink_node_new.set_current_gas_price_info(
            self.test_current_gas_price_info_new['percentile'],
            self.test_current_gas_price_info_new['price'])
        self.test_chainlink_node_new.set_eth_balance_info(
            self.test_eth_balance_info_new)
        self.test_chainlink_node_new.set_last_prometheus_source_used(
            self.test_last_prometheus_source_used_new)
        self.test_chainlink_node_new.set_last_monitored_prometheus(
            self.test_last_monitored_prometheus_new)

        # Loading objects
        self.loaded_cl_node_default_data = ChainlinkNode(
            self.test_chainlink_node_name, self.test_chainlink_node_id,
            self.test_chainlink_node_parent_id)
        self.loaded_cl_node_trans_data = ChainlinkNode(
            self.test_chainlink_node_name, self.test_chainlink_node_id,
            self.test_chainlink_node_parent_id)
        self.loaded_cl_node_trans_data.set_went_down_at_prometheus(
            self.test_went_down_at_prometheus)
        self.loaded_cl_node_trans_data.set_current_height(
            self.test_current_height)
        self.loaded_cl_node_trans_data.set_eth_blocks_in_queue(
            self.test_eth_blocks_in_queue)
        self.loaded_cl_node_trans_data.set_total_block_headers_received(
            self.test_total_block_headers_received)
        self.loaded_cl_node_trans_data.set_total_block_headers_dropped(
            self.test_total_block_headers_dropped)
        self.loaded_cl_node_trans_data.set_no_of_active_jobs(
            self.test_no_of_active_jobs)
        self.loaded_cl_node_trans_data.set_max_pending_tx_delay(
            self.test_max_pending_tx_delay)
        self.loaded_cl_node_trans_data.set_process_start_time_seconds(
            self.test_process_start_time_seconds)
        self.loaded_cl_node_trans_data.set_total_gas_bumps(
            self.test_total_gas_bumps)
        self.loaded_cl_node_trans_data.set_total_gas_bumps_exceeds_limit(
            self.test_total_gas_bumps_exceeds_limit)
        self.loaded_cl_node_trans_data.set_no_of_unconfirmed_txs(
            self.test_no_of_unconfirmed_txs)
        self.loaded_cl_node_trans_data.set_total_errored_job_runs(
            self.test_total_errored_job_runs)
        self.loaded_cl_node_trans_data.set_current_gas_price_info(
            self.test_current_gas_price_info['percentile'],
            self.test_current_gas_price_info['price'])
        self.loaded_cl_node_trans_data.set_eth_balance_info(
            self.test_eth_balance_info)
        self.loaded_cl_node_trans_data.set_last_prometheus_source_used(
            self.test_last_prometheus_source_used)
        self.loaded_cl_node_trans_data.set_last_monitored_prometheus(
            self.test_last_monitored_prometheus)

        # Raw data examples
        self.raw_data_example_result_all = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used_new,
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'time': self.test_last_monitored_prometheus_new,
                    },
                    'data': {
                        'head_tracker_current_head':
                            float(self.test_current_height_new),
                        'head_tracker_heads_received_total':
                            float(self.test_total_block_headers_received_new),
                        'job_subscriber_subscriptions':
                            float(self.test_no_of_active_jobs_new),
                        'max_unconfirmed_blocks':
                            float(self.test_max_pending_tx_delay_new),
                        'process_start_time_seconds':
                            self.test_process_start_time_seconds_new,
                        'tx_manager_num_gas_bumps_total':
                            float(self.test_total_gas_bumps_new),
                        'tx_manager_gas_bump_exceeds_limit_total':
                            float(self.test_total_gas_bumps_exceeds_limit_new),
                        'unconfirmed_transactions':
                            float(self.test_no_of_unconfirmed_txs_new),
                        'run_status_update_total_errors':
                            self.test_total_errored_job_runs_new,
                        'gas_updater_set_gas_price':
                            {
                                'percentile': '{}%'.format(
                                    self.test_current_gas_price_info_new[
                                        'percentile']),
                                'price':
                                    self.test_current_gas_price_info_new[
                                        'price']
                            },
                        'eth_balance': {
                            'address': 'address1',
                            'balance': self.test_eth_balance_info_new[
                                'balance'],
                            },
                    },
                }
            }
        }
        self.raw_data_example_result_options_None = copy.deepcopy(
            self.raw_data_example_result_all)
        self.raw_data_example_result_options_None['prometheus'][
            'result']['data']['gas_updater_set_gas_price'] = None
        self.raw_data_example_result_options_None['prometheus'][
            'result']['data']['run_status_update_total_errors'] = None
        self.raw_data_example_general_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used_new,
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.raw_data_example_downtime_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor_name,
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used_new,
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                }
            }
        }

        # Transformed data examples
        self.transformed_data_example_result_all = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used_new,
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'last_monitored':
                            self.test_last_monitored_prometheus_new,
                    },
                    'data': {
                        'went_down_at': self.test_went_down_at_prometheus_new,
                        'current_height': self.test_current_height_new,
                        'eth_blocks_in_queue':
                            self.test_eth_blocks_in_queue_new,
                        'total_block_headers_received':
                            self.test_total_block_headers_received_new,
                        'total_block_headers_dropped':
                            self.test_total_block_headers_dropped_new,
                        'no_of_active_jobs': self.test_no_of_active_jobs_new,
                        'max_pending_tx_delay':
                            self.test_max_pending_tx_delay_new,
                        'process_start_time_seconds':
                            self.test_process_start_time_seconds_new,
                        'total_gas_bumps': self.test_total_gas_bumps_new,
                        'total_gas_bumps_exceeds_limit':
                            self.test_total_gas_bumps_exceeds_limit_new,
                        'no_of_unconfirmed_txs':
                            self.test_no_of_unconfirmed_txs_new,
                        'total_errored_job_runs':
                            self.test_total_errored_job_runs_new,
                        'current_gas_price_info':
                            self.test_current_gas_price_info_new,
                        'eth_balance_info': self.test_eth_balance_info_new,
                    },
                }
            }
        }
        self.transformed_data_example_result_options_None = copy.deepcopy(
            self.transformed_data_example_result_all)
        self.transformed_data_example_result_options_None['prometheus'][
            'result']['data']['current_gas_price_info'] = None
        self.transformed_data_example_result_options_None['prometheus'][
            'result']['data']['run_status_update_total_errors'] = None
        self.transformed_data_example_general_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used_new,
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.transformed_data_example_downtime_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used_new,
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored_prometheus_new
                    }
                }
            }
        }

        # Processed data examples
        self.processed_data_example_result_all = {
            'prometheus': {
                'result': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used': {
                            'current':
                                self.test_last_prometheus_source_used_new,
                            'previous': self.test_last_prometheus_source_used
                        },
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'last_monitored':
                            self.test_last_monitored_prometheus_new,
                    },
                    'data': {
                        'went_down_at': {
                            'current': self.test_went_down_at_prometheus_new,
                            'previous': self.test_went_down_at_prometheus
                        },
                        'current_height': {
                            'current': self.test_current_height_new,
                            'previous': self.test_current_height
                        },
                        'eth_blocks_in_queue': {
                            'current': self.test_eth_blocks_in_queue_new,
                            'previous': self.test_eth_blocks_in_queue
                        },
                        'total_block_headers_received': {
                            'current':
                                self.test_total_block_headers_received_new,
                            'previous': self.test_total_block_headers_received,
                        },
                        'total_block_headers_dropped': {
                            'current':
                                self.test_total_block_headers_dropped_new,
                            'previous': self.test_total_block_headers_dropped,
                        },
                        'no_of_active_jobs': {
                            'current': self.test_no_of_active_jobs_new,
                            'previous': self.test_no_of_active_jobs,
                        },
                        'max_pending_tx_delay': {
                            'current': self.test_max_pending_tx_delay_new,
                            'previous': self.test_max_pending_tx_delay
                        },
                        'process_start_time_seconds': {
                            'current': self.test_process_start_time_seconds_new,
                            'previous': self.test_process_start_time_seconds,
                        },
                        'total_gas_bumps': {
                            'current': self.test_total_gas_bumps_new,
                            'previous': self.test_total_gas_bumps
                        },
                        'total_gas_bumps_exceeds_limit': {
                            'current':
                                self.test_total_gas_bumps_exceeds_limit_new,
                            'previous': self.test_total_gas_bumps_exceeds_limit,
                        },
                        'no_of_unconfirmed_txs': {
                            'current': self.test_no_of_unconfirmed_txs_new,
                            'previous': self.test_no_of_unconfirmed_txs,
                        },
                        'total_errored_job_runs': {
                            'current': self.test_total_errored_job_runs_new,
                            'previous': self.test_total_errored_job_runs,
                        },
                        'current_gas_price_info': {
                            'current': self.test_current_gas_price_info_new,
                            'previous': self.test_current_gas_price_info
                        },
                        'eth_balance_info': {
                            'current': self.test_eth_balance_info_new,
                            'previous': self.test_eth_balance_info
                        },
                    },
                }
            }
        }
        self.processed_data_example_result_options_None = copy.deepcopy(
            self.processed_data_example_result_all)
        self.processed_data_example_result_options_None['prometheus'][
            'result']['data']['current_gas_price_info']['current'] = None
        self.processed_data_example_general_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used': {
                            'current':
                                self.test_last_prometheus_source_used_new,
                            'previous': self.test_last_prometheus_source_used,
                        },
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }
        self.processed_data_example_downtime_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.test_chainlink_node_name,
                        'last_source_used': {
                            'current':
                                self.test_last_prometheus_source_used_new,
                            'previous': self.test_last_prometheus_source_used,
                        },
                        'node_id': self.test_chainlink_node_id,
                        'node_parent_id': self.test_chainlink_node_parent_id,
                        'time': self.test_last_monitored_prometheus_new
                    },
                    'message': self.test_node_is_down_exception.message,
                    'code': self.test_node_is_down_exception.code,
                    'data': {
                        'went_down_at': {
                            'current': self.test_last_monitored_prometheus_new,
                            'previous': None
                        }
                    }
                }
            }
        }

        # Test transformer
        self.test_data_transformer = ChainlinkNodeDataTransformer(
            self.transformer_name, self.dummy_logger, self.redis, self.rabbitmq,
            self.max_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_data_transformer.rabbitmq)
        delete_queue_if_exists(self.test_data_transformer.rabbitmq,
                               CL_NODE_DT_INPUT_QUEUE_NAME)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  RAW_DATA_EXCHANGE)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  STORE_EXCHANGE)
        delete_exchange_if_exists(self.test_data_transformer.rabbitmq,
                                  ALERT_EXCHANGE)
        disconnect_from_rabbit(self.test_data_transformer.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.redis = None
        self.test_node_is_down_exception = None
        self.test_exception = None
        self.test_chainlink_node = None
        self.test_chainlink_node_new = None
        self.test_state = None
        self.test_publishing_queue = None
        self.test_last_monitored = None
        self.test_heartbeat = None
        self.invalid_transformed_data = None
        self.test_data_transformer = None
        self.loaded_cl_node_default_data = None
        self.loaded_cl_node_trans_data = None
        self.transformed_data_example_result_all = None
        self.transformed_data_example_result_options_None = None
        self.transformed_data_example_general_error = None
        self.transformed_data_example_downtime_error = None
        self.processed_data_example_result_all = None
        self.processed_data_example_result_options_None = None
        self.processed_data_example_general_error = None
        self.processed_data_example_downtime_error = None
        self.raw_data_example_result_all = None
        self.raw_data_example_result_options_None = None
        self.raw_data_example_general_error = None
        self.raw_data_example_downtime_error = None

    def test_str_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name,
                         str(self.test_data_transformer))

    def test_transformer_name_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name,
                         self.test_data_transformer.transformer_name)

    def test_redis_returns_transformer_redis_instance(self) -> None:
        self.assertEqual(self.redis, self.test_data_transformer.redis)

    def test_state_returns_the_systems_state(self) -> None:
        self.test_data_transformer._state = self.test_state
        self.assertEqual(self.test_state, self.test_data_transformer.state)

    def test_publishing_queue_returns_publishing_queue(self) -> None:
        self.test_data_transformer._publishing_queue = \
            self.test_publishing_queue
        self.assertEqual(self.test_publishing_queue,
                         self.test_data_transformer.publishing_queue)

    def test_publishing_queue_has_the_correct_max_size(self) -> None:
        self.assertEqual(self.max_queue_size,
                         self.test_data_transformer.publishing_queue.maxsize)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_data_transformer._listen_for_data()
        mock_start_consuming.assert_called_once()

    @mock.patch.object(RabbitMQApi, "basic_qos")
    def test_initialise_rabbit_initializes_everything_as_expected(
            self, mock_basic_qos) -> None:
        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        connect_to_rabbit(self.rabbitmq)
        self.test_data_transformer.rabbitmq.queue_delete(
            CL_NODE_DT_INPUT_QUEUE_NAME)
        self.test_data_transformer.rabbitmq.exchange_delete(
            HEALTH_CHECK_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(STORE_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_data_transformer._initialise_rabbitmq()

        # Perform checks that the connection has been opened and marked as open,
        # that the delivery confirmation variable is set and basic_qos called
        # successfully.
        self.assertTrue(self.test_data_transformer.rabbitmq.is_connected)
        self.assertTrue(self.test_data_transformer.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_data_transformer.rabbitmq.channel._delivery_confirmation)
        mock_basic_qos.assert_called_once_with(
            prefetch_count=round(self.max_queue_size / 5))

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_data_transformer.rabbitmq.exchange_declare(STORE_EXCHANGE,
                                                             passive=True)
        self.test_data_transformer.rabbitmq.exchange_declare(ALERT_EXCHANGE,
                                                             passive=True)
        self.test_data_transformer.rabbitmq.exchange_declare(
            HEALTH_CHECK_EXCHANGE, passive=True)

        # Check whether the consuming exchanges and queues have been creating by
        # sending messages with the same routing keys as for the bindings. We
        # will also check if the size of the queues is 0 to confirm that
        # basic_consume was called (it will store the msg in the component
        # memory immediately). If one of the exchanges or queues is not created
        # or basic_consume is not called, then either an exception will be
        # thrown or the queue size would be 1 respectively. Note when deleting
        # the exchanges in the beginning we also released every binding, hence
        # there is no other queue binded with the same routing key to any
        # exchange at this point.
        self.test_data_transformer.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_data_transformer.rabbitmq.queue_declare(
            CL_NODE_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(0, res.method.message_count)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones set by send_heartbeat, and checks that the
        # heartbeat is received
        self.test_data_transformer._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_data_transformer.rabbitmq.queue_delete(
            self.test_rabbit_queue_name)

        res = self.test_data_transformer.rabbitmq.queue_declare(
            queue=self.test_rabbit_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_data_transformer.rabbitmq.queue_bind(
            queue=self.test_rabbit_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

        self.test_data_transformer._send_heartbeat(self.test_heartbeat)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_data_transformer.rabbitmq.queue_declare(
            queue=self.test_rabbit_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_data_transformer.rabbitmq.basic_get(
            self.test_rabbit_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    def test_load_state_successful_if_cl_node_exists_in_redis_and_redis_online(
            self) -> None:
        # We will test this for when transformed data has been already stored in
        # redis and for when default values have been stored in redis.

        # Test for when transformed data is stored in redis
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_chainlink_node_to_redis(
            self.redis, self.loaded_cl_node_trans_data)

        # Reset chainlink node to default values to detect the loading
        self.test_chainlink_node.reset()

        # Load state
        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_trans_data, loaded_cl_node)

        # Now for when default values are stored in redis. At this point
        # self.test_chainlink_node will contain the original data due to the
        # loaded metrics.
        self.redis.delete_all()

        # Store default data
        save_chainlink_node_to_redis(self.redis,
                                     self.loaded_cl_node_default_data)

        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_default_data, loaded_cl_node)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_cl_node_in_redis_and_redis_offline(
            self) -> None:
        # In this test we will check for when redis has transformed data and
        # default data is stored in the state, and vice-versa.

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # First test for when redis has default values, and the state has
        # transformed metrics
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first.
        save_chainlink_node_to_redis(self.redis,
                                     self.loaded_cl_node_default_data)

        # Load state
        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_trans_data, loaded_cl_node)

        # Now test for when redis has transformed data values, and the state is
        # default
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_chainlink_node_to_redis(
            self.redis, self.loaded_cl_node_trans_data)

        # Reset cl_node to default values
        self.test_chainlink_node.reset()

        # Load state
        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_default_data, loaded_cl_node)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_node_not_in_redis_and_redis_online(
            self) -> None:
        # We will perform this test for both when the current state has default
        # entries, and for when it has transformed data

        # Test for when the state contains transformed data
        # Clean test db
        self.redis.delete_all()

        # Load state
        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_trans_data, loaded_cl_node)

        # Test for when the state contains default data
        # Clean test db
        self.redis.delete_all()
        self.test_chainlink_node.reset()

        # Load state
        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_default_data, loaded_cl_node)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_cl_node_not_in_redis_and_redis_off(
            self) -> None:
        # We will perform this test for both when the current state has default
        # entries, and for when it has transformed data

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Test for when the state contains transformed data
        # Clean test db
        self.redis.delete_all()

        # Load state
        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_trans_data, loaded_cl_node)

        # Test for when the state contains default data
        # Clean test db
        self.redis.delete_all()
        self.test_chainlink_node.reset()

        # Load state
        loaded_cl_node = self.test_data_transformer.load_state(
            self.test_chainlink_node)
        self.assertEqual(self.loaded_cl_node_default_data, loaded_cl_node)

        # Clean test db
        self.redis.delete_all()

    @parameterized.expand([
        ({'prometheus': {}},),
        ({'bad_key': 'bad_val'},),
        ({'prometheus': 'bad_val'},),
    ])
    def test_update_state_raises_unexpected_data_exception_if_unexpected_data(
            self, transformed_data) -> None:
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._update_state,
                          transformed_data)

    def test_update_state_updates_state_correctly_if_result(self) -> None:
        # We will perform this test for when we receive optionals None, and for
        # when all metrics are enabled
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        old_state = copy.deepcopy(self.test_data_transformer._state)

        # First test for when all metrics are enabled
        self.test_data_transformer._update_state(
            self.transformed_data_example_result_all)

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the nodes not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        # Check that the nodes's state values have been modified correctly
        self.assertEqual(
            self.test_chainlink_node_new,
            self.test_data_transformer._state[self.test_chainlink_node_id])

        # Check that the prometheus interface is marked as up
        self.assertFalse(
            self.test_data_transformer._state[
                self.test_chainlink_node_id].is_down_prometheus)

        # Now test for when optionals are set to None
        self.test_data_transformer._update_state(
            self.transformed_data_example_result_options_None)

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the nodes not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        # Check that the nodes's state values have been modified correctly
        self.test_chainlink_node_new.set_current_gas_price_info(None, None)
        self.assertEqual(
            self.test_chainlink_node_new,
            self.test_data_transformer._state[self.test_chainlink_node_id])

        # Check that the prometheus interface is marked as up
        self.assertFalse(
            self.test_data_transformer._state[
                self.test_chainlink_node_id].is_down_prometheus)

    @parameterized.expand([
        ('self.transformed_data_example_general_error', False,),
        ('self.transformed_data_example_downtime_error', True,)
    ])
    def test_update_state_updates_state_correctly_if_error(
            self, transformed_data_err, is_downtime_error) -> None:
        transformed_data_eval = eval(transformed_data_err)
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        old_state = copy.deepcopy(self.test_data_transformer._state)

        self.test_data_transformer._update_state(transformed_data_eval)

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the nodes not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        old_modified_node_state = old_state[self.test_chainlink_node_id]
        old_modified_node_state.set_last_prometheus_source_used(
            transformed_data_eval['prometheus']['error']['meta_data'][
                'last_source_used'])

        if is_downtime_error:
            self.assertTrue(
                self.test_data_transformer._state[
                    self.test_chainlink_node_id].is_down_prometheus)
            old_modified_node_state.set_prometheus_as_down(
                transformed_data_eval['prometheus']['error']['data'][
                    'went_down_at'])
        else:
            self.assertFalse(
                self.test_data_transformer._state[
                    self.test_chainlink_node_id].is_down_prometheus)

        self.assertEqual(
            old_modified_node_state,
            self.test_data_transformer.state[self.test_chainlink_node_id])

    @parameterized.expand([
        ('self.transformed_data_example_result_all',),
        ('self.transformed_data_example_result_options_None',),
        ('self.transformed_data_example_general_error',),
        ('self.transformed_data_example_downtime_error',)
    ])
    def test_process_transformed_data_for_saving_returns_expected_data(
            self, transformed_data: str) -> None:
        transformed_data_eval = eval(transformed_data)
        processed_data = \
            self.test_data_transformer._process_transformed_data_for_saving(
                transformed_data_eval)
        self.assertDictEqual(transformed_data_eval, processed_data)

    @parameterized.expand([
        ({'bad_key': 'bad_val'},),
        ({'prometheus': 'bad_val'},),
    ])
    def test_proc_trans_data_for_saving_raises_unexp_data_except_on_unexp_data(
            self, transformed_data) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_saving,
            transformed_data)

    @parameterized.expand([
        ('self.transformed_data_example_result_all',
         'self.processed_data_example_result_all'),
        ('self.transformed_data_example_result_options_None',
         'self.processed_data_example_result_options_None'),
        ('self.transformed_data_example_general_error',
         'self.processed_data_example_general_error'),
        ('self.transformed_data_example_downtime_error',
         'self.processed_data_example_downtime_error'),
    ])
    def test_process_transformed_data_for_alerting_returns_expected_data(
            self, transformed_data: str, expected_processed_data: str) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        actual_data = \
            self.test_data_transformer._process_transformed_data_for_alerting(
                eval(transformed_data))
        self.assertDictEqual(eval(expected_processed_data), actual_data)

    @parameterized.expand([
        ({'prometheus': {}},),
        ({'bad_key': 'bad_val'},),
        ({'prometheus': 'bad_val'},),
    ])
    def test_proc_trans_data_for_alerting_raise_unex_data_except_on_unex_data(
            self, transformed_data) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_alerting,
            transformed_data)

    @parameterized.expand([
        ('self.raw_data_example_general_error',
         'self.transformed_data_example_general_error',),
        ('self.raw_data_example_downtime_error',
         'self.transformed_data_example_downtime_error',),
        ('self.raw_data_example_result_all',
         'self.transformed_data_example_result_all',),
        ('self.raw_data_example_result_options_None',
         'self.transformed_data_example_result_options_None',),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_returns_expected_data(
            self, raw_data, expected_transformed_data, mock_proc_saving,
            mock_proc_alerting) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        proc_saving_return = {'key_1': 'val1'}
        proc_alerting_return = {'key_2': 'val2'}
        mock_proc_saving.return_value = proc_saving_return
        mock_proc_alerting.return_value = proc_alerting_return

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(eval(raw_data))

        self.assertEqual(eval(expected_transformed_data), trans_data)
        self.assertEqual(proc_alerting_return, data_for_alerting)
        self.assertEqual(proc_saving_return, data_for_saving)

    @parameterized.expand([
        ({'prometheus': {}},),
        ({'bad_key': 'bad_val'},),
        ({'prometheus': 'bad_val'},),
    ])
    def test_transform_data_raises_unexpected_data_exception_on_unexpected_data(
            self, raw_data) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._transform_data, raw_data)

    @parameterized.expand([
        ('self.processed_data_example_general_error',
         'self.transformed_data_example_general_error'),
        ('self.processed_data_example_downtime_error',
         'self.transformed_data_example_downtime_error'),
        ('self.processed_data_example_result_all',
         'self.transformed_data_example_result_all'),
        ('self.processed_data_example_result_options_None',
         'self.transformed_data_example_result_options_None'),
    ])
    def test_place_latest_data_on_queue_places_the_correct_data_on_queue(
            self, data_for_alerting: str, data_for_saving: str) -> None:
        self.test_data_transformer._place_latest_data_on_queue(
            eval(data_for_alerting), eval(data_for_saving)
        )
        expected_data_for_alerting = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': CL_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            'data': eval(data_for_alerting),
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_for_saving = {
            'exchange': STORE_EXCHANGE,
            'routing_key': CL_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            'data': eval(data_for_saving),
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }

        self.assertEqual(
            2, self.test_data_transformer.publishing_queue.qsize())
        self.assertDictEqual(
            expected_data_for_alerting,
            self.test_data_transformer.publishing_queue.queue[0])
        self.assertDictEqual(
            expected_data_for_saving,
            self.test_data_transformer.publishing_queue.queue[1])

    @parameterized.expand([
        ({
            'prometheus': {
                'result': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            }
        }, (True, 'node_parent_id1', 'node_id1', 'node_name1',),),
        ({
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            }
        }, (True, 'node_parent_id1', 'node_id1', 'node_name1',),),
        ({
            'prometheus': {
                'error': {
                    'meta_data': {
                        'bad_node_parent_id_index': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            }
        }, None,),
        ({
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'bad_node_id_index': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            }
        }, None,),
        ({
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'bad_node_name_index': 'node_name1',
                    }
                }
            }
        }, None,),
        ({
            'prometheus': {
                'bad_index': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            }
        }, None,),
        ({
            'prometheus': {
                'result': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            },
            'bad_source': {
                'result': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            }
        }, None,),
        ({
            'bad_source': {
                'result': {
                    'meta_data': {
                        'node_parent_id': 'node_parent_id1',
                        'node_id': 'node_id1',
                        'node_name': 'node_name1',
                    }
                }
            }
        }, None,),
        ({'prometheus': {}}, None,),
    ])
    def test_raw_data_has_valid_sources_structure_return(
            self, raw_data, expected_ret) -> None:
        # TODO: This test must be expanded further as more sources are added.
        if expected_ret:
            actual_ret = \
                self.test_data_transformer \
                    ._raw_data_has_valid_sources_structure(raw_data)
            self.assertEqual(expected_ret, actual_ret)
        else:
            self.assertRaises(
                ReceivedUnexpectedDataException,
                self.test_data_transformer
                    ._raw_data_has_valid_sources_structure, raw_data)

    @parameterized.expand([({}, False,), ('self.test_state', True), ])
    @mock.patch.object(ChainlinkNodeDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_transforms_data_if_data_has_correct_structure(
            self, state, state_is_str: bool, mock_ack, mock_trans_data) -> None:
        # We will check that the data is transformed by checking that
        # `_transform_data` is called correctly. Note that both the validation
        # and the transformations were tested in previous tests. Also we will
        # test for both result and error, and for when the node is both in the
        # state and not in the state.
        mock_ack.return_value = None
        mock_trans_data.return_value = (None, None, None)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body_result = json.dumps(self.raw_data_example_result_all)
        body_error = json.dumps(self.raw_data_example_general_error)
        properties = pika.spec.BasicProperties()

        if state_is_str:
            self.test_data_transformer._state = copy.deepcopy(eval(state))
        else:
            self.test_data_transformer._state = copy.deepcopy(state)

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body_result)
        mock_trans_data.assert_called_once_with(
            self.raw_data_example_result_all)

        # To reset the state as if the node was not already added
        if state_is_str:
            self.test_data_transformer._state = copy.deepcopy(eval(state))
        else:
            self.test_data_transformer._state = copy.deepcopy(state)

        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body_error)

        self.assertEqual(2, mock_trans_data.call_count)
        args, _ = mock_trans_data.call_args
        self.assertEqual(self.raw_data_example_general_error, args[0])
        self.assertEqual(1, len(args))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @parameterized.expand([
        (ReceivedUnexpectedDataException,),
        (KeyError,),
        (Exception,),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_raw_data_has_valid_sources_structure")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_raw_data_does_not_call_trans_data_if_validate_raise_exception(
            self, exception, mock_ack, mock_trans_data,
            mock_validation) -> None:
        mock_ack.return_value = None
        mock_trans_data.return_value = None
        mock_validation.side_effect = exception

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_all)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body)

        mock_trans_data.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',
         'self.transformed_data_example_result_all',),
        ('self.raw_data_example_result_options_None',
         'self.transformed_data_example_result_options_None'),
        ('self.raw_data_example_general_error',
         'self.transformed_data_example_general_error',),
        ('self.raw_data_example_downtime_error',
         'self.transformed_data_example_downtime_error',),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_updates_state_if_no_processing_errors(
            self, raw_data, transformed_data, mock_ack,
            mock_update_state) -> None:
        mock_ack.return_value = None
        mock_update_state.return_value = None
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_update_state.assert_called_once_with(eval(transformed_data))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None,),
        ('self.raw_data_example_result_options_None', Exception('test'), None,),
        ('self.raw_data_example_general_error', Exception('test'), None,),
        ('self.raw_data_example_downtime_error', Exception('test'), None,),
        ('self.raw_data_example_result_all', None, Exception('test'),),
        ('self.raw_data_example_result_options_None', None, Exception('test'),),
        ('self.raw_data_example_general_error', None, Exception('test'),),
        ('self.raw_data_example_downtime_error', None, Exception('test'),),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_raw_data_has_valid_sources_structure")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_transform_data")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_update_state_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            mock_ack, mock_update_state, mock_transform, mock_validate) -> None:
        # We will test this for both when the raw_data structure is invalid and
        # when the transformation encounters a problem
        mock_ack.return_value = None
        mock_update_state.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.test_chainlink_node_parent_id,
                                          self.test_chainlink_node_id,
                                          self.test_chainlink_node_name)
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_update_state.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',
         'self.transformed_data_example_result_all',
         'self.processed_data_example_result_all',),
        ('self.raw_data_example_result_options_None',
         'self.transformed_data_example_result_options_None',
         'self.processed_data_example_result_options_None',),
        ('self.raw_data_example_general_error',
         'self.transformed_data_example_general_error',
         'self.processed_data_example_general_error',),
        ('self.raw_data_example_downtime_error',
         'self.transformed_data_example_downtime_error',
         'self.processed_data_example_downtime_error',),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_places_data_on_queue_if_no_processing_errors(
            self, raw_data, transformed_data, processed_data, mock_ack,
            mock_update_state, mock_place_on_queue) -> None:
        mock_ack.return_value = None
        mock_update_state.return_value = None
        mock_place_on_queue.return_value = None
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_place_on_queue.assert_called_once_with(eval(processed_data),
                                                    eval(transformed_data))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None, None,),
        ('self.raw_data_example_result_all', None, Exception('test'), None,),
        ('self.raw_data_example_result_all', None, None, Exception('test'),),
        ('self.raw_data_example_result_options_None', Exception('test'), None,
         None,),
        ('self.raw_data_example_result_options_None', None, Exception('test'),
         None,),
        ('self.raw_data_example_result_options_None', None, None,
         Exception('test'),),
        ('self.raw_data_example_general_error', Exception('test'), None, None,),
        ('self.raw_data_example_general_error', None, Exception('test'), None,),
        ('self.raw_data_example_general_error', None, None, Exception('test'),),
        ('self.raw_data_example_downtime_error', Exception('test'), None,
         None,),
        ('self.raw_data_example_downtime_error', None, Exception('test'),
         None,),
        ('self.raw_data_example_downtime_error', None, None,
         Exception('test'),),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_raw_data_has_valid_sources_structure")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_transform_data")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_place_data_on_queue_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            update_exception, mock_ack, mock_update_state, mock_transform,
            mock_validate, mock_place_on_queue) -> None:
        # We will test this for whenever a processing error happens in either
        # stages of the transformation process.
        mock_ack.return_value = None
        mock_place_on_queue.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.test_chainlink_node_parent_id,
                                          self.test_chainlink_node_id,
                                          self.test_chainlink_node_name)
        if update_exception:
            mock_update_state.side_effect = update_exception
        else:
            mock_update_state.return_value = None
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_place_on_queue.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',),
        ('self.raw_data_example_result_options_None',),
        ('self.raw_data_example_general_error',),
        ('self.raw_data_example_downtime_error',),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_data")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_in_queue_if_no_processing_errors(
            self, raw_data, mock_ack, mock_update_state, mock_place_on_queue,
            mock_send_data) -> None:
        mock_ack.return_value = None
        mock_update_state.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_data.return_value = None
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_send_data.assert_called_once()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None, None,),
        ('self.raw_data_example_result_all', None, Exception('test'), None,),
        ('self.raw_data_example_result_all', None, None, Exception('test'),),
        ('self.raw_data_example_result_options_None', Exception('test'), None,
         None,),
        ('self.raw_data_example_result_options_None', None, Exception('test'),
         None,),
        ('self.raw_data_example_result_options_None', None, None,
         Exception('test'),),
        ('self.raw_data_example_general_error', Exception('test'), None, None,),
        ('self.raw_data_example_general_error', None, Exception('test'), None,),
        ('self.raw_data_example_general_error', None, None, Exception('test'),),
        ('self.raw_data_example_downtime_error', Exception('test'), None,
         None,),
        ('self.raw_data_example_downtime_error', None, Exception('test'),
         None,),
        ('self.raw_data_example_downtime_error', None, None,
         Exception('test'),),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_send_data")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_raw_data_has_valid_sources_structure")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_transform_data")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_in_queue_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            update_exception, mock_ack, mock_update_state, mock_transform,
            mock_validate, mock_place_on_queue, mock_send_data) -> None:
        # We will test this for whenever a processing error happens in either
        # stages of the transformation process.
        mock_ack.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_data.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.test_chainlink_node_parent_id,
                                          self.test_chainlink_node_id,
                                          self.test_chainlink_node_name)
        if update_exception:
            mock_update_state.side_effect = update_exception
        else:
            mock_update_state.return_value = None
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        mock_send_data.assert_called_once_with()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all',),
        ('self.raw_data_example_result_options_None',),
        ('self.raw_data_example_general_error',),
        ('self.raw_data_example_downtime_error',),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_data")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_hb_if_no_proc_errors_and_send_data_success(
            self, raw_data, mock_ack, mock_update_state, mock_place_on_queue,
            mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_update_state.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties, body)

        test_heartbeat = {
            'component_name': self.transformer_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_with(test_heartbeat)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.raw_data_example_result_all', Exception('test'), None, None,
         None,),
        ('self.raw_data_example_result_all', None, Exception('test'), None,
         None,),
        ('self.raw_data_example_result_all', None, None, Exception('test'),
         None,),
        ('self.raw_data_example_result_all', None, None, None,
         Exception('test'),),
        ('self.raw_data_example_result_options_None', Exception('test'), None,
         None, None,),
        ('self.raw_data_example_result_options_None', None, Exception('test'),
         None, None,),
        ('self.raw_data_example_result_options_None', None, None,
         Exception('test'), None,),
        ('self.raw_data_example_result_options_None', None, None,
         None, Exception('test'),),
        ('self.raw_data_example_general_error', Exception('test'), None,
         None, None,),
        ('self.raw_data_example_general_error', None, Exception('test'),
         None, None,),
        ('self.raw_data_example_general_error', None, None, Exception('test'),
         None,),
        ('self.raw_data_example_general_error', None, None, None,
         Exception('test'),),
        ('self.raw_data_example_downtime_error', Exception('test'), None,
         None, None,),
        ('self.raw_data_example_downtime_error', None, Exception('test'),
         None, None,),
        ('self.raw_data_example_downtime_error', None, None,
         Exception('test'), None,),
        ('self.raw_data_example_downtime_error', None, None,
         None, Exception('test'),),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_data")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(ChainlinkNodeDataTransformer,
                       "_raw_data_has_valid_sources_structure")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_transform_data")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_update_state")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_processing_errors(
            self, raw_data, validation_exception, transformation_exception,
            update_exception, send_data_exception, mock_ack, mock_update_state,
            mock_transform, mock_validate, mock_place_on_queue, mock_send_data,
            mock_send_heartbeat) -> None:
        # We will test this for whenever a processing error happens in either
        # stages of the transformation process.
        mock_ack.return_value = None
        mock_place_on_queue.return_value = None
        mock_send_heartbeat.return_value = None
        if validation_exception:
            mock_validate.side_effect = validation_exception
        else:
            mock_validate.return_value = (True,
                                          self.test_chainlink_node_parent_id,
                                          self.test_chainlink_node_id,
                                          self.test_chainlink_node_name)
        if update_exception:
            mock_update_state.side_effect = update_exception
        else:
            mock_update_state.return_value = None
        if transformation_exception:
            mock_transform.side_effect = transformation_exception
        self.test_data_transformer._state = self.test_state

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(eval(raw_data))
        properties = pika.spec.BasicProperties()

        # Send raw data
        if send_data_exception:
            mock_send_data.side_effect = send_data_exception
            self.assertRaises(Exception,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body)
        else:
            mock_send_data.return_value = None
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)

        mock_send_heartbeat.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        (MessageWasNotDeliveredException('test'), None,),
        (None, MessageWasNotDeliveredException('test'),),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_data")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_raise_msg_not_del_exce_if_raised(
            self, send_data_exception, send_hb_exception, mock_ack,
            mock_send_hb, mock_send_data) -> None:
        # We will perform this test for both when the exception is raised by
        # send_data and by send_heartbeat
        if send_data_exception:
            mock_send_data.side_effect = send_data_exception
        else:
            mock_send_data.return_value = None

        if send_hb_exception:
            mock_send_hb.side_effect = send_hb_exception
        else:
            mock_send_hb.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_all)
        properties = pika.spec.BasicProperties()

        try:
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)
        except MessageWasNotDeliveredException as e:
            self.fail("Was not expecting {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @parameterized.expand([
        (AMQPConnectionError('test'), None, AMQPConnectionError,),
        (None, AMQPConnectionError('test'), AMQPConnectionError),
        (AMQPChannelError('test'), None, AMQPChannelError),
        (None, AMQPChannelError('test'), AMQPChannelError),
        (Exception('test'), None, Exception,),
        (None, Exception('test'), Exception,),
    ])
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_data")
    @mock.patch.object(ChainlinkNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_unexpected_errors_if_raised(
            self, send_data_exception, send_hb_exception, exception_instance,
            mock_ack, mock_send_hb, mock_send_data) -> None:
        # We will perform this test for both when the exception is raised by
        # send_data and by send_heartbeat
        if send_data_exception:
            mock_send_data.side_effect = send_data_exception
        else:
            mock_send_data.return_value = None

        if send_hb_exception:
            mock_send_hb.side_effect = send_hb_exception
        else:
            mock_send_hb.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_all)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_instance,
                          self.test_data_transformer._process_raw_data,
                          blocking_channel, method, properties, body)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()
