import json
import logging
import unittest
from configparser import ConfigParser
from datetime import timedelta, datetime
from typing import Dict
from unittest import mock
from unittest.mock import MagicMock

import pika
from freezegun import freeze_time
from parameterized import parameterized
from watchdog.events import FileCreatedEvent, FileModifiedEvent, \
    FileSystemEvent, FileDeletedEvent
from watchdog.observers.polling import PollingObserver

from src.config_manager import ConfigsManager
from src.config_manager.config_manager import CONFIG_PING_QUEUE
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE


class TestConfigsManager(unittest.TestCase):
    def setUp(self) -> None:
        self.CONFIG_MANAGER_NAME = "Config Manager"
        self.config_manager_logger = logging.getLogger("test_config_manager")
        self.rabbit_logger = logging.getLogger("test_rabbit")
        self.config_directory = "config"
        file_patterns = ["*.ini"]
        rabbit_ip = "localhost"

        self.test_config_manager = ConfigsManager(
            self.CONFIG_MANAGER_NAME, self.config_manager_logger,
            self.config_directory, rabbit_ip, file_patterns=file_patterns
        )

        self.rabbitmq = RabbitMQApi(
            self.rabbit_logger, rabbit_ip,
            connection_check_time_interval=timedelta(seconds=0)
        )

    def connect_to_rabbit(self, attempts: int = 3) -> None:
        tries = 0

        while tries < attempts:
            try:
                self.rabbitmq.connect()
                return
            except Exception as e:
                tries += 1
                print("Could not connect to rabbit. Attempts so far: {}".format(
                    tries))
                print(e)
                if tries >= attempts:
                    raise e

    def disconnect_from_rabbit(self, attempts: int = 3) -> None:
        tries = 0

        while tries < attempts:
            try:
                self.rabbitmq.disconnect()
                return
            except Exception as e:
                tries += 1
                print("Could not connect to rabbit. Attempts so far: {}".format(
                    tries))
                print(e)
                if tries >= attempts:
                    raise e

    def delete_queue_if_exists(self, queue_name: str) -> None:
        try:
            self.rabbitmq.queue_declare(queue_name, passive=True)
            self.rabbitmq.queue_purge(queue_name)
            self.rabbitmq.queue_delete(queue_name)
        except pika.exceptions.ChannelClosedByBroker:
            print("Queue {} does not exist - don't need to close".format(
                queue_name
            ))

    def delete_exchange_if_exists(self, exchange_name: str) -> None:
        try:
            self.rabbitmq.exchange_declare(exchange_name, passive=True)
            self.rabbitmq.exchange_delete(exchange_name)
        except pika.exceptions.ChannelClosedByBroker:
            print("Exchange {} does not exist - don't need to close".format(
                exchange_name))

    def tearDown(self) -> None:
        # flush and consume all from rabbit queues and exchanges
        self.connect_to_rabbit()

        queues = [CONFIG_PING_QUEUE]
        for queue in queues:
            self.delete_queue_if_exists(queue)

        exchanges = [CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE]
        for exchange in exchanges:
            self.delete_exchange_if_exists(exchange)

        self.disconnect_from_rabbit()

    def test_instance_created(self):
        self.assertIsNotNone(self.test_config_manager)

    def test_name(self):
        self.assertEqual(
            self.CONFIG_MANAGER_NAME, self.test_config_manager.name
        )

    @parameterized.expand([
        (CONFIG_PING_QUEUE,),
    ])
    @mock.patch.object(RabbitMQApi, "confirm_delivery")
    @mock.patch.object(RabbitMQApi, "basic_consume")
    def test__initialise_rabbit_initialises_queues(
            self, queue_to_check: str, mock_basic_consume: MagicMock,
            mock_confirm_delivery: MagicMock
    ):
        mock_basic_consume.return_value = None
        mock_confirm_delivery.return_value = None
        try:
            self.connect_to_rabbit()

            # Testing this separately since this is a critical function
            self.test_config_manager._initialise_rabbitmq()

            mock_basic_consume.assert_called()
            mock_confirm_delivery.assert_called()

            self.rabbitmq.queue_declare(queue_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Queue {} was not declared".format(queue_to_check))
        finally:
            self.disconnect_from_rabbit()

    @parameterized.expand([
        (CONFIG_EXCHANGE,),
        (HEALTH_CHECK_EXCHANGE,),
    ])
    @mock.patch.object(RabbitMQApi, "confirm_delivery")
    @mock.patch.object(RabbitMQApi, "basic_consume")
    def test__initialise_rabbit_initialises_exchanges(
            self, exchange_to_check: str, mock_basic_consume: MagicMock,
            mock_confirm_delivery: MagicMock
    ):
        mock_basic_consume.return_value = None
        mock_confirm_delivery.return_value = None

        try:
            self.connect_to_rabbit()

            # Testing this separately since this is a critical function
            self.test_config_manager._initialise_rabbitmq()

            mock_basic_consume.assert_called()
            mock_confirm_delivery.assert_called()

            self.rabbitmq.exchange_declare(exchange_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Exchange {} was not declared".format(exchange_to_check))
        finally:
            self.disconnect_from_rabbit()

    @unittest.skip
    def test__connect_to_rabbit(self):
        self.fail()

    @unittest.skip
    def test_disconnect_from_rabbit(self):
        self.fail()

    @unittest.skip
    def test__send_heartbeat(self):
        self.fail()

    @freeze_time("1997-08-15T10:21:33.000030")
    @mock.patch.object(RabbitMQApi, "basic_ack", autospec=True)
    @mock.patch.object(PollingObserver, "is_alive", autospec=True)
    def test__process_ping_sends_valid_hb(
            self, mock_is_alive: MagicMock, mock_ack: MagicMock
    ):
        mock_ack.return_value = None
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
            self.connect_to_rabbit()
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
            self.delete_queue_if_exists(HEARTBEAT_QUEUE)
            self.delete_exchange_if_exists(HEALTH_CHECK_EXCHANGE)
            self.disconnect_from_rabbit()

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

    @unittest.skip
    def test__send_data(self):
        self.fail()

    @unittest.skip
    def test_config_directory(self):
        self.fail()

    @unittest.skip
    def test_watching(self):
        self.fail()

    @unittest.skip
    def test_connected_to_rabbit(self):
        self.fail()

    @unittest.skip
    def test_start(self):
        self.fail()

    @unittest.skip
    def test__on_terminate(self):
        self.fail()

    @unittest.skip
    def test_foreach_config_file(self):
        self.fail()
