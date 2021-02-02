import copy
import json
import logging
import multiprocessing
import unittest
import time
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time

from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.system import SystemMonitorsManager, \
    SYS_MON_MAN_INPUT_QUEUE, SYS_MON_MAN_INPUT_ROUTING_KEY, \
    SYS_MON_MAN_ROUTING_KEY_CHAINS, SYS_MON_MAN_ROUTING_KEY_GEN
from src.monitors.starters import start_system_monitor
from src.utils import env
from src.utils.constants import HEALTH_CHECK_EXCHANGE, \
    CONFIG_EXCHANGE, SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME, \
    SYSTEM_MONITOR_NAME_TEMPLATE
from src.utils.exceptions import PANICException
from src.utils.types import str_to_bool
from test.test_utils import infinite_fn


class TestSystemMonitorsManager(unittest.TestCase):
    def setUp(self) -> None:
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
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = Process(target=infinite_fn, args=())
        self.dummy_process3.daemon = True
        self.config_process_dict_example = {
            'config_id1': {
                'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                    'system_1'),
                'process': self.dummy_process1,
                'chain': 'Substrate Polkadot'
            },
            'config_id2': {
                'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                    'system_2'),
                'process': self.dummy_process2,
                'chain': 'general'
            },
        }
        self.systems_configs_example = {
            'Substrate Polkadot': {
                'config_id1': {
                    'id': 'config_id1',
                    'parent_id': 'chain_1',
                    'name': 'system_1',
                    'exporter_url': 'dummy_url1',
                    'monitor_system': "True",
                }
            },
            'general': {
                'config_id2': {
                    'id': 'config_id2',
                    'parent_id': 'GENERAL',
                    'name': 'system_2',
                    'exporter_url': 'dummy_url2',
                    'monitor_system': "True",
                }
            },
        }
        self.sent_configs_example_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'system_1',
                'exporter_url': 'dummy_url1',
                'monitor_system': "True",
            }
        }
        self.sent_configs_example_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'system_2',
                'exporter_url': 'dummy_url2',
                'monitor_system': "True",
            }
        }
        self.system_id_new = 'config_id3'
        self.parent_id_new = 'chain_1'
        self.system_name_new = 'system_3'
        self.monitor_system_new = True
        self.node_exporter_url_new = 'dummy_url3'
        self.chain_example_new = 'Substrate Polkadot'
        self.system_config_example = SystemConfig(self.system_id_new,
                                                  self.parent_id_new,
                                                  self.system_name_new,
                                                  self.monitor_system_new,
                                                  self.node_exporter_url_new)
        self.test_manager = SystemMonitorsManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)
        self.chains_routing_key = 'chains.Substrate.Polkadot.nodes_config'
        self.general_routing_key = SYS_MON_MAN_ROUTING_KEY_GEN
        self.test_exception = PANICException('test_exception', 1)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.rabbitmq = None
        self.test_manager = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None
        self.config_process_dict_example = None
        self.systems_configs_example = None
        self.system_config_example = None
        self.test_manager = None
        self.test_exception = None

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
            # sending messages with the same routing keys as for the queues. We
            # will also check if the size of the queues is 0 to confirm that
            # basic_consume was called (it will store the msg in the component
            # memory immediately). If one of the exchanges or queues is not
            # created, then either an exception will be thrown or the queue size
            # would be 1. Note when deleting the exchanges in the beginning we
            # also released every binding, hence there are no other queue binded
            # with the same routing key to any exchange at this point.
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

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
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

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, 'Process')
    def test_create_and_start_monitor_process_stores_the_correct_process_info(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process3
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        expected_output = {
            'config_id1': {
                'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                    'system_1'),
                'process': self.dummy_process1,
                'chain': 'Substrate Polkadot'
            },
            'config_id2': {
                'component_name': SYSTEM_MONITOR_NAME_TEMPLATE.format(
                    'system_2'),
                'process': self.dummy_process2,
                'chain': 'general'
            },
            self.system_id_new: {}
        }
        new_entry = expected_output[self.system_id_new]
        new_entry['component_name'] = SYSTEM_MONITOR_NAME_TEMPLATE.format(
            self.system_name_new)
        new_entry['chain'] = self.chain_example_new
        new_entry['process'] = self.dummy_process3

        self.test_manager._create_and_start_monitor_process(
            self.system_config_example, self.system_id_new,
            self.chain_example_new)

        self.assertEqual(expected_output, self.test_manager.config_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_monitor_process_creates_the_correct_process(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._create_and_start_monitor_process(
            self.system_config_example, self.system_id_new,
            self.chain_example_new)

        new_entry = self.test_manager.config_process_dict[self.system_id_new]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(1, len(new_entry_process._args))
        self.assertEqual(self.system_config_example, new_entry_process._args[0])
        self.assertEqual(start_system_monitor, new_entry_process._target)

    @mock.patch("src.monitors.starters.create_logger")
    def test_create_and_start_monitor_process_starts_the_process(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger
        self.test_manager._create_and_start_monitor_process(
            self.system_config_example, self.system_id_new,
            self.chain_example_new)

        # We need to sleep to give some time for the monitor to be initialized,
        # otherwise the process would not terminate
        time.sleep(1)

        new_entry = self.test_manager.config_process_dict[self.system_id_new]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.is_alive())

        new_entry_process.terminate()
        new_entry_process.join()

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_default_key(self, mock_ack) -> None:
        # This test will pass if the stored systems config does not change.
        # This would mean that the DEFAULT key was ignored, otherwise, it would
        # have been included as a new config.
        mock_ack.return_value = None
        old_systems_configs = copy.deepcopy(self.systems_configs_example)
        self.test_manager._systems_configs = self.systems_configs_example

        # We will pass the acceptable schema as a value to make sure that the
        # default key will never be added. By passing the schema we will also
        # prevent processing errors from happening.
        self.sent_configs_example_chain['DEFAULT'] = {
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

        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain = json.dumps(self.sent_configs_example_chain)
            body_general = json.dumps(self.sent_configs_example_general)
            properties = pika.spec.BasicProperties()

            # We will send the message twice with both general and chain
            # routing keys to make sure that the DEFAULT key is ignored in both
            # cases
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general)
            self.assertEqual(old_systems_configs,
                             self.test_manager.systems_configs)
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain)
            self.assertEqual(old_systems_configs,
                             self.test_manager.systems_configs)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    def test_process_configs_stores_new_configs_to_be_monitored_correctly(
            self, startup_mock, mock_ack) -> None:
        # We will check whether new configs are added to the state. Since some
        # new configs have `monitor_system = False` we are also testing that
        # new configs are ignored if they should not be monitored.

        mock_ack.return_value = None
        startup_mock.return_value = None
        new_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'system_1',
                'exporter_url': 'dummy_url1',
                'monitor_system': "True",
            },
            'config_id3': {
                'id': 'config_id3',
                'parent_id': 'chain_1',
                'name': 'system_3',
                'exporter_url': 'dummy_url3',
                'monitor_system': "True",
            },
            'config_id4': {
                'id': 'config_id4',
                'parent_id': 'chain_1',
                'name': 'system_4',
                'exporter_url': 'dummy_url4',
                'monitor_system': "False",
            }
        }
        new_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'system_2',
                'exporter_url': 'dummy_url2',
                'monitor_system': "True",
            },
            'config_id5': {
                'id': 'config_id5',
                'parent_id': 'GENERAL',
                'name': 'system_5',
                'exporter_url': 'dummy_url5',
                'monitor_system': "True",
            },
            'config_id6': {
                'id': 'config_id6',
                'parent_id': 'GENERAL',
                'name': 'system_6',
                'exporter_url': 'dummy_url6',
                'monitor_system': "False",
            }
        }
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(
                self.sent_configs_example_chain)
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
            body_new_configs_chain = json.dumps(new_configs_chain)
            body_new_configs_general = json.dumps(new_configs_general)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)
            expected_output = copy.deepcopy(self.systems_configs_example)
            self.assertEqual(expected_output, self.test_manager.systems_configs)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)
            expected_output['Substrate Polkadot']['config_id3'] = \
                new_configs_chain['config_id3']
            expected_output['general']['config_id5'] = \
                new_configs_general['config_id5']
            self.assertEqual(expected_output, self.test_manager.systems_configs)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_configs_stores_modified_configs_to_be_monitored_correctly(
            self, join_mock, terminate_mock, startup_mock, mock_ack) -> None:
        # In this test we will check that modified configurations with
        # `monitor_system = True` are stored correctly in the state. Some
        # configurations will have `monitor_system = False` to check whether the
        # monitor associated with the previous configuration is terminated.

        mock_ack.return_value = None
        startup_mock.return_value = None
        join_mock.return_value = None
        terminate_mock.return_value = None
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        new_configs_chain_monitor_true = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'new_system_name_chain',
                'exporter_url': 'dummy_url1',
                'monitor_system': "True",
            },
        }
        new_configs_chain_monitor_false = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'new_system_name_chain',
                'exporter_url': 'dummy_url1',
                'monitor_system': "False",
            },
        }
        new_configs_general_monitor_true = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'new_system_name_general',
                'exporter_url': 'dummy_url2',
                'monitor_system': "True",
            },
        }
        new_configs_general_monitor_false = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'new_system_name_general',
                'exporter_url': 'dummy_url2',
                'monitor_system': "false",
            },
        }
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_mon_true = json.dumps(new_configs_chain_monitor_true)
            body_general_mon_true = json.dumps(new_configs_general_monitor_true)
            body_chain_mon_false = json.dumps(new_configs_chain_monitor_false)
            body_general_mon_false = json.dumps(
                new_configs_general_monitor_false)
            properties = pika.spec.BasicProperties()
            expected_output = copy.deepcopy(self.systems_configs_example)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_mon_true)
            expected_output['Substrate Polkadot']['config_id1'] = \
                new_configs_chain_monitor_true['config_id1']
            self.assertEqual(expected_output, self.test_manager.systems_configs)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_general_mon_true)
            expected_output['general']['config_id2'] = \
                new_configs_general_monitor_true['config_id2']
            self.assertEqual(expected_output, self.test_manager.systems_configs)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_chain_mon_false)
            expected_output['Substrate Polkadot'] = {}
            self.assertEqual(expected_output, self.test_manager.systems_configs)
            self.assertTrue(
                'config_id1' not in self.test_manager.config_process_dict)

            self.test_manager._process_configs(
                blocking_channel, method_general, properties,
                body_general_mon_false)
            expected_output['general'] = {}
            self.assertEqual(expected_output, self.test_manager.systems_configs)
            self.assertTrue(
                'config_id2' not in self.test_manager.config_process_dict)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_configs_removes_deleted_configs_from_state_correctly(
            self, join_mock, terminate_mock, mock_ack) -> None:
        # In this test we will check that removed configurations are actually
        # removed from the state

        mock_ack.return_value = None
        join_mock.return_value = None
        terminate_mock.return_value = None
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        new_configs_chain = {}
        new_configs_general = {}
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain = json.dumps(new_configs_chain)
            body_general = json.dumps(new_configs_general)
            properties = pika.spec.BasicProperties()
            expected_output = copy.deepcopy(self.systems_configs_example)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain)
            expected_output['Substrate Polkadot'] = {}
            self.assertEqual(expected_output, self.test_manager.systems_configs)
            self.assertTrue(
                'config_id1' not in self.test_manager.config_process_dict)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general)
            expected_output['general'] = {}
            self.assertEqual(expected_output, self.test_manager.systems_configs)
            self.assertTrue(
                'config_id2' not in self.test_manager.config_process_dict)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    def test_proc_configs_starts_new_monitors_for_new_configs_to_be_monitored(
            self, startup_mock, mock_ack) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if
        # `monitor_system = True`. Implicitly we will be also testing that if
        # `monitor_system = False` no new monitor is created.

        mock_ack.return_value = None
        startup_mock.return_value = None
        new_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'system_1',
                'exporter_url': 'dummy_url1',
                'monitor_system': "True",
            },
            'config_id3': {
                'id': 'config_id3',
                'parent_id': 'chain_1',
                'name': 'system_3',
                'exporter_url': 'dummy_url3',
                'monitor_system': "True",
            },
            'config_id4': {
                'id': 'config_id4',
                'parent_id': 'chain_1',
                'name': 'system_4',
                'exporter_url': 'dummy_url4',
                'monitor_system': "False",
            }
        }
        new_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'system_2',
                'exporter_url': 'dummy_url2',
                'monitor_system': "True",
            },
            'config_id5': {
                'id': 'config_id5',
                'parent_id': 'GENERAL',
                'name': 'system_5',
                'exporter_url': 'dummy_url5',
                'monitor_system': "True",
            },
            'config_id6': {
                'id': 'config_id6',
                'parent_id': 'GENERAL',
                'name': 'system_6',
                'exporter_url': 'dummy_url6',
                'monitor_system': "False",
            }
        }
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(
                self.sent_configs_example_chain)
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
            body_new_configs_chain = json.dumps(new_configs_chain)
            body_new_configs_general = json.dumps(new_configs_general)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.assertEqual(1, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id1' and 'Substrate Polkadot' in args)
            self.assertEqual(
                self.sent_configs_example_chain['config_id1']['id'],
                args[0].system_id)
            self.assertEqual(
                self.sent_configs_example_chain['config_id1']['parent_id'],
                args[0].parent_id)
            self.assertEqual(
                self.sent_configs_example_chain['config_id1']['name'],
                args[0].system_name)
            self.assertEqual(
                str_to_bool(
                    self.sent_configs_example_chain['config_id1']
                    ['monitor_system']), args[0].monitor_system)
            self.assertEqual(
                self.sent_configs_example_chain['config_id1']['exporter_url'],
                args[0].node_exporter_url)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.assertEqual(2, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id3' and 'Substrate Polkadot' in args)
            self.assertEqual(new_configs_chain['config_id3']['id'],
                             args[0].system_id)
            self.assertEqual(new_configs_chain['config_id3']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(new_configs_chain['config_id3']['name'],
                             args[0].system_name)
            self.assertEqual(
                str_to_bool(new_configs_chain['config_id3']['monitor_system']),
                args[0].monitor_system)
            self.assertEqual(new_configs_chain['config_id3']['exporter_url'],
                             args[0].node_exporter_url)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)
            self.assertEqual(3, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id2' and 'general' in args)
            self.assertEqual(
                self.sent_configs_example_general['config_id2']['id'],
                args[0].system_id)
            self.assertEqual(
                self.sent_configs_example_general['config_id2']['parent_id'],
                args[0].parent_id)
            self.assertEqual(
                self.sent_configs_example_general['config_id2']['name'],
                args[0].system_name)
            self.assertEqual(
                str_to_bool(
                    self.sent_configs_example_general['config_id2']
                    ['monitor_system']), args[0].monitor_system)
            self.assertEqual(
                self.sent_configs_example_general['config_id2']['exporter_url'],
                args[0].node_exporter_url)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)
            self.assertEqual(4, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id5' and 'general' in args)
            self.assertEqual(new_configs_general['config_id5']['id'],
                             args[0].system_id)
            self.assertEqual(new_configs_general['config_id5']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(new_configs_general['config_id5']['name'],
                             args[0].system_name)
            self.assertEqual(
                str_to_bool(
                    new_configs_general['config_id5']['monitor_system']),
                args[0].monitor_system)
            self.assertEqual(new_configs_general['config_id5']['exporter_url'],
                             args[0].node_exporter_url)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_confs_term_and_starts_monitors_for_modified_confs_to_be_mon(
            self, mock_ack, mock_create_logger) -> None:
        # In this test we will check that modified configurations with
        # `monitor_system = True` will have new monitors started. Implicitly
        # we will be checking that modified configs with
        # `monitor_system = False` will only have their previous processes
        # terminated.

        mock_ack.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        new_configs_chain_monitor_true = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'new_system_name_chain',
                'exporter_url': 'dummy_url1',
                'monitor_system': "True",
            },
        }
        new_configs_chain_monitor_false = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'new_system_name_chain',
                'exporter_url': 'dummy_url1',
                'monitor_system': "False",
            },
        }
        new_configs_general_monitor_true = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'new_system_name_general',
                'exporter_url': 'dummy_url2',
                'monitor_system': "True",
            },
        }
        new_configs_general_monitor_false = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'new_system_name_general',
                'exporter_url': 'dummy_url2',
                'monitor_system': "false",
            },
        }
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(self.sent_configs_example_chain)
            body_general_initial = json.dumps(self.sent_configs_example_general)
            body_chain_mon_true = json.dumps(new_configs_chain_monitor_true)
            body_general_mon_true = json.dumps(new_configs_general_monitor_true)
            body_chain_mon_false = json.dumps(new_configs_chain_monitor_false)
            body_general_mon_false = json.dumps(
                new_configs_general_monitor_false)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Assure that the processes have been started
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id1']['process'].is_alive())
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id2']['process'].is_alive())

            # Give some time till the process starts
            time.sleep(1)

            # Send the updated configs with `monitor_system = True`
            conf_id1_old_proc = self.test_manager.config_process_dict[
                'config_id1']['process']
            conf_id2_old_proc = self.test_manager.config_process_dict[
                'config_id2']['process']
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_mon_true)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_general_mon_true)

            # Give some time till the process re-starts
            time.sleep(1)

            # Check that the old process has terminated and a new one has
            # started.
            self.assertFalse(conf_id1_old_proc.is_alive())
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id1']['process'].is_alive())
            self.assertFalse(conf_id2_old_proc.is_alive())
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id2']['process'].is_alive())

            # Send the updated configs with `monitor_system = False`
            conf_id1_old_proc = self.test_manager.config_process_dict[
                'config_id1']['process']
            conf_id2_old_proc = self.test_manager.config_process_dict[
                'config_id2']['process']
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_mon_false)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_general_mon_false)

            # Give some time till the process stops
            time.sleep(1)

            # Check that the old process has terminated and that new ones have
            # not been started. If _create_start_process is called then the
            # config ids would be in config_process_dict
            self.assertFalse(conf_id1_old_proc.is_alive())
            self.assertFalse(
                'config_id1' in self.test_manager.config_process_dict)
            self.assertFalse(conf_id2_old_proc.is_alive())
            self.assertFalse(
                'config_id2' in self.test_manager.config_process_dict)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    def test_process_confs_restarts_an_updated_monitor_with_the_correct_conf(
            self, mock_terminate, mock_join, startup_mock, mock_ack) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on an updated configuration.
        mock_ack.return_value = None
        startup_mock.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        updated_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'name': 'changed_system_name_chain',
                'exporter_url': 'dummy_url1',
                'monitor_system': "True",
            },
        }
        updated_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'name': 'changed_system_name_gen',
                'exporter_url': 'dummy_url2',
                'monitor_system': "True",
            },
        }
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_updated_configs_chain = json.dumps(updated_configs_chain)
            body_updated_configs_general = json.dumps(updated_configs_general)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_updated_configs_chain)
            self.assertEqual(1, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id1' and 'Substrate Polkadot' in args)
            self.assertEqual(updated_configs_chain['config_id1']['id'],
                             args[0].system_id)
            self.assertEqual(updated_configs_chain['config_id1']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(updated_configs_chain['config_id1']['name'],
                             args[0].system_name)
            self.assertEqual(
                str_to_bool(
                    updated_configs_chain['config_id1']['monitor_system']),
                args[0].monitor_system)
            self.assertEqual(
                updated_configs_chain['config_id1']['exporter_url'],
                args[0].node_exporter_url)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_updated_configs_general)
            self.assertEqual(2, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id2' and 'general' in args)
            self.assertEqual(updated_configs_general['config_id2']['id'],
                             args[0].system_id)
            self.assertEqual(updated_configs_general['config_id2']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(updated_configs_general['config_id2']['name'],
                             args[0].system_name)
            self.assertEqual(
                str_to_bool(
                    updated_configs_general['config_id2']['monitor_system']),
                args[0].monitor_system)
            self.assertEqual(
                updated_configs_general['config_id2']['exporter_url'],
                args[0].node_exporter_url)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_terminates_monitors_for_removed_configs(
            self, mock_ack, mock_create_logger) -> None:
        # In this test we will check that when a config is removed, it's monitor
        # is terminated by _process_configs.
        mock_ack.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(self.sent_configs_example_chain)
            body_general_initial = json.dumps(self.sent_configs_example_general)
            body_chain_new = json.dumps({})
            body_general_new = json.dumps({})
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the monitors to start
            time.sleep(1)

            # Assure that the processes have been started
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id1']['process'].is_alive())
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id2']['process'].is_alive())

            # Send the updated configs
            conf_id1_old_proc = self.test_manager.config_process_dict[
                'config_id1']['process']
            conf_id2_old_proc = self.test_manager.config_process_dict[
                'config_id2']['process']
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_new)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_new)

            # Give time for the monitors to stop
            time.sleep(1)

            # Check that the old process has terminated
            self.assertFalse(conf_id1_old_proc.is_alive())
            self.assertFalse(conf_id2_old_proc.is_alive())

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_new_configs_with_missing_keys(
            self, mock_ack) -> None:
        # We will check whether the state is kept intact if new configurations
        # with missing keys are sent. Exceptions should never be raised in this
        # case, and basic_ack must be called to ignore the message.
        mock_ack.return_value = None
        new_configs_chain = {
            'config_id3': {
                'id': 'config_id3',
                'parentfg_id': 'chain_1',
                'namfge': 'system_3',
                'exporfgter_url': 'dummy_url3',
                'monitorfg_system': "True",
            },
        }
        new_configs_general = {
            'config_id5': {
                'id': 'config_id5',
                'parentdfg_id': 'GENERAL',
                'namdfge': 'system_5',
                'exporter_urdfgl': 'dummy_url5',
                'monitor_systdfgem': "True",
            },
        }
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_new_configs_chain = json.dumps(new_configs_chain)
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

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.assertEqual(2, mock_ack.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.config_process_dict)
            self.assertEqual(self.systems_configs_example,
                             self.test_manager.systems_configs)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_modified_configs_with_missing_keys(
            self, mock_ack) -> None:
        # We will check whether the state is kept intact if modified
        # configurations with missing keys are sent. Exceptions should never be
        # raised in this case, and basic_ack must be called to ignore the
        # message.
        mock_ack.return_value = None
        updated_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parentfg_id': 'chain_1',
                'namfge': 'system_1',
                'exporfgter_url': 'dummy_url1',
                'monitorfg_system': "True",
            },
        }
        updated_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parentdfg_id': 'GENERAL',
                'namdfge': 'system_2',
                'exporter_urdfgl': 'dummy_url2',
                'monitor_systdfgem': "True",
            },
        }
        self.test_manager._systems_configs = self.systems_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_updated_configs_chain = json.dumps(updated_configs_chain)
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

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_updated_configs_chain)
            self.assertEqual(2, mock_ack.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.config_process_dict)
            self.assertEqual(self.systems_configs_example,
                             self.test_manager.systems_configs)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_all_processes_are_alive(
            self, mock_ack, mock_create_logger) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(self.sent_configs_example_chain)
            body_general_initial = json.dumps(self.sent_configs_example_general)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the processes to start
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # Initialize
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is a valid HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            expected_output = {
                'component_name': self.test_manager.name,
                'running_processes':
                    [self.test_manager.config_process_dict['config_id1'][
                         'component_name'],
                     self.test_manager.config_process_dict['config_id2'][
                         'component_name']],
                'dead_processes': [],
                'timestamp': datetime(2012, 1, 1).timestamp(),
            }
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.config_process_dict['config_id1'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id2'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id1'][
                'process'].join()
            self.test_manager.config_process_dict['config_id2'][
                'process'].join()
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_some_processes_alive_some_dead(
            self, mock_ack, mock_create_logger) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(self.sent_configs_example_chain)
            body_general_initial = json.dumps(self.sent_configs_example_general)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the processes to start
            time.sleep(1)

            self.test_manager.config_process_dict['config_id1'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id1'][
                'process'].join()

            # Give time for the process to stop
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # Initialize
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is a valid HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            expected_output = {
                'component_name': self.test_manager.name,
                'running_processes':
                    [self.test_manager.config_process_dict['config_id2'][
                         'component_name']],
                'dead_processes':
                    [self.test_manager.config_process_dict['config_id1'][
                         'component_name']],
                'timestamp': datetime(2012, 1, 1).timestamp(),
            }
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.config_process_dict['config_id2'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id2'][
                'process'].join()
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_all_processes_dead(
            self, mock_ack, mock_create_logger) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(self.sent_configs_example_chain)
            body_general_initial = json.dumps(self.sent_configs_example_general)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the processes to start
            time.sleep(1)

            self.test_manager.config_process_dict['config_id1'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id1'][
                'process'].join()
            self.test_manager.config_process_dict['config_id2'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id2'][
                'process'].join()

            # Give time for the process to stop
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # Initialize
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, res.method.message_count)

            # Check that the message received is a valid HB
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            expected_output = {
                'component_name': self.test_manager.name,
                'running_processes': [],
                'dead_processes':
                    [self.test_manager.config_process_dict['config_id1'][
                         'component_name'],
                     self.test_manager.config_process_dict['config_id2'][
                         'component_name']],
                'timestamp': datetime(2012, 1, 1).timestamp(),
            }
            self.assertEqual(expected_output, json.loads(body))

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

    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes(
            self, send_hb_mock, mock_create_logger, mock_ack) -> None:
        send_hb_mock.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        try:
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(self.sent_configs_example_chain)
            body_general_initial = json.dumps(self.sent_configs_example_general)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the processes to start
            time.sleep(1)

            # Automate the case when having all processes dead
            self.test_manager.config_process_dict['config_id1'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id1'][
                'process'].join()
            self.test_manager.config_process_dict['config_id2'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id2'][
                'process'].join()

            # Give time for the processes to terminate
            time.sleep(1)

            # Check that that the processes have terminated
            self.assertFalse(self.test_manager.config_process_dict[
                                 'config_id1']['process'].is_alive())
            self.assertFalse(self.test_manager.config_process_dict[
                                 'config_id2']['process'].is_alive())

            # Initialize
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # Give time for the processes to start
            time.sleep(1)

            self.assertTrue(self.test_manager.config_process_dict['config_id1'][
                                'process'].is_alive())
            self.assertTrue(self.test_manager.config_process_dict['config_id2'][
                                'process'].is_alive())

            # Clean before test finishes
            self.test_manager.config_process_dict['config_id1'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id1'][
                'process'].join()
            self.test_manager.config_process_dict['config_id2'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id2'][
                'process'].join()
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    @mock.patch.object(SystemMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    def test_process_ping_restarts_dead_processes_with_correct_info(
            self, mock_alive, mock_join, startup_mock, send_hb_mock) -> None:
        send_hb_mock.return_value = None
        startup_mock.return_value = None
        mock_alive.return_value = False
        mock_join.return_value = None
        try:
            self.test_manager.rabbitmq.connect()

            del self.systems_configs_example['general']
            del self.config_process_dict_example['config_id2']
            self.test_manager._systems_configs = self.systems_configs_example
            self.test_manager._config_process_dict = \
                self.config_process_dict_example

            # Initialize
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            self.assertEqual(1, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id1' and 'Substrate Polkadot' in args)
            self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
                                 'config_id1']['id'], args[0].system_id)
            self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
                                 'config_id1']['parent_id'], args[0].parent_id)
            self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
                                 'config_id1']['name'], args[0].system_name)
            self.assertEqual(
                str_to_bool(self.systems_configs_example['Substrate Polkadot'][
                                'config_id1']['monitor_system']),
                args[0].monitor_system)
            self.assertEqual(self.systems_configs_example['Substrate Polkadot'][
                                 'config_id1']['exporter_url'],
                             args[0].node_exporter_url)

            # Clean before test finishes
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(multiprocessing.Process, "is_alive")
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, is_alive_mock) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat. In this test we will
        # check that no heartbeat is sent when mocking a raised exception.
        is_alive_mock.side_effect = self.test_exception
        try:
            self.test_manager._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            self.test_manager._systems_configs = self.systems_configs_example
            self.test_manager._config_process_dict = \
                self.config_process_dict_example

            # Initialize
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key='heartbeat.manager')
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(0, res.method.message_count)

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

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialize
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_connection_err_on_connection_err(
            self, hb_mock) -> None:
        hb_mock.side_effect = pika.exceptions.AMQPConnectionError('test')
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialize
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_chan_err_on_chan_err(
            self, hb_mock) -> None:
        hb_mock.side_effect = pika.exceptions.AMQPChannelError('test')
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialize
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemMonitorsManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_exception_on_unexpected_exception(
            self, hb_mock) -> None:
        hb_mock.side_effect = self.test_exception
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialize
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(PANICException, self.test_manager._process_ping,
                              blocking_channel, method, properties, body)

            # Clean before test finishes
            self.test_manager.rabbitmq.queue_delete(SYS_MON_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            self.fail("Test failed: {}".format(e))
