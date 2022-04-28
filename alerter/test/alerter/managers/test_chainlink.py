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
from src.alerter.alerter_starters import (start_chainlink_node_alerter,
                                          start_chainlink_contract_alerter)
from src.alerter.alerters.contract.chainlink import ChainlinkContractAlerter
from src.alerter.alerters.node.chainlink import ChainlinkNodeAlerter
from src.alerter.alerts.internal_alerts import ComponentResetAlert
from src.alerter.managers.chainlink import ChainlinkAlertersManager
from src.configs.alerts.contract.chainlink import (
    ChainlinkContractAlertsConfig)
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.configs.factory.alerts.chainlink_alerts import (
    ChainlinkContractAlertsConfigsFactory, ChainlinkNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (CHAINLINK_NODE_ALERTER_NAME,
                                       CHAINLINK_CONTRACT_ALERTER_NAME)
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE, ALERT_EXCHANGE,
    CL_ALERTERS_MAN_HB_QUEUE_NAME, CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
    PING_ROUTING_KEY, CL_ALERTS_CONFIGS_ROUTING_KEY,
    HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY, CL_NODE_ALERT_ROUTING_KEY,
    CL_CONTRACT_ALERT_ROUTING_KEY)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from test.test_utils.utils import (
    delete_exchange_if_exists, delete_queue_if_exists, disconnect_from_rabbit,
    connect_to_rabbit, infinite_fn
)


