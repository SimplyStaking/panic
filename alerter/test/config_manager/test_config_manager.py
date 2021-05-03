import copy
import json
import logging
import unittest
from configparser import ConfigParser
from datetime import timedelta, datetime
from typing import Dict, Any
from unittest import mock
from unittest.mock import MagicMock

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized
from watchdog.events import (
    FileCreatedEvent, FileModifiedEvent, FileSystemEvent, FileDeletedEvent
)
from watchdog.observers.polling import PollingObserver

from src.config_manager import ConfigsManager
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 CONFIGS_MANAGER_HEARTBEAT_QUEUE)
from test.utils.utils import (
    delete_exchange_if_exists, delete_queue_if_exists,
    disconnect_from_rabbit, connect_to_rabbit
)


class TestConfigsManager(unittest.TestCase):
    def setUp(self) -> None:
        self.CONFIG_MANAGER_NAME = "Config Manager"
        self.config_manager_logger = logging.getLogger("test_config_manager")
        self.config_manager_logger.disabled = True
        self.rabbit_logger = logging.getLogger("test_rabbit")
        self.rabbit_logger.disabled = True
        self.config_directory = "config"
        file_patterns = ["*.ini"]
        rabbit_ip = env.RABBIT_IP

        self.test_config_manager = ConfigsManager(
            self.CONFIG_MANAGER_NAME, self.config_manager_logger,
            self.config_directory, rabbit_ip, file_patterns=file_patterns
        )

        self.rabbitmq = RabbitMQApi(
            self.rabbit_logger, rabbit_ip,
            connection_check_time_interval=timedelta(seconds=0)
        )

    def tearDown(self) -> None:
        # flush and consume all from rabbit queues and exchanges
        connect_to_rabbit(self.rabbitmq)

        queues = [CONFIGS_MANAGER_HEARTBEAT_QUEUE]
        for queue in queues:
            delete_queue_if_exists(self.rabbitmq, queue)

        exchanges = [CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE]
        for exchange in exchanges:
            delete_exchange_if_exists(self.rabbitmq, exchange)

        disconnect_from_rabbit(self.rabbitmq)
        self.rabbitmq = None
        self.test_config_manager._rabbitmq = None
        self.test_config_manager._heartbeat_rabbit = None
        self.test_config_manager = None

    def test_instance_created(self):
        self.assertIsNotNone(self.test_config_manager)

    def test_name_returns_component_name(self):
        self.assertEqual(
            self.CONFIG_MANAGER_NAME, self.test_config_manager.name
        )

    @parameterized.expand([
        (CONFIGS_MANAGER_HEARTBEAT_QUEUE,),
    ])
    @mock.patch.object(RabbitMQApi, "confirm_delivery")
    @mock.patch.object(RabbitMQApi, "basic_consume")
    @mock.patch.object(RabbitMQApi, "basic_qos")
    def test__initialise_rabbit_initialises_queues(
            self, queue_to_check: str, mock_basic_qos: MagicMock,
            mock_basic_consume: MagicMock, mock_confirm_delivery: MagicMock
    ):
        mock_basic_consume.return_value = None
        mock_confirm_delivery.return_value = None
        try:
            connect_to_rabbit(self.rabbitmq)

            # Testing this separately since this is a critical function
            self.test_config_manager._initialise_rabbitmq()

            mock_basic_qos.assert_called_once()
            mock_basic_consume.assert_called_once()
            mock_confirm_delivery.assert_called()

            self.rabbitmq.queue_declare(queue_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Queue {} was not declared".format(queue_to_check))
        finally:
            disconnect_from_rabbit(self.test_config_manager._rabbitmq)
            disconnect_from_rabbit(self.test_config_manager._heartbeat_rabbit)

    @parameterized.expand([
        (CONFIG_EXCHANGE,),
        (HEALTH_CHECK_EXCHANGE,),
    ])
    @mock.patch.object(RabbitMQApi, "confirm_delivery")
    @mock.patch.object(RabbitMQApi, "basic_consume")
    @mock.patch.object(RabbitMQApi, "basic_qos")
    def test__initialise_rabbit_initialises_exchanges(
            self, exchange_to_check: str, mock_basic_qos: MagicMock,
            mock_basic_consume: MagicMock, mock_confirm_delivery: MagicMock
    ):
        mock_basic_consume.return_value = None
        mock_confirm_delivery.return_value = None

        try:
            connect_to_rabbit(self.rabbitmq)

            # Testing this separately since this is a critical function
            self.test_config_manager._initialise_rabbitmq()

            mock_basic_qos.assert_called_once()
            mock_basic_consume.assert_called()
            mock_confirm_delivery.assert_called()

            self.rabbitmq.exchange_declare(exchange_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Exchange {} was not declared".format(exchange_to_check))
        finally:
            disconnect_from_rabbit(self.test_config_manager._rabbitmq)
            disconnect_from_rabbit(self.test_config_manager._heartbeat_rabbit)

    @mock.patch.object(RabbitMQApi, "connect_till_successful", autospec=True)
    def test__connect_to_rabbit(self, mock_connect: MagicMock):
        mock_connect.return_value = None
        self.test_config_manager._connect_to_rabbit()

        mock_connect.assert_called()
        self.assertEqual(2, mock_connect.call_count)
        self.assertTrue(self.test_config_manager.connected_to_rabbit)

    @mock.patch.object(RabbitMQApi, "disconnect_till_successful", autospec=True)
    def test_disconnect_from_rabbit(self, mock_disconnect: MagicMock):
        mock_disconnect.return_value = None
        self.test_config_manager._connected_to_rabbit = True
        self.test_config_manager.disconnect_from_rabbit()
        mock_disconnect.assert_called()
        self.assertEqual(2, mock_disconnect.call_count)
        self.assertFalse(self.test_config_manager.connected_to_rabbit)

    @freeze_time("1997-08-15T10:21:33.000030")
    @mock.patch.object(PollingObserver, "is_alive", autospec=True)
    def test__process_ping_sends_valid_hb(self, mock_is_alive: MagicMock):
        mock_is_alive.return_value = True

        expected_output = {
            'component_name': self.CONFIG_MANAGER_NAME,
            'is_alive': True,
            'timestamp': datetime(
                year=1997, month=8, day=15, hour=10, minute=21, second=33,
                microsecond=30
            ).timestamp()
        }
        HEARTBEAT_QUEUE = "hb_test"
        try:
            connect_to_rabbit(self.rabbitmq)
            self.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, "topic", False, True, False, False
            )

            queue_res = self.rabbitmq.queue_declare(
                queue=HEARTBEAT_QUEUE, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, queue_res.method.message_count)

            self.rabbitmq.queue_bind(
                HEARTBEAT_QUEUE, HEALTH_CHECK_EXCHANGE, "heartbeat.*"
            )

            self.test_config_manager._initialise_rabbitmq()

            blocking_channel = self.test_config_manager._rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key="ping"
            )
            properties = pika.spec.BasicProperties()

            self.test_config_manager._process_ping(
                blocking_channel, method_chains, properties, b"ping"
            )

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            queue_res = self.rabbitmq.queue_declare(
                queue=HEARTBEAT_QUEUE, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, queue_res.method.message_count)

            # Check that the message received is a valid HB
            _, _, body = self.rabbitmq.basic_get(HEARTBEAT_QUEUE)
            self.assertDictEqual(expected_output, json.loads(body))
        finally:
            delete_queue_if_exists(self.rabbitmq, HEARTBEAT_QUEUE)
            delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
            disconnect_from_rabbit(self.test_config_manager._rabbitmq)
            disconnect_from_rabbit(self.test_config_manager._heartbeat_rabbit)

    @parameterized.expand([
        (FileCreatedEvent("test_config"),
         """ [test_section_1]
             test_field_1=Hello
             test_field_2=
             test_field_3=10
             test_field_4=true
         """,
         {"DEFAULT": {},
          "test_section_1": {
              "test_field_1": "Hello",
              "test_field_2": "",
              "test_field_3": "10",
              "test_field_4": "true"
          }}),
        (FileModifiedEvent("test_config"),
         """ [test_section_1]
             test_field_1=Hello
             test_field_2=
             test_field_3=10
             test_field_4=true

            [test_section_2]
            test_field_1=OK
            test_field_2=Bye
            test_field_3=4
            test_field_4=off
         """,
         {
             "DEFAULT": {},
             "test_section_1": {
                 "test_field_1": "Hello",
                 "test_field_2": "",
                 "test_field_3": "10",
                 "test_field_4": "true"
             },
             "test_section_2": {
                 "test_field_1": "OK",
                 "test_field_2": "Bye",
                 "test_field_3": "4",
                 "test_field_4": "off"
             }
         }),
        (FileDeletedEvent("test_config"), "", {}),
    ])
    @mock.patch.object(ConfigParser, "read", autospec=True)
    @mock.patch.object(ConfigsManager, "_send_data", autospec=True)
    @mock.patch("src.utils.routing_key.get_routing_key", autospec=True)
    def test__on_event_thrown(
            self, event_to_trigger: FileSystemEvent, config_file_input: str,
            expected_dict: Dict, mock_get_routing_key: MagicMock,
            mock_send_data: MagicMock, mock_config_parser: MagicMock
    ):
        TEST_ROUTING_KEY = "test_config"

        def read_config_side_effect(cp: ConfigParser, *args, **kwargs) -> None:
            """
            cp would be "self" in the context of this function being injected.
            """
            cp.read_string(config_file_input)

        mock_get_routing_key.return_value = TEST_ROUTING_KEY
        mock_send_data.return_value = None
        mock_config_parser.side_effect = read_config_side_effect

        self.test_config_manager._on_event_thrown(event_to_trigger)

        mock_get_routing_key.assert_called_once()
        mock_send_data.assert_called_once_with(
            self.test_config_manager, expected_dict, TEST_ROUTING_KEY
        )

    @parameterized.expand([
        ({},),
        ({"DEFAULT": {},
          "test_section_1": {
              "test_field_1": "Hello",
              "test_field_2": "",
              "test_field_3": "10",
              "test_field_4": "true"
          }},),
        ({
             "DEFAULT": {},
             "test_section_1": {
                 "test_field_1": "Hello",
                 "test_field_2": "",
                 "test_field_3": "10",
                 "test_field_4": "true"
             },
             "test_section_2": {
                 "test_field_1": "OK",
                 "test_field_2": "Bye",
                 "test_field_3": "4",
                 "test_field_4": "off"
             }
         },),
    ])
    def test_send_data(self, config: Dict[str, Any]):
        route_key = "test.route"
        CONFIG_QUEUE = "hb_test"
        try:
            self.test_config_manager._initialise_rabbitmq()

            connect_to_rabbit(self.rabbitmq)
            queue_res = self.rabbitmq.queue_declare(
                queue=CONFIG_QUEUE, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, queue_res.method.message_count)

            self.rabbitmq.queue_bind(
                CONFIG_QUEUE, CONFIG_EXCHANGE, route_key
            )

            self.test_config_manager._send_data(copy.deepcopy(config),
                                                route_key)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            queue_res = self.rabbitmq.queue_declare(
                queue=CONFIG_QUEUE, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, queue_res.method.message_count)

            # Check that the message received is what's expected
            _, _, body = self.rabbitmq.basic_get(CONFIG_QUEUE)
            self.assertDictEqual(config, json.loads(body))
        finally:
            delete_queue_if_exists(self.rabbitmq, CONFIG_QUEUE)
            disconnect_from_rabbit(self.test_config_manager._rabbitmq)
            disconnect_from_rabbit(self.test_config_manager._heartbeat_rabbit)

    @mock.patch.object(ConfigsManager, "_initialise_rabbitmq", autospec=True)
    @mock.patch.object(ConfigsManager, "foreach_config_file", autospec=True)
    @mock.patch.object(PollingObserver, "start", autospec=True)
    @mock.patch.object(RabbitMQApi, "start_consuming", autospec=True)
    def test_start_not_watching(
            self, mock_start_consuming: MagicMock,
            mock_observer_start: MagicMock, mock_foreach: MagicMock,
            mock_initialise_rabbit: MagicMock
    ):
        self.test_config_manager._watching = False
        mock_foreach.return_value = None
        mock_initialise_rabbit.return_value = None
        mock_observer_start.return_value = None
        mock_start_consuming.return_value = None
        self.test_config_manager.start()

        mock_initialise_rabbit.assert_called_once()
        mock_foreach.assert_called_once()
        mock_observer_start.assert_called_once()
        mock_start_consuming.assert_called_once()

        disconnect_from_rabbit(self.test_config_manager._rabbitmq)
        disconnect_from_rabbit(self.test_config_manager._heartbeat_rabbit)

    @mock.patch.object(ConfigsManager, "_initialise_rabbitmq", autospec=True)
    @mock.patch.object(ConfigsManager, "foreach_config_file", autospec=True)
    @mock.patch.object(PollingObserver, "start", autospec=True)
    def test_start_after_watching(
            self, mock_observer_start: MagicMock, mock_foreach: MagicMock,
            mock_initialise_rabbit: MagicMock
    ):
        self.test_config_manager._watching = True
        mock_foreach.return_value = None
        mock_initialise_rabbit.return_value = None
        mock_observer_start.return_value = None
        self.test_config_manager.start()

        mock_initialise_rabbit.assert_called_once()
        mock_foreach.assert_called_once()
        mock_observer_start.assert_not_called()

        disconnect_from_rabbit(self.test_config_manager._rabbitmq)
        disconnect_from_rabbit(self.test_config_manager._heartbeat_rabbit)

    @mock.patch('sys.exit', autospec=True)
    @mock.patch.object(ConfigsManager, "disconnect_from_rabbit", autospec=True)
    def test__on_terminate_when_not_observing(
            self, mock_disconnect: MagicMock, mock_sys_exit: MagicMock
    ):
        mock_disconnect.return_value = None
        mock_sys_exit.return_value = None
        # We mock the stack frame since we don't need it.
        mock_signal = MagicMock()
        mock_stack_frame = MagicMock()

        self.test_config_manager._on_terminate(mock_signal, mock_stack_frame)
        self.assertFalse(self.test_config_manager._watching)
        mock_disconnect.assert_called_once()
        mock_sys_exit.assert_called_once()

    @mock.patch('sys.exit', autospec=True)
    @mock.patch.object(ConfigsManager, "disconnect_from_rabbit", autospec=True)
    @mock.patch.object(PollingObserver, "stop", autospec=True)
    @mock.patch.object(PollingObserver, "join", autospec=True)
    def test__on_terminate_when_observing(
            self, mock_join: MagicMock, mock_stop: MagicMock,
            mock_disconnect: MagicMock, mock_sys_exit: MagicMock
    ):
        mock_join.return_value = None
        mock_stop.return_value = None
        mock_disconnect.return_value = None
        mock_sys_exit.return_value = None

        self.test_config_manager._watching = True
        # We mock the signal and stack frame since we don't need them.
        mock_signal = MagicMock()
        mock_stack_frame = MagicMock()

        self.test_config_manager._on_terminate(mock_signal, mock_stack_frame)
        self.assertFalse(self.test_config_manager._watching)
        mock_disconnect.assert_called_once()
        mock_stop.assert_called_once()
        mock_join.assert_called_once()
        mock_sys_exit.assert_called_once()

    @mock.patch("os.path.join", autospec=True)
    @mock.patch("os.walk", autospec=True)
    def test_foreach_config_file(
            self, mock_os_walk: MagicMock, mock_os_path_join: MagicMock
    ):
        def os_walk_fn(directory: str):
            file_system = [
                ('/foo', ('bar',), ('baz.ini',)),
                ('/foo/bar', (), ('spam.ini', 'eggs.txt')),
            ]
            for root, dirs, files in file_system:
                yield root, dirs, files

        def test_callback(input: str) -> None:
            self.assertIn(input, ['/foo/baz.ini', '/foo/bar/spam.ini'])

        mock_os_walk.side_effect = os_walk_fn
        mock_os_path_join.side_effect = lambda x, y: x + "/" + y
        self.test_config_manager.foreach_config_file(test_callback)
