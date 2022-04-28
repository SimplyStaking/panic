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
from src.data_transformers.node.evm import EVMNodeDataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.nodes.evm_node import EVMNode
from src.utils import env
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE, STORE_EXCHANGE, ALERT_EXCHANGE,
    EVM_NODE_DT_INPUT_QUEUE_NAME, EVM_NODE_RAW_DATA_ROUTING_KEY,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
from src.utils.exceptions import (PANICException, NodeIsDownException,
                                  ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, disconnect_from_rabbit,
    delete_exchange_if_exists, save_evm_node_to_redis)


class TestEVMNodeDataTransformer(unittest.TestCase):
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
        self.transformer_name = 'test_evm_node_data_transformer'

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

        # EVM Node instance
        self.test_evm_node_name = 'test_evm_node'
        self.test_evm_node_id = 'test_evm_node_id345834t8h3r5893h8'
        self.test_evm_node_parent_id = 'test_evm_node_parent_id34978gt63gtg'
        self.test_evm_node = EVMNode(
            self.test_evm_node_name, self.test_evm_node_id,
            self.test_evm_node_parent_id)
        self.test_state = {self.test_evm_node_id: self.test_evm_node}
        self.test_evm_node_is_down_exception = NodeIsDownException(
            self.test_evm_node.node_name)

        # Some test metrics
        self.test_went_down_at = None
        self.test_current_height = 1000

        # Set evm node values
        self.test_evm_node.set_went_down_at(self.test_went_down_at)
        self.test_evm_node.set_current_height(self.test_current_height)
        self.test_evm_node.set_syncing(True)
        self.test_evm_node.set_last_monitored(self.test_last_monitored)

        # Some raw data examples
        self.raw_data_example_result = {
            'result': {
                'meta_data': {
                    'monitor_name': 'test_monitor',
                    'node_name': self.test_evm_node.node_name,
                    'node_id': self.test_evm_node.node_id,
                    'node_parent_id': self.test_evm_node.parent_id,
                    'time': self.test_last_monitored + 60
                },
                'data': {
                    'current_height': 1010,
                    'syncing': True
                },
            }
        }
        self.raw_data_example_general_error = {
            'error': {
                'meta_data': {
                    'monitor_name': 'test_monitor',
                    'node_name': self.test_evm_node.node_name,
                    'node_id': self.test_evm_node.node_id,
                    'node_parent_id': self.test_evm_node.parent_id,
                    'time': self.test_last_monitored + 60
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        self.raw_data_example_downtime_error = {
            'error': {
                'meta_data': {
                    'monitor_name': 'test_monitor',
                    'node_name': self.test_evm_node.node_name,
                    'node_id': self.test_evm_node.node_id,
                    'node_parent_id': self.test_evm_node.parent_id,
                    'time': self.test_last_monitored + 60
                },
                'message': self.test_evm_node_is_down_exception.message,
                'code': self.test_evm_node_is_down_exception.code,
            }
        }

        # Transformed data example
        self.transformed_data_example_result = {
            'result': {
                'meta_data': {
                    'node_name': self.test_evm_node.node_name,
                    'node_id': self.test_evm_node.node_id,
                    'node_parent_id': self.test_evm_node.parent_id,
                    'last_monitored': self.test_last_monitored + 60
                },
                'data': {
                    'current_height': 1010,
                    'syncing': True,
                    'went_down_at': None,
                },
            }
        }
        self.transformed_data_example_general_error = {
            'error': {
                'meta_data': {
                    'node_name': self.test_evm_node.node_name,
                    'node_id': self.test_evm_node.node_id,
                    'node_parent_id': self.test_evm_node.parent_id,
                    'time': self.test_last_monitored + 60
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        self.transformed_data_example_downtime_error = {
            'error': {
                'meta_data': {
                    'node_name': self.test_evm_node.node_name,
                    'node_id': self.test_evm_node.node_id,
                    'node_parent_id': self.test_evm_node.parent_id,
                    'time': self.test_last_monitored + 60
                },
                'message': self.test_evm_node_is_down_exception.message,
                'code': self.test_evm_node_is_down_exception.code,
                'data': {'went_down_at': self.test_last_monitored + 60}
            }
        }
        self.invalid_transformed_data = {'bad_key': 'bad_value'}

        # EVM Node which is down
        self.test_evm_node_down = copy.deepcopy(self.test_evm_node)
        self.test_evm_node_down.set_went_down_at(
            self.transformed_data_example_downtime_error['error']['data'][
                'went_down_at'])

        # EVM Node with new metrics
        self.test_evm_node_new_metrics = EVMNode(
            self.test_evm_node_name, self.test_evm_node_id,
            self.test_evm_node_parent_id)
        self.test_evm_node_new_metrics.set_went_down_at(None)
        self.test_evm_node_new_metrics.set_current_height(1010)
        self.test_evm_node_new_metrics.set_syncing(True)
        self.test_evm_node_new_metrics.set_last_monitored(
            self.test_last_monitored + 60)

        meta_data_for_alerting_result = self.transformed_data_example_result[
            'result']['meta_data']
        self.test_data_for_alerting_result = {
            'result': {
                'meta_data': meta_data_for_alerting_result,
                'data': {
                    'current_height': {
                        'current':
                            self.test_evm_node_new_metrics.current_height,
                        'previous': self.test_evm_node.current_height
                    },
                    'syncing': {
                        'current': self.test_evm_node_new_metrics.syncing,
                        'previous': self.test_evm_node.syncing,
                    },
                    'went_down_at': {
                        'current': self.test_evm_node_new_metrics.went_down_at,
                        'previous': self.test_evm_node.went_down_at,
                    }
                }
            }
        }
        meta_data_for_alerting_down_err = \
            self.transformed_data_example_downtime_error['error']['meta_data']
        down_error_msg = self.test_evm_node_is_down_exception.message
        down_error_code = self.test_evm_node_is_down_exception.code
        new_went_down_at = self.transformed_data_example_downtime_error[
            'error']['data']['went_down_at']
        self.test_data_for_alerting_down_error = {
            'error': {
                'meta_data': meta_data_for_alerting_down_err,
                'code': down_error_code,
                'message': down_error_msg,
                'data': {
                    'went_down_at': {
                        'current': new_went_down_at,
                        'previous': self.test_evm_node.went_down_at,
                    }
                }
            }
        }
        self.test_data_transformer = EVMNodeDataTransformer(
            self.transformer_name, self.dummy_logger, self.redis, self.rabbitmq,
            self.max_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_data_transformer.rabbitmq)
        delete_queue_if_exists(self.test_data_transformer.rabbitmq,
                               self.test_rabbit_queue_name)
        delete_queue_if_exists(self.test_data_transformer.rabbitmq,
                               EVM_NODE_DT_INPUT_QUEUE_NAME)
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
        self.test_evm_node_is_down_exception = None
        self.test_exception = None
        self.redis = None
        self.test_evm_node = None
        self.test_evm_node_new_metrics = None
        self.test_state = None
        self.test_publishing_queue = None
        self.test_data_transformer = None
        self.test_evm_node_down = None

    def test_str_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name, str(self.test_data_transformer))

    def test_transformer_name_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name,
                         self.test_data_transformer.transformer_name)

    def test_redis_returns_transformer_redis_instance(self) -> None:
        self.assertEqual(self.redis, self.test_data_transformer.redis)

    def test_state_returns_the_nodes_state(self) -> None:
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
            EVM_NODE_DT_INPUT_QUEUE_NAME)
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
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY, body=self.test_data_str,
            is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages, and check that the
        # message received is the message sent
        res = self.test_data_transformer.rabbitmq.queue_declare(
            EVM_NODE_DT_INPUT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_data_transformer.rabbitmq.basic_get(
            EVM_NODE_DT_INPUT_QUEUE_NAME)
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

    def test_load_state_successful_if_evm_node_exists_in_redis_and_redis_online(
            self) -> None:
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_evm_node_to_redis(self.redis, self.test_evm_node)

        # Reset evm node to default values
        self.test_evm_node.reset()

        # Load state
        loaded_evm_node = self.test_data_transformer.load_state(
            self.test_evm_node)

        self.assertEqual(self.test_went_down_at, loaded_evm_node.went_down_at)
        self.assertEqual(self.test_current_height,
                         loaded_evm_node.current_height)
        self.assertEqual(False, loaded_evm_node.syncing)
        self.assertEqual(self.test_last_monitored,
                         loaded_evm_node.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_evm_node_in_redis_and_redis_offline(
            self) -> None:
        # Clean test db
        self.redis.delete_all()

        # Save state to Redis first
        save_evm_node_to_redis(self.redis, self.test_evm_node)

        # Reset evm node to default values
        self.test_evm_node.reset()

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Load state
        loaded_evm_node = self.test_data_transformer.load_state(
            self.test_evm_node)

        self.assertEqual(None, loaded_evm_node.went_down_at)
        self.assertEqual(None, loaded_evm_node.current_height)
        self.assertEqual(False, loaded_evm_node.syncing)
        self.assertEqual(None, loaded_evm_node.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_node_not_in_redis_and_redis_online(
            self) -> None:
        # Clean test db
        self.redis.delete_all()

        # Load state
        loaded_evm_node = self.test_data_transformer.load_state(
            self.test_evm_node)

        self.assertEqual(self.test_went_down_at, loaded_evm_node.went_down_at)
        self.assertEqual(self.test_current_height,
                         loaded_evm_node.current_height)
        self.assertEqual(True, loaded_evm_node.syncing)
        self.assertEqual(self.test_last_monitored,
                         loaded_evm_node.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_load_state_keeps_same_state_if_node_not_in_redis_and_redis_off(
            self) -> None:
        # Clean test db
        self.redis.delete_all()

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if redis is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Load state
        loaded_evm_node = self.test_data_transformer.load_state(
            self.test_evm_node)

        self.assertEqual(self.test_went_down_at, loaded_evm_node.went_down_at)
        self.assertEqual(self.test_current_height,
                         loaded_evm_node.current_height)
        self.assertEqual(True, loaded_evm_node.syncing)
        self.assertEqual(self.test_last_monitored,
                         loaded_evm_node.last_monitored)

        # Clean test db
        self.redis.delete_all()

    def test_update_state_raises_except_and_keeps_state_if_no_result_or_err(
            self) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        expected_state = copy.deepcopy(self.test_state)

        # First confirm that an exception is raised
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._update_state,
                          self.invalid_transformed_data)

        # Check that the state was not modified
        self.assertEqual(expected_state, self.test_data_transformer.state)

    @parameterized.expand([
        ('self.transformed_data_example_result',
         'self.test_evm_node_new_metrics', True),
        ('self.transformed_data_example_general_error', 'self.test_evm_node',
         True),
        ('self.transformed_data_example_downtime_error',
         'self.test_evm_node_down', False),
    ])
    def test_update_state_updates_state_correctly(
            self, transformed_data: str, expected_state: str,
            evm_node_expected_up: bool) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        old_state = copy.deepcopy(self.test_data_transformer._state)

        self.test_data_transformer._update_state(eval(transformed_data))

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the evm_nodes not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        # Check that the evm nodes' state values have been modified correctly
        self.assertEqual(
            eval(expected_state),
            self.test_data_transformer._state[self.test_evm_node_id])

        # Check that the node is marked as up/down accordingly
        if evm_node_expected_up:
            self.assertFalse(
                self.test_data_transformer._state[
                    self.test_evm_node_id].is_down)
        else:
            self.assertTrue(
                self.test_data_transformer._state[
                    self.test_evm_node_id].is_down)

    @parameterized.expand([
        ('self.transformed_data_example_result',
         'self.transformed_data_example_result'),
        ('self.transformed_data_example_general_error',
         'self.transformed_data_example_general_error'),
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
        ('self.transformed_data_example_result',
         'self.test_data_for_alerting_result'),
        ('self.transformed_data_example_general_error',
         'self.transformed_data_example_general_error'),
        ('self.transformed_data_example_downtime_error',
         'self.test_data_for_alerting_down_error'),
    ])
    def test_process_transformed_data_for_alerting_returns_expected_data(
            self, transformed_data: str, expected_processed_data: str) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        actual_data = \
            self.test_data_transformer._process_transformed_data_for_alerting(
                eval(transformed_data))
        self.assertDictEqual(eval(expected_processed_data), actual_data)

    def test_proc_trans_data_for_alerting_raise_unex_data_except_on_unex_data(
            self) -> None:
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_alerting,
            self.invalid_transformed_data)

    @parameterized.expand([
        ('self.raw_data_example_result',
         'self.transformed_data_example_result'),
        ('self.raw_data_example_general_error',
         'self.transformed_data_example_general_error'),
        ('self.raw_data_example_downtime_error',
         'self.transformed_data_example_downtime_error'),
    ])
    @mock.patch.object(EVMNodeDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(EVMNodeDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_returns_expected_data_if_result(
            self, raw_data, expected_processed_data, mock_process_for_saving,
            mock_process_for_alerting) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        self.test_data_transformer._state[self.test_evm_node_id].reset()
        mock_process_for_saving.return_value = {'key_1': 'val1'}
        mock_process_for_alerting.return_value = {'key_2': 'val2'}

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(eval(raw_data))

        expected_trans_data = copy.deepcopy(eval(expected_processed_data))

        self.assertDictEqual(expected_trans_data, trans_data)
        self.assertDictEqual({'key_2': 'val2'}, data_for_alerting)
        self.assertDictEqual({'key_1': 'val1'}, data_for_saving)

    def test_transform_data_raises_unexpected_data_exception_on_unexpected_data(
            self) -> None:
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._transform_data,
                          self.invalid_transformed_data)

    @parameterized.expand([
        ('self.transformed_data_example_result',
         'self.test_data_for_alerting_result',
         'self.transformed_data_example_result'),
        ('self.transformed_data_example_general_error',
         'self.transformed_data_example_general_error',
         'self.transformed_data_example_general_error'),
    ])
    def test_place_latest_data_on_queue_places_the_correct_data_on_queue(
            self, transformed_data: str, data_for_alerting: str,
            data_for_saving: str) -> None:
        self.test_data_transformer._place_latest_data_on_queue(
            eval(transformed_data), eval(data_for_alerting),
            eval(data_for_saving)
        )
        expected_data_for_alerting = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            'data': eval(data_for_alerting),
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_for_saving = {
            'exchange': STORE_EXCHANGE,
            'routing_key': EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            'data': eval(data_for_saving),
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

    @parameterized.expand([({}, False,), ('self.test_state', True), ])
    @mock.patch.object(EVMNodeDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_transforms_data_if_data_valid(
            self, state, state_is_str, mock_ack, mock_trans_data) -> None:
        """
        We will check that the data is transformed by checking that
        `_transform_data` is called correctly. The actual transformations are
        # already tested. Note we will test for both result and error, and when
        # the node is both in the state and not in the state.
        """
        mock_ack.return_value = None
        mock_trans_data.return_value = (None, None, None)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body_result = json.dumps(self.raw_data_example_result)
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
            self.raw_data_example_result)
        mock_trans_data.reset_mock()

        # To reset the state as if the node was not already added
        if state_is_str:
            self.test_data_transformer._state = copy.deepcopy(eval(state))
        else:
            self.test_data_transformer._state = copy.deepcopy(state)

        self.test_data_transformer._process_raw_data(blocking_channel,
                                                     method, properties,
                                                     body_error)

        mock_trans_data.assert_called_once_with(
            self.raw_data_example_general_error)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @parameterized.expand([
        ({},), (None,), ("test",), ({'bad_key': 'bad_value'},)
    ])
    @mock.patch.object(EVMNodeDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_call_trans_data_if_err_res_not_in_data(
            self, invalid_data, mock_ack, mock_trans_data) -> None:
        mock_ack.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
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
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
        properties = pika.spec.BasicProperties()

        # Make the state non-empty to check that the update does not modify
        # nodes not in question
        self.test_data_transformer._state['node2'] = self.test_data_str

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that there are 2 entries in the state, one which was not
        # modified, and the other having metrics the same as the newly
        # given data.
        expected_data = copy.deepcopy(self.test_evm_node_new_metrics)
        self.assertEqual(2, len(self.test_data_transformer._state.keys()))
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['node2'])
        self.assertEqual(
            expected_data,
            self.test_data_transformer._state[self.test_evm_node_id])

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMNodeDataTransformer, "_transform_data")
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
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
        properties = pika.spec.BasicProperties()

        # Make the state non-empty and save it to redis
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        save_evm_node_to_redis(self.redis, self.test_evm_node)

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)

        # Check that there is 1 entry in the state, one which was not modified.
        expected_data = copy.deepcopy(self.test_evm_node)
        self.assertEqual(1, len(self.test_data_transformer._state.keys()))
        self.assertEqual(
            expected_data,
            self.test_data_transformer._state[self.test_evm_node_id])

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMNodeDataTransformer, "_transform_data")
    @mock.patch.object(EVMNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_places_data_on_queue_if_no_processing_errors(
            self, mock_ack, mock_place_on_queue, mock_trans_data) -> None:
        mock_ack.return_value = None
        mock_trans_data.return_value = (
            self.transformed_data_example_result,
            self.test_data_for_alerting_result,
            self.transformed_data_example_result
        )

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)
        args, _ = mock_place_on_queue.call_args
        self.assertDictEqual(self.transformed_data_example_result, args[0])
        self.assertDictEqual(self.test_data_for_alerting_result, args[1])
        self.assertDictEqual(self.transformed_data_example_result, args[2])
        self.assertEqual(3, len(args))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @parameterized.expand([
        ({},), (None,), ("test",), ({'bad_key': 'bad_value'},)
    ])
    @mock.patch.object(EVMNodeDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_data_on_queue_if_processing_error(
            self, invalid_data, mock_ack, mock_place_on_queue) -> None:
        mock_ack.return_value = None

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
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

    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_waiting_on_queue_if_no_process_errors(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None

        # Load the state to avoid errors when having the node already in redis
        # due to other tests.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
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

    @mock.patch.object(EVMNodeDataTransformer, "_transform_data")
    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
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
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
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
    @mock.patch.object(EVMNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
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

        # Load the state to avoid having the node already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
        properties = pika.spec.BasicProperties()

        # Send raw data
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body)
        mock_send_hb.assert_called_once_with(test_hb)

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMNodeDataTransformer, "_update_state")
    @mock.patch.object(EVMNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_proc_errors(
            self, mock_ack, mock_send_hb, mock_update_state) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_update_state.side_effect = self.test_exception

        # Load the state to avoid having the node already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
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

    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
    @mock.patch.object(EVMNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_send_data_fails(
            self, mock_ack, mock_send_hb, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_send_data.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having the node already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
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
    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_err_if_raised_by_send_data(
            self, exception_type, exception_instance, mock_ack,
            mock_send_data) -> None:
        """
        We will perform this test only for errors we know that can be raised
        """
        mock_ack.return_value = None
        mock_send_data.side_effect = exception_instance

        # Load the state to avoid having the node already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
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
    @mock.patch.object(EVMNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
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

        # Load the state to avoid having the node already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
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

    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_msg_not_del_exception_if_raised_by_send_data(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having the node already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
        properties = pika.spec.BasicProperties()

        # Send raw data. Test would fail if an exception is raised
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body
        )

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)

    @mock.patch.object(EVMNodeDataTransformer, "_send_heartbeat")
    @mock.patch.object(EVMNodeDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_msg_not_del_exception_if_raised_by_send_hb(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having the node already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # We must initialise rabbit to the environment and parameters needed
        # by `_process_raw_data`
        self.test_data_transformer._initialise_rabbitmq()
        blocking_channel = self.test_data_transformer.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=EVM_NODE_RAW_DATA_ROUTING_KEY)
        body = json.dumps(self.raw_data_example_result)
        properties = pika.spec.BasicProperties()

        # Send raw data. Test would fail if an exception is raised
        self.test_data_transformer._process_raw_data(
            blocking_channel, method, properties, body
        )

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(1, mock_ack.call_count)
