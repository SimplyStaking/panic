import logging
from datetime import timedelta
from unittest import TestCase, skip

from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env


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
        connection_check_time_interval = timedelta(seconds=100)
        rabbit = RabbitMQApi(
            self.rabbit_logger, self.rabbit_ip, self.rabbit_port, username,
            password, connection_check_time_interval
        )

        self.assertIsNotNone(rabbit)
        self.assertEqual(rabbit._logger, self.rabbit_logger)
        self.assertEqual(rabbit._host, self.rabbit_ip)
        self.assertEqual(rabbit._port, self.rabbit_port)
        self.assertEqual(rabbit.username, username)
        self.assertEqual(rabbit.password, password)
        self.assertEqual(connection_check_time_interval,
                         connection_check_time_interval)
        self.assertFalse(rabbit.is_connected)

    @skip("Not implemented yet")
    def test_live_check_limiter(self):
        pass

    @skip("Not implemented yet")
    def test__set_as_connected(self):
        pass

    @skip("Not implemented yet")
    def test__set_as_disconnected(self):
        pass

    @skip("Not implemented yet")
    def test__is_recently_disconnected(self):
        pass

    @skip("Not implemented yet")
    def test__safe(self):
        pass

    @skip("Not implemented yet")
    def test__connection_initialised(self):
        pass

    @skip("Not implemented yet")
    def test_connect_unsafe(self):
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
