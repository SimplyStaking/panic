import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.data_store.redis import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.dockerhub import DockerhubStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (
    STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE, DOCKERHUB_STORE_INPUT_QUEUE_NAME,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY, DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY,
    TOPIC)
from src.utils.exceptions import (PANICException,
                                  ReceivedUnexpectedDataException)
from test.test_utils.utils import (
    connect_to_rabbit, disconnect_from_rabbit, delete_exchange_if_exists,
    delete_queue_if_exists)


class TestDockerhubStore(unittest.TestCase):
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

        self.mongo_db = env.DB_NAME
        self.mongo_port = env.DB_PORT

        self.test_store_name = 'store name'
        self.test_store = DockerhubStore(self.test_store_name,
                                         self.dummy_logger,
                                         self.rabbitmq)

        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.test_queue_name = 'test queue'

        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.rabbitmq.queue_declare(DOCKERHUB_STORE_INPUT_QUEUE_NAME, False,
                                    True, False, False)
        self.rabbitmq.queue_bind(DOCKERHUB_STORE_INPUT_QUEUE_NAME,
                                 STORE_EXCHANGE,
                                 DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        connect_to_rabbit(self.test_rabbit_manager)
        self.test_rabbit_manager.queue_declare(self.test_queue_name, False,
                                               True, False, False)
        self.test_rabbit_manager.queue_bind(self.test_queue_name,
                                            HEALTH_CHECK_EXCHANGE,
                                            self.heartbeat_routing_key)

        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)

        self.repo_namespace = 'simplyvc'
        self.repo_name = 'panic'
        self.repo_id = 'test_repo_id'
        self.parent_id = 'test_parent_id'

        self.repo_namespace_2 = 'simplyvc'
        self.repo_name_2 = 'panic_oasis'
        self.repo_id_2 = 'test_repo_id_2'
        self.parent_id_2 = 'test_parent_id_2'

        self.last_monitored = datetime(2012, 1, 1).timestamp()
        self.dockerhub_data_1 = {
            "result": {
                "meta_data": {
                    "repo_namespace": self.repo_namespace,
                    "repo_name": self.repo_name,
                    "repo_id": self.repo_id,
                    "repo_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "tags": {
                        '0': {
                            'tag_name': 'v2.0.0',
                            'last_updated': 1635498220.012198
                        },
                        '1': {
                            'tag_name': 'v1.0.0',
                            'last_updated': 1635229653
                        },
                        '2': {
                            'tag_name': 'v0.4.0',
                            'last_updated': 1632637653
                        },
                        '3': {
                            'tag_name': 'v0.3.0',
                            'last_updated': 1629959253
                        },
                        '4': {
                            'tag_name': 'v0.2.0',
                            'last_updated': 1627280853.0214
                        },
                    }
                }
            }
        }
        self.dockerhub_data_2 = {
            "result": {
                "meta_data": {
                    "repo_namespace": self.repo_namespace,
                    "repo_name": self.repo_name,
                    "repo_id": self.repo_id,
                    "repo_parent_id": self.parent_id,
                    "last_monitored": self.last_monitored
                },
                "data": {
                    "tags": {
                        '0': {
                            'tag_name': 'v2.0.0',
                            'last_updated': 1635498220.012198
                        },
                        '1': {
                            'tag_name': 'v1.0.0',
                            'last_updated': 1635229653
                        },
                        '2': {
                            'tag_name': 'v0.4.0',
                            'last_updated': 1632637653
                        }
                    }
                }
            }
        }

        self.dockerhub_data_error = {
            "error": {
                "meta_data": {
                    "repo_namespace": self.repo_namespace,
                    "repo_name": self.repo_name,
                    "repo_id": self.repo_id,
                    "repo_parent_id": self.parent_id,
                    "time": self.last_monitored
                },
                "code": "5018",
                "message": "error message"
            }
        }
        self.dockerhub_data_key_error = {
            "result": {
                "data": {
                    "repo_namespace": self.repo_namespace_2,
                    "repo_name": self.repo_name_2,
                    "repo_id": self.repo_id_2,
                    "repo_parent_id": self.parent_id_2,
                    "last_monitored": self.last_monitored
                },
                "wrong_data": {}
            }
        }
        self.dockerhub_data_unexpected = {
            "unexpected": {}
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, DOCKERHUB_STORE_INPUT_QUEUE_NAME)
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
        self.test_store._redis = None
        self.test_rabbit_manager = None
        self.test_store = None

    def test__str__returns_name_correctly(self) -> None:
        self.assertEqual(self.test_store_name, str(self.test_store))

    def test_name_property_returns_name_correctly(self) -> None:
        self.assertEqual(self.test_store_name, self.test_store.name)

    def test_mongo_db_property_returns_mongo_db_correctly(self) -> None:
        self.assertEqual(self.mongo_db, self.test_store.mongo_db)

    def test_mongo_port_property_returns_mongo_port_correctly(self) -> None:
        self.assertEqual(self.mongo_port, self.test_store.mongo_port)

    def test_redis_property_returns_redis_correctly(self) -> None:
        self.assertEqual(type(self.redis), type(self.test_store.redis))

    def test_mongo_property_returns_none_when_mongo_not_init(self) -> None:
        self.assertEqual(None, self.test_store.mongo)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
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
        self.test_store.rabbitmq.exchange_declare(STORE_EXCHANGE,
                                                  passive=True)
        self.test_store.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE,
                                                  passive=True)

        # Check whether the exchange has been creating by sending messages
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
            exchange=STORE_EXCHANGE,
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=False)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            DOCKERHUB_STORE_INPUT_QUEUE_NAME, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_store.rabbitmq.basic_get(
            DOCKERHUB_STORE_INPUT_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())

    @parameterized.expand([
        ("self.dockerhub_data_1",),
        ("self.dockerhub_data_2",),
    ])
    @mock.patch.object(RedisApi, "hset_multiple")
    def test_process_redis_store_redis_is_called_correctly(
            self, mock_dockerhub_data, mock_hset_multiple) -> None:
        data = eval(mock_dockerhub_data)
        self.test_store._process_redis_store(data)

        meta_data = data['result']['meta_data']
        repo_id = meta_data['repo_id']
        parent_id = meta_data['repo_parent_id']
        metrics = data['result']['data']

        call_1 = call(Keys.get_hash_parent(parent_id), {
            Keys.get_dockerhub_last_tags(repo_id):
                json.dumps(metrics['tags']),
            Keys.get_dockerhub_last_monitored(repo_id):
                str(meta_data['last_monitored']),
        })
        mock_hset_multiple.assert_has_calls([call_1])

    @mock.patch("src.data_store.stores.store.RedisApi.hset_multiple",
                autospec=True)
    def test_process_redis_store_does_nothing_on_error_key(
            self, mock_hset_multiple) -> None:
        self.test_store._process_redis_store(self.dockerhub_data_error)
        mock_hset_multiple.assert_not_called()

    def test_process_redis_store_raises_exception_on_unexpected_key(
            self) -> None:
        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_store._process_redis_store,
                          self.dockerhub_data_unexpected)

    @parameterized.expand([
        ("self.dockerhub_data_1",),
        ("self.dockerhub_data_2",),
    ])
    def test_process_redis_store_redis_stores_correctly(
            self, mock_dockerhub_data) -> None:
        data = eval(mock_dockerhub_data)
        self.test_store._process_redis_store(data)

        meta_data = data['result']['meta_data']
        repo_id = meta_data['repo_id']
        parent_id = meta_data['repo_parent_id']
        metrics = data['result']['data']

        self.assertEqual(json.dumps(metrics['tags']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_dockerhub_last_tags(
                                             repo_id)).decode("utf-8"))
        self.assertEqual(str(meta_data['last_monitored']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_dockerhub_last_monitored(
                                             repo_id)).decode("utf-8"))

    @parameterized.expand([
        ("self.dockerhub_data_1",),
        ("self.dockerhub_data_2",),
    ])
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_saves_in_redis(self, mock_dockerhub_data,
                                         mock_send_hb, mock_ack) -> None:
        self.rabbitmq.connect()
        mock_ack.return_value = None

        self.test_store._initialise_rabbitmq()
        data = eval(mock_dockerhub_data)

        blocking_channel = self.test_store.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(data)
        )
        mock_ack.assert_called_once()
        mock_send_hb.assert_called_once()

        meta_data = data['result']['meta_data']
        repo_id = meta_data['repo_id']
        parent_id = meta_data['repo_parent_id']
        metrics = data['result']['data']

        self.assertEqual(json.dumps(metrics['tags']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_dockerhub_last_tags(
                                             repo_id)).decode(
                             "utf-8"))
        self.assertEqual(str(meta_data['last_monitored']),
                         self.redis.hget(Keys.get_hash_parent(parent_id),
                                         Keys.get_dockerhub_last_monitored(
                                             repo_id)).decode(
                             "utf-8"))

    @parameterized.expand([
        ("KeyError", "self.dockerhub_data_key_error "),
        ("ReceivedUnexpectedDataException", "self.dockerhub_data_unexpected"),
    ])
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_with_bad_data_does_raises_exceptions(
            self, mock_error, mock_bad_data, mock_send_hb, mock_ack) -> None:
        self.rabbitmq.connect()
        mock_ack.return_value = None

        self.test_store._initialise_rabbitmq()

        blocking_channel = self.test_store.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(eval(mock_bad_data))
        )
        self.assertRaises(eval(mock_error),
                          self.test_store._process_redis_store,
                          eval(mock_bad_data))
        mock_ack.assert_called_once()
        mock_send_hb.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch(
        "src.data_store.stores.dockerhub.DockerhubStore._process_redis_store",
        autospec=True)
    def test_process_data_sends_heartbeat_correctly(self,
                                                    mock_process_redis_store,
                                                    mock_basic_ack) -> None:
        mock_basic_ack.return_value = None

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
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(self.dockerhub_data_1)
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

    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    def test_process_data_doesnt_send_heartbeat_on_processing_error(
            self, mock_basic_ack) -> None:
        mock_basic_ack.return_value = None

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
            routing_key=DOCKERHUB_TRANSFORMED_DATA_ROUTING_KEY)

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(
            blocking_channel,
            method_chains,
            properties,
            json.dumps(self.dockerhub_data_unexpected)
        )

        res = self.test_rabbit_manager.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(0, res.method.message_count)
