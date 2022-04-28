import copy
import json
import logging
import multiprocessing
import time
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time

from src.configs.repo import GitHubRepoConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.github import GitHubMonitorsManager
from src.monitors.starters import start_github_monitor
from src.utils import env
from src.utils.constants.names import GITHUB_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    GH_MON_MAN_CONFIGS_QUEUE_NAME, GH_MON_MAN_CONFIGS_ROUTING_KEY_GEN,
    GH_MON_MAN_HEARTBEAT_QUEUE_NAME, GH_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS,
    HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY, HEALTH_CHECK_EXCHANGE,
    CONFIG_EXCHANGE, PING_ROUTING_KEY, MONITORABLE_EXCHANGE)
from src.utils.exceptions import PANICException
from src.utils.types import str_to_bool
from test.test_utils.utils import (
    infinite_fn, connect_to_rabbit, delete_queue_if_exists,
    delete_exchange_if_exists, disconnect_from_rabbit)


class TestGitHubMonitorsManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_github_monitors_manager'
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
        self.config_process_dict_example = {
            'config_id1': {
                'component_name': GITHUB_MONITOR_NAME_TEMPLATE.format('repo_1'),
                'process': self.dummy_process1,
                'chain': 'Substrate Polkadot',
                'parent_id': 'chain_id1',
                'source_name': 'source_1',
                'base_chain': 'Substrate',
                'sub_chain': 'Polkadot',
            },
            'config_id2': {
                'component_name': GITHUB_MONITOR_NAME_TEMPLATE.format('repo_2'),
                'process': self.dummy_process2,
                'chain': 'general',
                'parent_id': 'general',
                'source_name': 'source_2',
                'base_chain': 'general',
                'sub_chain': 'general',
            },
        }
        self.github_repos_configs_example = {
            'Substrate Polkadot': {
                'config_id1': {
                    'id': 'config_id1',
                    'parent_id': 'chain_1',
                    'repo_name': 'repo_1',
                    'monitor_repo': "True",
                }
            },
            'general': {
                'config_id2': {
                    'id': 'config_id2',
                    'parent_id': 'GENERAL',
                    'repo_name': 'repo_2',
                    'monitor_repo': "True",
                }
            },
        }
        self.sent_configs_example_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'repo_1',
                'monitor_repo': "True",
            }
        }
        self.sent_configs_example_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'repo_2',
                'monitor_repo': "True",
            }
        }
        self.repo_id_new = 'config_id3'
        self.parent_id_new = 'chain_1'
        self.repo_name_new = 'repo_3/'
        self.monitor_repo_new = True
        self.chain_example_new = 'Substrate Polkadot'
        self.base_chain_new = 'Substrate'
        self.sub_chain_new = 'Polkadot'
        self.releases_page_new = \
            env.GITHUB_RELEASES_TEMPLATE.format(self.repo_name_new)
        self.repo_config_example = GitHubRepoConfig(self.repo_id_new,
                                                    self.parent_id_new,
                                                    self.repo_name_new,
                                                    self.monitor_repo_new,
                                                    self.releases_page_new)
        self.test_manager = GitHubMonitorsManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)
        self.chains_routing_key = \
            'chains.Substrate.Polkadot.github_repos_config'
        self.general_routing_key = GH_MON_MAN_CONFIGS_ROUTING_KEY_GEN
        self.test_exception = PANICException('test_exception', 1)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               GH_MON_MAN_HEARTBEAT_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               GH_MON_MAN_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq, CONFIG_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  MONITORABLE_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.rabbitmq = None
        self.config_process_dict_example = None
        self.github_repos_configs_example = None
        self.repo_config_example = None
        self.test_manager = None
        self.test_exception = None

        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, str(self.test_manager))

    def test_config_process_dict_returns_config_process_dict(self) -> None:
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_github_repos_configs_returns_github_repos_configs(self) -> None:
        self.test_manager._github_repos_configs = \
            self.github_repos_configs_example
        self.assertEqual(self.github_repos_configs_example,
                         self.test_manager.github_repos_configs)

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
        # To make sure that there is no connection/channel already
        # established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        self.rabbitmq.connect()
        self.test_manager.rabbitmq.queue_delete(
            GH_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.test_manager.rabbitmq.queue_delete(
            GH_MON_MAN_CONFIGS_QUEUE_NAME)
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
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=PING_ROUTING_KEY, body=self.test_data_str,
            is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=GH_MON_MAN_CONFIGS_ROUTING_KEY_CHAINS,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=GH_MON_MAN_CONFIGS_ROUTING_KEY_GEN,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)

        # Re-declare queue to get the number of messages
        res = self.test_manager.rabbitmq.queue_declare(
            GH_MON_MAN_HEARTBEAT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            GH_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())

        res = self.test_manager.rabbitmq.queue_declare(
            GH_MON_MAN_CONFIGS_QUEUE_NAME, False, True, False, False)
        self.assertEqual(2, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            GH_MON_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual(self.test_data_str, body.decode())
        _, _, body = self.test_manager.rabbitmq.basic_get(
            GH_MON_MAN_CONFIGS_QUEUE_NAME)
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
        expected_output = self.test_manager._config_process_dict
        expected_output[self.repo_id_new] = {
            'component_name': GITHUB_MONITOR_NAME_TEMPLATE.format(
                self.repo_name_new.replace('/', ' ')[:-1]),
            'base_chain': self.base_chain_new,
            'sub_chain': self.sub_chain_new,
            'source_name': self.repo_name_new[:-1],
            'chain': self.chain_example_new,
            'parent_id': self.parent_id_new,
            'process': self.dummy_process3,
        }

        self.test_manager._create_and_start_monitor_process(
            self.repo_config_example, self.repo_id_new, self.chain_example_new,
            self.base_chain_new, self.sub_chain_new)

        self.assertEqual(
            expected_output, self.test_manager.config_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_monitor_process_creates_the_correct_process(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._create_and_start_monitor_process(
            self.repo_config_example, self.repo_id_new, self.chain_example_new,
            self.base_chain_new, self.sub_chain_new)

        new_entry = self.test_manager.config_process_dict[self.repo_id_new]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(1, len(new_entry_process._args))
        self.assertEqual(self.repo_config_example, new_entry_process._args[0])
        self.assertEqual(start_github_monitor, new_entry_process._target)

    @mock.patch("src.monitors.starters.create_logger")
    def test_create_and_start_monitor_process_starts_the_process(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger
        self.test_manager._create_and_start_monitor_process(
            self.repo_config_example, self.repo_id_new, self.chain_example_new,
            self.base_chain_new, self.sub_chain_new)

        # We need to sleep to give some time for the monitor to be initialised,
        # otherwise the process would not terminate
        time.sleep(1)

        new_entry = self.test_manager.config_process_dict[self.repo_id_new]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.is_alive())

        new_entry_process.terminate()
        new_entry_process.join()

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_default_key(
            self, mock_ack, mock_process_send_mon_data) -> None:
        # This test will pass if the stored repos config does not change.
        # This would mean that the DEFAULT key was ignored, otherwise, it would
        # have been included as a new config.
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        old_github_repos_configs = copy.deepcopy(
            self.github_repos_configs_example)
        self.test_manager._github_repos_configs = \
            self.github_repos_configs_example

        # We will pass the acceptable schema as a value to make sure that the
        # default key will never be added. By passing the schema we will also
        # prevent processing errors from happening.
        self.sent_configs_example_chain['DEFAULT'] = {
            'id': 'default_id1',
            'parent_id': 'chain_1',
            'repo_name': 'default_repo_1',
            'monitor_repo': "True",
        }
        self.sent_configs_example_general['DEFAULT'] = {
            'id': 'default_id2',
            'parent_id': 'GENERAL',
            'repo_name': 'default_repo_2',
            'monitor_repo': "True",
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
            self.assertEqual(old_github_repos_configs,
                             self.test_manager.github_repos_configs)
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain)
            self.assertEqual(old_github_repos_configs,
                             self.test_manager.github_repos_configs)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(GitHubMonitorsManager,
                       "_create_and_start_monitor_process")
    def test_process_configs_stores_new_configs_to_be_monitored_correctly(
            self, startup_mock, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether new configs are added to the state. Since some
        # new configs have `monitor_repo = False` we are also testing that
        # new configs are ignored if they should not be monitored.
        startup_mock.return_value = None
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        new_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'repo_1',
                'monitor_repo': "True",
            },
            'config_id3': {
                'id': 'config_id3',
                'parent_id': 'chain_1',
                'repo_name': 'repo_3',
                'monitor_repo': "True",
            },
            'config_id4': {
                'id': 'config_id4',
                'parent_id': 'chain_1',
                'repo_name': 'repo_4',
                'monitor_repo': "False",
            }
        }
        new_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'repo_2',
                'monitor_repo': "True",
            },
            'config_id5': {
                'id': 'config_id5',
                'parent_id': 'GENERAL',
                'repo_name': 'repo_5',
                'monitor_repo': "True",
            },
            'config_id6': {
                'id': 'config_id6',
                'parent_id': 'GENERAL',
                'repo_name': 'repo_6',
                'monitor_repo': "False",
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
            expected_output = copy.deepcopy(self.github_repos_configs_example)
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)

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
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(GitHubMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_configs_stores_modified_configs_to_be_monitored_correctly(
            self, join_mock, terminate_mock, startup_mock, mock_ack,
            mock_process_send_mon_data) -> None:
        # In this test we will check that modified configurations with
        # `monitor_repo = True` are stored correctly in the state. Some
        # configurations will have `monitor_repo = False` to check whether the
        # monitor associated with the previous configuration is terminated.
        join_mock.return_value = None
        terminate_mock.return_value = None
        startup_mock.return_value = None
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._github_repos_configs = \
            self.github_repos_configs_example
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        new_configs_chain_monitor_true = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'new_repo_name_chain',
                'monitor_repo': "True",
            },
        }
        new_configs_chain_monitor_false = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'new_repo_name_chain',
                'monitor_repo': "False",
            },
        }
        new_configs_general_monitor_true = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'new_repo_name_general',
                'monitor_repo': "True",
            },
        }
        new_configs_general_monitor_false = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'new_repo_name_general',
                'monitor_repo': "false",
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
            body_general_mon_true = json.dumps(
                new_configs_general_monitor_true)
            body_chain_mon_false = json.dumps(new_configs_chain_monitor_false)
            body_general_mon_false = json.dumps(
                new_configs_general_monitor_false)
            properties = pika.spec.BasicProperties()
            expected_output = copy.deepcopy(self.github_repos_configs_example)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_mon_true)
            expected_output['Substrate Polkadot']['config_id1'] = \
                new_configs_chain_monitor_true['config_id1']
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_general_mon_true)
            expected_output['general']['config_id2'] = \
                new_configs_general_monitor_true['config_id2']
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_chain_mon_false)
            expected_output['Substrate Polkadot'] = {}
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)
            self.assertTrue(
                'config_id1' not in self.test_manager.config_process_dict)

            self.test_manager._process_configs(
                blocking_channel, method_general, properties,
                body_general_mon_false)
            expected_output['general'] = {}
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)
            self.assertTrue(
                'config_id2' not in self.test_manager.config_process_dict)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
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
        self.test_manager._github_repos_configs = \
            self.github_repos_configs_example
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
            expected_output = copy.deepcopy(self.github_repos_configs_example)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain)
            expected_output['Substrate Polkadot'] = {}
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)
            self.assertTrue(
                'config_id1' not in self.test_manager.config_process_dict)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general)
            expected_output['general'] = {}
            self.assertEqual(
                expected_output, self.test_manager.github_repos_configs)
            self.assertTrue(
                'config_id2' not in self.test_manager.config_process_dict)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(GitHubMonitorsManager,
                       "_create_and_start_monitor_process")
    def test_proc_configs_starts_new_monitors_for_new_configs_to_be_monitored(
            self, startup_mock, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if
        # `monitor_repo = True`. Implicitly we will be also testing that if
        # `monitor_repo = False` no new monitor is created.
        mock_process_send_mon_data.return_value = None
        mock_ack.return_value = None
        startup_mock.return_value = None
        new_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'repo_1',
                'monitor_repo': "True",
            },
            'config_id3': {
                'id': 'config_id3',
                'parent_id': 'chain_1',
                'repo_name': 'repo_3',
                'monitor_repo': "True",
            },
            'config_id4': {
                'id': 'config_id4',
                'parent_id': 'chain_1',
                'repo_name': 'repo_4',
                'monitor_repo': "False",
            }
        }
        new_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'repo_2',
                'monitor_repo': "True",
            },
            'config_id5': {
                'id': 'config_id5',
                'parent_id': 'GENERAL',
                'repo_name': 'repo_5',
                'monitor_repo': "True",
            },
            'config_id6': {
                'id': 'config_id6',
                'parent_id': 'GENERAL',
                'repo_name': 'repo_6',
                'monitor_repo': "False",
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
                args[0].repo_id)
            self.assertEqual(
                self.sent_configs_example_chain['config_id1']['parent_id'],
                args[0].parent_id)
            self.assertEqual(self.sent_configs_example_chain['config_id1'][
                                 'repo_name'] + '/', args[0].repo_name)
            self.assertEqual(
                str_to_bool(
                    self.sent_configs_example_chain['config_id1'][
                        'monitor_repo']), args[0].monitor_repo)
            self.assertEqual(env.GITHUB_RELEASES_TEMPLATE.format(
                self.sent_configs_example_chain['config_id1']['repo_name']
                + '/'), args[0].releases_page)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.assertEqual(2, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id3' and 'Substrate Polkadot' in args)
            self.assertEqual(new_configs_chain['config_id3']['id'],
                             args[0].repo_id)
            self.assertEqual(new_configs_chain['config_id3']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(new_configs_chain['config_id3']['repo_name'] + '/',
                             args[0].repo_name)
            self.assertEqual(
                str_to_bool(new_configs_chain['config_id3']['monitor_repo']),
                args[0].monitor_repo)
            self.assertEqual(env.GITHUB_RELEASES_TEMPLATE.format(
                new_configs_chain['config_id3']['repo_name'] + '/'),
                args[0].releases_page)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)
            self.assertEqual(3, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id2' and 'general' in args)
            self.assertEqual(
                self.sent_configs_example_general['config_id2']['id'],
                args[0].repo_id)
            self.assertEqual(
                self.sent_configs_example_general['config_id2']['parent_id'],
                args[0].parent_id)
            self.assertEqual(self.sent_configs_example_general['config_id2'][
                                 'repo_name'] + '/', args[0].repo_name)
            self.assertEqual(
                str_to_bool(
                    self.sent_configs_example_general['config_id2'][
                        'monitor_repo']), args[0].monitor_repo)
            self.assertEqual(env.GITHUB_RELEASES_TEMPLATE.format(
                self.sent_configs_example_general['config_id2']['repo_name']
                + '/'), args[0].releases_page)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)
            self.assertEqual(4, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id5' and 'general' in args)
            self.assertEqual(new_configs_general['config_id5']['id'],
                             args[0].repo_id)
            self.assertEqual(new_configs_general['config_id5']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(new_configs_general['config_id5'][
                                 'repo_name'] + '/', args[0].repo_name)
            self.assertEqual(
                str_to_bool(new_configs_general['config_id5']['monitor_repo']),
                args[0].monitor_repo)
            self.assertEqual(env.GITHUB_RELEASES_TEMPLATE.format(
                new_configs_general['config_id5']['repo_name'] + '/'),
                args[0].releases_page)

        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_confs_term_and_starts_monitors_for_modified_confs_to_be_mon(
            self, mock_ack, mock_create_logger,
            mock_process_send_mon_data) -> None:
        # In this test we will check that modified configurations with
        # `monitor_repo = True` will have new monitors started. Implicitly
        # we will be checking that modified configs with
        # `monitor_repo = False` will only have their previous processes
        # terminated.
        mock_process_send_mon_data.return_value = None
        mock_ack.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        new_configs_chain_monitor_true = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'new_repo_name_chain',
                'monitor_repo': "True",
            },
        }
        new_configs_chain_monitor_false = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'new_repo_name_chain',
                'monitor_repo': "False",
            },
        }
        new_configs_general_monitor_true = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'new_repo_name_general',
                'monitor_repo': "True",
            },
        }
        new_configs_general_monitor_false = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'new_repo_name_general',
                'monitor_repo': "false",
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
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
            body_chain_mon_true = json.dumps(new_configs_chain_monitor_true)
            body_general_mon_true = json.dumps(
                new_configs_general_monitor_true)
            body_chain_mon_false = json.dumps(new_configs_chain_monitor_false)
            body_general_mon_false = json.dumps(
                new_configs_general_monitor_false)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give some time till the processes start
            time.sleep(1)

            # Assure that the processes have been started
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id1']['process'].is_alive())
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id2']['process'].is_alive())

            # Send the updated configs with `monitor_repo = True`
            conf_id1_old_proc = self.test_manager.config_process_dict[
                'config_id1']['process']
            conf_id2_old_proc = self.test_manager.config_process_dict[
                'config_id2']['process']
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_mon_true)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_general_mon_true)

            # Give some time till the processes restart
            time.sleep(1)

            # Check that the old proceses has terminated and a new one has
            # started.
            self.assertFalse(conf_id1_old_proc.is_alive())
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id1']['process'].is_alive())
            self.assertFalse(conf_id2_old_proc.is_alive())
            self.assertTrue(self.test_manager.config_process_dict[
                                'config_id2']['process'].is_alive())

            # Send the updated configs with `monitor_repo = False`
            conf_id1_old_proc = self.test_manager.config_process_dict[
                'config_id1']['process']
            conf_id2_old_proc = self.test_manager.config_process_dict[
                'config_id2']['process']
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_mon_false)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_general_mon_false)

            # Give some time till the processes stops
            time.sleep(1)

            # Check that the old process has terminated and that new ones have
            # not been started. Note, if _create_start_process is called then
            # the config ids would be in config_process_dict
            self.assertFalse(conf_id1_old_proc.is_alive())
            self.assertFalse(
                'config_id1' in self.test_manager.config_process_dict)
            self.assertFalse(conf_id2_old_proc.is_alive())
            self.assertFalse(
                'config_id2' in self.test_manager.config_process_dict)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(GitHubMonitorsManager,
                       "_create_and_start_monitor_process")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    def test_process_confs_restarts_an_updated_monitor_with_the_correct_conf(
            self, mock_terminate, mock_join, startup_mock, mock_ack,
            mock_process_send_mon_data) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on an updated configuration.
        mock_process_send_mon_data.return_value = None
        mock_ack.return_value = None
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        updated_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parent_id': 'chain_1',
                'repo_name': 'changed_repo_name_chain',
                'monitor_repo': "True",
            },
        }
        updated_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parent_id': 'GENERAL',
                'repo_name': 'changed_repo_name_gen',
                'monitor_repo': "True",
            },
        }
        self.test_manager._github_repos_configs = \
            self.github_repos_configs_example
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
                             args[0].repo_id)
            self.assertEqual(updated_configs_chain['config_id1']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(
                updated_configs_chain['config_id1']['repo_name'] + '/',
                args[0].repo_name)
            self.assertEqual(
                str_to_bool(
                    updated_configs_chain['config_id1']['monitor_repo']),
                args[0].monitor_repo)
            self.assertEqual(env.GITHUB_RELEASES_TEMPLATE.format(
                updated_configs_chain['config_id1']['repo_name'] + '/'),
                args[0].releases_page)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_updated_configs_general)
            self.assertEqual(2, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id2' and 'general' in args)
            self.assertEqual(updated_configs_general['config_id2']['id'],
                             args[0].repo_id)
            self.assertEqual(updated_configs_general['config_id2']['parent_id'],
                             args[0].parent_id)
            self.assertEqual(
                updated_configs_general['config_id2']['repo_name'] + '/',
                args[0].repo_name)
            self.assertEqual(
                str_to_bool(
                    updated_configs_general['config_id2']['monitor_repo']),
                args[0].monitor_repo)
            self.assertEqual(env.GITHUB_RELEASES_TEMPLATE.format(
                updated_configs_general['config_id2']['repo_name'] + '/'),
                args[0].releases_page)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_terminates_monitors_for_removed_configs(
            self, mock_ack, mock_create_logger,
            mock_process_send_mon_data) -> None:
        # In this test we will check that when a config is removed, it's monitor
        # is terminated by _process_configs.
        mock_ack.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        mock_process_send_mon_data.return_value = None
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain_initial = json.dumps(self.sent_configs_example_chain)
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
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
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_new_configs_with_missing_keys(
            self, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether the state is kept intact if new configurations
        # with missing keys are sent. Exceptions should never be raised in this
        # case, and basic_ack must be called to ignore the message.
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        new_configs_chain = {
            'config_id3': {
                'id': 'config_id3',
                'parentfg_id': 'chain_1',
                'repo_namfge': 'repo_3',
                'monitorfg_repo': "True",
            },
        }
        new_configs_general = {
            'config_id5': {
                'id': 'config_id5',
                'parentdfg_id': 'GENERAL',
                'repo_namdfge': 'repo_5',
                'monitor_repostdfg': "True",
            },
        }
        self.test_manager._github_repos_configs = \
            self.github_repos_configs_example
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
            self.assertEqual(1, mock_process_send_mon_data.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.config_process_dict)
            self.assertEqual(self.github_repos_configs_example,
                             self.test_manager.github_repos_configs)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.assertEqual(2, mock_ack.call_count)
            self.assertEqual(2, mock_process_send_mon_data.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.config_process_dict)
            self.assertEqual(self.github_repos_configs_example,
                             self.test_manager.github_repos_configs)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_modified_configs_with_missing_Keys(
            self, mock_ack, mock_process_send_mon_data) -> None:
        # We will check whether the state is kept intact if modified
        # configurations with missing keys are sent. Exceptions should never be
        # raised in this case, and basic_ack must be called to ignore the
        # message.
        mock_ack.return_value = None
        mock_process_send_mon_data.return_value = None
        updated_configs_chain = {
            'config_id1': {
                'id': 'config_id1',
                'parentfg_id': 'chain_1',
                'repo_namfge': 'repo_1',
                'monitorfg_repo': "True",
            },
        }
        updated_configs_general = {
            'config_id2': {
                'id': 'config_id2',
                'parentdfg_id': 'GENERAL',
                'repo_namdfge': 'repo_2',
                'monitor_repo': "True",
            },
        }
        self.test_manager._github_repos_configs = \
            self.github_repos_configs_example
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
            self.assertEqual(1, mock_process_send_mon_data.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.config_process_dict)
            self.assertEqual(self.github_repos_configs_example,
                             self.test_manager.github_repos_configs)

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_updated_configs_chain)
            self.assertEqual(2, mock_ack.call_count)
            self.assertEqual(2, mock_process_send_mon_data.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.config_process_dict)
            self.assertEqual(self.github_repos_configs_example,
                             self.test_manager.github_repos_configs)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_all_processes_are_alive(
            self, mock_ack, mock_create_logger,
            mock_process_send_mon_data) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_process_send_mon_data.return_value = None
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
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
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

            # Initialise
            method_hb = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
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
            self.test_manager.config_process_dict['config_id1'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id2'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id1'][
                'process'].join()
            self.test_manager.config_process_dict['config_id2'][
                'process'].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_some_processes_alive_some_dead(
            self, mock_ack, mock_create_logger,
            mock_process_send_mon_data) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_process_send_mon_data.return_value = None
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
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
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

            # Initialise
            method_hb = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
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
            self.test_manager.config_process_dict['config_id2'][
                'process'].terminate()
            self.test_manager.config_process_dict['config_id2'][
                'process'].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_ping_sends_a_valid_hb_if_all_processes_dead(
            self, mock_ack, mock_create_logger,
            mock_process_send_mon_data) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_process_send_mon_data.return_value = None
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
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
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

            # Initialise
            method_hb = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
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
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(GitHubMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch("src.monitors.starters.create_logger")
    @mock.patch.object(GitHubMonitorsManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes(
            self, send_hb_mock, mock_create_logger, mock_ack,
            mock_process_send_mon_data) -> None:
        mock_process_send_mon_data.return_value = None
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
            body_general_initial = json.dumps(
                self.sent_configs_example_general)
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

            # Initialise
            method_hb = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
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
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager, "_send_heartbeat")
    @mock.patch.object(GitHubMonitorsManager,
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

            del self.github_repos_configs_example['general']
            del self.config_process_dict_example['config_id2']
            self.test_manager._github_repos_configs = \
                self.github_repos_configs_example
            self.test_manager._config_process_dict = \
                self.config_process_dict_example

            # Initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            properties = pika.spec.BasicProperties()
            body = 'ping'
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            self.assertEqual(1, startup_mock.call_count)
            args, _ = startup_mock.call_args
            self.assertTrue('config_id1' and 'Substrate Polkadot' in args)
            self.assertEqual(self.github_repos_configs_example[
                                 'Substrate Polkadot']['config_id1']['id'],
                             args[0].repo_id)
            self.assertEqual(self.github_repos_configs_example[
                                 'Substrate Polkadot']['config_id1'][
                                 'parent_id'],
                             args[0].parent_id)
            self.assertEqual(self.github_repos_configs_example[
                                 'Substrate Polkadot']['config_id1'][
                                 'repo_name'] + '/',
                             args[0].repo_name)
            self.assertEqual(
                str_to_bool(self.github_repos_configs_example[
                                'Substrate Polkadot']['config_id1'][
                                'monitor_repo']),
                args[0].monitor_repo)
            self.assertEqual(env.GITHUB_RELEASES_TEMPLATE.format(
                self.github_repos_configs_example[
                    'Substrate Polkadot']['config_id1']['repo_name'] + '/'),
                args[0].releases_page)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, 'Process')
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_process, mock_start, is_alive_mock) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat. In this test we will
        # check that no heartbeat is sent when mocking a raised exception.
        is_alive_mock.side_effect = self.test_exception
        mock_start.return_value = None
        mock_process.side_effect = self.dummy_process1
        try:
            self.test_manager._initialise_rabbitmq()

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            self.test_manager._github_repos_configs = \
                self.github_repos_configs_example
            self.test_manager._config_process_dict = \
                self.config_process_dict_example

            # Initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            properties = pika.spec.BasicProperties()
            body = 'ping'
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, res.method.message_count)
            self.test_manager.rabbitmq.queue_bind(
                queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            res = self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(0, res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_connection_err_on_connection_err(
            self, hb_mock) -> None:
        hb_mock.side_effect = pika.exceptions.AMQPConnectionError('test')
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_chan_err_on_chan_err(
            self, hb_mock) -> None:
        hb_mock.side_effect = pika.exceptions.AMQPChannelError('test')
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(GitHubMonitorsManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_exception_on_unexpected_exception(
            self, hb_mock) -> None:
        hb_mock.side_effect = self.test_exception
        try:
            self.test_manager._initialise_rabbitmq()

            # Initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(
                routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(PANICException, self.test_manager._process_ping,
                              blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
