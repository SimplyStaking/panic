import copy
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

from src.alerter.alerters.contract.chainlink import ChainlinkContractAlerter
from src.alerter.alerters.github import GithubAlerter
from src.alerter.alerters.network.cosmos import CosmosNetworkAlerter
from src.alerter.alerters.node.chainlink import ChainlinkNodeAlerter
from src.alerter.alerters.node.cosmos import CosmosNodeAlerter
from src.alerter.alerters.node.evm import EVMNodeAlerter
from src.alerter.alerters.system import SystemAlerter
from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis.redis_api import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.alert import AlertStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.data import (EXPIRE_METRICS, CHAIN_SOURCED_METRICS)
from src.utils.constants.rabbitmq import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                          ALERT_STORE_INPUT_QUEUE_NAME,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          ALERT_STORE_INPUT_ROUTING_KEY, TOPIC)
from src.utils.exceptions import (PANICException,
                                  MessageWasNotDeliveredException)
from test.test_utils.utils import (
    connect_to_rabbit, disconnect_from_rabbit, delete_exchange_if_exists,
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
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, TOPIC, False,
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
        self.parent_id2 = 'test_parent_id2'
        self.parent_id3 = 'test_parent_id3'
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

        self.alert_id_4 = 'test_alert_id_4'
        self.origin_id_4 = 'test_origin_id_4'
        self.alert_name_4 = 'test_alert_4'
        self.metric_4 = 'cl_node_is_down'
        self.severity_4 = 'info'
        self.message_4 = 'alert message 4'
        self.value_4 = 'alert_code_4'

        self.alert_id_5 = 'test_alert_id_5'
        self.origin_id_5 = 'test_origin_id_5'
        self.alert_name_5 = 'test_alert_5'
        self.metric_5 = 'cl_contract_price_feed_not_observed'
        self.severity_5 = 'info'
        self.message_5 = 'alert message 5'
        self.value_5 = 'alert_code_5'

        self.alert_id_6 = 'test_alert_id_6'
        self.origin_id_6 = 'test_origin_id_6'
        self.alert_name_6 = 'test_alert_6'
        self.metric_6 = 'evm_node_is_down'
        self.severity_6 = 'info'
        self.message_6 = 'alert message 6'
        self.value_6 = 'alert_code_6'

        self.metric_7 = 'cl_contract_no_synced_data_sources'

        self.alert_id_8 = 'test_alert_id_8'
        self.origin_id_8 = 'test_origin_id_8'
        self.alert_name_8 = 'test_alert_8'
        self.metric_8 = 'cosmos_node_slashed'
        self.severity_8 = 'info'
        self.message_8 = 'alert message 8'
        self.value_8 = 'alert_code_8'

        self.alert_id_9 = 'test_alert_id_9'
        self.origin_id_9 = 'test_origin_id_9'
        self.alert_name_9 = 'test_alert_9'
        self.metric_9 = 'cosmos_network_proposals_submitted'
        self.severity_9 = 'info'
        self.message_9 = 'alert message 9'
        self.value_9 = 'alert_code_9'

        self.last_monitored = datetime(2012, 1, 1).timestamp()
        self.none = None

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
            'parent_id': self.parent_id2,
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
        self.alert_data_4 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_4,
            'alert_code': {
                'name': self.alert_name_4,
                'code': self.value_4,
            },
            'severity': self.severity_4,
            'metric': self.metric_4,
            'message': self.message_4,
            'timestamp': self.last_monitored,
        }
        self.alert_data_4_1 = copy.deepcopy(self.alert_data_4)
        self.alert_data_4_1['parent_id'] = self.parent_id2

        self.alert_data_5 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_5,
            'alert_code': {
                'name': self.alert_name_5,
                'code': self.value_5,
            },
            'severity': self.severity_5,
            'metric': self.metric_5,
            'message': self.message_5,
            'timestamp': self.last_monitored,
            'alert_data': {
                'contract_proxy_address':
                    '0x5DcB78343780E1B1e578ae0590dc1e868792a435'
            }
        }
        self.alert_data_5_1 = copy.deepcopy(self.alert_data_5)
        self.alert_data_5_1['parent_id'] = self.parent_id2
        self.alert_data_5_1['alert_data']['contract_proxy_address'] = \
            '0xA5F7146D3cbB5a50Da36b8AC3857C48Ed3BF3bd9'
        self.alert_data_5_2 = copy.deepcopy(self.alert_data_5)
        self.alert_data_5_2['parent_id'] = self.parent_id3
        self.alert_data_5_2['origin_id'] = self.parent_id3
        self.alert_data_5_2['metric'] = self.metric_7
        del self.alert_data_5_2['alert_data']
        self.alert_data_6 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_6,
            'alert_code': {
                'name': self.alert_name_6,
                'code': self.value_6,
            },
            'severity': self.severity_6,
            'metric': self.metric_6,
            'message': self.message_6,
            'timestamp': self.last_monitored,
        }
        self.alert_data_6_1 = copy.deepcopy(self.alert_data_6)
        self.alert_data_6_1['parent_id'] = self.parent_id2

        self.alert_data_8 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_8,
            'alert_code': {
                'name': self.alert_name_8,
                'code': self.value_8,
            },
            'severity': self.severity_8,
            'metric': self.metric_8,
            'message': self.message_8,
            'timestamp': self.last_monitored,
        }
        self.alert_data_8_1 = copy.deepcopy(self.alert_data_8)
        self.alert_data_8_1['parent_id'] = self.parent_id2

        self.alert_data_9 = {
            'parent_id': self.parent_id,
            'origin_id': self.origin_id_9,
            'alert_code': {
                'name': self.alert_name_9,
                'code': self.value_9,
            },
            'severity': self.severity_9,
            'metric': self.metric_9,
            'message': self.message_9,
            'timestamp': self.last_monitored,
        }

        self.alert_data_9_1 = copy.deepcopy(self.alert_data_9)
        self.alert_data_9_1['parent_id'] = self.parent_id2

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

        self.alert_data_github_2 = copy.deepcopy(self.alert_data_1)
        self.alert_data_github_2['metric'] = 'github_cannot_access'

        self.alert_data_github_3 = copy.deepcopy(self.alert_data_2)
        self.alert_data_github_3['metric'] = 'github_release'

        """
        Internal alerts on component reset which are used to clear metrics from
        REDIS.
        """
        self.alert_internal_system_chain_1 = {
            'parent_id': self.parent_id,
            'origin_id': SystemAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_system_all_chains = {
            'parent_id': None,
            'origin_id': SystemAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_2,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_chainlink_1 = {
            'parent_id': self.parent_id,
            'origin_id': ChainlinkNodeAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_chainlink_all_chains = {
            'parent_id': None,
            'origin_id': ChainlinkNodeAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_2,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_cosmos_node = {
            'parent_id': self.parent_id,
            'origin_id': CosmosNodeAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_8,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_cosmos_node_all_chains = {
            'parent_id': None,
            'origin_id': CosmosNodeAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_8,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_cosmos_network = {
            'parent_id': self.parent_id,
            'origin_id': CosmosNetworkAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_9,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_cosmos_network_all_chains = {
            'parent_id': None,
            'origin_id': CosmosNetworkAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_9,
            'message': self.message_2,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_chainlink_contract_1 = {
            'parent_id': self.parent_id,
            'origin_id': ChainlinkContractAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_5,
            'message': self.message_5,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_chainlink_contract_3 = {
            'parent_id': self.parent_id3,
            'origin_id': ChainlinkContractAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_7,
            'message': self.message_5,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_chainlink_contract_all_chains = {
            'parent_id': None,
            'origin_id': ChainlinkContractAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_5,
            'message': self.message_5,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_evm_node_1 = {
            'parent_id': self.parent_id,
            'origin_id': EVMNodeAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_6,
            'message': self.message_6,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_evm_node_all_chains = {
            'parent_id': None,
            'origin_id': EVMNodeAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric_6,
            'message': self.message_6,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_github_chain_1 = {
            'parent_id': self.parent_id,
            'origin_id': GithubAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message,
            'timestamp': self.last_monitored,
        }
        self.alert_internal_github_all_chains = {
            'parent_id': None,
            'origin_id': GithubAlerter.__name__,
            'alert_code': {
                'name': 'internal_alert_1',
                'code': 'internal_alert_1',
            },
            'severity': self.internal,
            'metric': self.metric,
            'message': self.message_2,
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
                json.dumps(self.alert_data_unexpected)
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
                json.dumps(self.alert_data_1)
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
                json.dumps(self.alert_data_unexpected)
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
    def test_process_redis_store_calls_hset_on_normal_alerts(
            self, mock_hset) -> None:
        self.test_store._process_redis_store(self.alert_data_1)
        mock_hset.assert_called_once()

    @parameterized.expand([
        ("self.alert_data_1",),
        ("self.alert_data_2",),
        ("self.alert_data_3",),
        ("self.alert_data_8",),
        ("self.alert_data_9",),
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
                        'timestamp': data['timestamp'],
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
        ("self.alert_data_8",),
        ("self.alert_data_9",),
    ])
    @mock.patch.object(RedisApi, "hset")
    def test_process_redis_store_calls_redis_correctly_storing_metrics(
            self, mock_system_data, mock_hset) -> None:
        data = eval(mock_system_data)
        self.test_store._process_redis_store(data)

        # testing if the 'expiry' metric data is processed accordingly if the
        # metric is recognized to be within the list of EXPIRE_METRICS
        if data['metric'] in EXPIRE_METRICS:
            expiry = data['timestamp'] + 600
        else:
            expiry = None

        metric_data = {'severity': data['severity'],
                       'message': data['message'],
                       'metric': data['metric'],
                       'timestamp': data['timestamp'],
                       'expiry': expiry}
        key = data['origin_id']

        if data['metric'] in CHAIN_SOURCED_METRICS:
            call_1 = call(Keys.get_hash_parent(data['parent_id']),
                          eval('Keys.get_alert_{}()'.format(data['metric'])),
                          json.dumps(metric_data))
        else:
            call_1 = call(Keys.get_hash_parent(data['parent_id']),
                          eval('Keys.get_alert_{}(key)'.format(data['metric'])),
                          json.dumps(metric_data))

        mock_hset.assert_has_calls([call_1])

    def test_process_redis_store_system_removes_all_chains_sys_metrics_pid_none(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_1)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_1['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_1['origin_id'])".format(
                self.alert_data_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_2)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_2['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_2['origin_id'])".format(
                self.alert_data_2['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(self.alert_data_3)
        chain_hash_3 = Keys.get_hash_parent(self.alert_data_3['parent_id'])
        metric_key_3 = eval(
            "Keys.get_alert_{}(self.alert_data_3['origin_id'])".format(
                self.alert_data_3['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_3, metric_key_3))

        self.test_store._process_redis_store(
            self.alert_internal_system_all_chains)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertFalse(self.redis.hexists(chain_hash_2, metric_key_2))
        self.assertFalse(self.redis.hexists(chain_hash_3, metric_key_3))

    def test_process_redis_store_system_removes_all_system_metrics_for_chain(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_1)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_1['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_1['origin_id'])".format(
                self.alert_data_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_2)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_2['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_2['origin_id'])".format(
                self.alert_data_2['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(self.alert_data_3)
        chain_hash_3 = Keys.get_hash_parent(self.alert_data_3['parent_id'])
        metric_key_3 = eval(
            "Keys.get_alert_{}(self.alert_data_3['origin_id'])".format(
                self.alert_data_3['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_3, metric_key_3))

        self.test_store._process_redis_store(
            self.alert_internal_system_chain_1)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))
        self.assertFalse(self.redis.hexists(chain_hash_3, metric_key_3))

    def test_process_redis_store_chainlink_removes_all_chainlink_metrics_for_all_chains(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_4)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_4['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_4['origin_id'])".format(
                self.alert_data_4['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_4_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_4_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_4_1['origin_id'])".format(
                self.alert_data_4_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_chainlink_all_chains)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertFalse(self.redis.hexists(chain_hash_2, metric_key_2))

    def test_process_redis_store_chainlink_removes_all_chainlink_metrics_for_one_chain(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_4)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_4['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_4['origin_id'])".format(
                self.alert_data_4['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_4_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_4_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_4_1['origin_id'])".format(
                self.alert_data_4_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_chainlink_1)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

    def test_process_redis_store_cosmos_removes_all_cosmos_metrics_for_all_chains(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_8)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_8['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_8['origin_id'])".format(
                self.alert_data_8['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_8_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_8_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_8_1['origin_id'])".format(
                self.alert_data_8_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_cosmos_node_all_chains)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertFalse(self.redis.hexists(chain_hash_2, metric_key_2))

    def test_process_redis_store_cosmos_removes_all_cosmos_metrics_for_one_chain(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_8)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_8['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_8['origin_id'])".format(
                self.alert_data_8['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_8_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_8_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_8_1['origin_id'])".format(
                self.alert_data_8_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_cosmos_node)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

    def test_process_redis_store_cos_net_removes_all_cos_net_metrics_for_all_chains(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_9)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_9['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}()".format(
                self.alert_data_9['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_9_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_9_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}()".format(
                self.alert_data_9_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_cosmos_network_all_chains)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertFalse(self.redis.hexists(chain_hash_2, metric_key_2))

    def test_process_redis_store_cos_net_removes_all_cos_net_metrics_for_one_chain(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_9)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_9['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}()".format(
                self.alert_data_9['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_9_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_9_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}()".format(
                self.alert_data_9_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_cosmos_network)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

    def test_process_redis_store_cl_contract_removes_all_cl_contracts_metrics_for_all_chains(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_5)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_5['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_5['origin_id'], "
            "self.alert_data_5['alert_data']['contract_proxy_address'])".
                format(self.alert_data_5['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_5_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_5_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_5_1['origin_id'], "
            "self.alert_data_5_1['alert_data']['contract_proxy_address'])".
                format(self.alert_data_5_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(self.alert_data_5_2)
        chain_hash_3 = Keys.get_hash_parent(self.alert_data_5_2['parent_id'])
        metric_key_3 = eval(
            "Keys.get_alert_{}()".format(
                self.alert_data_5_2['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_3, metric_key_3))

        self.test_store._process_redis_store(
            self.alert_internal_chainlink_contract_all_chains)
        self.test_store._process_redis_store(
            self.alert_internal_chainlink_contract_3)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertFalse(self.redis.hexists(chain_hash_2, metric_key_2))
        self.assertFalse(self.redis.hexists(chain_hash_3, metric_key_3))

    def test_process_redis_store_cl_contract_removes_all_cl_contract_metrics_for_one_chain(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_5)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_5['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_5['origin_id'], "
            "self.alert_data_5['alert_data']['contract_proxy_address'])".
                format(self.alert_data_5['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_5_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_5_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_5_1['origin_id'], "
            "self.alert_data_5_1['alert_data']['contract_proxy_address'])".
                format(self.alert_data_5_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(self.alert_data_5_2)
        chain_hash_3 = Keys.get_hash_parent(self.alert_data_5_2['parent_id'])
        metric_key_3 = eval(
            "Keys.get_alert_{}()".format(
                self.alert_data_5_2['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_3, metric_key_3))

        self.test_store._process_redis_store(
            self.alert_internal_chainlink_contract_1)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))
        self.assertTrue(self.redis.hexists(chain_hash_3, metric_key_3))

    def test_process_redis_store_evm_node_removes_all_evm_node_metrics_for_all_chains(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_6)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_6['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_6['origin_id'])".
                format(self.alert_data_6['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_6_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_6_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_6_1['origin_id'])".
                format(self.alert_data_6_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_evm_node_all_chains)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertFalse(self.redis.hexists(chain_hash_2, metric_key_2))

    def test_process_redis_store_evm_node_removes_all_evm_node_metrics_for_one_chain(
            self) -> None:
        # First set metrics for different chains and check that they were set
        # in Redis.
        self.test_store._process_redis_store(self.alert_data_6)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_6['parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_6['origin_id'])".
                format(self.alert_data_6['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_6_1)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_6_1['parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_6_1['origin_id'])".
                format(self.alert_data_6_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(
            self.alert_internal_evm_node_1)

        self.assertFalse(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

    @parameterized.expand([
        ('self.alert_internal_github_all_chains',),
        ('self.alert_internal_github_chain_1',),
    ])
    def test_process_redis_store_github_removes_all_chains_github_metrics(
            self, internal_alert) -> None:
        # For github we will show that the value of the parent_id is irrelevant,
        # we always delete all github metrics for all chains
        self.test_store._process_redis_store(self.alert_data_github_1)
        chain_hash_1 = Keys.get_hash_parent(self.alert_data_github_1[
                                                'parent_id'])
        metric_key_1 = eval(
            "Keys.get_alert_{}(self.alert_data_github_1['origin_id'])".format(
                self.alert_data_github_1['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))

        self.test_store._process_redis_store(self.alert_data_github_2)
        chain_hash_2 = Keys.get_hash_parent(self.alert_data_github_2[
                                                'parent_id'])
        metric_key_2 = eval(
            "Keys.get_alert_{}(self.alert_data_github_2['origin_id'])".format(
                self.alert_data_github_2['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_2, metric_key_2))

        self.test_store._process_redis_store(self.alert_data_github_3)
        chain_hash_3 = Keys.get_hash_parent(self.alert_data_github_3[
                                                'parent_id'])
        metric_key_3 = eval(
            "Keys.get_alert_{}(self.alert_data_github_3['origin_id'])".format(
                self.alert_data_github_3['metric']))
        self.assertTrue(self.redis.hexists(chain_hash_3, metric_key_3))

        eval_internal_alert = eval(internal_alert)
        self.test_store._process_redis_store(eval_internal_alert)

        self.assertTrue(self.redis.hexists(chain_hash_1, metric_key_1))
        self.assertFalse(self.redis.hexists(chain_hash_2, metric_key_2))
        self.assertTrue(self.redis.hexists(chain_hash_3, metric_key_3))

    @mock.patch.object(AlertStore, "_process_mongo_store")
    @mock.patch.object(AlertStore, "_process_redis_store")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_calls_process_redis_and_mongo_store_correctly(
            self, mock_ack, mock_proc_redis, mock_proc_mongo) -> None:
        mock_ack.return_value = None
        mock_proc_redis.return_value = None
        mock_proc_mongo.return_value = None

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=ALERT_STORE_INPUT_ROUTING_KEY)
        body = json.dumps(self.alert_data_1)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_proc_redis.assert_called_once()
        mock_proc_mongo.assert_called_once()
        mock_ack.assert_called_once()

    @mock.patch.object(AlertStore, "_send_heartbeat")
    @mock.patch.object(AlertStore, "_process_mongo_store")
    @mock.patch.object(AlertStore, "_process_redis_store")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_does_not_send_hb_if_processing_error(
            self, mock_ack, mock_proc_redis, mock_proc_mongo,
            mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_proc_redis.return_value = None
        mock_proc_mongo.side_effect = self.test_exception
        mock_send_hb.return_value = None

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=ALERT_STORE_INPUT_ROUTING_KEY)
        body = json.dumps(self.alert_data_1)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_ack.assert_called_once()
        mock_send_hb.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch.object(AlertStore, "_send_heartbeat")
    @mock.patch.object(AlertStore, "_process_mongo_store")
    @mock.patch.object(AlertStore, "_process_redis_store")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_sends_hb_if_no_processing_errors(
            self, mock_ack, mock_proc_redis, mock_proc_mongo,
            mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_proc_redis.return_value = None
        mock_proc_mongo.return_value = None
        mock_send_hb.return_value = None

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=ALERT_STORE_INPUT_ROUTING_KEY)
        body = json.dumps(self.alert_data_1)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        test_hb = {
            'component_name': self.test_store_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        mock_ack.assert_called_once()
        mock_send_hb.assert_called_once_with(test_hb)

    @mock.patch.object(AlertStore, "_send_heartbeat")
    @mock.patch.object(AlertStore, "_process_mongo_store")
    @mock.patch.object(AlertStore, "_process_redis_store")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_does_not_raise_msg_not_del_exception(
            self, mock_ack, mock_proc_redis, mock_proc_mongo,
            mock_send_hb) -> None:
        mock_ack.return_value = None
        mock_proc_redis.return_value = None
        mock_proc_mongo.return_value = None
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test')

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=ALERT_STORE_INPUT_ROUTING_KEY)
        body = json.dumps(self.alert_data_1)
        properties = pika.spec.BasicProperties()

        try:
            self.test_store._process_data(blocking_channel, method, properties,
                                          body)
        except MessageWasNotDeliveredException as e:
            self.fail('{} was not supposed to be raised.'.format(e))

        mock_ack.assert_called_once()

    @parameterized.expand([
        (pika.exceptions.AMQPConnectionError,
         pika.exceptions.AMQPConnectionError('test'),),
        (pika.exceptions.AMQPChannelError,
         pika.exceptions.AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(AlertStore, "_process_mongo_store")
    @mock.patch.object(AlertStore, "_process_redis_store")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(AlertStore, "_send_heartbeat")
    def test_process_data_raises_unrecognized_error_if_raised_by_send_hb(
            self, exception_class, exception_instance, mock_send_hb, mock_ack,
            mock_proc_redis, mock_proc_mongo) -> None:
        mock_ack.return_value = None
        mock_proc_redis.return_value = None
        mock_proc_mongo.return_value = None
        mock_send_hb.side_effect = exception_instance

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=ALERT_STORE_INPUT_ROUTING_KEY)
        body = json.dumps(self.alert_data_1)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_class, self.test_store._process_data,
                          blocking_channel, method, properties, body)
        mock_ack.assert_called_once()
