import json
import logging
import unittest
from datetime import timedelta, datetime
from http.client import IncompleteRead
from typing import List, Union, Dict
from unittest import mock
from unittest.mock import call

import pika
from parameterized import parameterized
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.api_wrappers.cosmos import (
    CosmosRestServerApiWrapper, TendermintRpcApiWrapper)
from src.configs.nodes.cosmos import CosmosNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.cosmos import CosmosMonitor
from src.utils import env
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.exceptions import (
    ComponentNotGivenEnoughDataSourcesException, PANICException,
    CosmosSDKVersionIncompatibleException, CosmosRestServerApiCallException,
    TendermintRPCCallException, TendermintRPCIncompatibleException,
    NodeIsDownException, InvalidUrlException, DataReadingException,
    CannotConnectWithDataSourceException, IncorrectJSONRetrievedException)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit)
from test.utils.cosmos.cosmos import CosmosTestNodes


class DummyCosmosMonitor(CosmosMonitor):
    """
    This class is going to be used to test the logic inside the CosmosMonitor
    class. A dummy class must be used because the CosmosMonitor class contains
    some abstract methods.
    """

    def __init__(self, monitor_name: str, data_sources: List[CosmosNodeConfig],
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(monitor_name, data_sources, logger, monitor_period,
                         rabbitmq)

    def _send_data(self, *args) -> None:
        pass

    def _monitor(self) -> None:
        pass

    def _process_retrieved_data(self, *args) -> Dict:
        pass

    def _process_error(self, *args) -> Dict:
        pass

    def _get_data(self, *args) -> Union[Dict, List]:
        pass


class TestCosmosMonitor(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.routing_key = 'test_routing_key'
        self.test_data_str = 'test data'
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_exception_1 = PANICException('test_exception_1', 1)
        self.test_exception_2 = PANICException('test_exception_2', 2)
        self.test_queue_name = 'Test Queue'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.sdk_version_0_39_2 = 'v0.39.2'
        self.sdk_version_0_42_6 = 'v0.42.6'

        # Some dummy retrieval data
        self.rest_ret_1 = {
            'data': 'val_1',
            'pagination': {
                "next_key": "ASDFG9a7gfas79fg90as",
                "total": "331"
            }
        }
        self.rest_ret_2 = {
            'data': 'val_2',
            'pagination': {
                "next_key": None,
                "total": 0
            }
        }
        self.tendermint_ret_1 = {
            'result': {
                'data': 'val_1',
                'count': 30,
                'total': 60,
            }
        }
        self.tendermint_ret_2 = {
            'result': {
                'data': 'val_2',
                'count': 30,
                'total': 60
            }
        }

        # Test monitor instance
        self.cosmos_test_nodes = CosmosTestNodes()
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.data_sources = [
            self.cosmos_test_nodes.pruned_non_validator,
            self.cosmos_test_nodes.archive_non_validator,
            self.cosmos_test_nodes.archive_validator
        ]
        self.test_monitor = DummyCosmosMonitor(
            self.monitor_name, self.data_sources, self.dummy_logger,
            self.monitoring_period, self.rabbitmq
        )

    def tearDown(self) -> None:
        connect_to_rabbit(self.test_monitor.rabbitmq)
        delete_queue_if_exists(self.test_monitor.rabbitmq, self.test_queue_name)
        delete_exchange_if_exists(self.test_monitor.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_monitor.rabbitmq, RAW_DATA_EXCHANGE)
        disconnect_from_rabbit(self.test_monitor.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_exception_1 = None
        self.test_exception_2 = None
        self.cosmos_test_nodes.clear_attributes()
        self.cosmos_test_nodes = None
        self.test_monitor = None

    def test_str_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, str(self.test_monitor))

    def test_monitor_period_returns_monitor_period(self) -> None:
        self.assertEqual(self.monitoring_period,
                         self.test_monitor.monitor_period)

    def test_monitor_name_returns_monitor_name(self) -> None:
        self.assertEqual(self.monitor_name, self.test_monitor.monitor_name)

    def test_data_sources_returns_data_sources(self) -> None:
        self.assertEqual(self.data_sources, self.test_monitor.data_sources)

    def test_cosmos_rest_server_api_returns_cosmos_rest_server_api(
            self) -> None:
        test_wrapper = CosmosRestServerApiWrapper(self.dummy_logger)
        self.assertEqual(test_wrapper, self.test_monitor.cosmos_rest_server_api)

    def test_tendermint_rpc_api_returns_tendermint_rpc_api(self) -> None:
        test_wrapper = TendermintRpcApiWrapper(self.dummy_logger)
        self.assertEqual(test_wrapper, self.test_monitor.tendermint_rpc_api)

    def test_last_rest_retrieval_version_returns_last_rest_retrieval_version(
            self) -> None:
        # First we will check that last_rest_retrieval_version is set to v0.42.6
        # on __init__
        self.assertEqual(self.sdk_version_0_42_6,
                         self.test_monitor.last_rest_retrieval_version)
        self.test_monitor._last_rest_retrieval_version = self.sdk_version_0_39_2
        self.assertEqual(self.sdk_version_0_39_2,
                         self.test_monitor.last_rest_retrieval_version)

    def test__init__raises_exception_if_not_enough_data_sources_passed(
            self) -> None:
        self.assertRaises(
            ComponentNotGivenEnoughDataSourcesException, DummyCosmosMonitor,
            self.monitor_name, [], self.dummy_logger, self.monitoring_period,
            self.rabbitmq)

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

        # Check whether the exchange has been created by sending messages to it.
        # If this fails an exception is raised hence the test fails.
        self.test_monitor.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE, routing_key=self.routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)
        self.test_monitor.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=self.routing_key,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

    @mock.patch.object(DummyCosmosMonitor, "_process_retrieved_data")
    @mock.patch.object(DummyCosmosMonitor, "_process_error")
    def test_process_data_calls_process_error_on_retrieval_error(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_error.return_value = self.test_data_dict

        self.test_monitor._process_data(True, [self.test_exception_1],
                                        [self.test_data_dict])

        # Test passes if _process_error is called once and
        # process_retrieved_data is not called
        mock_process_error.assert_called_once_with(self.test_exception_1)
        mock_process_retrieved_data.assert_not_called()

    @mock.patch.object(DummyCosmosMonitor, "_process_retrieved_data")
    @mock.patch.object(DummyCosmosMonitor, "_process_error")
    def test_process_data_calls_process_retrieved_data_on_retrieval_success(
            self, mock_process_error, mock_process_retrieved_data) -> None:
        # Do not test the processing of data for now
        mock_process_retrieved_data.return_value = self.test_data_dict

        self.test_monitor._process_data(False, [self.test_exception_1],
                                        [self.test_data_dict])

        # Test passes if _process_error is not called and process_retrieved_data
        # is called once
        mock_process_error.assert_not_called()
        mock_process_retrieved_data.assert_called_once_with(self.test_data_dict)

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

    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_select_cosmos_rest_node_selects_first_reachable_synced_node(
            self, mock_execute_with_checks) -> None:
        """
        In this test we will check that if all nodes are synced and connected,
        then select_cosmos_rest_node will select the first node it finds
        """
        mock_execute_with_checks.return_value = {"syncing": False}
        actual = self.test_monitor._select_cosmos_rest_node(
            self.data_sources, self.sdk_version_0_39_2)
        self.assertEqual(self.data_sources[0], actual)

    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_select_cosmos_rest_node_does_not_select_syncing_nodes(
            self, mock_execute_with_checks) -> None:
        """
        In this test we will set the first two nodes to be syncing, and the
        last node as synced to check that the third node is selected. Note, all
        nodes are set to be connected.
        """
        mock_execute_with_checks.side_effect = [
            {"syncing": True},
            {"syncing": True},
            {"syncing": False}
        ]
        actual = self.test_monitor._select_cosmos_rest_node(
            self.data_sources, self.sdk_version_0_39_2)
        self.assertEqual(self.data_sources[2], actual)

    @parameterized.expand([
        (ReqConnectionError('test'),),
        (ReadTimeout('test'),),
        (InvalidURL('test'),),
        (InvalidSchema('test'),),
        (MissingSchema('test'),),
        (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (CosmosSDKVersionIncompatibleException('test_node', 'v0.39.2'),),
        (CosmosRestServerApiCallException('test_call', 'err_msg'),),
        (KeyError('test'),),
    ])
    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_select_cosmos_rest_node_does_not_select_nodes_raising_expected_err(
            self, exception_instance, mock_execute_with_checks) -> None:
        """
        In this test we will set the first two nodes to return one of the
        expected errors above, and the third to be connected and synced
        to demonstrate that the third node is selected if expected error is
        raised. Note that ReqConnectionError and ReadTimeout indicate that the
        node is offline, so we are also testing that nodes are not selected if
        they are offline
        """
        mock_execute_with_checks.side_effect = [
            exception_instance,
            exception_instance,
            {"syncing": False}
        ]
        actual = self.test_monitor._select_cosmos_rest_node(
            self.data_sources, self.sdk_version_0_39_2)
        self.assertEqual(self.data_sources[2], actual)

    @parameterized.expand([
        (ReqConnectionError('test'),),
        (ReadTimeout('test'),),
        (InvalidURL('test'),),
        (InvalidSchema('test'),),
        (MissingSchema('test'),),
        (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (CosmosSDKVersionIncompatibleException('test_node', 'v0.39.2'),),
        (CosmosRestServerApiCallException('test_call', 'err_msg'),),
        (KeyError('test'),),
    ])
    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_select_cosmos_rest_node_returns_None_if_no_node_selected(
            self, exception_instance, mock_execute_with_checks) -> None:
        """
        In this test we will check that if neither node is online, synced, and
        does not raise errors, then select_cosmos_rest_node returns None. Note,
        we will set the first node to be offline, the second node to raise an
        error and the third to be syncing .
        """
        mock_execute_with_checks.side_effect = [
            ReqConnectionError('test'),
            exception_instance,
            {"syncing": True}
        ]
        actual = self.test_monitor._select_cosmos_rest_node(
            self.data_sources, self.sdk_version_0_39_2)
        self.assertIsNone(actual)

    @mock.patch.object(TendermintRpcApiWrapper, 'execute_with_checks')
    def test_select_cosmos_tendermint_node_selects_first_reachable_synced_node(
            self, mock_execute_with_checks) -> None:
        """
        In this test we will check that if all nodes are synced and connected,
        then select_cosmos_tendermint_node will select the first node it finds
        """
        mock_execute_with_checks.return_value = {
            "result": {'sync_info': {'catching_up': False}}
        }
        actual = self.test_monitor._select_cosmos_tendermint_node(
            self.data_sources)
        self.assertEqual(self.data_sources[0], actual)

    @mock.patch.object(TendermintRpcApiWrapper, 'execute_with_checks')
    def test_select_cosmos_tendermint_node_does_not_select_syncing_nodes(
            self, mock_execute_with_checks) -> None:
        """
        In this test we will set the first two nodes to be syncing, and the
        last node as synced to check that the third node is selected. Note, all
        nodes are set to be connected.
        """
        mock_execute_with_checks.side_effect = [
            {"result": {'sync_info': {'catching_up': True}}},
            {"result": {'sync_info': {'catching_up': True}}},
            {"result": {'sync_info': {'catching_up': False}}}
        ]
        actual = self.test_monitor._select_cosmos_tendermint_node(
            self.data_sources)
        self.assertEqual(self.data_sources[2], actual)

    @parameterized.expand([
        (ReqConnectionError('test'),),
        (ReadTimeout('test'),),
        (InvalidURL('test'),),
        (InvalidSchema('test'),),
        (MissingSchema('test'),),
        (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (TendermintRPCCallException('test_api_call', 'error_msg'),),
        (TendermintRPCIncompatibleException('test_node'),),
        (KeyError('test'),),
    ])
    @mock.patch.object(TendermintRpcApiWrapper, 'execute_with_checks')
    def test_select_cosmos_tendermint_node_ignores_nodes_raising_expected_err(
            self, exception_instance, mock_execute_with_checks) -> None:
        """
        In this test we will set the first two nodes to return one of the
        expected errors above, and the third to be connected and synced
        to demonstrate that the third node is selected if an expected error is
        raised. Note that ReqConnectionError and ReadTimeout indicate that the
        node is offline, so we are also testing that nodes are not selected if
        they are offline
        """
        mock_execute_with_checks.side_effect = [
            exception_instance,
            exception_instance,
            {"result": {'sync_info': {'catching_up': False}}}
        ]
        actual = self.test_monitor._select_cosmos_tendermint_node(
            self.data_sources)
        self.assertEqual(self.data_sources[2], actual)

    @parameterized.expand([
        (ReqConnectionError('test'),),
        (ReadTimeout('test'),),
        (InvalidURL('test'),),
        (InvalidSchema('test'),),
        (MissingSchema('test'),),
        (IncompleteRead('test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (TendermintRPCCallException('test_api_call', 'error_msg'),),
        (TendermintRPCIncompatibleException('test_node'),),
        (KeyError('test'),),
    ])
    @mock.patch.object(TendermintRpcApiWrapper, 'execute_with_checks')
    def test_select_cosmos_tendermint_node_returns_None_if_no_node_selected(
            self, exception_instance, mock_execute_with_checks) -> None:
        """
        In this test we will check that if neither node is online, synced, and
        does not raise errors, then select_cosmos_tendermint_node returns None.
        Note, we will set the first node to be offline, the second node to raise
        an error and the third to be syncing .
        """
        mock_execute_with_checks.side_effect = [
            ReqConnectionError('test'),
            exception_instance,
            {"result": {'sync_info': {'catching_up': True}}}
        ]
        actual = self.test_monitor._select_cosmos_tendermint_node(
            self.data_sources)
        self.assertIsNone(actual)

    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_cosmos_rest_reachable_returns_true_None_if_data_ret_successful(
            self, mock_execute_with_checks) -> None:
        mock_execute_with_checks.side_effect = {"syncing": False}
        actual_reachable, actual_data_retrieval_exception = \
            self.test_monitor._cosmos_rest_reachable(self.data_sources[2],
                                                     self.sdk_version_0_39_2)
        self.assertTrue(actual_reachable)
        self.assertIsNone(actual_data_retrieval_exception)

    @parameterized.expand([
        (ReqConnectionError('test'), NodeIsDownException,),
        (ReadTimeout('test'), NodeIsDownException,),
        (InvalidURL('test'), InvalidUrlException,),
        (InvalidSchema('test'), InvalidUrlException,),
        (MissingSchema('test'), InvalidUrlException,),
        (IncompleteRead('test'), DataReadingException,),
        (ChunkedEncodingError('test'), DataReadingException,),
        (ProtocolError('test'), DataReadingException,),
        (CosmosSDKVersionIncompatibleException('test_node', 'v0.39.2'),
         CosmosSDKVersionIncompatibleException,),
        (CosmosRestServerApiCallException('test_call', 'err_msg'),
         CosmosRestServerApiCallException,),
    ])
    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_cosmos_rest_reachable_returns_false_err_if_expected_err_raised(
            self, raised_exception, returned_exception_type,
            mock_execute_with_checks) -> None:
        """
        The exceptions that might be raised are related to node downtime,
        invalid urls, data reading errors, Cosmos SDK incompatibility and REST
        Server API call errors. All of these indicate that the node is not
        reachable to PANIC at the REST endpoint.
        """
        mock_execute_with_checks.side_effect = raised_exception
        actual_reachable, actual_data_retrieval_exception = \
            self.test_monitor._cosmos_rest_reachable(self.data_sources[2],
                                                     self.sdk_version_0_39_2)
        self.assertFalse(actual_reachable)
        self.assertIsInstance(actual_data_retrieval_exception,
                              returned_exception_type)

    def test_execute_cosmos_rest_retrieval_with_exceptions_ret_fn_ret_if_no_err(
            self) -> None:
        def test_fn():
            return self.test_data_dict

        source_name = self.data_sources[0].node_name
        source_url = self.data_sources[0].cosmos_rest_url
        actual_ret = \
            self.test_monitor._execute_cosmos_rest_retrieval_with_exceptions(
                test_fn, source_name, source_url, self.sdk_version_0_39_2
            )
        self.assertEqual(self.test_data_dict, actual_ret)

    @parameterized.expand([
        (ReqConnectionError('test'), CannotConnectWithDataSourceException,),
        (ReadTimeout('test'), CannotConnectWithDataSourceException,),
        (InvalidURL('test'), InvalidUrlException,),
        (InvalidSchema('test'), InvalidUrlException,),
        (MissingSchema('test'), InvalidUrlException,),
        (IncompleteRead('test'), DataReadingException,),
        (ChunkedEncodingError('test'), DataReadingException,),
        (ProtocolError('test'), DataReadingException,),
        (CosmosSDKVersionIncompatibleException('test_node', 'v0.39.2'),
         CosmosSDKVersionIncompatibleException,),
        (CosmosRestServerApiCallException('test_call', 'err_msg'),
         CosmosRestServerApiCallException,),
        (KeyError('test'), IncorrectJSONRetrievedException,)
    ])
    def test_exec_cosmos_rest_ret_with_excep_detects_and_raises_excep_correctly(
            self, callback_raised_exception, expected_raised_exception) -> None:
        def test_fn():
            raise callback_raised_exception

        source_name = self.data_sources[0].node_name
        source_url = self.data_sources[0].cosmos_rest_url
        self.assertRaises(
            expected_raised_exception,
            self.test_monitor._execute_cosmos_rest_retrieval_with_exceptions,
            test_fn, source_name, source_url, self.sdk_version_0_39_2
        )

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_execute_cosmos_tendermint_ret_with_exceptions_ret_fn_ret_if_no_err(
            self, direct_retrieval) -> None:
        """
        In this test we will be checking that the
        _execute_cosmos_tendermint_retrieval_with_exceptions function returns
        the callback return if no error is raised. Note that we will be checking
        this for both when we perform a direct data retrieval and for when we
        perform an indirect data retrieval.
        """

        def test_fn():
            return self.test_data_dict

        source_name = self.data_sources[0].node_name
        source_url = self.data_sources[0].tendermint_rpc_url
        actual_ret = self.test_monitor. \
            _execute_cosmos_tendermint_retrieval_with_exceptions(
            test_fn, source_name, source_url, direct_retrieval
        )
        self.assertEqual(self.test_data_dict, actual_ret)

    @parameterized.expand([
        (ReqConnectionError('test'), CannotConnectWithDataSourceException,
         False,),
        (ReqConnectionError('test'), NodeIsDownException, True,),
        (ReadTimeout('test'), CannotConnectWithDataSourceException, False,),
        (ReadTimeout('test'), NodeIsDownException, True,),
        (InvalidURL('test'), InvalidUrlException, False,),
        (InvalidURL('test'), InvalidUrlException, True,),
        (InvalidSchema('test'), InvalidUrlException, False,),
        (InvalidSchema('test'), InvalidUrlException, True,),
        (MissingSchema('test'), InvalidUrlException, False,),
        (MissingSchema('test'), InvalidUrlException, True,),
        (IncompleteRead('test'), DataReadingException, False,),
        (IncompleteRead('test'), DataReadingException, True,),
        (ChunkedEncodingError('test'), DataReadingException, False,),
        (ChunkedEncodingError('test'), DataReadingException, True,),
        (ProtocolError('test'), DataReadingException, False,),
        (ProtocolError('test'), DataReadingException, True,),
        (TendermintRPCIncompatibleException('test_node'),
         TendermintRPCIncompatibleException, False,),
        (TendermintRPCIncompatibleException('test_node'),
         TendermintRPCIncompatibleException, True,),
        (TendermintRPCCallException('test_call', 'err_msg'),
         TendermintRPCCallException, False,),
        (TendermintRPCCallException('test_call', 'err_msg'),
         TendermintRPCCallException, True,),
        (KeyError('test'), IncorrectJSONRetrievedException, False,),
        (KeyError('test'), IncorrectJSONRetrievedException, True,)
    ])
    def test_exec_cosmos_tendermint_ret_with_ex_detects_and_raises_ex_correctly(
            self, callback_raised_exception, expected_raised_exception,
            direct_retrieval) -> None:
        """
        In this test we will be checking that the
        _execute_cosmos_tendermint_retrieval_with_exceptions function raises the
        correct exceptions if the callback raises an expected exception. Note
        that we will be checking each raised exception both with
        direct_retrieval True and False.
        """

        def test_fn():
            raise callback_raised_exception

        source_name = self.data_sources[0].node_name
        source_url = self.data_sources[0].tendermint_rpc_url
        self.assertRaises(
            expected_raised_exception, self.test_monitor.
                _execute_cosmos_tendermint_retrieval_with_exceptions, test_fn,
            source_name, source_url, direct_retrieval
        )

    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_get_rest_data_with_pagination_keys_returns_correctly(
            self, mock_execute) -> None:
        """
        In this test we will check that the data returned by
        _get_rest_data_with_pagination_keys is a list of API call return values,
        i.e. paginated data
        """

        def test_fn():
            return self.test_data_dict

        mock_execute.side_effect = [self.rest_ret_1, self.rest_ret_2]
        node_name = self.data_sources[0].node_name
        actual_ret = self.test_monitor._get_rest_data_with_pagination_keys(
            test_fn, [], {}, node_name, self.sdk_version_0_42_6)
        self.assertEqual([self.rest_ret_1, self.rest_ret_2], actual_ret)

    @mock.patch.object(CosmosRestServerApiWrapper, 'execute_with_checks')
    def test_get_rest_data_with_pagination_keys_performs_correct_calls(
            self, mock_execute) -> None:
        """
        In this test we will be checking that the
        _get_rest_data_with_pagination_keys performs a series of Cosmos Rest
        Server API calls correctly
        """

        def test_fn():
            return self.test_data_dict

        mock_execute.side_effect = [self.rest_ret_1, self.rest_ret_2]
        node_name = self.data_sources[0].node_name
        test_args = ['arg_1', 'arg_2']
        test_params = {'param_1': 'param_1_val', 'param_2': 'param_2_val'}
        test_args_first = ['arg_1', 'arg_2', test_params]
        test_args_second = [
            'arg_1', 'arg_2', {
                **test_params,
                'pagination.key': "ASDFG9a7gfas79fg90as"
            }
        ]
        self.test_monitor._get_rest_data_with_pagination_keys(
            test_fn, test_args, test_params, node_name, self.sdk_version_0_42_6)

        calls = mock_execute.call_args_list
        self.assertEqual(2, len(calls))
        mock_execute.assert_has_calls([
            call(test_fn, test_args_first, node_name, self.sdk_version_0_42_6),
            call(test_fn, test_args_second, node_name, self.sdk_version_0_42_6),
        ])

    @mock.patch.object(TendermintRpcApiWrapper, 'execute_with_checks')
    def test_get_tendermint_data_with_count_returns_correctly(
            self, mock_execute) -> None:
        """
        In this test we will check that the data returned by
        _get_tendermint_data_with_count is a list of API call return values,
        i.e. paginated data
        """

        def test_fn():
            return self.test_data_dict

        mock_execute.side_effect = [self.tendermint_ret_1,
                                    self.tendermint_ret_2]
        node_name = self.data_sources[0].node_name
        actual_ret = self.test_monitor._get_tendermint_data_with_count(
            test_fn, [], {}, node_name)
        self.assertEqual([self.tendermint_ret_1, self.tendermint_ret_2],
                         actual_ret)

    @mock.patch.object(TendermintRpcApiWrapper, 'execute_with_checks')
    def test_get_tendermint_data_with_count_performs_correct_calls(
            self, mock_execute) -> None:
        """
        In this test we will be checking that the
        _get_tendermint_data_with_count performs a series of Cosmos Tendermint
        API calls correctly
        """

        def test_fn():
            return self.test_data_dict

        mock_execute.side_effect = [self.tendermint_ret_1,
                                    self.tendermint_ret_2]
        node_name = self.data_sources[0].node_name
        test_args = ['arg_1', 'arg_2']
        test_params = {'param_1': 'param_1_val', 'param_2': 'param_2_val'}
        test_args_first = ['arg_1', 'arg_2', {**test_params, 'page': 1}]
        test_args_second = ['arg_1', 'arg_2', {**test_params, 'page': 2}]
        self.test_monitor._get_tendermint_data_with_count(
            test_fn, test_args, test_params, node_name)

        calls = mock_execute.call_args_list
        self.assertEqual(2, len(calls))
        mock_execute.assert_has_calls([
            call(test_fn, test_args_first, node_name),
            call(test_fn, test_args_second, node_name),
        ])

    def test_display_data_returns_the_correct_string(self) -> None:
        expected_output = json.dumps(self.test_data_dict)
        actual_output = self.test_monitor._display_data(self.test_data_dict)
        self.assertEqual(expected_output, actual_output)
