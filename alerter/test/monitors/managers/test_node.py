import copy
import json
import logging
import multiprocessing
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock
from unittest.mock import call

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.configs.nodes.node import NodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.node import NodeMonitorsManager
from src.monitors.monitor import Monitor
from src.monitors.node.chainlink import ChainlinkNodeMonitor
from src.monitors.starters import start_node_monitor
from src.utils import env
from src.utils.constants.names import NODE_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE, NODE_MON_MAN_HEARTBEAT_QUEUE_NAME,
    NODE_MON_MAN_CONFIGS_QUEUE_NAME, PING_ROUTING_KEY,
    NODE_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS,
    HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from test.utils.utils import (infinite_fn, connect_to_rabbit,
                              delete_queue_if_exists, disconnect_from_rabbit,
                              delete_exchange_if_exists)


class TestNodeMonitorsManager(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
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
        self.test_exception = PANICException('test_exception', 1)

        # Some dummy processes
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = Process(target=infinite_fn, args=())
        self.dummy_process3.daemon = True

        # Some dummy node configs
        self.node_id_1 = 'config_id1'
        self.parent_id_1 = 'chain_1'
        self.node_name_1 = 'node_1'
        self.monitor_node_1 = True
        self.monitor_prometheus_1 = True
        self.node_prometheus_urls_1 = ['url1', 'url2', 'url3']
        self.ethereum_addresses_1 = ['eth_add_1', 'eth_add_2', 'eth_add_3']
        self.node_config_1 = ChainlinkNodeConfig(
            self.node_id_1, self.parent_id_1, self.node_name_1,
            self.monitor_node_1, self.monitor_prometheus_1,
            self.node_prometheus_urls_1, self.ethereum_addresses_1)
        self.node_id_2 = 'config_id2'
        self.parent_id_2 = 'chain_2'
        self.node_name_2 = 'node_2'
        self.monitor_node_2 = True
        self.monitor_prometheus_2 = True
        self.node_prometheus_urls_2 = ['url4', 'url5', 'url6']
        self.ethereum_addresses_2 = ['eth_add_4', 'eth_add_5', 'eth_add_6']
        self.node_config_2 = ChainlinkNodeConfig(
            self.node_id_2, self.parent_id_2, self.node_name_2,
            self.monitor_node_2, self.monitor_prometheus_2,
            self.node_prometheus_urls_2, self.ethereum_addresses_2)
        self.node_id_3 = 'config_id3'
        self.parent_id_3 = 'chain_3'
        self.node_name_3 = 'node_3'
        self.monitor_node_3 = True
        self.node_config_3 = NodeConfig(
            self.node_id_3, self.parent_id_3, self.node_name_3,
            self.monitor_node_3)

        # Some config_process_dict, node_configs and sent_configs examples
        self.config_process_dict_example = {
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
        self.nodes_configs_example = {
            'Chainlink Binance Smart Chain': {
                'config_id1': {
                    'id': self.node_id_1,
                    'parent_id': self.parent_id_1,
                    'name': self.node_name_1,
                    'node_prometheus_urls':
                        ','.join(self.node_prometheus_urls_1),
                    'ethereum_addresses': ','.join(self.ethereum_addresses_1),
                    'monitor_node': str(self.monitor_node_1),
                    'monitor_prometheus': str(self.monitor_prometheus_1)
                },
                'config_id2': {
                    'id': self.node_id_2,
                    'parent_id': self.parent_id_2,
                    'name': self.node_name_2,
                    'node_prometheus_urls':
                        ','.join(self.node_prometheus_urls_2),
                    'ethereum_addresses': ','.join(self.ethereum_addresses_2),
                    'monitor_node': str(self.monitor_node_2),
                    'monitor_prometheus': str(self.monitor_prometheus_2)
                }
            },
            'Substrate Kusama': {
                'config_id3': {
                    'id': self.node_id_3,
                    'parent_id': self.parent_id_3,
                    'name': self.node_name_3,
                    'monitor_node': str(self.monitor_node_3),
                }
            },
        }
        self.sent_configs_example_chainlink = {
            'config_id1': {
                'id': self.node_id_1,
                'parent_id': self.parent_id_1,
                'name': self.node_name_1,
                'node_prometheus_urls': ','.join(self.node_prometheus_urls_1),
                'ethereum_addresses': ','.join(self.ethereum_addresses_1),
                'monitor_node': str(self.monitor_node_1),
                'monitor_prometheus': str(self.monitor_prometheus_1)
            },
            'config_id2': {
                'id': self.node_id_2,
                'parent_id': self.parent_id_2,
                'name': self.node_name_2,
                'node_prometheus_urls': ','.join(self.node_prometheus_urls_2),
                'ethereum_addresses': ','.join(self.ethereum_addresses_2),
                'monitor_node': str(self.monitor_node_2),
                'monitor_prometheus': str(self.monitor_prometheus_2)
            }
        }
        self.sent_configs_example_kusama = {
            'config_id3': {
                'id': self.node_id_3,
                'parent_id': self.parent_id_3,
                'name': self.node_name_3,
                'monitor_node': str(self.monitor_node_3),
            }
        }

        # Test manager object
        self.test_manager = NodeMonitorsManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)

        # Some test routing keys
        self.chainlink_routing_key = \
            'chains.Chainlink.Binance Smart Chain.nodes_config'
        self.kusama_routing_key = 'chains.Substrate.Kusama.nodes_config'

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               NODE_MON_MAN_HEARTBEAT_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               NODE_MON_MAN_CONFIGS_QUEUE_NAME)
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
        self.test_manager.rabbitmq.queue_delete(
            NODE_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.test_manager.rabbitmq.queue_delete(NODE_MON_MAN_CONFIGS_QUEUE_NAME)
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
            routing_key=PING_ROUTING_KEY, body=self.test_data_str,
            is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=NODE_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_manager.rabbitmq.queue_declare(
            NODE_MON_MAN_HEARTBEAT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(0, res.method.message_count)
        res = self.test_manager.rabbitmq.queue_declare(
            NODE_MON_MAN_CONFIGS_QUEUE_NAME, False, True, False, False)
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
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
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

        # Assume that the node with id config_id2 was not added yet.
        del self.config_process_dict_example[self.node_id_2]
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

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_starts_monitors_for_new_configs(
            self, third_conf_monitor_node, third_conf_monitor_prometheus,
            startup_mock) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if
        # `monitor_node and monitor_<any_source> = True`.
        # We will be also testing that if
        # `monitor_node or monitor_<all_sources> = False` no new monitor
        # is created. We will perform this test for both when the state is empty
        # and non-empty
        startup_mock.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        sent_configs['config_id3'] = {
            'id': self.node_id_3,
            'parent_id': self.parent_id_3,
            'name': self.node_name_3,
            'node_prometheus_urls': 'url7,url8,url9',
            'ethereum_addresses': 'eth_add_1,eth_add_2,eth_add_3',
            'monitor_node': third_conf_monitor_node,
            'monitor_prometheus': third_conf_monitor_prometheus
        }
        self.test_manager._process_chainlink_node_configs(sent_configs, {})
        expected_calls = [
            call(self.node_config_1, self.node_id_1, ChainlinkNodeMonitor),
            call(self.node_config_2, self.node_id_2, ChainlinkNodeMonitor),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(2, startup_mock.call_count)

        # Test when current_configs is non-empty
        startup_mock.reset_mock()
        current_configs = {
            'config_id1': {
                'id': self.node_id_1,
                'parent_id': self.parent_id_1,
                'name': self.node_name_1,
                'node_prometheus_urls': ','.join(self.node_prometheus_urls_1),
                'ethereum_addresses': ','.join(self.ethereum_addresses_1),
                'monitor_node': str(self.monitor_node_1),
                'monitor_prometheus': str(self.monitor_prometheus_1)
            }
        }
        self.test_manager._process_chainlink_node_configs(sent_configs,
                                                          current_configs)
        expected_calls = [
            call(self.node_config_2, self.node_id_2, ChainlinkNodeMonitor),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(1, startup_mock.call_count)

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_return_if_valid_new_configurations(
            self, third_conf_monitor_node, third_conf_monitor_prometheus,
            startup_mock) -> None:
        # In this test we will assume that all added configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        # We will perform this test for both when the state is empty and
        # non-empty.
        startup_mock.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        sent_configs['config_id3'] = {
            'id': self.node_id_3,
            'parent_id': self.parent_id_3,
            'name': self.node_name_3,
            'node_prometheus_urls': 'url7,url8,url9',
            'ethereum_addresses': 'eth_add_1,eth_add_2,eth_add_3',
            'monitor_node': third_conf_monitor_node,
            'monitor_prometheus': third_conf_monitor_prometheus
        }
        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs, {})
        expected_return = copy.deepcopy(sent_configs)
        del expected_return['config_id3']
        self.assertEqual(expected_return, actual_return)

        # Test when current_configs is non-empty
        current_configs = {
            'config_id1': {
                'id': self.node_id_1,
                'parent_id': self.parent_id_1,
                'name': self.node_name_1,
                'node_prometheus_urls': ','.join(self.node_prometheus_urls_1),
                'ethereum_addresses': ','.join(self.ethereum_addresses_1),
                'monitor_node': str(self.monitor_node_1),
                'monitor_prometheus': str(self.monitor_prometheus_1)
            }
        }
        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs, current_configs)
        expected_return = copy.deepcopy(sent_configs)
        del expected_return['config_id3']
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_restarts_monitors_for_edited_confs(
            self, deleted_conf_monitor_node, deleted_conf_monitor_prometheus,
            startup_mock, mock_terminate, mock_join) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed and started with the latest configuration as long
        # as `monitor_node and monitor_<any_source>=True`.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)

        # Assume that config_id1, will be the configuration whose monitors will
        # be killed but not started.
        sent_configs['config_id1'] = {
            'id': self.node_id_1,
            'parent_id': self.parent_id_1,
            'name': self.node_name_1,
            'node_prometheus_urls': ','.join(self.node_prometheus_urls_1),
            'ethereum_addresses': ','.join(self.ethereum_addresses_1),
            'monitor_node': deleted_conf_monitor_node,
            'monitor_prometheus': deleted_conf_monitor_prometheus
        }
        # Assume that for config_id2 the name of the node was changed
        sent_configs['config_id2'] = {
            'id': self.node_id_2,
            'parent_id': self.parent_id_2,
            'name': 'changed_node_name',
            'node_prometheus_urls': ','.join(self.node_prometheus_urls_2),
            'ethereum_addresses': ','.join(self.ethereum_addresses_2),
            'monitor_node': str(self.monitor_node_2),
            'monitor_prometheus': str(self.monitor_prometheus_2)
        }

        self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['Chainlink Binance Smart Chain'])
        modified_node_2_config = ChainlinkNodeConfig(
            self.node_id_2, self.parent_id_2, 'changed_node_name',
            self.monitor_node_2, self.monitor_prometheus_2,
            self.node_prometheus_urls_2, self.ethereum_addresses_2)
        startup_mock.assert_called_once_with(modified_node_2_config,
                                             self.node_id_2,
                                             ChainlinkNodeMonitor)
        self.assertEqual(2, mock_terminate.call_count)
        self.assertEqual(2, mock_join.call_count)
        self.assertTrue('config_id2' in self.test_manager.config_process_dict)
        self.assertFalse('config_id1' in self.test_manager.config_process_dict)

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_return_if_valid_edited_confs(
            self, deleted_conf_monitor_node, deleted_conf_monitor_prometheus,
            startup_mock, mock_terminate, mock_join) -> None:
        # In this test we will assume that all edited configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)

        # Assume config_id1 will be the config whose monitor will be killed and
        # not restarted.
        sent_configs['config_id1'] = {
            'id': self.node_id_1,
            'parent_id': self.parent_id_1,
            'name': self.node_name_1,
            'node_prometheus_urls': ','.join(self.node_prometheus_urls_1),
            'ethereum_addresses': ','.join(self.ethereum_addresses_1),
            'monitor_node': deleted_conf_monitor_node,
            'monitor_prometheus': deleted_conf_monitor_prometheus
        }
        # Assume that for config_id2 the name of the node was changed
        sent_configs['config_id2'] = {
            'id': self.node_id_2,
            'parent_id': self.parent_id_2,
            'name': 'changed_node_name',
            'node_prometheus_urls': ','.join(self.node_prometheus_urls_2),
            'ethereum_addresses': ','.join(self.ethereum_addresses_2),
            'monitor_node': str(self.monitor_node_2),
            'monitor_prometheus': str(self.monitor_prometheus_2)
        }

        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['Chainlink Binance Smart Chain'])
        expected_return = copy.deepcopy(sent_configs)
        del expected_return['config_id1']
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_deletes_monitors_for_deleted_confs(
            self, startup_mock, mock_terminate, mock_join) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        del sent_configs['config_id1']

        self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['Chainlink Binance Smart Chain'])
        startup_mock.assert_not_called()
        self.assertEqual(1, mock_terminate.call_count)
        self.assertEqual(1, mock_join.call_count)
        self.assertTrue('config_id2' in self.test_manager.config_process_dict)
        self.assertFalse('config_id1' in self.test_manager.config_process_dict)

    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_return_if_valid_deleted_confs(
            self, startup_mock, mock_terminate, mock_join) -> None:
        # In this test we will assume that all sent configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        del sent_configs['config_id1']

        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['Chainlink Binance Smart Chain'])
        self.assertEqual(sent_configs, actual_return)

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_default_key(self, mock_ack) -> None:
        # This test will pass if the stored nodes config does not change.
        # This would mean that the DEFAULT key was ignored, otherwise, it would
        # have been included as a new config.
        mock_ack.return_value = None
        old_nodes_configs = copy.deepcopy(self.nodes_configs_example)
        self.test_manager._nodes_configs = self.nodes_configs_example

        # We will pass the acceptable schema as a value to make sure that the
        # default key will never be added. By passing the schema we will also
        # prevent processing errors from happening.
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        sent_configs['DEFAULT'] = {
            'id': self.node_id_1,
            'parent_id': self.parent_id_1,
            'name': self.node_name_1,
            'node_prometheus_urls': ','.join(self.node_prometheus_urls_1),
            'ethereum_addresses': ','.join(self.ethereum_addresses_1),
            'monitor_node': str(self.monitor_node_1),
            'monitor_prometheus': str(self.monitor_prometheus_1)
        }

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=self.chainlink_routing_key)
        body = json.dumps(sent_configs)
        properties = pika.spec.BasicProperties()
        self.test_manager._process_configs(blocking_channel, method, properties,
                                           body)

        self.assertEqual(old_nodes_configs, self.test_manager.nodes_configs)
        mock_ack.assert_called_once()

    @mock.patch.object(multiprocessing.Process, 'start')
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_stores_updated_confs_correctly_if_recognised_chain(
            self, mock_ack, mock_start) -> None:
        # For now this test will only be performed for chainlink chains as they
        # are the only currently supported chains for node monitoring
        mock_ack.return_value = None
        mock_start.return_value = None

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=self.chainlink_routing_key)
        body = json.dumps(self.sent_configs_example_chainlink)
        properties = pika.spec.BasicProperties()

        self.assertEqual({}, self.test_manager.nodes_configs)
        self.test_manager._process_configs(blocking_channel, method, properties,
                                           body)
        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        expected_nodes_configs = {chain: self.nodes_configs_example[chain]}
        self.assertEqual(expected_nodes_configs,
                         self.test_manager.nodes_configs)
        mock_ack.assert_called_once()

    @mock.patch.object(multiprocessing.Process, 'start')
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_stores_empty_dict_if_unrecognised_chain(
            self, mock_ack, mock_start) -> None:
        # Note for now only chainlink chains are supported
        mock_ack.return_value = None
        mock_start.return_value = None

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=self.kusama_routing_key)
        body = json.dumps(self.sent_configs_example_kusama)
        properties = pika.spec.BasicProperties()

        self.assertEqual({}, self.test_manager.nodes_configs)
        self.test_manager._process_configs(blocking_channel, method, properties,
                                           body)
        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        expected_nodes_configs = {chain: {}}
        self.assertEqual(expected_nodes_configs,
                         self.test_manager.nodes_configs)
        mock_ack.assert_called_once()

    @parameterized.expand([
        ([True, True, True], [],),
        ([True, False, True], ['config_id2'],),
        ([False, False, False], ['config_id1', 'config_id2', 'config_id3'],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb(
            self, is_alive_side_effect, dead_configs, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method,
                                        properties, body)

        expected_hb = {
            'component_name': self.manager_name,
            'running_processes': [
                self.config_process_dict_example[config_id]['component_name']
                for config_id in self.config_process_dict_example
                if config_id not in dead_configs
            ],
            'dead_processes': [
                self.config_process_dict_example[config_id]['component_name']
                for config_id in self.config_process_dict_example
                if config_id in dead_configs
            ],
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(expected_hb)

    @parameterized.expand([
        ([True, True, True], [],),
        ([True, False, True], ['config_id2'],),
        ([False, False, False], ['config_id1', 'config_id2', 'config_id3'],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes_correctly(
            self, is_alive_side_effect, dead_configs, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method,
                                        properties, body)

        expected_calls = [
            call(self.config_process_dict_example[config_id]['node_config'],
                 config_id,
                 self.config_process_dict_example[config_id]['monitor_type'])
            for config_id in self.config_process_dict_example
            if config_id in dead_configs
        ]
        actual_calls = mock_create_and_start.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_send_hb, mock_is_alive) -> None:
        mock_is_alive.side_effect = self.test_exception
        mock_send_hb.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method,
                                        properties, body)

        mock_send_hb.assert_not_called()

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        # In this test we are assuming that no configs have been set, this is
        # done to keep the test as simple as possible. We are also assuming that
        # a MsgWasNotDeliveredException will be raised automatically because
        # we are deleting the HealthExchange after every test, and thus there
        # are no consumers of the heartbeat.
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        try:
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except MessageWasNotDeliveredException:
            self.fail('A MessageWasNotDeliveredException should not have been '
                      'raised')

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_raises_unrecognised_error_if_raised_by_send_heartbeat(
            self, exception_class, exception_instance, mock_send_hb) -> None:
        mock_send_hb.side_effect = exception_instance
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_class, self.test_manager._process_ping,
                          blocking_channel, method, properties, body)
