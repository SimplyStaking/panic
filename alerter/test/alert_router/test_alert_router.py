import logging
import unittest
from datetime import timedelta

import pika.exceptions

from src.alert_router.alert_router import AlertRouter
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (CONFIG_EXCHANGE, ALERT_EXCHANGE,
                                 STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 ALERT_ROUTER_CONFIGS_QUEUE_NAME)


class TestAlertRouter(unittest.TestCase):
    def setUp(self) -> None:
        self._alert_router_logger = logging.getLogger('test_alert_router')
        self._rabbit_logger = logging.getLogger('test_rabbit')
        self._redis_logger = logging.getLogger('test_reids')
        self._connection_check_time_interval = timedelta(seconds=0)

        self._rabbit_ip = 'localhost'
        self._config_exchange = CONFIG_EXCHANGE
        self._alert_input_exchange = ALERT_EXCHANGE

        self._redis_ip = 'localhost'
        self._redis_db = 1
        self._redis_port = 6379

        self._rabbitmq = RabbitMQApi(
            self._rabbit_logger, self._rabbit_ip,
            connection_check_time_interval=self._connection_check_time_interval)

        self._redis = RedisApi(self._redis_logger, self._redis_db,
                               self._redis_ip, self._redis_port)

        self._test_channel_config_file = {
            'channels.test_channel': {
                'id': "test_123",
                'channel_name': "test_channel",
                'info': "false",
                'warning': "false",
                'critical': "false",
                'error': "false",
                'parent_ids': "GENERAL,",
                'parent_names': ""
            }
        }

        self._test_alert_router = AlertRouter(
            "Alert Router", self._alert_router_logger, self._rabbit_ip,
            self._redis_ip,
            self._redis_db, self._redis_port, "test_alerter", True, True
        )

    def tearDown(self) -> None:
        # flush and consume all from rabbit queues and exchanges
        self._rabbitmq.connect_till_successful()

        try:
            self._rabbitmq.queue_declare(ALERT_ROUTER_CONFIGS_QUEUE_NAME,
                                         passive=True)
            self._rabbitmq.queue_purge(ALERT_ROUTER_CONFIGS_QUEUE_NAME)
            self._rabbitmq.queue_delete(ALERT_ROUTER_CONFIGS_QUEUE_NAME)
        except pika.exceptions.ChannelClosedByBroker as e:
            print("Queue {} does not exist - don't need to close".format(
                ALERT_ROUTER_CONFIGS_QUEUE_NAME
            ))

        exchanges = [
            ALERT_EXCHANGE, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
            STORE_EXCHANGE
        ]

        for exchange in exchanges:
            try:
                self._rabbitmq.exchange_declare(exchange, passive=True)
                self._rabbitmq.channel.exchange_delete(exchange)
            except pika.exceptions.ChannelClosedByBroker as e:
                print("Exchange {} does not exist - don't need to close".format(
                    exchange))

        self._rabbitmq.disconnect_till_successful()

    def test_alert_router_initialised(self):
        self.assertIsNotNone(self._test_alert_router)

    def test_name(self):
        self.assertEqual("Alert Router", self._test_alert_router.name)

    def test__initialise_rabbit(self):
        self.fail()

    def test__declare_exchange_and_bind_queue(self):
        self.fail()

    def test__process_configs(self):
        self.fail()

    def test__process_alert(self):
        self.fail()

    def test__process_ping(self):
        self.fail()

    def test_start(self):
        self.fail()

    def test_disconnect_from_rabbit(self):
        self.fail()

    def test_on_terminate(self):
        self.fail()

    def test__extract_config(self):
        self.fail()

    def test_is_all_muted(self):
        self.fail()

    def test_is_chain_severity_muted(self):
        self.fail()
