import json
import logging
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from time import sleep
from unittest import mock
import multiprocessing
import pika

from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.system import SystemMonitorsManager, \
    SYS_MON_MAN_INPUT_QUEUE, SYS_MON_MAN_INPUT_ROUTING_KEY, \
    SYS_MON_MAN_ROUTING_KEY_CHAINS, SYS_MON_MAN_ROUTING_KEY_GEN
from src.utils.constants import HEALTH_CHECK_EXCHANGE, \
    CONFIG_EXCHANGE, SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME


def infinite_fn() -> None:
    while True:
        sleep(10)


class TestSystemMonitor(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = 'localhost'
        # self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_system_monitors_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.config_process_dict_example = {
            'config_id1': {
                'component_name': 'system_monitor_system_1',
                'process': self.dummy_process1,
                'chain': 'Polkadot'
            },
            'config_id2': {
                'component_name': 'system_monitor_system_2',
                'process': self.dummy_process2,
                'chain': 'GENERAL'
            },
        }
        self.systems_configs_example = {
            'Polkadot': {
                'config_id1': {
                    'id': 'config_id1',
                    'parent_id': 'chain_1',
                    'name': 'system_1',
                    'exporter_url': 'dummy_url1',
                    'monitor_system': True,
                }
            },
            'general': {
                'config_id2': {
                    'id': 'config_id2',
                    'parent_id': 'GENERAL',
                    'name': 'system_2',
                    'exporter_url': 'dummy_url2',
                    'monitor_system': True,
                }
            },
        }
        self.test_manager = SystemMonitorsManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.test_manager = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.config_process_dict_example = None
        self.systems_configs_example = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.__str__())

    def test_config_process_dict_returns_config_process_dict(self) -> None:
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_systems_configs_returns_systems_configs(self) -> None:
        self.test_manager._systems_configs = self.systems_configs_example
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        self.assertEqual(1, mock_start_consuming.call_count)

    @mock.patch.object(SystemMonitorsManager, "_process_ping")
    def test_initialise_rabbitmq_initializes_everything_as_expected(
            self, mock_process_ping) -> None:
        mock_process_ping.return_value = None
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges and queues have not already been
            # declared
            self.rabbitmq.connect()
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_manager._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_manager.rabbitmq.is_connected)
            self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_manager.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchanges and queues have been creating by
            # sending messages with the same routing keys as for the queue. We
            # will also check if the size of the queues is 0 to confirm that
            # basic_consume was called (it will store the msg in the component
            # memory immediately). If one of the exchanges or queues is not
            # created, then either an exception or the queue size would be 1.
            # Note when deleting the exchanges in the beginning we also
            # released every binding, hence there are not other queues binded
            # with the same routing key at this point.
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=SYS_MON_MAN_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=CONFIG_EXCHANGE,
                routing_key=SYS_MON_MAN_ROUTING_KEY_CHAINS,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=CONFIG_EXCHANGE,
                routing_key=SYS_MON_MAN_ROUTING_KEY_GEN,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_manager.rabbitmq.queue_declare(
                SYS_MON_MAN_INPUT_QUEUE, False, True, False, False)
            self.assertEqual(0, res.method.message_count)
            res = self.test_manager.rabbitmq.queue_declare(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME, False, True, False,
                False)
            self.assertEqual(0, res.method.message_count)

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_send_data_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
            self.test_manager._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._send_heartbeat(self.test_heartbeat)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is actually the HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    # Todo: Before starting these tests first create the systems configs etc

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_monitor_process_stores_the_correct_process_info(
            self, mock_start) -> None:
        # TODO: Mock start() so that here we only check the dict
        mock_start.return_value = None

    def test_create_and_start_monitor_process_creates_the_correct_process(
            self) -> None:
        # TODO: Mock start and use the dict to check that the correct confs
        #     : have been set
        pass

    def test_create_and_start_monitor_process_starts_the_process(self) -> None:
        # TODO: Do not mock start. Terminate after checking that the process was
        #     : created
        pass

# TODO: Remove tearDown() commented code
# TODO: Remove SIGHUP comment
# TODO: Fix rabbit host
# TODO: Remove env commented code in system manager, github manager, monitor
#     : starters
# TODO: Now since tests finished we need to run in docker environment.
#     : Do not forget to do the three TODOs above before.
