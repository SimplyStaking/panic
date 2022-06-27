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

from src.abstract.publisher_subscriber import \
    QueuingPublisherSubscriberComponent
from src.alerter.alerter_starters import (
    start_substrate_node_alerter, start_substrate_network_alerter)
from src.alerter.alerters.network.substrate import SubstrateNetworkAlerter
from src.alerter.alerters.node.substrate import SubstrateNodeAlerter
from src.alerter.alerts.internal_alerts import ComponentResetAlert
from src.alerter.managers.substrate import SubstrateAlertersManager
from src.configs.alerts.network.substrate import SubstrateNetworkAlertsConfig
from src.configs.alerts.node.substrate import SubstrateNodeAlertsConfig
from src.configs.factory.alerts.substrate_alerts import (
    SubstrateNetworkAlertsConfigsFactory, SubstrateNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (
    SUBSTRATE_NODE_ALERTER_NAME, SUBSTRATE_NETWORK_ALERTER_NAME)
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE, ALERT_EXCHANGE,
    SUBSTRATE_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
    SUBSTRATE_ALERTERS_MAN_HB_QUEUE_NAME, SUBSTRATE_NETWORK_ALERT_ROUTING_KEY,
    PING_ROUTING_KEY, SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY,
    HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY, SUBSTRATE_NODE_ALERT_ROUTING_KEY)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from test.test_utils.utils import (
    delete_exchange_if_exists, delete_queue_if_exists, disconnect_from_rabbit,
    connect_to_rabbit, infinite_fn)


