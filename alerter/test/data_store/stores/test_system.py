import json
import logging
import time
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.system import SystemStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                          SYSTEM_STORE_INPUT_QUEUE_NAME,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          SYSTEM_STORE_INPUT_ROUTING_KEY, TOPIC)
from src.utils.exceptions import (PANICException,
                                  ReceivedUnexpectedDataException)
from test.utils.utils import (connect_to_rabbit,
                              disconnect_from_rabbit,
                              delete_exchange_if_exists,
                              delete_queue_if_exists)


class TestSystemStore(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        self.test_rabbit_manager = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        self.redis_db = env.REDIS_DB
        self.redis_host = env.REDIS_IP
        self.redis_port = env.REDIS_PORT
        self.redis_namespace = env.UNIQUE_ALERTER_IDENTIFIER
        self.redis = RedisApi(self.dummy_logger, self.redis_db,
                              self.redis_host, self.redis_port, '',
                              self.redis_namespace,
                              self.connection_check_time_interval)

        self.mongo_ip = env.DB_IP
        self.mongo_db = env.DB_NAME
        self.mongo_port = env.DB_PORT

        self.mongo = MongoApi(logger=self.dummy_logger.getChild(
            MongoApi.__name__),
            db_name=self.mongo_db, host=self.mongo_ip,
            port=self.mongo_port)

        self.test_store_name = 'store name'
        self.test_store = SystemStore(self.test_store_name,
                                      self.dummy_logger,
                                      self.rabbitmq)

        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self._input_routing_key = 'transformed_data.system.test_system'
        self.test_queue_name = 'test queue'

        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.rabbitmq.queue_declare(SYSTEM_STORE_INPUT_QUEUE_NAME, False, True,
                                    False, False)
        self.rabbitmq.queue_bind(SYSTEM_STORE_INPUT_QUEUE_NAME, STORE_EXCHANGE,
                                 SYSTEM_STORE_INPUT_ROUTING_KEY)

        connect_to_rabbit(self.test_rabbit_manager)
        self.test_rabbit_manager.queue_declare(self.test_queue_name, False,
                                               True, False, False)
        self.test_rabbit_manager.queue_bind(self.test_queue_name,
                                            HEALTH_CHECK_EXCHANGE,
                                            self.heartbeat_routing_key)

        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)

        self.system_id = 'test_system_id'
        self.parent_id = 'test_parent_id'
        self.system_name = 'test_system'

        self.system_id_2 = 'test_system_id_2'
        self.parent_id_2 = 'test_parent_id_2'
        self.system_name_2 = 'test_system_2'
        self.last_monitored = datetime(2012, 1, 1).timestamp()

        self.none = None
        # Process CPU Seconds Total
        self.current_cpu_sec = 42420.88
        self.previous_cpu_sec = 42400.42
        # Process Memory Usage
        self.current_mem_use = 20.00
        self.previous_mem_use = 10.23
        # Virtual Memory Usage
        self.current_v_mem_use = 735047680.0
        self.previous_v_mem_use = 723312578.0
        self.percent_usage = 40
        self.bytes_usage = 19283912
        self.seconds_usage = 1282389129
        self.pad = 10
        self.pad2 = 20
        self.system_data_1 = {
            "result": {
                "meta_data": {
                    "system_name": self.system_name,
                    "system_id": self.system_id,
                    "system_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "process_cpu_seconds_total": self.current_cpu_sec,
                    "process_memory_usage": self.current_mem_use,
                    "virtual_memory_usage": self.current_v_mem_use,
                    "open_file_descriptors": self.percent_usage,
                    "system_cpu_usage": self.percent_usage,
                    "system_ram_usage": self.percent_usage,
                    "system_storage_usage": self.percent_usage,
                    "network_receive_bytes_total": self.bytes_usage,
                    "network_transmit_bytes_total": self.bytes_usage,
                    "disk_io_time_seconds_total": self.seconds_usage,
                    "network_transmit_bytes_per_second": self.bytes_usage,
                    "network_receive_bytes_per_second": self.bytes_usage,
                    "disk_io_time_seconds_in_interval": self.seconds_usage,
                    "went_down_at": self.none
                }
            }
        }
        self.system_data_2 = {
            "result": {
                "meta_data": {
                    "system_name": self.system_name,
                    "system_id": self.system_id,
                    "system_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "process_cpu_seconds_total":
                        self.current_cpu_sec + self.pad,
                    "process_memory_usage": self.current_mem_use + self.pad,
                    "virtual_memory_usage": self.current_v_mem_use + self.pad,
                    "open_file_descriptors": self.percent_usage + self.pad,
                    "system_cpu_usage": self.percent_usage + self.pad,
                    "system_ram_usage": self.percent_usage + self.pad,
                    "system_storage_usage": self.percent_usage + self.pad,
                    "network_receive_bytes_total": self.bytes_usage + self.pad,
                    "network_transmit_bytes_total":
                        self.bytes_usage + self.pad,
                    "disk_io_time_seconds_total":
                        self.seconds_usage + self.pad,
                    "network_transmit_bytes_per_second":
                        self.bytes_usage + self.pad,
                    "network_receive_bytes_per_second":
                        self.bytes_usage + self.pad,
                    "disk_io_time_seconds_in_interval":
                        self.seconds_usage + self.pad,
                    "went_down_at": self.none
                }
            }
        }
        self.system_data_3 = {
            "result": {
                "meta_data": {
                    "system_name": self.system_name,
                    "system_id": self.system_id,
                    "system_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "process_cpu_seconds_total":
                        self.current_cpu_sec + self.pad2,
                    "process_memory_usage": self.current_mem_use + self.pad2,
                    "virtual_memory_usage": self.current_v_mem_use + self.pad2,
                    "open_file_descriptors": self.percent_usage + self.pad2,
                    "system_cpu_usage": self.percent_usage + self.pad2,
                    "system_ram_usage": self.percent_usage + self.pad2,
                    "system_storage_usage": self.percent_usage + self.pad2,
                    "network_receive_bytes_total": self.bytes_usage + self.pad2,
                    "network_transmit_bytes_total":
                        self.bytes_usage + self.pad2,
                    "disk_io_time_seconds_total":
                        self.seconds_usage + self.pad2,
                    "network_transmit_bytes_per_second":
                        self.bytes_usage + self.pad2,
                    "network_receive_bytes_per_second":
                        self.bytes_usage + self.pad2,
                    "disk_io_time_seconds_in_interval":
                        self.seconds_usage + self.pad2,
                    "went_down_at": self.none
                }
            }
        }
        self.system_data_error = {
            "error": {
                "meta_data": {
                    "system_name": self.system_name,
                    "system_id": self.system_id,
                    "system_parent_id": self.parent_id,
                    "time": self.last_monitored
                },
                "data": {
                    "went_down_at": self.last_monitored
                },
                "code": 5004
            }
        }
        self.system_data_key_error = {
            "result": {
                "data": {},
                "data2": {}
            }
        }
        self.system_data_unexpected = {
            "unexpected": {}
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, SYSTEM_STORE_INPUT_QUEUE_NAME)
        delete_exchange_if_exists(self.rabbitmq, STORE_EXCHANGE)
        delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        connect_to_rabbit(self.test_rabbit_manager)
        delete_queue_if_exists(self.test_rabbit_manager, self.test_queue_name)
        disconnect_from_rabbit(self.test_rabbit_manager)

        self.redis.delete_all_unsafe()
        self.redis = None
        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_rabbit_manager = None
        self.mongo.drop_collection(self.parent_id)
        self.mongo = None
        self.test_store._mongo = None
        self.test_store._redis = None
        self.test_store = None

    def test__str__returns_name_correctly(self) -> None:
        self.assertEqual(self.test_store_name, str(self.test_store))

    def test_name_property_returns_name_correctly(self) -> None:
        self.assertEqual(self.test_store_name, self.test_store.name)

    def test_mongo_ip_property_returns_mongo_ip_correctly(self) -> None:
        self.assertEqual(self.mongo_ip, self.test_store.mongo_ip)

    def test_mongo_db_property_returns_mongo_db_correctly(self) -> None:
        self.assertEqual(self.mongo_db, self.test_store.mongo_db)

    def test_mongo_port_property_returns_mongo_port_correctly(self) -> None:
        self.assertEqual(self.mongo_port, self.test_store.mongo_port)

    def test_redis_property_returns_redis_correctly(self) -> None:
        self.assertEqual(type(self.redis), type(self.test_store.redis))

    def test_mongo_property_returns_mongo_when_store_exists(self) -> None:
        self.assertEqual(type(self.mongo), type(self.test_store.mongo))

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        try:
            # To make sure that the exchanges have not already been declared
            self.rabbitmq.connect()
            self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.rabbitmq.exchange_delete(STORE_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_store._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_store.rabbitmq.is_connected)
            self.assertTrue(self.test_store.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_store.rabbitmq.channel._delivery_confirmation)

            # Check whether the producing exchanges have been created by
            # using passive=True. If this check fails an exception is raised
            # automatically.
            self.test_store.rabbitmq.exchange_declare(
                STORE_EXCHANGE, passive=True)
            self.test_store.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, passive=True)

            # Check whether the exchange has been created by sending messages
            # to it. If this fails an exception is raised, hence the test fails.
            self.test_store.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=self.heartbeat_routing_key, body=self.test_data_str,
                is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)
            # Check whether the exchange has been creating by sending messages
            # to it. If this fails an exception is raised, hence the test fails.
            self.test_store.rabbitmq.basic_publish_confirm(
                exchange=STORE_EXCHANGE, routing_key=self._input_routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)
            time.sleep(1)
            # Re-declare queue to get the number of messages
            res = self.test_store.rabbitmq.queue_declare(
                SYSTEM_STORE_INPUT_QUEUE_NAME, False, True, False, False)

            self.assertEqual(1, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("self.system_data_1",),
        ("self.system_data_2",),
        ("self.system_data_3",),
    ])
    @mock.patch.object(RedisApi, "hset_multiple")
    def test_process_redis_store_redis_is_called_correctly(
            self, mock_system_data, mock_hset_multiple) -> None:

        data = eval(mock_system_data)
        self.test_store._process_redis_store(data)

        meta_data = data['result']['meta_data']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['result']['data']

        call_1 = call(Keys.get_hash_parent(parent_id), {
            Keys.get_system_process_cpu_seconds_total(system_id):
                str(metrics['process_cpu_seconds_total']),
            Keys.get_system_process_memory_usage(system_id):
                str(metrics['process_memory_usage']),
            Keys.get_system_virtual_memory_usage(system_id):
                str(metrics['virtual_memory_usage']),
            Keys.get_system_open_file_descriptors(system_id):
                str(metrics['open_file_descriptors']),
            Keys.get_system_system_cpu_usage(system_id):
                str(metrics['system_cpu_usage']),
            Keys.get_system_system_ram_usage(system_id):
                str(metrics['system_ram_usage']),
            Keys.get_system_system_storage_usage(system_id):
                str(metrics['system_storage_usage']),
            Keys.get_system_network_transmit_bytes_per_second(
                system_id):
                str(metrics['network_transmit_bytes_per_second']),
            Keys.get_system_network_receive_bytes_per_second(
                system_id):
                str(metrics['network_receive_bytes_per_second']),
            Keys.get_system_network_receive_bytes_total(system_id):
                str(metrics['network_receive_bytes_total']),
            Keys.get_system_network_transmit_bytes_total(system_id):
                str(metrics['network_transmit_bytes_total']),
            Keys.get_system_disk_io_time_seconds_total(system_id):
                str(metrics['disk_io_time_seconds_total']),
            Keys.get_system_disk_io_time_seconds_in_interval(
                system_id):
                str(metrics['disk_io_time_seconds_in_interval']),
            Keys.get_system_went_down_at(system_id):
                str(metrics['went_down_at']),
            Keys.get_system_last_monitored(system_id):
                str(meta_data['last_monitored'])})
        mock_hset_multiple.assert_has_calls([call_1])

    @mock.patch.object(RedisApi, "hset")
    def test_process_redis_store_calls_hset_on_error(self, mock_hset) -> None:
        self.test_store._process_redis_store(self.system_data_error)
        call_1 = call(Keys.get_hash_parent(self.parent_id),
                      Keys.get_system_went_down_at(self.system_id),
                      str(self.last_monitored))
        mock_hset.assert_has_calls([call_1])

    def test_process_redis_store_raises_exception_on_unexpected_key(
            self) -> None:
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_store._process_redis_store,
                          self.system_data_unexpected)

    @parameterized.expand([
        ("self.system_data_1",),
        ("self.system_data_2",),
        ("self.system_data_3",),
    ])
    def test_process_redis_store_redis_stores_correctly(
            self, mock_system_data) -> None:

        data = eval(mock_system_data)
        self.test_store._process_redis_store(data)

        meta_data = data['result']['meta_data']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['result']['data']

        self.assertEqual(str(metrics['process_cpu_seconds_total']),
                         self.redis.hget(
                             Keys.get_hash_parent(parent_id),
                             Keys.get_system_process_cpu_seconds_total(
                                 system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['process_memory_usage']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_system_process_memory_usage(
                                             system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['virtual_memory_usage']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_system_virtual_memory_usage(
                                             system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['open_file_descriptors']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_system_open_file_descriptors(
                                             system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['system_cpu_usage']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_system_system_cpu_usage(
                                             system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['system_ram_usage']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_system_system_ram_usage(
                                             system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['system_storage_usage']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_system_system_storage_usage(
                                             system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['network_transmit_bytes_per_second']),
                         self.redis.hget(
                             Keys.get_hash_parent(parent_id),
                             Keys.get_system_network_transmit_bytes_per_second(
                                 system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['network_receive_bytes_per_second']),
                         self.redis.hget(
                             Keys.get_hash_parent(parent_id),
                             Keys.get_system_network_receive_bytes_per_second(
                                 system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['network_receive_bytes_per_second']),
                         self.redis.hget(
                             Keys.get_hash_parent(parent_id),
                             Keys.get_system_network_receive_bytes_total(
                                 system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['network_transmit_bytes_total']),
                         self.redis.hget(
                             Keys.get_hash_parent(parent_id),
                             Keys.get_system_network_transmit_bytes_total(
                                 system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['disk_io_time_seconds_total']),
                         self.redis.hget(
                             Keys.get_hash_parent(parent_id),
                             Keys.get_system_disk_io_time_seconds_total(
                                 system_id)).decode("utf-8"))
        self.assertEqual(str(metrics['disk_io_time_seconds_in_interval']),
                         self.redis.hget(
                             Keys.get_hash_parent(parent_id),
                             Keys.get_system_disk_io_time_seconds_in_interval(
                                 system_id)).decode("utf-8"))
        self.assertEqual(self.none, self.redis.hget(Keys.get_hash_parent(
            parent_id), Keys.get_system_went_down_at(
            system_id)))
        self.assertEqual(str(meta_data['last_monitored']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_system_last_monitored(
                                             system_id)).decode("utf-8"))

    @parameterized.expand([
        ("self.system_data_1",),
        ("self.system_data_2",),
        ("self.system_data_3",),
    ])
    @mock.patch("src.data_store.stores.system.SystemStore._process_mongo_store",
                autospec=True)
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_saves_in_redis(self, mock_system_data, mock_send_hb,
                                         mock_ack, mock_process_mongo) -> None:
        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()
            data = eval(mock_system_data)

            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )
            mock_process_mongo.assert_called_once()
            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            meta_data = data['result']['meta_data']
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            metrics = data['result']['data']

            self.assertEqual(str(metrics['process_cpu_seconds_total']),
                             self.redis.hget(
                                 Keys.get_hash_parent(parent_id),
                                 Keys.get_system_process_cpu_seconds_total(
                                     system_id)).decode("utf-8"))
            self.assertEqual(str(metrics['process_memory_usage']),
                             self.redis.hget(
                                 Keys.get_hash_parent(parent_id),
                                 Keys.get_system_process_memory_usage(
                                     system_id)).decode("utf-8"))
            self.assertEqual(str(metrics['virtual_memory_usage']),
                             self.redis.hget(
                                 Keys.get_hash_parent(parent_id),
                                 Keys.get_system_virtual_memory_usage(
                                     system_id)).decode("utf-8"))
            self.assertEqual(str(metrics['open_file_descriptors']),
                             self.redis.hget(
                                 Keys.get_hash_parent(parent_id),
                                 Keys.get_system_open_file_descriptors(
                                     system_id)).decode("utf-8"))
            self.assertEqual(str(metrics['system_cpu_usage']),
                             self.redis.hget(Keys.get_hash_parent(parent_id),
                                             Keys.get_system_system_cpu_usage(
                                                 system_id)).decode("utf-8"))
            self.assertEqual(str(metrics['system_ram_usage']),
                             self.redis.hget(Keys.get_hash_parent(parent_id),
                                             Keys.get_system_system_ram_usage(
                                                 system_id)).decode("utf-8"))
            self.assertEqual(str(metrics['system_storage_usage']),
                             self.redis.hget(
                                 Keys.get_hash_parent(parent_id),
                                 Keys.get_system_system_storage_usage(
                                     system_id)).decode("utf-8"))
            self.assertEqual(
                str(metrics['network_transmit_bytes_per_second']),
                self.redis.hget(
                    Keys.get_hash_parent(parent_id),
                    Keys.get_system_network_transmit_bytes_per_second(
                        system_id)).decode("utf-8"))
            self.assertEqual(
                str(metrics['network_receive_bytes_per_second']),
                self.redis.hget(
                    Keys.get_hash_parent(parent_id),
                    Keys.get_system_network_receive_bytes_per_second(
                        system_id)).decode("utf-8"))
            self.assertEqual(
                str(metrics['network_receive_bytes_per_second']),
                self.redis.hget(Keys.get_hash_parent(parent_id),
                                Keys.get_system_network_receive_bytes_total(
                                    system_id)).decode("utf-8"))
            self.assertEqual(
                str(metrics['network_transmit_bytes_total']),
                self.redis.hget(Keys.get_hash_parent(parent_id),
                                Keys.get_system_network_transmit_bytes_total(
                                    system_id)).decode("utf-8"))
            self.assertEqual(str(metrics['disk_io_time_seconds_total']),
                             self.redis.hget(
                                 Keys.get_hash_parent(parent_id),
                                 Keys.get_system_disk_io_time_seconds_total(
                                     system_id)).decode("utf-8"))
            self.assertEqual(
                str(metrics['disk_io_time_seconds_in_interval']),
                self.redis.hget(
                    Keys.get_hash_parent(parent_id),
                    Keys.get_system_disk_io_time_seconds_in_interval(
                        system_id)).decode("utf-8"))
            self.assertEqual(self.none, self.redis.hget(
                Keys.get_hash_parent(parent_id),
                Keys.get_system_went_down_at(
                    system_id)))
            self.assertEqual(str(meta_data['last_monitored']),
                             self.redis.hget(Keys.get_hash_parent(parent_id),
                                             Keys.get_system_last_monitored(
                                                 system_id)).decode("utf-8"))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("KeyError", "self.system_data_key_error "),
        ("ReceivedUnexpectedDataException", "self.system_data_unexpected"),
    ])
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_with_bad_data_does_raises_exceptions(
            self, mock_error, mock_bad_data, mock_send_hb, mock_ack) -> None:
        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.system_data_unexpected).encode()
            )
            self.assertRaises(eval(mock_error),
                              self.test_store._process_redis_store,
                              eval(mock_bad_data))
            mock_ack.assert_called_once()
            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.system.SystemStore._process_mongo_store",
                autospec=True)
    @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
                autospec=True)
    def test_process_data_sends_heartbeat_correctly(self,
                                                    mock_process_redis_store,
                                                    mock_process_mongo_store,
                                                    mock_basic_ack) -> None:

        mock_basic_ack.return_value = None
        try:
            self.test_rabbit_manager.connect()
            self.test_store._initialise_rabbitmq()

            self.test_rabbit_manager.queue_delete(self.test_queue_name)
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)

            self.test_rabbit_manager.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=self.heartbeat_routing_key)

            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.system_data_1).encode()
            )

            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            heartbeat_test = {
                'component_name': self.test_store_name,
                'is_alive': True,
                'timestamp': datetime(2012, 1, 1).timestamp()
            }

            _, _, body = self.test_rabbit_manager.basic_get(
                self.test_queue_name)
            self.assertEqual(heartbeat_test, json.loads(body))
            mock_process_redis_store.assert_called_once()
            mock_process_mongo_store.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    def test_process_data_doesnt_send_heartbeat_on_processing_error(
            self, mock_basic_ack) -> None:

        mock_basic_ack.return_value = None
        try:
            self.test_rabbit_manager.connect()
            self.test_store._initialise_rabbitmq()

            self.test_rabbit_manager.queue_delete(self.test_queue_name)
            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)

            self.test_rabbit_manager.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=self.heartbeat_routing_key)

            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.system_data_unexpected).encode()
            )

            res = self.test_rabbit_manager.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(MongoApi, "update_one")
    def test_process_mongo_store_calls_update_one(self,
                                                  mock_update_one) -> None:
        self.test_store._process_mongo_result_store(
            self.system_data_1['result'])
        mock_update_one.assert_called_once()

    def test_process_mongo_store_raises_exception_on_unexpected_key(
            self) -> None:
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_store._process_mongo_store,
                          self.system_data_unexpected)

    @parameterized.expand([
        ("self.system_data_1",),
        ("self.system_data_2",),
        ("self.system_data_3",),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(MongoApi, "update_one")
    def test_process_mongo_result_store_calls_mongo_correctly(
            self, mock_system_data, mock_update_one) -> None:
        data = eval(mock_system_data)
        self.test_store._process_mongo_result_store(data['result'])

        meta_data = data['result']['meta_data']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['result']['data']
        call_1 = call(
            parent_id,
            {'doc_type': 'system', 'd': datetime.now().hour},
            {
                '$push': {
                    system_id: {
                        'process_cpu_seconds_total': str(
                            metrics['process_cpu_seconds_total']),
                        'process_memory_usage': str(
                            metrics['process_memory_usage']),
                        'virtual_memory_usage': str(
                            metrics['virtual_memory_usage']),
                        'open_file_descriptors': str(
                            metrics['open_file_descriptors']),
                        'system_cpu_usage': str(metrics['system_cpu_usage']),
                        'system_ram_usage': str(metrics['system_ram_usage']),
                        'system_storage_usage': str(
                            metrics['system_storage_usage']),
                        'network_transmit_bytes_per_second': str(
                            metrics['network_transmit_bytes_per_second']),
                        'network_receive_bytes_per_second': str(
                            metrics['network_receive_bytes_per_second']),
                        'network_receive_bytes_total': str(
                            metrics['network_receive_bytes_total']),
                        'network_transmit_bytes_total': str(
                            metrics['network_transmit_bytes_total']),
                        'disk_io_time_seconds_total': str(
                            metrics['disk_io_time_seconds_total']),
                        'disk_io_time_seconds_in_interval': str(
                            metrics['disk_io_time_seconds_in_interval']),
                        'went_down_at': str(metrics['went_down_at']),
                        'timestamp': str(meta_data['last_monitored']),
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )
        mock_update_one.assert_has_calls([call_1])

    @parameterized.expand([
        ("self.system_data_1",),
        ("self.system_data_2",),
        ("self.system_data_3",),
    ])
    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
                autospec=True)
    @mock.patch.object(MongoApi, "update_one")
    def test_process_data_calls_mongo_correctly(
            self, mock_system_data, mock_update_one, mock_process_redis_store,
            mock_send_hb, mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = eval(mock_system_data)
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )

            mock_process_redis_store.assert_called_once()
            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            meta_data = data['result']['meta_data']
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            metrics = data['result']['data']
            call_1 = call(
                parent_id,
                {'doc_type': 'system', 'd': datetime.now().hour},
                {
                    '$push': {
                        system_id: {
                            'process_cpu_seconds_total': str(
                                metrics['process_cpu_seconds_total']),
                            'process_memory_usage': str(
                                metrics['process_memory_usage']),
                            'virtual_memory_usage': str(
                                metrics['virtual_memory_usage']),
                            'open_file_descriptors': str(
                                metrics['open_file_descriptors']),
                            'system_cpu_usage': str(
                                metrics['system_cpu_usage']),
                            'system_ram_usage': str(
                                metrics['system_ram_usage']),
                            'system_storage_usage': str(
                                metrics['system_storage_usage']),
                            'network_transmit_bytes_per_second': str(
                                metrics['network_transmit_bytes_per_second']),
                            'network_receive_bytes_per_second': str(
                                metrics['network_receive_bytes_per_second']),
                            'network_receive_bytes_total': str(
                                metrics['network_receive_bytes_total']),
                            'network_transmit_bytes_total': str(
                                metrics['network_transmit_bytes_total']),
                            'disk_io_time_seconds_total': str(
                                metrics['disk_io_time_seconds_total']),
                            'disk_io_time_seconds_in_interval': str(
                                metrics['disk_io_time_seconds_in_interval']),
                            'went_down_at': str(metrics['went_down_at']),
                            'timestamp': str(meta_data['last_monitored']),
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
            mock_update_one.assert_has_calls([call_1])
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(MongoApi, "update_one")
    def test_process_mongo_error_store_calls_mongo_correctly(
            self, mock_update_one) -> None:

        data = self.system_data_error
        self.test_store._process_mongo_error_store(data['error'])

        meta_data = data['error']['meta_data']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['error']['data']

        call_1 = call(
            parent_id,
            {'doc_type': 'system', 'd': datetime.now().hour},
            {
                '$push': {
                    system_id: {
                        'went_down_at': str(metrics['went_down_at']),
                        'timestamp': str(meta_data['time']),
                    }
                },
                '$inc': {'n_entries': 1},
            }
        )
        mock_update_one.assert_has_calls([call_1])

    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
                autospec=True)
    @mock.patch.object(MongoApi, "update_one")
    def test_process_data_calls_mongo_correctly_on_error_data(
            self, mock_update_one, mock_process_redis_store,
            mock_send_hb, mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = self.system_data_error
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )

            mock_process_redis_store.assert_called_once()
            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            meta_data = data['error']['meta_data']
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            metrics = data['error']['data']

            call_1 = call(
                parent_id,
                {'doc_type': 'system', 'd': datetime.now().hour},
                {
                    '$push': {
                        system_id: {
                            'went_down_at': str(metrics['went_down_at']),
                            'timestamp': str(meta_data['time']),
                        }
                    },
                    '$inc': {'n_entries': 1},
                }
            )
            mock_update_one.assert_has_calls([call_1])
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("self.system_data_1",),
        ("self.system_data_2",),
        ("self.system_data_3",),
    ])
    def test_process_mongo_store_mongo_stores_correctly(
            self, mock_system_data) -> None:

        data = eval(mock_system_data)
        self.test_store._process_mongo_store(data)

        meta_data = data['result']['meta_data']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['result']['data']

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'system',
            1,
            str(metrics['process_cpu_seconds_total']),
            str(metrics['process_memory_usage']),
            str(metrics['virtual_memory_usage']),
            str(metrics['open_file_descriptors']),
            str(metrics['system_cpu_usage']),
            str(metrics['system_ram_usage']),
            str(metrics['system_storage_usage']),
            str(metrics['network_receive_bytes_total']),
            str(metrics['network_transmit_bytes_total']),
            str(metrics['disk_io_time_seconds_total']),
            str(metrics['network_transmit_bytes_per_second']),
            str(metrics['network_receive_bytes_per_second']),
            str(metrics['disk_io_time_seconds_in_interval']),
            str(metrics['went_down_at'])
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            document[system_id][0]['process_cpu_seconds_total'],
            document[system_id][0]['process_memory_usage'],
            document[system_id][0]['virtual_memory_usage'],
            document[system_id][0]['open_file_descriptors'],
            document[system_id][0]['system_cpu_usage'],
            document[system_id][0]['system_ram_usage'],
            document[system_id][0]['system_storage_usage'],
            document[system_id][0]['network_receive_bytes_total'],
            document[system_id][0]['network_transmit_bytes_total'],
            document[system_id][0]['disk_io_time_seconds_total'],
            document[system_id][0]['network_transmit_bytes_per_second'],
            document[system_id][0]['network_receive_bytes_per_second'],
            document[system_id][0]['disk_io_time_seconds_in_interval'],
            document[system_id][0]['went_down_at']
        ]

        self.assertListEqual(expected, actual)

    @freeze_time("2012-01-01")
    def test_process_mongo_error_store_store_correctly(self) -> None:

        data = self.system_data_error
        self.test_store._process_mongo_error_store(data['error'])

        meta_data = data['error']['meta_data']
        system_id = meta_data['system_id']
        parent_id = meta_data['system_parent_id']
        metrics = data['error']['data']

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'system',
            1,
            str(meta_data['time']),
            str(metrics['went_down_at'])
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            document[system_id][0]['timestamp'],
            document[system_id][0]['went_down_at']
        ]

        self.assertListEqual(expected, actual)

    @parameterized.expand([
        ("self.system_data_1",),
        ("self.system_data_2",),
        ("self.system_data_3",),
    ])
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
                autospec=True)
    def test_process_data_results_stores_in_mongo_correctly(
            self, mock_system_data, mock_process_redis_store,
            mock_send_hb, mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = eval(mock_system_data)
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )

            mock_process_redis_store.assert_called_once()
            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            meta_data = data['result']['meta_data']
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            metrics = data['result']['data']

            documents = self.mongo.get_all(parent_id)
            document = documents[0]
            expected = [
                'system',
                1,
                str(metrics['process_cpu_seconds_total']),
                str(metrics['process_memory_usage']),
                str(metrics['virtual_memory_usage']),
                str(metrics['open_file_descriptors']),
                str(metrics['system_cpu_usage']),
                str(metrics['system_ram_usage']),
                str(metrics['system_storage_usage']),
                str(metrics['network_receive_bytes_total']),
                str(metrics['network_transmit_bytes_total']),
                str(metrics['disk_io_time_seconds_total']),
                str(metrics['network_transmit_bytes_per_second']),
                str(metrics['network_receive_bytes_per_second']),
                str(metrics['disk_io_time_seconds_in_interval']),
                str(metrics['went_down_at'])
            ]
            actual = [
                document['doc_type'],
                document['n_entries'],
                document[system_id][0]['process_cpu_seconds_total'],
                document[system_id][0]['process_memory_usage'],
                document[system_id][0]['virtual_memory_usage'],
                document[system_id][0]['open_file_descriptors'],
                document[system_id][0]['system_cpu_usage'],
                document[system_id][0]['system_ram_usage'],
                document[system_id][0]['system_storage_usage'],
                document[system_id][0]['network_receive_bytes_total'],
                document[system_id][0]['network_transmit_bytes_total'],
                document[system_id][0]['disk_io_time_seconds_total'],
                document[system_id][0]['network_transmit_bytes_per_second'],
                document[system_id][0]['network_receive_bytes_per_second'],
                document[system_id][0]['disk_io_time_seconds_in_interval'],
                document[system_id][0]['went_down_at']
            ]

            self.assertListEqual(expected, actual)

        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
                autospec=True)
    def test_process_data_error_stores_in_mongo_correctly(
            self, mock_process_redis_store,
            mock_send_hb, mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = self.system_data_error
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self._input_routing_key)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )

            mock_process_redis_store.assert_called_once()
            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            meta_data = data['error']['meta_data']
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            metrics = data['error']['data']

            documents = self.mongo.get_all(parent_id)
            document = documents[0]
            expected = [
                'system',
                1,
                str(meta_data['time']),
                str(metrics['went_down_at'])
            ]
            actual = [
                document['doc_type'],
                document['n_entries'],
                document[system_id][0]['timestamp'],
                document[system_id][0]['went_down_at']
            ]

            self.assertListEqual(expected, actual)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
