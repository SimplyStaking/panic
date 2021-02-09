import json
import logging
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock

import pika

from src.data_transformers.manager import DataTransformersManager, \
    _DT_MAN_INPUT_QUEUE, _DT_MAN_INPUT_ROUTING_KEY
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import SYSTEM_DATA_TRANSFORMER_NAME, \
    GITHUB_DATA_TRANSFORMER_NAME, HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import PANICException
from test.test_utils import infinite_fn


class TestDataTransformersManager(unittest.TestCase):
    def setUp(self) -> None:

        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbit_ip = 'localhost'
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_data_transformers_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.transformer_process_dict_example = {
            SYSTEM_DATA_TRANSFORMER_NAME: self.dummy_process1,
            GITHUB_DATA_TRANSFORMER_NAME: self.dummy_process2,
        }
        self.test_manager = DataTransformersManager(self.dummy_logger,
                                                    self.manager_name,
                                                    self.rabbitmq)
        self.test_exception = PANICException('test_exception', 1)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_manager.rabbitmq.connect()

            # Declare them before just in case there are tests which do not
            # use these queues and exchanges
            self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_declare(
                _DT_MAN_INPUT_QUEUE, False, True, False, False)
            self.test_manager.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, 'topic', False, True, False, False)

            self.test_manager.rabbitmq.queue_purge(self.test_queue_name)
            self.test_manager.rabbitmq.queue_purge(_DT_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(_DT_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            print("Deletion of queues and exchanges failed: {}".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.test_manager = None
        self.test_exception = None
        self.transformer_process_dict_example = None

    def test_str_returns_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.__str__())

    def test_name_returns_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_transformer_process_dict_returns_transformer_process_dict(
            self) -> None:
        self.test_manager._transformer_process_dict = \
            self.transformer_process_dict_example
        self.assertEqual(self.transformer_process_dict_example,
                         self.test_manager.transformer_process_dict)

    def test_initialise_rabbitmq_initializes_everything_as_expected(
            self) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchange and queue have not already been
            # declared
            self.rabbitmq.connect()
            self.test_manager.rabbitmq.queue_delete(_DT_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_manager._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_manager.rabbitmq.is_connected)
            self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_manager.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchange and queue have been creating by
            # sending messages with the same routing keys as for the queue. We
            # will also check if the size of the queue is 0 to confirm that
            # basic_consume was called (it will store the msg in the component
            # memory immediately). If one of the exchange or queue is not
            # created, then either an exception will be thrown or the queue size
            # would be 1. Note when deleting the exchange in the beginning we
            # also released every binding, hence there is no other queue binded
            # with the same routing key to any exchange at this point.
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=_DT_MAN_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_manager.rabbitmq.queue_declare(
                _DT_MAN_INPUT_QUEUE, False, True, False, False)
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        self.assertEqual(1, mock_start_consuming.call_count)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_manager._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._send_heartbeat(self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))
