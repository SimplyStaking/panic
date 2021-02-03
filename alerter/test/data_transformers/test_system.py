import logging
import unittest
from datetime import timedelta
from queue import Queue
from unittest import mock

from src.data_store.redis import RedisApi
from src.data_transformers.system import SystemDataTransformer, \
    _SYSTEM_DT_INPUT_QUEUE
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitorables.system import System
from src.utils import env
from src.utils.constants import HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE, \
    STORE_EXCHANGE, ALERT_EXCHANGE


class TestSystemDataTransformer(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        # self.rabbit_ip = env.RABBIT_IP
        self.rabbit_ip = 'localhost'
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
        self.test_state = {self.test_system_id: self.test_system}
        self.test_publishing_queue = Queue(self.max_queue_size)
        self.test_rabbit_queue_name = 'Test Queue'
        self.test_data_transformer = SystemDataTransformer(
            self.transformer_name, self.dummy_logger, self.redis, self.rabbitmq,
            self.max_queue_size)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_data_transformer.rabbitmq.connect_till_successful()

            # Declare them before just in case there are tests which do not
            # use these queues and exchanges
            # TODO: Add test queue
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
                _SYSTEM_DT_INPUT_QUEUE)
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
            self.test_data_transformer.rabbitmq.disconnect_till_successful()
        except Exception as e:
            print("Deletion of queues and exchanges failed: {}".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.redis = None
        self.test_system = None
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

    def test_initialise_rabbit_initializes_everything_as_expected(self) -> None:
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

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_data_transformer.rabbitmq.is_connected)
            self.assertTrue(
                self.test_data_transformer.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_data_transformer.rabbitmq
                    .channel._delivery_confirmation)

            # TODO: Continue test

            # Check whether the queues and exchanges were created by
            # re-declaring them with passive=True. If they are not created yet
            # this would raise an exception, hence the tests would fail.
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    # TODO: First test initialise rabbit and then send_heartbeat in data
    #     : transformer

# todo: change comment in component and env.variables commented here