class TestSubstrateAlertersManager(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy objects
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.manager_name = 'test_substrate_alerters_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': self.manager_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.dummy_process_1 = Process(target=infinite_fn, args=())
        self.dummy_process_1.daemon = True
        self.dummy_process_2 = Process(target=infinite_fn, args=())
        self.dummy_process_2.daemon = True
        self.test_exception = PANICException('test_exception', 1)

        # RabbitMQ initialisation
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, env.RABBIT_IP,
            connection_check_time_interval=self.connection_check_time_interval)

        # Test routing key and parent_id
        self.routing_key = 'chains.substrate.polkadot.alerts_config'
        self.parent_id = "chain_name_d21d780d-92cb-42de-a7c1-11b751654510"
        self.chain_name = 'substrate polkadot'

        # Construct received configurations
        substrate_config_metrics = [
            'cannot_access_validator', 'cannot_access_node',
            'no_change_in_best_block_height_validator',
            'no_change_in_best_block_height_node',
            'no_change_in_finalized_block_height_validator',
            'no_change_in_finalized_block_height_node',
            'validator_is_syncing', 'node_is_syncing',
            'not_active_in_session', 'is_disabled', 'not_elected',
            'bonded_amount_change', 'no_heartbeat_did_not_author_block',
            'offline', 'slashed', 'payout_not_claimed',
            'controller_address_change', 'grandpa_is_stalled',
            'new_proposal', 'new_referendum', 'referendum_concluded'
        ]
        self.received_configs = {}
        for i in range(len(substrate_config_metrics)):
            self.received_configs[str(i)] = {
                'name': substrate_config_metrics[i],
                'parent_id': self.parent_id
            }

        # Construct expected stored configurations
        filtered_received_configs = {}
        for _, config in self.received_configs.items():
            filtered_received_configs[config['name']] = copy.deepcopy(config)

        self.node_config_expected = {
            self.chain_name: SubstrateNodeAlertsConfig(
                parent_id=self.parent_id,
                cannot_access_validator=filtered_received_configs[
                    'cannot_access_validator'],
                cannot_access_node=filtered_received_configs[
                    'cannot_access_node'],
                no_change_in_best_block_height_validator=
                filtered_received_configs[
                    'no_change_in_best_block_height_validator'],
                no_change_in_best_block_height_node=filtered_received_configs[
                    'no_change_in_best_block_height_node'],
                no_change_in_finalized_block_height_validator=
                filtered_received_configs[
                    'no_change_in_finalized_block_height_validator'],
                no_change_in_finalized_block_height_node=
                filtered_received_configs[
                    'no_change_in_finalized_block_height_node'],
                validator_is_syncing=filtered_received_configs[
                    'validator_is_syncing'],
                node_is_syncing=filtered_received_configs[
                    'node_is_syncing'],
                not_active_in_session=filtered_received_configs[
                    'not_active_in_session'],
                is_disabled=filtered_received_configs[
                    'is_disabled'],
                not_elected=filtered_received_configs['not_elected'],
                bonded_amount_change=filtered_received_configs[
                    'bonded_amount_change'],
                no_heartbeat_did_not_author_block=filtered_received_configs[
                    'no_heartbeat_did_not_author_block'],
                offline=filtered_received_configs['offline'],
                slashed=filtered_received_configs['slashed'],
                payout_not_claimed=filtered_received_configs[
                    'payout_not_claimed'],
                controller_address_change=filtered_received_configs[
                    'controller_address_change']
            )
        }

        self.network_config_expected = {
            self.chain_name: SubstrateNetworkAlertsConfig(
                parent_id=self.parent_id,
                grandpa_is_stalled=
                filtered_received_configs['grandpa_is_stalled'],
                new_proposal=filtered_received_configs['new_proposal'],
                new_referendum=filtered_received_configs['new_referendum'],
                referendum_concluded=
                filtered_received_configs['referendum_concluded'],
            )
        }

        self.test_manager = SubstrateAlertersManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)
        self.alerter_process_dict_example = {
            SUBSTRATE_NODE_ALERTER_NAME: self.dummy_process_1,
            SUBSTRATE_NETWORK_ALERTER_NAME: self.dummy_process_2
        }
        self.node_alerts_config_factory = (
            SubstrateNodeAlertsConfigsFactory())
        self.network_alerts_config_factory = (
            SubstrateNetworkAlertsConfigsFactory())
        self.configs_processor_helper_example = {
            SUBSTRATE_NODE_ALERTER_NAME: {
                'alerterClass': SubstrateNodeAlerter,
                'factory': self.node_alerts_config_factory,
                'routing_key': SUBSTRATE_NODE_ALERT_ROUTING_KEY,
                'starter': start_substrate_node_alerter,
            },
            SUBSTRATE_NETWORK_ALERTER_NAME: {
                'alerterClass': SubstrateNetworkAlerter,
                'factory': self.network_alerts_config_factory,
                'routing_key': SUBSTRATE_NETWORK_ALERT_ROUTING_KEY,
                'starter': start_substrate_network_alerter,
            },
        }

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               SUBSTRATE_ALERTERS_MAN_HB_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               SUBSTRATE_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq, ALERT_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq, CONFIG_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.dummy_process_1 = None
        self.dummy_process_2 = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_exception = None
        self.node_alerts_config_factory = None
        self.network_alerts_config_factory = None
        self.alerter_process_dict_example = None
        self.test_manager = None
        self.configs_processor_helper_example = None
        self.received_configs = None
        self.filtered_received_configs = None
        self.node_config_expected = None
        self.network_config_expected = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, str(self.test_manager))

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_alerter_process_dict_returns_alerter_process_dict(self) -> None:
        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example
        self.assertEqual(self.alerter_process_dict_example,
                         self.test_manager.alerter_process_dict)

    def test_config_factory_properties_return_correctly(self) -> None:
        # Test for the node alerts config factory
        self.test_manager._node_alerts_config_factory = \
            self.node_alerts_config_factory
        self.assertEqual(self.node_alerts_config_factory,
                         self.test_manager.node_alerts_config_factory)

        # Test for the network alerts config factory
        self.test_manager._network_alerts_config_factory = \
            self.network_alerts_config_factory
        self.assertEqual(self.network_alerts_config_factory,
                         self.test_manager.network_alerts_config_factory)

    def test_configs_processor_helper_return_correctly(self) -> None:
        self.test_manager._configs_processor_helper = \
            self.configs_processor_helper_example
        self.assertEqual(self.configs_processor_helper_example,
                         self.test_manager.configs_processor_helper)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        self.assertEqual(1, mock_start_consuming.call_count)

    @mock.patch.object(RabbitMQApi, "basic_consume")
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
            SUBSTRATE_ALERTERS_MAN_HB_QUEUE_NAME)
        self.test_manager.rabbitmq.queue_delete(
            SUBSTRATE_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
        self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(ALERT_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_manager._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_manager.rabbitmq.is_connected)
        self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_manager.rabbitmq.channel._delivery_confirmation)

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_manager.rabbitmq.exchange_declare(ALERT_EXCHANGE,
                                                    passive=True)

        # Check whether the consuming exchanges and queues have been created by
        # sending messages with the same routing keys as for the bindings.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=PING_ROUTING_KEY,
            body='test_str', is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY,
            body='another_test_str', is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages, and check that the
        # message received is the message sent
        res = self.test_manager.rabbitmq.queue_declare(
            SUBSTRATE_ALERTERS_MAN_HB_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            SUBSTRATE_ALERTERS_MAN_HB_QUEUE_NAME)
        self.assertEqual('test_str', body.decode())

        res = self.test_manager.rabbitmq.queue_declare(
            SUBSTRATE_ALERTERS_MAN_CONFIGS_QUEUE_NAME, False, True, False,
            False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            SUBSTRATE_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual('another_test_str', body.decode())

        expected_calls = [
            call(SUBSTRATE_ALERTERS_MAN_HB_QUEUE_NAME,
                 self.test_manager._process_ping, True, False, None),
            call(SUBSTRATE_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
                 self.test_manager._process_configs, False, False, None)
        ]
        mock_basic_consume.assert_has_calls(expected_calls, True)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones set by send_heartbeat, and checks that the
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
        _, _, body = self.test_manager.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    @parameterized.expand([
        ([True, True], [],),
        ([False, True], [SUBSTRATE_NODE_ALERTER_NAME],),
        ([True, False], [SUBSTRATE_NETWORK_ALERTER_NAME],),
        ([False, False], [SUBSTRATE_NODE_ALERTER_NAME,
                          SUBSTRATE_NETWORK_ALERTER_NAME],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(SubstrateAlertersManager,
                       "_create_and_start_alerter_processes")
    @mock.patch.object(SubstrateAlertersManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb(
            self, is_alive_side_effect, dead_alerters, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect

        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example

        # Some variables below are needed as parameters for the process_ping fn
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        expected_hb = {
            'component_name': self.manager_name,
            'running_processes': [
                alerter
                for alerter in self.alerter_process_dict_example.keys()
                if alerter not in dead_alerters
            ],
            'dead_processes': dead_alerters,
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(expected_hb)

    @parameterized.expand([
        ([True, True], False,),
        ([False, True], True,),
        ([True, False], True,),
        ([False, False], True,),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(SubstrateAlertersManager,
                       "_create_and_start_alerter_processes")
    @mock.patch.object(SubstrateAlertersManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes_correctly(
            self, is_alive_side_effect, expected_restart, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect

        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example

        # Some variables below are needed as parameters for the process_ping fn
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        if expected_restart:
            mock_create_and_start.assert_called_once()
        else:
            mock_create_and_start.assert_not_called()

    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(SubstrateAlertersManager, "_send_heartbeat")
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_send_hb, mock_is_alive) -> None:
        mock_is_alive.side_effect = self.test_exception
        mock_send_hb.return_value = None
        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example

        # Some variables below are needed as parameters for the process_ping fn
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        mock_send_hb.assert_not_called()

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        """
        In this test we are assuming that no configs have been set, this is done
        to keep the test as simple as possible. We are also assuming that a
        MsgWasNotDeliveredException will be raised automatically because we are
        deleting the HealthExchange after every test, and thus there are no
        consumers of the heartbeat.
        """
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
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
    @mock.patch.object(SubstrateAlertersManager, "_send_heartbeat")
    def test_process_ping_raises_unrecognised_error_if_raised_by_send_heartbeat(
            self, exception_class, exception_instance, mock_send_hb) -> None:
        mock_send_hb.side_effect = exception_instance

        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_class, self.test_manager._process_ping,
                          blocking_channel, method, properties, body)

    @parameterized.expand([
        ({}, False,),
        ('self.alerter_process_dict_example', True)
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(SubstrateAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_alerter_processes_if_processes_not_running(
            self, state, state_is_str, mock_start, mock_push_and_send) -> None:
        """
        In this test we will check that the required processes are created and
        started, and that reset alerts are sent. We will perform this test for
        both when the function is executed for the first time (empty state), and
        for when the process is dead (state non-empty but dummy process not
        running by default)
        """
        self.test_manager._alerter_process_dict = (
            eval(state) if state_is_str else state
        )
        mock_start.return_value = None
        mock_push_and_send.return_value = None

        self.test_manager._create_and_start_alerter_processes()

        node_alerter_process = self.test_manager.alerter_process_dict[
            SUBSTRATE_NODE_ALERTER_NAME]
        network_alerter_process = self.test_manager.alerter_process_dict[
            SUBSTRATE_NETWORK_ALERTER_NAME]

        # Check that the processes were created correctly
        self.assertTrue(node_alerter_process.daemon)
        self.assertEqual(1, len(node_alerter_process._args))
        self.assertEqual(self.test_manager.node_alerts_config_factory,
                         node_alerter_process._args[0])
        self.assertEqual(start_substrate_node_alerter,
                         node_alerter_process._target)
        self.assertTrue(network_alerter_process.daemon)
        self.assertEqual(1, len(network_alerter_process._args))
        self.assertEqual(self.test_manager.network_alerts_config_factory,
                         network_alerter_process._args[0])
        self.assertEqual(start_substrate_network_alerter,
                         network_alerter_process._target)

        # Check that the processes were started
        self.assertEqual(2, mock_start.call_count)

        # Check that 2 reset alerts were sent
        expected_alert_1 = ComponentResetAlert(
            SUBSTRATE_NODE_ALERTER_NAME, datetime.now().timestamp(),
            SubstrateNodeAlerter.__name__)
        expected_alert_2 = ComponentResetAlert(
            SUBSTRATE_NETWORK_ALERTER_NAME, datetime.now().timestamp(),
            SubstrateNetworkAlerter.__name__)
        expected_calls = [
            call(expected_alert_1.alert_data, SUBSTRATE_NODE_ALERT_ROUTING_KEY),
            call(expected_alert_2.alert_data,
                 SUBSTRATE_NETWORK_ALERT_ROUTING_KEY),
        ]
        mock_push_and_send.assert_has_calls(expected_calls, True)

    @mock.patch.object(SubstrateAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_alerter_proc_does_nothing_if_proc_running(
            self, mock_start, mock_is_alive, mock_init_proc,
            mock_push_and_send) -> None:
        """
        In this test we will check that no process is created or started, and
        that no reset alert is sent.
        """
        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example
        mock_start.return_value = None
        mock_is_alive.return_value = True
        mock_init_proc.return_value = None
        mock_push_and_send.return_value = None

        self.test_manager._create_and_start_alerter_processes()

        mock_push_and_send.assert_not_called()
        mock_init_proc.assert_not_called()
        mock_start.assert_not_called()

    @freeze_time("2012-01-01")
    @mock.patch.object(RabbitMQApi, 'basic_ack')
    @mock.patch.object(SubstrateAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    def test_process_configs_if_non_empty_configs_received(
            self, mock_push_and_send, mock_ack) -> None:
        """
        In this test we will check that if non-empty configs are received, the
        process_configs function stores the received configs and sends a reset
        alert
        """
        mock_ack.return_value = None
        mock_push_and_send.return_value = None

        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(routing_key=self.routing_key)
        body = bytes(json.dumps(self.received_configs), 'utf-8')
        properties = pika.spec.BasicProperties()

        self.test_manager._process_configs(blocking_channel, method_chains,
                                           properties, body)

        expected_alert_1 = ComponentResetAlert(
            SUBSTRATE_NODE_ALERTER_NAME, datetime.now().timestamp(),
            SubstrateNodeAlerter.__name__, self.parent_id, self.chain_name
        )
        expected_alert_2 = ComponentResetAlert(
            SUBSTRATE_NETWORK_ALERTER_NAME, datetime.now().timestamp(),
            SubstrateNetworkAlerter.__name__, self.parent_id, self.chain_name
        )

        self.assertEqual(
            self.node_config_expected,
            self.test_manager.node_alerts_config_factory.configs)
        self.assertEqual(
            self.network_config_expected,
            self.test_manager.network_alerts_config_factory.configs)
        expected_calls = [
            call(expected_alert_1.alert_data,
                 SUBSTRATE_NODE_ALERT_ROUTING_KEY),
            call(expected_alert_2.alert_data,
                 SUBSTRATE_NETWORK_ALERT_ROUTING_KEY),
        ]
        mock_push_and_send.assert_has_calls(expected_calls, True)
        mock_ack.assert_called_once()

    @mock.patch.object(RabbitMQApi, 'basic_ack')
    @mock.patch.object(SubstrateAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    def test_process_configs_if_received_empty_configs(
            self, mock_push_and_send, mock_ack) -> None:
        """
        In this test we will check that if empty configs are received, the
        process_configs function removes the already stored config and does not
        send a reset alert.
        """
        mock_ack.return_value = None
        mock_push_and_send.return_value = None

        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(routing_key=self.routing_key)
        body = bytes(json.dumps({}), 'utf-8')
        properties = pika.spec.BasicProperties()
        parsed_routing_key = self.routing_key.split('.')

        # Store configs directly since we need to test their removal
        self.test_manager.node_alerts_config_factory.add_new_config(
            self.chain_name, self.received_configs)
        self.test_manager.network_alerts_config_factory.add_new_config(
            self.chain_name, self.received_configs)

        # Make sure that the configs were added
        self.assertEqual(
            self.node_config_expected,
            self.test_manager.node_alerts_config_factory.configs)
        self.assertEqual(
            self.network_config_expected,
            self.test_manager.network_alerts_config_factory.configs)

        # Send an empty config for the same chain
        self.test_manager._process_configs(blocking_channel, method_chains,
                                           properties, body)
        expected_configs = {}
        self.assertEqual(
            expected_configs,
            self.test_manager.node_alerts_config_factory.configs)
        self.assertEqual(
            expected_configs,
            self.test_manager.network_alerts_config_factory.configs)
        mock_push_and_send.assert_not_called()
        mock_ack.assert_called_once()

    @mock.patch.object(QueuingPublisherSubscriberComponent, "_push_to_queue")
    @mock.patch.object(SubstrateAlertersManager, "_send_data")
    def test_push_latest_data_to_queue_and_send_pushes_correctly_and_sends(
            self, mock_send_data, mock_push) -> None:
        mock_send_data.return_value = None
        mock_push.return_value = None
        test_dict = {'test_key': 'test_val'}

        self.test_manager._push_latest_data_to_queue_and_send(
            test_dict, self.routing_key)

        mock_push.assert_called_once_with(
            data=test_dict, exchange=ALERT_EXCHANGE,
            routing_key=self.routing_key,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True
        )
        mock_send_data.assert_called_once()
