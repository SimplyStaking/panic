import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from queue import Queue
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.data_store.redis import RedisApi
from src.data_transformers.contracts.evm import EVMContractsDataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.contracts.v3 import V3EvmContract
from src.monitorables.contracts.v4 import V4EvmContract
from src.utils import env
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE, STORE_EXCHANGE, ALERT_EXCHANGE,
    EVM_CONTRACTS_DT_INPUT_QUEUE_NAME, CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    CL_CONTRACTS_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.exceptions import (PANICException,
                                  ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from test.utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, disconnect_from_rabbit,
    delete_exchange_if_exists, save_evm_contract_to_redis)


class TestEVMContractsDataTransformer(unittest.TestCase):
    def setUp(self) -> None:
        # Dummy data and objects
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': self.test_last_monitored,
        }
        self.test_exception = PANICException('test_exception', 1)
        self.test_rabbit_queue_name = 'Test Queue'
        self.max_queue_size = 1000
        self.test_data_str = 'test_data'
        self.test_publishing_queue = Queue(self.max_queue_size)
        self.transformer_name = 'test_evm_contracts_data_transformer'

        # Rabbit instance
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        # Redis instance
        self.redis_db = env.REDIS_DB
        self.redis_host = env.REDIS_IP
        self.redis_port = env.REDIS_PORT
        self.redis_namespace = env.UNIQUE_ALERTER_IDENTIFIER
        self.redis = RedisApi(
            self.dummy_logger, self.redis_db, self.redis_host, self.redis_port,
            '', self.redis_namespace, self.connection_check_time_interval)

        # Test meta_data credentials
        self.test_monitor_name = 'test_monitor'
        self.test_node_id_1 = 'node_id_1'
        self.test_parent_id_1 = 'parent_id_1'
        self.test_node_name_1 = 'node_name_1'

        # Test contract credentials
        self.test_proxy_address_1 = 'test_proxy_address_1'
        self.test_aggregator_address_1 = 'test_aggregator_address_1'
        self.test_latest_round_1 = 40
        self.test_latest_answer_1 = 34534534563464
        self.test_latest_timestamp_1 = self.test_last_monitored + 30
        self.test_answered_in_round_1 = 40
        self.test_withdrawable_payment_1 = 3458347534235
        self.test_owed_payment_1 = 34
        self.test_historical_rounds_1 = [
            {
                'roundId': 38,
                'roundAnswer': 10,
                'roundTimestamp': self.test_last_monitored + 10,
                'answeredInRound': 38,
                'nodeSubmission': 5
            },
            {
                'roundId': 39,
                'roundAnswer': 5,
                'roundTimestamp': self.test_last_monitored + 20,
                'answeredInRound': 39,
                'nodeSubmission': 10
            }
        ]
        self.test_historical_rounds_1_transformed = copy.deepcopy(
            self.test_historical_rounds_1)
        self.test_historical_rounds_1_transformed[0]['deviation'] = 50.0
        self.test_historical_rounds_1_transformed[1]['deviation'] = 100.0
        self.test_proxy_address_2 = 'test_proxy_address_2'
        self.test_aggregator_address_2 = 'test_aggregator_address_2'
        self.test_latest_round_2 = 50
        self.test_latest_answer_2 = 3453453456
        self.test_latest_timestamp_2 = self.test_last_monitored + 30
        self.test_answered_in_round_2 = 40
        self.test_withdrawable_payment_2 = 3458347
        self.test_owed_payment_2 = 35
        self.test_historical_rounds_2 = [
            {
                'roundId': 48,
                'roundAnswer': 10,
                'roundTimestamp': self.test_last_monitored + 10,
                'answeredInRound': 48,
                'nodeSubmission': 5
            },
            {
                'roundId': 49,
                'roundAnswer': 5,
                'roundTimestamp': self.test_last_monitored + 20,
                'answeredInRound': 49,
                'nodeSubmission': 10
            }
        ]
        self.test_historical_rounds_2_transformed = copy.deepcopy(
            self.test_historical_rounds_2)
        self.test_historical_rounds_2_transformed[0]['deviation'] = 50.0
        self.test_historical_rounds_2_transformed[1]['deviation'] = 100.0
        self.test_historical_rounds_3 = [
            {
                'roundId': 48,
                'roundAnswer': 10,
                'roundTimestamp': self.test_last_monitored + 10,
                'answeredInRound': 48,
                'nodeSubmission': 5,
                'noOfObservations': 4,
                'noOfTransmitters': 14,
            },
            {
                'roundId': 49,
                'roundAnswer': 5,
                'roundTimestamp': self.test_last_monitored + 20,
                'answeredInRound': 49,
                'nodeSubmission': 10,
                'noOfObservations': 5,
                'noOfTransmitters': 16,
            }
        ]
        self.test_historical_rounds_3_transformed = copy.deepcopy(
            self.test_historical_rounds_3)
        self.test_historical_rounds_3_transformed[0]['deviation'] = 50.0
        self.test_historical_rounds_3_transformed[1]['deviation'] = 100.0
        self.test_historical_rounds_4 = [
            {
                'roundId': 38,
                'roundAnswer': 10,
                'roundTimestamp': self.test_last_monitored + 10,
                'answeredInRound': 38,
                'nodeSubmission': 5,
                'noOfObservations': 6,
                'noOfTransmitters': 17,
            },
            {
                'roundId': 39,
                'roundAnswer': 5,
                'roundTimestamp': self.test_last_monitored + 20,
                'answeredInRound': 39,
                'nodeSubmission': 10,
                'noOfObservations': 7,
                'noOfTransmitters': 18,
            }
        ]
        self.test_historical_rounds_4_transformed = copy.deepcopy(
            self.test_historical_rounds_4)
        self.test_historical_rounds_4_transformed[0]['deviation'] = 50.0
        self.test_historical_rounds_4_transformed[1]['deviation'] = 100.0

        # Some raw data examples
        self.raw_data_example_result_v3 = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor_name,
                    'node_name': self.test_node_name_1,
                    'node_id': self.test_node_id_1,
                    'node_parent_id': self.test_parent_id_1,
                    'time': self.test_last_monitored + 60
                },
                'data': {
                    self.test_proxy_address_1: {
                        'contractVersion': 3,
                        'aggregatorAddress': self.test_aggregator_address_1,
                        'latestRound': self.test_latest_round_1,
                        'latestAnswer': self.test_latest_answer_1,
                        'latestTimestamp': self.test_latest_timestamp_1,
                        'answeredInRound': self.test_answered_in_round_1,
                        'withdrawablePayment': self.test_withdrawable_payment_1,
                        'historicalRounds': self.test_historical_rounds_1
                    },
                    self.test_proxy_address_2: {
                        'contractVersion': 3,
                        'aggregatorAddress': self.test_aggregator_address_2,
                        'latestRound': self.test_latest_round_2,
                        'latestAnswer': self.test_latest_answer_2,
                        'latestTimestamp': self.test_latest_timestamp_2,
                        'answeredInRound': self.test_answered_in_round_2,
                        'withdrawablePayment': self.test_withdrawable_payment_2,
                        'historicalRounds': self.test_historical_rounds_2
                    },
                },
            }
        }
        self.raw_data_example_result_v4 = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor_name,
                    'node_name': self.test_node_name_1,
                    'node_id': self.test_node_id_1,
                    'node_parent_id': self.test_parent_id_1,
                    'time': self.test_last_monitored + 60
                },
                'data': {
                    self.test_proxy_address_1: {
                        'contractVersion': 4,
                        'aggregatorAddress': self.test_aggregator_address_1,
                        'latestRound': self.test_latest_round_1,
                        'latestAnswer': self.test_latest_answer_1,
                        'latestTimestamp': self.test_latest_timestamp_1,
                        'answeredInRound': self.test_answered_in_round_1,
                        'owedPayment': self.test_owed_payment_1,
                        'historicalRounds': self.test_historical_rounds_3
                    },
                    self.test_proxy_address_2: {
                        'contractVersion': 4,
                        'aggregatorAddress': self.test_aggregator_address_2,
                        'latestRound': self.test_latest_round_2,
                        'latestAnswer': self.test_latest_answer_2,
                        'latestTimestamp': self.test_latest_timestamp_2,
                        'answeredInRound': self.test_answered_in_round_2,
                        'owedPayment': self.test_owed_payment_2,
                        'historicalRounds': self.test_historical_rounds_4
                    },
                },
            }
        }
        self.raw_data_example_error = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor_name,
                    'node_parent_id': self.test_parent_id_1,
                    'time': self.test_last_monitored + 60
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }

        # Transformed data example
        self.transformed_data_example_result_v3 = {
            'result': {
                'meta_data': {
                    'node_name': self.test_node_name_1,
                    'node_id': self.test_node_id_1,
                    'node_parent_id': self.test_parent_id_1,
                    'last_monitored': self.test_last_monitored + 60
                },
                'data': {
                    self.test_proxy_address_1: {
                        'contractVersion': 3,
                        'aggregatorAddress': self.test_aggregator_address_1,
                        'latestRound': self.test_latest_round_1,
                        'latestAnswer': self.test_latest_answer_1,
                        'latestTimestamp': self.test_latest_timestamp_1,
                        'answeredInRound': self.test_answered_in_round_1,
                        'withdrawablePayment': self.test_withdrawable_payment_1,
                        'historicalRounds':
                            self.test_historical_rounds_1_transformed
                    },
                    self.test_proxy_address_2: {
                        'contractVersion': 3,
                        'aggregatorAddress': self.test_aggregator_address_2,
                        'latestRound': self.test_latest_round_2,
                        'latestAnswer': self.test_latest_answer_2,
                        'latestTimestamp': self.test_latest_timestamp_2,
                        'answeredInRound': self.test_answered_in_round_2,
                        'withdrawablePayment': self.test_withdrawable_payment_2,
                        'historicalRounds':
                            self.test_historical_rounds_2_transformed
                    },
                },
            }
        }
        self.transformed_data_example_result_v4 = {
            'result': {
                'meta_data': {
                    'node_name': self.test_node_name_1,
                    'node_id': self.test_node_id_1,
                    'node_parent_id': self.test_parent_id_1,
                    'last_monitored': self.test_last_monitored + 60
                },
                'data': {
                    self.test_proxy_address_1: {
                        'contractVersion': 4,
                        'aggregatorAddress': self.test_aggregator_address_1,
                        'latestRound': self.test_latest_round_1,
                        'latestAnswer': self.test_latest_answer_1,
                        'latestTimestamp': self.test_latest_timestamp_1,
                        'answeredInRound': self.test_answered_in_round_1,
                        'owedPayment': self.test_owed_payment_1,
                        'historicalRounds':
                            self.test_historical_rounds_3_transformed
                    },
                    self.test_proxy_address_2: {
                        'contractVersion': 4,
                        'aggregatorAddress': self.test_aggregator_address_2,
                        'latestRound': self.test_latest_round_2,
                        'latestAnswer': self.test_latest_answer_2,
                        'latestTimestamp': self.test_latest_timestamp_2,
                        'answeredInRound': self.test_answered_in_round_2,
                        'owedPayment': self.test_owed_payment_2,
                        'historicalRounds':
                            self.test_historical_rounds_4_transformed
                    },
                },
            }
        }
        self.transformed_data_example_error = {
            'error': {
                'meta_data': {
                    'node_parent_id': self.test_parent_id_1,
                    'time': self.test_last_monitored + 60
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        self.invalid_transformed_data = {'bad_key': 'bad_value'}

        # EVM Contracts with received state
        self.test_evm_contract_1_new_metrics = V3EvmContract(
            self.test_proxy_address_1, self.test_aggregator_address_1,
            self.test_parent_id_1, self.test_node_id_1)
        self.test_evm_contract_2_new_metrics = V3EvmContract(
            self.test_proxy_address_2, self.test_aggregator_address_2,
            self.test_parent_id_1, self.test_node_id_1)
        self.test_evm_contract_3_new_metrics = V4EvmContract(
            self.test_proxy_address_1, self.test_aggregator_address_1,
            self.test_parent_id_1, self.test_node_id_1)
        self.test_evm_contract_4_new_metrics = V4EvmContract(
            self.test_proxy_address_2, self.test_aggregator_address_2,
            self.test_parent_id_1, self.test_node_id_1)

        # Test state before receiving new metrics
        self.test_state_v3 = {
            self.test_node_id_1: {
                self.test_proxy_address_1: copy.deepcopy(
                    self.test_evm_contract_1_new_metrics),
                self.test_proxy_address_2: copy.deepcopy(
                    self.test_evm_contract_2_new_metrics),
            },
        }
        self.test_state_v4 = {
            self.test_node_id_1: {
                self.test_proxy_address_1: copy.deepcopy(
                    self.test_evm_contract_3_new_metrics),
                self.test_proxy_address_2: copy.deepcopy(
                    self.test_evm_contract_4_new_metrics),
            },
        }

        # Update the states with received metrics
        self.test_evm_contract_1_new_metrics.set_latest_round(
            self.test_latest_round_1)
        self.test_evm_contract_1_new_metrics.set_latest_answer(
            self.test_latest_answer_1)
        self.test_evm_contract_1_new_metrics.set_latest_timestamp(
            self.test_latest_timestamp_1)
        self.test_evm_contract_1_new_metrics.set_answered_in_round(
            self.test_answered_in_round_1)
        self.test_evm_contract_1_new_metrics.set_withdrawable_payment(
            self.test_withdrawable_payment_1)
        self.test_evm_contract_1_new_metrics.set_historical_rounds(
            self.test_historical_rounds_1_transformed)
        self.test_evm_contract_1_new_metrics.set_last_monitored(
            self.test_last_monitored + 60)

        self.test_evm_contract_2_new_metrics.set_latest_round(
            self.test_latest_round_2)
        self.test_evm_contract_2_new_metrics.set_latest_answer(
            self.test_latest_answer_2)
        self.test_evm_contract_2_new_metrics.set_latest_timestamp(
            self.test_latest_timestamp_2)
        self.test_evm_contract_2_new_metrics.set_answered_in_round(
            self.test_answered_in_round_2)
        self.test_evm_contract_2_new_metrics.set_withdrawable_payment(
            self.test_withdrawable_payment_2)
        self.test_evm_contract_2_new_metrics.set_historical_rounds(
            self.test_historical_rounds_2_transformed)
        self.test_evm_contract_2_new_metrics.set_last_monitored(
            self.test_last_monitored + 60)

        self.test_evm_contract_3_new_metrics.set_latest_round(
            self.test_latest_round_1)
        self.test_evm_contract_3_new_metrics.set_latest_answer(
            self.test_latest_answer_1)
        self.test_evm_contract_3_new_metrics.set_latest_timestamp(
            self.test_latest_timestamp_1)
        self.test_evm_contract_3_new_metrics.set_answered_in_round(
            self.test_answered_in_round_1)
        self.test_evm_contract_3_new_metrics.set_owed_payment(
            self.test_owed_payment_1)
        self.test_evm_contract_3_new_metrics.set_historical_rounds(
            self.test_historical_rounds_3_transformed)
        self.test_evm_contract_3_new_metrics.set_last_monitored(
            self.test_last_monitored + 60)

        self.test_evm_contract_4_new_metrics.set_latest_round(
            self.test_latest_round_2)
        self.test_evm_contract_4_new_metrics.set_latest_answer(
            self.test_latest_answer_2)
        self.test_evm_contract_4_new_metrics.set_latest_timestamp(
            self.test_latest_timestamp_2)
        self.test_evm_contract_4_new_metrics.set_answered_in_round(
            self.test_answered_in_round_2)
        self.test_evm_contract_4_new_metrics.set_owed_payment(
            self.test_owed_payment_2)
        self.test_evm_contract_4_new_metrics.set_historical_rounds(
            self.test_historical_rounds_4_transformed)
        self.test_evm_contract_4_new_metrics.set_last_monitored(
            self.test_last_monitored + 60)

        # Test state after receiving new metrics
        self.test_state_v3_updated = {
            self.test_node_id_1: {
                self.test_proxy_address_1: self.test_evm_contract_1_new_metrics,
                self.test_proxy_address_2: self.test_evm_contract_2_new_metrics,
            },
        }
        self.test_state_v4_updated = {
            self.test_node_id_1: {
                self.test_proxy_address_1: self.test_evm_contract_3_new_metrics,
                self.test_proxy_address_2: self.test_evm_contract_4_new_metrics,
            },
        }

        meta_data_for_alerting_result_v3 = \
            self.transformed_data_example_result_v3['result']['meta_data']
        self.test_data_for_alerting_result_v3 = {
            'result': {
                'meta_data': meta_data_for_alerting_result_v3,
                'data': {
                    self.test_proxy_address_1: {
                        'latestRound': {
                            'current': self.test_latest_round_1,
                            'previous': None,
                        },
                        'latestAnswer': {
                            'current': self.test_latest_answer_1,
                            'previous': None,
                        },
                        'latestTimestamp': {
                            'current': self.test_latest_timestamp_1,
                            'previous': None,
                        },
                        'answeredInRound': {
                            'current': self.test_answered_in_round_1,
                            'previous': None,
                        },
                        'withdrawablePayment': {
                            'current': self.test_withdrawable_payment_1,
                            'previous': None,
                        },
                        'historicalRounds': {
                            'current':
                                self.test_historical_rounds_1_transformed,
                            'previous': [],
                        },
                        'contractVersion': 3,
                        'aggregatorAddress': self.test_aggregator_address_1,
                    },
                    self.test_proxy_address_2: {
                        'latestRound': {
                            'current': self.test_latest_round_2,
                            'previous': None,
                        },
                        'latestAnswer': {
                            'current': self.test_latest_answer_2,
                            'previous': None,
                        },
                        'latestTimestamp': {
                            'current': self.test_latest_timestamp_2,
                            'previous': None,
                        },
                        'answeredInRound': {
                            'current': self.test_answered_in_round_2,
                            'previous': None,
                        },
                        'withdrawablePayment': {
                            'current': self.test_withdrawable_payment_2,
                            'previous': None,
                        },
                        'historicalRounds': {
                            'current':
                                self.test_historical_rounds_2_transformed,
                            'previous': [],
                        },
                        'contractVersion': 3,
                        'aggregatorAddress': self.test_aggregator_address_2,
                    },
                }
            }
        }
        meta_data_for_alerting_result_v4 = \
            self.transformed_data_example_result_v4['result']['meta_data']
        self.test_data_for_alerting_result_v4 = {
            'result': {
                'meta_data': meta_data_for_alerting_result_v4,
                'data': {
                    self.test_proxy_address_1: {
                        'latestRound': {
                            'current': self.test_latest_round_1,
                            'previous': None,
                        },
                        'latestAnswer': {
                            'current': self.test_latest_answer_1,
                            'previous': None,
                        },
                        'latestTimestamp': {
                            'current': self.test_latest_timestamp_1,
                            'previous': None,
                        },
                        'answeredInRound': {
                            'current': self.test_answered_in_round_1,
                            'previous': None,
                        },
                        'owedPayment': {
                            'current': self.test_owed_payment_1,
                            'previous': None,
                        },
                        'historicalRounds': {
                            'current':
                                self.test_historical_rounds_3_transformed,
                            'previous': [],
                        },
                        'contractVersion': 4,
                        'aggregatorAddress': self.test_aggregator_address_1,
                    },
                    self.test_proxy_address_2: {
                        'latestRound': {
                            'current': self.test_latest_round_2,
                            'previous': None,
                        },
                        'latestAnswer': {
                            'current': self.test_latest_answer_2,
                            'previous': None,
                        },
                        'latestTimestamp': {
                            'current': self.test_latest_timestamp_2,
                            'previous': None,
                        },
                        'answeredInRound': {
                            'current': self.test_answered_in_round_2,
                            'previous': None,
                        },
                        'owedPayment': {
                            'current': self.test_owed_payment_2,
                            'previous': None,
                        },
                        'historicalRounds': {
                            'current':
                                self.test_historical_rounds_4_transformed,
                            'previous': [],
                        },
                        'contractVersion': 4,
                        'aggregatorAddress': self.test_aggregator_address_2,
                    },
                }
            }
        }
        self.test_data_transformer = EVMContractsDataTransformer(
            self.transformer_name, self.dummy_logger, self.redis, self.rabbitmq,
            self.max_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_data_transformer.rabbitmq)
        delete_queue_if_exists(self.test_data_transformer.rabbitmq,
                               self.test_rabbit_queue_name)
        delete_queue_if_exists(self.test_data_transformer.rabbitmq,
                               EVM_CONTRACTS_DT_INPUT_QUEUE_NAME)
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
        self.test_exception = None
        self.redis = None
        self.test_publishing_queue = None
        self.test_data_transformer = None
        self.test_evm_contract_1_new_metrics = None
        self.test_evm_contract_2_new_metrics = None
        self.test_evm_contract_3_new_metrics = None
        self.test_evm_contract_4_new_metrics = None

    def test_str_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name, str(self.test_data_transformer))

    def test_transformer_name_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name,
                         self.test_data_transformer.transformer_name)

    def test_redis_returns_transformer_redis_instance(self) -> None:
        self.assertEqual(self.redis, self.test_data_transformer.redis)

    def test_state_returns_the_nodes_state(self) -> None:
        self.test_data_transformer._state = self.test_data_str
        self.assertEqual(self.test_data_str, self.test_data_transformer.state)

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

    @mock.patch.object(RabbitMQApi, "basic_consume")
    @mock.patch.object(RabbitMQApi, "basic_qos")
    def test_initialise_rabbit_initializes_everything_as_expected(
            self, mock_basic_qos, mock_basic_consume) -> None:
        mock_basic_consume.return_value = None

        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        self.rabbitmq.connect()
        self.test_data_transformer.rabbitmq.queue_delete(
            EVM_CONTRACTS_DT_INPUT_QUEUE_NAME)
        self.test_data_transformer.rabbitmq.exchange_delete(
            HEALTH_CHECK_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(STORE_EXCHANGE)
        self.test_data_transformer.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_data_transformer._initialise_rabbitmq()

        # Perform checks that the connection has been opened and marked as
        # open, that the delivery confirmation variable is set and basic_qos
        # called successfully.
        self.assertTrue(self.test_data_transformer.rabbitmq.is_connected)
        self.assertTrue(
            self.test_data_transformer.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_data_transformer.rabbitmq
                .channel._delivery_confirmation)
        mock_basic_qos.assert_called_once_with(prefetch_count=round(
            self.max_queue_size / 5))

        # Check whether the producing exchanges have been created by
        # using passive=True. If this check fails an exception is raised
        # automatically.
        self.test_data_transformer.rabbitmq.exchange_declare(
            STORE_EXCHANGE, passive=True)
        self.test_data_transformer.rabbitmq.exchange_declare(
            ALERT_EXCHANGE, passive=True)
        self.test_data_transformer.rabbitmq.exchange_declare(
            HEALTH_CHECK_EXCHANGE, passive=True)

        # Check whether the consuming exchanges and queues have been creating by
        # sending messages with the same routing keys as for the bindings.
        self.test_data_transformer.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages, and check that the
        # message received is the message sent
        res = self.test_data_transformer.rabbitmq.queue_declare(
            EVM_CONTRACTS_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_data_transformer.rabbitmq.basic_get(
            EVM_CONTRACTS_DT_INPUT_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())

        mock_basic_consume.assert_called_once()

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

    def test_load_state_successful_if_evm_contract_in_redis_and_redis_online(
            self) -> None:
        """
        We will perform this test for both V3 and V4 type contracts
        """
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_evm_contract_to_redis(self.redis,
                                   self.test_evm_contract_1_new_metrics)
        save_evm_contract_to_redis(self.redis,
                                   self.test_evm_contract_4_new_metrics)

        # Reset evm contract to default values
        self.test_evm_contract_1_new_metrics.reset()
        self.test_evm_contract_4_new_metrics.reset()

        # Load state
        loaded_evm_contract_v3 = self.test_data_transformer.load_state(
            self.test_evm_contract_1_new_metrics)
        loaded_evm_contract_v4 = self.test_data_transformer.load_state(
            self.test_evm_contract_4_new_metrics)

        self.assertEqual(self.test_latest_round_1,
                         loaded_evm_contract_v3.latest_round)
        self.assertEqual(self.test_latest_answer_1,
                         loaded_evm_contract_v3.latest_answer)
        self.assertEqual(self.test_latest_timestamp_1,
                         loaded_evm_contract_v3.latest_timestamp)
        self.assertEqual(self.test_answered_in_round_1,
                         loaded_evm_contract_v3.answered_in_round)
        self.assertEqual(self.test_historical_rounds_1_transformed,
                         loaded_evm_contract_v3.historical_rounds)
        self.assertEqual(self.test_withdrawable_payment_1,
                         loaded_evm_contract_v3.withdrawable_payment)
        self.assertEqual(self.test_last_monitored + 60,
                         loaded_evm_contract_v3.last_monitored)

        self.assertEqual(self.test_latest_round_2,
                         loaded_evm_contract_v4.latest_round)
        self.assertEqual(self.test_latest_answer_2,
                         loaded_evm_contract_v4.latest_answer)
        self.assertEqual(self.test_latest_timestamp_2,
                         loaded_evm_contract_v4.latest_timestamp)
        self.assertEqual(self.test_answered_in_round_2,
                         loaded_evm_contract_v4.answered_in_round)
        self.assertEqual(self.test_historical_rounds_4_transformed,
                         loaded_evm_contract_v4.historical_rounds)
        self.assertEqual(self.test_owed_payment_2,
                         loaded_evm_contract_v4.owed_payment)
        self.assertEqual(self.test_last_monitored + 60,
                         loaded_evm_contract_v4.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_evm_contract_in_redis_and_redis_off(
            self) -> None:
        """
        We will perform this test for both V3 and V4 type contracts
        """

        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_evm_contract_to_redis(self.redis,
                                   self.test_evm_contract_1_new_metrics)
        save_evm_contract_to_redis(self.redis,
                                   self.test_evm_contract_4_new_metrics)

        # Reset evm contract to default values
        self.test_evm_contract_1_new_metrics.reset()
        self.test_evm_contract_4_new_metrics.reset()

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Load state
        loaded_evm_contract_v3 = self.test_data_transformer.load_state(
            self.test_evm_contract_1_new_metrics)
        loaded_evm_contract_v4 = self.test_data_transformer.load_state(
            self.test_evm_contract_4_new_metrics)

        self.assertEqual(None, loaded_evm_contract_v3.latest_round)
        self.assertEqual(None, loaded_evm_contract_v3.latest_answer)
        self.assertEqual(None, loaded_evm_contract_v3.latest_timestamp)
        self.assertEqual(None, loaded_evm_contract_v3.answered_in_round)
        self.assertEqual([], loaded_evm_contract_v3.historical_rounds)
        self.assertEqual(None, loaded_evm_contract_v3.withdrawable_payment)
        self.assertEqual(None, loaded_evm_contract_v3.last_monitored)

        self.assertEqual(None, loaded_evm_contract_v4.latest_round)
        self.assertEqual(None, loaded_evm_contract_v4.latest_answer)
        self.assertEqual(None, loaded_evm_contract_v4.latest_timestamp)
        self.assertEqual(None, loaded_evm_contract_v4.answered_in_round)
        self.assertEqual([], loaded_evm_contract_v4.historical_rounds)
        self.assertEqual(None, loaded_evm_contract_v4.owed_payment)
        self.assertEqual(None, loaded_evm_contract_v4.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_contract_not_in_redis_and_redis_on(
            self) -> None:
        """
        We will perform this test for both V3 and V4 type contracts
        """

        # Clean test db
        self.redis.delete_all()

        # Load state
        loaded_evm_contract_v3 = self.test_data_transformer.load_state(
            self.test_evm_contract_1_new_metrics)
        loaded_evm_contract_v4 = self.test_data_transformer.load_state(
            self.test_evm_contract_4_new_metrics)

        self.assertEqual(self.test_latest_round_1,
                         loaded_evm_contract_v3.latest_round)
        self.assertEqual(self.test_latest_answer_1,
                         loaded_evm_contract_v3.latest_answer)
        self.assertEqual(self.test_latest_timestamp_1,
                         loaded_evm_contract_v3.latest_timestamp)
        self.assertEqual(self.test_answered_in_round_1,
                         loaded_evm_contract_v3.answered_in_round)
        self.assertEqual(self.test_historical_rounds_1_transformed,
                         loaded_evm_contract_v3.historical_rounds)
        self.assertEqual(self.test_withdrawable_payment_1,
                         loaded_evm_contract_v3.withdrawable_payment)
        self.assertEqual(self.test_last_monitored + 60,
                         loaded_evm_contract_v3.last_monitored)

        self.assertEqual(self.test_latest_round_2,
                         loaded_evm_contract_v4.latest_round)
        self.assertEqual(self.test_latest_answer_2,
                         loaded_evm_contract_v4.latest_answer)
        self.assertEqual(self.test_latest_timestamp_2,
                         loaded_evm_contract_v4.latest_timestamp)
        self.assertEqual(self.test_answered_in_round_2,
                         loaded_evm_contract_v4.answered_in_round)
        self.assertEqual(self.test_historical_rounds_4_transformed,
                         loaded_evm_contract_v4.historical_rounds)
        self.assertEqual(self.test_owed_payment_2,
                         loaded_evm_contract_v4.owed_payment)
        self.assertEqual(self.test_last_monitored + 60,
                         loaded_evm_contract_v4.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_contract_not_in_redis_and_redis_off(
            self) -> None:
        # Clean test db
        self.redis.delete_all()

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Load state
        loaded_evm_contract_v3 = self.test_data_transformer.load_state(
            self.test_evm_contract_1_new_metrics)
        loaded_evm_contract_v4 = self.test_data_transformer.load_state(
            self.test_evm_contract_4_new_metrics)

        self.assertEqual(self.test_latest_round_1,
                         loaded_evm_contract_v3.latest_round)
        self.assertEqual(self.test_latest_answer_1,
                         loaded_evm_contract_v3.latest_answer)
        self.assertEqual(self.test_latest_timestamp_1,
                         loaded_evm_contract_v3.latest_timestamp)
        self.assertEqual(self.test_answered_in_round_1,
                         loaded_evm_contract_v3.answered_in_round)
        self.assertEqual(self.test_historical_rounds_1_transformed,
                         loaded_evm_contract_v3.historical_rounds)
        self.assertEqual(self.test_withdrawable_payment_1,
                         loaded_evm_contract_v3.withdrawable_payment)
        self.assertEqual(self.test_last_monitored + 60,
                         loaded_evm_contract_v3.last_monitored)

        self.assertEqual(self.test_latest_round_2,
                         loaded_evm_contract_v4.latest_round)
        self.assertEqual(self.test_latest_answer_2,
                         loaded_evm_contract_v4.latest_answer)
        self.assertEqual(self.test_latest_timestamp_2,
                         loaded_evm_contract_v4.latest_timestamp)
        self.assertEqual(self.test_answered_in_round_2,
                         loaded_evm_contract_v4.answered_in_round)
        self.assertEqual(self.test_historical_rounds_4_transformed,
                         loaded_evm_contract_v4.historical_rounds)
        self.assertEqual(self.test_owed_payment_2,
                         loaded_evm_contract_v4.owed_payment)
        self.assertEqual(self.test_last_monitored + 60,
                         loaded_evm_contract_v4.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_update_state_raises_except_and_keeps_state_if_no_result_or_err(
            self) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)
        expected_state = copy.deepcopy(self.test_state_v3)

        # First confirm that an exception is raised
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._update_state,
                          self.invalid_transformed_data)

        # Check that the state was not modified
        self.assertEqual(expected_state, self.test_data_transformer.state)

    @parameterized.expand([
        ('self.transformed_data_example_result_v3', 'self.test_state_v3',
         'self.test_state_v3_updated'),
        ('self.transformed_data_example_result_v4', 'self.test_state_v4',
         'self.test_state_v4_updated'),
        ('self.transformed_data_example_error', 'self.test_state_v3',
         'self.test_state_v3'),
    ])
    def test_update_state_updates_state_correctly(
            self, transformed_data, initial_state, expected_state) -> None:
        self.test_data_transformer._state = copy.deepcopy(eval(initial_state))
        self.test_data_transformer._state['dummy_id'] = self.test_data_str

        self.test_data_transformer._update_state(eval(transformed_data))

        evaluated_expected_state = eval(expected_state)
        evaluated_expected_state['dummy_id'] = self.test_data_str
        self.assertEqual(self.test_data_transformer.state,
                         evaluated_expected_state)

    @parameterized.expand([
        ('self.transformed_data_example_result_v3',
         'self.transformed_data_example_result_v3'),
        ('self.transformed_data_example_result_v4',
         'self.transformed_data_example_result_v4'),
        ('self.transformed_data_example_error',
         'self.transformed_data_example_error'),
    ])
    def test_process_transformed_data_for_saving_returns_expected_data(
            self, transformed_data: str, expected_processed_data: str) -> None:
        processed_data = \
            self.test_data_transformer._process_transformed_data_for_saving(
                eval(transformed_data))
        self.assertDictEqual(eval(expected_processed_data), processed_data)

    def test_proc_trans_data_for_saving_raises_unexp_data_except_on_unexp_data(
            self) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_saving,
            self.invalid_transformed_data)

    @parameterized.expand([
        ('self.transformed_data_example_result_v3', 'self.test_state_v3',
         'self.test_data_for_alerting_result_v3'),
        ('self.transformed_data_example_result_v4', 'self.test_state_v4',
         'self.test_data_for_alerting_result_v4'),
        ('self.transformed_data_example_error', 'self.test_state_v3',
         'self.transformed_data_example_error'),
    ])
    def test_process_transformed_data_for_alerting_returns_expected_data(
            self, transformed_data, initial_state,
            expected_processed_data) -> None:
        self.test_data_transformer._state = copy.deepcopy(eval(initial_state))
        actual_data = \
            self.test_data_transformer._process_transformed_data_for_alerting(
                eval(transformed_data))
        self.assertEqual(eval(expected_processed_data), actual_data)

    def test_proc_trans_data_for_alerting_raise_unex_data_except_on_unex_data(
            self) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_alerting,
            self.invalid_transformed_data)

    @parameterized.expand([
        ('self.raw_data_example_result_v3', 'self.test_state_v3',
         'self.transformed_data_example_result_v3'),
        ('self.raw_data_example_result_v4', 'self.test_state_v4',
         'self.transformed_data_example_result_v4'),
        ('self.raw_data_example_error', 'self.test_state_v3',
         'self.transformed_data_example_error'),
    ])
    @mock.patch.object(EVMContractsDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(EVMContractsDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_returns_expected_data_if_result(
            self, raw_data, init_state, expected_processed_data,
            mock_process_for_saving, mock_process_for_alerting) -> None:
        self.test_data_transformer._state = copy.deepcopy(eval(init_state))
        mock_process_for_saving.return_value = {'key_1': 'val1'}
        mock_process_for_alerting.return_value = {'key_2': 'val2'}

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(eval(raw_data))

        expected_trans_data = copy.deepcopy(eval(expected_processed_data))

        self.assertEqual(expected_trans_data, trans_data)
        self.assertEqual({'key_2': 'val2'}, data_for_alerting)
        self.assertEqual({'key_1': 'val1'}, data_for_saving)

    def test_transform_data_raises_unexpected_data_exception_on_unexpected_data(
            self) -> None:
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._transform_data,
                          self.invalid_transformed_data)

    def test_place_latest_data_on_queue_places_the_correct_data_on_queue(
            self) -> None:
        self.test_data_transformer._place_latest_data_on_queue(
            self.test_data_for_alerting_result_v3,
            self.transformed_data_example_result_v3
        )
        expected_data_for_alerting = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': CL_CONTRACTS_TRANSFORMED_DATA_ROUTING_KEY,
            'data': self.test_data_for_alerting_result_v3,
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_for_saving = {
            'exchange': STORE_EXCHANGE,
            'routing_key': CL_CONTRACTS_TRANSFORMED_DATA_ROUTING_KEY,
            'data': self.transformed_data_example_result_v3,
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }

        self.assertEqual(2, self.test_data_transformer.publishing_queue.qsize())
        self.assertDictEqual(
            expected_data_for_alerting,
            self.test_data_transformer.publishing_queue.queue[0])
        self.assertDictEqual(
            expected_data_for_saving,
            self.test_data_transformer.publishing_queue.queue[1])

    @parameterized.expand([(V3EvmContract, 3,), (V4EvmContract, 4,), ])
    def test_create_state_entry_creates_new_entry_if_no_entry_for_contract(
            self, contract_class, version) -> None:
        """
        In this test we will check that a new state entry will be created for a
        node's contract state if there is no entry for that node or contract
        yet. This test will be performed for both v3 and v4 contracts
        """
        # Add some dummy state to confirm that the state is updated correctly
        self.test_data_transformer._state['dummy_id'] = self.test_data_str

        # Test for when no entry has been added yet for both the contract and
        # the node
        state_created = self.test_data_transformer._create_state_entry(
            self.test_node_id_1, self.test_proxy_address_1,
            self.test_parent_id_1, version, self.test_aggregator_address_1)
        expected_state = {
            'dummy_id': self.test_data_str,
            self.test_node_id_1: {
                self.test_proxy_address_1: contract_class(
                    self.test_proxy_address_1, self.test_aggregator_address_1,
                    self.test_parent_id_1, self.test_node_id_1)
            }
        }
        self.assertEqual(expected_state, self.test_data_transformer.state)
        self.assertTrue(state_created)

        # Test for when an entry has already been created for the node
        state_created = self.test_data_transformer._create_state_entry(
            self.test_node_id_1, self.test_proxy_address_2,
            self.test_parent_id_1, version, self.test_aggregator_address_2)
        expected_state[self.test_node_id_1][
            self.test_proxy_address_2] = contract_class(
            self.test_proxy_address_2, self.test_aggregator_address_2,
            self.test_parent_id_1, self.test_node_id_1)
        self.assertEqual(expected_state, self.test_data_transformer.state)
        self.assertTrue(state_created)

    @parameterized.expand([
        (3, 'self.test_state_v3_updated',),
        (4, 'self.test_state_v4_updated',),
    ])
    def test_create_state_entry_no_new_contract_entry_if_already_created_with_same_version(
            self, version, init_state) -> None:
        """
        In this test we will check that no new entry will be created for a
        node's contract state if there is already one with the same version.
        This test will be performed for both v3 and v4 contracts
        """
        self.test_data_transformer._state = copy.deepcopy(eval(init_state))
        self.test_data_transformer._state['dummy_id'] = self.test_data_str

        state_created = self.test_data_transformer._create_state_entry(
            self.test_node_id_1, self.test_proxy_address_1,
            self.test_parent_id_1, version, self.test_aggregator_address_1)

        # We expect an unchanged state
        expected_state = copy.deepcopy(eval(init_state))
        expected_state['dummy_id'] = self.test_data_str
        self.assertEqual(expected_state, self.test_data_transformer.state)
        self.assertFalse(state_created)

    @parameterized.expand([
        ('self.test_state_v3_updated', V4EvmContract, 4,),
        ('self.test_state_v4_updated', V3EvmContract, 3,),
    ])
    def test_create_state_entry_creates_new_entry_if_contract_entry_has_a_different_version(
            self, init_state, new_contract_class, new_version) -> None:
        """
        In this test we will check that a new state entry will be created for a
        node's contract state if there is an entry with a different version for
        that node and contract
        """
        self.test_data_transformer._state = copy.deepcopy(eval(init_state))
        self.test_data_transformer._state['dummy_id'] = self.test_data_str

        state_created = self.test_data_transformer._create_state_entry(
            self.test_node_id_1, self.test_proxy_address_1,
            self.test_parent_id_1, new_version, self.test_aggregator_address_1)

        expected_state = {
            'dummy_id': self.test_data_str,
            self.test_node_id_1: {
                self.test_proxy_address_1: new_contract_class(
                    self.test_proxy_address_1, self.test_aggregator_address_1,
                    self.test_parent_id_1, self.test_node_id_1),
                self.test_proxy_address_2:
                    eval(init_state)[self.test_node_id_1][
                        self.test_proxy_address_2]
            }
        }
        self.assertEqual(expected_state, self.test_data_transformer.state)
        self.assertTrue(state_created)

    @parameterized.expand([({}, False,), ('self.test_state_v3', True), ])
    @mock.patch.object(EVMContractsDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_transforms_data_if_data_valid(
            self, state, state_is_str, mock_ack, mock_trans_data) -> None:
        """
        We will check that the data is transformed by checking that
        `_transform_data` is called correctly. The actual transformations are
        # already tested. Note we will test for both result and error, and when
        # the node and contracts are both in the state and not in the state.
        """
        mock_ack.return_value = None
        mock_trans_data.return_value = (None, None, None)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body_result = json.dumps(self.raw_data_example_result_v3)
        body_error = json.dumps(self.raw_data_example_error)
        properties = pika.spec.BasicProperties()

        if state_is_str:
            self.test_data_transformer._state = copy.deepcopy(eval(state))
        else:
            self.test_data_transformer._state = copy.deepcopy(state)

        # Send raw data
        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body_result)
        mock_trans_data.assert_called_once_with(self.raw_data_example_result_v3)
        mock_trans_data.reset_mock()

        # To reset the state as if the node was not already added
        if state_is_str:
            self.test_data_transformer._state = copy.deepcopy(eval(state))
        else:
            self.test_data_transformer._state = copy.deepcopy(state)

        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body_error)

        mock_trans_data.assert_called_once_with(self.raw_data_example_error)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @parameterized.expand([
        ({},), (None,), ("test",), ({'bad_key': 'bad_value'},)
    ])
    @mock.patch.object(EVMContractsDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_call_trans_data_if_err_res_not_in_data(
            self, invalid_data, mock_ack, mock_trans_data) -> None:
        mock_ack.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(invalid_data)
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

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_updates_state_if_no_processing_errors(
            self, mock_ack) -> None:
        # To make sure there is no state in redis as the state must be compared.
        # We will check that the state has been updated correctly.
        self.redis.delete_all()

        mock_ack.return_value = None

        # We must initialise rabbit to the environment and parameters needed by
        # `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to check that the update does not modify
        # nodes not in question
        self.test_data_transformer._state['node2'] = self.test_data_str

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that there are 2 nodes in the state, one which was not modified,
        # and the other having 2 contracts with metrics the same as the newly
        # given data.
        self.assertEqual(2, len(self.test_data_transformer._state.keys()))
        self.assertEqual(2, len(self.test_data_transformer._state[
                                    self.test_node_id_1].keys()))
        contract_1_expected_data = copy.deepcopy(
            self.test_evm_contract_1_new_metrics)
        contract_2_expected_data = copy.deepcopy(
            self.test_evm_contract_2_new_metrics)
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['node2'])
        self.assertEqual(
            contract_1_expected_data,
            self.test_data_transformer._state[self.test_node_id_1][
                self.test_proxy_address_1])
        self.assertEqual(
            contract_2_expected_data,
            self.test_data_transformer._state[self.test_node_id_1][
                self.test_proxy_address_2])

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMContractsDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_update_state_if_processing_fails(
            self, mock_ack, mock_transform_data) -> None:
        """
        We will automate processing failure by generating an exception from the
        self._transform_data function.
        """
        mock_ack.return_value = None
        mock_transform_data.side_effect = self.test_exception

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Make the state non-empty and save it to redis. This will be used to
        # check that the state is not updated with new metrics if processing
        # fails
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)
        new_contract_1 = V3EvmContract(
            self.test_proxy_address_1, self.test_aggregator_address_1,
            self.test_parent_id_1, self.test_node_id_1)
        new_contract_2 = V3EvmContract(
            self.test_proxy_address_2, self.test_aggregator_address_2,
            self.test_parent_id_1, self.test_node_id_1)
        save_evm_contract_to_redis(self.redis, new_contract_1)
        save_evm_contract_to_redis(self.redis, new_contract_2)

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that there is 1 node and 2 contracts in the state with
        # unmodified data.
        expected_data_contract_1 = copy.deepcopy(new_contract_1)
        expected_data_contract_2 = copy.deepcopy(new_contract_2)
        self.assertEqual(1, len(self.test_data_transformer._state.keys()))
        self.assertEqual(2, len(self.test_data_transformer._state[
                                    self.test_node_id_1].keys()))
        self.assertEqual(
            expected_data_contract_1,
            self.test_data_transformer._state[self.test_node_id_1][
                self.test_proxy_address_1])
        self.assertEqual(
            expected_data_contract_2,
            self.test_data_transformer._state[self.test_node_id_1][
                self.test_proxy_address_2])

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMContractsDataTransformer, "_transform_data")
    @mock.patch.object(EVMContractsDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_places_data_on_queue_if_no_processing_errors(
            self, mock_ack, mock_place_on_queue, mock_trans_data) -> None:
        mock_ack.return_value = None
        mock_trans_data.return_value = (
            self.transformed_data_example_result_v3,
            self.test_data_for_alerting_result_v3,
            self.transformed_data_example_result_v3
        )

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)
        args, _ = mock_place_on_queue.call_args
        self.assertDictEqual(self.test_data_for_alerting_result_v3, args[0])
        self.assertDictEqual(self.transformed_data_example_result_v3, args[1])
        self.assertEqual(2, len(args))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @parameterized.expand([
        ({},), (None,), ("test",), ({'bad_key': 'bad_value'},)
    ])
    @mock.patch.object(EVMContractsDataTransformer,
                       "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_data_on_queue_if_processing_error(
            self, invalid_data, mock_ack, mock_place_on_queue) -> None:
        mock_ack.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(invalid_data)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that place_on_queue was not called
        mock_place_on_queue.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_waiting_on_queue_if_no_process_errors(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None

        # Load the state to avoid loading from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that send_data was called
        self.assertEqual(1, mock_send_data.call_count)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMContractsDataTransformer, "_transform_data")
    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_waiting_on_queue_if_process_errors(
            self, mock_ack, mock_send_data, mock_transform_data) -> None:
        """
        We will automate processing errors by making self._transform_data
        generate an exception.
        """
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_transform_data.side_effect = self.test_exception

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that send_data was called
        self.assertEqual(1, mock_send_data.call_count)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsDataTransformer, "_send_heartbeat")
    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_hb_if_no_proc_errors_and_send_data_success(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        test_hb = {
            'component_name': self.test_data_transformer.transformer_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp(),
        }

        # Load the state to avoid loading data from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)
        mock_send_hb.assert_called_once_with(test_hb)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMContractsDataTransformer, "_update_state")
    @mock.patch.object(EVMContractsDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_proc_errors(
            self, mock_ack, mock_send_hb, mock_update_state) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_update_state.side_effect = self.test_exception

        # Load the state to avoid loading data from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that send_heartbeat was not called
        mock_send_hb.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(EVMContractsDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_send_data_fails(
            self, mock_ack, mock_send_hb, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_send_data.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid loading data from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that send_heartbeat was not called
        mock_send_hb.assert_not_called()

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @parameterized.expand([
        (pika.exceptions.AMQPConnectionError,
         pika.exceptions.AMQPConnectionError('test err'),),
        (pika.exceptions.AMQPChannelError,
         pika.exceptions.AMQPChannelError('test err'),),
        (Exception, Exception('test'),)
    ])
    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_err_if_raised_by_send_data(
            self, exception_type, exception_instance, mock_ack,
            mock_send_data) -> None:
        """
        We will perform this test only for errors we know that can be raised
        """
        mock_ack.return_value = None
        mock_send_data.side_effect = exception_instance

        # Load the state to avoid having to load data from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data and assert exception
        self.assertRaises(
            exception_type, self.test_data_transformer._process_raw_data,
            blocking_channel, method, properties, body
        )

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @parameterized.expand([
        (pika.exceptions.AMQPConnectionError,
         pika.exceptions.AMQPConnectionError('test err'),),
        (pika.exceptions.AMQPChannelError,
         pika.exceptions.AMQPChannelError('test err'),),
        (Exception, Exception('test'),)
    ])
    @mock.patch.object(EVMContractsDataTransformer, "_send_heartbeat")
    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_err_if_raised_by_send_hb(
            self, exception_type, exception_instance, mock_ack,
            mock_send_data, mock_send_hb) -> None:
        """
        We will perform this test only for errors we know that can be raised
        """
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.side_effect = exception_instance

        # Load the state to avoid having to load data from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data and assert exception
        self.assertRaises(
            exception_type, self.test_data_transformer._process_raw_data,
            blocking_channel, method, properties, body
        )

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_msg_not_del_exception_if_raised_by_send_data(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having to load data from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data. Test would fail if an exception is raised
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body
        )

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMContractsDataTransformer, "_send_heartbeat")
    @mock.patch.object(EVMContractsDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_msg_not_del_exception_if_raised_by_send_hb(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having to load data from redis.
        self.test_data_transformer._state = copy.deepcopy(self.test_state_v3)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=CHAINLINK_CONTRACTS_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result_v3)
        properties = pika.spec.BasicProperties()

        # Send raw data. Test would fail if an exception is raised
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body
        )

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)
