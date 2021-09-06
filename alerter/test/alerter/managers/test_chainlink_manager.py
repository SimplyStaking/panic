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
from parameterized import parameterized

from src.alerter.alerter_starters import start_chainlink_node_alerter
from src.alerter.alerters.node.chainlink import ChainlinkNodeAlerter
from src.alerter.alerts.internal_alerts import ComponentResetAlert
from src.alerter.managers.chainlink import (ChainlinkAlertersManager)
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.configs.factory.alerts.chainlink import (
    ChainlinkNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import CHAINLINK_NODE_ALERTER_NAME
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE,
    CONFIG_EXCHANGE,
    CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
    CL_ALERTERS_MAN_HB_QUEUE_NAME,
    PING_ROUTING_KEY, HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY,
    ALERT_EXCHANGE, CL_NODE_ALERT_ROUTING_KEY, CL_ALERTS_CONFIGS_ROUTING_KEY)
from src.utils.exceptions import PANICException
from test.utils.utils import (
    delete_exchange_if_exists, delete_queue_if_exists,
    disconnect_from_rabbit, connect_to_rabbit
)
from test.utils.utils import infinite_fn


class TestChainlinkNodeAlerterManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_chainlink_alerters_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': self.manager_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.chainlink_alerter_name = CHAINLINK_NODE_ALERTER_NAME
        self.dummy_process = Process(target=infinite_fn, args=())
        self.dummy_process.daemon = True

        self.test_rabbit_manager = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        self.test_manager = ChainlinkAlertersManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)
        self.test_exception = PANICException('test_exception', 1)

        self.routing_key_1 = 'chains.chainlink.ethereum.alerts_config'
        self.routing_key_2 = 'chains.chainlink.polygon.alerts_config'
        self.config_1 = {
            "1": {
                "name": "1_st_alert",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "6": {
                "name": "head_tracker_current_head",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "7": {
                "name": "head_tracker_heads_received_total",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "8": {
                "name": "max_unconfirmed_blocks",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "9": {
                "name": "tx_manager_gas_bump_exceeds_limit_total",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "10": {
                "name": "unconfirmed_transactions",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "11": {
                "name": "eth_balance_amount",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "12": {
                "name": "run_status_update_total",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "13": {
                "name": "process_start_time_seconds",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "14": {
                "name": "eth_balance_amount_increase",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            },
            "15": {
                "name": "node_is_down",
                "parent_id": "chain_name_d21d780d-92cb-42de-a7c1-11b751654510",
            }
        }
        self.config_2 = {
            "1": {
                "name": "1_st_alert",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "6": {
                "name": "head_tracker_current_head",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "7": {
                "name": "head_tracker_heads_received_total",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "8": {
                "name": "max_unconfirmed_blocks",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "9": {
                "name": "tx_manager_gas_bump_exceeds_limit_total",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "10": {
                "name": "unconfirmed_transactions",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "11": {
                "name": "eth_balance_amount",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "12": {
                "name": "run_status_update_total",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "13": {
                "name": "process_start_time_seconds",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "14": {
                "name": "eth_balance_amount_increase",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            },
            "15": {
                "name": "node_is_down",
                "parent_id": "chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4",
            }
        }

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_rabbit_manager)
        connect_to_rabbit(self.test_manager.rabbitmq)

        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  ALERT_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  CONFIG_EXCHANGE)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               CL_ALERTERS_MAN_HB_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME)

        disconnect_from_rabbit(self.test_manager.rabbitmq)
        disconnect_from_rabbit(self.test_rabbit_manager)

        self.dummy_logger = None
        self.rabbitmq = None
        self.test_manager = None
        self.test_exception = None
        self.test_rabbit_manager = None

        self.dummy_process = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, str(self.test_manager))

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        self.assertEqual(1, mock_start_consuming.call_count)

    @mock.patch.object(RabbitMQApi, "basic_consume")
    @mock.patch.object(ChainlinkAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    @mock.patch.object(ChainlinkAlertersManager, "_process_ping")
    @mock.patch.object(ChainlinkAlertersManager, "_process_configs")
    @mock.patch.object(ChainlinkAlertersManager,
                       "_create_and_start_alerter_process")
    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self, mock_start_alerter_process, mock_process_configs,
            mock_process_ping, mock_push_latest_data_to_queue_and_send,
            mock_basic_consume) -> None:
        mock_process_ping.return_value = None
        mock_process_configs.return_value = None
        mock_start_alerter_process.return_value = None
        self.test_rabbit_manager.connect()
        # To make sure that there is no connection/channel already
        # established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        self.test_manager.rabbitmq.connect()
        self.test_manager.rabbitmq.queue_delete(
            CL_ALERTERS_MAN_HB_QUEUE_NAME)
        self.test_manager.rabbitmq.queue_delete(
            CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME
        )
        self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)

        self.test_manager._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_manager.rabbitmq.is_connected)
        self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_manager.rabbitmq.channel._delivery_confirmation)

        # Check whether the exchanges and queues have been creating by
        # sending messages with the same routing keys as for the queues. We
        # will also check if the size of the queues is 1 to confirm that the
        # message was sent. We then check if basic_consume was called
        # correctly with the correct arguments If one of the exchanges or
        # queues is not created, then an exception will be thrown.
        # Note when deleting the exchanges in the beginning we also
        # released every binding, hence there is no other queue binded with
        # the same routing key to any exchange at this point.
        self.test_rabbit_manager.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=PING_ROUTING_KEY, body=self.test_data_str,
            is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=ALERT_EXCHANGE,
            routing_key=CL_NODE_ALERT_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=False
        )
        self.test_rabbit_manager.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=CL_ALERTS_CONFIGS_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )
        # Re-declare queue to get the number of messages
        res = self.test_rabbit_manager.queue_declare(
            CL_ALERTERS_MAN_HB_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(1, res.method.message_count)
        res = self.test_rabbit_manager.queue_declare(
            CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(1, res.method.message_count)
        self.assertEqual(2, mock_basic_consume.call_count)

        expected_calls = [
            call(CL_ALERTERS_MAN_HB_QUEUE_NAME,
                 self.test_manager._process_ping, True, False, None),
            call(CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
                 self.test_manager._process_configs, False, False, None)
        ]
        mock_basic_consume.assert_has_calls(expected_calls, True)
        mock_push_latest_data_to_queue_and_send.assert_not_called()

    @mock.patch.object(ChainlinkAlertersManager,
                       "_create_and_start_alerter_process")
    def test_send_heartbeat_sends_a_heartbeat_correctly(
            self, mock_start_alerter_process) -> None:
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
        self.assertEqual(0, mock_start_alerter_process.call_count)

    @mock.patch.object(ChainlinkAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_alerter_process_creates_the_correct_process(
            self, mock_start, mock_push_latest_data_to_queue_and_send) -> None:
        mock_start.return_value = None
        mock_push_latest_data_to_queue_and_send.return_value = None

        self.test_manager._create_and_start_alerter_processes()

        new_entry_process = self.test_manager.alerter_process_dict[
            CHAINLINK_NODE_ALERTER_NAME]

        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(1, len(new_entry_process._args))
        self.assertEqual(start_chainlink_node_alerter,
                         new_entry_process._target)
        mock_push_latest_data_to_queue_and_send.assert_called_once()

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(ChainlinkAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    @mock.patch("src.alerter.alerter_starters.create_logger")
    def test_start_alerters_process_starts_the_process(
            self, mock_create_logger, mock_push_latest_data_to_queue_and_send,
            mock_start) -> None:
        mock_create_logger.return_value = self.dummy_logger
        mock_push_latest_data_to_queue_and_send.return_value = None
        mock_start.return_value = None

        self.test_manager._create_and_start_alerter_processes()

        mock_start.assert_called_once()
        mock_push_latest_data_to_queue_and_send.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(ChainlinkAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    @mock.patch("src.alerter.alerter_starters.create_logger")
    def test_start_alerters_process_sends_a_component_reset_alert(
            self, mock_create_logger, mock_push_latest_data_to_queue_and_send,
            mock_start) -> None:
        mock_create_logger.return_value = self.dummy_logger
        mock_push_latest_data_to_queue_and_send.return_value = None
        mock_start.return_value = None

        self.test_manager._create_and_start_alerter_processes()

        expected_alert = ComponentResetAlert(CHAINLINK_NODE_ALERTER_NAME,
                                             datetime.now().timestamp(),
                                             ChainlinkNodeAlerter.__name__)

        mock_push_latest_data_to_queue_and_send.assert_called_once_with(
            expected_alert.alert_data)

    @freeze_time("2012-01-01")
    @mock.patch(
        "src.alerter.managers.chainlink.ChainlinkNodeAlerterManager._push_latest_data_to_queue_and_send")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    def test_process_ping_sends_a_valid_hb_if_process_is_alive(
            self, mock_terminate, mock_join, mock_start, mock_is_alive,
            mock_ack, mock_push_latest_data_to_queue_and_send) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_ack.return_value = None
        mock_is_alive.return_value = True
        mock_start.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        self.test_manager._initialise_rabbitmq()
        self.test_manager._create_and_start_alerter_processes()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

        # initialise
        blocking_channel = self.test_manager.rabbitmq.channel
        properties = pika.spec.BasicProperties()
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
        expected_output = {
            "component_name": self.manager_name,
            "dead_processes": [],
            "running_processes": [CHAINLINK_NODE_ALERTER_NAME],
            "timestamp": datetime(2012, 1, 1).timestamp()
        }
        # Check that the message received is a valid HB
        _, _, body = self.test_manager.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output, json.loads(body))
        self.assertEqual(
            1, mock_push_latest_data_to_queue_and_send.call_count)

    @freeze_time("2012-01-01")
    @mock.patch(
        "src.alerter.managers.chainlink.ChainlinkNodeAlerterManager._push_latest_data_to_queue_and_send")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    def test_process_ping_sends_a_valid_hb_if_process_is_dead(
            self, mock_terminate, mock_join, mock_start, mock_is_alive,
            mock_ack, mock_push_latest_data_to_queue_and_send) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # received heartbeat is valid.
        mock_ack.return_value = None
        mock_is_alive.return_value = False
        mock_start.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        self.test_manager._initialise_rabbitmq()
        self.test_manager._create_and_start_alerter_processes()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

        # initialise
        blocking_channel = self.test_manager.rabbitmq.channel
        properties = pika.spec.BasicProperties()
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
        expected_output = {
            "component_name": self.manager_name,
            "dead_processes": [CHAINLINK_NODE_ALERTER_NAME],
            "running_processes": [],
            "timestamp": datetime(2012, 1, 1).timestamp()
        }
        # Check that the message received is a valid HB
        _, _, body = self.test_manager.rabbitmq.basic_get(
            self.test_queue_name)
        self.assertEqual(expected_output, json.loads(body))
        self.assertEqual(
            2,
            mock_push_latest_data_to_queue_and_send.call_count)

    @freeze_time("2012-01-01")
    @mock.patch(
        "src.alerter.managers.chainlink.ChainlinkNodeAlerterManager._push_latest_data_to_queue_and_send")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch("src.alerter.alerter_starters.create_logger")
    @mock.patch.object(ChainlinkAlertersManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes(
            self, send_hb_mock, mock_create_logger, mock_ack,
            mock_push_latest_data_to_queue_and_send) -> None:
        send_hb_mock.return_value = None
        mock_create_logger.return_value = self.dummy_logger
        mock_ack.return_value = None
        self.test_manager._initialise_rabbitmq()
        self.test_manager._create_and_start_alerter_processes()

        # Give time for the processes to start
        time.sleep(1)

        # Automate the case when having all processes dead
        self.test_manager.alerter_process_dict[
            CHAINLINK_NODE_ALERTER_NAME].terminate()
        self.test_manager.alerter_process_dict[
            CHAINLINK_NODE_ALERTER_NAME].join()

        # Give time for the processes to terminate
        time.sleep(1)

        # Check that that the processes have terminated
        self.assertFalse(self.test_manager.alerter_process_dict[
                             CHAINLINK_NODE_ALERTER_NAME].is_alive())

        # initialise
        blocking_channel = self.test_manager.rabbitmq.channel
        properties = pika.spec.BasicProperties()
        method_hb = pika.spec.Basic.Deliver(
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
        body = 'ping'
        self.test_manager._process_ping(blocking_channel, method_hb,
                                        properties, body)

        # Give time for the processes to start
        time.sleep(1)

        self.assertTrue(self.test_manager.alerter_process_dict[
                            CHAINLINK_NODE_ALERTER_NAME].is_alive())

        # Clean before test finishes
        self.test_manager.alerter_process_dict[
            CHAINLINK_NODE_ALERTER_NAME].terminate()
        self.test_manager.alerter_process_dict[
            CHAINLINK_NODE_ALERTER_NAME].join()
        self.assertEqual(
            2,
            mock_push_latest_data_to_queue_and_send.call_count
        )

    @mock.patch(
        "src.alerter.managers.chainlink.ChainlinkNodeAlerterManager._push_latest_data_to_queue_and_send")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, 'Process')
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_process, mock_start, is_alive_mock,
            mock_push_latest_data_to_queue_and_send) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat. In this test we will
        # check that no heartbeat is sent when mocking a raised exception.
        is_alive_mock.side_effect = self.test_exception
        mock_start.return_value = None
        mock_process.side_effect = self.dummy_process
        self.test_manager._initialise_rabbitmq()
        self.test_manager._create_and_start_alerter_processes()

        self.test_manager.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )

        # Delete the queue before to avoid messages in the queue on error.
        self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

        # initialise
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
        mock_push_latest_data_to_queue_and_send.assert_called_once()

    @mock.patch(
        "src.alerter.managers.chainlink.ChainlinkNodeAlerterManager._push_latest_data_to_queue_and_send")
    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self, mock_push_latest_data_to_queue_and_send) -> None:
        self.test_manager._initialise_rabbitmq()
        self.test_manager._create_and_start_alerter_processes()

        # initialise
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
        properties = pika.spec.BasicProperties()
        body = 'ping'

        self.test_manager._process_ping(blocking_channel, method,
                                        properties, body)
        mock_push_latest_data_to_queue_and_send.assert_called_once()

    @parameterized.expand([
        ("pika.exceptions.AMQPChannelError('test')",
         "pika.exceptions.AMQPChannelError"),
        ("self.test_exception", "PANICException"),
    ])
    @mock.patch(
        "src.alerter.managers.chainlink.ChainlinkNodeAlerterManager._push_latest_data_to_queue_and_send")
    @mock.patch.object(ChainlinkAlertersManager, "_send_heartbeat")
    def test_process_ping_send_hb_raises_exceptions(
            self, param_input, param_expected, hb_mock,
            mock_push_latest_data_to_queue_and_send) -> None:
        hb_mock.side_effect = eval(param_input)
        self.test_manager._initialise_rabbitmq()

        # initialise
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
        properties = pika.spec.BasicProperties()
        body = 'ping'

        self.assertRaises(eval(param_expected),
                          self.test_manager._process_ping,
                          blocking_channel,
                          method, properties, body)
        mock_push_latest_data_to_queue_and_send.assert_not_called()

    @parameterized.expand([
        ("self.config_1", "self.routing_key_1"),
        ("self.config_2", "self.routing_key_2")
    ])
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(ChainlinkNodeAlertsConfigsFactory, "add_new_config")
    def test_process_configs_calls_config_factory_correctly(
            self, param_config, param_routing_key, mock_add_new_config,
            mock_ack) -> None:
        mock_ack.return_value = None

        self.test_manager.rabbitmq.connect()

        routing_key = eval(param_routing_key)
        parsed_routing_key = routing_key.split('.')

        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(
            routing_key=routing_key)
        body = json.dumps(eval(param_config))
        properties = pika.spec.BasicProperties()
        self.test_manager._process_configs(
            blocking_channel, method_chains, properties, body)

        chain_name = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        mock_add_new_config.assert_called_once_with(
            chain_name, eval(param_config))

    @parameterized.expand([
        ("self.routing_key_1",),
        ("self.routing_key_2",)
    ])
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(ChainlinkNodeAlertsConfigsFactory, "remove_config")
    def test_process_config_calls_config_factory_remove_config_correctly(
            self, param_routing_key, mock_remove_config, mock_ack) -> None:
        mock_ack.return_value = None

        self.test_manager.rabbitmq.connect()

        routing_key = eval(param_routing_key)
        parsed_routing_key = routing_key.split('.')

        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(
            routing_key=routing_key)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        self.test_manager._process_configs(
            blocking_channel, method_chains, properties, body)

        chain_name = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        mock_remove_config.assert_called_once_with(
            chain_name)

    @parameterized.expand([
        ("self.config_1", "self.routing_key_1"),
        ("self.config_2", "self.routing_key_2")
    ])
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch(
        "src.alerter.managers.chainlink.ChainlinkNodeAlerterManager._push_latest_data_to_queue_and_send")
    def test_process_configs_configs_get_updated_and_generates_alert(
            self, param_config, param_routing_key, mock_push_data_to_queue,
            mock_ack) -> None:
        mock_ack.return_value = None

        self.test_manager.rabbitmq.connect()

        routing_key = eval(param_routing_key)
        parsed_routing_key = routing_key.split('.')

        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(
            routing_key=routing_key)
        body = json.dumps(eval(param_config))
        properties = pika.spec.BasicProperties()
        self.test_manager._process_configs(
            blocking_channel, method_chains, properties, body)

        call_1 = call({'alert_code': {'name': 'ComponentResetAlert',
                                      'code': 'internal_alert_1'},
                       'metric': 'component_reset_alert',
                       'message': 'Component: Chainlink Node Alerter has been reset for chainlink polygon.',
                       'severity': 'INTERNAL',
                       'parent_id': 'chain_name_28a13d92-740f-4ae9-ade3-3248d76faaa4',
                       'origin_id': 'ChainlinkNodeAlerter',
                       'timestamp': 1625239987.518717}
                      )

        mock_push_data_to_queue.has_calls(call_1)

        self.test_manager._process_configs(
            blocking_channel, method_chains, properties, body)

        # Second time the config is updated therefore a reset alert should
        # be sent.
        mock_push_data_to_queue.has_calls(call_1, call_1)

    @parameterized.expand([
        ("self.config_1", "self.routing_key_1"),
        ("self.config_2", "self.routing_key_2")
    ])
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_stores_configs_in_factory(
            self, param_config, param_routing_key, mock_ack) -> None:
        mock_ack.return_value = None

        self.test_manager.rabbitmq.connect()

        routing_key = eval(param_routing_key)
        parsed_routing_key = routing_key.split('.')
        chain_name = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        self.assertFalse(
            self.test_manager.node_alerts_config_factory.config_exists(
                chain_name, ChainlinkNodeAlertsConfig))

        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(
            routing_key=routing_key)
        body = json.dumps(eval(param_config))
        properties = pika.spec.BasicProperties()
        self.test_manager._process_configs(
            blocking_channel, method_chains, properties, body)

        self.assertTrue(
            self.test_manager.node_alerts_config_factory.config_exists(
                chain_name, ChainlinkNodeAlertsConfig))
