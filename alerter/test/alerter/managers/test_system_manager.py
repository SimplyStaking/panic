import copy
import json
import logging
import multiprocessing
import time
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock
from unittest.mock import call

import pika
import pika.exceptions
from freezegun import freeze_time

from src.alerter.alerter_starters import start_system_alerter
from src.alerter.managers.system import SystemAlertersManager
from src.configs.system_alerts import SystemAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE,
                                 SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME,
                                 SYSTEM_ALERTER_NAME_TEMPLATE,
                                 SYS_ALERTERS_MAN_INPUT_QUEUE,
                                 SYS_ALERTERS_MAN_INPUT_ROUTING_KEY,
                                 SYS_ALERTERS_MAN_CONF_ROUTING_KEY_CHAIN,
                                 SYS_ALERTERS_MAN_CONF_ROUTING_KEY_GEN)
from src.utils.exceptions import PANICException
from test.utils.test_utils import infinite_fn


# Tests adapted from Monitors managers
class TestSystemAlertersManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_system_alerters_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.parent_id_1 = 'test_parent_id_1'
        self.parent_id_2 = 'test_parent_id_2'
        self.parent_id_3 = 'test_parent_id_3'

        self.chain_1 = 'Substrate Polkadot'
        self.chain_2 = 'general'
        self.chain_3 = 'Cosmos'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': datetime(2012, 1, 1, 1).timestamp(),
        }
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = Process(target=infinite_fn, args=())
        self.dummy_process3.daemon = True
        self.config_process_dict_example = {
            self.parent_id_1: {
                "component_name": SYSTEM_ALERTER_NAME_TEMPLATE.format(
                    self.chain_1),
                "process": self.dummy_process1,
                "chain": self.chain_1
            },
            self.parent_id_2: {
                "component_name": SYSTEM_ALERTER_NAME_TEMPLATE.format(
                    self.chain_2),
                "process": self.dummy_process2,
                "chain": self.chain_2
            }
        }
        self.expected_output = {
            self.parent_id_1: {
                "component_name": SYSTEM_ALERTER_NAME_TEMPLATE.format(
                    self.chain_1),
                "process": self.dummy_process1,
                "chain": self.chain_1
            },
            self.parent_id_2: {
                "component_name": SYSTEM_ALERTER_NAME_TEMPLATE.format(
                    self.chain_2),
                "process": self.dummy_process2,
                "chain": self.chain_2
            }
        }
        """
        ############# Alerts config base configuration ######################
        """
        self.enabled_alert = "True"
        self.critical_threshold_percentage = 95
        self.critical_threshold_seconds = 300
        self.critical_repeat_seconds = 300
        self.critical_enabled = "True"
        self.warning_threshold_percentage = 85
        self.warning_threshold_seconds = 200
        self.warning_enabled = "True"

        # ALERTS CONFIG PARENT_1

        self.base_config = {
            "name": "base_percent_config",
            "enabled": self.enabled_alert,
            "parent_id": self.parent_id_1,
            "critical_threshold": self.critical_threshold_percentage,
            "critical_repeat": self.critical_repeat_seconds,
            "critical_enabled": self.critical_enabled,
            "warning_threshold": self.warning_threshold_percentage,
            "warning_enabled": self.warning_enabled
        }

        self.open_file_descriptors = copy.deepcopy(self.base_config)
        self.open_file_descriptors['name'] = "open_file_descriptors"

        self.system_cpu_usage = copy.deepcopy(self.base_config)
        self.system_cpu_usage['name'] = "system_cpu_usage"

        self.system_storage_usage = copy.deepcopy(self.base_config)
        self.system_storage_usage['name'] = "system_storage_usage"

        self.system_ram_usage = copy.deepcopy(self.base_config)
        self.system_ram_usage['name'] = "system_ram_usage"

        self.system_is_down = copy.deepcopy(self.base_config)
        self.system_is_down['name'] = "system_is_down"
        self.system_is_down['critical_threshold'] = \
            self.critical_threshold_seconds
        self.system_is_down['warning_threshold'] = \
            self.warning_threshold_seconds

        self.sent_configs_example = {
            1: self.open_file_descriptors,
            2: self.system_cpu_usage,
            3: self.system_storage_usage,
            4: self.system_ram_usage,
            5: self.system_is_down
        }

        self.sent_configs_example_with_default = {
            "DEFAULT": {},
            "1": self.open_file_descriptors,
            "2": self.system_cpu_usage,
            "3": self.system_storage_usage,
            "4": self.system_ram_usage,
            "5": self.system_is_down
        }

        self.sent_configs_example_with_missing_keys = {
            "DEFAULT": {},
            "1": self.open_file_descriptors,
            "2": self.system_cpu_usage,
            "4": self.system_ram_usage,
            "5": self.system_is_down
        }

        # ALERTS CONFIG PARENT_2
        self.base_config_2 = {
            "name": "base_percent_config",
            "enabled": self.enabled_alert,
            "parent_id": self.parent_id_2,
            "critical_threshold": self.critical_threshold_percentage,
            "critical_repeat": self.critical_repeat_seconds,
            "critical_enabled": self.critical_enabled,
            "warning_threshold": self.warning_threshold_percentage,
            "warning_enabled": self.warning_enabled
        }

        self.open_file_descriptors_2 = copy.deepcopy(self.base_config_2)
        self.open_file_descriptors_2['name'] = "open_file_descriptors"

        self.system_cpu_usage_2 = copy.deepcopy(self.base_config_2)
        self.system_cpu_usage_2['name'] = "system_cpu_usage"

        self.system_storage_usage_2 = copy.deepcopy(self.base_config_2)
        self.system_storage_usage_2['name'] = "system_storage_usage"

        self.system_ram_usage_2 = copy.deepcopy(self.base_config_2)
        self.system_ram_usage_2['name'] = "system_ram_usage"

        self.system_is_down_2 = copy.deepcopy(self.base_config_2)
        self.system_is_down_2['name'] = "system_is_down"
        self.system_is_down_2['critical_threshold'] = \
            self.critical_threshold_seconds
        self.system_is_down_2['warning_threshold'] = \
            self.warning_threshold_seconds

        self.sent_configs_example_with_default_2 = {
            "DEFAULT": {},
            "1": self.open_file_descriptors_2,
            "2": self.system_cpu_usage_2,
            "3": self.system_storage_usage_2,
            "4": self.system_ram_usage_2,
            "5": self.system_is_down_2
        }

        self.sent_configs_example_with_default_2_missing_keys = {
            "DEFAULT": {},
            "1": self.open_file_descriptors_2,
            "2": self.system_cpu_usage_2,
            "4": self.system_ram_usage_2,
            "5": self.system_is_down_2
        }

        self.system_alerts_config = SystemAlertsConfig(
            self.parent_id_1,
            self.open_file_descriptors,
            self.system_cpu_usage,
            self.system_storage_usage,
            self.system_ram_usage,
            self.system_is_down
        )

        self.system_alerts_config_2 = SystemAlertsConfig(
            self.parent_id_2,
            self.open_file_descriptors_2,
            self.system_cpu_usage_2,
            self.system_storage_usage_2,
            self.system_ram_usage_2,
            self.system_is_down_2
        )

        self.test_manager = SystemAlertersManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)

        self.empty_message = {
            "DEFAULT": {}
        }
        self.chain_example_new = 'Substrate Polkadot'
        self.chains_routing_key = 'chains.Substrate.Polkadot.alerts_config'
        self.general_routing_key = SYS_ALERTERS_MAN_CONF_ROUTING_KEY_GEN
        self.test_exception = PANICException('test_exception', 1)
        self.systems_alerts_configs = {}

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_manager.rabbitmq.connect()
            # Declare queues incase they haven't been declared already
            self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_declare(
                queue=SYS_ALERTERS_MAN_INPUT_QUEUE, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_declare(
                queue=SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME, durable=True,
                exclusive=False, auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_purge(self.test_queue_name)
            self.test_manager.rabbitmq.queue_purge(SYS_ALERTERS_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_purge(
                SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(
                SYS_ALERTERS_MAN_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            print("Test failed: %s".format(e))

        self.dummy_logger = None
        self.rabbitmq = None
        self.test_manager = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None
        self.test_manager = None
        self.test_exception = None
        self.system_alerts_config = None
        self.base_config = None
        self.open_file_descriptors = None
        self.system_cpu_usage = None
        self.system_storage_usage = None
        self.system_ram_usage = None
        self.system_is_down = None
        self.systems_alerts_configs = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.__str__())

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_systems_configs_returns_systems_configs(self) -> None:
        self.test_manager._systems_alerts_configs[self.parent_id_1] = \
            self.system_alerts_config
        self.assertEqual(self.system_alerts_config,
                         self.test_manager.systems_alerts_configs[
                             self.parent_id_1])

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        mock_start_consuming.assert_called_once()

    @mock.patch.object(SystemAlertersManager, "_process_ping")
    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self, mock_process_ping) -> None:
        mock_process_ping.return_value = None
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges and queues have not already been
            # declared
            self.test_manager.rabbitmq.connect()

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
                routing_key=SYS_ALERTERS_MAN_INPUT_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=CONFIG_EXCHANGE,
                routing_key=SYS_ALERTERS_MAN_CONF_ROUTING_KEY_CHAIN,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=CONFIG_EXCHANGE,
                routing_key=SYS_ALERTERS_MAN_CONF_ROUTING_KEY_GEN,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queue to get the number of messages
            res = self.test_manager.rabbitmq.queue_declare(
                SYS_ALERTERS_MAN_INPUT_QUEUE, False, True, False, False)
            self.assertEqual(0, res.method.message_count)
            res = self.test_manager.rabbitmq.queue_declare(
                SYSTEM_ALERTERS_MANAGER_CONFIGS_QUEUE_NAME, False, True, False,
                False)
            self.assertEqual(0, res.method.message_count)
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
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, 'Process')
    def test_create_and_start_alerter_process_stores_the_correct_process_info(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process3
        self.test_manager._parent_id_process_dict = \
            self.config_process_dict_example

        self.expected_output[self.parent_id_3] = {}

        new_entry = self.expected_output[self.parent_id_3]
        new_entry['component_name'] = SYSTEM_ALERTER_NAME_TEMPLATE.format(
            self.chain_3)
        new_entry['chain'] = self.chain_3
        new_entry['process'] = self.dummy_process3

        self.test_manager._create_and_start_alerter_process(
            self.system_alerts_config, self.parent_id_3,
            self.chain_3)

        self.assertEqual(self.expected_output,
                         self.test_manager.parent_id_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_alerter_process_creates_the_correct_process(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._create_and_start_alerter_process(
            self.system_alerts_config, self.parent_id_3,
            self.chain_3)

        new_entry = self.test_manager.parent_id_process_dict[self.parent_id_3]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(2, len(new_entry_process._args))
        self.assertEqual(self.system_alerts_config, new_entry_process._args[0])
        self.assertEqual(self.chain_3, new_entry_process._args[1])
        self.assertEqual(start_system_alerter, new_entry_process._target)

    @mock.patch("src.alerter.alerter_starters.create_logger")
    def test_create_and_start_alerter_process_starts_the_process(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger
        self.test_manager._create_and_start_alerter_process(
            self.system_alerts_config, self.parent_id_3,
            self.chain_3)

        # We need to sleep to give some time for the alerter to be initialised,
        # otherwise the process would not terminate
        time.sleep(1)

        new_entry = self.test_manager.parent_id_process_dict[self.parent_id_3]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.is_alive())

        new_entry_process.terminate()
        new_entry_process.join()

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch("src.alerter.managers.system.SystemAlertsConfig")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_default_key(self, mock_ack,
                                                 mock_alerts_config,
                                                 mock_start) -> None:
        # This test will pass if the stored systems config does not change.
        # This would mean that the DEFAULT key was ignored, otherwise, it would
        # have been included as a new config.
        mock_start.return_value = None
        mock_ack.return_value = None
        try:
            # Must create a connection so that the blocking channel is passed
            self.test_manager.rabbitmq.connect()
            blocking_channel = self.test_manager.rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.chains_routing_key)
            method_general = pika.spec.Basic.Deliver(
                routing_key=self.general_routing_key)
            body_chain = json.dumps(self.sent_configs_example_with_default)
            body_general = json.dumps(self.sent_configs_example_with_default)
            properties = pika.spec.BasicProperties()

            # We will send the message twice with both general and chain
            # routing keys to make sure that the DEFAULT key is ignored in both
            # cases
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general)
            mock_alerts_config.assert_called_once_with(
                parent_id=self.parent_id_1,
                open_file_descriptors=self.open_file_descriptors,
                system_cpu_usage=self.system_cpu_usage,
                system_storage_usage=self.system_storage_usage,
                system_ram_usage=self.system_ram_usage,
                system_is_down=self.system_is_down
            )
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain)
            self.assertEqual(2, mock_alerts_config.call_count)
            mock_alerts_config.assert_called_with(
                parent_id=self.parent_id_1,
                open_file_descriptors=self.open_file_descriptors,
                system_cpu_usage=self.system_cpu_usage,
                system_storage_usage=self.system_storage_usage,
                system_ram_usage=self.system_ram_usage,
                system_is_down=self.system_is_down
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.managers.system.SystemAlertsConfig")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemAlertersManager,
                       "_create_and_start_alerter_process")
    def test_process_configs_stores_new_configs_to_be_alerted_correctly(
            self, startup_mock, mock_ack, mock_system_alerts_config) -> None:

        mock_ack.return_value = None
        startup_mock.return_value = None

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
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)

            call_1 = call(parent_id=self.parent_id_1,
                          open_file_descriptors=self.open_file_descriptors,
                          system_cpu_usage=self.system_cpu_usage,
                          system_storage_usage=self.system_storage_usage,
                          system_ram_usage=self.system_ram_usage,
                          system_is_down=self.system_is_down)

            mock_system_alerts_config.assert_has_calls([call_1])

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)
            call_2 = call(parent_id=self.parent_id_2,
                          open_file_descriptors=self.open_file_descriptors_2,
                          system_cpu_usage=self.system_cpu_usage_2,
                          system_storage_usage=self.system_storage_usage_2,
                          system_ram_usage=self.system_ram_usage_2,
                          system_is_down=self.system_is_down_2)

            mock_system_alerts_config.assert_has_calls([call_2])

            self.open_file_descriptors['enabled'] = str(
                not bool(self.enabled_alert))
            self.open_file_descriptors_2['enabled'] = str(
                not bool(self.enabled_alert))
            self.sent_configs_example_with_default[
                '1'] = self.open_file_descriptors
            self.sent_configs_example_with_default_2[
                '1'] = self.open_file_descriptors_2

            body_new_configs_chain = json.dumps(
                self.sent_configs_example_with_default)
            body_new_configs_general = json.dumps(
                self.sent_configs_example_with_default_2)
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            call_3 = call(parent_id=self.parent_id_1,
                          open_file_descriptors=self.open_file_descriptors,
                          system_cpu_usage=self.system_cpu_usage,
                          system_storage_usage=self.system_storage_usage,
                          system_ram_usage=self.system_ram_usage,
                          system_is_down=self.system_is_down)
            mock_system_alerts_config.assert_has_calls([call_3])
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)
            call_4 = call(parent_id=self.parent_id_2,
                          open_file_descriptors=self.open_file_descriptors_2,
                          system_cpu_usage=self.system_cpu_usage_2,
                          system_storage_usage=self.system_storage_usage_2,
                          system_ram_usage=self.system_ram_usage_2,
                          system_is_down=self.system_is_down_2)
            mock_system_alerts_config.assert_has_calls([call_4])
            self.assertEqual(4, mock_system_alerts_config.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.managers.system.SystemAlertsConfig")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    def test_process_configs_stores_modified_configs_to_be_alerted_on_correctly(
            self, mock_join, mock_terminate, mock_start, mock_ack,
            mock_system_alerts_config) -> None:

        mock_ack.return_value = None
        mock_start.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None

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
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            mock_join.assert_not_called()
            mock_terminate.assert_not_called()
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)
            mock_join.assert_not_called()
            mock_terminate.assert_not_called()

            self.open_file_descriptors['enabled'] = str(
                not bool(self.enabled_alert))
            self.open_file_descriptors_2['enabled'] = str(
                not bool(self.enabled_alert))
            self.sent_configs_example_with_default[
                '1'] = self.open_file_descriptors
            self.sent_configs_example_with_default_2[
                '1'] = self.open_file_descriptors_2

            body_new_configs_chain = json.dumps(
                self.sent_configs_example_with_default)
            body_new_configs_general = json.dumps(
                self.sent_configs_example_with_default_2)
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.assertEqual(1, mock_join.call_count)
            self.assertEqual(1, mock_terminate.call_count)

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)
            self.assertEqual(2, mock_join.call_count)
            self.assertEqual(2, mock_terminate.call_count)
            self.assertTrue(
                self.parent_id_1 in self.test_manager.parent_id_process_dict)
            self.assertTrue(
                self.parent_id_2 in self.test_manager.parent_id_process_dict)
            self.assertEqual(4, mock_system_alerts_config.call_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.managers.system.SystemAlertsConfig")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemAlertersManager,
                       "_create_and_start_alerter_process")
    def test_proc_configs_starts_new_alerters_for_new_configs_to_be_alerted_on(
            self, startup_mock, mock_ack, mock_system_alerters_config) -> None:

        mock_system_alerters_config_1 = mock_system_alerters_config(
            parent_id=self.parent_id_1,
            open_file_descriptors=self.open_file_descriptors,
            system_cpu_usage=self.system_cpu_usage,
            system_storage_usage=self.system_storage_usage,
            system_ram_usage=self.system_ram_usage,
            system_is_down=self.system_is_down)
        mock_system_alerters_config_2 = mock_system_alerters_config(
            parent_id=self.parent_id_2,
            open_file_descriptors=self.open_file_descriptors_2,
            system_cpu_usage=self.system_cpu_usage_2,
            system_storage_usage=self.system_storage_usage_2,
            system_ram_usage=self.system_ram_usage_2,
            system_is_down=self.system_is_down_2)
        mock_ack.return_value = None
        startup_mock.return_value = None
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
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.assertEqual(1, startup_mock.call_count)
            startup_mock.assert_called_once_with(
                mock_system_alerters_config_1, self.parent_id_1,
                self.chain_1
            )

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_general_initial)
            self.assertEqual(2, startup_mock.call_count)
            startup_mock.assert_called_with(
                mock_system_alerters_config_2, self.parent_id_2,
                self.chain_2
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerter_starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_confs_term_and_starts_alerters_for_modified_confs_to_be_alerted_on(
            self, mock_ack, mock_create_logger) -> None:

        mock_ack.return_value = None
        mock_create_logger.return_value = self.dummy_logger
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
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Assure that the processes have been started
            self.assertTrue(self.test_manager.parent_id_process_dict[
                                self.parent_id_1]['process'].is_alive())
            self.assertTrue(self.test_manager.parent_id_process_dict[
                                self.parent_id_2]['process'].is_alive())

            # Give some time till the process starts
            time.sleep(1)

            parent_id_1_old_proc = self.test_manager.parent_id_process_dict[
                self.parent_id_1]['process']
            parent_id_2_old_proc = self.test_manager.parent_id_process_dict[
                self.parent_id_2]['process']

            self.open_file_descriptors['enabled'] = str(
                not bool(self.enabled_alert))
            self.open_file_descriptors_2['enabled'] = str(
                not bool(self.enabled_alert))
            self.sent_configs_example_with_default[
                '1'] = self.open_file_descriptors
            self.sent_configs_example_with_default_2[
                '1'] = self.open_file_descriptors_2

            body_new_configs_chain = json.dumps(
                self.sent_configs_example_with_default)
            body_new_configs_general = json.dumps(
                self.sent_configs_example_with_default_2)
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)

            # Give some time till the process re-starts
            time.sleep(1)

            # Check that the old process has terminated and a new one has
            # started.
            self.assertFalse(parent_id_1_old_proc.is_alive())
            self.assertTrue(self.test_manager.parent_id_process_dict[
                                self.parent_id_1]['process'].is_alive())
            self.assertFalse(parent_id_2_old_proc.is_alive())
            self.assertTrue(self.test_manager.parent_id_process_dict[
                                self.parent_id_2]['process'].is_alive())
            self.test_manager.parent_id_process_dict[
                                self.parent_id_1]['process'].terminate()
            self.test_manager.parent_id_process_dict[
                                self.parent_id_2]['process'].terminate()
            self.test_manager.parent_id_process_dict[
                                self.parent_id_1]['process'].join()
            self.test_manager.parent_id_process_dict[
                                self.parent_id_2]['process'].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.alerter_starters.create_logger")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_proc_configs_term_and_stops_alerters_for_removed_configs(
            self, mock_ack, mock_create_logger) -> None:

        mock_ack.return_value = None
        mock_create_logger.return_value = self.dummy_logger
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
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Assure that the processes have been started
            self.assertTrue(self.test_manager.parent_id_process_dict[
                                self.parent_id_1]['process'].is_alive())
            self.assertTrue(self.test_manager.parent_id_process_dict[
                                self.parent_id_2]['process'].is_alive())

            # Give some time till the process starts
            time.sleep(1)

            parent_id_1_old_proc = self.test_manager.parent_id_process_dict[
                self.parent_id_1]['process']
            parent_id_2_old_proc = self.test_manager.parent_id_process_dict[
                self.parent_id_2]['process']

            body_new_configs_chain = json.dumps(self.empty_message)
            body_new_configs_general = json.dumps(self.empty_message)
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)

            # Give some time till the process re-starts
            time.sleep(1)

            # Check that the old process has terminated and a new one has
            # started.
            self.assertFalse(parent_id_1_old_proc.is_alive())
            self.assertFalse(parent_id_2_old_proc.is_alive())
            self.assertFalse(
                self.parent_id_1 in self.test_manager.parent_id_process_dict)
            self.assertFalse(
                self.parent_id_1 in self.test_manager.systems_alerts_configs)
            self.assertFalse(
                self.parent_id_2 in self.test_manager.parent_id_process_dict)
            self.assertFalse(
                self.parent_id_2 in self.test_manager.systems_alerts_configs)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch("src.alerter.managers.system.SystemAlertsConfig")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(SystemAlertersManager,
                       "_create_and_start_alerter_process")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    def test_process_confs_restarts_an_updated_alerter_with_the_correct_conf(
            self, mock_terminate, mock_join, startup_mock, mock_ack,
            mock_system_alerters_config) -> None:

        mock_ack.return_value = None
        startup_mock.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None

        self.test_manager._systems_alerts_configs[self.parent_id_1] = \
            self.system_alerts_config
        self.test_manager._parent_id_process_dict = \
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

            self.open_file_descriptors['enabled'] = str(
                not bool(self.enabled_alert))
            self.open_file_descriptors_2['enabled'] = str(
                not bool(self.enabled_alert))
            self.sent_configs_example_with_default[
                '1'] = self.open_file_descriptors
            self.sent_configs_example_with_default_2[
                '1'] = self.open_file_descriptors_2

            mock_system_alerters_config_1 = mock_system_alerters_config(
                parent_id=self.parent_id_1,
                open_file_descriptors=self.open_file_descriptors,
                system_cpu_usage=self.system_cpu_usage,
                system_storage_usage=self.system_storage_usage,
                system_ram_usage=self.system_ram_usage,
                system_is_down=self.system_is_down)
            mock_system_alerters_config_2 = mock_system_alerters_config(
                parent_id=self.parent_id_2,
                open_file_descriptors=self.open_file_descriptors_2,
                system_cpu_usage=self.system_cpu_usage_2,
                system_storage_usage=self.system_storage_usage_2,
                system_ram_usage=self.system_ram_usage_2,
                system_is_down=self.system_is_down_2)

            body_updated_configs_chain = json.dumps(
                self.sent_configs_example_with_default)
            body_updated_configs_general = json.dumps(
                self.sent_configs_example_with_default_2)

            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_updated_configs_chain)
            startup_mock.assert_called_with(
                mock_system_alerters_config_1, self.parent_id_1,
                self.chain_1
            )

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_updated_configs_general)
            startup_mock.assert_called_with(
                mock_system_alerters_config_2, self.parent_id_2,
                self.chain_2
            )
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_new_configs_with_missing_keys(
            self, mock_ack) -> None:
        # We will check whether the state is kept intact if new configurations
        # with missing keys are sent. Exceptions should never be raised in this
        # case, and basic_ack must be called to ignore the message.
        mock_ack.return_value = None
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
            body_new_configs_general = json.dumps(
                self.sent_configs_example_with_default_2)
            body_new_configs_chain_missing = json.dumps(
                self.sent_configs_example_with_missing_keys)
            properties = pika.spec.BasicProperties()

            # This should start a process as normal
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_new_configs_general)
            self.assertEqual(1, mock_ack.call_count)
            self.assertTrue(
                self.parent_id_2 in self.test_manager.systems_alerts_configs)

            # This should fail to start a process as there are missing keys
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_new_configs_chain_missing)
            self.assertEqual(2, mock_ack.call_count)
            self.assertFalse(
                self.parent_id_1 in self.test_manager.systems_alerts_configs)
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
        self.test_manager._systems_alerts_configs[self.parent_id_1] = \
            self.system_alerts_config
        self.test_manager._systems_alerts_configs[self.parent_id_2] = \
            self.system_alerts_config_2
        self.test_manager._parent_id_process_dict = \
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
            body_updated_configs_chain = json.dumps(
                self.sent_configs_example_with_missing_keys)
            body_updated_configs_general = json.dumps(
                self.sent_configs_example_with_default_2_missing_keys)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties,
                                               body_updated_configs_general)
            self.assertEqual(1, mock_ack.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.parent_id_process_dict)
            self.assertEqual(self.system_alerts_config,
                             self.test_manager.systems_alerts_configs[
                                 self.parent_id_1])

            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties,
                                               body_updated_configs_chain)
            self.assertEqual(2, mock_ack.call_count)
            self.assertEqual(self.config_process_dict_example,
                             self.test_manager.parent_id_process_dict)
            self.assertEqual(self.system_alerts_config_2,
                             self.test_manager.systems_alerts_configs[
                                 self.parent_id_2])
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerter_starters.create_logger")
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
            body_chain_initial = json.dumps(
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
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

            # initialise
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
                    [self.test_manager.parent_id_process_dict[self.parent_id_1][
                         'component_name'],
                     self.test_manager.parent_id_process_dict[self.parent_id_2][
                         'component_name']],
                'dead_processes': [],
                'timestamp': datetime(2012, 1, 1).timestamp(),
            }
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].join()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerter_starters.create_logger")
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
            body_chain_initial = json.dumps(
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the processes to start
            time.sleep(1)

            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].join()

            # Give time for the process to stop
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # initialise
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
                    [self.test_manager.parent_id_process_dict[self.parent_id_2][
                         'component_name']],
                'dead_processes':
                    [self.test_manager.parent_id_process_dict[self.parent_id_1][
                         'component_name']],
                'timestamp': datetime(2012, 1, 1).timestamp(),
            }
            self.assertEqual(expected_output, json.loads(body))

            # Clean before test finishes
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch("src.alerter.alerter_starters.create_logger")
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
            body_chain_initial = json.dumps(
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the processes to start
            time.sleep(1)

            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].join()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].join()

            # Give time for the process to stop
            time.sleep(1)

            # Delete the queue before to avoid messages in the queue on error.
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

            # initialise
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
                    [self.test_manager.parent_id_process_dict[self.parent_id_1][
                         'component_name'],
                     self.test_manager.parent_id_process_dict[self.parent_id_2][
                         'component_name']],
                'timestamp': datetime(2012, 1, 1).timestamp(),
            }
            self.assertEqual(expected_output, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch("src.alerter.alerter_starters.create_logger")
    @mock.patch.object(SystemAlertersManager, "_send_heartbeat")
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
            body_chain_initial = json.dumps(
                self.sent_configs_example_with_default)
            body_general_initial = json.dumps(
                self.sent_configs_example_with_default_2)
            properties = pika.spec.BasicProperties()

            # First send the new configs as the state is empty
            self.test_manager._process_configs(blocking_channel, method_chains,
                                               properties, body_chain_initial)
            self.test_manager._process_configs(blocking_channel, method_general,
                                               properties, body_general_initial)

            # Give time for the processes to start
            time.sleep(1)

            # Automate the case when having all processes dead
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].join()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].join()

            # Give time for the processes to terminate
            time.sleep(1)

            # Check that that the processes have terminated
            self.assertFalse(self.test_manager.parent_id_process_dict[
                                 self.parent_id_1]['process'].is_alive())
            self.assertFalse(self.test_manager.parent_id_process_dict[
                                 self.parent_id_2]['process'].is_alive())

            # initialise
            method_hb = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            body = 'ping'
            self.test_manager._process_ping(blocking_channel, method_hb,
                                            properties, body)

            # Give time for the processes to start
            time.sleep(1)

            self.assertTrue(
                self.test_manager.parent_id_process_dict[self.parent_id_1][
                    'process'].is_alive())
            self.assertTrue(
                self.test_manager.parent_id_process_dict[self.parent_id_2][
                    'process'].is_alive())

            # Clean before test finishes
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_1][
                'process'].join()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].terminate()
            self.test_manager.parent_id_process_dict[self.parent_id_2][
                'process'].join()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlertersManager, "_send_heartbeat")
    @mock.patch.object(SystemAlertersManager,
                       "_create_and_start_alerter_process")
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

            self.test_manager._systems_alerts_configs[self.parent_id_1] = \
                self.system_alerts_config
            self.test_manager._systems_alerts_configs[self.parent_id_2] = \
                self.system_alerts_config_2
            self.test_manager._parent_id_process_dict = \
                self.config_process_dict_example

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            self.assertEqual(2, startup_mock.call_count)

            call_1 = call(
                self.test_manager.systems_alerts_configs[self.parent_id_1],
                self.parent_id_1, self.chain_1)
            call_2 = call(
                self.test_manager.systems_alerts_configs[self.parent_id_2],
                self.parent_id_2, self.chain_2)
            startup_mock.assert_has_calls([call_1, call_2])
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

            self.test_manager._systems_alerts_configs[self.parent_id_1] = \
                self.system_alerts_config
            self.test_manager._systems_alerts_configs[self.parent_id_2] = \
                self.system_alerts_config_2
            self.test_manager._parent_id_process_dict = \
                self.config_process_dict_example

            # initialise
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
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        try:
            self.test_manager._initialise_rabbitmq()

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlertersManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_connection_err_on_connection_err(
            self, hb_mock) -> None:
        hb_mock.side_effect = pika.exceptions.AMQPConnectionError('test')
        try:
            self.test_manager._initialise_rabbitmq()

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(pika.exceptions.AMQPConnectionError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlertersManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_amqp_chan_err_on_chan_err(
            self, hb_mock) -> None:
        hb_mock.side_effect = pika.exceptions.AMQPChannelError('test')
        try:
            self.test_manager._initialise_rabbitmq()

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(pika.exceptions.AMQPChannelError,
                              self.test_manager._process_ping, blocking_channel,
                              method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(SystemAlertersManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_exception_on_unexpected_exception(
            self, hb_mock) -> None:
        hb_mock.side_effect = self.test_exception
        try:
            self.test_manager._initialise_rabbitmq()

            # initialise
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='heartbeat.manager')
            properties = pika.spec.BasicProperties()
            body = 'ping'

            self.assertRaises(PANICException, self.test_manager._process_ping,
                              blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
