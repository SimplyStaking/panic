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
from src.data_store.stores.contract.chainlink import ChainlinkContractStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (
    STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE, HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY,
    CL_CONTRACT_STORE_INPUT_QUEUE_NAME)
from src.utils.exceptions import (PANICException, NodeIsDownException,
                                  MessageWasNotDeliveredException)
from src.utils.types import convert_to_int, convert_to_float
from test.utils.utils import (connect_to_rabbit,
                              disconnect_from_rabbit,
                              delete_exchange_if_exists,
                              delete_queue_if_exists)


class TestChainlinkContractStore(unittest.TestCase):
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
        self.test_store = ChainlinkContractStore(self.test_store_name,
                                                 self.dummy_logger,
                                                 self.rabbitmq)

        # Dummy data
        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.input_routing_key = CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY
        self.test_queue_name = 'test queue'
        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)
        self.node_id = 'test_node_id'
        self.parent_id = 'test_parent_id'
        self.node_name = 'test_node'
        self.pad = 10
        self.downtime_exception = NodeIsDownException(self.node_name)

        # Some metrics contract version 3
        self.test_contract_version_3 = 3
        self.test_aggregator_address_3 = \
            '0x00c7A37B03690fb9f41b5C5AF8131735C7275446'
        self.test_aggregator_address_3_1 = \
            '0x11c7A37B03690fb9f41b5C5AF8131735C7275446'
        self.test_proxy_address_3 = \
            '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419'
        self.test_proxy_address_3_1 = \
            '0x6B4aL5Pj9cbd43714FE2740f5E3616155c5b8419'
        self.test_latest_round_3 = 92233720368547767541
        self.test_latest_round_3_1 = 92233720368547767540
        self.test_latest_answer_3 = 319275162350
        self.test_latest_answer_3_1 = 319275162349
        self.test_latest_timestamp_3 = 1630316066
        self.test_latest_timestamp_3_1 = 1630316065
        self.test_answered_in_round_3 = 1630316066
        self.test_answered_in_round_3_1 = 1630316065
        self.test_withdrawable_payment_3 = 4750000000000000000
        self.test_withdrawable_payment_3_1 = 4750000000000111111
        self.test_historical_rounds_3 = [
            {
                'roundId': 92233720368547767540,
                'roundAnswer': 319275162350,
                'roundTimestamp': 1630316065,
                'answeredInRound': 1630316066,
                'nodeSubmission': 8,
                'deviation': 100,
            },
            {
                'roundId': 92233720368547767539,
                'roundAnswer': 319275162349,
                'roundTimestamp': 1630316064,
                'answeredInRound': 1630316065,
                'nodeSubmission': 8,
                'deviation': 50,
            }
        ]
        self.test_historical_rounds_3_1 = [
            {
                'roundId': 92233720368547767538,
                'roundAnswer': 319275162348,
                'roundTimestamp': 1630316063,
                'answeredInRound': 1630316064,
                'nodeSubmission': 7,
                'deviation': 200,
            },
            {
                'roundId': 92233720368547767523,
                'roundAnswer': 319275162321,
                'roundTimestamp': 1630316012,
                'answeredInRound': 1630316011,
                'nodeSubmission': 7,
                'deviation': 1200,
            }
        ]
        # Some metrics contract version 4
        self.test_contract_version_4 = 4
        self.test_aggregator_address_4 = \
            '0x00d9B37B03690fb9f41b5C5AF8131735C7275456'
        self.test_aggregator_address_4_1 = \
            '0x22d9B37B03690fb9f41b5C5AF8131735C7275456'
        self.test_proxy_address_4 = \
            '0x6C4eC3Df9cbd43714FE2740f5E3616155c5b8419'
        self.test_proxy_address_4_1 = \
            '0x7D5bD4Df9cbd43714FE2740f5E3616155c5b8419'
        self.test_latest_round_4 = 92233720368547767541
        self.test_latest_round_4_1 = 82233720368547767541
        self.test_latest_answer_4 = 319275162350
        self.test_latest_answer_4_1 = 319275162340
        self.test_latest_timestamp_4 = 1630316066
        self.test_latest_timestamp_4_1 = 1630315066
        self.test_answered_in_round_4 = 1630316066
        self.test_answered_in_round_4_1 = 1630313066
        self.test_owed_payment_4 = 4750000000000000000
        self.test_owed_payment_4_1 = 3750000000000000000
        self.test_historical_rounds_4 = [
            {
                'roundId': 92233720368547767540,
                'roundAnswer': 319275162350,
                'roundTimestamp': 1630316065,
                'answeredInRound': 1630316066,
                'nodeSubmission': 8,
                'noOfObservations': 8,
                'noOfTransmitters': 8,
                'deviation': 100,
            },
            {
                'roundId': 92233720368547767539,
                'roundAnswer': 319275162349,
                'roundTimestamp': 1630316064,
                'answeredInRound': 1630316065,
                'nodeSubmission': 8,
                'noOfObservations': 8,
                'noOfTransmitters': 8,
                'deviation': 50,
            }
        ]
        self.test_historical_rounds_4_1 = [
            {
                'roundId': 192233720368547767540,
                'roundAnswer': 1319275162350,
                'roundTimestamp': 11630316065,
                'answeredInRound': 11630316066,
                'nodeSubmission': 81,
                'noOfObservations': 81,
                'noOfTransmitters': 81,
                'deviation': 1001,
            },
            {
                'roundId': 192233720368547767539,
                'roundAnswer': 1319275162349,
                'roundTimestamp': 11630316064,
                'answeredInRound': 11630316065,
                'nodeSubmission': 81,
                'noOfObservations': 81,
                'noOfTransmitters': 81,
                'deviation': 150,
            }
        ]

        self.test_last_monitored = datetime(2012, 1, 1).timestamp()
        self.contract_data_v3 = {
            "result": {
                "meta_data": {
                    "node_name": self.node_name,
                    "node_id": self.node_id,
                    "node_parent_id": self.parent_id,
                    "last_monitored": self.test_last_monitored,
                },
                "data": {
                    self.test_proxy_address_3: {
                        "contractVersion": self.test_contract_version_3,
                        "aggregatorAddress": self.test_aggregator_address_3,
                        "latestRound": self.test_latest_round_3,
                        "latestAnswer": self.test_latest_answer_3,
                        "latestTimestamp": self.test_latest_timestamp_3,
                        "answeredInRound": self.test_answered_in_round_3,
                        "withdrawablePayment":
                            self.test_withdrawable_payment_3,
                        "historicalRounds": self.test_historical_rounds_3,
                    },
                    self.test_proxy_address_3_1: {
                        "contractVersion": self.test_contract_version_3,
                        "aggregatorAddress": self.test_aggregator_address_3_1,
                        "latestRound": self.test_latest_round_3_1,
                        "latestAnswer": self.test_latest_answer_3_1,
                        "latestTimestamp": self.test_latest_timestamp_3_1,
                        "answeredInRound": self.test_answered_in_round_3_1,
                        "withdrawablePayment":
                            self.test_withdrawable_payment_3_1,
                        "historicalRounds": self.test_historical_rounds_3_1,
                    }
                }
            }
        }
        self.contract_data_v4 = {
            "result": {
                "meta_data": {
                    "node_name": self.node_name,
                    "node_id": self.node_id,
                    "node_parent_id": self.parent_id,
                    "last_monitored": self.test_last_monitored,
                },
                "data": {
                    self.test_proxy_address_4: {
                        "contractVersion": self.test_contract_version_4,
                        "aggregatorAddress": self.test_aggregator_address_4,
                        "latestRound": self.test_latest_round_4,
                        "latestAnswer": self.test_latest_answer_4,
                        "latestTimestamp": self.test_latest_timestamp_4,
                        "answeredInRound": self.test_answered_in_round_4,
                        "owedPayment": self.test_owed_payment_4,
                        "historicalRounds": self.test_historical_rounds_4,
                    },
                    self.test_proxy_address_4_1: {
                        "contractVersion": self.test_contract_version_4,
                        "aggregatorAddress": self.test_aggregator_address_4_1,
                        "latestRound": self.test_latest_round_4_1,
                        "latestAnswer": self.test_latest_answer_4_1,
                        "latestTimestamp": self.test_latest_timestamp_4_1,
                        "answeredInRound": self.test_answered_in_round_4_1,
                        "owedPayment": self.test_owed_payment_4_1,
                        "historicalRounds": self.test_historical_rounds_4_1,
                    }
                }
            }
        }

        self.contract_data_down_error = {
            'error': {
                'meta_data': {
                    'node_name': self.node_name,
                    'node_id': self.node_id,
                    'node_parent_id': self.parent_id,
                    'time': self.test_last_monitored
                },
                'message': self.downtime_exception.message,
                'code': self.downtime_exception.code,
            }
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq,
                               CL_CONTRACT_STORE_INPUT_QUEUE_NAME)
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
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            CL_CONTRACT_STORE_INPUT_QUEUE_NAME, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_store.rabbitmq.basic_get(
            CL_CONTRACT_STORE_INPUT_QUEUE_NAME)
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
    @mock.patch.object(ChainlinkContractStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkContractStore, "_process_redis_store")
    @mock.patch.object(ChainlinkContractStore, "_send_heartbeat")
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
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.contract_data_v3)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_proc_mongo.assert_called_once_with(
            self.contract_data_v3)
        mock_proc_redis.assert_called_once_with(
            self.contract_data_v3)
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
    @mock.patch.object(ChainlinkContractStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkContractStore, "_process_redis_store")
    @mock.patch.object(ChainlinkContractStore, "_send_heartbeat")
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
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.contract_data_v3)
        properties = pika.spec.BasicProperties()

        self.test_store._process_data(blocking_channel, method, properties,
                                      body)

        mock_send_hb.assert_not_called()
        mock_ack.assert_called_once()

    @mock.patch.object(ChainlinkContractStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkContractStore, "_process_redis_store")
    @mock.patch.object(ChainlinkContractStore, "_send_heartbeat")
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
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.contract_data_v3)
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
    @mock.patch.object(ChainlinkContractStore, "_process_mongo_store")
    @mock.patch.object(ChainlinkContractStore, "_process_redis_store")
    @mock.patch.object(ChainlinkContractStore, "_send_heartbeat")
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
            routing_key=CL_CONTRACT_TRANSFORMED_DATA_ROUTING_KEY)
        body = json.dumps(self.contract_data_v3)
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_type,
                          self.test_store._process_data,
                          blocking_channel, method, properties, body)

        mock_ack.assert_called_once()

    @parameterized.expand([
        ("self.contract_data_v3",),
        ("self.contract_data_v4",),
    ])
    def test_process_redis_result_store_stores_correctly(
            self, data_var) -> None:
        data = eval(data_var)['result']
        meta_data = data['meta_data']
        redis_hash = Keys.get_hash_parent(self.parent_id)

        self.test_store._process_redis_result_store(data)

        metrics = data['data']
        for proxy_address, contract_data in metrics.items():
            self.assertEqual(
                contract_data['contractVersion'],
                convert_to_int(self.redis.hget(
                    redis_hash, Keys.get_cl_contract_version(
                        self.node_id,
                        proxy_address)).decode("utf-8"), 'bad_val'))

            self.assertEqual(
                contract_data['aggregatorAddress'],
                self.redis.hget(
                    redis_hash, Keys.get_cl_contract_aggregator_address(
                        self.node_id, proxy_address)).decode("utf-8"))

            self.assertEqual(
                contract_data['latestRound'],
                convert_to_int(self.redis.hget(
                    redis_hash, Keys.get_cl_contract_latest_round(
                        self.node_id, proxy_address)).decode("utf-8"),
                               'bad_val'))

            self.assertEqual(
                contract_data['latestAnswer'],
                convert_to_int(self.redis.hget(
                    redis_hash, Keys.get_cl_contract_latest_answer(
                        self.node_id, proxy_address)).decode("utf-8"),
                               'bad_val'))

            self.assertEqual(
                contract_data['latestTimestamp'],
                convert_to_int(self.redis.hget(
                    redis_hash, Keys.get_cl_contract_latest_timestamp(
                        self.node_id, proxy_address)).decode("utf-8"),
                               'bad_val'))

            self.assertEqual(
                contract_data['answeredInRound'],
                convert_to_int(self.redis.hget(
                    redis_hash, Keys.get_cl_contract_answered_in_round(
                        self.node_id, proxy_address)).decode("utf-8"),
                               'bad_val'))

            self.assertEqual(
                json.dumps(contract_data['historicalRounds']),
                self.redis.hget(
                    redis_hash, Keys.get_cl_contract_historical_rounds(
                        self.node_id, proxy_address)).decode("utf-8"))

            self.assertEqual(
                meta_data['last_monitored'],
                convert_to_float(self.redis.hget(
                    redis_hash, Keys.get_cl_contract_last_monitored(
                        self.node_id, proxy_address)).decode("utf-8"),
                                 'bad_val'))

            if int(contract_data['contractVersion']) == 3:
                self.assertEqual(
                    contract_data['withdrawablePayment'],
                    convert_to_int(self.redis.hget(
                        redis_hash, Keys.get_cl_contract_withdrawable_payment(
                            self.node_id, proxy_address)).decode("utf-8"),
                                   'bad_val'))
            elif int(contract_data['contractVersion']) == 4:
                self.assertEqual(
                    contract_data['owedPayment'],
                    convert_to_int(self.redis.hget(
                        redis_hash, Keys.get_cl_contract_owed_payment(
                            self.node_id, proxy_address)).decode("utf-8"),
                                   'bad_val'))

    @mock.patch.object(RedisApi, "set_unsafe")
    @mock.patch.object(RedisApi, "hset_unsafe")
    @mock.patch.object(RedisApi, "set_multiple_unsafe")
    @mock.patch.object(RedisApi, "set_for_unsafe")
    @mock.patch.object(ChainlinkContractStore, "_process_redis_result_store")
    def test_process_redis_error_store_does_nothing(
            self, mock_result_store, mock_set_unsafe, mock_hset_unsafe,
            mock_set_multiple_unsafe, mock_set_for_unsafe) -> None:
        self.test_store._process_redis_store(self.contract_data_down_error)
        mock_result_store.assert_not_called()
        mock_set_unsafe.assert_not_called()
        mock_hset_unsafe.assert_not_called()
        mock_set_multiple_unsafe.assert_not_called()
        mock_set_for_unsafe.assert_not_called()

    @parameterized.expand([
        ("self.contract_data_v3",),
        ("self.contract_data_v4",),
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

        for proxy_address, contract_data in metrics.items():
            if int(contract_data['contractVersion']) == 3:
                expected = [
                    'contract',
                    len(metrics),
                    contract_data['contractVersion'],
                    contract_data['aggregatorAddress'],
                    contract_data['latestRound'],
                    contract_data['latestAnswer'],
                    contract_data['latestTimestamp'],
                    contract_data['answeredInRound'],
                    contract_data['withdrawablePayment'],
                    contract_data['historicalRounds'],
                    meta_data['last_monitored'],
                ]
                actual = [
                    document['doc_type'],
                    document['n_entries'],
                    convert_to_int(document[proxy_address][0][
                                       'contractVersion'], 'bad_val'),
                    document[proxy_address][0]['aggregatorAddress'],
                    convert_to_int(document[proxy_address][0]['latestRound'],
                                   'bad_val'),
                    convert_to_int(document[proxy_address][0]['latestAnswer'],
                                   'bad_val'),
                    convert_to_float(document[proxy_address][0][
                                         'latestTimestamp'], 'bad_val'),
                    convert_to_int(document[proxy_address][0][
                                       'answeredInRound'], 'bad_val'),
                    convert_to_int(
                        document[proxy_address][0]['withdrawablePayment'],
                        'bad_val'),
                    document[proxy_address][0]['historicalRounds'],
                    convert_to_int(document[proxy_address][0]['timestamp'],
                                   'bad_val'),
                ]
            elif int(contract_data['contractVersion']) == 4:
                expected = [
                    'contract',
                    1,
                    contract_data['contractVersion'],
                    contract_data['aggregatorAddress'],
                    contract_data['latestRound'],
                    contract_data['latestAnswer'],
                    contract_data['latestTimestamp'],
                    contract_data['answeredInRound'],
                    contract_data['owedPayment'],
                    str(contract_data['historicalRounds']),
                    meta_data['last_monitored'],
                ]
                actual = [
                    document['doc_type'],
                    document['n_entries'],
                    convert_to_int(document[proxy_address][0][
                                       'contractVersion'], 'bad_val'),
                    document[proxy_address][0]['aggregatorAddress'],
                    convert_to_int(document[proxy_address][0]['latestRound'],
                                   'bad_val'),
                    convert_to_int(document[proxy_address][0]['latestAnswer'],
                                   'bad_val'),
                    convert_to_float(document[proxy_address][0][
                                         'latestTimestamp'], 'bad_val'),
                    convert_to_int(document[proxy_address][0][
                                       'answeredInRound'], 'bad_val'),
                    convert_to_int(
                        document[proxy_address][0]['owedPayment'],
                        'bad_val'),
                    document[proxy_address][0]['historicalRounds'],
                    convert_to_int(document[proxy_address][0]['timestamp'],
                                   'bad_val'),
                ]

    @mock.patch.object(MongoApi, "insert_one")
    @mock.patch.object(MongoApi, "insert_many")
    @mock.patch.object(MongoApi, "update_one")
    @mock.patch.object(ChainlinkContractStore, "_process_mongo_result_store")
    def test_process_mongo_error_store_does_nothing(
            self, mock_result_store, mock_insert_one, mock_insert_many,
            mock_update_one) -> None:
        self.test_store._process_mongo_store(self.contract_data_down_error)
        mock_result_store.assert_not_called()
        mock_insert_one.assert_not_called()
        mock_insert_many.assert_not_called()
        mock_update_one.assert_not_called()
