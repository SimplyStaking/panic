import logging
import unittest
from datetime import timedelta

from src.config_manager import ConfigsManager
from src.message_broker.rabbitmq import RabbitMQApi


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

    def tearDown(self) -> None:
        pass

    def test_instance_created(self):
        self.assertIsNotNone(self.test_config_manager)
        
    @unittest.skip
    def test_name(self):
        self.fail()

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
