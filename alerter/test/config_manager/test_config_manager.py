import logging
import unittest
from datetime import timedelta

import pika

from src.config_manager import ConfigsManager
from src.config_manager.config_manager import CONFIG_PING_QUEUE
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE


class TestConfigsManager(unittest.TestCase):
    def setUp(self) -> None:
        self.config_manager_name = "Config Manager"
        self.config_manager_logger = logging.getLogger("test_config_manager")
        self.rabbit_logger = logging.getLogger("test_rabbit")
        self.config_directory = "config"
        file_patterns = ["*.ini"]
        rabbit_ip = "localhost"

        self.test_config_manager = ConfigsManager(
            self.config_manager_name, self.config_manager_logger,
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
            self.config_manager_name, self.test_config_manager.name
        )

    @unittest.skip
    def test__initialise_rabbitmq(self):
        self.fail()

    @unittest.skip
    def test__connect_to_rabbit(self):
        self.fail()

    @unittest.skip
    def test_disconnect_from_rabbit(self):
        self.fail()

    @unittest.skip
    def test__send_heartbeat(self):
        self.fail()

    @unittest.skip
    def test__process_ping(self):
        self.fail()

    @unittest.skip
    def test__send_data(self):
        self.fail()

    @unittest.skip
    def test__on_event_thrown(self):
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
