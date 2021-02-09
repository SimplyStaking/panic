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
                                  ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from src.utils.types import convert_to_float_if_not_none


class TestSystemDataTransformer(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.redis_db = env.REDIS_TEST_DB
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
        self.test_network_transmit_bytes_total = 45363635633
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
                    'time': datetime(2012, 1, 1).timestamp() + 60
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
                    'time': datetime(2012, 1, 1).timestamp() + 60
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
                    'time': datetime(2012, 1, 1).timestamp() + 60
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
                    'network_transmit_bytes_per_second': 16103476165.4,
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
            16103476165.4)
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

        meta_data_for_alerting_result = \
            self.transformed_data_example_result['result']['meta_data']
        self.test_data_for_alerting_result = {
            'result': {
                'meta_data': meta_data_for_alerting_result,
                'data': {
                    'process_cpu_seconds_total': {
                        'current':
                            self.test_system_new_metrics
                                .process_cpu_seconds_total,
                        'previous': self.test_system.process_cpu_seconds_total,
                    },
                    'process_memory_usage': {
                        'current':
                            self.test_system_new_metrics.process_memory_usage,
                        'previous': self.test_system.process_memory_usage,
                    },
                    'virtual_memory_usage': {
                        'current':
                            self.test_system_new_metrics.virtual_memory_usage,
                        'previous': self.test_system.virtual_memory_usage,
                    },
                    'open_file_descriptors': {
                        'current':
                            self.test_system_new_metrics.open_file_descriptors,
                        'previous': self.test_system.open_file_descriptors,
                    },
                    'system_cpu_usage': {
                        'current':
                            self.test_system_new_metrics.system_cpu_usage,
                        'previous': self.test_system.system_cpu_usage,
                    },
                    'system_ram_usage': {
                        'current':
                            self.test_system_new_metrics.system_ram_usage,
                        'previous': self.test_system.system_ram_usage,
                    },
                    'system_storage_usage': {
                        'current':
                            self.test_system_new_metrics.system_storage_usage,
                        'previous': self.test_system.system_storage_usage,
                    },
                    'network_receive_bytes_total': {
                        'current':
                            self.test_system_new_metrics
                                .network_receive_bytes_total,
                        'previous': self.test_system
                            .network_receive_bytes_total,
                    },
                    'network_transmit_bytes_total': {
                        'current':
                            self.test_system_new_metrics
                                .network_transmit_bytes_total,
                        'previous': self.test_system
                            .network_transmit_bytes_total,
                    },
                    'disk_io_time_seconds_total': {
                        'current':
                            self.test_system_new_metrics
                                .disk_io_time_seconds_total,
                        'previous': self.test_system.disk_io_time_seconds_total,
                    },
                    'network_transmit_bytes_per_second': {
                        'current':
                            self.test_system_new_metrics
                                .network_transmit_bytes_per_second,
                        'previous': self.test_system
                            .network_transmit_bytes_per_second,
                    },
                    'network_receive_bytes_per_second': {
                        'current':
                            self.test_system_new_metrics
                                .network_receive_bytes_per_second,
                        'previous': self.test_system
                            .network_receive_bytes_per_second,
                    },
                    'disk_io_time_seconds_in_interval': {
                        'current':
                            self.test_system_new_metrics
                                .disk_io_time_seconds_in_interval,
                        'previous': self.test_system
                            .disk_io_time_seconds_in_interval,
                    },
                    'went_down_at': {
                        'current': self.test_system_new_metrics.went_down_at,
                        'previous': self.test_system.went_down_at,
                    }
                }
            }
        }
        meta_data_for_alerting_down_err = \
            self.transformed_data_example_downtime_error['error']['meta_data']
        down_error_msg = self.test_system_is_down_exception.message
        down_error_code = self.test_system_is_down_exception.code
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
                        'previous': self.test_system.went_down_at,
                    }
                }
            }
        }
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

        self.test_data_transformer._save_to_redis(self.test_system)

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
        self.test_data_transformer._save_to_redis(self.test_system)

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
        self.test_data_transformer._save_to_redis(self.test_system)

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
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
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
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # First confirm that an exception is still raised
        self.assertRaises(KeyError, self.test_data_transformer._update_state,
                          invalid_transformed_data)

    def test_update_state_raises_key_error_exception_if_keys_do_not_exist_error(
            self) -> None:
        invalid_transformed_data = copy.deepcopy(
            self.transformed_data_example_downtime_error)
        del invalid_transformed_data['error']['data']
        self.test_data_transformer._state = copy.deepcopy(self.test_state)

        # First confirm that an exception is still raised
        self.assertRaises(KeyError, self.test_data_transformer._update_state,
                          invalid_transformed_data)

    def test_update_state_updates_state_correctly_on_result_data(self) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
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
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
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
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
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

    def test_process_transformed_data_for_saving_returns_trans_data_if_result(
            self) -> None:
        processed_data = \
            self.test_data_transformer._process_transformed_data_for_saving(
                self.transformed_data_example_result)
        self.assertDictEqual(self.transformed_data_example_result,
                             processed_data)

    def test_process_transformed_data_for_saving_returns_trans_data_if_error(
            self) -> None:
        processed_data = \
            self.test_data_transformer._process_transformed_data_for_saving(
                self.transformed_data_example_general_error)
        self.assertDictEqual(self.transformed_data_example_general_error,
                             processed_data)

    def test_proc_trans_data_for_saving_raises_unexp_data_except_on_unexp_data(
            self) -> None:
        invalid_transformed_data = {'bad_key': 'bad_value'}
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_saving,
            invalid_transformed_data)

    def test_process_trans_data_for_alerting_returns_expected_data_if_result(
            self) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        actual_data = \
            self.test_data_transformer._process_transformed_data_for_alerting(
                self.transformed_data_example_result)
        self.assertDictEqual(self.test_data_for_alerting_result, actual_data)

    def test_process_trans_data_for_alerting_returns_trans_data_if_non_down_err(
            self) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        actual_data = \
            self.test_data_transformer._process_transformed_data_for_alerting(
                self.transformed_data_example_general_error)
        self.assertDictEqual(self.transformed_data_example_general_error,
                             actual_data)

    def test_process_trans_data_for_alerting_returns_expected_data_if_down_err(
            self) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        actual_data = \
            self.test_data_transformer._process_transformed_data_for_alerting(
                self.transformed_data_example_downtime_error)
        self.assertDictEqual(self.test_data_for_alerting_down_error,
                             actual_data)

    def test_proc_trans_data_for_alerting_raise_unex_data_except_on_unex_data(
            self) -> None:
        invalid_transformed_data = {'bad_key', 'bad_val'}
        self.assertRaises(
            ReceivedUnexpectedDataException,
            self.test_data_transformer._process_transformed_data_for_alerting,
            invalid_transformed_data)

    def test_proc_trans_data_for_alerting_raise_key_err_if_key_not_exist_result(
            self) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        transformed_data = copy.deepcopy(self.transformed_data_example_result)
        del transformed_data['result']['data']['process_cpu_seconds_total']
        self.assertRaises(
            KeyError,
            self.test_data_transformer._process_transformed_data_for_alerting,
            transformed_data)

    def test_proc_trans_data_for_alert_raise_key_err_if_keys_not_exist_error(
            self) -> None:
        # Test when the error is not related to downtime
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        transformed_data = copy.deepcopy(
            self.transformed_data_example_general_error)
        del transformed_data['error']['meta_data']
        self.assertRaises(
            KeyError,
            self.test_data_transformer._process_transformed_data_for_alerting,
            transformed_data)

        # Test when the error is related to downtime
        transformed_data = copy.deepcopy(
            self.transformed_data_example_downtime_error)
        del transformed_data['error']['data']['went_down_at']
        self.assertRaises(
            KeyError,
            self.test_data_transformer._process_transformed_data_for_alerting,
            transformed_data)

    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_returns_expected_data_if_result_and_first_mon_round(
            self, mock_process_for_saving, mock_process_for_alerting) -> None:
        self.test_data_transformer._state = self.test_state
        self.test_system.reset()
        mock_process_for_saving.return_value = {'key_1': 'val1'}
        mock_process_for_alerting.return_value = {'key_2': 'val2'}

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(
                self.raw_data_example_result)

        # Set metrics which need more than 1 monitoring round to be computed
        # to None.
        expected_trans_data = copy.deepcopy(
            self.transformed_data_example_result)
        expected_trans_data['result']['data'][
            'network_transmit_bytes_per_second'] = None
        expected_trans_data['result']['data'][
            'network_receive_bytes_per_second'] = None
        expected_trans_data['result']['data'][
            'disk_io_time_seconds_in_interval'] = None

        self.assertDictEqual(expected_trans_data, trans_data)
        self.assertDictEqual({'key_2': 'val2'}, data_for_alerting)
        self.assertDictEqual({'key_1': 'val1'}, data_for_saving)

    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_ret_expected_data_if_result_and_second_mon_round(
            self, mock_process_for_saving, mock_process_for_alerting) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        mock_process_for_saving.return_value = {'key_1': 'val1'}
        mock_process_for_alerting.return_value = {'key_2': 'val2'}

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(
                self.raw_data_example_result)

        self.assertDictEqual(self.transformed_data_example_result, trans_data)
        self.assertDictEqual({'key_2': 'val2'}, data_for_alerting)
        self.assertDictEqual({'key_1': 'val1'}, data_for_saving)

    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_returns_expected_data_if_non_down_error(
            self, mock_process_for_saving, mock_process_for_alerting) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        mock_process_for_saving.return_value = {'key_1': 'val1'}
        mock_process_for_alerting.return_value = {'key_2': 'val2'}

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(
                self.raw_data_example_general_error)

        self.assertDictEqual(self.transformed_data_example_general_error,
                             trans_data)
        self.assertDictEqual({'key_2': 'val2'}, data_for_alerting)
        self.assertDictEqual({'key_1': 'val1'}, data_for_saving)

    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_alerting")
    @mock.patch.object(SystemDataTransformer,
                       "_process_transformed_data_for_saving")
    def test_transform_data_returns_expected_data_if_down_error(
            self, mock_process_for_saving, mock_process_for_alerting) -> None:
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        mock_process_for_saving.return_value = {'key_1': 'val1'}
        mock_process_for_alerting.return_value = {'key_2': 'val2'}

        trans_data, data_for_alerting, data_for_saving = \
            self.test_data_transformer._transform_data(
                self.raw_data_example_downtime_error)

        self.assertDictEqual(self.transformed_data_example_downtime_error,
                             trans_data)
        self.assertDictEqual({'key_2': 'val2'}, data_for_alerting)
        self.assertDictEqual({'key_1': 'val1'}, data_for_saving)

    def test_transform_data_raises_unexpected_data_exception_on_unexpected_data(
            self) -> None:
        invalid_transformed_data = {'bad_key': 'bad_value'}
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_data_transformer._transform_data,
                          invalid_transformed_data)

    def test_transform_data_raises_key_error_if_key_does_not_exist_result(
            self) -> None:
        # Test for non first monitoring round data
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        raw_data = copy.deepcopy(self.raw_data_example_result)
        del raw_data['result']['meta_data']['time']
        self.assertRaises(KeyError, self.test_data_transformer._transform_data,
                          raw_data)

        # Test for first monitoring round data
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        self.test_system.reset()
        raw_data = copy.deepcopy(self.raw_data_example_result)
        del raw_data['result']['meta_data']['time']
        self.assertRaises(KeyError, self.test_data_transformer._transform_data,
                          raw_data)

    def test_transform_data_raises_key_error_if_key_does_not_exist_error(
            self) -> None:
        # Test when the error is not related to downtime
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        raw_data = copy.deepcopy(self.raw_data_example_general_error)
        del raw_data['error']['meta_data']
        self.assertRaises(KeyError, self.test_data_transformer._transform_data,
                          raw_data)

        # Test when the error is related to downtime
        raw_data = copy.deepcopy(self.raw_data_example_downtime_error)
        del raw_data['error']['meta_data']
        self.assertRaises(KeyError, self.test_data_transformer._transform_data,
                          raw_data)

    def test_place_latest_data_on_queue_places_the_correct_data_on_queue_result(
            self) -> None:
        data_for_saving = copy.deepcopy(self.transformed_data_example_result)
        self.test_data_transformer._place_latest_data_on_queue(
            self.transformed_data_example_result,
            self.test_data_for_alerting_result,
            data_for_saving
        )
        expected_data_for_alerting = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': 'alerter.system.{}'.format(
                self.test_system_parent_id),
            'data': self.test_data_for_alerting_result,
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_for_saving = {
            'exchange': STORE_EXCHANGE,
            'routing_key': 'system',
            'data': data_for_saving,
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

    def test_place_latest_data_on_queue_places_the_correct_data_on_queue_error(
            self) -> None:
        data_for_alerting = data_for_saving = copy.deepcopy(
            self.transformed_data_example_general_error)
        self.test_data_transformer._place_latest_data_on_queue(
            self.transformed_data_example_general_error, data_for_alerting,
            data_for_saving
        )
        expected_data_for_alerting = {
            'exchange': ALERT_EXCHANGE,
            'routing_key': 'alerter.system.{}'.format(
                self.test_system_parent_id),
            'data': data_for_alerting,
            'properties': pika.BasicProperties(delivery_mode=2),
            'mandatory': True
        }
        expected_data_for_saving = {
            'exchange': STORE_EXCHANGE,
            'routing_key': 'system',
            'data': data_for_saving,
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

    def test_place_latest_data_on_queue_raises_key_error_if_keys_missing_result(
            self) -> None:
        transformed_data = copy.deepcopy(self.transformed_data_example_result)
        del transformed_data['result']['meta_data']
        self.assertRaises(
            KeyError, self.test_data_transformer._place_latest_data_on_queue,
            transformed_data, {}, {})

    def test_place_latest_data_on_queue_raises_key_error_if_keys_missing_error(
            self) -> None:
        transformed_data = copy.deepcopy(
            self.transformed_data_example_general_error)
        del transformed_data['error']['meta_data']
        self.assertRaises(
            KeyError, self.test_data_transformer._place_latest_data_on_queue,
            transformed_data, {}, {})

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_transforms_data_if_data_valid_and_new_system(
            self, mock_ack, mock_trans_data) -> None:
        # We will check that the data is transformed by checking that
        # `_transform_data` is called correctly. The actual transformations are
        # already tested. Note we will test for both result and error.
        mock_ack.return_value = None
        mock_trans_data.return_value = (None, None, None)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)

            # To reset the state as if the system was not already added
            self.test_data_transformer._state = {}

            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            self.assertEqual(2, mock_trans_data.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_transforms_data_if_data_valid_and_system_in_state(
            self, mock_ack, mock_trans_data) -> None:
        # We will check that the data is transformed by checking that
        # `_transform_data` is called correctly. The actual transformations are
        # already tested. Note we will test for both result and error.
        mock_ack.return_value = None
        mock_trans_data.return_value = (None, None, None)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            self.test_data_transformer._state = copy.deepcopy(self.test_state)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            self.assertEqual(2, mock_trans_data.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_call_trans_data_if_err_res_not_in_data(
            self, mock_ack, mock_trans_data) -> None:
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body = json.dumps({'bad_key': 'bad_val'})
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)

            mock_trans_data.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_call_trans_data_if_missing_keys_in_data(
            self, mock_ack, mock_trans_data) -> None:
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`. Here we must cater for both the error
            # and result cases.
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps({'result': {'bad_key': 'val'}})
            body_error = json.dumps({'error': {'bad_key': 'val'}})
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            mock_trans_data.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_updates_state_if_no_processing_errors_new_system(
            self, mock_ack) -> None:
        # To make sure there is no state in redis as the state must be compared.
        self.redis.delete_all()

        # We will check that the state has been updated correctly.
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Make the state non-empty to check that the update does not modify
            # systems not in question
            self.test_data_transformer._state['system2'] = self.test_data_str

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)

            # Check that there are 2 entries in the state, one which was not
            # modified, and the other having metrics the same as the newly
            # given data.
            expected_data = copy.deepcopy(self.test_system_new_metrics)
            expected_data.set_network_transmit_bytes_per_second(None)
            expected_data.set_network_receive_bytes_per_second(None)
            expected_data.set_disk_io_time_seconds_in_interval(None)
            self.assertEqual(2, len(self.test_data_transformer._state.keys()))
            self.assertEqual(self.test_data_str,
                             self.test_data_transformer._state['system2'])
            self.assertEqual(
                expected_data.__dict__,
                self.test_data_transformer._state[self.test_system_id].__dict__)

            # To reset the state as if the system was not already added
            del self.test_data_transformer._state[self.test_system_id]
            self.redis.delete_all()

            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            # Check that there are 2 entries in the state, one which was not
            # modified, and the other having metrics the same as the newly
            # given data.
            self.assertEqual(2, len(self.test_data_transformer._state.keys()))
            self.assertEqual(self.test_data_str,
                             self.test_data_transformer._state['system2'])
            expected_data = System(self.test_system_name, self.test_system_id,
                                   self.test_system_parent_id)
            self.assertEqual(
                expected_data.__dict__,
                self.test_data_transformer._state[self.test_system_id].__dict__)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_updates_state_if_no_process_errors_sys_in_state(
            self, mock_ack) -> None:
        # We will check that the state has been updated correctly.
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Define a state. Make sure the state in question is stored in
            # redis.
            self.test_data_transformer._state = copy.deepcopy(self.test_state)
            self.test_data_transformer._save_to_redis(self.test_system)
            self.test_data_transformer._state['system2'] = self.test_data_str

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)

            # Check that there are 2 entries in the state, one which was not
            # modified, and the other having metrics the same as the newly
            # given data.
            self.assertEqual(2, len(self.test_data_transformer._state.keys()))
            self.assertEqual(self.test_data_str,
                             self.test_data_transformer._state['system2'])
            self.assertEqual(
                self.test_system_new_metrics.__dict__,
                self.test_data_transformer._state[self.test_system_id].__dict__)

            # Reset state for error path
            self.test_data_transformer._state = copy.deepcopy(self.test_state)
            self.test_data_transformer._save_to_redis(self.test_system)
            self.test_data_transformer._state['system2'] = self.test_data_str

            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            # Check that there are 2 entries in the state, one which was not
            # modified, and the other having metrics the same as the newly
            # given data.
            self.assertEqual(2, len(self.test_data_transformer._state.keys()))
            self.assertEqual(self.test_data_str,
                             self.test_data_transformer._state['system2'])
            self.assertEqual(
                self.test_system.__dict__,
                self.test_data_transformer._state[self.test_system_id].__dict__)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(SystemDataTransformer, "_save_to_redis")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_saves_sys_to_redis_if_no_proc_errors_new_system(
            self, mock_ack, mock_save_to_redis, mock_trans_data) -> None:
        # We will perform this test by checking that `_save_to_redis` is called
        # correctly, as the logic of `save_to_redis` is already tested.
        mock_ack.return_value = None
        mock_trans_data.side_effect = [
            (
                self.transformed_data_example_result,
                self.test_data_for_alerting_result,
                self.transformed_data_example_result
            ),
            (
                self.transformed_data_example_downtime_error,
                self.test_data_for_alerting_down_error,
                self.transformed_data_example_downtime_error
            ),
        ]
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            args, _ = mock_save_to_redis.call_args
            self.assertDictEqual(
                self.test_data_transformer._state[self.test_system_id].__dict__,
                args[0].__dict__)
            self.assertEqual(1, len(args))

            # To reset the state as if the system was not already added
            del self.test_data_transformer._state[self.test_system_id]

            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            args, _ = mock_save_to_redis.call_args
            self.assertDictEqual(
                self.test_data_transformer._state[self.test_system_id].__dict__,
                args[0].__dict__)
            self.assertEqual(1, len(args))

            self.assertEqual(2, mock_save_to_redis.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(SystemDataTransformer, "_save_to_redis")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_saves_sys_to_redis_if_no_proc_errors_sys_in_state(
            self, mock_ack, mock_save_to_redis, mock_transform_data) -> None:
        # We will perform this test by checking that `_save_to_redis` is called
        # correctly, as the logic of `save_to_redis` is already tested.
        mock_ack.return_value = None
        mock_transform_data.side_effect = [
            (
                self.transformed_data_example_result,
                self.test_data_for_alerting_result,
                self.transformed_data_example_result
            ),
            (
                self.transformed_data_example_downtime_error,
                self.test_data_for_alerting_down_error,
                self.transformed_data_example_downtime_error
            ),
        ]
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Add the system to the state
            self.test_data_transformer._state = copy.deepcopy(self.test_state)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            args, _ = mock_save_to_redis.call_args
            self.assertDictEqual(
                self.test_data_transformer._state[self.test_system_id].__dict__,
                args[0].__dict__)
            self.assertEqual(1, len(args))

            # Reset state for second test
            self.test_data_transformer._state = copy.deepcopy(self.test_state)

            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            args, _ = mock_save_to_redis.call_args
            self.assertDictEqual(
                self.test_data_transformer._state[self.test_system_id].__dict__,
                args[0].__dict__)
            self.assertEqual(1, len(args))

            self.assertEqual(2, mock_save_to_redis.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_update_state_if_res_or_err_not_in_data(
            self, mock_ack) -> None:
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body = json.dumps({'bad_key': 'bad_val'})
            properties = pika.spec.BasicProperties()

            # Make the state non-empty and save it to redis
            self.test_data_transformer._state = copy.deepcopy(self.test_state)
            self.test_data_transformer._save_to_redis(self.test_system)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)

            # Check that there is 1 entry in the state, one which was not
            # modified.
            expected_data = copy.deepcopy(self.test_system)
            self.assertEqual(1, len(self.test_data_transformer._state.keys()))
            self.assertEqual(
                expected_data.__dict__,
                self.test_data_transformer._state[self.test_system_id].__dict__)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @mock.patch.object(SystemDataTransformer, "_save_to_redis")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_save_to_redis_if_res_or_err_not_in_data(
            self, mock_ack, mock_save_to_redis) -> None:
        # Empty Redis as it's value must be compared
        self.redis.delete_all()

        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body = json.dumps({'bad_key': 'bad_val'})
            properties = pika.spec.BasicProperties()

            # Make the state non-empty
            self.test_data_transformer._state = copy.deepcopy(self.test_state)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)

            # Check that save to redis was not called
            mock_save_to_redis.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_update_state_if_missing_keys_in_data(
            self, mock_ack) -> None:
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            data_result = copy.deepcopy(self.raw_data_example_result)
            del data_result['result']['meta_data']
            data_error = copy.deepcopy(self.raw_data_example_downtime_error)
            del data_error['error']['meta_data']
            body_result = json.dumps(data_result)
            body_error = json.dumps(data_error)
            properties = pika.spec.BasicProperties()

            # Make the state non-empty and save it to redis
            self.test_data_transformer._state = copy.deepcopy(self.test_state)
            self.test_data_transformer._save_to_redis(self.test_system)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            # Check that there is 1 entry in the state, one which was not
            # modified.
            expected_data = copy.deepcopy(self.test_system)
            self.assertEqual(1, len(self.test_data_transformer._state.keys()))
            self.assertEqual(
                expected_data.__dict__,
                self.test_data_transformer._state[self.test_system_id].__dict__)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_save_to_redis")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_save_to_redis_if_missing_keys_in_data(
            self, mock_ack, mock_save_to_redis) -> None:
        # Empty Redis as it's value must be compared
        self.redis.delete_all()

        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps({'result': {'bad_key': 'bad_val'}})
            body_error = json.dumps({'error': {'bad_key': 'bad_val'}})
            properties = pika.spec.BasicProperties()

            # Make the state non-empty
            self.test_data_transformer._state = copy.deepcopy(self.test_state)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            # Check that save to redis was not called
            mock_save_to_redis.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_update_state_if_transform_data_exception(
            self, mock_ack, mock_transform_data) -> None:
        mock_ack.return_value = None
        mock_transform_data.side_effect = self.test_exception
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Make the state non-empty and save it to redis
            self.test_data_transformer._state = copy.deepcopy(self.test_state)
            self.test_data_transformer._save_to_redis(self.test_system)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            # Check that there is 1 entry in the state, one which was not
            # modified.
            expected_data = copy.deepcopy(self.test_system)
            self.assertEqual(1, len(self.test_data_transformer._state.keys()))
            self.assertEqual(
                expected_data.__dict__,
                self.test_data_transformer._state[self.test_system_id].__dict__)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(SystemDataTransformer, "_save_to_redis")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_save_to_redis_if_trans_data_exception(
            self, mock_ack, mock_save_to_redis, mock_trans_data) -> None:
        # Empty Redis as it's value must be compared
        self.redis.delete_all()

        mock_ack.return_value = None
        mock_trans_data.side_effect = self.test_exception
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps({'result': {'bad_key': 'bad_val'}})
            body_error = json.dumps({'error': {'bad_key': 'bad_val'}})
            properties = pika.spec.BasicProperties()

            # Make the state non-empty
            self.test_data_transformer._state = copy.deepcopy(self.test_state)

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)

            # Check that save to redis was not called
            mock_save_to_redis.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(SystemDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_places_data_on_queue_if_no_processing_errors(
            self, mock_ack, mock_place_on_queue, mock_trans_data) -> None:
        mock_ack.return_value = None
        mock_trans_data.side_effect = [
            (
                self.transformed_data_example_result,
                self.test_data_for_alerting_result,
                self.transformed_data_example_result
            ),
            (
                self.transformed_data_example_downtime_error,
                self.test_data_for_alerting_down_error,
                self.transformed_data_example_downtime_error
            ),
        ]
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            args, _ = mock_place_on_queue.call_args
            self.assertDictEqual(self.transformed_data_example_result, args[0])
            self.assertDictEqual(self.test_data_for_alerting_result, args[1])
            self.assertDictEqual(self.transformed_data_example_result, args[2])
            self.assertEqual(3, len(args))

            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            args, _ = mock_place_on_queue.call_args
            self.assertDictEqual(self.transformed_data_example_downtime_error,
                                 args[0])
            self.assertDictEqual(self.test_data_for_alerting_down_error,
                                 args[1])
            self.assertDictEqual(self.transformed_data_example_downtime_error,
                                 args[2])
            self.assertEqual(3, len(args))

            self.assertEqual(2, mock_place_on_queue.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_data_on_queue_if_result_or_error_not_in_data(
            self, mock_ack, mock_place_on_queue) -> None:
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body = json.dumps({'bad_key': 'bad_val'})
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body)
            # Check that place_on_queue was not called
            mock_place_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        mock_ack.assert_called_once()

    @mock.patch.object(SystemDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_data_on_queue_if_missing_keys_in_data(
            self, mock_ack, mock_place_on_queue) -> None:
        mock_ack.return_value = None
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            data_result = copy.deepcopy(self.raw_data_example_result)
            del data_result['result']['meta_data']
            data_error = copy.deepcopy(self.raw_data_example_downtime_error)
            del data_error['error']['meta_data']
            body_result = json.dumps(data_result)
            body_error = json.dumps(data_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that place_on_queue was not called
            mock_place_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(SystemDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_data_on_queue_if_transform_data_exception(
            self, mock_ack, mock_place_on_queue, mock_transform_data) -> None:
        mock_ack.return_value = None
        mock_transform_data.side_effect = self.test_exception
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that place_on_queue was not called
            mock_place_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_save_to_redis")
    @mock.patch.object(SystemDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_data_on_queue_if_save_to_redis_exception(
            self, mock_ack, mock_place_on_queue, mock_save_to_redis) -> None:
        mock_ack.return_value = None
        mock_save_to_redis.side_effect = self.test_exception

        # Load the state to avoid errors when having the system already in
        # redis due to other tests.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that place_on_queue was not called
            mock_place_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_update_state")
    @mock.patch.object(SystemDataTransformer, "_place_latest_data_on_queue")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_data_on_queue_if_update_state_exception(
            self, mock_ack, mock_place_on_queue, mock_update_state) -> None:
        mock_ack.return_value = None
        mock_update_state.side_effect = self.test_exception

        # Load the state to avoid errors when having the system already in
        # redis due to other tests.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that place_on_queue was not called
            mock_place_on_queue.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_waiting_on_queue_if_no_process_errors(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None

        # Load the state to avoid errors when having the system already in
        # redis due to other tests.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_general_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that send_data was called
            self.assertEqual(2, mock_send_data.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_data_waiting_on_queue_if_process_errors(
            self, mock_ack, mock_send_data, mock_transform_data) -> None:
        # We will test this by mocking that _transform_data returns an
        # exception. It is safe to assume that the other error paths will result
        # in the same outcome as all the errors are caught. Thus this test-case
        # was essentially done for completion.
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_transform_data.side_effect = self.test_exception
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that send_data was called
            self.assertEqual(2, mock_send_data.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_sends_hb_if_no_proc_errors_and_send_data_success(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.return_value = None

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that send_heartbeat was called
            self.assertEqual(2, mock_send_hb.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_transform_data")
    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_processing_errors_trans_data(
            self, mock_ack, mock_send_hb, mock_trans_data) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_trans_data.side_effect = self.test_exception
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that send_heartbeat was not called
            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_update_state")
    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_proc_errors_update_state(
            self, mock_ack, mock_send_hb, mock_update_state) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_update_state.side_effect = self.test_exception

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that send_heartbeat was not called
            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_save_to_redis")
    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_proc_errors_save_to_redis(
            self, mock_ack, mock_send_hb, mock_save_to_redis) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_save_to_redis.side_effect = self.test_exception

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that send_heartbeat was not called
            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_does_not_send_hb_if_send_data_fails(
            self, mock_ack, mock_send_hb, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_send_data.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_result)
            self.test_data_transformer._process_raw_data(blocking_channel,
                                                         method, properties,
                                                         body_error)
            # Check that send_heartbeat was not called
            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_amqp_conn_err_if_conn_err_in_send_data(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.side_effect = pika.exceptions.AMQPConnectionError(
            'test err')

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data and assert exception
            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_result
                              )
            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_error
                              )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_amqp_conn_err_if_conn_err_in_send_hb(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.side_effect = pika.exceptions.AMQPConnectionError(
            'test err')

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data and assert exception
            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_result
                              )
            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_error
                              )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_amqp_chan_err_if_chan_err_in_send_data(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.side_effect = pika.exceptions.AMQPChannelError(
            'test err')

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data and assert exception
            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_result
                              )
            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_error
                              )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_raises_amqp_chan_err_if_chan_err_in_send_hb(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.side_effect = pika.exceptions.AMQPChannelError(
            'test err')

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data and assert exception
            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_result
                              )
            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_error
                              )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_unexpec_except_if_unexpec_except_in_send_data(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.side_effect = self.test_exception

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data and assert exception
            self.assertRaises(PANICException,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_result
                              )
            self.assertRaises(PANICException,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_error
                              )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_unexpec_except_if_unexpec_except_in_send_hb(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.side_effect = self.test_exception

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data and assert exception
            self.assertRaises(PANICException,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_result
                              )
            self.assertRaises(PANICException,
                              self.test_data_transformer._process_raw_data,
                              blocking_channel, method, properties, body_error
                              )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_msg_not_del_exception_if_raised_by_send_data(
            self, mock_ack, mock_send_data) -> None:
        mock_ack.return_value = None
        mock_send_data.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data. Test would fail if an exception is raised
            self.test_data_transformer._process_raw_data(
                blocking_channel, method, properties, body_result
            )
            self.test_data_transformer._process_raw_data(
                blocking_channel, method, properties, body_error
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        # Make sure that the message has been acknowledged. This must be done
        # in all test cases to cover every possible case, and avoid doing a
        # very large amount of tests around this.
        self.assertEqual(2, mock_ack.call_count)

    @mock.patch.object(SystemDataTransformer, "_send_heartbeat")
    @mock.patch.object(SystemDataTransformer, "_send_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_raw_data_no_msg_not_del_exception_if_raised_by_send_hb(
            self, mock_ack, mock_send_data, mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_send_data.return_value = None
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test err')

        # Load the state to avoid having the system already in redis, hence
        # avoiding errors.
        self.test_data_transformer._state = copy.deepcopy(self.test_state)
        try:
            # We must initialise rabbit to the environment and parameters needed
            # by `_process_raw_data`
            self.test_data_transformer._initialise_rabbitmq()
            blocking_channel = self.test_data_transformer.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=_SYSTEM_DT_INPUT_ROUTING_KEY)
            body_result = json.dumps(self.raw_data_example_result)
            body_error = json.dumps(self.raw_data_example_downtime_error)
            properties = pika.spec.BasicProperties()

            # Send raw data. Test would fail if an exception is raised
            self.test_data_transformer._process_raw_data(
                blocking_channel, method, properties, body_result
            )
            self.test_data_transformer._process_raw_data(
                blocking_channel, method, properties, body_error
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))
