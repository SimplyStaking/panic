import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from queue import Queue
from unittest import mock

import pika

from src.data_store.redis import RedisApi, Keys
from src.data_transformers.system import (SystemDataTransformer,
                                          _SYSTEM_DT_INPUT_QUEUE,
                                          _SYSTEM_DT_INPUT_ROUTING_KEY)
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.system import System
from src.utils import env
from src.utils.constants import (HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE,
                                 STORE_EXCHANGE, ALERT_EXCHANGE)
from src.utils.exceptions import (PANICException, SystemIsDownException,
                                  ReceivedUnexpectedDataException)
from src.utils.types import convert_to_float_if_not_none


class TestSystemDataTransformer(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = 'localhost'
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.redis_db = env.REDIS_TEST_DB
        self.redis_host = 'localhost'
        self.redis_host = env.REDIS_IP
        self.redis_port = env.REDIS_PORT
        self.redis_namespace = env.UNIQUE_ALERTER_IDENTIFIER
        self.redis = RedisApi(self.dummy_logger, self.redis_db,
                              self.redis_host, self.redis_port, '',
                              self.redis_namespace,
                              self.connection_check_time_interval)
        self.transformer_name = 'test_system_data_transformer'
        self.max_queue_size = 1000
        self.test_system_name = 'test_system'
        self.test_system_id = 'test_system_id345834t8h3r5893h8'
        self.test_system_parent_id = 'test_system_parent_id34978gt63gtg'
        self.test_system = System(self.test_system_name, self.test_system_id,
                                  self.test_system_parent_id)
        self.test_data_str = 'test_data'
        self.test_state = {self.test_system_id: self.test_system}
        self.test_publishing_queue = Queue(self.max_queue_size)
        self.test_rabbit_queue_name = 'Test Queue'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.test_system_is_down_exception = SystemIsDownException(
            self.test_system.system_name)
        self.test_exception = PANICException('test_exception', 1)
        self.test_went_down_at = None
        self.test_process_cpu_seconds_total = 100
        self.test_process_memory_usage = 95
        self.test_virtual_memory_usage = 678998
        self.test_open_file_descriptors = 4
        self.test_system_cpu_usage = 50
        self.test_system_ram_usage = None
        self.test_system_storage_usage = 49
        self.test_network_transmit_bytes_per_second = 456546
        self.test_network_transmit_bytes_total = 45363635635
        self.test_network_receive_bytes_per_second = 345
        self.test_network_receive_bytes_total = 4564567
        self.test_disk_io_time_seconds_in_interval = 45
        self.test_disk_io_time_seconds_total = 6347
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()

        # Set system values
        self.test_system.set_went_down_at(self.test_went_down_at)
        self.test_system.set_process_cpu_seconds_total(
            self.test_process_cpu_seconds_total)
        self.test_system.set_process_memory_usage(
            self.test_process_memory_usage)
        self.test_system.set_virtual_memory_usage(
            self.test_virtual_memory_usage)
        self.test_system.set_open_file_descriptors(
            self.test_open_file_descriptors)
        self.test_system.set_system_cpu_usage(self.test_system_cpu_usage)
        self.test_system.set_system_ram_usage(self.test_system_ram_usage)
        self.test_system.set_system_storage_usage(
            self.test_system_storage_usage)
        self.test_system.set_network_transmit_bytes_per_second(
            self.test_network_transmit_bytes_per_second)
        self.test_system.set_network_transmit_bytes_total(
            self.test_network_transmit_bytes_total)
        self.test_system.set_network_receive_bytes_per_second(
            self.test_network_receive_bytes_per_second)
        self.test_system.set_network_receive_bytes_total(
            self.test_network_receive_bytes_total)
        self.test_system.set_disk_io_time_seconds_in_interval(
            self.test_disk_io_time_seconds_in_interval)
        self.test_system.set_disk_io_time_seconds_total(
            self.test_disk_io_time_seconds_total)
        self.test_system.set_last_monitored(self.test_last_monitored)

        self.raw_data_example_result = {
            'result': {
                'meta_data': {
                    'monitor_name': 'test_monitor',
                    'system_name': self.test_system.system_name,
                    'system_id': self.test_system.system_id,
                    'system_parent_id': self.test_system.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'data': {
                    'process_cpu_seconds_total': 2786.82,
                    'process_memory_usage': 56,
                    'virtual_memory_usage': 118513664.0,
                    'open_file_descriptors': 0.78125,
                    'system_cpu_usage': 7.85,
                    'system_ram_usage': 34.09,
                    'system_storage_usage': 44.37,
                    'network_transmit_bytes_total': 1011572205557.0,
                    'network_receive_bytes_total': 722359147027.0,
                    'disk_io_time_seconds_total': 76647.0,
                },
            }
        }
        self.raw_data_example_general_error = {
            'error': {
                'meta_data': {
                    'monitor_name': 'test_monitor',
                    'system_name': self.test_system.system_name,
                    'system_id': self.test_system.system_id,
                    'system_parent_id': self.test_system.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        self.raw_data_example_downtime_error = {
            'error': {
                'meta_data': {
                    'monitor_name': 'test_monitor',
                    'system_name': self.test_system.system_name,
                    'system_id': self.test_system.system_id,
                    'system_parent_id': self.test_system.parent_id,
                    'time': datetime(2012, 1, 1).timestamp()
                },
                'message': self.test_system_is_down_exception.message,
                'code': self.test_system_is_down_exception.code,
            }
        }
        self.transformed_data_example_result = {
            'result': {
                'meta_data': {
                    'system_name': self.test_system.system_name,
                    'system_id': self.test_system.system_id,
                    'system_parent_id': self.test_system.parent_id,
                    'last_monitored': datetime(2012, 1, 1).timestamp() + 60
                },
                'data': {
                    'process_cpu_seconds_total': 2786.82,
                    'process_memory_usage': 56,
                    'virtual_memory_usage': 118513664.0,
                    'open_file_descriptors': 0.78125,
                    'system_cpu_usage': 7.85,
                    'system_ram_usage': 34.09,
                    'system_storage_usage': 44.37,
                    'network_transmit_bytes_total': 1011572205557.0,
                    'network_receive_bytes_total': 722359147027.0,
                    'disk_io_time_seconds_total': 76647.0,
                    'went_down_at': None,
                    'network_transmit_bytes_per_second': 16103476165.36667,
                    'network_receive_bytes_per_second': 12039243041.0,
                    'disk_io_time_seconds_in_interval': 70300,
                },
            }
        }
        self.transformed_data_example_general_error = {
            'error': {
                'meta_data': {
                    'system_name': self.test_system.system_name,
                    'system_id': self.test_system.system_id,
                    'system_parent_id': self.test_system.parent_id,
                    'time': datetime(2012, 1, 1).timestamp() + 60
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        self.transformed_data_example_downtime_error = {
            'error': {
                'meta_data': {
                    'system_name': self.test_system.system_name,
                    'system_id': self.test_system.system_id,
                    'system_parent_id': self.test_system.parent_id,
                    'time': datetime(2012, 1, 1).timestamp() + 60
                },
                'message': self.test_system_is_down_exception.message,
                'code': self.test_system_is_down_exception.code,
                'data': {'went_down_at': datetime(2012, 1, 1).timestamp() + 60}
            }
        }
        self.test_system_new_metrics = System(self.test_system_name,
                                              self.test_system_id,
                                              self.test_system_parent_id)
        self.test_system_new_metrics.set_went_down_at(None)
        self.test_system_new_metrics.set_process_cpu_seconds_total(2786.82)
        self.test_system_new_metrics.set_process_memory_usage(56)
        self.test_system_new_metrics.set_virtual_memory_usage(118513664.0)
        self.test_system_new_metrics.set_open_file_descriptors(0.78125)
        self.test_system_new_metrics.set_system_cpu_usage(7.85)
        self.test_system_new_metrics.set_system_ram_usage(34.09)
        self.test_system_new_metrics.set_system_storage_usage(44.37)
        self.test_system_new_metrics.set_network_transmit_bytes_per_second(
            16103476165.36667)
        self.test_system_new_metrics.set_network_transmit_bytes_total(
            1011572205557.0)
        self.test_system_new_metrics.set_network_receive_bytes_per_second(
            12039243041.0)
        self.test_system_new_metrics.set_network_receive_bytes_total(
            722359147027.0)
        self.test_system_new_metrics.set_disk_io_time_seconds_in_interval(70300)
        self.test_system_new_metrics.set_disk_io_time_seconds_total(76647.0)
        self.test_system_new_metrics.set_last_monitored(
            datetime(2012, 1, 1).timestamp() + 60)

        self.test_data_transformer = SystemDataTransformer(
            self.transformer_name, self.dummy_logger, self.redis, self.rabbitmq,
            self.max_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_data_transformer.rabbitmq.connect()

            # Declare them before just in case there are tests which do not
            # use these queues and exchanges
            self.test_data_transformer.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.test_data_transformer.rabbitmq.queue_declare(
                _SYSTEM_DT_INPUT_QUEUE, False, True, False, False)
            self.test_data_transformer.rabbitmq.exchange_declare(
                RAW_DATA_EXCHANGE, 'direct', False, True, False, False)
            self.test_data_transformer.rabbitmq.exchange_declare(
                STORE_EXCHANGE, 'direct', False, True, False, False)
            self.test_data_transformer.rabbitmq.exchange_declare(
                ALERT_EXCHANGE, 'topic', False, True, False, False)
            self.test_data_transformer.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, 'topic', False, True, False, False)

            self.test_data_transformer.rabbitmq.queue_purge(
                self.test_rabbit_queue_name)
            self.test_data_transformer.rabbitmq.queue_purge(
                _SYSTEM_DT_INPUT_QUEUE)
            self.test_data_transformer.rabbitmq.queue_delete(
                self.test_rabbit_queue_name)
            self.test_data_transformer.rabbitmq.queue_delete(
                _SYSTEM_DT_INPUT_QUEUE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                RAW_DATA_EXCHANGE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                STORE_EXCHANGE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                ALERT_EXCHANGE)
            self.test_data_transformer.rabbitmq.disconnect()
        except Exception as e:
            print("Deletion of queues and exchanges failed: {}".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.test_system_is_down_exception = None
        self.test_exception = None
        self.redis = None
        self.test_system = None
        self.test_system_new_metrics = None
        self.test_state = None
        self.test_publishing_queue = None
        self.test_data_transformer = None

    def test_str_returns_transformer_name(self) -> None:
        self.assertEqual(self.transformer_name, str(self.test_data_transformer))

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
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges and queues have not already been
            # declared
            self.rabbitmq.connect()
            self.test_data_transformer.rabbitmq.queue_delete(
                _SYSTEM_DT_INPUT_QUEUE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                HEALTH_CHECK_EXCHANGE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                RAW_DATA_EXCHANGE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                STORE_EXCHANGE)
            self.test_data_transformer.rabbitmq.exchange_delete(
                ALERT_EXCHANGE)
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

            # Check whether the consuming exchanges and queues have been
            # creating by sending messages with the same routing keys as for the
            # bindings. We will also check if the size of the queues is 0 to
            # confirm that basic_consume was called (it will store the msg in
            # the component memory immediately). If one of the exchanges or
            # queues is not created or basic_consume is not called, then either
            # an exception will be thrown or the queue size would be 1
            # respectively. Note when deleting the exchanges in the beginning we
            # also released every binding, hence there are no other queue binded
            # with the same routing key to any exchange at this point.
            self.test_data_transformer.rabbitmq.basic_publish_confirm(
                exchange=RAW_DATA_EXCHANGE,
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_data_transformer.rabbitmq.queue_declare(
                _SYSTEM_DT_INPUT_QUEUE, False, True, False, False)
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones set by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_data_transformer._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_data_transformer.rabbitmq.queue_delete(
                self.test_rabbit_queue_name)

            res = self.test_data_transformer.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_data_transformer.rabbitmq.queue_bind(
                queue=self.test_rabbit_queue_name,
                exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.worker')

            self.test_data_transformer._send_heartbeat(self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_data_transformer.rabbitmq.queue_declare(
                queue=self.test_rabbit_queue_name, durable=True,
                exclusive=False, auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_data_transformer.rabbitmq.basic_get(
                self.test_rabbit_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_save_to_redis_saves_system_to_redis_correctly(self) -> None:
        # Clean test db
        self.redis.delete_all()

        self.test_data_transformer.save_to_redis(self.test_system)

        redis_hash = Keys.get_hash_parent(self.test_system.parent_id)
        system_id = self.test_system.system_id
        actual_went_down_at = convert_to_float_if_not_none(self.redis.hget(
            redis_hash, Keys.get_system_went_down_at(system_id)), None)
        actual_process_cpu_seconds_total = convert_to_float_if_not_none(
            self.redis.hget(
                redis_hash,
                Keys.get_system_process_cpu_seconds_total(system_id)), None)
        actual_process_memory_usage = convert_to_float_if_not_none(
            self.redis.hget(redis_hash,
                            Keys.get_system_process_memory_usage(system_id)),
            None)
        actual_virtual_memory_usage = convert_to_float_if_not_none(
            self.redis.hget(redis_hash,
                            Keys.get_system_virtual_memory_usage(system_id)),
            None)
        actual_open_file_descriptors = convert_to_float_if_not_none(
            self.redis.hget(redis_hash,
                            Keys.get_system_open_file_descriptors(system_id)),
            None)
        actual_system_cpu_usage = convert_to_float_if_not_none(self.redis.hget(
            redis_hash, Keys.get_system_system_cpu_usage(system_id)), None)
        actual_system_ram_usage = convert_to_float_if_not_none(self.redis.hget(
            redis_hash, Keys.get_system_system_ram_usage(system_id)), None)
        actual_system_storage_usage = convert_to_float_if_not_none(
            self.redis.hget(redis_hash,
                            Keys.get_system_system_storage_usage(system_id)),
            None)
        actual_network_transmit_bytes_per_second = convert_to_float_if_not_none(
            self.redis.hget(
                redis_hash, Keys.get_system_network_transmit_bytes_per_second(
                    system_id)), None)
        actual_network_transmit_bytes_total = convert_to_float_if_not_none(
            self.redis.hget(
                redis_hash,
                Keys.get_system_network_transmit_bytes_total(system_id)), None)
        actual_network_receive_bytes_per_second = convert_to_float_if_not_none(
            self.redis.hget(
                redis_hash, Keys.get_system_network_receive_bytes_per_second(
                    system_id)), None)
        actual_network_receive_bytes_total = convert_to_float_if_not_none(
            self.redis.hget(
                redis_hash,
                Keys.get_system_network_receive_bytes_total(system_id)), None)
        actual_disk_io_time_seconds_in_interval = convert_to_float_if_not_none(
            self.redis.hget(
                redis_hash,
                Keys.get_system_disk_io_time_seconds_in_interval(system_id)),
            None)
        actual_disk_io_time_seconds_total = convert_to_float_if_not_none(
            self.redis.hget(
                redis_hash,
                Keys.get_system_disk_io_time_seconds_total(system_id)), None)
        actual_last_monitored = convert_to_float_if_not_none(self.redis.hget(
            redis_hash, Keys.get_system_last_monitored(system_id)), None)

        self.assertEqual(actual_went_down_at, self.test_system.went_down_at)
        self.assertEqual(actual_process_cpu_seconds_total,
                         self.test_system.process_cpu_seconds_total)
        self.assertEqual(actual_process_memory_usage,
                         self.test_system.process_memory_usage)
        self.assertEqual(actual_virtual_memory_usage,
                         self.test_system.virtual_memory_usage)
        self.assertEqual(actual_open_file_descriptors,
                         self.test_system.open_file_descriptors)
        self.assertEqual(actual_system_cpu_usage,
                         self.test_system.system_cpu_usage)
        self.assertEqual(actual_system_ram_usage,
                         self.test_system.system_ram_usage)
        self.assertEqual(actual_system_storage_usage,
                         self.test_system.system_storage_usage)
        self.assertEqual(actual_network_transmit_bytes_per_second,
                         self.test_system.network_transmit_bytes_per_second)
        self.assertEqual(actual_network_transmit_bytes_total,
                         self.test_system.network_transmit_bytes_total)
        self.assertEqual(actual_network_receive_bytes_per_second,
                         self.test_system.network_receive_bytes_per_second)
        self.assertEqual(actual_network_receive_bytes_total,
                         self.test_system.network_receive_bytes_total)
        self.assertEqual(actual_disk_io_time_seconds_in_interval,
                         self.test_system.disk_io_time_seconds_in_interval)
        self.assertEqual(actual_disk_io_time_seconds_total,
                         self.test_system.disk_io_time_seconds_total)
        self.assertEqual(actual_last_monitored, self.test_system.last_monitored)

    def test_load_state_successful_if_state_exists_in_redis_and_redis_online(
            self) -> None:
        # Save state to Redis first
        self.test_data_transformer.save_to_redis(self.test_system)

        # Reset system to default values
        self.test_system.reset()

        # Load state
        loaded_system = self.test_data_transformer.load_state(self.test_system)

        self.assertEqual(self.test_went_down_at, loaded_system.went_down_at)
        self.assertEqual(self.test_process_cpu_seconds_total,
                         loaded_system.process_cpu_seconds_total)
        self.assertEqual(self.test_process_memory_usage,
                         loaded_system.process_memory_usage)
        self.assertEqual(self.test_virtual_memory_usage,
                         loaded_system.virtual_memory_usage)
        self.assertEqual(self.test_open_file_descriptors,
                         loaded_system.open_file_descriptors)
        self.assertEqual(self.test_system_cpu_usage,
                         loaded_system.system_cpu_usage)
        self.assertEqual(self.test_system_ram_usage,
                         loaded_system.system_ram_usage)
        self.assertEqual(self.test_system_storage_usage,
                         loaded_system.system_storage_usage)
        self.assertEqual(self.test_network_transmit_bytes_per_second,
                         loaded_system.network_transmit_bytes_per_second)
        self.assertEqual(self.test_network_transmit_bytes_total,
                         loaded_system.network_transmit_bytes_total)
        self.assertEqual(self.test_network_receive_bytes_per_second,
                         loaded_system.network_receive_bytes_per_second)
        self.assertEqual(self.test_network_receive_bytes_total,
                         loaded_system.network_receive_bytes_total)
        self.assertEqual(self.test_disk_io_time_seconds_in_interval,
                         loaded_system.disk_io_time_seconds_in_interval)
        self.assertEqual(self.test_disk_io_time_seconds_total,
                         loaded_system.disk_io_time_seconds_total)
        self.assertEqual(self.test_last_monitored, loaded_system.last_monitored)

    def test_load_state_keeps_same_state_if_state_in_redis_and_redis_offline(
            self) -> None:
        # Save state to Redis first
        self.test_data_transformer.save_to_redis(self.test_system)

        # Reset system to default values
        self.test_system.reset()

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if the system is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Load state
        loaded_system = self.test_data_transformer.load_state(self.test_system)

        self.assertEqual(None, loaded_system.went_down_at)
        self.assertEqual(None, loaded_system.process_cpu_seconds_total)
        self.assertEqual(None, loaded_system.process_memory_usage)
        self.assertEqual(None, loaded_system.virtual_memory_usage)
        self.assertEqual(None, loaded_system.open_file_descriptors)
        self.assertEqual(None, loaded_system.system_cpu_usage)
        self.assertEqual(None, loaded_system.system_ram_usage)
        self.assertEqual(None, loaded_system.system_storage_usage)
        self.assertEqual(None, loaded_system.network_transmit_bytes_per_second)
        self.assertEqual(None, loaded_system.network_transmit_bytes_total)
        self.assertEqual(None, loaded_system.network_receive_bytes_per_second)
        self.assertEqual(None, loaded_system.network_receive_bytes_total)
        self.assertEqual(None, loaded_system.disk_io_time_seconds_in_interval)
        self.assertEqual(None, loaded_system.disk_io_time_seconds_total)
        self.assertEqual(None, loaded_system.last_monitored)

    def test_load_state_keeps_same_state_if_state_not_in_redis_and_redis_online(
            self) -> None:
        # Clean test db
        self.redis.delete_all()

        # Set the _do_not_use_if_recently_went_down function to return True
        # as if the system is down
        self.test_data_transformer.redis._do_not_use_if_recently_went_down = \
            lambda: True

        # Load state
        loaded_system = self.test_data_transformer.load_state(self.test_system)

        self.assertEqual(self.test_went_down_at, loaded_system.went_down_at)
        self.assertEqual(self.test_process_cpu_seconds_total,
                         loaded_system.process_cpu_seconds_total)
        self.assertEqual(self.test_process_memory_usage,
                         loaded_system.process_memory_usage)
        self.assertEqual(self.test_virtual_memory_usage,
                         loaded_system.virtual_memory_usage)
        self.assertEqual(self.test_open_file_descriptors,
                         loaded_system.open_file_descriptors)
        self.assertEqual(self.test_system_cpu_usage,
                         loaded_system.system_cpu_usage)
        self.assertEqual(self.test_system_ram_usage,
                         loaded_system.system_ram_usage)
        self.assertEqual(self.test_system_storage_usage,
                         loaded_system.system_storage_usage)
        self.assertEqual(self.test_network_transmit_bytes_per_second,
                         loaded_system.network_transmit_bytes_per_second)
        self.assertEqual(self.test_network_transmit_bytes_total,
                         loaded_system.network_transmit_bytes_total)
        self.assertEqual(self.test_network_receive_bytes_per_second,
                         loaded_system.network_receive_bytes_per_second)
        self.assertEqual(self.test_network_receive_bytes_total,
                         loaded_system.network_receive_bytes_total)
        self.assertEqual(self.test_disk_io_time_seconds_in_interval,
                         loaded_system.disk_io_time_seconds_in_interval)
        self.assertEqual(self.test_disk_io_time_seconds_total,
                         loaded_system.disk_io_time_seconds_total)
        self.assertEqual(self.test_last_monitored, loaded_system.last_monitored)

    def test_load_state_keeps_same_state_if_state_not_in_redis_and_redis_off(
            self) -> None:
        # Clean test db
        self.redis.delete_all()

        # Load state
        loaded_system = self.test_data_transformer.load_state(self.test_system)

        self.assertEqual(self.test_went_down_at, loaded_system.went_down_at)
        self.assertEqual(self.test_process_cpu_seconds_total,
                         loaded_system.process_cpu_seconds_total)
        self.assertEqual(self.test_process_memory_usage,
                         loaded_system.process_memory_usage)
        self.assertEqual(self.test_virtual_memory_usage,
                         loaded_system.virtual_memory_usage)
        self.assertEqual(self.test_open_file_descriptors,
                         loaded_system.open_file_descriptors)
        self.assertEqual(self.test_system_cpu_usage,
                         loaded_system.system_cpu_usage)
        self.assertEqual(self.test_system_ram_usage,
                         loaded_system.system_ram_usage)
        self.assertEqual(self.test_system_storage_usage,
                         loaded_system.system_storage_usage)
        self.assertEqual(self.test_network_transmit_bytes_per_second,
                         loaded_system.network_transmit_bytes_per_second)
        self.assertEqual(self.test_network_transmit_bytes_total,
                         loaded_system.network_transmit_bytes_total)
        self.assertEqual(self.test_network_receive_bytes_per_second,
                         loaded_system.network_receive_bytes_per_second)
        self.assertEqual(self.test_network_receive_bytes_total,
                         loaded_system.network_receive_bytes_total)
        self.assertEqual(self.test_disk_io_time_seconds_in_interval,
                         loaded_system.disk_io_time_seconds_in_interval)
        self.assertEqual(self.test_disk_io_time_seconds_total,
                         loaded_system.disk_io_time_seconds_total)
        self.assertEqual(self.test_last_monitored, loaded_system.last_monitored)

    def test_update_state_raises_unexpected_data_exception_if_no_result_or_err(
            self) -> None:
        invalid_transformed_data = {'bad_key': 'bad_value'}
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._update_state,
                          invalid_transformed_data)

    def test_update_state_leaves_same_state_if_no_result_or_err_in_trans_data(
            self) -> None:
        invalid_transformed_data = {'bad_key': 'bad_value'}
        self.test_data_transformer._state = self.test_state
        expected_state = copy.deepcopy(self.test_state)

        # First confirm that an exception is still raised
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._update_state,
                          invalid_transformed_data)

        # Check that there are the same keys in the state
        self.assertEqual(expected_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the stored system state has the same variable values. This
        # must be done separately as otherwise the object's low level address
        # will be compared
        for system_id in expected_state.keys():
            self.assertDictEqual(
                expected_state[system_id].__dict__,
                self.test_data_transformer.state[system_id].__dict__)

    def test_update_state_raise_key_error_exception_if_keys_do_not_exist_result(
            self) -> None:
        invalid_transformed_data = copy.deepcopy(
            self.transformed_data_example_result)
        del invalid_transformed_data['result']['data']
        self.test_data_transformer._state = self.test_state

        # First confirm that an exception is still raised
        self.assertRaises(KeyError, self.test_data_transformer._update_state,
                          invalid_transformed_data)

    def test_update_state_raises_key_error_exception_if_keys_do_not_exist_error(
            self) -> None:
        invalid_transformed_data = copy.deepcopy(
            self.transformed_data_example_downtime_error)
        del invalid_transformed_data['error']['data']
        self.test_data_transformer._state = self.test_state

        # First confirm that an exception is still raised
        self.assertRaises(KeyError, self.test_data_transformer._update_state,
                          invalid_transformed_data)

    def test_update_state_updates_state_correctly_on_result_data(self) -> None:
        self.test_data_transformer._state = self.test_state
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        old_state = copy.deepcopy(self.test_data_transformer._state)

        self.test_data_transformer._update_state(
            self.transformed_data_example_result)

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the systems not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        # Check that the system's state values have been modified to the new
        # metrics
        self.assertDictEqual(
            self.test_system_new_metrics.__dict__,
            self.test_data_transformer._state[self.test_system_id].__dict__)

        # Check that the system is marked as up
        self.assertFalse(
            self.test_data_transformer._state[self.test_system_id].is_down)

    def test_update_state_updates_state_correctly_on_error_data_general_except(
            self) -> None:
        self.test_data_transformer._state = self.test_state
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        old_state = copy.deepcopy(self.test_data_transformer._state)

        self.test_data_transformer._update_state(
            self.transformed_data_example_general_error)

        # Check that there are the same keys in the state
        self.assertEqual(old_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the systems not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        # Check that the system's state values have not been changed. When there
        # are general exceptions, the state doesn't need to change
        self.assertDictEqual(
            old_state[self.test_system_id].__dict__,
            self.test_data_transformer._state[self.test_system_id].__dict__)

        # Check that the system is still up
        self.assertFalse(
            self.test_data_transformer._state[self.test_system_id].is_down)

    def test_update_state_updates_state_correctly_on_error_data_downtime_except(
            self) -> None:
        self.test_data_transformer._state = self.test_state
        self.test_data_transformer._state['dummy_id'] = self.test_data_str
        expected_state = copy.deepcopy(self.test_data_transformer._state)
        expected_state[self.test_system_id].set_went_down_at(
            self.transformed_data_example_downtime_error['error']['data'][
                'went_down_at']
        )

        self.test_data_transformer._update_state(
            self.transformed_data_example_downtime_error)

        # Check that there are the same keys in the state
        self.assertEqual(expected_state.keys(),
                         self.test_data_transformer.state.keys())

        # Check that the systems not in question are not modified
        self.assertEqual(self.test_data_str,
                         self.test_data_transformer._state['dummy_id'])

        # Check that the system's state values have been changed to the latest
        # metrics
        self.assertDictEqual(
            expected_state[self.test_system_id].__dict__,
            self.test_data_transformer._state[self.test_system_id].__dict__)

        # Check that the system is marked as down
        self.assertTrue(
            self.test_data_transformer._state[self.test_system_id].is_down)

# todo: change comment in component and env.variables commented here
# todo: noticed that i am not saving to redis when processing raw data. This
#     : should be done.
# TODO: Must save github state in redis as well
