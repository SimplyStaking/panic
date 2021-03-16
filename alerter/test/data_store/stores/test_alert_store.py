import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from queue import Queue
from typing import Union, Dict
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.data_store.redis.redis_api import RedisApi
from src.data_store.mongo.mongo_api import MongoApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.data_store.redis.store_keys import Keys

from src.data_store.stores.alert import AlertStore
from src.utils import env
from src.utils.constants import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 ALERT_STORE_INPUT_QUEUE,
                                 ALERT_STORE_INPUT_ROUTING_KEY)
from src.utils.exceptions import (PANICException,
                                  ReceivedUnexpectedDataException,
                                  MessageWasNotDeliveredException)
from test.utils.utils import (infinite_fn, connect_to_rabbit,
                              disconnect_from_rabbit,
                              delete_exchange_if_exists,
                              delete_queue_if_exists)


class TestAlertStore(unittest.TestCase):
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

        self.mongo_ip = env.DB_IP
        self.mongo_db = env.DB_NAME
        self.mongo_port = env.DB_PORT

        self.mongo = MongoApi(logger=self.dummy_logger.getChild(
                                  MongoApi.__name__),
                              db_name=self.mongo_db, host=self.mongo_ip,
                              port=self.mongo_port)

        self.redis_db = env.REDIS_DB
        self.redis_host = env.REDIS_IP
        self.redis_port = env.REDIS_PORT
        self.redis_namespace = env.UNIQUE_ALERTER_IDENTIFIER
        self.redis = RedisApi(self.dummy_logger, self.redis_db,
                              self.redis_host, self.redis_port, '',
                              self.redis_namespace,
                              self.connection_check_time_interval)

        self.test_store_name = 'store name'
        self.test_store = AlertStore(self.test_store_name,
                                     self.dummy_logger,
                                     self.rabbitmq)

        self.routing_key = 'heartbeat.worker'
        self.test_queue_name = 'test queue'

        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, 'direct', False,
                                       True, False, False)
        self.rabbitmq.queue_declare(ALERT_STORE_INPUT_QUEUE, False, True,
                                    False, False)
        self.rabbitmq.queue_bind(ALERT_STORE_INPUT_QUEUE,
                                 STORE_EXCHANGE,
                                 ALERT_STORE_INPUT_ROUTING_KEY)

        connect_to_rabbit(self.test_rabbit_manager)
        self.test_rabbit_manager.queue_declare(self.test_queue_name, False,
                                               True, False, False)
        self.test_rabbit_manager.queue_bind(self.test_queue_name,
                                            HEALTH_CHECK_EXCHANGE,
                                            self.routing_key)

        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)

        self.parent_id = 'test_parent_id'

        self.alert_id = 'test_alert_id'
        self.origin_id = 'test_origin_id'
        self.alert_name = 'test_alert'
        self.metric = 'system_is_down'
        self.severity = 'warning'
        self.message = 'alert message'

        self.alert_id_2 = 'test_origin_id_2'
        self.origin_id_2 = 'test_origin_id_2'
        self.alert_name_2 = 'test_alert_2'
        self.severity_2 = 'critical'
        self.message_2 = 'alert message 2'

        self.alert_id_3 = 'test_origin_id_3'
        self.origin_id_3 = 'test_origin_id_3'
        self.alert_name_3 = 'test_alert_3'
        self.severity_3 = 'info'
        self.message_3 = 'alert message 3'

        self.last_monitored = datetime(2012, 1, 1).timestamp()
        self.none = None

        self.alert_data_1 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id,
            'alert_code': {
                'name': self.alert_name
            },
            'severity': self.severity,
            'metric': self.metric,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_data_2 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_2,
            'alert_code': {
                'name': self.alert_name_2
            },
            'severity': self.severity_2,
            'metric': self.metric,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_data_3 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_3,
            'alert_code': {
                'name': self.alert_name_3
            },
            'severity': self.severity_3,
            'metric': self.metric,
            'message': self.message_3,
            'timestamp': self.last_monitored,
        }
        self.alert_data_key_error = {
            "result": {
                "data": {},
                "data2": {}
            }
        }
        self.alert_data_unexpected = {
            "unexpected": {}
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, ALERT_STORE_INPUT_QUEUE)
        delete_exchange_if_exists(self.rabbitmq, STORE_EXCHANGE)
        delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        connect_to_rabbit(self.test_rabbit_manager)
        delete_queue_if_exists(self.test_rabbit_manager, self.test_queue_name)
        disconnect_from_rabbit(self.test_rabbit_manager)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_rabbit_manager = None
        self.mongo.drop_collection(self.parent_id)
        self.mongo = None

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

    def test_mongo_property_returns_none_when_mongo_not_init(self) -> None:
        self.assertEqual(type(self.mongo), type(self.test_store.mongo))

    def test_redis_property_returns_redis_correctly(self) -> None:
        self.assertEqual(type(self.redis), type(self.test_store.redis))

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

            # Check whether the exchange has been creating by sending messages
            # to it. If this fails an exception is raised, hence the test fails.
            self.test_store.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE, routing_key=self.routing_key,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)
            # Check whether the exchange has been creating by sending messages
            # to it. If this fails an exception is raised, hence the test fails.
            self.test_store.rabbitmq.basic_publish_confirm(
                exchange=STORE_EXCHANGE,
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("KeyError", "self.alert_data_key_error "),
    ])
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_with_bad_data_does_raises_exceptions(
            self, mock_error, mock_bad_data, mock_send_hb, mock_ack) -> None:
        self.rabbitmq.connect()
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, "direct", False, True,
                                       False, False)
        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.alert_data_unexpected).encode()
            )
            self.assertRaises(eval(mock_error),
                              self.test_store._process_mongo_store,
                              eval(mock_bad_data))
            mock_ack.assert_called_once()
            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.alert.AlertStore._process_redis_store",
                autospec=True)
    @mock.patch("src.data_store.stores.alert.AlertStore._process_mongo_store",
                autospec=True)
    def test_process_data_sends_heartbeat_correctly(self,
                                                    mock_process_mongo_store,
                                                    mock_process_redis_store,
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
                routing_key=self.routing_key)

            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.alert_data_1).encode()
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
            mock_process_mongo_store.assert_called_once()
            mock_process_redis_store.assert_called_once()
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
                routing_key=self.routing_key)

            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(self.alert_data_unexpected).encode()
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
        self.test_store._process_mongo_store(self.alert_data_1)
        mock_update_one.assert_called_once()

    @mock.patch.object(RedisApi, "hset")
    def test_process_redis_store_calls_hset(self, mock_hset) -> None:
        self.test_store._process_redis_store(self.alert_data_1)
        mock_hset.assert_called_once()

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(MongoApi, "update_one")
    def test_process_mongo_store_calls_mongo_correctly(
            self, mock_system_data, mock_update_one) -> None:
        data = eval(mock_system_data)
        self.test_store._process_mongo_store(data)

        call_1 = call(
            data['parent_id'],
            {
                'doc_type': 'alert',
                'n_alerts': {'$lt': 1000}
            },
            {
                '$push': {
                    'alerts': {
                        'origin': data['origin_id'],
                        'alert_name': data['alert_code']['name'],
                        'severity': data['severity'],
                        'metric': data['metric'],
                        'message': data['message'],
                        'timestamp': str(data['timestamp']),
                    }
                },
                '$min': {'first': data['timestamp']},
                '$max': {'last': data['timestamp']},
                '$inc': {'n_alerts': 1},
            }
        )
        mock_update_one.assert_has_calls([call_1])

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(RedisApi, "hset")
    def test_process_redis_store_calls_redis_correctly(
            self, mock_system_data, mock_hset) -> None:
        data = eval(mock_system_data)
        self.test_store._process_redis_store(data)

        metric_data = {'severity': data['severity'],
                       'message': data['message']}
        key = data['origin_id']

        call_1 = call(Keys.get_hash_parent(data['parent_id']),
                      eval('Keys.get_alert_{}(key)'.format(data['metric'])),
                      json.dumps(metric_data))
        mock_hset.assert_has_calls([call_1])

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.alert.AlertStore._process_redis_store",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    @mock.patch.object(MongoApi, "update_one")
    def test_process_data_calls_mongo_correctly(
            self, mock_system_data, mock_update_one, mock_send_hb,
            mock_process_redis_store, mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = eval(mock_system_data)
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )

            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            call_1 = call(
                data['parent_id'],
                {
                    'doc_type': 'alert',
                    'n_alerts': {'$lt': 1000}
                },
                {
                    '$push': {
                        'alerts': {
                            'origin': data['origin_id'],
                            'alert_name': data['alert_code']['name'],
                            'severity': data['severity'],
                            'metric': data['metric'],
                            'message': data['message'],
                            'timestamp': str(data['timestamp']),
                        }
                    },
                    '$min': {'first': data['timestamp']},
                    '$max': {'last': data['timestamp']},
                    '$inc': {'n_alerts': 1},
                }
            )
            mock_update_one.assert_has_calls([call_1])
            mock_process_redis_store.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.alert.AlertStore._process_mongo_store",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    @mock.patch.object(RedisApi, "hset")
    def test_process_data_calls_redis_correctly(
            self, mock_system_data, mock_hset, mock_send_hb,
            mock_process_mongo_store, mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = eval(mock_system_data)
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )

            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            metric_data = {'severity': data['severity'],
                           'message': data['message']}
            key = data['origin_id']

            call_1 = call(Keys.get_hash_parent(data['parent_id']),
                          eval('Keys.get_alert_{}(key)'.format(data['metric'])),
                          json.dumps(metric_data))
            mock_hset.assert_has_calls([call_1])
            mock_process_mongo_store.assert_called_once()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    def test_process_mongo_store_mongo_stores_correctly(
            self, mock_system_data) -> None:

        data = eval(mock_system_data)
        self.test_store._process_mongo_store(data)

        documents = self.mongo.get_all(data['parent_id'])
        document = documents[0]
        expected = [
                'alert',
                1,
                str(data['origin_id']),
                str(data['alert_code']['name']),
                str(data['severity']),
                str(data['metric']),
                str(data['message']),
                str(data['timestamp'])
            ]
        actual = [
                document['doc_type'],
                document['n_alerts'],
                document['alerts'][0]['origin'],
                document['alerts'][0]['alert_name'],
                document['alerts'][0]['severity'],
                document['alerts'][0]['metric'],
                document['alerts'][0]['message'],
                document['alerts'][0]['timestamp']
            ]

        self.assertListEqual(expected, actual)

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    def test_process_redis_store_redis_stores_correctly(
            self, mock_system_data) -> None:

        data = eval(mock_system_data)
        self.test_store._process_redis_store(data)

        key = data['origin_id']

        stored_data = self.redis.hget(
            Keys.get_hash_parent(data['parent_id']),
            eval('Keys.get_alert_{}(key)'.format(data['metric'])))

        expected_data = {'severity': data['severity'],
                         'message': data['message']}

        self.assertEqual(expected_data, json.loads(stored_data))

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.alert.AlertStore._process_redis_store",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_results_stores_in_mongo_correctly(
            self, mock_system_data, mock_send_hb, mock_process_redis_store,
            mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = eval(mock_system_data)
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

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

            documents = self.mongo.get_all(data['parent_id'])
            document = documents[0]
            expected = [
                    'alert',
                    1,
                    str(data['origin_id']),
                    str(data['alert_code']['name']),
                    str(data['severity']),
                    str(data['message']),
                    str(data['timestamp'])
                ]
            actual = [
                    document['doc_type'],
                    document['n_alerts'],
                    document['alerts'][0]['origin'],
                    document['alerts'][0]['alert_name'],
                    document['alerts'][0]['severity'],
                    document['alerts'][0]['message'],
                    document['alerts'][0]['timestamp']
                ]

            self.assertListEqual(expected, actual)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ("self.alert_data_1", ),
        ("self.alert_data_2", ),
        ("self.alert_data_3", ),
    ])
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.alert.AlertStore._process_mongo_store",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_results_stores_in_redis_correctly(
            self, mock_system_data, mock_send_hb, mock_process_mongo_store,
            mock_ack) -> None:

        mock_ack.return_value = None
        try:
            self.test_store._initialise_rabbitmq()

            data = eval(mock_system_data)
            blocking_channel = self.test_store.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY)

            properties = pika.spec.BasicProperties()
            self.test_store._process_data(
                blocking_channel,
                method_chains,
                properties,
                json.dumps(data).encode()
            )

            mock_process_mongo_store.assert_called_once()
            mock_ack.assert_called_once()
            mock_send_hb.assert_called_once()

            key = data['origin_id']

            stored_data = self.redis.hget(
                Keys.get_hash_parent(data['parent_id']),
                eval('Keys.get_alert_{}(key)'.format(data['metric'])))

            expected_data = {'severity': data['severity'],
                             'message': data['message']}

            self.assertEqual(expected_data, json.loads(stored_data))
        except Exception as e:
            self.fail("Test failed: {}".format(e))
