import copy
import logging
from datetime import timedelta
from typing import List, Any
from unittest import TestCase, skip, mock
from unittest.mock import MagicMock, PropertyMock

import pika.exceptions
from parameterized import parameterized

from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.exceptions import ConnectionNotInitialisedException
from src.utils.timing import TimedTaskLimiter


class TestRabbitMQApi(TestCase):
    def setUp(self) -> None:
        self.rabbit_ip = env.RABBIT_IP
        self.rabbit_port = env.RABBIT_PORT
        self.rabbit_logger = logging.getLogger("testRabbit")
        self.username = ''
        self.password = ''
        self.connection_check_time_interval = timedelta(seconds=30)
        self.rabbit = RabbitMQApi(
            self.rabbit_logger, self.rabbit_ip, self.rabbit_port, self.username,
            self.password, self.connection_check_time_interval
        )

    def tearDown(self) -> None:
        pass

    def test_rabbit_object_initialised_correctly(self):
        # Settings these to be different so we can ensure that they are set
        # correctly
        username = 'test_username'
        password = 'test_password'
        connection_check_seconds = 100
        rabbit = RabbitMQApi(
            self.rabbit_logger, self.rabbit_ip, self.rabbit_port, username,
            password, timedelta(seconds=connection_check_seconds)
        )

        self.assertIsNotNone(rabbit)
        self.assertEqual(rabbit._logger, self.rabbit_logger)
        self.assertEqual(rabbit.host, self.rabbit_ip)
        self.assertEqual(rabbit.port, self.rabbit_port)
        self.assertEqual(rabbit.username, username)
        self.assertEqual(rabbit.password, password)
        self.assertEqual(connection_check_seconds,
                         rabbit.connection_check_time_interval_seconds)
        self.assertEqual(
            connection_check_seconds,
            rabbit.live_check_limiter.time_interval.total_seconds()
        )
        self.assertFalse(rabbit.is_connected)

    @parameterized.expand([
        ("started with true", True), ("started with false", False)
    ])
    def test_set_as_connected_sets_connected_as_true(
            self, name: str, starting_value: bool
    ):
        self.rabbit._is_connected = starting_value
        self.rabbit._set_as_connected()
        self.assertTrue(self.rabbit.is_connected)

    @parameterized.expand([
        ("started with true", True), ("started with false", False)
    ])
    def test_set_as_disconnected_sets_connected_as_false(
            self, name: str, starting_value: bool
    ):
        self.rabbit._is_connected = starting_value
        self.rabbit._set_as_disconnected()
        self.assertFalse(self.rabbit.is_connected)

    @parameterized.expand([
        ("is connected and can do task return false", True, True, False),
        ("is connected and cannot do task return false", True, False, False),
        ("is not connected and can do task return false", False, True, False),
        ("is not connected and cannot do task return true", False, False, True)
    ])
    @mock.patch.object(RabbitMQApi, "is_connected",
                       new_callable=mock.PropertyMock)
    @mock.patch.object(TimedTaskLimiter, "can_do_task", autospec=True)
    def test_is_recently_disconnected(
            self, name: str, is_connected_mock_value: bool,
            can_do_task_value: bool, expected_output: bool,
            mock_can_do_task: MagicMock, mock_is_connected: PropertyMock
    ):
        print(type(mock_is_connected))
        mock_is_connected.return_value = is_connected_mock_value
        mock_can_do_task.return_value = can_do_task_value
        self.assertEqual(
            expected_output, self.rabbit._is_recently_disconnected()
        )

    @parameterized.expand([
        ("multiple string inputs and string output",
         ["first_input", "second_input"], "output"),
        ("single string input and int output", ["only input"], 10),
        ("bool and int inputs and bool output", [True, 1], False),
        ("none input none output", [None], None)
    ])
    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_executes_with_no_errors_and_returns_correctly(
            self, name: str, function_arguments: List[Any],
            function_output: Any, mock_is_recently_disconnected: MagicMock
    ):
        mock_function_to_execute = MagicMock(return_value=function_output)
        mock_is_recently_disconnected.return_value = False

        self.assertEquals(
            function_output, self.rabbit._safe(
                mock_function_to_execute, function_arguments, "DEFAULT"
            )
        )
        mock_is_recently_disconnected.assert_called_once()
        mock_function_to_execute.assert_called_once_with(*function_arguments)

    @parameterized.expand([
        ("multiple string inputs and string output",
         ["first_input", "second_input"], "output"),
        ("single string input and int output", ["only input"], 10),
        ("bool and int inputs and bool output", [True, 1], False),
        ("none input none output", [None], None)
    ])
    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_returns_default_if_recently_disconnected(
            self, name: str, function_arguments: List[Any],
            function_output: Any, mock_is_recently_disconnected: MagicMock
    ):
        mock_function_to_execute = MagicMock(return_value=function_output)
        mock_function_to_execute.__name__ = "test_function"
        mock_is_recently_disconnected.return_value = True

        self.assertEquals(
            "DEFAULT", self.rabbit._safe(
                mock_function_to_execute, function_arguments, "DEFAULT"
            )
        )
        mock_is_recently_disconnected.assert_called_once()
        mock_function_to_execute.assert_not_called()

    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_on_unroutable_error_raises(
            self, mock_is_recently_disconnected: MagicMock
    ):
        mock_is_recently_disconnected.return_value = False
        mock_function_to_execute = MagicMock()
        mock_function_to_execute.__name__ = "test_function"
        mock_function_to_execute.side_effect = pika.exceptions.UnroutableError(
            "Test Unroutable"
        )

        self.assertRaises(
            pika.exceptions.UnroutableError, self.rabbit._safe,
            mock_function_to_execute, [], "DEFAULT"
        )
        mock_is_recently_disconnected.assert_called_once()

    @mock.patch.object(RabbitMQApi, "new_channel_unsafe", autospec=True)
    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_on_channel_error_creates_new_channel_and_raises(
            self, mock_is_recently_disconnected: MagicMock,
            mock_new_channel_unsafe: MagicMock
    ):
        mock_is_recently_disconnected.return_value = False
        mock_new_channel_unsafe.return_value = False
        mock_function_to_execute = MagicMock()
        mock_function_to_execute.__name__ = "test_function"
        mock_function_to_execute.side_effect = pika.exceptions.AMQPChannelError(
            "Test Channel"
        )

        self.assertRaises(
            pika.exceptions.AMQPChannelError, self.rabbit._safe,
            mock_function_to_execute, [], "DEFAULT"
        )
        mock_is_recently_disconnected.assert_called_once()
        mock_new_channel_unsafe.assert_called_once()

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe", autospec=True)
    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_on_connection_error_if_not_connected_raises(
            self, mock_is_recently_disconnected: MagicMock,
            mock_disconnect_unsafe: MagicMock, mock_connection: PropertyMock
    ):
        mock_is_recently_disconnected.return_value = False
        mock_connection.return_value = None
        mock_function_to_execute = MagicMock()
        mock_function_to_execute.__name__ = "test_function"
        mock_function_to_execute.side_effect = \
            pika.exceptions.AMQPConnectionError("Test Connection")

        self.assertRaises(
            pika.exceptions.AMQPConnectionError, self.rabbit._safe,
            mock_function_to_execute, [], "DEFAULT"
        )
        mock_is_recently_disconnected.assert_called_once()
        mock_connection.assert_called_once()
        mock_disconnect_unsafe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe", autospec=True)
    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_on_connection_error_disconnects_if_connected_raises(
            self, mock_is_recently_disconnected: MagicMock,
            mock_disconnect_unsafe: MagicMock, mock_connection: PropertyMock
    ):
        mock_is_recently_disconnected.return_value = False
        mock_connection.return_value = True  # as long as it's not None
        mock_disconnect_unsafe.return_value = None
        mock_function_to_execute = MagicMock()
        mock_function_to_execute.__name__ = "test_function"
        mock_function_to_execute.side_effect = \
            pika.exceptions.AMQPConnectionError("Test Connection")

        self.assertRaises(
            pika.exceptions.AMQPConnectionError, self.rabbit._safe,
            mock_function_to_execute, [], "DEFAULT"
        )
        mock_is_recently_disconnected.assert_called_once()
        mock_connection.assert_called_once()
        mock_disconnect_unsafe.assert_called_once()

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe", autospec=True)
    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_on_other_exception_no_disconnection_and_raises(
            self, mock_is_recently_disconnected: MagicMock,
            mock_disconnect_unsafe: MagicMock, mock_connection: PropertyMock
    ):
        mock_is_recently_disconnected.return_value = False
        mock_connection.return_value = None
        mock_disconnect_unsafe.return_value = None
        mock_function_to_execute = MagicMock()
        mock_function_to_execute.__name__ = "test_function"
        mock_function_to_execute.side_effect = Exception("A test exception")

        self.assertRaises(
            Exception, self.rabbit._safe, mock_function_to_execute, [],
            "DEFAULT"
        )
        mock_is_recently_disconnected.assert_called_once()
        mock_connection.assert_called_once()
        mock_disconnect_unsafe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "disconnect_unsafe", autospec=True)
    @mock.patch.object(RabbitMQApi, "_is_recently_disconnected", autospec=True)
    def test_safe_function_other_exception_connection_disconnects_and_raises(
            self, mock_is_recently_disconnected: MagicMock,
            mock_disconnect_unsafe: MagicMock, mock_connection: PropertyMock
    ):
        mock_is_recently_disconnected.return_value = False
        mock_connection.return_value.is_closed.return_value = True
        mock_disconnect_unsafe.return_value = None
        mock_function_to_execute = MagicMock()
        mock_function_to_execute.__name__ = "test_function"
        mock_function_to_execute.side_effect = Exception("A test exception")

        self.assertRaises(
            Exception, self.rabbit._safe, mock_function_to_execute, [],
            "DEFAULT"
        )
        mock_is_recently_disconnected.assert_called_once()
        mock_connection.assert_called()
        mock_disconnect_unsafe.assert_called_once()

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    def test_connection_initialised_with_connection_not_none_returns_true(
            self, mock_connection: PropertyMock
    ):
        mock_connection.return_value = "Test Connection Exists"
        self.assertTrue(self.rabbit._connection_initialised())

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    def test_connection_initialised_with_connection_none_raises_exception(
            self, mock_connection: PropertyMock
    ):
        mock_connection.return_value = None
        self.assertRaises(
            ConnectionNotInitialisedException,
            self.rabbit._connection_initialised
        )

    @mock.patch.object(RabbitMQApi, "_set_as_connected", autospec=True)
    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "is_connected", new_callable=PropertyMock)
    def test_connect_unsafe_does_nothing_if_connected_and_is_open(
            self, mock_is_connected: PropertyMock,
            mock_connection: PropertyMock, mock_set_as_connected: MagicMock
    ):
        mock_is_connected.return_value = True
        mock_connection.return_value.is_open.return_value = True

        self.assertIsNone(self.rabbit.connect_unsafe())
        mock_set_as_connected.assert_not_called()

    @skip("Not Implemented yet")
    def test_connect_unsafe_opens_connection_if_not_connected(self):
        pass

    @skip("Not implemented yet")
    def test_connect(self):
        pass

    @skip("Not implemented yet")
    def test_disconnect_unsafe(self):
        pass

    @skip("Not implemented yet")
    def test_disconnect(self):
        pass

    @skip("Not implemented yet")
    def test_connect_till_successful(self):
        pass

    @skip("Not implemented yet")
    def test_disconnect_till_successful(self):
        pass

    @skip("Not implemented yet")
    def test_queue_declare(self):
        pass

    @skip("Not implemented yet")
    def test_queue_bind(self):
        pass

    @skip("Not implemented yet")
    def test_basic_publish(self):
        pass

    @skip("Not implemented yet")
    def test_basic_publish_confirm(self):
        pass

    @skip("Not implemented yet")
    def test_basic_consume(self):
        pass

    @skip("Not implemented yet")
    def test_basic_get(self):
        pass

    @skip("Not implemented yet")
    def test_start_consuming(self):
        pass

    @skip("Not implemented yet")
    def test_basic_ack(self):
        pass

    @skip("Not implemented yet")
    def test_basic_qos(self):
        pass

    @skip("Not implemented yet")
    def test_exchange_declare(self):
        pass

    @skip("Not implemented yet")
    def test_confirm_delivery(self):
        pass

    @skip("Not implemented yet")
    def test_queue_purge(self):
        pass

    @skip("Not implemented yet")
    def test_exchange_delete(self):
        pass

    @skip("Not implemented yet")
    def test_queue_delete(self):
        pass

    @skip("Not implemented yet")
    def test_new_channel_unsafe(self):
        pass

    @skip("Not implemented yet")
    def test_new_channel(self):
        pass

    @skip("Not implemented yet")
    def test_perform_operation_till_successful(self):
        pass
