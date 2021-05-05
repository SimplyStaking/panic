import json
import logging
import unittest
import copy
from datetime import datetime
from datetime import timedelta
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.alerter.managers.github import GithubAlerterManager
from src.alerter.managers.system import SystemAlertersManager
from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis.redis_api import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.alert import AlertStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 ALERT_STORE_INPUT_QUEUE_NAME,
                                 HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                 ALERT_STORE_INPUT_ROUTING_KEY)
from src.utils.exceptions import (PANICException)
from test.utils.utils import (connect_to_rabbit,
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
            MongoApi.__name__), db_name=self.mongo_db, host=self.mongo_ip,
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

        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.test_queue_name = 'test queue'

        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.rabbitmq.queue_declare(ALERT_STORE_INPUT_QUEUE_NAME, False, True,
                                    False, False)
        self.rabbitmq.queue_bind(ALERT_STORE_INPUT_QUEUE_NAME, STORE_EXCHANGE,
                                 ALERT_STORE_INPUT_ROUTING_KEY)

        connect_to_rabbit(self.test_rabbit_manager)
        self.test_rabbit_manager.queue_declare(self.test_queue_name, False,
                                               True, False, False)
        self.test_rabbit_manager.queue_bind(self.test_queue_name,
                                            HEALTH_CHECK_EXCHANGE,
                                            self.heartbeat_routing_key)

        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)

        self.info = 'INFO'
        self.warning = 'WARNING'
        self.critical = 'CRITICAL'
        self.internal = 'INTERNAL'

        self.parent_id = 'test_parent_id'
        self.alert_id = 'test_alert_id'
        self.origin_id = 'test_origin_id'
        self.alert_name = 'test_alert'
        self.metric = 'system_is_down'
        self.severity = 'warning'
        self.message = 'alert message'
        self.value = 'alert_code_1'

        self.alert_id_2 = 'test_alert_id_2'
        self.origin_id_2 = 'test_origin_id_2'
        self.alert_name_2 = 'test_alert_2'
        self.metric_2 = 'system_cpu_usage'
        self.severity_2 = 'critical'
        self.message_2 = 'alert message 2'
        self.value_2 = 'alert_code_2'

        self.alert_id_3 = 'test_alert_id_3'
        self.origin_id_3 = 'test_origin_id_3'
        self.alert_name_3 = 'test_alert_3'
        self.metric_3 = 'system_storage_usage'
        self.severity_3 = 'info'
        self.message_3 = 'alert message 3'
        self.value_3 = 'alert_code_3'

        self.last_monitored = datetime(2012, 1, 1).timestamp()
        self.none = None

        self.system_alert_metrics = ['open_file_descriptors',
                                     'system_cpu_usage',
                                     'system_storage_usage',
                                     'system_ram_usage',
                                     'system_is_down',
                                     'invalid_url',
                                     'metric_not_found']
        # We do not want to reset `github_release` for Github metrics as we
        # will lose the pending upgrades
        self.github_alert_metrics = ['cannot_access_github']

        # Normal alerts
        self.alert_data_1 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id,
            'alert_code': {
                'name': self.alert_name,
                'code': self.value,
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
                'name': self.alert_name_2,
                'code': self.value_2,
            },
            'severity': self.severity_2,
            'metric': self.metric_2,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_data_3 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_3,
            'alert_code': {
                'name': self.alert_name_3,
                'code': self.value_3,
            },
            'severity': self.severity_3,
            'metric': self.metric_3,
            'message': self.message_3,
            'timestamp': self.last_monitored,
        }

        # Bad data
        self.alert_data_key_error = {
            "result": {
                "data": {},
                "data2": {}
            }
        }
        self.alert_data_unexpected = {
            "unexpected": {}
        }

        # Alerts copied for GITHUB metric values, these are used to test
        # Metric deletion on startup
        self.alert_data_github_1 = copy.deepcopy(self.alert_data_1)
        self.alert_data_github_1['metric'] = 'github_release'

        self.alert_data_github_2 = copy.deepcopy(self.alert_data_2)
        self.alert_data_github_2['metric'] = 'cannot_access_github'

        """
        Internal alerts on startup which are used to clear metrics from
        REDIS. Note: we only care about alert_code.code and severity for
        this alert.

        internal_alert_1 = ComponentReset: reset data for one chain
        internal_alert_2 = ComponentResetAll: reset data for all chains
        """
        self.alert_internal_system_1 = {
            'parent_id': self.parent_id,
            'origin_id': SystemAlertersManager.__name__,
            'alert_code': {
                'name': 'internal_alert_2',
                'code': 'internal_alert_2',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_system_2 = {
            'parent_id': self.parent_id,
            'origin_id': SystemAlertersManager.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_2,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_system_3 = {
            'parent_id': self.parent_id,
            'origin_id': SystemAlertersManager.__name__,
            'alert_code': {
                'name': 'internal_alert_2',
                'code': 'internal_alert_2',
            },
            'severity': self.internal,
            'metric': self.metric_3,
            'message': self.message_3,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_github_1 = {
            'parent_id': self.parent_id,
            'origin_id': GithubAlerterManager.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_github_2 = {
            'parent_id': self.parent_id,
            'origin_id': GithubAlerterManager.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_github_3 = {
            'parent_id': self.parent_id,
            'origin_id': GithubAlerterManager.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message_3,
            'timestamp': self.last_monitored,
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, ALERT_STORE_INPUT_QUEUE_NAME)
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
        self.redis.delete_all_unsafe()
        self.redis = None
        self.test_store._redis = None
        self.mongo.drop_collection(self.parent_id)
        self.mongo = None
        self.test_store._mongo = None
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

    def test_mongo_property_returns_mongo(self) -> None:
        self.assertEqual(type(self.mongo), type(self.test_store.mongo))

    def test_redis_property_returns_redis_correctly(self) -> None:
        self.assertEqual(type(self.redis), type(self.test_store.redis))

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        try:
            # To make sure that the exchanges have not already been declared
            self.rabbitmq.connect()
            self.rabbitmq.queue_delete(ALERT_STORE_INPUT_QUEUE_NAME)
            self.test_rabbit_manager.queue_delete(self.test_queue_name)
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
                routing_key=ALERT_STORE_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=False)

            # Re-declare queue to get the number of messages
            res = self.test_store.rabbitmq.queue_declare(
                ALERT_STORE_INPUT_QUEUE_NAME, False, True, False, False)

            self.assertEqual(1, res.method.message_count)
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
                routing_key=self.heartbeat_routing_key)

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
                routing_key=self.heartbeat_routing_key)

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
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
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
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
    ])
    @mock.patch.object(RedisApi, "hset")
    def test_process_redis_store_calls_redis_correctly_storing_metrics(
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
        ("self.alert_internal_system_1",),
        ("self.alert_internal_system_2",),
        ("self.alert_internal_system_3",),
    ])
    @mock.patch.object(RedisApi, "get_keys_unsafe")
    @mock.patch.object(RedisApi, "hkeys")
    @mock.patch.object(RedisApi, "hremove")
    @mock.patch.object(RedisApi, "hexists")
    def test_process_redis_store_system_removes_metrics_if_they_exist(
            self, mock_data, mock_hexists, mock_hremove, mock_hkeys,
            mock_get_keys_unsafe) -> None:

        mock_hexists.return_value = True

        # Create data needed for test
        data = eval(mock_data)
        key = data['origin_id']
        calls = []
        hkeys_list = []

        # The return value is taken from alert in this test, but it in reality
        # we need to query redis for it.
        mock_get_keys_unsafe.return_value = [Keys.get_hash_parent(
            data['parent_id'])]
        # Create the expected calls which will happen
        for metric_name in self.system_alert_metrics:
            call_1 = call(Keys.get_hash_parent(data['parent_id']),
                          eval('Keys.get_alert_{}(key)'.format(metric_name)))
            calls.append(call_1)
            hkeys_list.append(eval('Keys.get_alert_{}(key)'.format(
                metric_name)))

        mock_hkeys.return_value = hkeys_list

        # Process the data
        self.test_store._process_redis_store(data)

        mock_hexists.assert_has_calls(calls)
        mock_hremove.assert_has_calls(calls)

    @parameterized.expand([
        ("self.alert_internal_github_1",),
        ("self.alert_internal_github_2",),
        ("self.alert_internal_github_3",),
    ])
    @mock.patch.object(RedisApi, "get_keys_unsafe")
    @mock.patch.object(RedisApi, "hkeys")
    @mock.patch.object(RedisApi, "hremove")
    @mock.patch.object(RedisApi, "hexists")
    def test_process_redis_store_github_removes_metrics_if_they_exist(
            self, mock_data, mock_hexists, mock_hremove, mock_hkeys,
            mock_get_keys_unsafe) -> None:

        mock_hexists.return_value = True

        # Create data needed for test
        data = eval(mock_data)
        key = data['origin_id']
        calls = []
        hkeys_list = []

        # The return value is taken from alert in this test, but it in reality
        # we need to query redis for it.
        mock_get_keys_unsafe.return_value = [Keys.get_hash_parent(
            data['parent_id'])]

        for metric_name in self.github_alert_metrics:
            call_1 = call(Keys.get_hash_parent(data['parent_id']),
                          eval('Keys.get_alert_{}(key)'.format(metric_name)))
            calls.append(call_1)
            hkeys_list.append(eval('Keys.get_alert_{}(key)'.format(
                metric_name)))

        mock_hkeys.return_value = hkeys_list

        # Process the data
        self.test_store._process_redis_store(data)

        mock_hexists.assert_has_calls(calls)
        mock_hremove.assert_has_calls(calls)

    @parameterized.expand([
        ("self.alert_internal_system_1",),
        ("self.alert_internal_system_2",),
        ("self.alert_internal_system_3",),
    ])
    @mock.patch.object(RedisApi, "get_keys_unsafe")
    @mock.patch.object(RedisApi, "hkeys")
    @mock.patch.object(RedisApi, "hremove")
    @mock.patch.object(RedisApi, "hexists")
    def test_process_redis_store_system_do_not_remove_metrics_if_they_do_not_exists(
            self, mock_data, mock_hexists, mock_hremove, mock_hkeys,
            mock_get_keys_unsafe) -> None:

        mock_hexists.return_value = False

        # Create data needed for test
        data = eval(mock_data)
        key = data['origin_id']
        calls = []
        hkeys_list = []

        # The return value is taken from alert in this test, but it in reality
        # we need to query redis for it.
        mock_get_keys_unsafe.return_value = [Keys.get_hash_parent(
            data['parent_id'])]

        for metric_name in self.system_alert_metrics:
            call_1 = call(Keys.get_hash_parent(data['parent_id']),
                          eval('Keys.get_alert_{}(key)'.format(metric_name)))
            calls.append(call_1)
            hkeys_list.append(eval('Keys.get_alert_{}(key)'.format(
                metric_name)))

        mock_hkeys.return_value = hkeys_list

        self.test_store._process_redis_store(data)

        mock_hexists.assert_has_calls(calls)
        mock_hremove.assert_not_called()

    @parameterized.expand([
        ("self.alert_internal_github_1",),
        ("self.alert_internal_github_2",),
        ("self.alert_internal_github_3",),
    ])
    @mock.patch.object(RedisApi, "get_keys_unsafe")
    @mock.patch.object(RedisApi, "hkeys")
    @mock.patch.object(RedisApi, "hremove")
    @mock.patch.object(RedisApi, "hexists")
    def test_process_redis_store_github_do_not_remove_metrics_if_they_do_not_exists(
            self, mock_data, mock_hexists, mock_hremove, mock_hkeys,
            mock_get_keys_unsafe) -> None:

        mock_hexists.return_value = False

        # Create data needed for test
        data = eval(mock_data)
        key = data['origin_id']
        calls = []
        hkeys_list = []

        # The return value is taken from alert in this test, but it in reality
        # we need to query redis for it.
        mock_get_keys_unsafe.return_value = [Keys.get_hash_parent(
            data['parent_id'])]

        for metric_name in self.github_alert_metrics:
            call_1 = call(Keys.get_hash_parent(data['parent_id']),
                          eval('Keys.get_alert_{}(key)'.format(metric_name)))
            calls.append(call_1)
            hkeys_list.append(eval('Keys.get_alert_{}(key)'.format(
                metric_name)))

        mock_hkeys.return_value = hkeys_list

        self.test_store._process_redis_store(data)

        mock_hexists.assert_has_calls(calls)
        mock_hremove.assert_not_called()

    @parameterized.expand([
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
    ])
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
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
    ])
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
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
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
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
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
        ("self.alert_data_1", "self.alert_internal_system_1",),
        ("self.alert_data_2", "self.alert_internal_system_2",),
        ("self.alert_data_3", "self.alert_internal_system_3",),
    ])
    def test_process_redis_store_system_redis_stores_and_deletes_correctly(
            self, mock_system_data, mock_internal_alert) -> None:

        # First store the data
        system_data = eval(mock_system_data)
        key = system_data['origin_id']
        self.test_store._process_redis_store(system_data)

        # Check if the data exists inside REDIS
        self.assertTrue(self.redis.hexists(
            Keys.get_hash_parent(system_data['parent_id']),
            eval('Keys.get_alert_{}(key)'.format(system_data['metric']))
        ))

        stored_data = self.redis.hget(
            Keys.get_hash_parent(system_data['parent_id']),
            eval('Keys.get_alert_{}(key)'.format(system_data['metric'])))

        expected_data = {'severity': system_data['severity'],
                         'message': system_data['message']}

        self.assertEqual(expected_data, json.loads(stored_data))

        # Send the internal alert to delete the data
        internal_data = eval(mock_internal_alert)
        self.test_store._process_redis_store(internal_data)

        # Check if the data is removed from REDIS
        self.assertFalse(self.redis.hexists(
            Keys.get_hash_parent(system_data['parent_id']),
            eval('Keys.get_alert_{}(key)'.format(system_data['metric']))
        ))

    @parameterized.expand([
        ("self.alert_data_github_2", "self.alert_internal_github_1",),
        ("self.alert_data_github_2", "self.alert_internal_github_3",),
    ])
    def test_process_redis_store_github_redis_stores_and_deletes_correctly(
            self, mock_github_data, mock_internal_alert) -> None:

        # First store the data
        github_data = eval(mock_github_data)
        key = github_data['origin_id']
        self.test_store._process_redis_store(github_data)

        # Check if the data exists inside REDIS
        self.assertTrue(self.redis.hexists(
            Keys.get_hash_parent(github_data['parent_id']),
            eval('Keys.get_alert_{}(key)'.format(github_data['metric']))
        ))

        stored_data = self.redis.hget(
            Keys.get_hash_parent(github_data['parent_id']),
            eval('Keys.get_alert_{}(key)'.format(github_data['metric'])))

        expected_data = {'severity': github_data['severity'],
                         'message': github_data['message']}

        self.assertEqual(expected_data, json.loads(stored_data))

        # Send the internal alert to delete the data
        internal_data = eval(mock_internal_alert)
        self.test_store._process_redis_store(internal_data)

        # Check if the data is removed from REDIS
        self.assertFalse(self.redis.hexists(
            Keys.get_hash_parent(github_data['parent_id']),
            eval('Keys.get_alert_{}(key)'.format(github_data['metric']))
        ))

    @parameterized.expand([
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
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
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
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
