import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from http.client import IncompleteRead
from typing import Any
from unittest import mock
from unittest.mock import call

import pika
from freezegun import freeze_time
from parameterized import parameterized
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError
from web3 import Web3
from web3.contract import ContractFunction, ContractEvent
from web3.eth import Eth
from web3.exceptions import ContractLogicError

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.contracts.evm import (EVMContractsMonitor,
                                        _WEI_WATCHERS_RETRIEVAL_TIME_PERIOD,
                                        _PROMETHEUS_RETRIEVAL_TIME_PERIOD)
from src.utils import env
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          RAW_DATA_EXCHANGE,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          EVM_CONTRACTS_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (PANICException,
                                  ComponentNotGivenEnoughDataSourcesException,
                                  MetricNotFoundException,
                                  CouldNotRetrieveContractsException,
                                  NoSyncedDataSourceWasAccessibleException)
from test.utils.utils import (connect_to_rabbit, delete_queue_if_exists,
                              delete_exchange_if_exists, disconnect_from_rabbit)


class TestEventsClass:
    def __init__(self, events: Any):
        self._events = events

    def get_all_entries(self):
        return self._events


class TestEVMContractsMonitor(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.weiwatchers_url = 'test_weiwatchers_url'
        self.evm_nodes = ['url1', 'url2', 'url3']
        self.node_id_1 = 'test_node_id_1'
        self.parent_id_1 = 'test_parent_id_1'
        self.node_name_1 = 'test_node_1'
        self.monitor_node_1 = True
        self.monitor_prometheus_1 = True
        self.node_prometheus_urls_1 = ['url4', 'url5', 'url6']
        self.node_id_2 = 'test_node_id_2'
        self.parent_id_2 = 'test_parent_id_2'
        self.node_name_2 = 'test_node_2'
        self.monitor_node_2 = True
        self.monitor_prometheus_2 = True
        self.node_prometheus_urls_2 = ['url7', 'url8', 'url9']
        self.routing_key = 'test_routing_key'
        self.test_data_str = 'test data'
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.test_queue_name = 'Test Queue'
        self.eth_address_1 = "0x4562845f37813a201b9ddb52e57a902659b7ae6a"
        self.retrieved_prom_data_1 = {
            'eth_balance': {
                '{"account": "0x4562845f37813a201b9ddb52e57a902659b7ae6a"}':
                    26.043292035081947
            },
        }
        self.eth_address_2 = "0x2607e6f021922a5483d64935f87e15ea797fe8d4"
        self.retrieved_prom_data_2 = {
            'eth_balance': {
                '{"account": "0x2607e6f021922a5483d64935f87e15ea797fe8d4"}':
                    45.043292035081947
            },
        }
        self.node_eth_address_example = {
            self.node_id_1: self.eth_address_1,
            self.node_id_2: self.eth_address_2
        }
        self.proxy_address_1 = '0xFDF9EB5fafc11Efa65f6FD144898da39a7920Ae8'
        self.proxy_address_2 = '0x678df3415fc31947dA4324eC63212874be5a82f8'
        self.proxy_address_3 = '0x824b4A1A0443609A2ADd94a700b770FA5bE31287'
        self.proxy_address_4 = '0x7969b8018928F3d9faaE9AC71744ed2C1486536F'
        self.contract_address_1 = '0x05883D24a5712c04f1b843C4839dC93073A56Ef4'
        self.contract_address_2 = '0x12A6B73A568f8DC3D24DA1654079343f18f69236'
        self.contract_address_3 = '0x01A1F73b1f4726EB6EB189FFA5CBB91AF8E14025'
        self.contract_address_4 = '0x02F878A94a1AE1B15705aCD65b5519A46fe3517e'
        self.retrieved_contracts_example = [
            {
                'contractAddress': self.contract_address_1,
                'proxyAddress': self.proxy_address_1,
                'contractVersion': 3,
            },
            {
                'contractAddress': self.contract_address_2,
                'proxyAddress': self.proxy_address_2,
                'contractVersion': 3,
            },
            {
                'contractAddress': self.contract_address_3,
                'proxyAddress': self.proxy_address_3,
                'contractVersion': 4,
            },
            {
                'contractAddress': self.contract_address_4,
                'proxyAddress': self.proxy_address_4,
                'contractVersion': 4,
            }
        ]
        self.contract_1_oracles = [
            self.eth_address_1, self.eth_address_2, 'irrelevant_address_1',
            'irrelevant_address_2']
        self.contract_2_oracles = [
            self.eth_address_1, 'irrelevant_address_1', 'irrelevant_address_2']
        self.contract_3_transmitters = [
            self.eth_address_2, self.eth_address_1, 'irrelevant_address_1',
            'irrelevant_address_2'
        ]
        self.contract_4_transmitters = [
            self.eth_address_2, 'irrelevant_address_1', 'irrelevant_address_2'
        ]
        self.filtered_contracts_example = {
            self.node_id_1: {
                'v3': [self.proxy_address_1, self.proxy_address_2],
                'v4': [self.proxy_address_3]
            },
            self.node_id_2: {
                'v3': [self.proxy_address_1],
                'v4': [self.proxy_address_3, self.proxy_address_4]
            }
        }
        self.current_block = 1000
        self.current_round = 95
        self.answer = 345783563784
        self.started_at = 4545654
        self.updated_at = 4545674
        self.answered_in_round = 95
        self.withdrawable_payment = 4356546893693
        self.test_parent_id = 'test_parent_id'

        # Dummy objects
        self.test_exception = PANICException('test_exception', 1)
        self.node_config_1 = ChainlinkNodeConfig(
            self.node_id_1, self.parent_id_1, self.node_name_1,
            self.monitor_node_1, self.monitor_prometheus_1,
            self.node_prometheus_urls_1)
        self.node_config_2 = ChainlinkNodeConfig(
            self.node_id_2, self.parent_id_2, self.node_name_2,
            self.monitor_node_2, self.monitor_prometheus_2,
            self.node_prometheus_urls_2)
        self.test_monitor = EVMContractsMonitor(
            self.monitor_name, self.weiwatchers_url, self.evm_nodes,
            [self.node_config_1, self.node_config_2], self.dummy_logger,
            self.monitoring_period, self.rabbitmq)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_monitor.rabbitmq)
        delete_queue_if_exists(self.test_monitor.rabbitmq, self.test_queue_name)
        delete_exchange_if_exists(self.test_monitor.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_monitor.rabbitmq, RAW_DATA_EXCHANGE)
        disconnect_from_rabbit(self.test_monitor.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_exception = None
        self.node_config_1 = None
        self.node_config_2 = None
        self.test_monitor = None

    def test_str_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, str(self.test_monitor))

    def test_monitor_period_returns_monitor_period(self) -> None:
        self.assertEqual(self.monitoring_period,
                         self.test_monitor.monitor_period)

    def test_monitor_name_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.monitor_name)

    def test_node_configs_returns_node_configs(self) -> None:
        self.assertEqual([self.node_config_1, self.node_config_2],
                         self.test_monitor.node_configs)

    def test_evm_node_w3_interface_returns_evm_node_w3_interface(self) -> None:
        self.test_monitor._evm_node_w3_interface = self.test_data_dict
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.evm_node_w3_interface)

    def test_contracts_url_returns_wei_watchers_url(self) -> None:
        self.assertEqual(self.weiwatchers_url, self.test_monitor.contracts_url)

    def test_node_eth_address_returns_node_eth_address(self) -> None:
        self.test_monitor._node_eth_address = self.test_data_dict
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.node_eth_address)

    def test_contracts_data_returns_contracts_data(self) -> None:
        self.test_monitor._contracts_data = self.test_data_dict
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.contracts_data)

    def test_node_contracts_returns_node_contracts(self) -> None:
        self.test_monitor._node_contracts = self.test_data_dict
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.node_contracts)

    def test_last_block_monitored_returns_last_block_monitored(self) -> None:
        self.test_monitor._last_block_monitored = self.test_data_dict
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.last_block_monitored)

    def test_wei_watchers_retrieval_limiter_returns_weiwatchers_limiter(
            self) -> None:
        self.test_monitor._wei_watchers_retrieval_limiter = self.test_data_dict
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.wei_watchers_retrieval_limiter)

    def test_eth_address_retrieval_limiter_returns_eth_address_limiter(
            self) -> None:
        self.test_monitor._eth_address_retrieval_limiter = self.test_data_dict
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.eth_address_retrieval_limiter)

    def test_EVMContractsMonitor_init_raises_exception_if_nodes_lists_empty(
            self) -> None:
        """
        In this test we will check that if the list of evm nodes or the list
        of chainlink node configs is empty, then a
        ComponentNotGivenEnoughDataSourcesException is raised by the __init__
        function of the monitor.
        """

        # If the list of evm nodes is empty
        self.assertRaises(
            ComponentNotGivenEnoughDataSourcesException, EVMContractsMonitor,
            self.monitor_name, self.weiwatchers_url, [],
            [self.node_config_1, self.node_config_2], self.dummy_logger,
            self.monitoring_period, self.rabbitmq)

        # If the list of node configs is empty
        self.assertRaises(
            ComponentNotGivenEnoughDataSourcesException, EVMContractsMonitor,
            self.monitor_name, self.weiwatchers_url, self.evm_nodes,
            [], self.dummy_logger, self.monitoring_period, self.rabbitmq)

    def test_EVMContractsMonitor_init_creates_w3_interfaces_for_each_evm_node(
            self) -> None:
        test_monitor = EVMContractsMonitor(
            self.monitor_name, self.weiwatchers_url, self.evm_nodes,
            [self.node_config_1, self.node_config_2], self.dummy_logger,
            self.monitoring_period, self.rabbitmq)

        for evm_node_url in self.evm_nodes:
            self.assertTrue(evm_node_url in test_monitor.evm_node_w3_interface)
            value = test_monitor.evm_node_w3_interface[evm_node_url]
            self.assertIsInstance(value, Web3)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges have not already been declared
        self.rabbitmq.connect()
        self.rabbitmq.exchange_delete(RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_monitor._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open and
        # that the delivery confirmation variable is set.
        self.assertTrue(self.test_monitor.rabbitmq.is_connected)
        self.assertTrue(self.test_monitor.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_monitor.rabbitmq.channel._delivery_confirmation)

        # Check whether the exchange has been creating by sending messages to
        # it. If this fails an exception is raised hence the test fails.
        self.test_monitor.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE, routing_key=self.routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)
        self.test_monitor.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=self.routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

    @mock.patch.object(EVMContractsMonitor, "_process_retrieved_data")
    @mock.patch.object(EVMContractsMonitor, "_process_error")
    def test_process_data_calls_process_error_on_retrieval_error(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_error.return_value = self.test_data_dict

        self.test_monitor._process_data(True, [self.test_exception], [])

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        self.assertEqual(1, mock_process_error.call_count)
        self.assertEqual(0, mock_process_retrieved_data.call_count)

    @mock.patch.object(EVMContractsMonitor, "_process_retrieved_data")
    @mock.patch.object(EVMContractsMonitor, "_process_error")
    def test_process_data_calls_process_retrieved_data_on_retrieval_success(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_retrieved_data.return_value = self.test_data_dict

        self.test_monitor._process_data(False, [], [self.test_data_dict,
                                                    self.node_config_1])

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        self.assertEqual(0, mock_process_error.call_count)
        self.assertEqual(1, mock_process_retrieved_data.call_count)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        self.test_monitor._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
        self.test_monitor._send_heartbeat(self.test_heartbeat)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    @mock.patch("src.monitors.contracts.evm.get_json")
    def test_get_chain_contracts_calls_and_returns_get_json_correctly(
            self, mock_get_json) -> None:
        mock_get_json.return_value = self.test_data_str
        actual_return = self.test_monitor._get_chain_contracts()
        mock_get_json.assert_called_once_with(
            self.weiwatchers_url, self.dummy_logger, None, True)
        self.assertEqual(self.test_data_str, actual_return)

    def test_store_chain_contracts_stores_contracts_data(self) -> None:
        self.assertEqual([], self.test_monitor.contracts_data)
        self.test_monitor._store_chain_contracts([self.test_data_dict])
        self.assertEqual([self.test_data_dict],
                         self.test_monitor.contracts_data)

    @mock.patch("src.monitors.contracts.evm.get_prometheus_metrics_data")
    def test_get_nodes_eth_address_returns_correctly_if_no_errors(
            self, mock_get_prom_metrics_data) -> None:
        """
        In this test we will assume that the prometheus metrics will be returned
        correctly for each node, assuming we have 2 node configs.
        """
        mock_get_prom_metrics_data.side_effect = [self.retrieved_prom_data_1,
                                                  self.retrieved_prom_data_2]
        actual = self.test_monitor._get_nodes_eth_address()
        expected = (
            {
                self.node_id_1: self.eth_address_1,
                self.node_id_2: self.eth_address_2,
            }, False
        )
        self.assertEqual(expected, actual)

    @parameterized.expand([
        (ReqConnectionError('test'),), (ReadTimeout('test'),),
        (InvalidURL('test'),), (InvalidSchema('test'),),
        (MissingSchema('test'),), (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),), (ProtocolError('test'),),
        (MetricNotFoundException('test_metric', 'test_endpoint'),),
    ])
    @mock.patch("src.monitors.contracts.evm.get_prometheus_metrics_data")
    def test_get_nodes_eth_address_returns_correctly_if_prom_retrieval_errors(
            self, error_instance, mock_get_prom_metrics_data) -> None:
        """
        This test will be performed for 3 scenarios, for when the first
        retrieval only errors, for when the second retrieval only errors and
        for when all retrievals error. Note, different errors will be tested by
        parameterized expand, these errors are the only recognizable errors by
        the function.
        """
        # Only second retrieval errors
        mock_get_prom_metrics_data.side_effect = [
            self.retrieved_prom_data_1, error_instance] \
            if type(error_instance) == MetricNotFoundException \
            else [self.retrieved_prom_data_1, error_instance, error_instance,
                  error_instance]
        actual = self.test_monitor._get_nodes_eth_address()
        expected = ({self.node_id_1: self.eth_address_1}, True)
        self.assertEqual(expected, actual)
        mock_get_prom_metrics_data.reset_mock()

        # Only first retrieval errors
        mock_get_prom_metrics_data.side_effect = [
            error_instance, self.retrieved_prom_data_2] \
            if type(error_instance) == MetricNotFoundException \
            else [error_instance, error_instance, error_instance,
                  self.retrieved_prom_data_2]
        actual = self.test_monitor._get_nodes_eth_address()
        expected = ({self.node_id_2: self.eth_address_2}, True)
        self.assertEqual(expected, actual)
        mock_get_prom_metrics_data.reset_mock()

        # Both retrievals error
        mock_get_prom_metrics_data.side_effect = [
            error_instance, error_instance] \
            if type(error_instance) == MetricNotFoundException \
            else [error_instance, error_instance, error_instance,
                  error_instance, error_instance, error_instance]
        actual = self.test_monitor._get_nodes_eth_address()
        expected = ({}, True)
        self.assertEqual(expected, actual)

    def test_store_nodes_eth_addresses_stores_node_eth_address(self) -> None:
        self.assertEqual({}, self.test_monitor.node_eth_address)
        self.test_monitor._store_nodes_eth_addresses(self.test_data_dict)
        self.assertEqual(self.test_data_dict,
                         self.test_monitor.node_eth_address)

    @mock.patch.object(Eth, 'is_syncing')
    @mock.patch.object(Web3, 'isConnected')
    def test_select_node_selects_first_connected_and_synced_node_it_finds(
            self, mock_is_connected, mock_syncing) -> None:
        """
        In this test we will check that if all nodes are synced and connected,
        then select_node will select the first node it finds
        """
        mock_syncing.return_value = False
        mock_is_connected.return_value = True
        actual = self.test_monitor._select_node()
        self.assertEqual(self.evm_nodes[0], actual)

    @mock.patch.object(Eth, 'is_syncing')
    @mock.patch.object(Web3, 'isConnected')
    def test_select_node_does_not_select_syncing_nodes(
            self, mock_is_connected, mock_syncing) -> None:
        """
        In this test we will set the first two nodes to be syncing, and the
        last node as synced to check that the third node is selected. Note, all
        nodes are set to be connected.
        """
        mock_syncing.side_effect = [True, True, False]
        mock_is_connected.return_value = True
        actual = self.test_monitor._select_node()
        self.assertEqual(self.evm_nodes[2], actual)

    @mock.patch.object(Eth, 'is_syncing')
    @mock.patch.object(Web3, 'isConnected')
    def test_select_node_does_not_select_disconnected_nodes(
            self, mock_is_connected, mock_syncing) -> None:
        """
        In this test we will set the first two nodes to be disconnected, and the
        last node as connected to check that the third node is selected. Note,
        all nodes will be set as synced.
        """
        mock_syncing.return_value = False
        mock_is_connected.side_effect = [False, False, True]
        actual = self.test_monitor._select_node()
        self.assertEqual(self.evm_nodes[2], actual)

    @parameterized.expand([
        (ReqConnectionError('test'),),
        (ReadTimeout('test'),),
        (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (InvalidURL('test'),),
        (InvalidSchema('test'),),
        (MissingSchema('test'),),
    ])
    @mock.patch.object(Eth, 'is_syncing')
    @mock.patch.object(Web3, 'isConnected')
    def test_select_node_does_not_select_nodes_raising_recognizable_errors(
            self, exception_instance, mock_is_connected, mock_syncing) -> None:
        """
        In this test we will set the first two nodes to return one of the
        recognizable errors above, and the third to be connected and synced,
        to demonstrate that the third node is selected if no recognizable error
        is raised.
        """
        mock_syncing.return_value = False
        mock_is_connected.side_effect = [exception_instance, exception_instance,
                                         True]
        actual = self.test_monitor._select_node()
        self.assertEqual(self.evm_nodes[2], actual)

    @parameterized.expand([
        (ReqConnectionError('test'),),
        (ReadTimeout('test'),),
        (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (InvalidURL('test'),),
        (InvalidSchema('test'),),
        (MissingSchema('test'),),
    ])
    @mock.patch.object(Eth, 'is_syncing')
    @mock.patch.object(Web3, 'isConnected')
    def test_select_node_returns_None_if_no_node_satisfies_the_requirements(
            self, exception_instance, mock_is_connected, mock_syncing) -> None:
        """
        In this test we will check that if neither node is connected, synced,
        and does not raise errors, then select_node returns None. Note, we will
        set the first node to be disconnected, the second to be syncing and the
        third to raise an error.
        """
        mock_syncing.return_value = True
        mock_is_connected.side_effect = [False, True, exception_instance]
        actual = self.test_monitor._select_node()
        self.assertEqual(None, actual)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_filter_contracts_by_node_filters_correctly(
            self, mock_to_checksum, mock_call) -> None:
        """
        In this test we we assume that the data retrieved from the chain is the
        one declared in the setUp function. This is used to check if contracts
        are filtered according to which nodes are participating on them.
        """
        self.test_monitor._node_eth_address = self.node_eth_address_example
        self.test_monitor._contracts_data = self.retrieved_contracts_example
        mock_to_checksum.side_effect = [self.eth_address_1, self.eth_address_2]
        mock_call.side_effect = [
            self.contract_1_oracles, self.contract_2_oracles,
            self.contract_3_transmitters, self.contract_4_transmitters,
            self.contract_1_oracles, self.contract_2_oracles,
            self.contract_3_transmitters, self.contract_4_transmitters]

        actual = self.test_monitor._filter_contracts_by_node(self.evm_nodes[0])
        self.assertEqual(self.filtered_contracts_example, actual)

    def test_store_node_contracts_stores_node_contracts(self) -> None:
        self.assertEqual({}, self.test_monitor.node_contracts)
        self.test_monitor._store_node_contracts(self.filtered_contracts_example)
        self.assertEqual(self.filtered_contracts_example,
                         self.test_monitor.node_contracts)

    def test_get_v3_data_returns_empty_dict_if_node_id_was_not_filtered(
            self) -> None:
        """
        This scenario could occur if some recognized error was raised while
        getting the eth address of a node, resulting into that node to not be
        included in filtering.
        """
        selected_node = self.evm_nodes[0]
        actual = self.test_monitor._get_v3_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_1, self.node_id_1)
        self.assertEqual({}, actual)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v3_data_creates_filter_correctly_first_time_round(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        In this test we will check that the create_filter function which
        retrieves round events is called correctly when called the first time
        (the first block to query is the current). For this test we will use
        the first node, which has 2 v3 contracts associated with it.
        """
        mock_to_checksum.return_value = self.eth_address_1
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([])
        mock_call.side_effect = [
            self.contract_address_1, [
                self.current_block, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
            self.contract_address_2, [
                self.current_block, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        self.test_monitor._get_v3_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_1, self.node_id_1)
        actual_calls = mock_create_filter.call_args_list
        expected_calls = [
            call(fromBlock=self.current_block, toBlock=self.current_block,
                 argument_filters={'oracle': self.eth_address_1}),
            call(fromBlock=self.current_block, toBlock=self.current_block,
                 argument_filters={'oracle': self.eth_address_1})
        ]
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v3_data_calls_filter_correctly_second_time_round(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        In this test we will check that the create_filter function which
        retrieves round events is called correctly when called the second time
        (the first block to query is + 1 last monitored). We will automate this
        scenario by pre-setting self.last_block_monitored. For this test we will
        use the first node, which has 2 v3 contracts associated with it.
        """
        self.test_monitor._last_block_monitored[self.node_id_1] = {}
        self.test_monitor._last_block_monitored[self.node_id_1][
            self.proxy_address_1] = self.current_block - 2
        self.test_monitor._last_block_monitored[self.node_id_1][
            self.proxy_address_2] = self.current_block - 2
        mock_to_checksum.return_value = self.eth_address_1
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([])
        mock_call.side_effect = [
            self.contract_address_1, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
            self.contract_address_2, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        self.test_monitor._get_v3_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_1, self.node_id_1)
        actual_calls = mock_create_filter.call_args_list
        expected_calls = [
            call(fromBlock=self.current_block - 1, toBlock=self.current_block,
                 argument_filters={'oracle': self.eth_address_1}),
            call(fromBlock=self.current_block - 1, toBlock=self.current_block,
                 argument_filters={'oracle': self.eth_address_1})
        ]
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v3_data_return_if_no_rounds_recorded(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        This test covers the scenario where no round answers were submitted
        by the node in-between blocks
        """
        mock_to_checksum.return_value = self.eth_address_1
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([])
        mock_call.side_effect = [
            self.contract_address_1, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
            self.contract_address_2, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_v3_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_1, self.node_id_1)
        expected_return = {
            self.proxy_address_1: {
                'contractVersion': 3,
                'aggregatorAddress': self.contract_address_1,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'withdrawablePayment': self.withdrawable_payment,
                'historicalRounds': []
            },
            self.proxy_address_2: {
                'contractVersion': 3,
                'aggregatorAddress': self.contract_address_2,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'withdrawablePayment': self.withdrawable_payment,
                'historicalRounds': []
            }
        }
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v3_data_return_if_some_rounds_with_consensus_recorded(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        This test covers the scenario where round answers were submitted
        by the node in-between blocks, and a round consensus was reached
        already.
        """
        mock_to_checksum.return_value = self.eth_address_1
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([
            {
                'args': {
                    'round': self.current_round - 1,
                    'submission': self.answer - 10
                }
            },
            {
                'args': {
                    'round': self.current_round - 2,
                    'submission': self.answer - 20
                }
            }
        ])
        mock_call.side_effect = [
            self.contract_address_1, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
            [self.current_round - 1, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 1],
            [self.current_round - 2, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 2],
            self.contract_address_2, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment,
            [self.current_round - 1, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 1],
            [self.current_round - 2, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 2],
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_v3_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_1, self.node_id_1)
        expected_return = {
            self.proxy_address_1: {
                'contractVersion': 3,
                'aggregatorAddress': self.contract_address_1,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'withdrawablePayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round - 1,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 1,
                        'nodeSubmission': self.answer - 10
                    },
                    {
                        'roundId': self.current_round - 2,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 2,
                        'nodeSubmission': self.answer - 20
                    }
                ]
            },
            self.proxy_address_2: {
                'contractVersion': 3,
                'aggregatorAddress': self.contract_address_2,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'withdrawablePayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round - 1,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 1,
                        'nodeSubmission': self.answer - 10
                    },
                    {
                        'roundId': self.current_round - 2,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 2,
                        'nodeSubmission': self.answer - 20
                    }
                ]
            }
        }
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v3_data_return_if_some_rounds_without_consensus_recorded(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        This test covers the scenario where round answers were submitted
        by the node in-between blocks, and a round consensus has not been
        reached yet.
        """
        mock_to_checksum.return_value = self.eth_address_1
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([
            {
                'args': {
                    'round': self.current_round,
                    'submission': self.answer - 10
                },
                'blockNumber': self.current_block
            },
        ])
        mock_call.side_effect = [
            self.contract_address_1, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment, ContractLogicError('test'),
            self.contract_address_2, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.withdrawable_payment, ContractLogicError('test'),
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_v3_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_1, self.node_id_1)
        expected_return = {
            self.proxy_address_1: {
                'contractVersion': 3,
                'aggregatorAddress': self.contract_address_1,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'withdrawablePayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round,
                        'roundAnswer': None,
                        'roundTimestamp': None,
                        'answeredInRound': None,
                        'nodeSubmission': self.answer - 10
                    },
                ]
            },
            self.proxy_address_2: {
                'contractVersion': 3,
                'aggregatorAddress': self.contract_address_2,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'withdrawablePayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round,
                        'roundAnswer': None,
                        'roundTimestamp': None,
                        'answeredInRound': None,
                        'nodeSubmission': self.answer - 10
                    },
                ]
            }
        }
        self.assertEqual(expected_return, actual_return)
        self.assertEqual(self.test_monitor.last_block_monitored[self.node_id_1][
                             self.proxy_address_1], self.current_block - 1)
        self.assertEqual(self.test_monitor.last_block_monitored[self.node_id_1][
                             self.proxy_address_2], self.current_block - 1)

    def test_get_v4_data_returns_empty_dict_if_node_id_was_not_filtered(
            self) -> None:
        """
        This scenario could occur if some recognized error was raised while
        getting the eth address of a node, resulting into that node to not be
        included in filtering.
        """
        selected_node = self.evm_nodes[0]
        actual = self.test_monitor._get_v4_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_2, self.node_id_2)
        self.assertEqual({}, actual)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v4_data_creates_filter_correctly_first_time_round(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        In this test we will check that the create_filter function which
        retrieves round events is called correctly when called the first time
        (the first block to query is the current). For this test we will use
        the second node, which has 2 v4 contracts associated with it.
        """
        mock_to_checksum.return_value = self.eth_address_2
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([])
        mock_call.side_effect = [
            self.contract_address_3, [
                self.current_block, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_3_transmitters, self.withdrawable_payment,
            self.contract_address_4, [
                self.current_block, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_4_transmitters, self.withdrawable_payment,
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        self.test_monitor._get_v4_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_2, self.node_id_2)
        actual_calls = mock_create_filter.call_args_list
        expected_calls = [
            call(fromBlock=self.current_block, toBlock=self.current_block),
            call(fromBlock=self.current_block, toBlock=self.current_block)
        ]
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v4_data_calls_filter_correctly_second_time_round(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        In this test we will check that the create_filter function which
        retrieves round events is called correctly when called the second time
        (the first block to query is + 1 last monitored). We will automate this
        scenario by pre-setting self.last_block_monitored. For this test we will
        use the second node, which has 2 v4 contracts associated with it.
        """
        self.test_monitor._last_block_monitored[self.node_id_2] = {}
        self.test_monitor._last_block_monitored[self.node_id_2][
            self.proxy_address_3] = self.current_block - 2
        self.test_monitor._last_block_monitored[self.node_id_2][
            self.proxy_address_4] = self.current_block - 2
        mock_to_checksum.return_value = self.eth_address_2
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([])
        mock_call.side_effect = [
            self.contract_address_3, [
                self.current_block, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_3_transmitters, self.withdrawable_payment,
            self.contract_address_4, [
                self.current_block, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_4_transmitters, self.withdrawable_payment,
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        self.test_monitor._get_v4_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_2, self.node_id_2)
        actual_calls = mock_create_filter.call_args_list
        expected_calls = [
            call(fromBlock=self.current_block - 1, toBlock=self.current_block),
            call(fromBlock=self.current_block - 1, toBlock=self.current_block)
        ]
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v4_data_return_if_no_rounds_transmitted(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        This test covers the scenario where no round results were transmitted
        yet in-between blocks
        """
        mock_to_checksum.return_value = self.eth_address_2
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([])
        mock_call.side_effect = [
            self.contract_address_3, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_3_transmitters, self.withdrawable_payment,
            self.contract_address_4, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_4_transmitters, self.withdrawable_payment,
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_v4_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_2, self.node_id_2)
        expected_return = {
            self.proxy_address_3: {
                'contractVersion': 4,
                'aggregatorAddress': self.contract_address_3,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'owedPayment': self.withdrawable_payment,
                'historicalRounds': []
            },
            self.proxy_address_4: {
                'contractVersion': 4,
                'aggregatorAddress': self.contract_address_4,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'owedPayment': self.withdrawable_payment,
                'historicalRounds': []
            }
        }
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v4_data_ignores_contracts_if_node_no_longer_participating(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        In this test we will check that if a node is no longer a participant of
        a contract, then it is ignored such that no data is returned for it.
        """
        self.contract_3_transmitters.remove(self.eth_address_2)
        mock_to_checksum.return_value = self.eth_address_2
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([])
        mock_call.side_effect = [
            self.contract_address_3, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_3_transmitters,
            self.contract_address_4, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_4_transmitters, self.withdrawable_payment,
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_v4_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_2, self.node_id_2)
        expected_return = {
            self.proxy_address_4: {
                'contractVersion': 4,
                'aggregatorAddress': self.contract_address_4,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'owedPayment': self.withdrawable_payment,
                'historicalRounds': []
            }
        }
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v4_data_return_if_some_rounds_recorded_and_node_sent_answer(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        This test covers the scenario where round answers were transmitted
        in-between blocks, and the node has submitted an answer.
        """
        mock_to_checksum.return_value = self.eth_address_2
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([
            {
                'args': {
                    'aggregatorRoundId': self.current_round - 1,
                    'observers': b'\x02\x03\x04\x00',
                    'observations': [self.answer - 1, self.answer - 2,
                                     self.answer - 3, self.answer - 10]
                }
            },
            {
                'args': {
                    'aggregatorRoundId': self.current_round - 2,
                    'observers': b'\x02\x03\x04\x00',
                    'observations': [self.answer - 1, self.answer - 2,
                                     self.answer - 3, self.answer - 20]
                }
            }
        ])
        mock_call.side_effect = [
            self.contract_address_3, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_3_transmitters, self.withdrawable_payment,
            [self.current_round - 1, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 1],
            [self.current_round - 2, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 2],
            self.contract_address_4, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_4_transmitters, self.withdrawable_payment,
            [self.current_round - 1, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 1],
            [self.current_round - 2, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 2],
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_v4_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_2, self.node_id_2)
        expected_return = {
            self.proxy_address_3: {
                'contractVersion': 4,
                'aggregatorAddress': self.contract_address_3,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'owedPayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round - 1,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 1,
                        'nodeSubmission': self.answer - 10,
                        'noOfObservations': 4,
                        'noOfTransmitters': 4,
                    },
                    {
                        'roundId': self.current_round - 2,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 2,
                        'nodeSubmission': self.answer - 20,
                        'noOfObservations': 4,
                        'noOfTransmitters': 4,
                    }
                ]
            },
            self.proxy_address_4: {
                'contractVersion': 4,
                'aggregatorAddress': self.contract_address_4,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'owedPayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round - 1,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 1,
                        'nodeSubmission': self.answer - 10,
                        'noOfObservations': 4,
                        'noOfTransmitters': 3,
                    },
                    {
                        'roundId': self.current_round - 2,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 2,
                        'nodeSubmission': self.answer - 20,
                        'noOfObservations': 4,
                        'noOfTransmitters': 3,
                    }
                ]
            }
        }
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(ContractFunction, "call")
    @mock.patch.object(ContractEvent, 'createFilter')
    @mock.patch.object(Eth, 'get_block')
    @mock.patch.object(Web3, 'toChecksumAddress')
    def test_get_v4_data_return_if_some_rounds_recorded_and_no_node_answer(
            self, mock_to_checksum, mock_get_block, mock_create_filter,
            mock_call) -> None:
        """
        This test covers the scenario where round answers were transmitted
        in-between blocks, and the node did not submit its answer.
        """
        mock_to_checksum.return_value = self.eth_address_2
        mock_get_block.return_value = {'number': self.current_block}
        mock_create_filter.return_value = TestEventsClass([
            {
                'args': {
                    'aggregatorRoundId': self.current_round - 1,
                    'observers': b'\x02\x03\x04\x01',
                    'observations': [self.answer - 1, self.answer - 2,
                                     self.answer - 3, self.answer - 10]
                }
            },
            {
                'args': {
                    'aggregatorRoundId': self.current_round - 2,
                    'observers': b'\x02\x03\x04\x01',
                    'observations': [self.answer - 1, self.answer - 2,
                                     self.answer - 3, self.answer - 20]
                }
            }
        ])
        mock_call.side_effect = [
            self.contract_address_3, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_3_transmitters, self.withdrawable_payment,
            [self.current_round - 1, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 1],
            [self.current_round - 2, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 2],
            self.contract_address_4, [
                self.current_round, self.answer, self.started_at,
                self.updated_at, self.answered_in_round],
            self.contract_4_transmitters, self.withdrawable_payment,
            [self.current_round - 1, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 1],
            [self.current_round - 2, self.answer, self.started_at,
             self.updated_at, self.answered_in_round - 2],
        ]
        self.test_monitor._node_contracts = self.filtered_contracts_example
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_v4_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_2, self.node_id_2)
        expected_return = {
            self.proxy_address_3: {
                'contractVersion': 4,
                'aggregatorAddress': self.contract_address_3,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'owedPayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round - 1,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 1,
                        'nodeSubmission': None,
                        'noOfObservations': 4,
                        'noOfTransmitters': 4,
                    },
                    {
                        'roundId': self.current_round - 2,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 2,
                        'nodeSubmission': None,
                        'noOfObservations': 4,
                        'noOfTransmitters': 4,
                    }
                ]
            },
            self.proxy_address_4: {
                'contractVersion': 4,
                'aggregatorAddress': self.contract_address_4,
                'latestRound': self.current_round,
                'latestAnswer': self.answer,
                'latestTimestamp': self.updated_at,
                'answeredInRound': self.answered_in_round,
                'owedPayment': self.withdrawable_payment,
                'historicalRounds': [
                    {
                        'roundId': self.current_round - 1,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 1,
                        'nodeSubmission': None,
                        'noOfObservations': 4,
                        'noOfTransmitters': 3,
                    },
                    {
                        'roundId': self.current_round - 2,
                        'roundAnswer': self.answer,
                        'roundTimestamp': self.updated_at,
                        'answeredInRound': self.answered_in_round - 2,
                        'nodeSubmission': None,
                        'noOfObservations': 4,
                        'noOfTransmitters': 3,
                    }
                ]
            }
        }
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(EVMContractsMonitor, '_get_v4_data')
    @mock.patch.object(EVMContractsMonitor, '_get_v3_data')
    def test_get_data_return(self, mock_get_v3_data, mock_get_v4_data) -> None:
        """
        In this test we will check that the get_data function will return the
        expected data, i.e. v3 contracts data followed by v4 contracts data.
        """
        v3_data = {'v3_data_key': 'v3_data_value'}
        v4_data = {'v4_data_key': 'v4_data_value'}
        mock_get_v3_data.return_value = v3_data
        mock_get_v4_data.return_value = v4_data
        selected_node = self.evm_nodes[0]

        actual_return = self.test_monitor._get_data(
            self.test_monitor.evm_node_w3_interface[selected_node],
            self.eth_address_1, self.node_id_1)
        expected_return = {
            'v3_data_key': 'v3_data_value',
            'v4_data_key': 'v4_data_value'
        }
        self.assertEqual(expected_return, actual_return)

    @freeze_time("2012-01-01")
    def test_process_error_returns_expected_processed_data(self) -> None:
        actual_return = self.test_monitor._process_error(self.test_exception,
                                                         self.test_parent_id)
        expected_return = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'parent_id': self.test_parent_id,
                    'time': datetime.now().timestamp()
                },
                'message': self.test_exception.message,
                'code': self.test_exception.code,
            }
        }
        self.assertEqual(expected_return, actual_return)

    @freeze_time("2012-01-01")
    def test_process_retrieved_data_returns_expected_processed_data(
            self) -> None:
        actual_return = self.test_monitor._process_retrieved_data(
            self.test_data_dict, self.node_config_1)
        expected_return = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config_1.node_name,
                    'node_id': self.node_config_1.node_id,
                    'node_parent_id': self.node_config_1.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': copy.deepcopy(self.test_data_dict),
            }
        }
        self.assertEqual(expected_return, actual_return)

    def test_send_data_sends_data_correctly(self) -> None:
        """
        This test creates a queue which receives messages with the same routing
        key as the ones sent by send_data, and checks that the data is received
        """
        self.test_monitor._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_monitor.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_monitor.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=RAW_DATA_EXCHANGE,
            routing_key=EVM_CONTRACTS_RAW_DATA_ROUTING_KEY)

        self.test_monitor._send_data(self.test_data_dict)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_data_dict, json.loads(body))

    def test_get_node_config_by_node_id_returns_correctly(self) -> None:
        """
        In this test we will check that if a node_config with the given node_id
        is stored in the state, that node_config is returned by the
        get_node_config_by_node_id function. If such a node_config does not
        exist we will check that the function returns None.
        """
        # Test for when a config with the given node_id exists in the state
        actual = self.test_monitor._get_node_config_by_node_id(self.node_id_1)
        self.assertEqual(self.node_config_1, actual)

        # Test for when a config with the given node_id does not exist in the
        # state
        actual = self.test_monitor._get_node_config_by_node_id('bad_id')
        self.assertIsNone(actual)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsMonitor, '_send_heartbeat')
    @mock.patch.object(EVMContractsMonitor, '_send_data')
    @mock.patch.object(EVMContractsMonitor, '_select_node')
    @mock.patch.object(EVMContractsMonitor, '_get_nodes_eth_address')
    @mock.patch.object(EVMContractsMonitor, '_store_chain_contracts')
    @mock.patch.object(EVMContractsMonitor, '_get_chain_contracts')
    def test_monitor_retrieves_data_from_weiwatchers_periodically(
            self, mock_get_chain_contracts, mock_store_chain_contracts,
            mock_get_nodes_eth_address, mock_select_node, mock_send_data,
            mock_send_heartbeat) -> None:
        """
        In this test we will check that wei-watchers data is retrieved
        periodically by the self._monitor fn. In addition to this we will check
        that on start, data is retrieved.
        """
        mock_get_chain_contracts.return_value = self.test_data_dict
        mock_store_chain_contracts.return_value = None
        mock_get_nodes_eth_address.return_value = (None, True)
        mock_select_node.return_value = None
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None
        period = _WEI_WATCHERS_RETRIEVAL_TIME_PERIOD

        # Check that data from wei-watchers is retrieved and stored first time
        # round
        self.test_monitor._monitor()
        mock_get_chain_contracts.assert_called_once()
        mock_store_chain_contracts.assert_called_once_with(self.test_data_dict)
        mock_get_chain_contracts.reset_mock()
        mock_store_chain_contracts.reset_mock()

        # Check that data from wei-watchers is not retrieved if not enough time
        # passes
        self.test_monitor.wei_watchers_retrieval_limiter. \
            _last_time_that_did_task = \
            datetime.fromtimestamp(datetime.now().timestamp() - period + 1)
        self.test_monitor._monitor()
        mock_get_chain_contracts.assert_not_called()
        mock_store_chain_contracts.assert_not_called()
        mock_get_chain_contracts.reset_mock()
        mock_store_chain_contracts.reset_mock()

        # Check that data from wei-watchers is retrieved if enough time passes
        self.test_monitor.wei_watchers_retrieval_limiter. \
            _last_time_that_did_task = \
            datetime.fromtimestamp(datetime.now().timestamp() - period - 1)
        self.test_monitor._monitor()
        mock_get_chain_contracts.assert_called_once()
        mock_store_chain_contracts.assert_called_once_with(self.test_data_dict)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsMonitor, '_send_heartbeat')
    @mock.patch.object(EVMContractsMonitor, '_send_data')
    @mock.patch.object(EVMContractsMonitor, '_select_node')
    @mock.patch.object(EVMContractsMonitor, '_store_nodes_eth_addresses')
    @mock.patch.object(EVMContractsMonitor, '_get_nodes_eth_address')
    @mock.patch.object(EVMContractsMonitor, '_store_chain_contracts')
    @mock.patch.object(EVMContractsMonitor, '_get_chain_contracts')
    def test_monitor_retrieves_nodes_eth_address_periodically(
            self, mock_get_chain_contracts, mock_store_chain_contracts,
            mock_get_nodes_eth_address, mock_store_nodes_eth_addresses,
            mock_select_node, mock_send_data, mock_send_heartbeat) -> None:
        """
        In this test we will check that prometheus data is retrieved
        periodically by the self._monitor fn. In addition to this we will check
        that prometheus data is retrieved on start.
        """
        mock_get_chain_contracts.return_value = None
        mock_store_chain_contracts.return_value = None
        mock_get_nodes_eth_address.return_value = (self.test_data_dict, False)
        mock_store_nodes_eth_addresses.return_value = None
        mock_select_node.return_value = None
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None
        period = _PROMETHEUS_RETRIEVAL_TIME_PERIOD

        # Check that data from prometheus is retrieved and stored first time
        # round
        self.test_monitor._monitor()
        mock_get_nodes_eth_address.assert_called_once()
        mock_store_nodes_eth_addresses.assert_called_once_with(
            self.test_data_dict)
        mock_get_nodes_eth_address.reset_mock()
        mock_store_nodes_eth_addresses.reset_mock()

        # Check that data from prometheus is not retrieved if not enough time
        # passes
        self.test_monitor.eth_address_retrieval_limiter. \
            _last_time_that_did_task = \
            datetime.fromtimestamp(datetime.now().timestamp() - period + 1)
        self.test_monitor._monitor()
        mock_get_nodes_eth_address.assert_not_called()
        mock_store_nodes_eth_addresses.assert_not_called()
        mock_get_nodes_eth_address.reset_mock()
        mock_store_nodes_eth_addresses.reset_mock()

        # Check that data from prometheus is retrieved if enough time passes
        self.test_monitor.eth_address_retrieval_limiter. \
            _last_time_that_did_task = \
            datetime.fromtimestamp(datetime.now().timestamp() - period - 1)
        self.test_monitor._monitor()
        mock_get_nodes_eth_address.assert_called_once()
        mock_store_nodes_eth_addresses.assert_called_once_with(
            self.test_data_dict)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsMonitor, '_send_heartbeat')
    @mock.patch.object(EVMContractsMonitor, '_send_data')
    @mock.patch.object(EVMContractsMonitor, '_select_node')
    @mock.patch.object(EVMContractsMonitor, '_store_nodes_eth_addresses')
    @mock.patch.object(EVMContractsMonitor, '_get_nodes_eth_address')
    @mock.patch.object(EVMContractsMonitor, '_store_chain_contracts')
    @mock.patch.object(EVMContractsMonitor, '_get_chain_contracts')
    def test_monitor_retrieves_prometheus_data_if_previous_retrieval_failed(
            self, mock_get_chain_contracts, mock_store_chain_contracts,
            mock_get_nodes_eth_address, mock_store_nodes_eth_addresses,
            mock_select_node, mock_send_data, mock_send_heartbeat) -> None:
        """
        In this test we will check that if the self._monitor function fails in
        retrieving the full prometheus data, then in the next round it
        re-attempts the retrieval.
        """
        mock_get_chain_contracts.return_value = None
        mock_store_chain_contracts.return_value = None
        mock_get_nodes_eth_address.return_value = (self.test_data_dict, True)
        mock_store_nodes_eth_addresses.return_value = None
        mock_select_node.return_value = None
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None

        # Check that data from prometheus is retrieved and stored first time
        # round
        self.test_monitor._monitor()
        mock_get_nodes_eth_address.assert_called_once()
        mock_store_nodes_eth_addresses.assert_called_once_with(
            self.test_data_dict)
        mock_get_nodes_eth_address.reset_mock()
        mock_store_nodes_eth_addresses.reset_mock()

        # Check that data from prometheus is retrieved again since retrieval
        # has failed
        self.test_monitor._monitor()
        mock_get_nodes_eth_address.assert_called_once()
        mock_store_nodes_eth_addresses.assert_called_once_with(
            self.test_data_dict)
        mock_get_nodes_eth_address.reset_mock()
        mock_store_nodes_eth_addresses.reset_mock()

    @parameterized.expand([
        (ReqConnectionError('test'),), (ReadTimeout('test'),),
        (InvalidURL('test'),), (InvalidSchema('test'),),
        (MissingSchema('test'),), (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),), (ProtocolError('test'),),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsMonitor, '_send_heartbeat')
    @mock.patch.object(EVMContractsMonitor, '_send_data')
    @mock.patch.object(EVMContractsMonitor, '_select_node')
    @mock.patch.object(EVMContractsMonitor, '_store_nodes_eth_addresses')
    @mock.patch.object(EVMContractsMonitor, '_get_nodes_eth_address')
    @mock.patch.object(EVMContractsMonitor, '_store_chain_contracts')
    @mock.patch.object(EVMContractsMonitor, '_get_chain_contracts')
    def test_monitor_processes_and_sends_error_and_hb_if_weiwatchers_exception(
            self, exception, mock_get_chain_contracts,
            mock_store_chain_contracts, mock_get_nodes_eth_address,
            mock_store_nodes_eth_addresses, mock_select_node, mock_send_data,
            mock_send_heartbeat) -> None:
        """
        In this test we will check that if data from wei-watchers could not be
        retrieved, then a CouldNotRetrieveContractsException is processed and
        sent together with a heartbeat.
        """
        mock_get_chain_contracts.side_effect = exception
        mock_store_chain_contracts.return_value = None
        mock_get_nodes_eth_address.return_value = (self.test_data_dict, False)
        mock_store_nodes_eth_addresses.return_value = None
        mock_select_node.return_value = None
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None
        expected_raised_exception = CouldNotRetrieveContractsException(
            self.monitor_name, self.test_monitor.contracts_url)
        expected_processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'parent_id': self.parent_id_1,
                    'time': datetime.now().timestamp()
                },
                'message': expected_raised_exception.message,
                'code': expected_raised_exception.code,
            }
        }
        expected_heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }

        self.test_monitor._monitor()
        mock_send_data.assert_called_once_with(expected_processed_data)
        mock_send_heartbeat.assert_called_once_with(expected_heartbeat)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsMonitor, '_send_heartbeat')
    @mock.patch.object(EVMContractsMonitor, '_send_data')
    @mock.patch.object(EVMContractsMonitor, '_select_node')
    @mock.patch.object(EVMContractsMonitor, '_store_nodes_eth_addresses')
    @mock.patch.object(EVMContractsMonitor, '_get_nodes_eth_address')
    @mock.patch.object(EVMContractsMonitor, '_store_chain_contracts')
    @mock.patch.object(EVMContractsMonitor, '_get_chain_contracts')
    def test_monitor_processes_and_sends_error_and_hb_if_no_evm_node_selected(
            self, mock_get_chain_contracts, mock_store_chain_contracts,
            mock_get_nodes_eth_address, mock_store_nodes_eth_addresses,
            mock_select_node, mock_send_data, mock_send_heartbeat) -> None:
        """
        In this test we will check that if no evm node is selected, then a
        NoSyncedDataSourceWasAccessibleException is processed and sent together
        with a heartbeat.
        """
        mock_get_chain_contracts.return_value = None
        mock_store_chain_contracts.return_value = None
        mock_get_nodes_eth_address.return_value = (self.test_data_dict, False)
        mock_store_nodes_eth_addresses.return_value = None
        mock_select_node.return_value = None
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None
        expected_raised_exception = NoSyncedDataSourceWasAccessibleException(
            self.monitor_name, 'EVM node')
        expected_processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'parent_id': self.parent_id_1,
                    'time': datetime.now().timestamp()
                },
                'message': expected_raised_exception.message,
                'code': expected_raised_exception.code,
            }
        }
        expected_heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }

        self.test_monitor._monitor()
        mock_send_data.assert_called_once_with(expected_processed_data)
        mock_send_heartbeat.assert_called_once_with(expected_heartbeat)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsMonitor, '_filter_contracts_by_node')
    @mock.patch.object(EVMContractsMonitor, '_get_data')
    @mock.patch.object(EVMContractsMonitor, '_send_heartbeat')
    @mock.patch.object(EVMContractsMonitor, '_send_data')
    @mock.patch.object(EVMContractsMonitor, '_select_node')
    @mock.patch.object(EVMContractsMonitor, '_get_nodes_eth_address')
    @mock.patch.object(EVMContractsMonitor, '_get_chain_contracts')
    def test_monitor_gets_data_for_each_node_processes_it_and_sends_it_and_hb(
            self, mock_get_chain_contracts, mock_get_nodes_eth_address,
            mock_select_node, mock_send_data, mock_send_heartbeat,
            mock_get_data, mock_filter_contracts_by_node) -> None:
        mock_get_chain_contracts.return_value = self.retrieved_contracts_example
        mock_get_nodes_eth_address.return_value = (
            self.node_eth_address_example,
            False
        )
        mock_select_node.return_value = self.evm_nodes[0]
        mock_filter_contracts_by_node.return_value = \
            self.filtered_contracts_example
        mock_get_data.return_value = self.test_data_dict
        expected_heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }

        self.test_monitor._monitor()

        calls = mock_send_data.call_args_list
        self.assertEqual(2, len(calls))
        mock_send_data.assert_any_call({
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config_1.node_name,
                    'node_id': self.node_config_1.node_id,
                    'node_parent_id': self.node_config_1.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': copy.deepcopy(self.test_data_dict),
            }
        })
        mock_send_data.assert_any_call({
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config_2.node_name,
                    'node_id': self.node_config_2.node_id,
                    'node_parent_id': self.node_config_2.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': copy.deepcopy(self.test_data_dict),
            }
        })
        mock_send_heartbeat.assert_called_once_with(expected_heartbeat)

    @freeze_time("2012-01-01")
    @mock.patch.object(EVMContractsMonitor, '_filter_contracts_by_node')
    @mock.patch.object(EVMContractsMonitor, '_get_data')
    @mock.patch.object(EVMContractsMonitor, '_send_heartbeat')
    @mock.patch.object(EVMContractsMonitor, '_send_data')
    @mock.patch.object(EVMContractsMonitor, '_select_node')
    @mock.patch.object(EVMContractsMonitor, '_get_nodes_eth_address')
    @mock.patch.object(EVMContractsMonitor, '_get_chain_contracts')
    def test_monitor_skips_node_if_data_retrieval_fails_for_node(
            self, mock_get_chain_contracts, mock_get_nodes_eth_address,
            mock_select_node, mock_send_data, mock_send_heartbeat,
            mock_get_data, mock_filter_contracts_by_node) -> None:
        mock_get_chain_contracts.return_value = self.retrieved_contracts_example
        mock_get_nodes_eth_address.return_value = (
            self.node_eth_address_example,
            False
        )
        mock_select_node.return_value = self.evm_nodes[0]
        mock_filter_contracts_by_node.return_value = \
            self.filtered_contracts_example
        mock_get_data.side_effect = [self.test_data_dict,
                                     ReqConnectionError('test')]
        expected_heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }

        self.test_monitor._monitor()

        calls = mock_send_data.call_args_list
        self.assertEqual(1, len(calls))
        mock_send_data.assert_any_call({
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config_1.node_name,
                    'node_id': self.node_config_1.node_id,
                    'node_parent_id': self.node_config_1.parent_id,
                    'time': datetime.now().timestamp()
                },
                'data': copy.deepcopy(self.test_data_dict),
            }
        })
        mock_send_heartbeat.assert_called_once_with(expected_heartbeat)
