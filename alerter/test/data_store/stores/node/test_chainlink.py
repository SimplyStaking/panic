import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock
from unittest.mock import Mock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.data_store.mongo.mongo_api import MongoApi
from src.data_store.redis import RedisApi
from src.data_store.stores.node.chainlink import ChainlinkNodeStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          CL_NODE_TRANSFORMED_DATA_ROUTING_KEY,
                                          CL_NODE_STORE_INPUT_QUEUE_NAME)
from src.utils.exceptions import (PANICException, NodeIsDownException,
                                  MessageWasNotDeliveredException,
                                  ReceivedUnexpectedDataException)
from test.utils.utils import (connect_to_rabbit,
                              disconnect_from_rabbit,
                              delete_exchange_if_exists,
                              delete_queue_if_exists, dummy_function,
                              dummy_none_function)


class TestSystemStore(unittest.TestCase):
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
        self.mongo_ip = env.DB_IP
        self.mongo_db = env.DB_NAME
        self.mongo_port = env.DB_PORT
        self.mongo = MongoApi(logger=self.dummy_logger.getChild(
            MongoApi.__name__),
            db_name=self.mongo_db, host=self.mongo_ip,
            port=self.mongo_port)

        # Test store object
        self.test_store_name = 'store name'
        self.test_store = ChainlinkNodeStore(self.test_store_name,
                                             self.dummy_logger, self.rabbitmq)

        # Dummy data
        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.input_routing_key = CL_NODE_TRANSFORMED_DATA_ROUTING_KEY
        self.test_queue_name = 'test queue'
        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)
        self.node_id = 'test_node_id'
        self.parent_id = 'test_parent_id'
        self.node_name = 'test_node'
        self.pad = 10
        self.downtime_exception = NodeIsDownException(self.node_name)

        # Some metrics
        self.test_went_down_at_prometheus = None
        self.test_current_height = 50000000000
        self.test_eth_blocks_in_queue = 3
        self.test_total_block_headers_received = 454545040
        self.test_total_block_headers_dropped = 4
        self.test_no_of_active_jobs = 10
        self.test_max_pending_tx_delay = 6
        self.test_process_start_time_seconds = 345474.4
        self.test_total_gas_bumps = 11
        self.test_total_gas_bumps_exceeds_limit = 13
        self.test_no_of_unconfirmed_txs = 7
        self.test_total_errored_job_runs = 15
        self.test_current_gas_price_info = {
            'percentile': 50.5,
            'price': 22.0,
        }
        self.test_eth_balance_info = {
            'address1': {'balance': 34.4, 'latest_usage': 5.0},
            'address2': {'balance': 40.0, 'latest_usage': 0.0},
            'address3': {'balance': 70.0, 'latest_usage': 34.0}
        }
        self.test_last_prometheus_source_used = "prometheus_source_1"
        self.test_last_monitored_prometheus = datetime(2012, 1, 1).timestamp()
        self.node_data_optionals_enabled = {
            "prometheus": {
                "result": {
                    "meta_data": {
                        "node_name": self.node_name,
                        "node_id": self.node_id,
                        "node_parent_id": self.parent_id,
                        "last_monitored": self.test_last_monitored_prometheus,
                        "last_source_used":
                            self.test_last_prometheus_source_used,
                    },
                    "data": {
                        "went_down_at": self.test_went_down_at_prometheus,
                        "current_height": self.test_current_height,
                        "eth_blocks_in_queue": self.test_eth_blocks_in_queue,
                        "total_block_headers_received":
                            self.test_total_block_headers_received,
                        "total_block_headers_dropped":
                            self.test_total_block_headers_dropped,
                        "no_of_active_jobs": self.test_no_of_active_jobs,
                        "max_pending_tx_delay": self.test_max_pending_tx_delay,
                        "process_start_time_seconds":
                            self.test_process_start_time_seconds,
                        "total_gas_bumps": self.test_total_gas_bumps,
                        "total_gas_bumps_exceeds_limit":
                            self.test_total_gas_bumps_exceeds_limit,
                        "no_of_unconfirmed_txs":
                            self.test_no_of_unconfirmed_txs,
                        "total_errored_job_runs":
                            self.test_total_errored_job_runs,
                        "current_gas_price_info":
                            self.test_current_gas_price_info,
                        "eth_balance_info": self.test_eth_balance_info,
                    }
                }
            }
        }
        self.node_data_optionals_disabled = copy.deepcopy(
            self.node_data_optionals_enabled)
        self.node_data_optionals_disabled['prometheus']['result']['data'][
            'current_gas_price_info'] = None
        self.node_data_optionals_enabled_pad = {
            "prometheus": {
                "result": {
                    "meta_data": {
                        "node_name": self.node_name,
                        "node_id": self.node_id,
                        "node_parent_id": self.parent_id,
                        "last_monitored":
                            self.test_last_monitored_prometheus + self.pad,
                        "last_source_used":
                            self.test_last_prometheus_source_used,
                    },
                    "data": {
                        "went_down_at": self.test_went_down_at_prometheus,
                        "current_height": self.test_current_height + self.pad,
                        "eth_blocks_in_queue":
                            self.test_eth_blocks_in_queue + self.pad,
                        "total_block_headers_received":
                            self.test_total_block_headers_received + self.pad,
                        "total_block_headers_dropped":
                            self.test_total_block_headers_dropped + self.pad,
                        "no_of_active_jobs":
                            self.test_no_of_active_jobs + self.pad,
                        "max_pending_tx_delay":
                            self.test_max_pending_tx_delay + self.pad,
                        "process_start_time_seconds":
                            self.test_process_start_time_seconds + self.pad,
                        "total_gas_bumps": self.test_total_gas_bumps + self.pad,
                        "total_gas_bumps_exceeds_limit":
                            self.test_total_gas_bumps_exceeds_limit + self.pad,
                        "no_of_unconfirmed_txs":
                            self.test_no_of_unconfirmed_txs + self.pad,
                        "total_errored_job_runs":
                            self.test_total_errored_job_runs + self.pad,
                        "current_gas_price_info": {
                            'percentile': self.test_current_gas_price_info[
                                              'percentile'] + self.pad,
                            'price': self.test_current_gas_price_info[
                                         'price'] + self.pad,
                        },
                        "eth_balance_info": {
                            'address1': {
                                'balance': self.test_eth_balance_info[
                                               'address1'][
                                               'balance'] + self.pad,
                                'latest_usage': self.test_eth_balance_info[
                                                    'address1'][
                                                    'latest_usage'] + self.pad,
                            },
                            'address2': {
                                'balance': self.test_eth_balance_info[
                                               'address2'][
                                               'balance'] + self.pad,
                                'latest_usage': self.test_eth_balance_info[
                                                    'address2'][
                                                    'latest_usage'] + self.pad,
                            },
                            'address3': {
                                'balance': self.test_eth_balance_info[
                                               'address3'][
                                               'balance'] + self.pad,
                                'latest_usage': self.test_eth_balance_info[
                                                    'address3'][
                                                    'latest_usage'] + self.pad,
                            }
                        },
                    }
                }
            }
        }
        self.node_data_down_error = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        'time': self.test_last_monitored_prometheus
                    },
                    'message': self.downtime_exception.message,
                    'code': self.downtime_exception.code,
                    'data': {
                        'went_down_at': self.test_last_monitored_prometheus
                    }
                }
            }
        }
        self.node_data_non_down_err = {
            'prometheus': {
                'error': {
                    'meta_data': {
                        'node_name': self.node_name,
                        'last_source_used':
                            self.test_last_prometheus_source_used,
                        'node_id': self.node_id,
                        'node_parent_id': self.parent_id,
                        'time': self.test_last_monitored_prometheus
                    },
                    'message': self.test_exception.message,
                    'code': self.test_exception.code,
                }
            }
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, CL_NODE_STORE_INPUT_QUEUE_NAME)
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

    def test_mongo_ip_returns_mongo_ip(self) -> None:
        self.assertEqual(self.mongo_ip, self.test_store.mongo_ip)

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
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            CL_NODE_STORE_INPUT_QUEUE_NAME, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_store.rabbitmq.basic_get(
            CL_NODE_STORE_INPUT_QUEUE_NAME)
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
    @mock.patch.object(ChainlinkNodeStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkNodeStore, "_process_redis_store")
    @mock.patch.object(ChainlinkNodeStore, "_send_heartbeat")
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
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
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
    @mock.patch.object(ChainlinkNodeStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkNodeStore, "_process_redis_store")
    @mock.patch.object(ChainlinkNodeStore, "_send_heartbeat")
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
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data_optionals_enabled)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_send_hb.assert_not_called()
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkNodeStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkNodeStore, "_process_redis_store")
    @mock.patch.object(ChainlinkNodeStore, "_send_heartbeat")
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
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
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
    @mock.patch.object(ChainlinkNodeStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkNodeStore, "_process_redis_store")
    @mock.patch.object(ChainlinkNodeStore, "_send_heartbeat")
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
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.node_data_optionals_enabled)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_type,
                          self.test_store._process_data,
                          blocking_channel, method, properties, body)

        mock_ack.assert_called_once()

    @parameterized.expand([
        ({'prometheus': {'error': 4}, 'rpc': {'bad_index_key': {}, }, },),
        ({'prometheus': {}, 'rpc': {}, },),
        ({'prometheus': {}, },),
        ({},),
    ])
    def test_process_store_raises_ReceivedUnexpectDataExcept_if_bad_trans_data(
            self, test_trans_data) -> None:
        # Note that for this test we will only consider the data's structure,
        # not the metrics.
        test_config = {
            'prometheus': {
                'result': dummy_function,
                'error': dummy_none_function,
            },
            'rpc': {
                'result': dummy_function,
                'error': dummy_none_function,
            },
        }

        self.assertRaises(ReceivedUnexpectedDataException,
                          self.test_store._process_store, test_config,
                          test_trans_data)

    def test_process_store_calls_correct_function_for_sources(self) -> None:
        test_result_fn = Mock(return_value="result")
        test_error_fn = Mock(return_value="error")
        test_config = {
            'prometheus': {
                'result': test_result_fn,
                'error': test_error_fn,
            },
            'rpc': {
                'result': test_result_fn,
                'error': test_error_fn,
            }
        }
        test_trans_data = {
            'prometheus': {
                'error': 20,
            },
            'rpc': {
                'result': 10
            }
        }

        self.test_store._process_store(test_config, test_trans_data)

        test_result_fn.assert_called_once_with(10)
        test_error_fn.assert_called_once_with(20)

    # TODO: Start tests for _process_redis_store

    #
    # @parameterized.expand([
    #     ("self.system_data_1",),
    #     ("self.system_data_2",),
    #     ("self.system_data_3",),
    # ])
    # @mock.patch.object(RedisApi, "hset_multiple")
    # def test_process_redis_store_redis_is_called_correctly(
    #         self, mock_system_data, mock_hset_multiple) -> None:
    #
    #     data = eval(mock_system_data)
    #     self.test_store._process_redis_store(data)
    #
    #     meta_data = data['result']['meta_data']
    #     system_id = meta_data['system_id']
    #     parent_id = meta_data['system_parent_id']
    #     metrics = data['result']['data']
    #
    #     call_1 = call(Keys.get_hash_parent(parent_id), {
    #         Keys.get_system_process_cpu_seconds_total(system_id):
    #             str(metrics['process_cpu_seconds_total']),
    #         Keys.get_system_process_memory_usage(system_id):
    #             str(metrics['process_memory_usage']),
    #         Keys.get_system_virtual_memory_usage(system_id):
    #             str(metrics['virtual_memory_usage']),
    #         Keys.get_system_open_file_descriptors(system_id):
    #             str(metrics['open_file_descriptors']),
    #         Keys.get_system_system_cpu_usage(system_id):
    #             str(metrics['system_cpu_usage']),
    #         Keys.get_system_system_ram_usage(system_id):
    #             str(metrics['system_ram_usage']),
    #         Keys.get_system_system_storage_usage(system_id):
    #             str(metrics['system_storage_usage']),
    #         Keys.get_system_network_transmit_bytes_per_second(
    #             system_id):
    #             str(metrics['network_transmit_bytes_per_second']),
    #         Keys.get_system_network_receive_bytes_per_second(
    #             system_id):
    #             str(metrics['network_receive_bytes_per_second']),
    #         Keys.get_system_network_receive_bytes_total(system_id):
    #             str(metrics['network_receive_bytes_total']),
    #         Keys.get_system_network_transmit_bytes_total(system_id):
    #             str(metrics['network_transmit_bytes_total']),
    #         Keys.get_system_disk_io_time_seconds_total(system_id):
    #             str(metrics['disk_io_time_seconds_total']),
    #         Keys.get_system_disk_io_time_seconds_in_interval(
    #             system_id):
    #             str(metrics['disk_io_time_seconds_in_interval']),
    #         Keys.get_system_went_down_at(system_id):
    #             str(metrics['went_down_at']),
    #         Keys.get_system_last_monitored(system_id):
    #             str(meta_data['last_monitored'])})
    #     mock_hset_multiple.assert_has_calls([call_1])
    #
    # @mock.patch.object(RedisApi, "hset")
    # def test_process_redis_store_calls_hset_on_error(self, mock_hset) -> None:
    #     self.test_store._process_redis_store(self.system_data_error)
    #     call_1 = call(Keys.get_hash_parent(self.parent_id),
    #                   Keys.get_system_went_down_at(self.system_id),
    #                   str(self.last_monitored))
    #     mock_hset.assert_has_calls([call_1])
    #
    # def test_process_redis_store_raises_exception_on_unexpected_key(
    #         self) -> None:
    #     self.assertRaises(ReceivedUnexpectedDataException,
    #                       self.test_store._process_redis_store,
    #                       self.system_data_unexpected)
    #
    # @parameterized.expand([
    #     ("self.system_data_1",),
    #     ("self.system_data_2",),
    #     ("self.system_data_3",),
    # ])
    # def test_process_redis_store_redis_stores_correctly(
    #         self, mock_system_data) -> None:
    #
    #     data = eval(mock_system_data)
    #     self.test_store._process_redis_store(data)
    #
    #     meta_data = data['result']['meta_data']
    #     system_id = meta_data['system_id']
    #     parent_id = meta_data['system_parent_id']
    #     metrics = data['result']['data']
    #
    #     self.assertEqual(str(metrics['process_cpu_seconds_total']),
    #                      self.redis.hget(
    #                          Keys.get_hash_parent(parent_id),
    #                          Keys.get_system_process_cpu_seconds_total(
    #                              system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['process_memory_usage']),
    #                      self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                      Keys.get_system_process_memory_usage(
    #                                          system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['virtual_memory_usage']),
    #                      self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                      Keys.get_system_virtual_memory_usage(
    #                                          system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['open_file_descriptors']),
    #                      self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                      Keys.get_system_open_file_descriptors(
    #                                          system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['system_cpu_usage']),
    #                      self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                      Keys.get_system_system_cpu_usage(
    #                                          system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['system_ram_usage']),
    #                      self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                      Keys.get_system_system_ram_usage(
    #                                          system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['system_storage_usage']),
    #                      self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                      Keys.get_system_system_storage_usage(
    #                                          system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['network_transmit_bytes_per_second']),
    #                      self.redis.hget(
    #                          Keys.get_hash_parent(parent_id),
    #                          Keys.get_system_network_transmit_bytes_per_second(
    #                              system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['network_receive_bytes_per_second']),
    #                      self.redis.hget(
    #                          Keys.get_hash_parent(parent_id),
    #                          Keys.get_system_network_receive_bytes_per_second(
    #                              system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['network_receive_bytes_per_second']),
    #                      self.redis.hget(
    #                          Keys.get_hash_parent(parent_id),
    #                          Keys.get_system_network_receive_bytes_total(
    #                              system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['network_transmit_bytes_total']),
    #                      self.redis.hget(
    #                          Keys.get_hash_parent(parent_id),
    #                          Keys.get_system_network_transmit_bytes_total(
    #                              system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['disk_io_time_seconds_total']),
    #                      self.redis.hget(
    #                          Keys.get_hash_parent(parent_id),
    #                          Keys.get_system_disk_io_time_seconds_total(
    #                              system_id)).decode("utf-8"))
    #     self.assertEqual(str(metrics['disk_io_time_seconds_in_interval']),
    #                      self.redis.hget(
    #                          Keys.get_hash_parent(parent_id),
    #                          Keys.get_system_disk_io_time_seconds_in_interval(
    #                              system_id)).decode("utf-8"))
    #     self.assertEqual(self.none, self.redis.hget(Keys.get_hash_parent(
    #         parent_id), Keys.get_system_went_down_at(
    #         system_id)))
    #     self.assertEqual(str(meta_data['last_monitored']),
    #                      self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                      Keys.get_system_last_monitored(
    #                                          system_id)).decode("utf-8"))
    #
    # @parameterized.expand([
    #     ("self.system_data_1",),
    #     ("self.system_data_2",),
    #     ("self.system_data_3",),
    # ])
    # @mock.patch("src.data_store.stores.system.SystemStore._process_mongo_store",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
    #             autospec=True)
    # def test_process_data_saves_in_redis(self, mock_system_data, mock_send_hb,
    #                                      mock_ack, mock_process_mongo) -> None:
    #     mock_ack.return_value = None
    #     try:
    #         self.test_store._initialise_rabbitmq()
    #         data = eval(mock_system_data)
    #
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(data)
    #         )
    #         mock_process_mongo.assert_called_once()
    #         mock_ack.assert_called_once()
    #         mock_send_hb.assert_called_once()
    #
    #         meta_data = data['result']['meta_data']
    #         system_id = meta_data['system_id']
    #         parent_id = meta_data['system_parent_id']
    #         metrics = data['result']['data']
    #
    #         self.assertEqual(str(metrics['process_cpu_seconds_total']),
    #                          self.redis.hget(
    #                              Keys.get_hash_parent(parent_id),
    #                              Keys.get_system_process_cpu_seconds_total(
    #                                  system_id)).decode("utf-8"))
    #         self.assertEqual(str(metrics['process_memory_usage']),
    #                          self.redis.hget(
    #                              Keys.get_hash_parent(parent_id),
    #                              Keys.get_system_process_memory_usage(
    #                                  system_id)).decode("utf-8"))
    #         self.assertEqual(str(metrics['virtual_memory_usage']),
    #                          self.redis.hget(
    #                              Keys.get_hash_parent(parent_id),
    #                              Keys.get_system_virtual_memory_usage(
    #                                  system_id)).decode("utf-8"))
    #         self.assertEqual(str(metrics['open_file_descriptors']),
    #                          self.redis.hget(
    #                              Keys.get_hash_parent(parent_id),
    #                              Keys.get_system_open_file_descriptors(
    #                                  system_id)).decode("utf-8"))
    #         self.assertEqual(str(metrics['system_cpu_usage']),
    #                          self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                          Keys.get_system_system_cpu_usage(
    #                                              system_id)).decode("utf-8"))
    #         self.assertEqual(str(metrics['system_ram_usage']),
    #                          self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                          Keys.get_system_system_ram_usage(
    #                                              system_id)).decode("utf-8"))
    #         self.assertEqual(str(metrics['system_storage_usage']),
    #                          self.redis.hget(
    #                              Keys.get_hash_parent(parent_id),
    #                              Keys.get_system_system_storage_usage(
    #                                  system_id)).decode("utf-8"))
    #         self.assertEqual(
    #             str(metrics['network_transmit_bytes_per_second']),
    #             self.redis.hget(
    #                 Keys.get_hash_parent(parent_id),
    #                 Keys.get_system_network_transmit_bytes_per_second(
    #                     system_id)).decode("utf-8"))
    #         self.assertEqual(
    #             str(metrics['network_receive_bytes_per_second']),
    #             self.redis.hget(
    #                 Keys.get_hash_parent(parent_id),
    #                 Keys.get_system_network_receive_bytes_per_second(
    #                     system_id)).decode("utf-8"))
    #         self.assertEqual(
    #             str(metrics['network_receive_bytes_per_second']),
    #             self.redis.hget(Keys.get_hash_parent(parent_id),
    #                             Keys.get_system_network_receive_bytes_total(
    #                                 system_id)).decode("utf-8"))
    #         self.assertEqual(
    #             str(metrics['network_transmit_bytes_total']),
    #             self.redis.hget(Keys.get_hash_parent(parent_id),
    #                             Keys.get_system_network_transmit_bytes_total(
    #                                 system_id)).decode("utf-8"))
    #         self.assertEqual(str(metrics['disk_io_time_seconds_total']),
    #                          self.redis.hget(
    #                              Keys.get_hash_parent(parent_id),
    #                              Keys.get_system_disk_io_time_seconds_total(
    #                                  system_id)).decode("utf-8"))
    #         self.assertEqual(
    #             str(metrics['disk_io_time_seconds_in_interval']),
    #             self.redis.hget(
    #                 Keys.get_hash_parent(parent_id),
    #                 Keys.get_system_disk_io_time_seconds_in_interval(
    #                     system_id)).decode("utf-8"))
    #         self.assertEqual(self.none, self.redis.hget(
    #             Keys.get_hash_parent(parent_id),
    #             Keys.get_system_went_down_at(
    #                 system_id)))
    #         self.assertEqual(str(meta_data['last_monitored']),
    #                          self.redis.hget(Keys.get_hash_parent(parent_id),
    #                                          Keys.get_system_last_monitored(
    #                                              system_id)).decode("utf-8"))
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @parameterized.expand([
    #     ("KeyError", "self.system_data_key_error "),
    #     ("ReceivedUnexpectedDataException", "self.system_data_unexpected"),
    # ])
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
    #             autospec=True)
    # def test_process_data_with_bad_data_does_raises_exceptions(
    #         self, mock_error, mock_bad_data, mock_send_hb, mock_ack) -> None:
    #     mock_ack.return_value = None
    #     try:
    #         self.test_store._initialise_rabbitmq()
    #
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(self.system_data_unexpected)
    #         )
    #         self.assertRaises(eval(mock_error),
    #                           self.test_store._process_redis_store,
    #                           eval(mock_bad_data))
    #         mock_ack.assert_called_once()
    #         mock_send_hb.assert_not_called()
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @freeze_time("2012-01-01")
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.system.SystemStore._process_mongo_store",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
    #             autospec=True)
    # def test_process_data_sends_heartbeat_correctly(self,
    #                                                 mock_process_redis_store,
    #                                                 mock_process_mongo_store,
    #                                                 mock_basic_ack) -> None:
    #
    #     mock_basic_ack.return_value = None
    #     try:
    #         self.test_rabbit_manager.connect()
    #         self.test_store._initialise_rabbitmq()
    #
    #         self.test_rabbit_manager.queue_delete(self.test_queue_name)
    #         res = self.test_rabbit_manager.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=False
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #
    #         self.test_rabbit_manager.queue_bind(
    #             queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
    #             routing_key=self.heartbeat_routing_key)
    #
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(self.system_data_1)
    #         )
    #
    #         res = self.test_rabbit_manager.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=True
    #         )
    #         self.assertEqual(1, res.method.message_count)
    #
    #         heartbeat_test = {
    #             'component_name': self.test_store_name,
    #             'is_alive': True,
    #             'timestamp': datetime(2012, 1, 1).timestamp()
    #         }
    #
    #         _, _, body = self.test_rabbit_manager.basic_get(
    #             self.test_queue_name)
    #         self.assertEqual(heartbeat_test, json.loads(body))
    #         mock_process_redis_store.assert_called_once()
    #         mock_process_mongo_store.assert_called_once()
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # def test_process_data_doesnt_send_heartbeat_on_processing_error(
    #         self, mock_basic_ack) -> None:
    #
    #     mock_basic_ack.return_value = None
    #     try:
    #         self.test_rabbit_manager.connect()
    #         self.test_store._initialise_rabbitmq()
    #
    #         self.test_rabbit_manager.queue_delete(self.test_queue_name)
    #         res = self.test_rabbit_manager.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=False
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #
    #         self.test_rabbit_manager.queue_bind(
    #             queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
    #             routing_key=self.heartbeat_routing_key)
    #
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(self.system_data_unexpected)
    #         )
    #
    #         res = self.test_rabbit_manager.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=True
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(MongoApi, "update_one")
    # def test_process_mongo_store_calls_update_one(self,
    #                                               mock_update_one) -> None:
    #     self.test_store._process_mongo_result_store(
    #         self.system_data_1['result'])
    #     mock_update_one.assert_called_once()
    #
    # def test_process_mongo_store_raises_exception_on_unexpected_key(
    #         self) -> None:
    #     self.assertRaises(ReceivedUnexpectedDataException,
    #                       self.test_store._process_mongo_store,
    #                       self.system_data_unexpected)
    #
    # @parameterized.expand([
    #     ("self.system_data_1",),
    #     ("self.system_data_2",),
    #     ("self.system_data_3",),
    # ])
    # @freeze_time("2012-01-01")
    # @mock.patch.object(MongoApi, "update_one")
    # def test_process_mongo_result_store_calls_mongo_correctly(
    #         self, mock_system_data, mock_update_one) -> None:
    #     data = eval(mock_system_data)
    #     self.test_store._process_mongo_result_store(data['result'])
    #
    #     meta_data = data['result']['meta_data']
    #     system_id = meta_data['system_id']
    #     parent_id = meta_data['system_parent_id']
    #     metrics = data['result']['data']
    #     call_1 = call(
    #         parent_id,
    #         {'doc_type': 'system', 'd': datetime.now().hour},
    #         {
    #             '$push': {
    #                 system_id: {
    #                     'process_cpu_seconds_total': str(
    #                         metrics['process_cpu_seconds_total']),
    #                     'process_memory_usage': str(
    #                         metrics['process_memory_usage']),
    #                     'virtual_memory_usage': str(
    #                         metrics['virtual_memory_usage']),
    #                     'open_file_descriptors': str(
    #                         metrics['open_file_descriptors']),
    #                     'system_cpu_usage': str(metrics['system_cpu_usage']),
    #                     'system_ram_usage': str(metrics['system_ram_usage']),
    #                     'system_storage_usage': str(
    #                         metrics['system_storage_usage']),
    #                     'network_transmit_bytes_per_second': str(
    #                         metrics['network_transmit_bytes_per_second']),
    #                     'network_receive_bytes_per_second': str(
    #                         metrics['network_receive_bytes_per_second']),
    #                     'network_receive_bytes_total': str(
    #                         metrics['network_receive_bytes_total']),
    #                     'network_transmit_bytes_total': str(
    #                         metrics['network_transmit_bytes_total']),
    #                     'disk_io_time_seconds_total': str(
    #                         metrics['disk_io_time_seconds_total']),
    #                     'disk_io_time_seconds_in_interval': str(
    #                         metrics['disk_io_time_seconds_in_interval']),
    #                     'went_down_at': str(metrics['went_down_at']),
    #                     'timestamp': meta_data['last_monitored'],
    #                 }
    #             },
    #             '$inc': {'n_entries': 1},
    #         }
    #     )
    #     mock_update_one.assert_has_calls([call_1])
    #
    # @parameterized.expand([
    #     ("self.system_data_1",),
    #     ("self.system_data_2",),
    #     ("self.system_data_3",),
    # ])
    # @freeze_time("2012-01-01")
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
    #             autospec=True)
    # @mock.patch.object(MongoApi, "update_one")
    # def test_process_data_calls_mongo_correctly(
    #         self, mock_system_data, mock_update_one, mock_process_redis_store,
    #         mock_send_hb, mock_ack) -> None:
    #
    #     mock_ack.return_value = None
    #     try:
    #         self.test_store._initialise_rabbitmq()
    #
    #         data = eval(mock_system_data)
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(data)
    #         )
    #
    #         mock_process_redis_store.assert_called_once()
    #         mock_ack.assert_called_once()
    #         mock_send_hb.assert_called_once()
    #
    #         meta_data = data['result']['meta_data']
    #         system_id = meta_data['system_id']
    #         parent_id = meta_data['system_parent_id']
    #         metrics = data['result']['data']
    #         call_1 = call(
    #             parent_id,
    #             {'doc_type': 'system', 'd': datetime.now().hour},
    #             {
    #                 '$push': {
    #                     system_id: {
    #                         'process_cpu_seconds_total': str(
    #                             metrics['process_cpu_seconds_total']),
    #                         'process_memory_usage': str(
    #                             metrics['process_memory_usage']),
    #                         'virtual_memory_usage': str(
    #                             metrics['virtual_memory_usage']),
    #                         'open_file_descriptors': str(
    #                             metrics['open_file_descriptors']),
    #                         'system_cpu_usage': str(
    #                             metrics['system_cpu_usage']),
    #                         'system_ram_usage': str(
    #                             metrics['system_ram_usage']),
    #                         'system_storage_usage': str(
    #                             metrics['system_storage_usage']),
    #                         'network_transmit_bytes_per_second': str(
    #                             metrics['network_transmit_bytes_per_second']),
    #                         'network_receive_bytes_per_second': str(
    #                             metrics['network_receive_bytes_per_second']),
    #                         'network_receive_bytes_total': str(
    #                             metrics['network_receive_bytes_total']),
    #                         'network_transmit_bytes_total': str(
    #                             metrics['network_transmit_bytes_total']),
    #                         'disk_io_time_seconds_total': str(
    #                             metrics['disk_io_time_seconds_total']),
    #                         'disk_io_time_seconds_in_interval': str(
    #                             metrics['disk_io_time_seconds_in_interval']),
    #                         'went_down_at': str(metrics['went_down_at']),
    #                         'timestamp': meta_data['last_monitored'],
    #                     }
    #                 },
    #                 '$inc': {'n_entries': 1},
    #             }
    #         )
    #         mock_update_one.assert_has_calls([call_1])
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @freeze_time("2012-01-01")
    # @mock.patch.object(MongoApi, "update_one")
    # def test_process_mongo_error_store_calls_mongo_correctly(
    #         self, mock_update_one) -> None:
    #
    #     data = self.system_data_error
    #     self.test_store._process_mongo_error_store(data['error'])
    #
    #     meta_data = data['error']['meta_data']
    #     system_id = meta_data['system_id']
    #     parent_id = meta_data['system_parent_id']
    #     metrics = data['error']['data']
    #
    #     call_1 = call(
    #         parent_id,
    #         {'doc_type': 'system', 'd': datetime.now().hour},
    #         {
    #             '$push': {
    #                 system_id: {
    #                     'went_down_at': str(metrics['went_down_at']),
    #                     'timestamp': meta_data['time'],
    #                 }
    #             },
    #             '$inc': {'n_entries': 1},
    #         }
    #     )
    #     mock_update_one.assert_has_calls([call_1])
    #
    # @freeze_time("2012-01-01")
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
    #             autospec=True)
    # @mock.patch.object(MongoApi, "update_one")
    # def test_process_data_calls_mongo_correctly_on_error_data(
    #         self, mock_update_one, mock_process_redis_store,
    #         mock_send_hb, mock_ack) -> None:
    #
    #     mock_ack.return_value = None
    #     try:
    #         self.test_store._initialise_rabbitmq()
    #
    #         data = self.system_data_error
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(data)
    #         )
    #
    #         mock_process_redis_store.assert_called_once()
    #         mock_ack.assert_called_once()
    #         mock_send_hb.assert_called_once()
    #
    #         meta_data = data['error']['meta_data']
    #         system_id = meta_data['system_id']
    #         parent_id = meta_data['system_parent_id']
    #         metrics = data['error']['data']
    #
    #         call_1 = call(
    #             parent_id,
    #             {'doc_type': 'system', 'd': datetime.now().hour},
    #             {
    #                 '$push': {
    #                     system_id: {
    #                         'went_down_at': str(metrics['went_down_at']),
    #                         'timestamp': meta_data['time'],
    #                     }
    #                 },
    #                 '$inc': {'n_entries': 1},
    #             }
    #         )
    #         mock_update_one.assert_has_calls([call_1])
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @parameterized.expand([
    #     ("self.system_data_1",),
    #     ("self.system_data_2",),
    #     ("self.system_data_3",),
    # ])
    # def test_process_mongo_store_mongo_stores_correctly(
    #         self, mock_system_data) -> None:
    #
    #     data = eval(mock_system_data)
    #     self.test_store._process_mongo_store(data)
    #
    #     meta_data = data['result']['meta_data']
    #     system_id = meta_data['system_id']
    #     parent_id = meta_data['system_parent_id']
    #     metrics = data['result']['data']
    #
    #     documents = self.mongo.get_all(parent_id)
    #     document = documents[0]
    #     expected = [
    #         'system',
    #         1,
    #         str(metrics['process_cpu_seconds_total']),
    #         str(metrics['process_memory_usage']),
    #         str(metrics['virtual_memory_usage']),
    #         str(metrics['open_file_descriptors']),
    #         str(metrics['system_cpu_usage']),
    #         str(metrics['system_ram_usage']),
    #         str(metrics['system_storage_usage']),
    #         str(metrics['network_receive_bytes_total']),
    #         str(metrics['network_transmit_bytes_total']),
    #         str(metrics['disk_io_time_seconds_total']),
    #         str(metrics['network_transmit_bytes_per_second']),
    #         str(metrics['network_receive_bytes_per_second']),
    #         str(metrics['disk_io_time_seconds_in_interval']),
    #         str(metrics['went_down_at'])
    #     ]
    #     actual = [
    #         document['doc_type'],
    #         document['n_entries'],
    #         document[system_id][0]['process_cpu_seconds_total'],
    #         document[system_id][0]['process_memory_usage'],
    #         document[system_id][0]['virtual_memory_usage'],
    #         document[system_id][0]['open_file_descriptors'],
    #         document[system_id][0]['system_cpu_usage'],
    #         document[system_id][0]['system_ram_usage'],
    #         document[system_id][0]['system_storage_usage'],
    #         document[system_id][0]['network_receive_bytes_total'],
    #         document[system_id][0]['network_transmit_bytes_total'],
    #         document[system_id][0]['disk_io_time_seconds_total'],
    #         document[system_id][0]['network_transmit_bytes_per_second'],
    #         document[system_id][0]['network_receive_bytes_per_second'],
    #         document[system_id][0]['disk_io_time_seconds_in_interval'],
    #         document[system_id][0]['went_down_at']
    #     ]
    #
    #     self.assertListEqual(expected, actual)
    #
    # @freeze_time("2012-01-01")
    # def test_process_mongo_error_store_store_correctly(self) -> None:
    #
    #     data = self.system_data_error
    #     self.test_store._process_mongo_error_store(data['error'])
    #
    #     meta_data = data['error']['meta_data']
    #     system_id = meta_data['system_id']
    #     parent_id = meta_data['system_parent_id']
    #     metrics = data['error']['data']
    #
    #     documents = self.mongo.get_all(parent_id)
    #     document = documents[0]
    #     expected = [
    #         'system',
    #         1,
    #         meta_data['time'],
    #         str(metrics['went_down_at'])
    #     ]
    #     actual = [
    #         document['doc_type'],
    #         document['n_entries'],
    #         document[system_id][0]['timestamp'],
    #         document[system_id][0]['went_down_at']
    #     ]
    #
    #     self.assertListEqual(expected, actual)
    #
    # @parameterized.expand([
    #     ("self.system_data_1",),
    #     ("self.system_data_2",),
    #     ("self.system_data_3",),
    # ])
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
    #             autospec=True)
    # def test_process_data_results_stores_in_mongo_correctly(
    #         self, mock_system_data, mock_process_redis_store,
    #         mock_send_hb, mock_ack) -> None:
    #
    #     mock_ack.return_value = None
    #     try:
    #         self.test_store._initialise_rabbitmq()
    #
    #         data = eval(mock_system_data)
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(data)
    #         )
    #
    #         mock_process_redis_store.assert_called_once()
    #         mock_ack.assert_called_once()
    #         mock_send_hb.assert_called_once()
    #
    #         meta_data = data['result']['meta_data']
    #         system_id = meta_data['system_id']
    #         parent_id = meta_data['system_parent_id']
    #         metrics = data['result']['data']
    #
    #         documents = self.mongo.get_all(parent_id)
    #         document = documents[0]
    #         expected = [
    #             'system',
    #             1,
    #             str(metrics['process_cpu_seconds_total']),
    #             str(metrics['process_memory_usage']),
    #             str(metrics['virtual_memory_usage']),
    #             str(metrics['open_file_descriptors']),
    #             str(metrics['system_cpu_usage']),
    #             str(metrics['system_ram_usage']),
    #             str(metrics['system_storage_usage']),
    #             str(metrics['network_receive_bytes_total']),
    #             str(metrics['network_transmit_bytes_total']),
    #             str(metrics['disk_io_time_seconds_total']),
    #             str(metrics['network_transmit_bytes_per_second']),
    #             str(metrics['network_receive_bytes_per_second']),
    #             str(metrics['disk_io_time_seconds_in_interval']),
    #             str(metrics['went_down_at'])
    #         ]
    #         actual = [
    #             document['doc_type'],
    #             document['n_entries'],
    #             document[system_id][0]['process_cpu_seconds_total'],
    #             document[system_id][0]['process_memory_usage'],
    #             document[system_id][0]['virtual_memory_usage'],
    #             document[system_id][0]['open_file_descriptors'],
    #             document[system_id][0]['system_cpu_usage'],
    #             document[system_id][0]['system_ram_usage'],
    #             document[system_id][0]['system_storage_usage'],
    #             document[system_id][0]['network_receive_bytes_total'],
    #             document[system_id][0]['network_transmit_bytes_total'],
    #             document[system_id][0]['disk_io_time_seconds_total'],
    #             document[system_id][0]['network_transmit_bytes_per_second'],
    #             document[system_id][0]['network_receive_bytes_per_second'],
    #             document[system_id][0]['disk_io_time_seconds_in_interval'],
    #             document[system_id][0]['went_down_at']
    #         ]
    #
    #         self.assertListEqual(expected, actual)
    #
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
    #             autospec=True)
    # @mock.patch("src.data_store.stores.system.SystemStore._process_redis_store",
    #             autospec=True)
    # def test_process_data_error_stores_in_mongo_correctly(
    #         self, mock_process_redis_store,
    #         mock_send_hb, mock_ack) -> None:
    #
    #     mock_ack.return_value = None
    #     try:
    #         self.test_store._initialise_rabbitmq()
    #
    #         data = self.system_data_error
    #         blocking_channel = self.test_store.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self._input_routing_key)
    #
    #         properties = pika.spec.BasicProperties()
    #         self.test_store._process_data(
    #             blocking_channel,
    #             method_chains,
    #             properties,
    #             json.dumps(data)
    #         )
    #
    #         mock_process_redis_store.assert_called_once()
    #         mock_ack.assert_called_once()
    #         mock_send_hb.assert_called_once()
    #
    #         meta_data = data['error']['meta_data']
    #         system_id = meta_data['system_id']
    #         parent_id = meta_data['system_parent_id']
    #         metrics = data['error']['data']
    #
    #         documents = self.mongo.get_all(parent_id)
    #         document = documents[0]
    #         expected = [
    #             'system',
    #             1,
    #             meta_data['time'],
    #             str(metrics['went_down_at'])
    #         ]
    #         actual = [
    #             document['doc_type'],
    #             document['n_entries'],
    #             document[system_id][0]['timestamp'],
    #             document[system_id][0]['went_down_at']
    #         ]
    #
    #         self.assertListEqual(expected, actual)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