class TestChainlinkAlertersManager(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy objects
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.manager_name = 'test_chainlink_alerters_manager'
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
        self.routing_key_1 = 'chains.chainlink.matic.alerts_config'
        self.parent_id_1 = "chain_name_d21d780d-92cb-42de-a7c1-11b751654510"

        self.config_1 = {
            "1": {
                "name": "head_tracker_current_head",
                "parent_id": self.parent_id_1,
            },
            "2": {
                "name": "head_tracker_heads_received_total",
                "parent_id": self.parent_id_1,
            },
            "3": {
                "name": "max_unconfirmed_blocks",
                "parent_id": self.parent_id_1,
            },
            "4": {
                "name": "process_start_time_seconds",
                "parent_id": self.parent_id_1,
            },
            "5": {
                "name": "tx_manager_gas_bump_exceeds_limit_total",
                "parent_id": self.parent_id_1,
            },
            "6": {
                "name": "unconfirmed_transactions",
                "parent_id": self.parent_id_1,
            },
            "7": {
                "name": "run_status_update_total",
                "parent_id": self.parent_id_1,
            },
            "8": {
                "name": "eth_balance_amount",
                "parent_id": self.parent_id_1,
            },
            "9": {
                "name": "eth_balance_amount_increase",
                "parent_id": self.parent_id_1,
            },
            "10": {
                "name": "node_is_down",
                "parent_id": self.parent_id_1,
            },
            "11": {
                "name": "price_feed_not_observed",
                "parent_id": self.parent_id_1,
            },
            "12": {
                "name": "price_feed_deviation",
                "parent_id": self.parent_id_1,
            },
            "13": {
                "name": "consensus_failure",
                "parent_id": self.parent_id_1,
            },
            "14": {
                "name": "error_retrieving_chainlink_contract_data",
                "parent_id": self.parent_id_1,
            },
        }

        self.test_manager = ChainlinkAlertersManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)
        self.alerter_process_dict_example = {
            CHAINLINK_NODE_ALERTER_NAME: self.dummy_process_1,
            CHAINLINK_CONTRACT_ALERTER_NAME: self.dummy_process_2,
        }
        self.node_alerts_config_factory = ChainlinkNodeAlertsConfigsFactory()
        self.contract_alerts_config_factory = \
            ChainlinkContractAlertsConfigsFactory()
        self.configs_processor_helper_example = {
            CHAINLINK_NODE_ALERTER_NAME: {
                'alerterClass': ChainlinkNodeAlerter,
                'configsClass': ChainlinkNodeAlertsConfig,
                'factory': self.node_alerts_config_factory,
                'routing_key': CL_NODE_ALERT_ROUTING_KEY,
                'starter': start_chainlink_node_alerter,
            },
            CHAINLINK_CONTRACT_ALERTER_NAME: {
                'alerterClass': ChainlinkContractAlerter,
                'configsClass': ChainlinkContractAlertsConfig,
                'factory': self.contract_alerts_config_factory,
                'routing_key': CL_CONTRACT_ALERT_ROUTING_KEY,
                'starter': start_chainlink_contract_alerter,
            },
        }

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)

        delete_queue_if_exists(
            self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               CL_ALERTERS_MAN_HB_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
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
        self.contract_alerts_config_factory = None
        self.alerter_process_dict_example = None
        self.test_manager = None
        self.configs_processor_helper_example = None

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
        # Test for the contract alerts config factory
        self.test_manager._contracts_alerts_config_factory = \
            self.contract_alerts_config_factory
        self.assertEqual(self.contract_alerts_config_factory,
                         self.test_manager.contracts_alerts_config_factory)

        # Test for the node alerts config factory
        self.test_manager._node_alerts_config_factory = \
            self.node_alerts_config_factory
        self.assertEqual(self.node_alerts_config_factory,
                         self.test_manager.node_alerts_config_factory)

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
        self.test_manager.rabbitmq.queue_delete(CL_ALERTERS_MAN_HB_QUEUE_NAME)
        self.test_manager.rabbitmq.queue_delete(
            CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
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

        # Check whether the consuming exchanges and queues have been creating by
        # sending messages with the same routing keys as for the bindings.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=PING_ROUTING_KEY,
            body='test_str', is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE, routing_key=CL_ALERTS_CONFIGS_ROUTING_KEY,
            body='another_test_str', is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)

        # Re-declare queue to get the number of messages, and check that the
        # message received is the message sent
        res = self.test_manager.rabbitmq.queue_declare(
            CL_ALERTERS_MAN_HB_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            CL_ALERTERS_MAN_HB_QUEUE_NAME)
        self.assertEqual('test_str', body.decode())

        res = self.test_manager.rabbitmq.queue_declare(
            CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual('another_test_str', body.decode())

        expected_calls = [
            call(CL_ALERTERS_MAN_HB_QUEUE_NAME, self.test_manager._process_ping,
                 True, False, None),
            call(CL_ALERTERS_MAN_CONFIGS_QUEUE_NAME,
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
        ([True, False], [CHAINLINK_CONTRACT_ALERTER_NAME],),
        ([False, True], [CHAINLINK_NODE_ALERTER_NAME],),
        ([False, False], [CHAINLINK_NODE_ALERTER_NAME,
                          CHAINLINK_CONTRACT_ALERTER_NAME],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(ChainlinkAlertersManager,
                       "_create_and_start_alerter_processes")
    @mock.patch.object(ChainlinkAlertersManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb(
            self, is_alive_side_effect, dead_alerters, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect

        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
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
        ([True, False], True,),
        ([False, True], True,),
        ([False, False], True,),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(ChainlinkAlertersManager,
                       "_create_and_start_alerter_processes")
    @mock.patch.object(ChainlinkAlertersManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes_correctly(
            self, is_alive_side_effect, expected_restart, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect

        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method, properties,
                                        body)

        if expected_restart:
            mock_create_and_start.assert_called_once()
        else:
            mock_create_and_start.assert_not_called()

    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(ChainlinkAlertersManager, "_send_heartbeat")
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_send_hb, mock_is_alive) -> None:
        mock_is_alive.side_effect = self.test_exception
        mock_send_hb.return_value = None
        self.test_manager._alerter_process_dict = \
            self.alerter_process_dict_example

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
    @mock.patch.object(ChainlinkAlertersManager, "_send_heartbeat")
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

    @parameterized.expand([
        ({}, False,),
        ('self.alerter_process_dict_example', True)
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(ChainlinkAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_alerter_processes_if_processes_not_running(
            self, state, state_is_str, mock_start, mock_push_and_send) -> None:
        """
        In this test we will check that the required processes are created and
        started, and that reset alerts are sent. We will perform this test for
        both when the function is executed for the first time (empty state), and
        for when the process is dead (state non empty but dummy process not
        running by default)
        """
        self.test_manager._alerter_process_dict = eval(
            state) if state_is_str else state
        mock_start.return_value = None
        mock_push_and_send.return_value = None

        self.test_manager._create_and_start_alerter_processes()

        node_alerter_process = self.test_manager.alerter_process_dict[
            CHAINLINK_NODE_ALERTER_NAME]
        contract_alerter_process = self.test_manager.alerter_process_dict[
            CHAINLINK_CONTRACT_ALERTER_NAME]

        # Check that the processes were created correctly
        self.assertTrue(node_alerter_process.daemon)
        self.assertEqual(1, len(node_alerter_process._args))
        self.assertEqual(self.test_manager.node_alerts_config_factory,
                         node_alerter_process._args[0])
        self.assertEqual(start_chainlink_node_alerter,
                         node_alerter_process._target)

        self.assertTrue(contract_alerter_process.daemon)
        self.assertEqual(1, len(contract_alerter_process._args))
        self.assertEqual(self.test_manager.contracts_alerts_config_factory,
                         contract_alerter_process._args[0])
        self.assertEqual(start_chainlink_contract_alerter,
                         contract_alerter_process._target)

        # Check that the processes were started
        self.assertEqual(2, mock_start.call_count)

        # Check that 2 reset alerts were sent
        expected_alert_1 = ComponentResetAlert(
            CHAINLINK_NODE_ALERTER_NAME, datetime.now().timestamp(),
            ChainlinkNodeAlerter.__name__)
        expected_alert_2 = ComponentResetAlert(
            CHAINLINK_CONTRACT_ALERTER_NAME, datetime.now().timestamp(),
            ChainlinkContractAlerter.__name__)
        expected_calls = [
            call(expected_alert_1.alert_data, CL_NODE_ALERT_ROUTING_KEY),
            call(expected_alert_2.alert_data, CL_CONTRACT_ALERT_ROUTING_KEY)
        ]
        mock_push_and_send.assert_has_calls(expected_calls, True)

    @mock.patch.object(ChainlinkAlertersManager,
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
    @mock.patch.object(ChainlinkAlertersManager,
                       "_push_latest_data_to_queue_and_send")
    def test_process_configs_if_non_empty_configs_received(
            self, mock_push_and_send, mock_ack) -> None:
        """
        In this test we will check that if non-empty configs are received,
        the process_configs function stores the received configs and sends a
        reset alert
        """
        mock_ack.return_value = None
        mock_push_and_send.return_value = None

        blocking_channel = self.test_manager.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(routing_key=self.routing_key_1)
        body = json.dumps(self.config_1)
        properties = pika.spec.BasicProperties()
        parsed_routing_key = self.routing_key_1.split('.')
        chain_name = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        self.test_manager._process_configs(blocking_channel, method_chains,
                                           properties, body)

        expected_node_configs = {
            chain_name: ChainlinkNodeAlertsConfig(
                parent_id=self.parent_id_1,
                head_tracker_current_head=self.config_1['1'],
                head_tracker_heads_received_total=self.config_1['2'],
                max_unconfirmed_blocks=self.config_1['3'],
                process_start_time_seconds=self.config_1['4'],
                tx_manager_gas_bump_exceeds_limit_total=self.config_1['5'],
                unconfirmed_transactions=self.config_1['6'],
                run_status_update_total=self.config_1['7'],
                eth_balance_amount=self.config_1['8'],
                eth_balance_amount_increase=self.config_1['9'],
                node_is_down=self.config_1['10']
            )
        }
        expected_contract_configs = {
            chain_name: ChainlinkContractAlertsConfig(
                parent_id=self.parent_id_1,
                price_feed_not_observed=self.config_1['11'],
                price_feed_deviation=self.config_1['12'],
                consensus_failure=self.config_1['13'],
            )
        }
        expected_alert_1 = ComponentResetAlert(
            CHAINLINK_NODE_ALERTER_NAME, datetime.now().timestamp(),
            ChainlinkNodeAlerter.__name__, self.parent_id_1, chain_name
        )
        expected_alert_2 = ComponentResetAlert(
            CHAINLINK_CONTRACT_ALERTER_NAME, datetime.now().timestamp(),
            ChainlinkContractAlerter.__name__, self.parent_id_1, chain_name
        )

        self.assertEqual(expected_node_configs,
                         self.test_manager.node_alerts_config_factory.configs)
        self.assertEqual(
            expected_contract_configs,
            self.test_manager.contracts_alerts_config_factory.configs)
        expected_calls = [
            call(expected_alert_1.alert_data, CL_NODE_ALERT_ROUTING_KEY),
            call(expected_alert_2.alert_data, CL_CONTRACT_ALERT_ROUTING_KEY)
        ]
        mock_push_and_send.assert_has_calls(expected_calls, True)
        mock_ack.assert_called_once()

    @mock.patch.object(RabbitMQApi, 'basic_ack')
    @mock.patch.object(ChainlinkAlertersManager,
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
        method_chains = pika.spec.Basic.Deliver(routing_key=self.routing_key_1)
        body = json.dumps({})
        properties = pika.spec.BasicProperties()
        parsed_routing_key = self.routing_key_1.split('.')
        chain_name = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        # Store configs directly since we need to test their removal
        self.test_manager.node_alerts_config_factory.add_new_config(
            chain_name, self.config_1)
        self.test_manager.contracts_alerts_config_factory.add_new_config(
            chain_name, self.config_1)

        # Make sure that the configs were added
        expected_node_configs = {
            chain_name: ChainlinkNodeAlertsConfig(
                parent_id=self.parent_id_1,
                head_tracker_current_head=self.config_1['1'],
                head_tracker_heads_received_total=self.config_1['2'],
                max_unconfirmed_blocks=self.config_1['3'],
                process_start_time_seconds=self.config_1['4'],
                tx_manager_gas_bump_exceeds_limit_total=self.config_1['5'],
                unconfirmed_transactions=self.config_1['6'],
                run_status_update_total=self.config_1['7'],
                eth_balance_amount=self.config_1['8'],
                eth_balance_amount_increase=self.config_1['9'],
                node_is_down=self.config_1['10']
            )
        }
        expected_contract_configs = {
            chain_name: ChainlinkContractAlertsConfig(
                parent_id=self.parent_id_1,
                price_feed_not_observed=self.config_1['11'],
                price_feed_deviation=self.config_1['12'],
                consensus_failure=self.config_1['13'],
            )
        }
        self.assertEqual(expected_node_configs,
                         self.test_manager.node_alerts_config_factory.configs)
        self.assertEqual(
            expected_contract_configs,
            self.test_manager.contracts_alerts_config_factory.configs)

        # Send an empty config for the same chain
        self.test_manager._process_configs(blocking_channel, method_chains,
                                           properties, body)
        expected_configs = {}
        self.assertEqual(expected_configs,
                         self.test_manager.node_alerts_config_factory.configs)
        self.assertEqual(
            expected_configs,
            self.test_manager.contracts_alerts_config_factory.configs)
        mock_push_and_send.assert_not_called()
        mock_ack.assert_called_once()

    @mock.patch.object(QueuingPublisherSubscriberComponent, "_push_to_queue")
    @mock.patch.object(ChainlinkAlertersManager, "_send_data")
    def test_push_latest_data_to_queue_and_send_pushes_correctly_and_sends(
            self, mock_send_data, mock_push) -> None:
        mock_send_data.return_value = None
        mock_push.return_value = None
        test_dict = {'test_key': 'test_val'}

        self.test_manager._push_latest_data_to_queue_and_send(
            test_dict, self.routing_key_1)

        mock_push.assert_called_once_with(
            data=test_dict, exchange=ALERT_EXCHANGE,
            routing_key=self.routing_key_1,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True
        )
        mock_send_data.assert_called_once()
