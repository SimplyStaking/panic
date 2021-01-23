import logging
import unittest
from datetime import timedelta

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
            "Alert Router", self._alert_router_logger, self._rabbit_ip, self._redis_ip,
            self._redis_db, self._redis_port, "test_alerter", True, True
        )

    def tearDown(self) -> None:
        # flush and consume all from rabbit queues and exchanges
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.queue_purge(ALERT_ROUTER_CONFIGS_QUEUE_NAME)
        self._rabbitmq.queue_delete(ALERT_ROUTER_CONFIGS_QUEUE_NAME)

        exchanges = [
            ALERT_EXCHANGE, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
            STORE_EXCHANGE
        ]

        for exchange in exchanges:
            self._rabbitmq.channel.exchange_delete(exchange)

        self._rabbitmq.disconnect_till_successful()

    def test_alert_router_initialised(self):
        self.assertIsNotNone(self._test_alert_router)
