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
from src.data_store.stores.node.evm import EVMNodeStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.mongo import REPLICA_SET_HOSTS, REPLICA_SET_NAME
from src.utils.constants.rabbitmq import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
                                          EVM_NODE_STORE_INPUT_QUEUE_NAME)
from src.utils.exceptions import (PANICException, NodeIsDownException,
                                  MessageWasNotDeliveredException)
from src.utils.types import (convert_to_int, convert_to_float,
                             convert_none_to_bool)
from test.test_utils.utils import (
    connect_to_rabbit, disconnect_from_rabbit, delete_exchange_if_exists,
    delete_queue_if_exists)


class TestEVMNodeStore(unittest.TestCase):
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
        self.test_store = EVMNodeStore(self.test_store_name,
                                       self.dummy_logger, self.rabbitmq)

        # Dummy data
        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.input_routing_key = EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY
        self.test_queue_name = 'test queue'
        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)
        self.node_id = 'test_node_id'
        self.parent_id = 'test_parent_id'
        self.node_name = 'test_node'
        self.pad = 10
        self.downtime_exception = NodeIsDownException(self.node_name)

        # Some metrics
        self.test_went_down_at = None
        self.test_current_height = 50000000000
        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.node_data = {
            "result": {
                "meta_data": {
                    "node_name": self.node_name,
                    "node_id": self.node_id,
                    "node_parent_id": self.parent_id,
                    "last_monitored": self.test_last_monitored,
                },
                "data": {
                    "went_down_at": self.test_went_down_at,
                    "current_height": self.test_current_height,
                    "syncing": False
                }
            }
        }
        self.node_data_pad = {
            "result": {
                "meta_data": {
                    "node_name": self.node_name,
                    "node_id": self.node_id,
                    "node_parent_id": self.parent_id,
                    "last_monitored":
                        self.test_last_monitored + self.pad,
                },
                "data": {
                    "went_down_at": self.test_went_down_at,
                    "current_height": self.test_current_height + self.pad,
                    "syncing": False
                }
            }
        }
        self.node_data_down_error = {
            'error': {
                'meta_data': {
                    'node_name': self.node_name,
                    'node_id': self.node_id,
                    'node_parent_id': self.parent_id,
                    'time': self.test_last_monitored
                },
                'message': self.downtime_exception.message,
                'code': self.downtime_exception.code,
                'data': {
                    'went_down_at': self.test_last_monitored
                }
            }
        }
        self.node_data_non_down_err = {
            'error': {
                'meta_data': {
                    'node_name': self.node_name,
                    'node_id': self.node_id,
                    'node_parent_id': self.parent_id,
                    'time': self.test_last_monitored
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, EVM_NODE_STORE_INPUT_QUEUE_NAME)
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
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            EVM_NODE_STORE_INPUT_QUEUE_NAME, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_store.rabbitmq.basic_get(
            EVM_NODE_STORE_INPUT_QUEUE_NAME)
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
    def test_listen_for_data_calls_basic_consume_and_start_consuming(
            self, mock_start_consuming, mock_basic_consume) -> None:
        mock_start_consuming.return_value = None
        mock_basic_consume.return_value = None

        self.test_store._listen_for_data()

        mock_start_consuming.assert_called_once()
        mock_basic_consume.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMNodeStore, "_process_mongo_store")
    @mock.patch.object(EVMNodeStore, "_process_redis_store")
    @mock.patch.object(EVMNodeStore, "_send_heartbeat")
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
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_proc_mongo.assert_called_once_with(
            self.node_data)
        mock_proc_redis.assert_called_once_with(
            self.node_data)
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
    @mock.patch.object(EVMNodeStore, "_process_mongo_store")
    @mock.patch.object(EVMNodeStore, "_process_redis_store")
    @mock.patch.object(EVMNodeStore, "_send_heartbeat")
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
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_send_hb.assert_not_called()
        mock_ack.assert_called_once()

    @mock.patch.object(EVMNodeStore, "_process_mongo_store")
    @mock.patch.object(EVMNodeStore, "_process_redis_store")
    @mock.patch.object(EVMNodeStore, "_send_heartbeat")
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
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data)
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
    @mock.patch.object(EVMNodeStore, "_process_mongo_store")
    @mock.patch.object(EVMNodeStore, "_process_redis_store")
    @mock.patch.object(EVMNodeStore, "_send_heartbeat")
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
            routing_key=EVM_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_type,
                          self.test_store._process_data,
                          blocking_channel, method, properties, body)

        mock_ack.assert_called_once()

    @parameterized.expand([
        ("self.node_data",),
        ("self.node_data_pad",),
    ])
    def test_process_redis_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['result']
        redis_hash = Keys.get_hash_parent(self.parent_id)

        self.test_store._process_redis_result_store(data)

        self.assertEqual(
            data['data']['current_height'],
            convert_to_int(self.redis.hget(redis_hash,
                                           Keys.get_evm_node_current_height(
                                               self.node_id)
                                           ).decode("utf-8"), 'bad_val'))
        self.assertEqual(
            data['data']['syncing'],
            convert_none_to_bool(
                self.redis.hget(
                    redis_hash,
                    Keys.get_evm_node_syncing(self.node_id)).decode("utf-8"),
                'bad_val'))
        self.assertEqual(
            data['meta_data']['last_monitored'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_evm_node_last_monitored(self.node_id)
            ).decode("utf-8"), 'bad_val'))
        self.assertEqual(
            data['data']['went_down_at'],
            self.redis.hget(
                redis_hash,
                Keys.get_evm_node_went_down_at(self.node_id)
            ))

    def test_process_redis_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['error']
        redis_hash = Keys.get_hash_parent(self.parent_id)
        self.test_store._process_redis_error_store(data)

        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_evm_node_current_height(
                                      self.node_id))
        )
        self.assertEqual(None, self.redis.hget(
            redis_hash, Keys.get_evm_node_last_monitored(self.node_id)
        ))
        self.assertEqual(
            data['data']['went_down_at'],
            convert_to_float(self.redis.hget(
                redis_hash,
                Keys.get_evm_node_went_down_at(self.node_id)
            ).decode("utf-8"), 'bad_val'))

    def test_process_redis_error_store_stores_correctly_not_down_err(
            self) -> None:
        data = self.node_data_non_down_err['error']
        redis_hash = Keys.get_hash_parent(self.parent_id)
        self.test_store._process_redis_error_store(data)

        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_evm_node_current_height(
                                      self.node_id))
        )
        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_evm_node_syncing(
                                      self.node_id))
        )
        self.assertEqual(None, self.redis.hget(
            redis_hash, Keys.get_evm_node_last_monitored(self.node_id)
        ))
        self.assertEqual(
            None, self.redis.hget(redis_hash,
                                  Keys.get_evm_node_went_down_at(
                                      self.node_id)))

    @parameterized.expand([
        ("self.node_data",),
        ("self.node_data_pad",),
    ])
    def test_process_mongo_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['result']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_result_store(data)

        documents = self.mongo.get_all(parent_id)
        document = documents[0]
        expected = [
            'node',
            1,
            metrics['current_height'],
            metrics['syncing'],
            metrics['went_down_at'],
            meta_data['last_monitored'],
        ]
        actual = [
            document['doc_type'],
            document['n_entries'],
            convert_to_int(document[node_id][0]['current_height'], 'bad_val'),
            convert_none_to_bool(document[node_id][0]['syncing'], 'bad_val'),
            None if document[node_id][0]['went_down_at'] == 'None'
            else convert_to_float(
                document[node_id][0]['went_down_at'], 'bad_val'),
            document[node_id][0]['timestamp'],
        ]

        self.assertListEqual(expected, actual)

    def test_process_mongo_error_store_stores_correctly_if_down_err(
            self) -> None:
        data = self.node_data_down_error['error']
        meta_data = data['meta_data']
        node_id = meta_data['node_id']
        parent_id = meta_data['node_parent_id']
        metrics = data['data']

        self.test_store._process_mongo_error_store(data)

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
            convert_to_float(document[node_id][0]['went_down_at'],
                             'bad_val'),
            document[node_id][0]['timestamp'],
        ]

        self.assertEqual(2, len(document[node_id][0]))
        self.assertListEqual(expected, actual)
