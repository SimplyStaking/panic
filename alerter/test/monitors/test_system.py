import logging
import unittest
from datetime import timedelta

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.system import SystemMonitor
from src.utils.constants import RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE


class TestSystemMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(self.dummy_logger,
                                    connection_check_time_interval=
                                    self.connection_check_time_interval)
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.system_id = 'test_system_id'
        self.parent_id = 'test_parent_id'
        self.system_name = 'test_system'
        self.monitor_system = True
        self.node_exporter_url = 'test_url'
        self.system_config = SystemConfig(self.system_id, self.parent_id,
                                          self.system_name, self.monitor_system,
                                          self.node_exporter_url)
        self.test_monitor = SystemMonitor(self.monitor_name, self.system_config,
                                          self.dummy_logger,
                                          self.monitoring_period, self.rabbitmq)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.system_config = None
        self.test_monitor = None

    def test_str_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.__str__())

    def test_get_monitor_period_returns_monitor_period(self) -> None:
        self.assertEqual(self.monitoring_period,
                         self.test_monitor.monitor_period)

    def test_get_monitor_name_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.monitor_name)

    def test_initialize_rabbitmq_initializes_everything_as_expected(
            self) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges have not already been declared
            self.rabbitmq.connect()
            self.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
            self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_monitor._initialise_rabbitmq()
            self.assertTrue(self.test_monitor.rabbitmq.is_connected)
            self.assertTrue(self.test_monitor.rabbitmq.connection.is_open)
            # TODO: Need to continue doing tests for exchanges and confirm
            #     : delivery here
            self.test_monitor.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

