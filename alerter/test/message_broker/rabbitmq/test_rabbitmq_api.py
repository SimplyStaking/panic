import logging
from datetime import timedelta
from typing import List, Any, Optional, Union
from unittest import TestCase, skip, mock
from unittest.mock import MagicMock, PropertyMock

import pika.exceptions
from parameterized import parameterized

from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.exceptions import ConnectionNotInitialisedException, \
    BlankCredentialException, MessageWasNotDeliveredException
from src.utils.timing import TimedTaskLimiter
from test.utils.test_utils import TestConnection, dummy_function


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

        self.assertEqual(
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

        self.assertEqual(
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

    @parameterized.expand([
        ("useranme_and_password_blank", '', ''),
        ("useranme_and_password_none", None, None),
        ("username_and_password_filled", 'test_user', 'test_password')
    ])
    @mock.patch.object(TestConnection, "channel", autospec=True)
    @mock.patch("pika.BlockingConnection", autospec=True)
    @mock.patch.object(RabbitMQApi, "_set_as_connected", autospec=True)
    def test_connect_unsafe_opens_connection_if_not_connected(
            self, name: str, username: Optional[str], password: Optional[str],
            mock_set_as_connected: MagicMock,
            mock_blocking_connection: MagicMock, mock_channel: MagicMock
    ):
        def return_dict_from_params(params: pika.ConnectionParameters):
            print(params._credentials.username)
            print(params._credentials.password)
            print(params._credentials.erase_on_connect)
            return TestConnection(
                host=params._host, port=params._port,
                virtual_host=params._virtual_host,
                credentials=params._credentials
            )

        mock_set_as_connected.return_value = None
        mock_blocking_connection.side_effect = return_dict_from_params
        mock_channel.return_value = True

        self.rabbit._username = username
        self.rabbit._password = password
        self.assertIsNone(self.rabbit.connect_unsafe())
        self.assertIs(type(self.rabbit.connection), TestConnection)
        self.assertEqual(self.rabbit.host, self.rabbit.connection.host)
        self.assertEqual(self.rabbit.port, self.rabbit.connection.port)
        self.assertEqual("/", self.rabbit.connection.virtual_host)
        self.assertEqual(
            pika.PlainCredentials(username or 'guest', password or 'guest'),
            self.rabbit.connection.credentials
        )
        self.assertTrue(self.rabbit.channel)
        mock_set_as_connected.assert_called_once()
        mock_blocking_connection.assert_called_once()
        mock_channel.assert_called_once()

    @parameterized.expand([
        ("password_only_blank", 'test_user', ''),
        ("password_only_none", 'test_user', None),
        ("username_only_blank", '', 'test_password'),
        ("username_only_none", None, 'test_password'),
    ])
    @mock.patch.object(TestConnection, "channel", autospec=True)
    @mock.patch("pika.BlockingConnection", autospec=True)
    @mock.patch.object(RabbitMQApi, "_set_as_connected", autospec=True)
    def test_connect_unsafe_raises_exception_if_single_credential_invalid(
            self, name: str, username: Optional[str], password: Optional[str],
            mock_set_as_connected: MagicMock,
            mock_blocking_connection: MagicMock, mock_channel: MagicMock
    ):
        mock_set_as_connected.return_value = None
        mock_blocking_connection.return_value = None
        mock_channel.return_value = None

        self.rabbit._username = username
        self.rabbit._password = password
        self.assertRaises(BlankCredentialException, self.rabbit.connect_unsafe)
        self.assertIsNone(self.rabbit.connection)
        self.assertIsNone(self.rabbit.channel)
        mock_set_as_connected.assert_not_called()
        mock_blocking_connection.assert_not_called()
        mock_channel.assert_not_called()

    @parameterized.expand([
        ("connect unsafe returns none", None),
        ("connect unsafe returns 10", 10),
        ("connect unsafe returns -1y", -1)
    ])
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_connect_successful_returns_same_if(
            self, name: str, expected_return: Optional[int],
            mock_safe: MagicMock
    ):
        mock_safe.return_value = expected_return
        self.assertEqual(expected_return, self.rabbit.connect())
        mock_safe.assert_called_once_with(
            self.rabbit, self.rabbit.connect_unsafe, [], -1
        )

    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_connect_propogates_errors(self, mock_safe: MagicMock):
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(Exception, self.rabbit.connect)
        mock_safe.assert_called_once_with(
            self.rabbit, self.rabbit.connect_unsafe, [], -1
        )

    @mock.patch.object(RabbitMQApi, "_set_as_disconnected", autospec=True)
    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    def test_disconnect_unsafe_closes_connection_if_connected(
            self, mock_connection: PropertyMock,
            mock_set_as_disconnected: MagicMock,
    ):
        mock_connection.return_value.is_open.return_value = True
        mock_connection.return_value.close.return_value = None
        mock_set_as_disconnected.return_value = None
        self.assertIsNone(self.rabbit.disconnect_unsafe())
        mock_connection.return_value.close.assert_called_once_with()
        mock_set_as_disconnected.assert_called_once_with(self.rabbit)

    @mock.patch.object(RabbitMQApi, "_set_as_disconnected", autospec=True)
    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    def test_disconnect_unsafe_does_nothing_if_not_connected(
            self, mock_connection: PropertyMock,
            mock_set_as_disconnected: MagicMock,
    ):
        mock_connection.return_value.is_open = False
        mock_connection.return_value.close.return_value = None
        mock_set_as_disconnected.return_value = None
        self.assertIsNone(self.rabbit.disconnect_unsafe())
        mock_connection.return_value.close.assert_not_called()
        mock_set_as_disconnected.assert_called_once_with(self.rabbit)

    @parameterized.expand([
        ("disconnect unsafe returns none", None),
        ("disconnect unsafe returns 10", 10),
        ("disconnect unsafe returns -1y", -1)
    ])
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_disconnect_if_connected_successful_returns_same_if(
            self, name: str, expected_return: Optional[int],
            mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = True
        mock_safe.return_value = expected_return
        self.assertEqual(expected_return, self.rabbit.disconnect())
        mock_safe.assert_called_once_with(
            self.rabbit, self.rabbit.disconnect_unsafe, [], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_disconnect_if_not_connected_does_nothing(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.disconnect())
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_disconnect_propogates_errors(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(Exception, self.rabbit.disconnect)
        mock_safe.assert_called_once_with(
            self.rabbit, self.rabbit.disconnect_unsafe, [], -1
        )

    @mock.patch.object(RabbitMQApi, "perform_operation_till_successful",
                       autospec=True)
    def test_connect_till_successful_returns_nothing(
            self, mock_perform_operation_till_successful: MagicMock,
    ):
        mock_perform_operation_till_successful.return_value = "dummy return"
        self.assertIsNone(self.rabbit.connect_till_successful())
        mock_perform_operation_till_successful.assert_called_once_with(
            self.rabbit, self.rabbit.connect, [], -1
        )

    @mock.patch.object(RabbitMQApi, "perform_operation_till_successful",
                       autospec=True)
    def test_connect_till_successful_even_after_a_number_of_tries(
            self, mock_perform_operation_till_successful: MagicMock,
    ):
        attempts = 3
        tries = 0

        def try_n_times_then_return(*args, **kwargs):
            nonlocal tries
            if attempts == tries:
                return None
            tries += 1
            print(tries)
            raise Exception("Test Excepton")

        mock_perform_operation_till_successful.side_effect = \
            try_n_times_then_return
        self.assertIsNone(self.rabbit.connect_till_successful())
        mock_perform_operation_till_successful.assert_called_with(
            self.rabbit, self.rabbit.connect, [], -1
        )
        self.assertEqual(4, mock_perform_operation_till_successful.call_count)

    @mock.patch.object(RabbitMQApi, "perform_operation_till_successful",
                       autospec=True)
    def test_disconnect_till_successful_returns_nothing(
            self, mock_perform_operation_till_successful: MagicMock,
    ):
        mock_perform_operation_till_successful.return_value = "dummy return"
        self.assertIsNone(self.rabbit.disconnect_till_successful())
        mock_perform_operation_till_successful.assert_called_once_with(
            self.rabbit, self.rabbit.disconnect, [], -1
        )

    @mock.patch.object(RabbitMQApi, "perform_operation_till_successful",
                       autospec=True)
    def test_disconnect_till_successful_even_after_a_number_of_tries(
            self, mock_perform_operation_till_successful: MagicMock,
    ):
        attempts = 3
        tries = 0

        def try_n_times_then_return(*args, **kwargs):
            nonlocal tries
            if attempts == tries:
                return None
            tries += 1
            print(tries)
            raise Exception("Test Excepton")

        mock_perform_operation_till_successful.side_effect = \
            try_n_times_then_return
        self.assertIsNone(self.rabbit.disconnect_till_successful())
        mock_perform_operation_till_successful.assert_called_with(
            self.rabbit, self.rabbit.disconnect, [], -1
        )
        self.assertEqual(4, mock_perform_operation_till_successful.call_count)

    @parameterized.expand([
        ((0, "Test"),),
        (None,),
        ((1, ""),),
        ((-1, "Testing"),)
    ])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_declare_returns_same_if_successful(
            self, expected_output: Optional[Union[int, str]],
            mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.queue_bind.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.queue_declare(
            "test_queue", passive=False, durable=True, exclusive=True,
            auto_delete=False
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_declare,
            ["test_queue", False, True, True, False], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_declare_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.queue_declare(
            "test_queue", passive=False, durable=True, exclusive=True,
            auto_delete=False
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_declare_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.queue_declare.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.queue_declare, "test_queue", passive=False,
            durable=True, exclusive=True, auto_delete=False
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_declare,
            ["test_queue", False, True, True, False], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_bind_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock
    ):
        mock_channel.return_value.queue_bind.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.queue_bind(
            "test_queue", "TEST_EXCHANGE", routing_key="test.key"
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_bind,
            ["test_queue", "TEST_EXCHANGE", "test.key"], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_bind_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.queue_bind(
            "test_queue", "TEST_EXCHANGE", routing_key="test.key"
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_bind_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.queue_bind.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.queue_bind, "test_queue", "TEST_EXCHANGE",
            routing_key="test.key"
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_bind,
            ["test_queue", "TEST_EXCHANGE", "test.key"], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_publish_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.basic_publish.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.basic_publish(
            "TEST_EXCHANGE", "test.key", "Test Body", is_body_dict=False,
            properties=pika.BasicProperties(), mandatory=True
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_publish,
            ["TEST_EXCHANGE", "test.key", "Test Body", pika.BasicProperties(),
             True], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_publish_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.basic_publish(
            "TEST_EXCHANGE", "test.key", "Test Body", is_body_dict=False,
            properties=pika.BasicProperties(), mandatory=True
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_publish_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.basic_publish.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.basic_publish, "TEST_EXCHANGE", "test.key",
            "Test Body", is_body_dict=False, properties=pika.BasicProperties(),
            mandatory=True
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_publish,
            ["TEST_EXCHANGE", "test.key", "Test Body", pika.BasicProperties(),
             True], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "basic_publish")
    def test_basic_publish_confirm_successful_returns_same(
            self, expected_out: Optional[int], mock_basic_publish: MagicMock
    ):
        mock_basic_publish.return_value = expected_out
        self.assertEqual(expected_out, self.rabbit.basic_publish_confirm(
            "TEST_EXCHANGE", "test.key", "Test Body", is_body_dict=False,
            properties=pika.BasicProperties(), mandatory=True
        ))
        mock_basic_publish.assert_called_once_with(
            "TEST_EXCHANGE", "test.key", "Test Body", False,
            pika.BasicProperties(), True
        )

    @mock.patch.object(RabbitMQApi, "basic_publish")
    def test_basic_publish_confirm_unroutable_error_raises_not_delivered(
            self, mock_basic_publish: MagicMock
    ):
        mock_basic_publish.side_effect = pika.exceptions.UnroutableError(
            "Test Error")
        self.assertRaises(
            MessageWasNotDeliveredException, self.rabbit.basic_publish_confirm,
            "TEST_EXCHANGE", "test.key", "Test Body", is_body_dict=False,
            properties=pika.BasicProperties(), mandatory=True
        )
        mock_basic_publish.assert_called_once_with(
            "TEST_EXCHANGE", "test.key", "Test Body", False,
            pika.BasicProperties(), True
        )

    @mock.patch.object(RabbitMQApi, "basic_publish")
    def test_basic_publish_confirm_propogrates_other_errors(
            self, mock_basic_publish: MagicMock
    ):
        mock_basic_publish.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.basic_publish_confirm, "TEST_EXCHANGE",
            "test.key", "Test Body", is_body_dict=False,
            properties=pika.BasicProperties(), mandatory=True
        )
        mock_basic_publish.assert_called_once_with(
            "TEST_EXCHANGE", "test.key", "Test Body", False,
            pika.BasicProperties(), True
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_consume_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.basic_consume.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.basic_consume(
            "TEST_EXCHANGE", dummy_function, auto_ack=True, exclusive=True,
            consumer_tag="tag1"
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_consume,
            ["TEST_EXCHANGE", dummy_function, True, True, "tag1"], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_consume_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.basic_consume(
            "TEST_EXCHANGE", dummy_function, auto_ack=True, exclusive=True,
            consumer_tag="tag1"
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_consume_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.basic_consume.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.basic_consume, "TEST_EXCHANGE",
            dummy_function, auto_ack=True, exclusive=True,
            consumer_tag="tag1"
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_consume,
            ["TEST_EXCHANGE", dummy_function, True, True, "tag1"], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_get_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.basic_get.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.basic_get(
            "test_queue", auto_ack=True
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_get,
            ["test_queue", True], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_get_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.basic_get("test_queue", auto_ack=True))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_get_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.basic_get.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.basic_get, "test_queue", auto_ack=True
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_get,
            ["test_queue", True], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_start_consuming_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.start_consuming.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.start_consuming())
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.start_consuming, [], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_start_consuming_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.start_consuming())
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_start_consuming_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.start_consuming.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(Exception, self.rabbit.start_consuming)
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.start_consuming, [], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_ack_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.basic_ack.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.basic_ack(
            delivery_tag=100, multiple=True
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_ack, [100, True], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_ack_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(
            self.rabbit.basic_ack(delivery_tag=100, multiple=True)
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_ack_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.basic_ack.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(Exception, self.rabbit.basic_ack, delivery_tag=100,
                          multiple=True)
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_ack, [100, True], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_qos_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.basic_qos.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.basic_qos(
            prefetch_size=10, prefetch_count=100, global_qos=True
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_qos, [10, 100, True],
            -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_qos_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.basic_qos(
            prefetch_size=10, prefetch_count=100, global_qos=True
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_basic_qos_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.basic_qos.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.basic_qos, prefetch_size=10,
            prefetch_count=100, global_qos=True
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.basic_qos,
            [10, 100, True], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_exchange_declare_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.exchange_declare.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.exchange_declare(
            "TEST_EXCHANGE", exchange_type="topic", passive=False, durable=True,
            auto_delete=True, internal=False
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.exchange_declare,
            ["TEST_EXCHANGE", "topic", False, True, True, False], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_exchange_declare_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.exchange_declare(
            "TEST_EXCHANGE", exchange_type="topic", passive=False, durable=True,
            auto_delete=True, internal=False
        ))
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_exchange_declare_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.exchange_declare.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.exchange_declare, "TEST_EXCHANGE",
            exchange_type="topic", passive=False, durable=True,
            auto_delete=True, internal=False
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.exchange_declare,
            ["TEST_EXCHANGE", "topic", False, True, True, False], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_confirm_delivery_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.confirm_delivery.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.confirm_delivery())

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.confirm_delivery, [], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_confirm_delivery_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.confirm_delivery())

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_confirm_delivery_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.confirm_delivery.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(Exception, self.rabbit.confirm_delivery)
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.confirm_delivery, [], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_purge_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.queue_purge.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.queue_purge("test_queue"))

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_purge, ["test_queue"],
            -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_purge_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.queue_purge("test_queue"))

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_purge_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.queue_purge.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(Exception, self.rabbit.queue_purge, "test_queue")
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_purge, ["test_queue"],
            -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_exchange_delete_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.exchange_delete.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.exchange_delete(
            exchange="TEST_EXCHANGE", if_unused=True
        ))

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.exchange_delete,
            ["TEST_EXCHANGE", True], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_exchange_delete_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.exchange_delete(
            exchange="TEST_EXCHANGE,", if_unused=True
        ))

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_exchange_delete_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.exchange_delete.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.exchange_delete, exchange="TEST_EXCHANGE",
            if_unused=True
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.exchange_delete,
            ["TEST_EXCHANGE", True], -1
        )

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_delete_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock, mock_channel: PropertyMock

    ):
        mock_channel.return_value.queue_delete.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.queue_delete(
            queue="test_queue", if_unused=True, if_empty=True
        ))

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_delete,
            ["test_queue", True, True], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_delete_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.queue_delete(
            queue="test_queue", if_unused=True, if_empty=True
        ))

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_queue_delete_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_channel: PropertyMock
    ):
        mock_channel.return_value.queue_delete.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(
            Exception, self.rabbit.queue_delete, queue="test_queue",
            if_unused=True, if_empty=True
        )
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, mock_channel.return_value.queue_delete,
            ["test_queue", True, True], -1
        )

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    def test_new_channel_unsafe_creates_channel_if_not_open(
            self, mock_channel: PropertyMock, mock_connection: PropertyMock
    ):
        mock_channel.return_value.is_open.return_value = False
        mock_channel.return_value.close.return_value = None
        mock_connection.return_value.channel.return_value = "Test Channel"
        self.rabbit.new_channel_unsafe()
        self.assertEqual("Test Channel", self.rabbit._channel)
        mock_connection.return_value.close.assert_not_called()
        mock_connection.return_value.channel.assert_called_once_with()

    @mock.patch.object(RabbitMQApi, "connection", new_callable=PropertyMock)
    @mock.patch.object(RabbitMQApi, "channel", new_callable=PropertyMock)
    def test_new_channel_unsafe_creates_channel_closes_if_open(
            self, mock_channel: PropertyMock, mock_connection: PropertyMock
    ):
        mock_channel.return_value.is_open.return_value = True
        mock_channel.return_value.close.return_value = None
        mock_connection.return_value.channel.return_value = "Test Channel"

        self.rabbit.new_channel_unsafe()
        self.assertEqual("Test Channel", self.rabbit._channel)
        mock_channel.return_value.close.assert_called_once_with()
        mock_connection.return_value.channel.assert_called_once_with()

    @parameterized.expand([(0,), (None,), (1,), (-1,)])
    @mock.patch.object(RabbitMQApi, "new_channel_unsafe", autospec=True)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_new_channel_returns_same_if_successful(
            self, expected_output: Optional[int], mock_safe: MagicMock,
            mock_connection_initialised: MagicMock,
            mock_new_channel_unsafe: PropertyMock
    ):
        mock_new_channel_unsafe.return_value = False
        mock_safe.return_value = expected_output
        mock_connection_initialised.return_value = True
        self.assertEqual(expected_output, self.rabbit.new_channel())

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, self.rabbit.new_channel_unsafe, [], -1
        )

    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_new_channel_does_nothing_if_not_connection_initialised(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock
    ):
        mock_connection_initialised.return_value = False
        self.assertIsNone(self.rabbit.new_channel())

        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_not_called()

    @mock.patch.object(RabbitMQApi, "new_channel_unsafe", autospec=True)
    @mock.patch.object(RabbitMQApi, "_connection_initialised", autospec=True)
    @mock.patch.object(RabbitMQApi, "_safe", autospec=True)
    def test_new_channel_propagates_error(
            self, mock_safe: MagicMock, mock_connection_initialised: MagicMock,
            mock_new_channel_unsafe: PropertyMock
    ):
        mock_new_channel_unsafe.return_value = False
        mock_connection_initialised.return_value = True
        mock_safe.side_effect = Exception("Test Exception")
        self.assertRaises(Exception, self.rabbit.new_channel)
        mock_connection_initialised.assert_called_once_with(self.rabbit)
        mock_safe.assert_called_once_with(
            self.rabbit, self.rabbit.new_channel_unsafe, [], -1
        )

    @mock.patch.object(RabbitMQApi, "connection_check_time_interval_seconds",
                       new_callable=PropertyMock)
    def test_perform_operation_till_successful_no_retry_if_not_default(
            self, mock_connection_check_time_interval_seconds: PropertyMock
    ):
        def test_function():
            return "OK"

        mock_connection_check_time_interval_seconds.return_value = 10
        self.assertIsNone(
            self.rabbit.perform_operation_till_successful(test_function, [], -1)
        )

    @mock.patch.object(RabbitMQApi, "connection_check_time_interval_seconds",
                       new_callable=PropertyMock)
    def test_perform_operation_till_successful_retries_if_default_return(
            self, mock_connection_check_time_interval_seconds: PropertyMock
    ):
        attempt = 0
        retries = 3

        def test_function(retries):
            nonlocal attempt
            if attempt == retries:
                return "OK"
            else:
                attempt += 1
                return -1

        mock_connection_check_time_interval_seconds.return_value = 10
        self.assertIsNone(self.rabbit.perform_operation_till_successful(
            test_function, [retries], -1
        ))
