import json
import logging
import unittest
from datetime import timedelta, datetime
from http.client import IncompleteRead
from typing import List, Union, Dict
from unittest import mock

import pika
from parameterized import parameterized
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.api_wrappers.substrate import SubstrateApiWrapper
from src.configs.nodes.substrate import SubstrateNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.substrate import SubstrateMonitor
from src.utils import env
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY)
from src.utils.exceptions import (
    PANICException, ComponentNotGivenEnoughDataSourcesException,
    SubstrateApiCallException, SubstrateApiIsNotReachableException,
    DataReadingException, IncorrectJSONRetrievedException, NodeIsDownException)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit)
from test.utils.substrate.substrate import SubstrateTestNodes


class DummySubstrateMonitor(SubstrateMonitor):
    """
    This class is going to be used to test the logic inside the SubstrateMonitor
    class. A dummy class must be used because the SubstrateMonitor class
    contains some abstract methods.
    """

    def __init__(
            self, monitor_name: str, data_sources: List[SubstrateNodeConfig],
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


class TestSubstrateMonitor(unittest.TestCase):
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

        # Test monitor instance
        self.substrate_test_nodes = SubstrateTestNodes()
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.data_sources = [
            self.substrate_test_nodes.pruned_non_validator,
            self.substrate_test_nodes.archive_non_validator,
            self.substrate_test_nodes.archive_validator
        ]
        self.test_monitor = DummySubstrateMonitor(
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
        self.substrate_test_nodes.clear_attributes()
        self.substrate_test_nodes = None
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

    def test_substrate_api_wrapper_returns_substrate_api_wrapper(
            self) -> None:
        test_wrapper = SubstrateApiWrapper(
            env.SUBSTRATE_API_IP, env.SUBSTRATE_API_PORT, self.dummy_logger)
        self.assertEqual(test_wrapper, self.test_monitor.substrate_api_wrapper)

    def test__init__raises_exception_if_not_enough_data_sources_passed(
            self) -> None:
        self.assertRaises(
            ComponentNotGivenEnoughDataSourcesException, DummySubstrateMonitor,
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

    @mock.patch.object(DummySubstrateMonitor, "_process_retrieved_data")
    @mock.patch.object(DummySubstrateMonitor, "_process_error")
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

    @mock.patch.object(DummySubstrateMonitor, "_process_retrieved_data")
    @mock.patch.object(DummySubstrateMonitor, "_process_error")
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

    @mock.patch.object(SubstrateApiWrapper, 'execute_with_checks')
    def test_select_websocket_node_selects_first_reachable_synced_node(
            self, mock_execute_with_checks) -> None:
        """
        In this test we will check that if all nodes are synced and connected,
        then select_websocket_node will select the first node it finds
        """
        mock_execute_with_checks.return_value = {
            "result": {"isSyncing": False}
        }
        actual = self.test_monitor._select_websocket_node(self.data_sources)
        self.assertEqual(self.data_sources[0], actual)

    @mock.patch.object(SubstrateApiWrapper, 'execute_with_checks')
    def test_select_websocket_node_does_not_select_syncing_nodes(
            self, mock_execute_with_checks) -> None:
        """
        In this test we will set the first two nodes to be syncing, and the last
        node as synced to check that the third node is selected. Note, all nodes
        are set to be connected.
        """
        mock_execute_with_checks.side_effect = [
            {"result": {"isSyncing": True}},
            {"result": {"isSyncing": True}},
            {"result": {"isSyncing": False}}
        ]
        actual = self.test_monitor._select_websocket_node(self.data_sources)
        self.assertEqual(self.data_sources[2], actual)

    @parameterized.expand([
        (IncompleteRead(b'test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (SubstrateApiCallException('test_call', 'err'),),
        (KeyError('test'),),
    ])
    @mock.patch.object(SubstrateApiWrapper, 'execute_with_checks')
    def test_select_websocket_node_does_not_select_nodes_raising_expected_err(
            self, exception_instance, mock_execute_with_checks) -> None:
        """
        In this test we will set the first two nodes to return one of the
        expected errors above, and the third to be connected and synced
        to demonstrate that the third node is selected if an expected error is
        raised. Note that node downtime is implicitly tested by checking for the
        SubstrateApiCallException (since check_for_downtime = False)
        """
        mock_execute_with_checks.side_effect = [
            exception_instance,
            exception_instance,
            {"result": {"isSyncing": False}}
        ]
        actual = self.test_monitor._select_websocket_node(self.data_sources)
        self.assertEqual(self.data_sources[2], actual)

    @parameterized.expand([
        (ReqConnectionError('test'),),
        (ReadTimeout('test'),),
        (InvalidURL('test'),),
        (InvalidSchema('test'),),
        (MissingSchema('test'),),
    ])
    @mock.patch.object(SubstrateApiWrapper, 'execute_with_checks')
    def test_select_websocket_node_raises_substrate_api_exception_if_conn_err(
            self, exception_instance, mock_execute_with_checks) -> None:
        """
        In this test we will check that the select_websocket_node fn raises a
        SubstrateApiIsNotReachableException if it cannot reach the Substrate API
        service
        """
        mock_execute_with_checks.side_effect = exception_instance
        self.assertRaises(SubstrateApiIsNotReachableException,
                          self.test_monitor._select_websocket_node,
                          self.data_sources)

    @parameterized.expand([
        (IncompleteRead(b'test'),),
        (ChunkedEncodingError('test'),),
        (ProtocolError('test'),),
        (SubstrateApiCallException('test_call', 'err'),),
        (KeyError('test'),),
    ])
    @mock.patch.object(SubstrateApiWrapper, 'execute_with_checks')
    def test_select_websocket_node_returns_None_if_no_node_selected(
            self, exception_instance, mock_execute_with_checks) -> None:
        """
        In this test we will check that if neither node is online, synced, and
        does not raise errors, then select_websocket_node returns None. Note,
        we will set the first two nodes to raise an error and the third to be
        syncing, remember, we are check_for_downtime = False.
        In addition to this, connection errors are excluded from this test as
        these would raise a SubstrateApiCallNotReachableException as expected.
        """
        mock_execute_with_checks.side_effect = [
            exception_instance,
            exception_instance,
            {"result": {"isSyncing": True}}
        ]
        actual = self.test_monitor._select_websocket_node(self.data_sources)
        self.assertIsNone(actual)

    def test_execute_websocket_retrieval_with_exceptions_ret_fn_ret_if_no_err(
            self) -> None:
        def test_fn():
            return self.test_data_dict

        actual_ret = \
            self.test_monitor._execute_websocket_retrieval_with_exceptions(
                test_fn, self.data_sources[0]
            )
        self.assertEqual(self.test_data_dict, actual_ret)

    @parameterized.expand([
        (ReqConnectionError('test'), SubstrateApiIsNotReachableException,),
        (ReadTimeout('test'), SubstrateApiIsNotReachableException,),
        (InvalidURL('test'), SubstrateApiIsNotReachableException,),
        (InvalidSchema('test'), SubstrateApiIsNotReachableException,),
        (MissingSchema('test'), SubstrateApiIsNotReachableException,),
        (IncompleteRead('test'), DataReadingException,),
        (ChunkedEncodingError('test'), DataReadingException,),
        (ProtocolError('test'), DataReadingException,),
        (NodeIsDownException('test_node'), NodeIsDownException,),
        (SubstrateApiCallException('test_call', 'err_msg'),
         SubstrateApiCallException,),
        (KeyError('test'), IncorrectJSONRetrievedException,)
    ])
    def test_exec_websocket_ret_with_excep_detects_and_raises_excep_correctly(
            self, callback_raised_exception, expected_raised_exception) -> None:
        def test_fn():
            raise callback_raised_exception

        self.assertRaises(
            expected_raised_exception,
            self.test_monitor._execute_websocket_retrieval_with_exceptions,
            test_fn, self.data_sources[0]
        )

    def test_display_data_returns_the_correct_string(self) -> None:
        expected_output = json.dumps(self.test_data_dict)
        actual_output = self.test_monitor._display_data(self.test_data_dict)
        self.assertEqual(expected_output, actual_output)
