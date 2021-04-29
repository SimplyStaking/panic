import json
import logging
import multiprocessing
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock

import pika

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.configs.nodes.node import NodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.node import NodeMonitorsManager
from src.monitors.monitor import Monitor
from src.monitors.node.chainlink import ChainlinkNodeMonitor
from src.monitors.starters import start_node_monitor
from src.utils import env
from src.utils.constants import (NODE_MONITOR_NAME_TEMPLATE,
                                 HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE,
                                 NODE_MON_MAN_INPUT_QUEUE,
                                 NODE_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 NODE_MON_MAN_INPUT_ROUTING_KEY,
                                 NODE_MON_MAN_ROUTING_KEY_CHAINS)
from src.utils.exceptions import PANICException
from test.utils.utils import (infinite_fn, connect_to_rabbit,
                              delete_queue_if_exists, disconnect_from_rabbit,
                              delete_exchange_if_exists)


class TestNodeMonitorsManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_node_monitors_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = Process(target=infinite_fn, args=())
        self.dummy_process3.daemon = True
        self.node_id_1 = 'config_id1'
        self.parent_id_1 = 'chain_1'
        self.node_name_1 = 'node_1'
        self.monitor_node_1 = True
        self.node_prometheus_urls_1 = ['url1', 'url2', 'url3']
        self.ethereum_addresses_1 = ['eth_add_1', 'eth_add_2', 'eth_add_3']
        self.node_config_1 = ChainlinkNodeConfig(
            self.node_id_1, self.parent_id_1, self.node_name_1,
            self.monitor_node_1, self.node_prometheus_urls_1,
            self.ethereum_addresses_1)
        self.node_id_2 = 'config_id2'
        self.parent_id_2 = 'chain_2'
        self.node_name_2 = 'node_2'
        self.monitor_node_2 = True
        self.node_prometheus_urls_2 = ['url4', 'url5', 'url6']
        self.ethereum_addresses_2 = ['eth_add_4', 'eth_add_5', 'eth_add_6']
        self.node_config_2 = ChainlinkNodeConfig(
            self.node_id_2, self.parent_id_2, self.node_name_2,
            self.monitor_node_2, self.node_prometheus_urls_2,
            self.ethereum_addresses_2)
        self.node_id_3 = 'config_id3'
        self.parent_id_3 = 'chain_3'
        self.node_name_3 = 'node_3'
        self.monitor_node_3 = True
        self.node_config_3 = NodeConfig(
            self.node_id_3, self.parent_id_3, self.node_name_3,
            self.monitor_node_3)

        # We will assume that node_config_2 is the new node config to be sent in
        # all tests.
        self.config_process_dict_example = {
            'config_id1': {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_name_1),
                'process': self.dummy_process1,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_1,
            },
            'config_id3': {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_name_3),
                'process': self.dummy_process3,
                'monitor_type': Monitor,
                'node_config': self.node_config_3
            },
        }
        self.nodes_configs_example = {
            'Chainlink Binance Smart Chain': {
                'config_id1': {
                    'id': self.node_id_1,
                    'parent_id': self.parent_id_1,
                    'name': self.node_name_1,
                    'node_prometheus_urls':
                        ','.join(self.node_prometheus_urls_1),
                    'monitor_node': str(self.monitor_node_1),
                }
            },
            'Substrate Kusama': {
                'config_id3': {
                    'id': self.node_id_3,
                    'parent_id': self.parent_id_3,
                    'name': self.node_name_3,
                    'monitor_system': str(self.monitor_node_3),
                }
            },
        }
        self.sent_configs_example_chainlink = {
            'config_id1': {
                'id': self.node_id_1,
                'parent_id': self.parent_id_1,
                'name': self.node_name_1,
                'node_prometheus_urls':
                    ','.join(self.node_prometheus_urls_1),
                'monitor_node': str(self.monitor_node_1),
            }
        }
        self.sent_configs_example_kusama = {
            'config_id3': {
                'id': self.node_id_3,
                'parent_id': self.parent_id_3,
                'name': self.node_name_3,
                'monitor_system': str(self.monitor_node_3),
            }
        }
        self.test_manager = NodeMonitorsManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)
        self.chainlink_routing_key = \
            'chains.Chainlink.Binance Smart Chain.nodes_config'
        self.kusama_routing_key = 'chains.Substrate.Kusama.nodes_config'
        self.test_exception = PANICException('test_exception', 1)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               NODE_MON_MAN_INPUT_QUEUE)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               NODE_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq, CONFIG_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None
        self.node_config_1 = None
        self.node_config_2 = None
        self.node_config_3 = None
        self.config_process_dict_example = None
        self.nodes_configs_example = None
        self.sent_configs_example_chainlink = None
        self.sent_configs_example_kusama = None
        self.test_manager = None
        self.test_exception = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, str(self.test_manager))

    def test_config_process_dict_returns_config_process_dict(self) -> None:
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_nodes_configs_returns_nodes_configs(self) -> None:
        self.test_manager._nodes_configs = self.nodes_configs_example
        self.assertEqual(self.nodes_configs_example,
                         self.test_manager.nodes_configs)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        mock_start_consuming.assert_called_once()

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already
        # established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        self.rabbitmq.connect()
        self.test_manager.rabbitmq.queue_delete(NODE_MON_MAN_INPUT_QUEUE)
        self.test_manager.rabbitmq.queue_delete(
            NODE_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
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
        # sending messages with the same routing keys as for the queues. We
        # will also check if the size of the queues is 0 to confirm that
        # basic_consume was called (it will store the msg in the component
        # memory immediately). If one of the exchanges or queues is not
        # created, then an exception will be thrown. Note when deleting the
        # exchanges in the beginning we also released every binding, hence there
        # is no other queue binded with the same routing key to any exchange at
        # this point.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=NODE_MON_MAN_INPUT_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=NODE_MON_MAN_ROUTING_KEY_CHAINS,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_manager.rabbitmq.queue_declare(
            NODE_MON_MAN_INPUT_QUEUE, False, True, False, False)
        self.assertEqual(0, res.method.message_count)
        res = self.test_manager.rabbitmq.queue_declare(
            NODE_MONITORS_MANAGER_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(0, res.method.message_count)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
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

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, 'Process')
    def test_create_and_start_monitor_process_stores_the_correct_process_info(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process2
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        expected_output = {
            'config_id1': {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_name_1),
                'process': self.dummy_process1,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_1,
            },
            'config_id2': {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_name_2),
                'process': self.dummy_process2,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_2,
            },
            'config_id3': {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_name_3),
                'process': self.dummy_process3,
                'monitor_type': Monitor,
                'node_config': self.node_config_3
            },
        }

        self.test_manager._create_and_start_monitor_process(
            self.node_config_2, self.node_id_2, ChainlinkNodeMonitor)

        self.assertEqual(expected_output, self.test_manager.config_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_monitor_process_creates_and_starts_correct_proc(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._create_and_start_monitor_process(
            self.node_config_2, self.node_id_2, ChainlinkNodeMonitor)

        new_entry = self.test_manager.config_process_dict[self.node_id_2]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(2, len(new_entry_process._args))
        self.assertEqual(self.node_config_2, new_entry_process._args[0])
        self.assertEqual(ChainlinkNodeMonitor, new_entry_process._args[1])
        self.assertEqual(start_node_monitor, new_entry_process._target)
        mock_start.assert_called_once()

