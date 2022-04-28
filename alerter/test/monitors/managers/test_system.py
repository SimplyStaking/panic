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
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.system import SystemMonitorsManager
from src.monitors.starters import start_system_monitor
from src.utils import env
from src.utils.constants.names import SYSTEM_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE, SYS_MON_MAN_CONFIGS_QUEUE_NAME,
    SYS_MON_MAN_HEARTBEAT_QUEUE_NAME, PING_ROUTING_KEY,
    SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_SYS,
    NODES_CONFIGS_ROUTING_KEY_CHAINS, SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN,
    HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY, MONITORABLE_EXCHANGE)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from test.test_utils.utils import (
    infinite_fn, connect_to_rabbit, delete_queue_if_exists,
    delete_exchange_if_exists, disconnect_from_rabbit)


class TestSystemMonitorsManager(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_system_monitors_manager'
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
        self.dummy_process4 = Process(target=infinite_fn, args=())
        self.dummy_process4.daemon = True

        # Some configuration examples
        self.system_id_1 = 'config_id1'
        self.parent_id_1 = 'chain_1'
        self.system_name_1 = 'system_1'
        self.monitor_system_1 = True
        self.node_exporter_url_1 = 'dummy_url1'
        self.chain_1 = 'Substrate Polkadot'
        self.base_chain_1 = 'Substrate'
        self.sub_chain_1 = 'Polkadot'
        self.system_config_1 = SystemConfig(self.system_id_1, self.parent_id_1,
                                            self.system_name_1,
                                            self.monitor_system_1,
                                            self.node_exporter_url_1)
        self.system_id_2 = 'config_id2'
        self.parent_id_2 = 'GENERAL'
        self.system_name_2 = 'system_2'
        self.monitor_system_2 = True
        self.node_exporter_url_2 = 'dummy_url2'
        self.chain_2 = 'general'
        self.base_chain_2 = 'general'
        self.sub_chain_2 = 'general'
        self.system_config_2 = SystemConfig(self.system_id_2, self.parent_id_2,
                                            self.system_name_2,
                                            self.monitor_system_2,
                                            self.node_exporter_url_2)
        self.system_id_3 = 'config_id3'
        self.parent_id_3 = 'chain_1'
        self.system_name_3 = 'system_3'
        self.monitor_system_3 = True
        self.node_exporter_url_3 = 'dummy_url3'
        self.chain_3 = 'Substrate Polkadot'
        self.base_chain_3 = 'Substrate'
        self.sub_chain_3 = 'Polkadot'
        self.system_config_3 = SystemConfig(self.system_id_3, self.parent_id_3,
                                            self.system_name_3,
                                            self.monitor_system_3,
                                            self.node_exporter_url_3)
        self.system_id_4 = 'config_id4'
        self.parent_id_4 = 'chain_2'
        self.system_name_4 = 'system_4'
        self.monitor_system_4 = True
        self.node_exporter_url_4 = 'dummy_url4'
        self.chain_4 = 'Chainlink chainlink'
        self.base_chain_4 = 'Chainlink'
        self.sub_chain_4 = 'chainlink'
        self.system_config_4 = SystemConfig(self.system_id_4, self.parent_id_4,
                                            self.system_name_4,
                                            self.monitor_system_4,
                                            self.node_exporter_url_4)

        # Some config_process_dict, sent_configs and system_configs examples.
        # Here we wil assume that only configurations 1, 2, 4 are in the state.
        self.config_process_dict_example = {
            self.system_id_1: {
                'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                    self.system_name_1),
                'process': self.dummy_process1,
                'chain': self.chain_1,
                'parent_id': self.parent_id_1,
                'source_name': self.system_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
            },
            self.system_id_2: {
                'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                    self.system_name_2),
                'process': self.dummy_process2,
                'chain': self.chain_2,
                'parent_id': self.parent_id_2,
                'source_name': self.system_name_2,
                'base_chain': self.base_chain_2,
                'sub_chain': self.sub_chain_2,
            },
            self.system_id_4: {
                'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                    self.system_name_4),
                'process': self.dummy_process4,
                'chain': self.chain_4,
                'parent_id': self.parent_id_4,
                'source_name': self.system_name_4,
                'base_chain': self.base_chain_4,
                'sub_chain': self.sub_chain_4,
            },
        }
        self.systems_configs_example = {
            self.chain_1: {
                self.system_id_1: {
                    'id': self.system_id_1,
                    'parent_id': self.parent_id_1,
                    'name': self.system_name_1,
                    'exporter_url': self.node_exporter_url_1,
                    'monitor_system': str(self.monitor_system_1),
                },
            },
            self.chain_2: {
                self.system_id_2: {
                    'id': self.system_id_2,
                    'parent_id': self.parent_id_2,
                    'name': self.system_name_2,
                    'exporter_url': self.node_exporter_url_2,
                    'monitor_system': str(self.monitor_system_2),
                }
            },
            self.chain_4: {
                self.system_id_4: {
                    'id': self.system_id_4,
                    'parent_id': self.parent_id_4,
                    'name': self.system_name_4,
                    'exporter_url': self.node_exporter_url_4,
                    'monitor_system': str(self.monitor_system_4),
                }
            },
        }
        self.sent_configs_example_chain_nodes = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parent_id': self.parent_id_1,
                'name': self.system_name_1,
                'exporter_url': self.node_exporter_url_1,
                'monitor_system': str(self.monitor_system_1),
            }
        }
        self.sent_configs_example_chain_sys = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parent_id': self.parent_id_4,
                'name': self.system_name_4,
                'exporter_url': self.node_exporter_url_4,
                'monitor_system': str(self.monitor_system_4),
            }
        }
        self.sent_configs_example_general = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parent_id': self.parent_id_2,
                'name': self.system_name_2,
                'exporter_url': self.node_exporter_url_2,
                'monitor_system': str(self.monitor_system_2),
            }
        }

        # Test manager instance
        self.test_manager = SystemMonitorsManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)

        # Relevant routing keys
        self.chains_routing_key_nodes = 'chains.Substrate.Polkadot.nodes_config'
        self.chains_routing_key_sys = \
            'chains.Chainlink.chainlink.systems_config'
        self.general_routing_key = SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               SYS_MON_MAN_HEARTBEAT_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               SYS_MON_MAN_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq, CONFIG_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  MONITORABLE_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.rabbitmq = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None
        self.config_process_dict_example = None
        self.systems_configs_example = None
        self.system_config_1 = None
        self.system_config_2 = None
        self.system_config_3 = None
        self.system_config_4 = None
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

    def test_systems_configs_returns_systems_configs(self) -> None:
        self.test_manager._systems_configs = self.systems_configs_example
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        mock_start_consuming.assert_called_once()

    @mock.patch.object(RabbitMQApi, 'basic_consume')
    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self, mock_basic_consume) -> None:
        mock_basic_consume.return_value = None
        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        self.rabbitmq.connect()
        self.test_manager.rabbitmq.queue_delete(
            SYS_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_CONFIGS_QUEUE_NAME)
        self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(MONITORABLE_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_manager._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_manager.rabbitmq.is_connected)
        self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_manager.rabbitmq.channel._delivery_confirmation)

        # Check whether the exchanges and queues have been creating by
        # sending messages with the same routing keys as for the queues, and
        # checking what messages have been received if any.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=PING_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=SYS_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS_SYS,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=NODES_CONFIGS_ROUTING_KEY_CHAINS,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=SYS_MON_MAN_CONFIGS_ROUTING_KEY_GEN,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_manager.rabbitmq.queue_declare(
            SYS_MON_MAN_HEARTBEAT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            SYS_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())

        res = self.test_manager.rabbitmq.queue_declare(
            SYS_MON_MAN_CONFIGS_QUEUE_NAME, False, True, False, False)
        self.assertEqual(3, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            SYS_MON_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())
        _, _, body = self.test_manager.rabbitmq.basic_get(
            SYS_MON_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())
        _, _, body = self.test_manager.rabbitmq.basic_get(
            SYS_MON_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())

        # Check that basic_consume was called twice, once for each consumer
        # queue
        calls = mock_basic_consume.call_args_list
        self.assertEqual(2, len(calls))

        # Check that the publishing exchanges were created by sending messages
        # to them. If this fails an exception is raised hence the test fails.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=MONITORABLE_EXCHANGE, routing_key='test_key',
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

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
        mock_init.return_value = self.dummy_process3
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        expected_output = self.test_manager._config_process_dict
        expected_output[self.system_id_3] = {
            'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                self.system_name_3),
            'process': self.dummy_process3,
            'chain': self.chain_3,
            'chain_id': self.parent_id_3,
            'source_name': self.system_name_3,
            'base_chain': self.base_chain_3,
            'sub_chain': self.sub_chain_3,
        }
        self.test_manager._create_and_start_monitor_process(
            self.system_config_3, self.system_id_3, self.chain_3,
            self.base_chain_3, self.sub_chain_3)

        self.assertEqual(expected_output, self.test_manager.config_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_monitor_process_creates_the_correct_process(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._create_and_start_monitor_process(
            self.system_config_3, self.system_id_3, self.chain_3,
            self.base_chain_3, self.sub_chain_3)

        new_entry = self.test_manager.config_process_dict[self.system_id_3]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(1, len(new_entry_process._args))
        self.assertEqual(self.system_config_3, new_entry_process._args[0])
        self.assertEqual(start_system_monitor, new_entry_process._target)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_monitor_process_starts_the_process(
            self, mock_start) -> None:
        self.test_manager._create_and_start_monitor_process(
            self.system_config_3, self.system_id_3, self.chain_3,
            self.base_chain_3, self.sub_chain_3)
        mock_start.assert_called_once()

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_default_key(
            self, mock_ack, mock_process_send_mon_data) -> None:
        # This test will pass if the stored systems config does not change.
        # This would mean that the DEFAULT key was ignored, otherwise, it would
        # have been included as a new config.
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        old_systems_configs = copy.deepcopy(self.systems_configs_example)
        self.test_manager._systems_configs = self.systems_configs_example

        # We will pass the acceptable schema as a value with all possible
        # routing keys to make sure that the default key will never be added.
        # By passing the schema we will also prevent processing errors from
        # happening.
        self.sent_configs_example_chain_nodes['DEFAULT'] = {
            'id': 'default_id1',
            'parent_id': 'chain_1',
            'name': 'default_system_1',
            'exporter_url': 'default_dummy_url1',
            'monitor_system': "True",
        }
        self.sent_configs_example_general['DEFAULT'] = {
            'id': 'default_id2',
            'parent_id': 'GENERAL',
            'name': 'default_system_2',
            'exporter_url': 'default_dummy_url2',
            'monitor_system': "True",
        }
        self.sent_configs_example_chain_sys['DEFAULT'] = {
            'id': 'default_id3',
            'parent_id': 'chain_3',
            'name': 'default_system_3',
            'exporter_url': 'default_dummy_url3',
            'monitor_system': "True",
        }

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_chain_nodes = json.dumps(self.sent_configs_example_chain_nodes)
        body_chain_sys = json.dumps(self.sent_configs_example_chain_sys)
        body_general = json.dumps(self.sent_configs_example_general)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties, body_general)
        self.assertEqual(old_systems_configs, self.test_manager.systems_configs)
        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_chain_nodes)
        self.assertEqual(old_systems_configs, self.test_manager.systems_configs)
        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties, body_chain_sys)
        self.assertEqual(old_systems_configs, self.test_manager.systems_configs)
        self.assertEqual(3, mock_ack.call_count)

    @parameterized.expand([
        ('chains.Chainlink.chainlink.nodes_config',),
        ('chains.chainlink.binance smart chain.nodes_config',)
    ])
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_confs_ignores_nodes_confs_from_chains_with_separate_sys_confs(
            self, routing_key, mock_ack) -> None:
        # This test will pass if the stored systems config does not change.
        mock_ack.return_value = None
        old_systems_configs = copy.deepcopy(self.systems_configs_example)
        self.test_manager._systems_configs = self.systems_configs_example
        sent_configs = {
            'config_id5': {
                'id': 'config_id5',
                'parent_id': self.parent_id_4,
                'name': 'system_5',
                'exporter_url': 'url_5',
                'monitor_system': "True",
            }
        }

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=routing_key)
        body = json.dumps(sent_configs)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel, method, properties,
                                           body)
        self.assertEqual(old_systems_configs, self.test_manager.systems_configs)
        mock_ack.assert_called_once()

    '''
    In the tests below we will assume that configs are sent with the acceptable
    routing keys
    '''

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    def test_process_configs_stores_new_configs_to_be_monitored_correctly(
            self, startup_mock, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether new configs are added to the state. Since some
        # new configs have `monitor_system = False` we are also testing that
        # new configs are ignored if they should not be monitored.
        startup_mock.return_value = None
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._systems_configs = self.systems_configs_example
        new_configs_chain_nodes = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parent_id': self.parent_id_1,
                'name': self.system_name_1,
                'exporter_url': self.node_exporter_url_1,
                'monitor_system': str(self.monitor_system_1),
            },
            self.system_id_3: {
                'id': self.system_id_3,
                'parent_id': self.parent_id_3,
                'name': self.system_name_3,
                'exporter_url': self.node_exporter_url_3,
                'monitor_system': str(self.monitor_system_3),
            },
            'config_id5': {
                'id': 'config_id5',
                'parent_id': self.parent_id_1,
                'name': 'system_5',
                'exporter_url': 'url_5',
                'monitor_system': "False",
            }
        }
        new_configs_chain_sys = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parent_id': self.parent_id_4,
                'name': self.system_name_4,
                'exporter_url': self.node_exporter_url_4,
                'monitor_system': str(self.monitor_system_4),
            },
            'config_id6': {
                'id': 'config_id6',
                'parent_id': self.parent_id_4,
                'name': 'system_6',
                'exporter_url': 'url_6',
                'monitor_system': "True",
            },
            'config_id7': {
                'id': 'config_id7',
                'parent_id': self.parent_id_4,
                'name': 'system_7',
                'exporter_url': 'url_7',
                'monitor_system': "False",
            }
        }
        new_configs_general = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parent_id': self.parent_id_2,
                'name': self.system_name_2,
                'exporter_url': self.node_exporter_url_2,
                'monitor_system': str(self.monitor_system_2),
            },
            'config_id8': {
                'id': 'config_id8',
                'parent_id': self.parent_id_2,
                'name': 'system_8',
                'exporter_url': 'url_8',
                'monitor_system': "True",
            },
            'config_id9': {
                'id': 'config_id9',
                'parent_id': self.parent_id_2,
                'name': 'system_9',
                'exporter_url': 'url_9',
                'monitor_system': "False",
            }
        }
        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_new_configs_chain_sys = json.dumps(new_configs_chain_sys)
        body_new_configs_chain_nodes = json.dumps(new_configs_chain_nodes)
        body_new_configs_general = json.dumps(new_configs_general)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties,
                                           body_new_configs_chain_sys)
        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_new_configs_chain_nodes)
        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties,
                                           body_new_configs_general)

        expected_sys_confs = copy.deepcopy(self.systems_configs_example)
        expected_sys_confs[self.chain_1][self.system_id_3] = \
            new_configs_chain_nodes[self.system_id_3]
        expected_sys_confs[self.chain_2]['config_id8'] = \
            new_configs_general['config_id8']
        expected_sys_confs[self.chain_4]['config_id6'] = \
            new_configs_chain_sys['config_id6']
        self.assertEqual(expected_sys_confs, self.test_manager.systems_configs)
        self.assertEqual(3, mock_ack.call_count)

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_configs_stores_modified_configs_to_be_monitored_correctly(
            self, join_mock, terminate_mock, startup_mock, mock_ack,
            mock_process_send_mon_data) -> None:
        # In this test we will check that modified configurations with
        # `monitor_system = True` are stored correctly in the state. Some
        # configurations will have `monitor_system = False` to check whether the
        # monitor associated with the previous configuration is terminated.
        join_mock.return_value = None
        terminate_mock.return_value = None
        startup_mock.return_value = None
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        new_configs_chain_nodes_monitor_true = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parent_id': self.parent_id_1,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_1,
                'monitor_system': str(self.monitor_system_1),
            },
        }
        new_configs_chain_nodes_monitor_false = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parent_id': self.parent_id_1,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_1,
                'monitor_system': "False",
            },
        }
        new_configs_chain_sys_monitor_true = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parent_id': self.parent_id_4,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_4,
                'monitor_system': str(self.monitor_system_4),
            },
        }
        new_configs_chain_sys_monitor_false = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parent_id': self.parent_id_4,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_4,
                'monitor_system': "False",
            },
        }
        new_configs_general_monitor_true = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parent_id': self.parent_id_2,
                'name': 'new_system_name_general',
                'exporter_url': self.node_exporter_url_2,
                'monitor_system': str(self.monitor_system_2),
            },
        }
        new_configs_general_monitor_false = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parent_id': self.parent_id_2,
                'name': 'new_system_name_general',
                'exporter_url': self.node_exporter_url_2,
                'monitor_system': "False",
            },
        }
        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_chain_nodes_mon_true = json.dumps(
            new_configs_chain_nodes_monitor_true)
        body_chain_sys_mon_true = json.dumps(
            new_configs_chain_sys_monitor_true)
        body_general_mon_true = json.dumps(new_configs_general_monitor_true)
        body_chain_nodes_mon_false = json.dumps(
            new_configs_chain_nodes_monitor_false)
        body_chain_sys_mon_false = json.dumps(
            new_configs_chain_sys_monitor_false)
        body_general_mon_false = json.dumps(
            new_configs_general_monitor_false)
        properties = pika.spec.BasicProperties()
        expected_output = copy.deepcopy(self.systems_configs_example)

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_chain_nodes_mon_true)
        expected_output[self.chain_1][self.system_id_1] = \
            new_configs_chain_nodes_monitor_true[self.system_id_1]
        self.assertEqual(expected_output, self.test_manager.systems_configs)

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties,
                                           body_chain_sys_mon_true)
        expected_output[self.chain_4][self.system_id_4] = \
            new_configs_chain_sys_monitor_true[self.system_id_4]
        self.assertEqual(expected_output, self.test_manager.systems_configs)

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties, body_general_mon_true)
        expected_output[self.chain_2][self.system_id_2] = \
            new_configs_general_monitor_true[self.system_id_2]
        self.assertEqual(expected_output, self.test_manager.systems_configs)

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_chain_nodes_mon_false)
        expected_output[self.chain_1] = {}
        self.assertEqual(expected_output, self.test_manager.systems_configs)
        self.assertTrue(
            self.system_id_1 not in self.test_manager.config_process_dict)

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties, body_chain_sys_mon_false)
        expected_output[self.chain_4] = {}
        self.assertEqual(expected_output, self.test_manager.systems_configs)
        self.assertTrue(
            self.system_id_4 not in self.test_manager.config_process_dict)

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties, body_general_mon_false)
        expected_output[self.chain_2] = {}
        self.assertEqual(expected_output, self.test_manager.systems_configs)
        self.assertTrue(
            self.system_id_2 not in self.test_manager.config_process_dict)

        self.assertEqual(6, mock_ack.call_count)

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_configs_removes_deleted_configs_from_state_correctly(
            self, join_mock, terminate_mock, mock_ack,
            mock_process_send_mon_data) -> None:
        # In this test we will check that removed configurations are actually
        # removed from the state
        join_mock.return_value = None
        terminate_mock.return_value = None
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        new_configs_chain_sys = {}
        new_configs_chain_nodes = {}
        new_configs_general = {}

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_chain_sys = json.dumps(new_configs_chain_sys)
        body_chain_nodes = json.dumps(new_configs_chain_nodes)
        body_general = json.dumps(new_configs_general)
        properties = pika.spec.BasicProperties()
        expected_output = copy.deepcopy(self.systems_configs_example)

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_chain_nodes)
        expected_output[self.chain_1] = {}
        self.assertEqual(expected_output, self.test_manager.systems_configs)
        self.assertTrue(
            self.system_id_1 not in self.test_manager.config_process_dict)

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties, body_chain_sys)
        expected_output[self.chain_4] = {}
        self.assertEqual(expected_output, self.test_manager.systems_configs)
        self.assertTrue(
            self.system_id_4 not in self.test_manager.config_process_dict)

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties, body_general)
        expected_output[self.chain_2] = {}
        self.assertEqual(expected_output, self.test_manager.systems_configs)
        self.assertTrue(
            self.system_id_2 not in self.test_manager.config_process_dict)
        self.assertEqual(3, mock_ack.call_count)

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    def test_proc_configs_starts_new_monitors_for_new_configs_to_be_monitored(
            self, startup_mock, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if
        # `monitor_system = True`. Implicitly we will be also testing that if
        # `monitor_system = False` no new monitor is created.
        startup_mock.return_value = None
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._systems_configs = self.systems_configs_example
        new_configs_chain_nodes = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parent_id': self.parent_id_1,
                'name': self.system_name_1,
                'exporter_url': self.node_exporter_url_1,
                'monitor_system': str(self.monitor_system_1),
            },
            self.system_id_3: {
                'id': self.system_id_3,
                'parent_id': self.parent_id_3,
                'name': self.system_name_3,
                'exporter_url': self.node_exporter_url_3,
                'monitor_system': str(self.monitor_system_3),
            },
            'config_id5': {
                'id': 'config_id5',
                'parent_id': self.parent_id_1,
                'name': 'system_5',
                'exporter_url': 'url_5',
                'monitor_system': "False",
            }
        }
        new_configs_chain_sys = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parent_id': self.parent_id_4,
                'name': self.system_name_4,
                'exporter_url': self.node_exporter_url_4,
                'monitor_system': str(self.monitor_system_4),
            },
            'config_id6': {
                'id': 'config_id6',
                'parent_id': self.parent_id_4,
                'name': 'system_6',
                'exporter_url': 'url_6',
                'monitor_system': "True",
            },
            'config_id7': {
                'id': 'config_id7',
                'parent_id': self.parent_id_4,
                'name': 'system_7',
                'exporter_url': 'url_7',
                'monitor_system': "False",
            }
        }
        new_configs_general = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parent_id': self.parent_id_2,
                'name': self.system_name_2,
                'exporter_url': self.node_exporter_url_2,
                'monitor_system': str(self.monitor_system_2),
            },
            'config_id8': {
                'id': 'config_id8',
                'parent_id': self.parent_id_2,
                'name': 'system_8',
                'exporter_url': 'url_8',
                'monitor_system': "True",
            },
            'config_id9': {
                'id': 'config_id9',
                'parent_id': self.parent_id_2,
                'name': 'system_9',
                'exporter_url': 'url_9',
                'monitor_system': "False",
            }
        }
        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_new_configs_chain_sys = json.dumps(new_configs_chain_sys)
        body_new_configs_chain_nodes = json.dumps(new_configs_chain_nodes)
        body_new_configs_general = json.dumps(new_configs_general)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_new_configs_chain_nodes)
        startup_mock.assert_called_once_with(self.system_config_3,
                                             self.system_id_3,
                                             self.chain_3,
                                             self.base_chain_3,
                                             self.sub_chain_3)

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_sys, properties,
                                           body_new_configs_chain_sys)
        new_sys_config = SystemConfig('config_id6', self.parent_id_4,
                                      'system_6', True, 'url_6')
        self.assertEqual(2, startup_mock.call_count)
        args, _ = startup_mock.call_args
        self.assertEqual(new_sys_config, args[0])
        self.assertEqual('config_id6', args[1])
        self.assertEqual(self.chain_4, args[2])

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties,
                                           body_new_configs_general)
        new_sys_config = SystemConfig('config_id8', self.parent_id_2,
                                      'system_8', True, 'url_8')
        self.assertEqual(3, startup_mock.call_count)
        args, _ = startup_mock.call_args
        self.assertEqual(new_sys_config, args[0])
        self.assertEqual('config_id8', args[1])
        self.assertEqual(self.chain_2, args[2])

        self.assertEqual(3, mock_ack.call_count)

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_confs_term_and_starts_monitors_for_modified_confs_to_be_mon(
            self, mock_ack, mock_startup, mock_start, mock_terminate,
            mock_join, mock_process_send_mon_data) -> None:
        # In this test we will check that modified configurations with
        # `monitor_system = True` will have new monitors started. Implicitly
        # we will be checking that modified configs with
        # `monitor_system = False` will only have their previous processes
        # terminated.
        mock_ack.return_value = None
        mock_startup.return_value = None
        mock_start.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        new_configs_chain_nodes_monitor_true = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parent_id': self.parent_id_1,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_1,
                'monitor_system': str(self.monitor_system_1),
            },
        }
        new_configs_chain_nodes_monitor_false = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parent_id': self.parent_id_1,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_1,
                'monitor_system': "False",
            },
        }
        new_configs_chain_sys_monitor_true = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parent_id': self.parent_id_4,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_4,
                'monitor_system': str(self.monitor_system_4),
            },
        }
        new_configs_chain_sys_monitor_false = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parent_id': self.parent_id_4,
                'name': 'new_system_name_chain',
                'exporter_url': self.node_exporter_url_4,
                'monitor_system': "False",
            },
        }
        new_configs_general_monitor_true = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parent_id': self.parent_id_2,
                'name': 'new_system_name_general',
                'exporter_url': self.node_exporter_url_2,
                'monitor_system': str(self.monitor_system_2),
            },
        }
        new_configs_general_monitor_false = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parent_id': self.parent_id_2,
                'name': 'new_system_name_general',
                'exporter_url': self.node_exporter_url_2,
                'monitor_system': "False",
            },
        }
        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_chain_nodes_mon_true = json.dumps(
            new_configs_chain_nodes_monitor_true)
        body_chain_sys_mon_true = json.dumps(
            new_configs_chain_sys_monitor_true)
        body_general_mon_true = json.dumps(new_configs_general_monitor_true)
        body_chain_nodes_mon_false = json.dumps(
            new_configs_chain_nodes_monitor_false)
        body_chain_sys_mon_false = json.dumps(
            new_configs_chain_sys_monitor_false)
        body_general_mon_false = json.dumps(new_configs_general_monitor_false)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_chain_nodes_mon_true)
        self.system_config_1.set_system_name('new_system_name_chain')
        mock_startup.assert_called_once_with(self.system_config_1,
                                             self.system_id_1,
                                             self.chain_1,
                                             self.base_chain_1,
                                             self.sub_chain_1)
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties, body_chain_sys_mon_true)
        args, _ = mock_startup.call_args
        self.system_config_4.set_system_name('new_system_name_chain')
        self.assertEqual(self.system_config_4, args[0])
        self.assertEqual(self.system_id_4, args[1])
        self.assertEqual(self.chain_4, args[2])
        self.assertEqual(2, mock_terminate.call_count)
        self.assertEqual(2, mock_join.call_count)

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties, body_general_mon_true)
        args, _ = mock_startup.call_args
        self.system_config_2.set_system_name('new_system_name_general')
        self.assertEqual(self.system_config_2, args[0])
        self.assertEqual(self.system_id_2, args[1])
        self.assertEqual(self.chain_2, args[2])
        self.assertEqual(3, mock_terminate.call_count)
        self.assertEqual(3, mock_join.call_count)

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_chain_nodes_mon_false)
        self.assertEqual(3, mock_startup.call_count)
        self.assertEqual(4, mock_terminate.call_count)
        self.assertEqual(4, mock_join.call_count)

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties, body_chain_sys_mon_false)
        self.assertEqual(3, mock_startup.call_count)
        self.assertEqual(5, mock_terminate.call_count)
        self.assertEqual(5, mock_join.call_count)

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties, body_general_mon_false)
        self.assertEqual(3, mock_startup.call_count)
        self.assertEqual(6, mock_terminate.call_count)
        self.assertEqual(6, mock_join.call_count)
        self.assertEqual(6, mock_ack.call_count)

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    def test_process_configs_terminates_monitors_for_removed_configs(
            self, mock_startup, mock_start, mock_join, mock_terminate,
            mock_ack, mock_process_send_mon_data) -> None:
        # In this test we will check that the monitors associated with removed
        # configurations are terminated.
        mock_startup.return_value = None
        mock_start.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        new_configs_chain_sys = {}
        new_configs_chain_nodes = {}
        new_configs_general = {}

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_chain_sys = json.dumps(new_configs_chain_sys)
        body_chain_nodes = json.dumps(new_configs_chain_nodes)
        body_general = json.dumps(new_configs_general)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_chain_nodes)
        mock_start.assert_not_called()
        mock_startup.assert_not_called()
        mock_join.assert_called_once()
        mock_terminate.assert_called_once()

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties, body_chain_sys)
        mock_start.assert_not_called()
        mock_startup.assert_not_called()
        self.assertEqual(2, mock_join.call_count)
        self.assertEqual(2, mock_terminate.call_count)

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties, body_general)
        mock_start.assert_not_called()
        mock_startup.assert_not_called()
        self.assertEqual(3, mock_join.call_count)
        self.assertEqual(3, mock_terminate.call_count)

        self.assertEqual(3, mock_ack.call_count)

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_new_configs_with_missing_keys(
            self, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether the state is kept intact if new configurations
        # with missing keys are sent. Exceptions should never be raised in this
        # case, and basic_ack must be called to ignore the message.
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        new_configs_chain_nodes = {
            self.system_id_3: {
                'id': self.system_id_3,
                'parentfg_id': self.parent_id_3,
                'namfge': self.system_name_3,
                'exporfgter_url': self.node_exporter_url_3,
                'monitorfg_system': str(self.monitor_system_3),
            },
        }
        new_configs_chain_sys = {
            'config_id5': {
                'id': 'config_id5',
                'parentfg_id': self.parent_id_4,
                'namfge': 'system_5',
                'exporfgter_url': 'url5',
                'monitorfg_system': "True",
            },
        }
        new_configs_general = {
            'config_id6': {
                'id': 'config_id6',
                'parentfg_id': self.parent_id_2,
                'namfge': 'system_6',
                'exporfgter_url': 'url6',
                'monitorfg_system': "True",
            },
        }
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_new_configs_chain_nodes = json.dumps(new_configs_chain_nodes)
        body_new_configs_chain_sys = json.dumps(new_configs_chain_sys)
        body_new_configs_general = json.dumps(new_configs_general)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties,
                                           body_new_configs_general)
        self.assertEqual(1, mock_ack.call_count)
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_new_configs_chain_nodes)
        self.assertEqual(2, mock_ack.call_count)
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties,
                                           body_new_configs_chain_sys)
        self.assertEqual(3, mock_ack.call_count)
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

    @mock.patch.object(SystemMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_modified_configs_with_missing_keys(
            self, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether the state is kept intact if modified
        # configurations with missing keys are sent. Exceptions should never be
        # raised in this case, and basic_ack must be called to ignore the
        # message.
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        updated_configs_chain_nodes = {
            self.system_id_1: {
                'id': self.system_id_1,
                'parentfg_id': self.parent_id_1,
                'namfge': 'new_name',
                'exporfgter_url': self.node_exporter_url_1,
                'monitorfg_system': str(self.monitor_system_1),
            },
        }
        updated_configs_chain_sys = {
            self.system_id_4: {
                'id': self.system_id_4,
                'parentfg_id': self.parent_id_4,
                'namfge': 'new_name',
                'exporfgter_url': self.node_exporter_url_4,
                'monitorfg_system': str(self.monitor_system_4),
            },
        }
        updated_configs_general = {
            self.system_id_2: {
                'id': self.system_id_2,
                'parentdfg_id': self.parent_id_2,
                'namdfge': 'new_name',
                'exporter_urdfgl': self.node_exporter_url_2,
                'monitor_systdfgem': str(self.monitor_system_2),
            },
        }
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains_nodes = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_nodes)
        method_chains_sys = pika.spec.Basic.Deliver(
            routing_key=self.chains_routing_key_sys)
        method_general = pika.spec.Basic.Deliver(
            routing_key=self.general_routing_key)
        body_updated_configs_chain_nodes = json.dumps(
            updated_configs_chain_nodes)
        body_updated_configs_chain_sys = json.dumps(
            updated_configs_chain_sys)
        body_updated_configs_general = json.dumps(updated_configs_general)
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel, method_general,
                                           properties,
                                           body_updated_configs_general)
        self.assertEqual(1, mock_ack.call_count)
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

        self.test_manager._process_configs(blocking_channel,
                                           method_chains_nodes, properties,
                                           body_updated_configs_chain_nodes)
        self.assertEqual(2, mock_ack.call_count)
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

        self.test_manager._process_configs(blocking_channel, method_chains_sys,
                                           properties,
                                           body_updated_configs_chain_sys)
        self.assertEqual(3, mock_ack.call_count)
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)
        self.assertEqual(self.systems_configs_example,
                         self.test_manager.systems_configs)

    @parameterized.expand([
        ([True, True, True], [],),
        ([True, False, True], ['self.system_id_2'],),
        ([False, False, False], ['self.system_id_1', 'self.system_id_2',
                                 'self.system_id_4'],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb(
            self, is_alive_side_effect, dead_configs, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        dead_configs_eval = list(map(eval, dead_configs))
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._systems_configs = self.systems_configs_example

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
                if config_id not in dead_configs_eval
            ],
            'dead_processes': [
                self.config_process_dict_example[config_id]['component_name']
                for config_id in self.config_process_dict_example
                if config_id in dead_configs_eval
            ],
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(expected_hb)

    @parameterized.expand([
        ([True, True, True], [],),
        ([True, False, True], ['self.system_id_2'],),
        ([False, False, False], ['self.system_id_1', 'self.system_id_2',
                                 'self.system_id_4'],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes_correctly(
            self, is_alive_side_effect, dead_configs, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        dead_configs_eval = list(map(eval, dead_configs))
        system_ids_configs_dict = {
            self.system_id_1: self.system_config_1,
            self.system_id_2: self.system_config_2,
            self.system_id_3: self.system_config_3,
            self.system_id_4: self.system_config_4
        }

        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._systems_configs = self.systems_configs_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        expected_calls = [
            call(system_ids_configs_dict[config_id], config_id,
                 self.config_process_dict_example[config_id]['chain'],
                 self.config_process_dict_example[config_id]['base_chain'],
                 self.config_process_dict_example[config_id]['sub_chain'])
            for config_id in self.config_process_dict_example
            if config_id in dead_configs_eval
        ]
        actual_calls = mock_create_and_start.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
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
        (pika.exceptions.AMQPConnectionError,
         pika.exceptions.AMQPConnectionError('test'),),
        (pika.exceptions.AMQPChannelError,
         pika.exceptions.AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
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
