import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis import RedisApi, Keys
from src.data_store.stores.node.cosmos import CosmosNodeStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.cosmos import BOND_STATUS_BONDED
from src.utils.constants.mongo import REPLICA_SET_HOSTS, REPLICA_SET_NAME
from src.utils.constants.rabbitmq import (
    STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE, HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    COSMOS_NODE_STORE_INPUT_QUEUE_NAME)
from src.utils.exceptions import (PANICException, NodeIsDownException,
                                  MessageWasNotDeliveredException)
from src.utils.types import convert_to_int, convert_to_float, str_to_bool
from test.test_utils.utils import (connect_to_rabbit,
                                   disconnect_from_rabbit,
                                   delete_exchange_if_exists,
                                   delete_queue_if_exists)


class TestCosmosNodeStore(unittest.TestCase):
    def setUp(self) -> None:
        # Dummy objects
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)

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
        self.redis = RedisApi(self.dummy_logger, self.redis_db,
                              self.redis_host, self.redis_port, '',
                              self.redis_namespace,
                              self.connection_check_time_interval)

        # Mongo instance        
        self.mongo_db = env.DB_NAME
        self.mongo_port = env.DB_PORT
        self.mongo = MongoApi(logger=self.dummy_logger.getChild(
            MongoApi.__name__),
            db_name=self.mongo_db, host=REPLICA_SET_HOSTS,
            replicaSet=REPLICA_SET_NAME)

        # Test store object
        self.test_store_name = 'store name'
        self.test_store = CosmosNodeStore(self.test_store_name,
                                          self.dummy_logger, self.rabbitmq)

        # Dummy data
        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.input_routing_key = COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY
        self.test_queue_name = 'test queue'
        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)
        self.node_id = 'test_node_id'
        self.parent_id = 'test_parent_id'
        self.node_name = 'test_node'
        self.pad = 10
        self.downtime_exception = NodeIsDownException(self.node_name)
        self.is_validator = True
        self.operator_address = 'test_address'

        # Some metrics
        self.test_went_down_at_prometheus = None
        self.test_current_height = 10000
        self.test_voting_power = 99

        self.test_went_down_at_cosmos_rest = None
        self.test_bond_status = BOND_STATUS_BONDED
        self.test_jailed = False

        self.test_went_down_at_tendermint_rpc = None
        self.test_slashed = {
            'slashed': True,
            'amount_map': {'40': 56.6}
        }
        self.test_missed_blocks = {
            'total_count': 3,
            'missed_heights': [47, 46, 45]
        }
        self.test_is_syncing = False

        self.test_last_monitored_prometheus = datetime(2012, 1, 1).timestamp()
        self.test_last_monitored_cosmos_rest = datetime(2012, 1, 1).timestamp()
        self.test_last_monitored_tendermint_rpc = \
            datetime(2012, 1, 1).timestamp()
        self.node_data_optionals_enabled = {
            "prometheus": {
                "result": {
                    "meta_data": {
                        "node_name": self.node_name,
                        "node_id": self.node_id,
                        "node_parent_id": self.parent_id,
                        "last_monitored": self.test_last_monitored_prometheus,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address
                    },
                    "data": {
                        "went_down_at": self.test_went_down_at_prometheus,
                        "current_height": self.test_current_height,
                        "voting_power": self.test_voting_power,
                    }
                }
            },
            "cosmos_rest": {
                "result": {
                    "meta_data": {
                        "node_name": self.node_name,
                        "node_id": self.node_id,
                        "node_parent_id": self.parent_id,
                        "last_monitored": self.test_last_monitored_cosmos_rest,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address
                    },
                    "data": {
                        "went_down_at": self.test_went_down_at_cosmos_rest,
                        "bond_status": self.test_bond_status,
                        "jailed": self.test_jailed
                    }
                }
            },
            "tendermint_rpc": {
                "result": {
                    "meta_data": {
                        "node_name": self.node_name,
                        "node_id": self.node_id,
                        "node_parent_id": self.parent_id,
                        "last_monitored":
                            self.test_last_monitored_tendermint_rpc,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address
                    },
                    "data": {
                        "went_down_at": self.test_went_down_at_tendermint_rpc,
                        "slashed": self.test_slashed,
                        "missed_blocks": self.test_missed_blocks,
                        "is_syncing": self.test_is_syncing
                    }
                }
            }
        }

        self.node_data_down_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address,
                        'time': self.test_last_monitored_prometheus
                    },
                    'message': self.downtime_exception.message,
                    'code': self.downtime_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored_prometheus
                    }
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address,
                        'time': self.test_last_monitored_cosmos_rest
                    },
                    'message': self.downtime_exception.message,
                    'code': self.downtime_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored_cosmos_rest
                    }
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address,
                        'time': self.test_last_monitored_tendermint_rpc
                    },
                    'message': self.downtime_exception.message,
                    'code': self.downtime_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored_tendermint_rpc
                    }
                }
            },
        }

        self.node_data_non_down_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address,
                        'time': self.test_last_monitored_prometheus
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code
                }
            },
            'cosmos_rest': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address,
                        'time': self.test_last_monitored_cosmos_rest
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code
                }
            },
            'tendermint_rpc': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        "is_validator": self.is_validator,
                        "operator_address": self.operator_address,
                        'time': self.test_last_monitored_tendermint_rpc
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code
                }
            },
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq,
                               COSMOS_NODE_STORE_INPUT_QUEUE_NAME)
        delete_queue_if_exists(self.rabbitmq, self.test_queue_name)
        delete_exchange_if_exists(self.rabbitmq, STORE_EXCHANGE)
        delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        self.redis.delete_all_unsafe()
        self.mongo.drop_collection(self.parent_id)
        self.redis = None
        self.rabbitmq = None
        self.mongo = None
        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.test_exception = None
        self.downtime_exception = None
        self.test_store._mongo = None
        self.test_store._redis = None
        self.test_store = None

    def test__str__returns_name_correctly(self) -> None:
        self.assertEqual(self.test_store_name, str(self.test_store))

    def test_name_returns_store_name(self) -> None:
        self.assertEqual(self.test_store_name, self.test_store.name)

    def test_mongo_db_returns_mongo_db(self) -> None:
        self.assertEqual(self.mongo_db, self.test_store.mongo_db)

    def test_mongo_port_returns_mongo_port(self) -> None:
        self.assertEqual(self.mongo_port, self.test_store.mongo_port)

    def test_redis_returns_redis_instance(self) -> None:
        # Need to re-set redis object due to initialisation in the constructor
        self.test_store._redis = self.redis
        self.assertEqual(self.redis, self.test_store.redis)

    def test_mongo_returns_mongo_instance(self) -> None:
        # Need to re-set mongo object due to initialisation in the constructor
        self.test_store._mongo = self.mongo
        self.assertEqual(self.mongo, self.test_store.mongo)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that the exchanges have not already been declared
        connect_to_rabbit(self.rabbitmq)
        delete_exchange_if_exists(self.rabbitmq, STORE_EXCHANGE)
        delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        self.test_store._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_store.rabbitmq.is_connected)
        self.assertTrue(self.test_store.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_store.rabbitmq.channel._delivery_confirmation)

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_store.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE,
                                                  passive=True)

        # Check whether the consuming exchange has been creating by sending
        # messages to it. If this fails an exception is raised, hence the test
        # fails.
        self.test_store.rabbitmq.basic_publish_confirm(
            exchange=STORE_EXCHANGE,
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            COSMOS_NODE_STORE_INPUT_QUEUE_NAME, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_store.rabbitmq.basic_get(
            COSMOS_NODE_STORE_INPUT_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())

    @freeze_time("2012-01-01")
    def test_send_heartbeat_sends_a_hb_correctly(self) -> None:
        self.test_store._initialise_rabbitmq()
        res = self.test_store.rabbitmq.queue_declare(
            self.test_queue_name, False, True, False, False)
        self.assertEqual(0, res.method.message_count)
        self.rabbitmq.queue_bind(
            queue=self.test_queue_name,
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)

        test_hb = {
            'component_name': self.test_store_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self.test_store._send_heartbeat(test_hb)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            self.test_queue_name, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_store.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(test_hb, json.loads(body))

    @mock.patch.object(RabbitMQApi, "basic_consume")
    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_basic_consume_and_listen_for_data(
            self, mock_start_consuming, mock_basic_consume) -> None:
        mock_start_consuming.return_value = None
        mock_basic_consume.return_value = None

        self.test_store._listen_for_data()

        mock_start_consuming.assert_called_once()
        mock_basic_consume.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(CosmosNodeStore, "_process_mongo_store")
    @mock.patch.object(CosmosNodeStore, "_process_redis_store")
    @mock.patch.object(CosmosNodeStore, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_calls_process_redis_store_and_process_mongo_store(
            self, mock_ack, mock_send_hb, mock_proc_redis,
            mock_proc_mongo) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_proc_redis.return_value = None
        mock_proc_mongo.return_value = None

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data_optionals_enabled)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_proc_mongo.assert_called_once_with(
            self.node_data_optionals_enabled)
        mock_proc_redis.assert_called_once_with(
            self.node_data_optionals_enabled)
        mock_ack.assert_called_once()

        # We will also check if a heartbeat was sent to avoid having more tests
        test_hb = {
            'component_name': self.test_store_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(test_hb)

    @parameterized.expand([
        (Exception('test'), None,),
        (None, Exception('test'),),
    ])
    @mock.patch.object(CosmosNodeStore, "_process_mongo_store")
    @mock.patch.object(CosmosNodeStore, "_process_redis_store")
    @mock.patch.object(CosmosNodeStore, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_does_not_send_hb_if_processing_error(
            self, proc_redis_exception, proc_mongo_exception, mock_ack,
            mock_send_hb, mock_proc_redis, mock_proc_mongo) -> None:
        mock_ack.return_value = None
        mock_send_hb.return_value = None
        mock_proc_redis.side_effect = proc_redis_exception
        mock_proc_mongo.side_effect = proc_mongo_exception

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data_optionals_enabled)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_send_hb.assert_not_called()
        mock_ack.assert_called_once()

    @mock.patch.object(CosmosNodeStore, "_process_mongo_store")
    @mock.patch.object(CosmosNodeStore, "_process_redis_store")
    @mock.patch.object(CosmosNodeStore, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_does_not_raise_msg_not_del_exce_if_raised(
            self, mock_ack, mock_send_hb, mock_proc_redis,
            mock_proc_mongo) -> None:
        mock_ack.return_value = None
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test')
        mock_proc_redis.return_value = None
        mock_proc_mongo.return_value = None

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data_optionals_enabled)
        properties = pika.spec.BasicProperties()

        try:
            self.test_store._process_data(blocking_channel, method, properties,
                                          body)
        except MessageWasNotDeliveredException as e:
            self.fail("Was not expecting {}".format(e))

        mock_ack.assert_called_once()

    @parameterized.expand([
        (AMQPConnectionError('test'), AMQPConnectionError,),
        (AMQPChannelError('test'), AMQPChannelError,),
        (Exception('test'), Exception,),
    ])
    @mock.patch.object(CosmosNodeStore, "_process_mongo_store")
    @mock.patch.object(CosmosNodeStore, "_process_redis_store")
    @mock.patch.object(CosmosNodeStore, "_send_heartbeat")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_data_raises_unexpected_errors_if_raised(
            self, exception_instance, exception_type, mock_ack, mock_send_hb,
            mock_proc_redis, mock_proc_mongo) -> None:
        mock_ack.return_value = None
        mock_send_hb.side_effect = exception_instance
        mock_proc_redis.return_value = None
        mock_proc_mongo.return_value = None

        self.test_store._initialise_rabbitmq()
        blocking_channel = self.test_store.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data_optionals_enabled)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_type,
                          self.test_store._process_data,
                          blocking_channel, method, properties, body)

        mock_ack.assert_called_once()

    @mock.patch("src.data_store.stores.node.cosmos."
                "transformed_data_processing_helper")
    def test_process_redis_store_calls_transformed_data_helper_fn_correctly(
            self, mock_helper_fn) -> None:
        mock_helper_fn.return_value = None
        test_conf = {
            'prometheus': {
                'result':
                    self.test_store._process_redis_prometheus_result_store,
                'error':
                    self.test_store._process_redis_prometheus_error_store,
            },
            'tendermint_rpc': {
                'result':
                    self.test_store._process_redis_tendermint_rpc_result_store,
                'error':
                    self.test_store._process_redis_tendermint_rpc_error_store,
            },
            'cosmos_rest': {
                'result':
                    self.test_store._process_redis_cosmos_rest_result_store,
                'error':
                    self.test_store._process_redis_cosmos_rest_error_store,
            }
        }
        self.test_store._process_redis_store(self.node_data_optionals_enabled)
        mock_helper_fn.assert_called_once_with(self.test_store_name, test_conf,
                                               self.node_data_optionals_enabled)

    @parameterized.expand([
        ("self.node_data_optionals_enabled",),
    ])
    def test_process_redis_prometheus_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['prometheus']['result']
        redis_hash = Keys.get_hash_parent(self.parent_id)

        self.test_store._process_redis_prometheus_result_store(data)

        self.assertEqual(
            data['data']['went_down_at'],
            self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_went_down_at_prometheus(self.node_id)
            ))
        self.assertEqual(
            data['data']['current_height'],
            convert_to_int(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_current_height(
                    self.node_id)).decode('utf-8'), 'bad_val'))
        self.assertEqual(
            data['data']['voting_power'],
            convert_to_int(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_voting_power(self.node_id)
            ).decode('utf-8'), 'bad_val'))
        self.assertEqual(
            data['meta_data']['last_monitored'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_last_monitored_prometheus(self.node_id)
            ).decode('utf-8'), 'bad_val'))

    @parameterized.expand([
        ("self.node_data_optionals_enabled",),
    ])
    def test_process_redis_cosmos_rest_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['cosmos_rest']['result']
        redis_hash = Keys.get_hash_parent(self.parent_id)

        self.test_store._process_redis_cosmos_rest_result_store(data)

        self.assertEqual(
            data['data']['went_down_at'],
            self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_went_down_at_cosmos_rest(self.node_id)
            ))
        self.assertEqual(
            data['data']['bond_status'],
            (self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_bond_status(self.node_id)
            )).decode('utf-8'))
        self.assertEqual(
            data['data']['jailed'],
            str_to_bool(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_jailed(self.node_id)
            ).decode('utf-8')))
        self.assertEqual(
            data['meta_data']['last_monitored'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_last_monitored_cosmos_rest(self.node_id)
            ).decode('utf-8'), 'bad_val'))

    @parameterized.expand([
        ("self.node_data_optionals_enabled",),
    ])
    def test_process_redis_tendermint_rpc_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['tendermint_rpc']['result']
        redis_hash = Keys.get_hash_parent(self.parent_id)

        self.test_store._process_redis_tendermint_rpc_result_store(data)

        self.assertEqual(
            data['data']['went_down_at'],
            self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_went_down_at_tendermint_rpc(self.node_id)
            ))
        self.assertEqual(
            data['data']['slashed'],
            json.loads((self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_slashed(self.node_id)).decode('utf-8')))
        )
        self.assertEqual(
            data['data']['missed_blocks'],
            json.loads(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_missed_blocks(self.node_id)
            ).decode('utf-8')))
        self.assertEqual(
            data['data']['is_syncing'],
            str_to_bool(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_is_syncing(self.node_id)
            ).decode('utf-8')))
        self.assertEqual(
            data['meta_data']['last_monitored'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_last_monitored_tendermint_rpc(self.node_id)
            ).decode('utf-8'), 'bad_val'))

    def test_process_redis_prometheus_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['prometheus']['error']
        redis_hash = Keys.get_hash_parent(self.parent_id)
        self.test_store._process_redis_prometheus_error_store(data)

        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_cosmos_node_current_height(
                                      self.node_id))
        )
        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_cosmos_node_voting_power(
                                      self.node_id))
        )
        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_cosmos_node_is_syncing(
                                      self.node_id))
        )
        self.assertEqual(
            data['data']['went_down_at'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_went_down_at_prometheus(self.node_id)
            ).decode("utf-8"), 'bad_val'))

    def test_process_redis_cosmos_rest_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['cosmos_rest']['error']
        redis_hash = Keys.get_hash_parent(self.parent_id)
        self.test_store._process_redis_cosmos_rest_error_store(data)

        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_cosmos_node_bond_status(
                                      self.node_id))
        )
        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_cosmos_node_jailed(
                                      self.node_id))
        )
        self.assertEqual(
            data['data']['went_down_at'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_went_down_at_cosmos_rest(self.node_id)
            ).decode("utf-8"), 'bad_val'))

    def test_process_redis_tendermint_rpc_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['tendermint_rpc']['error']
        redis_hash = Keys.get_hash_parent(self.parent_id)
        self.test_store._process_redis_tendermint_rpc_error_store(data)

        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_cosmos_node_slashed(
                                      self.node_id))
        )
        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_cosmos_node_missed_blocks(
                                      self.node_id))
        )
        self.assertEqual(
            data['data']['went_down_at'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_cosmos_node_went_down_at_tendermint_rpc(self.node_id)
            ).decode("utf-8"), 'bad_val'))

    @mock.patch.object(RedisApi, "hset_multiple")
    def test_process_redis_prometheus_error_store_stores_correctly_not_down_err(
            self, redis_set) -> None:
        data = self.node_data_non_down_error['prometheus']['error']

        self.test_store._process_redis_prometheus_error_store(data)

        redis_set.assert_not_called()

    @mock.patch.object(RedisApi, "hset_multiple")
    def test_process_redis_cosmos_rest_error_store_stores_correctly_not_down_err(
            self, redis_set) -> None:
        data = self.node_data_non_down_error['cosmos_rest']['error']

        self.test_store._process_redis_cosmos_rest_error_store(data)

        redis_set.assert_not_called()

    @mock.patch.object(RedisApi, "hset_multiple")
    def test_process_redis_tendermint_rpc_error_store_stores_correctly_not_down_err(
            self, redis_set) -> None:
        data = self.node_data_non_down_error['tendermint_rpc']['error']

        self.test_store._process_redis_tendermint_rpc_error_store(data)

        redis_set.assert_not_called()

    @mock.patch("src.data_store.stores.node.cosmos."
                "transformed_data_processing_helper")
    def test_process_mongo_store_calls_transformed_data_helper_fn_correctly(
            self, mock_helper_fn) -> None:
        mock_helper_fn.return_value = None
        test_conf = {
            'prometheus': {
                'result':
                    self.test_store._process_mongo_prometheus_result_store,
                'error': self.test_store._process_mongo_prometheus_error_store,
            },
            'cosmos_rest': {
                'result':
                    self.test_store._process_mongo_cosmos_rest_result_store,
                'error': self.test_store._process_mongo_cosmos_rest_error_store,
            },
            'tendermint_rpc': {
                'result':
                    self.test_store._process_mongo_tendermint_rpc_result_store,
                'error':
                    self.test_store._process_mongo_tendermint_rpc_error_store,
            }
        }
        self.test_store._process_mongo_store(self.node_data_optionals_enabled)
        mock_helper_fn.assert_called_once_with(self.test_store_name, test_conf,
                                               self.node_data_optionals_enabled)

    @parameterized.expand([
        ("self.node_data_optionals_enabled",),
    ])
    def test_process_mongo_prometheus_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['prometheus']['result']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_prometheus_result_store(data)

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'node',
            1,
            metrics['went_down_at'],
            metrics['current_height'],
            metrics['voting_power'],
            meta_data['last_monitored']
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            None if document[node_id][0]['went_down_at_prometheus'] == 'None'
            else convert_to_float(
                document[node_id][0]['went_down_at_prometheus'], 'bad_val'),
            convert_to_int(document[node_id][0]['current_height'], 'bad_val'),
            convert_to_int(document[node_id][0]['voting_power'], 'bad_val'),
            document[node_id][0]['timestamp'],

        ]

        self.assertListEqual(expected, actual)

    @parameterized.expand([
        ("self.node_data_optionals_enabled",),
    ])
    def test_process_mongo_cosmos_rest_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['cosmos_rest']['result']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_cosmos_rest_result_store(data)

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'node',
            1,
            metrics['went_down_at'],
            metrics['bond_status'],
            metrics['jailed'],
            meta_data['last_monitored'],
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            None if document[node_id][0]['went_down_at_cosmos_rest'] == 'None'
            else convert_to_float(
                document[node_id][0]['went_down_at_cosmos_rest'], 'bad_val'),
            document[node_id][0]['bond_status'],
            str_to_bool(document[node_id][0]['jailed']),
            document[node_id][0]['timestamp'],
        ]

        self.assertListEqual(expected, actual)

    @parameterized.expand([
        ("self.node_data_optionals_enabled",),
    ])
    def test_process_mongo_tendermint_rpc_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['tendermint_rpc']['result']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_tendermint_rpc_result_store(data)

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'node',
            1,
            metrics['went_down_at'],
            metrics['slashed'],
            metrics['missed_blocks'],
            metrics['is_syncing'],
            meta_data['last_monitored'],
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            None if document[node_id][0][
                        'went_down_at_tendermint_rpc'] == 'None'
            else convert_to_float(
                document[node_id][0]['went_down_at_tendermint_rpc'], 'bad_val'),
            None if document[node_id][0]['slashed'] == 'None'
            else json.loads(document[node_id][0]['slashed']),
            None if document[node_id][0]['missed_blocks'] == 'None'
            else json.loads(document[node_id][0]['missed_blocks']),
            str_to_bool(document[node_id][0]['is_syncing']),
            document[node_id][0]['timestamp'],
        ]

        self.assertListEqual(expected, actual)

    def test_process_mongo_prometheus_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['prometheus']['error']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_prometheus_error_store(data)

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'node',
            1,
            metrics['went_down_at'],
            meta_data['time'],
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            convert_to_float(document[node_id][0]['went_down_at_prometheus'],
                             'bad_val'),
            document[node_id][0]['timestamp'],
        ]

        self.assertEqual(2, len(document[node_id][0]))
        self.assertListEqual(expected, actual)

    def test_process_mongo_cosmos_rest_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['prometheus']['error']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_cosmos_rest_error_store(data)

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'node',
            1,
            metrics['went_down_at'],
            meta_data['time'],
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            convert_to_float(document[node_id][0]['went_down_at_cosmos_rest'],
                             'bad_val'),
            document[node_id][0]['timestamp'],
        ]

        self.assertEqual(2, len(document[node_id][0]))
        self.assertListEqual(expected, actual)

    def test_process_mongo_tendermint_rpc_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['prometheus']['error']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_tendermint_rpc_error_store(data)

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'node',
            1,
            metrics['went_down_at'],
            meta_data['time'],
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            convert_to_float(
                document[node_id][0]['went_down_at_tendermint_rpc'],
                'bad_val'),
            document[node_id][0]['timestamp'],
        ]

        self.assertEqual(2, len(document[node_id][0]))
        self.assertListEqual(expected, actual)

    @mock.patch.object(MongoApi, "update_one")
    def test_process_mongo_prometheus_error_store_stores_correctly_non_down_err(
            self, mongo_update) -> None:
        data = self.node_data_non_down_error['prometheus']['error']

        self.test_store._process_mongo_prometheus_error_store(data)

        mongo_update.assert_not_called()

    @mock.patch.object(MongoApi, "update_one")
    def test_process_mongo_cosmos_rest_error_store_stores_correctly_non_down_err(
            self, mongo_update) -> None:
        data = self.node_data_non_down_error['cosmos_rest']['error']

        self.test_store._process_mongo_cosmos_rest_error_store(data)

        mongo_update.assert_not_called()

    @mock.patch.object(MongoApi, "update_one")
    def test_process_mongo_tendermint_rpc_error_store_stores_correctly_non_down_err(
            self, mongo_update) -> None:
        data = self.node_data_non_down_error['tendermint_rpc']['error']

        self.test_store._process_mongo_tendermint_rpc_error_store(data)

        mongo_update.assert_not_called()
