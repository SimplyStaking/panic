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
                },
                'config_id2': {
                    'id': self.node_id_2,
                    'parent_id': self.parent_id_2,
                    'name': self.node_name_2,
                    'node_prometheus_urls':
                        ','.join(self.node_prometheus_urls_2),
                    'ethereum_addresses': ','.join(self.ethereum_addresses_2),
                    'monitor_node': str(self.monitor_node_2),
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
                'node_prometheus_urls': ','.join(self.node_prometheus_urls_1),
                'ethereum_addresses': ','.join(self.ethereum_addresses_1),
                'monitor_node': str(self.monitor_node_1),
            },
            'config_id2': {
                'id': self.node_id_2,
                'parent_id': self.parent_id_2,
                'name': self.node_name_2,
                'node_prometheus_urls': ','.join(self.node_prometheus_urls_2),
                'ethereum_addresses': ','.join(self.ethereum_addresses_2),
                'monitor_node': str(self.monitor_node_2),
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

    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_starts_monitors_for_new_configs(
            self, startup_mock) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if `monitor_node = True`.
        # We will be also testing that if `monitor_node = False` no new monitor
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
            'monitor_node': "False",
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
            }
        }
        self.test_manager._process_chainlink_node_configs(sent_configs,
                                                          current_configs)
        expected_calls = [
            call(self.node_config_2, self.node_id_2, ChainlinkNodeMonitor),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(1, startup_mock.call_count)

    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_return_if_valid_new_configurations(
            self, startup_mock) -> None:
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
            'monitor_node': "False",
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
            }
        }
        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs, current_configs)
        expected_return = copy.deepcopy(sent_configs)
        del expected_return['config_id3']
        self.assertEqual(expected_return, actual_return)

    # TODO: Not, all dummy processes are in the state. Do same tests for modify
    #     : and remove.

    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_process_configs_ignores_default_key(self, mock_ack) -> None:
    #     # This test will pass if the stored systems config does not change.
    #     # This would mean that the DEFAULT key was ignored, otherwise, it would
    #     # have been included as a new config.
    #     mock_ack.return_value = None
    #     old_systems_configs = copy.deepcopy(self.systems_configs_example)
    #     self.test_manager._systems_configs = self.systems_configs_example
    #
    #     # We will pass the acceptable schema as a value to make sure that the
    #     # default key will never be added. By passing the schema we will also
    #     # prevent processing errors from happening.
    #     self.sent_configs_example_chain['DEFAULT'] = {
    #         'id': 'default_id1',
    #         'parent_id': 'chain_1',
    #         'name': 'default_system_1',
    #         'exporter_url': 'default_dummy_url1',
    #         'monitor_system': "True",
    #     }
    #     self.sent_configs_example_general['DEFAULT'] = {
    #         'id': 'default_id2',
    #         'parent_id': 'GENERAL',
    #         'name': 'default_system_2',
    #         'exporter_url': 'default_dummy_url2',
    #         'monitor_system': "True",
    #     }
    #
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain = json.dumps(self.sent_configs_example_chain)
    #         body_general = json.dumps(self.sent_configs_example_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         # We will send the message twice with both general and chain
    #         # routing keys to make sure that the DEFAULT key is ignored in both
    #         # cases
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general)
    #         self.assertEqual(old_systems_configs,
    #                          self.test_manager.systems_configs)
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain)
    #         self.assertEqual(old_systems_configs,
    #                          self.test_manager.systems_configs)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # @mock.patch.object(SystemMonitorsManager,
    #                    "_create_and_start_monitor_process")
    # def test_process_configs_stores_new_configs_to_be_monitored_correctly(
    #         self, startup_mock, mock_ack) -> None:
    #     # We will check whether new configs are added to the state. Since some
    #     # new configs have `monitor_system = False` we are also testing that
    #     # new configs are ignored if they should not be monitored.
    #
    #     mock_ack.return_value = None
    #     startup_mock.return_value = None
    #     new_configs_chain = {
    #         'config_id1': {
    #             'id': 'config_id1',
    #             'parent_id': 'chain_1',
    #             'name': 'system_1',
    #             'exporter_url': 'dummy_url1',
    #             'monitor_system': "True",
    #         },
    #         'config_id3': {
    #             'id': 'config_id3',
    #             'parent_id': 'chain_1',
    #             'name': 'system_3',
    #             'exporter_url': 'dummy_url3',
    #             'monitor_system': "True",
    #         },
    #         'config_id4': {
    #             'id': 'config_id4',
    #             'parent_id': 'chain_1',
    #             'name': 'system_4',
    #             'exporter_url': 'dummy_url4',
    #             'monitor_system': "False",
    #         }
    #     }
    #     new_configs_general = {
    #         'config_id2': {
    #             'id': 'config_id2',
    #             'parent_id': 'GENERAL',
    #             'name': 'system_2',
    #             'exporter_url': 'dummy_url2',
    #             'monitor_system': "True",
    #         },
    #         'config_id5': {
    #             'id': 'config_id5',
    #             'parent_id': 'GENERAL',
    #             'name': 'system_5',
    #             'exporter_url': 'dummy_url5',
    #             'monitor_system': "True",
    #         },
    #         'config_id6': {
    #             'id': 'config_id6',
    #             'parent_id': 'GENERAL',
    #             'name': 'system_6',
    #             'exporter_url': 'dummy_url6',
    #             'monitor_system': "False",
    #         }
    #     }
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #
    #         # We will send new configs through both the existing and
    #         # non-existing chain and general paths to make sure that all routes
    #         # work as expected.
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_initial = json.dumps(
    #             self.sent_configs_example_chain)
    #         body_general_initial = json.dumps(
    #             self.sent_configs_example_general)
    #         body_new_configs_chain = json.dumps(new_configs_chain)
    #         body_new_configs_general = json.dumps(new_configs_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_initial)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_initial)
    #         expected_output = copy.deepcopy(self.systems_configs_example)
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties,
    #                                            body_new_configs_chain)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties,
    #                                            body_new_configs_general)
    #         expected_output['Substrate Polkadot']['config_id3'] = \
    #             new_configs_chain['config_id3']
    #         expected_output['general']['config_id5'] = \
    #             new_configs_general['config_id5']
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # @mock.patch.object(SystemMonitorsManager,
    #                    "_create_and_start_monitor_process")
    # @mock.patch.object(multiprocessing.Process, "terminate")
    # @mock.patch.object(multiprocessing.Process, "join")
    # def test_process_configs_stores_modified_configs_to_be_monitored_correctly(
    #         self, join_mock, terminate_mock, startup_mock, mock_ack) -> None:
    #     # In this test we will check that modified configurations with
    #     # `monitor_system = True` are stored correctly in the state. Some
    #     # configurations will have `monitor_system = False` to check whether the
    #     # monitor associated with the previous configuration is terminated.
    #
    #     mock_ack.return_value = None
    #     startup_mock.return_value = None
    #     join_mock.return_value = None
    #     terminate_mock.return_value = None
    #     self.test_manager._systems_configs = self.systems_configs_example
    #     self.test_manager._config_process_dict = \
    #         self.config_process_dict_example
    #
    #     new_configs_chain_monitor_true = {
    #         'config_id1': {
    #             'id': 'config_id1',
    #             'parent_id': 'chain_1',
    #             'name': 'new_system_name_chain',
    #             'exporter_url': 'dummy_url1',
    #             'monitor_system': "True",
    #         },
    #     }
    #     new_configs_chain_monitor_false = {
    #         'config_id1': {
    #             'id': 'config_id1',
    #             'parent_id': 'chain_1',
    #             'name': 'new_system_name_chain',
    #             'exporter_url': 'dummy_url1',
    #             'monitor_system': "False",
    #         },
    #     }
    #     new_configs_general_monitor_true = {
    #         'config_id2': {
    #             'id': 'config_id2',
    #             'parent_id': 'GENERAL',
    #             'name': 'new_system_name_general',
    #             'exporter_url': 'dummy_url2',
    #             'monitor_system': "True",
    #         },
    #     }
    #     new_configs_general_monitor_false = {
    #         'config_id2': {
    #             'id': 'config_id2',
    #             'parent_id': 'GENERAL',
    #             'name': 'new_system_name_general',
    #             'exporter_url': 'dummy_url2',
    #             'monitor_system': "false",
    #         },
    #     }
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_mon_true = json.dumps(new_configs_chain_monitor_true)
    #         body_general_mon_true = json.dumps(new_configs_general_monitor_true)
    #         body_chain_mon_false = json.dumps(new_configs_chain_monitor_false)
    #         body_general_mon_false = json.dumps(
    #             new_configs_general_monitor_false)
    #         properties = pika.spec.BasicProperties()
    #         expected_output = copy.deepcopy(self.systems_configs_example)
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_mon_true)
    #         expected_output['Substrate Polkadot']['config_id1'] = \
    #             new_configs_chain_monitor_true['config_id1']
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties,
    #                                            body_general_mon_true)
    #         expected_output['general']['config_id2'] = \
    #             new_configs_general_monitor_true['config_id2']
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties,
    #                                            body_chain_mon_false)
    #         expected_output['Substrate Polkadot'] = {}
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #         self.assertTrue(
    #             'config_id1' not in self.test_manager.config_process_dict)
    #
    #         self.test_manager._process_configs(
    #             blocking_channel, method_general, properties,
    #             body_general_mon_false)
    #         expected_output['general'] = {}
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #         self.assertTrue(
    #             'config_id2' not in self.test_manager.config_process_dict)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # @mock.patch.object(multiprocessing.Process, "terminate")
    # @mock.patch.object(multiprocessing.Process, "join")
    # def test_process_configs_removes_deleted_configs_from_state_correctly(
    #         self, join_mock, terminate_mock, mock_ack) -> None:
    #     # In this test we will check that removed configurations are actually
    #     # removed from the state
    #
    #     mock_ack.return_value = None
    #     join_mock.return_value = None
    #     terminate_mock.return_value = None
    #     self.test_manager._systems_configs = self.systems_configs_example
    #     self.test_manager._config_process_dict = \
    #         self.config_process_dict_example
    #
    #     new_configs_chain = {}
    #     new_configs_general = {}
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain = json.dumps(new_configs_chain)
    #         body_general = json.dumps(new_configs_general)
    #         properties = pika.spec.BasicProperties()
    #         expected_output = copy.deepcopy(self.systems_configs_example)
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain)
    #         expected_output['Substrate Polkadot'] = {}
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #         self.assertTrue(
    #             'config_id1' not in self.test_manager.config_process_dict)
    #
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general)
    #         expected_output['general'] = {}
    #         self.assertEqual(expected_output, self.test_manager.systems_configs)
    #         self.assertTrue(
    #             'config_id2' not in self.test_manager.config_process_dict)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch("src.monitors.starters.create_logger")
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_proc_confs_term_and_starts_monitors_for_modified_confs_to_be_mon(
    #         self, mock_ack, mock_create_logger) -> None:
    #     # In this test we will check that modified configurations with
    #     # `monitor_system = True` will have new monitors started. Implicitly
    #     # we will be checking that modified configs with
    #     # `monitor_system = False` will only have their previous processes
    #     # terminated.
    #
    #     mock_ack.return_value = None
    #     mock_create_logger.return_value = self.dummy_logger
    #     new_configs_chain_monitor_true = {
    #         'config_id1': {
    #             'id': 'config_id1',
    #             'parent_id': 'chain_1',
    #             'name': 'new_system_name_chain',
    #             'exporter_url': 'dummy_url1',
    #             'monitor_system': "True",
    #         },
    #     }
    #     new_configs_chain_monitor_false = {
    #         'config_id1': {
    #             'id': 'config_id1',
    #             'parent_id': 'chain_1',
    #             'name': 'new_system_name_chain',
    #             'exporter_url': 'dummy_url1',
    #             'monitor_system': "False",
    #         },
    #     }
    #     new_configs_general_monitor_true = {
    #         'config_id2': {
    #             'id': 'config_id2',
    #             'parent_id': 'GENERAL',
    #             'name': 'new_system_name_general',
    #             'exporter_url': 'dummy_url2',
    #             'monitor_system': "True",
    #         },
    #     }
    #     new_configs_general_monitor_false = {
    #         'config_id2': {
    #             'id': 'config_id2',
    #             'parent_id': 'GENERAL',
    #             'name': 'new_system_name_general',
    #             'exporter_url': 'dummy_url2',
    #             'monitor_system': "false",
    #         },
    #     }
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_initial = json.dumps(self.sent_configs_example_chain)
    #         body_general_initial = json.dumps(self.sent_configs_example_general)
    #         body_chain_mon_true = json.dumps(new_configs_chain_monitor_true)
    #         body_general_mon_true = json.dumps(new_configs_general_monitor_true)
    #         body_chain_mon_false = json.dumps(new_configs_chain_monitor_false)
    #         body_general_mon_false = json.dumps(
    #             new_configs_general_monitor_false)
    #         properties = pika.spec.BasicProperties()
    #
    #         # First send the new configs as the state is empty
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_initial)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_initial)
    #
    #         # Assure that the processes have been started
    #         self.assertTrue(self.test_manager.config_process_dict[
    #                             'config_id1']['process'].is_alive())
    #         self.assertTrue(self.test_manager.config_process_dict[
    #                             'config_id2']['process'].is_alive())
    #
    #         # Give some time till the process starts
    #         time.sleep(1)
    #
    #         # Send the updated configs with `monitor_system = True`
    #         conf_id1_old_proc = self.test_manager.config_process_dict[
    #             'config_id1']['process']
    #         conf_id2_old_proc = self.test_manager.config_process_dict[
    #             'config_id2']['process']
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_mon_true)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties,
    #                                            body_general_mon_true)
    #
    #         # Give some time till the process re-starts
    #         time.sleep(1)
    #
    #         # Check that the old process has terminated and a new one has
    #         # started.
    #         self.assertFalse(conf_id1_old_proc.is_alive())
    #         self.assertTrue(self.test_manager.config_process_dict[
    #                             'config_id1']['process'].is_alive())
    #         self.assertFalse(conf_id2_old_proc.is_alive())
    #         self.assertTrue(self.test_manager.config_process_dict[
    #                             'config_id2']['process'].is_alive())
    #
    #         # Send the updated configs with `monitor_system = False`
    #         conf_id1_old_proc = self.test_manager.config_process_dict[
    #             'config_id1']['process']
    #         conf_id2_old_proc = self.test_manager.config_process_dict[
    #             'config_id2']['process']
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_mon_false)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties,
    #                                            body_general_mon_false)
    #
    #         # Give some time till the process stops
    #         time.sleep(1)
    #
    #         # Check that the old process has terminated and that new ones have
    #         # not been started. If _create_start_process is called then the
    #         # config ids would be in config_process_dict
    #         self.assertFalse(conf_id1_old_proc.is_alive())
    #         self.assertFalse(
    #             'config_id1' in self.test_manager.config_process_dict)
    #         self.assertFalse(conf_id2_old_proc.is_alive())
    #         self.assertFalse(
    #             'config_id2' in self.test_manager.config_process_dict)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # @mock.patch.object(SystemMonitorsManager,
    #                    "_create_and_start_monitor_process")
    # @mock.patch.object(multiprocessing.Process, "join")
    # @mock.patch.object(multiprocessing.Process, "terminate")
    # def test_process_confs_restarts_an_updated_monitor_with_the_correct_conf(
    #         self, mock_terminate, mock_join, startup_mock, mock_ack) -> None:
    #     # We will check whether _create_and_start_monitor_process is called
    #     # correctly on an updated configuration.
    #     mock_ack.return_value = None
    #     startup_mock.return_value = None
    #     mock_join.return_value = None
    #     mock_terminate.return_value = None
    #     updated_configs_chain = {
    #         'config_id1': {
    #             'id': 'config_id1',
    #             'parent_id': 'chain_1',
    #             'name': 'changed_system_name_chain',
    #             'exporter_url': 'dummy_url1',
    #             'monitor_system': "True",
    #         },
    #     }
    #     updated_configs_general = {
    #         'config_id2': {
    #             'id': 'config_id2',
    #             'parent_id': 'GENERAL',
    #             'name': 'changed_system_name_gen',
    #             'exporter_url': 'dummy_url2',
    #             'monitor_system': "True",
    #         },
    #     }
    #     self.test_manager._systems_configs = self.systems_configs_example
    #     self.test_manager._config_process_dict = \
    #         self.config_process_dict_example
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #
    #         # We will send new configs through both the existing and
    #         # non-existing chain and general paths to make sure that all routes
    #         # work as expected.
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_updated_configs_chain = json.dumps(updated_configs_chain)
    #         body_updated_configs_general = json.dumps(updated_configs_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties,
    #                                            body_updated_configs_chain)
    #         self.assertEqual(1, startup_mock.call_count)
    #         args, _ = startup_mock.call_args
    #         self.assertTrue('config_id1' and 'Substrate Polkadot' in args)
    #         self.assertEqual(updated_configs_chain['config_id1']['id'],
    #                          args[0].system_id)
    #         self.assertEqual(updated_configs_chain['config_id1']['parent_id'],
    #                          args[0].parent_id)
    #         self.assertEqual(updated_configs_chain['config_id1']['name'],
    #                          args[0].system_name)
    #         self.assertEqual(
    #             str_to_bool(
    #                 updated_configs_chain['config_id1']['monitor_system']),
    #             args[0].monitor_system)
    #         self.assertEqual(
    #             updated_configs_chain['config_id1']['exporter_url'],
    #             args[0].node_exporter_url)
    #
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties,
    #                                            body_updated_configs_general)
    #         self.assertEqual(2, startup_mock.call_count)
    #         args, _ = startup_mock.call_args
    #         self.assertTrue('config_id2' and 'general' in args)
    #         self.assertEqual(updated_configs_general['config_id2']['id'],
    #                          args[0].system_id)
    #         self.assertEqual(updated_configs_general['config_id2']['parent_id'],
    #                          args[0].parent_id)
    #         self.assertEqual(updated_configs_general['config_id2']['name'],
    #                          args[0].system_name)
    #         self.assertEqual(
    #             str_to_bool(
    #                 updated_configs_general['config_id2']['monitor_system']),
    #             args[0].monitor_system)
    #         self.assertEqual(
    #             updated_configs_general['config_id2']['exporter_url'],
    #             args[0].node_exporter_url)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch("src.monitors.starters.create_logger")
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_process_configs_terminates_monitors_for_removed_configs(
    #         self, mock_ack, mock_create_logger) -> None:
    #     # In this test we will check that when a config is removed, it's monitor
    #     # is terminated by _process_configs.
    #     mock_ack.return_value = None
    #     mock_create_logger.return_value = self.dummy_logger
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_initial = json.dumps(self.sent_configs_example_chain)
    #         body_general_initial = json.dumps(self.sent_configs_example_general)
    #         body_chain_new = json.dumps({})
    #         body_general_new = json.dumps({})
    #         properties = pika.spec.BasicProperties()
    #
    #         # First send the new configs as the state is empty
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_initial)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_initial)
    #
    #         # Give time for the monitors to start
    #         time.sleep(1)
    #
    #         # Assure that the processes have been started
    #         self.assertTrue(self.test_manager.config_process_dict[
    #                             'config_id1']['process'].is_alive())
    #         self.assertTrue(self.test_manager.config_process_dict[
    #                             'config_id2']['process'].is_alive())
    #
    #         # Send the updated configs
    #         conf_id1_old_proc = self.test_manager.config_process_dict[
    #             'config_id1']['process']
    #         conf_id2_old_proc = self.test_manager.config_process_dict[
    #             'config_id2']['process']
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_new)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_new)
    #
    #         # Give time for the monitors to stop
    #         time.sleep(1)
    #
    #         # Check that the old process has terminated
    #         self.assertFalse(conf_id1_old_proc.is_alive())
    #         self.assertFalse(conf_id2_old_proc.is_alive())
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_process_configs_ignores_new_configs_with_missing_keys(
    #         self, mock_ack) -> None:
    #     # We will check whether the state is kept intact if new configurations
    #     # with missing keys are sent. Exceptions should never be raised in this
    #     # case, and basic_ack must be called to ignore the message.
    #     mock_ack.return_value = None
    #     new_configs_chain = {
    #         'config_id3': {
    #             'id': 'config_id3',
    #             'parentfg_id': 'chain_1',
    #             'namfge': 'system_3',
    #             'exporfgter_url': 'dummy_url3',
    #             'monitorfg_system': "True",
    #         },
    #     }
    #     new_configs_general = {
    #         'config_id5': {
    #             'id': 'config_id5',
    #             'parentdfg_id': 'GENERAL',
    #             'namdfge': 'system_5',
    #             'exporter_urdfgl': 'dummy_url5',
    #             'monitor_systdfgem': "True",
    #         },
    #     }
    #     self.test_manager._systems_configs = self.systems_configs_example
    #     self.test_manager._config_process_dict = \
    #         self.config_process_dict_example
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #
    #         # We will send new configs through both the existing and
    #         # non-existing chain and general paths to make sure that all routes
    #         # work as expected.
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_new_configs_chain = json.dumps(new_configs_chain)
    #         body_new_configs_general = json.dumps(new_configs_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties,
    #                                            body_new_configs_general)
    #         self.assertEqual(1, mock_ack.call_count)
    #         self.assertEqual(self.config_process_dict_example,
    #                          self.test_manager.config_process_dict)
    #         self.assertEqual(self.systems_configs_example,
    #                          self.test_manager.systems_configs)
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties,
    #                                            body_new_configs_chain)
    #         self.assertEqual(2, mock_ack.call_count)
    #         self.assertEqual(self.config_process_dict_example,
    #                          self.test_manager.config_process_dict)
    #         self.assertEqual(self.systems_configs_example,
    #                          self.test_manager.systems_configs)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_process_configs_ignores_modified_configs_with_missing_keys(
    #         self, mock_ack) -> None:
    #     # We will check whether the state is kept intact if modified
    #     # configurations with missing keys are sent. Exceptions should never be
    #     # raised in this case, and basic_ack must be called to ignore the
    #     # message.
    #     mock_ack.return_value = None
    #     updated_configs_chain = {
    #         'config_id1': {
    #             'id': 'config_id1',
    #             'parentfg_id': 'chain_1',
    #             'namfge': 'system_1',
    #             'exporfgter_url': 'dummy_url1',
    #             'monitorfg_system': "True",
    #         },
    #     }
    #     updated_configs_general = {
    #         'config_id2': {
    #             'id': 'config_id2',
    #             'parentdfg_id': 'GENERAL',
    #             'namdfge': 'system_2',
    #             'exporter_urdfgl': 'dummy_url2',
    #             'monitor_systdfgem': "True",
    #         },
    #     }
    #     self.test_manager._systems_configs = self.systems_configs_example
    #     self.test_manager._config_process_dict = \
    #         self.config_process_dict_example
    #     try:
    #         # Must create a connection so that the blocking channel is passed
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #
    #         # We will send new configs through both the existing and
    #         # non-existing chain and general paths to make sure that all routes
    #         # work as expected.
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_updated_configs_chain = json.dumps(updated_configs_chain)
    #         body_updated_configs_general = json.dumps(updated_configs_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties,
    #                                            body_updated_configs_general)
    #         self.assertEqual(1, mock_ack.call_count)
    #         self.assertEqual(self.config_process_dict_example,
    #                          self.test_manager.config_process_dict)
    #         self.assertEqual(self.systems_configs_example,
    #                          self.test_manager.systems_configs)
    #
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties,
    #                                            body_updated_configs_chain)
    #         self.assertEqual(2, mock_ack.call_count)
    #         self.assertEqual(self.config_process_dict_example,
    #                          self.test_manager.config_process_dict)
    #         self.assertEqual(self.systems_configs_example,
    #                          self.test_manager.systems_configs)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @freeze_time("2012-01-01")
    # @mock.patch("src.monitors.starters.create_logger")
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_process_ping_sends_a_valid_hb_if_all_processes_are_alive(
    #         self, mock_ack, mock_create_logger) -> None:
    #     # This test creates a queue which receives messages with the same
    #     # routing key as the ones sent by send_heartbeat, and checks that the
    #     # received heartbeat is valid.
    #     mock_create_logger.return_value = self.dummy_logger
    #     mock_ack.return_value = None
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_initial = json.dumps(self.sent_configs_example_chain)
    #         body_general_initial = json.dumps(self.sent_configs_example_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         # First send the new configs as the state is empty
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_initial)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_initial)
    #
    #         # Give time for the processes to start
    #         time.sleep(1)
    #
    #         # Delete the queue before to avoid messages in the queue on error.
    #         self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
    #
    #         # Initialise
    #         method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         body = 'ping'
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=False
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #         self.test_manager.rabbitmq.queue_bind(
    #             queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
    #             routing_key='heartbeat.manager')
    #         self.test_manager._process_ping(blocking_channel, method_hb,
    #                                         properties, body)
    #
    #         # By re-declaring the queue again we can get the number of messages
    #         # in the queue.
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=True
    #         )
    #         self.assertEqual(1, res.method.message_count)
    #
    #         # Check that the message received is a valid HB
    #         _, _, body = self.test_manager.rabbitmq.basic_get(
    #             self.test_queue_name)
    #         expected_output = {
    #             'component_name': self.test_manager.name,
    #             'running_processes':
    #                 [self.test_manager.config_process_dict['config_id1'][
    #                      'component_name'],
    #                  self.test_manager.config_process_dict['config_id2'][
    #                      'component_name']],
    #             'dead_processes': [],
    #             'timestamp': datetime(2012, 1, 1).timestamp(),
    #         }
    #         self.assertEqual(expected_output, json.loads(body))
    #
    #         # Clean before test finishes
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].join()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].join()
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @freeze_time("2012-01-01")
    # @mock.patch("src.monitors.starters.create_logger")
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_process_ping_sends_a_valid_hb_if_some_processes_alive_some_dead(
    #         self, mock_ack, mock_create_logger) -> None:
    #     # This test creates a queue which receives messages with the same
    #     # routing key as the ones sent by send_heartbeat, and checks that the
    #     # received heartbeat is valid.
    #     mock_create_logger.return_value = self.dummy_logger
    #     mock_ack.return_value = None
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_initial = json.dumps(self.sent_configs_example_chain)
    #         body_general_initial = json.dumps(self.sent_configs_example_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         # First send the new configs as the state is empty
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_initial)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_initial)
    #
    #         # Give time for the processes to start
    #         time.sleep(1)
    #
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].join()
    #
    #         # Give time for the process to stop
    #         time.sleep(1)
    #
    #         # Delete the queue before to avoid messages in the queue on error.
    #         self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
    #
    #         # Initialise
    #         method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         body = 'ping'
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=False
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #         self.test_manager.rabbitmq.queue_bind(
    #             queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
    #             routing_key='heartbeat.manager')
    #         self.test_manager._process_ping(blocking_channel, method_hb,
    #                                         properties, body)
    #
    #         # By re-declaring the queue again we can get the number of messages
    #         # in the queue.
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=True
    #         )
    #         self.assertEqual(1, res.method.message_count)
    #
    #         # Check that the message received is a valid HB
    #         _, _, body = self.test_manager.rabbitmq.basic_get(
    #             self.test_queue_name)
    #         expected_output = {
    #             'component_name': self.test_manager.name,
    #             'running_processes':
    #                 [self.test_manager.config_process_dict['config_id2'][
    #                      'component_name']],
    #             'dead_processes':
    #                 [self.test_manager.config_process_dict['config_id1'][
    #                      'component_name']],
    #             'timestamp': datetime(2012, 1, 1).timestamp(),
    #         }
    #         self.assertEqual(expected_output, json.loads(body))
    #
    #         # Clean before test finishes
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].join()
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @freeze_time("2012-01-01")
    # @mock.patch("src.monitors.starters.create_logger")
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # def test_process_ping_sends_a_valid_hb_if_all_processes_dead(
    #         self, mock_ack, mock_create_logger) -> None:
    #     # This test creates a queue which receives messages with the same
    #     # routing key as the ones sent by send_heartbeat, and checks that the
    #     # received heartbeat is valid.
    #     mock_create_logger.return_value = self.dummy_logger
    #     mock_ack.return_value = None
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_initial = json.dumps(self.sent_configs_example_chain)
    #         body_general_initial = json.dumps(self.sent_configs_example_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         # First send the new configs as the state is empty
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_initial)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_initial)
    #
    #         # Give time for the processes to start
    #         time.sleep(1)
    #
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].join()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].join()
    #
    #         # Give time for the process to stop
    #         time.sleep(1)
    #
    #         # Delete the queue before to avoid messages in the queue on error.
    #         self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
    #
    #         # Initialise
    #         method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         body = 'ping'
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=False
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #         self.test_manager.rabbitmq.queue_bind(
    #             queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
    #             routing_key='heartbeat.manager')
    #         self.test_manager._process_ping(blocking_channel, method_hb,
    #                                         properties, body)
    #
    #         # By re-declaring the queue again we can get the number of messages
    #         # in the queue.
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=True
    #         )
    #         self.assertEqual(1, res.method.message_count)
    #
    #         # Check that the message received is a valid HB
    #         _, _, body = self.test_manager.rabbitmq.basic_get(
    #             self.test_queue_name)
    #         expected_output = {
    #             'component_name': self.test_manager.name,
    #             'running_processes': [],
    #             'dead_processes':
    #                 [self.test_manager.config_process_dict['config_id1'][
    #                      'component_name'],
    #                  self.test_manager.config_process_dict['config_id2'][
    #                      'component_name']],
    #             'timestamp': datetime(2012, 1, 1).timestamp(),
    #         }
    #         self.assertEqual(expected_output, json.loads(body))
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @freeze_time("2012-01-01")
    # @mock.patch.object(RabbitMQApi, "basic_ack")
    # @mock.patch("src.monitors.starters.create_logger")
    # @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    # def test_process_ping_restarts_dead_processes(
    #         self, send_hb_mock, mock_create_logger, mock_ack) -> None:
    #     send_hb_mock.return_value = None
    #     mock_create_logger.return_value = self.dummy_logger
    #     mock_ack.return_value = None
    #     try:
    #         self.test_manager.rabbitmq.connect()
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method_chains = pika.spec.Basic.Deliver(
    #             routing_key=self.chains_routing_key)
    #         method_general = pika.spec.Basic.Deliver(
    #             routing_key=self.general_routing_key)
    #         body_chain_initial = json.dumps(self.sent_configs_example_chain)
    #         body_general_initial = json.dumps(self.sent_configs_example_general)
    #         properties = pika.spec.BasicProperties()
    #
    #         # First send the new configs as the state is empty
    #         self.test_manager._process_configs(blocking_channel, method_chains,
    #                                            properties, body_chain_initial)
    #         self.test_manager._process_configs(blocking_channel, method_general,
    #                                            properties, body_general_initial)
    #
    #         # Give time for the processes to start
    #         time.sleep(1)
    #
    #         # Automate the case when having all processes dead
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].join()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].join()
    #
    #         # Give time for the processes to terminate
    #         time.sleep(1)
    #
    #         # Check that that the processes have terminated
    #         self.assertFalse(self.test_manager.config_process_dict[
    #                              'config_id1']['process'].is_alive())
    #         self.assertFalse(self.test_manager.config_process_dict[
    #                              'config_id2']['process'].is_alive())
    #
    #         # Initialise
    #         method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         body = 'ping'
    #         self.test_manager._process_ping(blocking_channel, method_hb,
    #                                         properties, body)
    #
    #         # Give time for the processes to start
    #         time.sleep(1)
    #
    #         self.assertTrue(self.test_manager.config_process_dict['config_id1'][
    #                             'process'].is_alive())
    #         self.assertTrue(self.test_manager.config_process_dict['config_id2'][
    #                             'process'].is_alive())
    #
    #         # Clean before test finishes
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id1'][
    #             'process'].join()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].terminate()
    #         self.test_manager.config_process_dict['config_id2'][
    #             'process'].join()
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    # @mock.patch.object(SystemMonitorsManager,
    #                    "_create_and_start_monitor_process")
    # @mock.patch.object(multiprocessing.Process, "join")
    # @mock.patch.object(multiprocessing.Process, "is_alive")
    # def test_process_ping_restarts_dead_processes_with_correct_info(
    #         self, mock_alive, mock_join, startup_mock, send_hb_mock) -> None:
    #     send_hb_mock.return_value = None
    #     startup_mock.return_value = None
    #     mock_alive.return_value = False
    #     mock_join.return_value = None
    #     try:
    #         self.test_manager.rabbitmq.connect()
    #
    #         del self.systems_configs_example['general']
    #         del self.config_process_dict_example['config_id2']
    #         self.test_manager._systems_configs = self.systems_configs_example
    #         self.test_manager._config_process_dict = \
    #             self.config_process_dict_example
    #
    #         # Initialise
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         properties = pika.spec.BasicProperties()
    #         body = 'ping'
    #         self.test_manager._process_ping(blocking_channel, method,
    #                                         properties, body)
    #
    #         self.assertEqual(1, startup_mock.call_count)
    #         args, _ = startup_mock.call_args
    #         self.assertTrue('config_id1' and 'Substrate Polkadot' in args)
    #         self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
    #                              'config_id1']['id'], args[0].system_id)
    #         self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
    #                              'config_id1']['parent_id'], args[0].parent_id)
    #         self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
    #                              'config_id1']['name'], args[0].system_name)
    #         self.assertEqual(
    #             str_to_bool(self.systems_configs_example['Substrate Polkadot'][
    #                             'config_id1']['monitor_system']),
    #             args[0].monitor_system)
    #         self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
    #                              'config_id1']['exporter_url'],
    #                          args[0].node_exporter_url)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(multiprocessing.Process, "is_alive")
    # @mock.patch.object(multiprocessing.Process, "start")
    # @mock.patch.object(multiprocessing, 'Process')
    # def test_process_ping_does_not_send_hb_if_processing_fails(
    #         self, mock_process, mock_start, is_alive_mock) -> None:
    #     # This test creates a queue which receives messages with the same
    #     # routing key as the ones sent by send_heartbeat. In this test we will
    #     # check that no heartbeat is sent when mocking a raised exception.
    #     is_alive_mock.side_effect = self.test_exception
    #     mock_start.return_value = None
    #     mock_process.side_effect = self.dummy_process1
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #
    #         # Delete the queue before to avoid messages in the queue on error.
    #         self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
    #
    #         self.test_manager._systems_configs = self.systems_configs_example
    #         self.test_manager._config_process_dict = \
    #             self.config_process_dict_example
    #
    #         # Initialise
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         properties = pika.spec.BasicProperties()
    #         body = 'ping'
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=False
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #         self.test_manager.rabbitmq.queue_bind(
    #             queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
    #             routing_key='heartbeat.manager')
    #         self.test_manager._process_ping(blocking_channel, method,
    #                                         properties, body)
    #
    #         # By re-declaring the queue again we can get the number of messages
    #         # in the queue.
    #         res = self.test_manager.rabbitmq.queue_declare(
    #             queue=self.test_queue_name, durable=True, exclusive=False,
    #             auto_delete=False, passive=True
    #         )
    #         self.assertEqual(0, res.method.message_count)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
    #         self) -> None:
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #
    #         # Initialise
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         properties = pika.spec.BasicProperties()
    #         body = 'ping'
    #
    #         self.test_manager._process_ping(blocking_channel, method,
    #                                         properties, body)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    # def test_process_ping_send_hb_raises_amqp_connection_err_on_connection_err(
    #         self, hb_mock) -> None:
    #     hb_mock.side_effect = pika.exceptions.AMQPConnectionError('test')
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #
    #         # Initialise
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         properties = pika.spec.BasicProperties()
    #         body = 'ping'
    #
    #         self.assertRaises(pika.exceptions.AMQPConnectionError,
    #                           self.test_manager._process_ping, blocking_channel,
    #                           method, properties, body)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    # def test_process_ping_send_hb_raises_amqp_chan_err_on_chan_err(
    #         self, hb_mock) -> None:
    #     hb_mock.side_effect = pika.exceptions.AMQPChannelError('test')
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #
    #         # Initialise
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         properties = pika.spec.BasicProperties()
    #         body = 'ping'
    #
    #         self.assertRaises(pika.exceptions.AMQPChannelError,
    #                           self.test_manager._process_ping, blocking_channel,
    #                           method, properties, body)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
    #
    # @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    # def test_process_ping_send_hb_raises_exception_on_unexpected_exception(
    #         self, hb_mock) -> None:
    #     hb_mock.side_effect = self.test_exception
    #     try:
    #         self.test_manager._initialise_rabbitmq()
    #
    #         # Initialise
    #         blocking_channel = self.test_manager.rabbitmq.channel
    #         method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
    #         properties = pika.spec.BasicProperties()
    #         body = 'ping'
    #
    #         self.assertRaises(PANICException, self.test_manager._process_ping,
    #                           blocking_channel, method, properties, body)
    #     except Exception as e:
    #         self.fail("Test failed: {}".format(e))
