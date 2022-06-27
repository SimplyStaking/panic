import copy
import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from typing import Dict
from unittest import mock

from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.api_wrappers.substrate import SubstrateApiWrapper
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.network.substrate import SubstrateNetworkMonitor
from src.utils import env
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE,
    SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    PANICException, NoSyncedDataSourceWasAccessibleException,
    SubstrateApiIsNotReachableException, DataReadingException,
    IncorrectJSONRetrievedException, SubstrateApiCallException,
    SubstrateNetworkDataCouldNotBeObtained, MessageWasNotDeliveredException)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit, assert_not_called_with)
from test.utils.substrate.substrate import SubstrateTestNodes


class TestSubstrateNetworkMonitor(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.test_data_dict = {
            'test_key_1': 'test_val_1',
            'test_key_2': 'test_val_2',
        }
        self.test_queue_name = 'Test Queue'
        self.test_exception_1 = PANICException('test_exception_1', 1)

        # --------------- Data retrieval variables and examples ---------------

        # Websocket
        self.retrieved_websocket_indirect_data = {
            'grandpa_stalled': None,
            'public_prop_count': "0x00000010",
            'active_proposals': [
                {
                    "balance": "0x0000000000000000000000e8d4a51000",
                    "seconds": [
                        "16SqCKhH9Ew2azrzpqJKq6pRB4yZuEgrdPUbExFsbJ4uMXea",
                        "12mhTbzPtYHg1vWutbxiJ4tzh8PY754WCXcHt9YTVsNebrmV"
                    ],
                    "image": {
                        "at": "0x00199ad9",
                        "balance": "0x00000000000000000000000017d78400",
                        "proposal": {
                            "callIndex": "0x0709",
                            "args": {
                                "new": 259
                            }
                        },
                        "proposer":
                            "148AWXqV4tXLhmN9fetHzPn4G6r7ZaTkax7LvhTUgbdoDGYu"
                    },
                    "imageHash": "0xaa0894ab657781342b66e4a563c0750078bfdab371",
                    "index": "0x00000008",
                    "proposer": "16SqCKhH9Ew2azrzpqJKq6pRB4yZuEgrdPUFsbJ4uMXea"
                },
            ],
            'referendum_count': 2,
            'active_referendums': [
                {
                    "image": {
                        "at": "0x00bbbd92",
                        "balance": "0x0000000000000000000000000ee6a8bc",
                        "proposal": {
                            "callIndex": "0x0402",
                            "args": {
                                "source": {
                                    "id": "F7fq1idt8qAgF4vc3cZ4ohwJ5qWdVYs1ZUhh"
                                },
                                "dest": {
                                    "id": "F7fq1imJVvbubz6mJdnL3cqmYrLQaN2W8kRw"
                                },
                                "value": 63000000000000
                            }
                        },
                        "proposer": "GAT6yjj2uYt63PzeqvxE9LC9fUwnangEiVb25JioNQ"
                    },
                    "imageHash": "0xcfc8324d60ba320178034ab946fb0b9f96e819c47a",
                    "index": "0x00000023",
                    "status": {
                        "end": 7257600,
                        "proposalHash": "0x6baf3a4e178034ab946fb0b9f96e819c47a",
                        "threshold": "Supermajorityapproval",
                        "delay": 403200,
                        "tally": {
                            "ayes": 2468601400000,
                            "nays": 694138712800000,
                            "turnout": 748573829000000
                        }
                    },
                    "allAye": [
                        {
                            "accountId": "13Sx69yrSYyQymWiG7ftgR3Ypokbd31ux9rY",
                            "isDelegating": False,
                            "registry": {},
                            "vote": "0x80",
                            "balance": "0x00000000000000000000091c38c26c00"
                        },
                    ],
                    "allNay": [
                        {
                            "accountId": "15UdEq58PRiXUppeCzbBv2rA6pti8c2TDHcu",
                            "isDelegating": False,
                            "registry": {},
                            "vote": "0x01",
                            "balance": "0x000000000000000000000045d964b800"
                        },
                    ],
                    "voteCount": 23,
                    "voteCountAye": 6,
                    "voteCountNay": 17,
                    "votedAye": "0x00000000000000000000023ec41c0ac0",
                    "votedNay": "0x000000000000000000027750c366bb00",
                    "votedTotal": "0x00000000000000000002a8d2ed2a6b40",
                    "isPassing": False,
                    "votes": [
                        {
                            "accountId": "13Sx69yrSYyQymWiG7UyTtCswixiQ31ux9rY",
                            "isDelegating": False,
                            "registry": {},
                            "vote": "0x80",
                            "balance": "0x00000000000000000000091c38c26c00"
                        },
                    ]
                }
            ],
            'all_referendums': {
                0: {
                    "ongoing": {
                        "end": 7257600,
                        "proposalHash": "0xcfc8324d60ba32046dfgh0b9f96e819c47a",
                        "threshold": "Supermajorityapproval",
                        "delay": 403200,
                        "tally": {
                            "ayes": 2468601400000,
                            "nays": 694138712800000,
                            "turnout": 748573829000000
                        }
                    }
                },
                1: {
                    "finished": {
                        "approved": True,
                        "end": 6712649
                    }
                }
            }
        }
        self.retrieved_websocket_data = {
            **self.retrieved_websocket_indirect_data,
        }

        # Test monitor instance
        self.substrate_test_nodes = SubstrateTestNodes()
        self.monitor_name = 'test_monitor'
        self.monitoring_period = 10
        self.data_sources = [
            self.substrate_test_nodes.pruned_non_validator,
            self.substrate_test_nodes.archive_non_validator,
            self.substrate_test_nodes.archive_validator
        ]
        self.governance_addresses = ['governance_address_1',
                                     'governance_address_2',
                                     'governance_address_3']
        self.parent_id = 'parent_id_1'
        self.chain_name = 'substrate_chain_1'
        self.test_monitor = SubstrateNetworkMonitor(
            self.monitor_name, self.data_sources, self.governance_addresses,
            self.parent_id, self.chain_name, self.dummy_logger,
            self.monitoring_period, self.rabbitmq
        )

        self.received_retrieval_info_all_source_types_enabled = {
            'websocket': {
                'data': self.retrieved_websocket_data,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_websocket_data,
                'processing_function':
                    self.test_monitor._process_retrieved_websocket_data,
                'monitoring_enabled': True
            },
        }
        self.received_retrieval_info_some_sources_disabled = {
            # TODO: To be modified when adding new data sources
            'websocket': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_websocket_data,
                'processing_function':
                    self.test_monitor._process_retrieved_websocket_data,
                'monitoring_enabled': False
            },
        }
        self.received_retrieval_info_all_source_types_enabled_err = {
            'websocket': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': self.test_exception_1,
                'get_function': self.test_monitor._get_websocket_data,
                'processing_function':
                    self.test_monitor._process_retrieved_websocket_data,
                'monitoring_enabled': True
            },
        }

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
        self.test_exception_1 = None
        self.substrate_test_nodes.clear_attributes()
        self.substrate_test_nodes = None
        self.test_monitor = None

    def test_governance_addresses_returns_governance_addresses(self) -> None:
        self.assertEqual(self.governance_addresses,
                         self.test_monitor.governance_addresses)

    def test_parent_id_returns_parent_id(self) -> None:
        self.assertEqual(self.parent_id, self.test_monitor.parent_id)

    def test_chain_name_returns_chain_name(self) -> None:
        self.assertEqual(self.chain_name, self.test_monitor.chain_name)

    def test_get_websocket_indirect_data_return_if_empty_source_url(
            self) -> None:
        data_source = self.data_sources[0]
        data_source.set_node_ws_url('')
        expected_return = {
            'grandpa_stalled': None,
            'public_prop_count': None,
            'active_proposals': None,
            'referendum_count': None,
            'active_referendums': None,
            'all_referendums': None,
        }
        actual_return = self.test_monitor._get_websocket_indirect_data(
            data_source)
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(SubstrateApiWrapper, 'get_referendum_info_of')
    @mock.patch.object(SubstrateApiWrapper, 'get_democracy_referendums')
    @mock.patch.object(SubstrateApiWrapper, 'get_referendum_count')
    @mock.patch.object(SubstrateApiWrapper, 'get_democracy_proposals')
    @mock.patch.object(SubstrateApiWrapper, 'get_public_prop_count')
    @mock.patch.object(SubstrateApiWrapper, 'get_grandpa_stalled')
    def test_get_websocket_indirect_data_return(
            self, mock_grandpa_stalled, mock_get_props_count,
            mock_get_proposals, mock_get_referendum_count,
            mock_get_referendums, mock_referendum_info_of) -> None:
        """
        In this test we are checking the get_websocket_indirect_data return
        assuming that a valid data source was given
        """
        mock_grandpa_stalled.return_value = {
            "result": self.retrieved_websocket_indirect_data['grandpa_stalled']
        }
        mock_get_props_count.return_value = {
            "result": self.retrieved_websocket_indirect_data[
                'public_prop_count']
        }
        mock_get_proposals.return_value = {
            "result": self.retrieved_websocket_indirect_data['active_proposals']
        }
        mock_get_referendum_count.return_value = {"result": "0x2"}
        mock_get_referendums.return_value = {
            "result": self.retrieved_websocket_indirect_data[
                'active_referendums']
        }
        mock_referendum_info_of.side_effect = [
            {"result": self.retrieved_websocket_indirect_data[
                'all_referendums'][0]},
            {"result": self.retrieved_websocket_indirect_data[
                'all_referendums'][1]}
        ]

        actual_return = self.test_monitor._get_websocket_indirect_data(
            self.data_sources[0])
        self.assertEqual(self.retrieved_websocket_indirect_data, actual_return)

    @mock.patch.object(SubstrateNetworkMonitor, '_select_websocket_node')
    def test_get_websocket_data_return_if_no_indirect_source_selected(
            self, mock_select_websocket_node) -> None:
        mock_select_websocket_node.return_value = None
        expected_return = ({}, True, NoSyncedDataSourceWasAccessibleException(
            self.monitor_name, 'indirect Substrate websocket node'))
        actual_return = self.test_monitor._get_websocket_data()
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(SubstrateNetworkMonitor, '_get_websocket_indirect_data')
    @mock.patch.object(SubstrateNetworkMonitor, '_select_websocket_node')
    def test_get_websocket_data_return_if_data_retrieval_successful(
            self, mock_select_node, mock_get_indirect) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_indirect.return_value = self.retrieved_websocket_indirect_data

        expected_return = (self.retrieved_websocket_indirect_data, False, None)
        actual_return = self.test_monitor._get_websocket_data()
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        (SubstrateApiIsNotReachableException('test_monitor', 'api_url'),
         SubstrateApiIsNotReachableException),
        (DataReadingException('test_monitor', 'ws_url_1'),
         DataReadingException),
        (IncorrectJSONRetrievedException('substrate_api', 'err'),
         SubstrateNetworkDataCouldNotBeObtained),
        (SubstrateApiCallException('api_call', 'err'),
         SubstrateApiCallException),
    ])
    @mock.patch.object(SubstrateNetworkMonitor, '_get_websocket_indirect_data')
    @mock.patch.object(SubstrateNetworkMonitor, '_select_websocket_node')
    def test_get_websocket_data_return_if_expected_error_in_data_retrieval(
            self, error_raised, error_instance_returned, mock_select_node,
            mock_get_indirect_data) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_indirect_data.side_effect = error_raised
        actual_return = self.test_monitor._get_websocket_data()
        self.assertEqual({}, actual_return[0])
        self.assertEqual(True, actual_return[1])
        self.assertIsInstance(actual_return[2], error_instance_returned)

    @parameterized.expand([
        ('self.received_retrieval_info_all_source_types_enabled',
         ['self.retrieved_websocket_data', False, None]),
        ('self.received_retrieval_info_all_source_types_enabled_err',
         [{}, True, PANICException('test_exception_1', 1)]),
    ])
    @mock.patch.object(SubstrateNetworkMonitor, '_get_websocket_data')
    def test_get_data_return(
            self, expected_ret, retrieved_websocket_data,
            mock_get_websocket_data) -> None:
        """
        In this test we will check that the retrieval info is returned correctly
        for every possible test case. We will use parameterized.expand to
        explore all possible cases.
        TODO: Once we add more data sources this test must be modified such that
              it is similar to the SubstrateNodeMonitor one.
        """
        if retrieved_websocket_data[0]:
            # If the first element is a variable evaluate it
            retrieved_websocket_data[0] = eval(retrieved_websocket_data[0])
        mock_get_websocket_data.return_value = tuple(retrieved_websocket_data)
        actual_ret = self.test_monitor._get_data()
        expected_ret = eval(expected_ret)
        expected_ret['websocket']['get_function'] = mock_get_websocket_data
        self.assertEqual(expected_ret, actual_ret)

    @freeze_time("2012-01-01")
    def test_process_error_returns_expected_data(self) -> None:
        expected_output = {
            'error': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'parent_id': self.test_monitor.parent_id,
                    'chain_name': self.test_monitor.chain_name,
                    'time': datetime.now().timestamp(),
                    'governance_addresses':
                        self.test_monitor.governance_addresses
                },
                'message': self.test_exception_1.message,
                'code': self.test_exception_1.code,
            }
        }
        actual_output = self.test_monitor._process_error(self.test_exception_1)
        self.assertEqual(expected_output, actual_output)

    @freeze_time("2012-01-01")
    def test_process_retrieved_websocket_data_returns_expected_data(
            self) -> None:
        expected_ret = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'parent_id': self.test_monitor.parent_id,
                    'chain_name': self.test_monitor.chain_name,
                    'time': datetime.now().timestamp(),
                    'governance_addresses':
                        self.test_monitor.governance_addresses
                },
                'data': copy.deepcopy(self.test_data_dict),
            }
        }
        actual_ret = self.test_monitor._process_retrieved_websocket_data(
            self.test_data_dict)
        self.assertEqual(expected_ret, actual_ret)

    def test_process_retrieved_data_calls_the_correct_fn_and_returns_its_return(
            self) -> None:
        test_fn_call_count = 0

        def test_fn(x: Dict):
            nonlocal test_fn_call_count
            test_fn_call_count += 1
            return x

        actual_ret = self.test_monitor._process_retrieved_data(
            test_fn, self.test_data_dict)
        expected_ret = self.test_data_dict
        self.assertEqual(expected_ret, actual_ret)
        self.assertEqual(1, test_fn_call_count)

    def test_send_data_sends_data_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_data, and checks that the data is
        # received
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
            routing_key=SUBSTRATE_NETWORK_RAW_DATA_ROUTING_KEY)

        self.test_monitor._send_data(self.test_data_dict)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the sent data
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_data_dict, json.loads(body))

    @freeze_time("2012-01-01")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data, mock_send_heartbeat, mock_send_data) -> None:
        # Here we are assuming that all sources are enabled.
        expected_output_data = {
            'websocket': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'parent_id': self.test_monitor.parent_id,
                        'chain_name': self.test_monitor.chain_name,
                        'time': datetime.now().timestamp(),
                        'governance_addresses':
                            self.test_monitor.governance_addresses
                    },
                    'data': self.retrieved_websocket_data,
                }
            },
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None

        self.test_monitor._monitor()
        mock_send_data.assert_called_once_with(expected_output_data)
        mock_send_heartbeat.assert_called_once_with(expected_output_hb)

    @freeze_time("2012-01-01")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_sends_empty_dict_for_disabled_sources(
            self, mock_get_data, mock_send_heartbeat, mock_send_data) -> None:
        expected_output_data = {'websocket': {}}
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }
        mock_get_data.return_value = \
            self.received_retrieval_info_some_sources_disabled
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None

        self.test_monitor._monitor()
        mock_send_data.assert_called_once_with(expected_output_data)
        mock_send_heartbeat.assert_called_once_with(expected_output_hb)

    @parameterized.expand([
        (['self.test_exception_1'],),
    ])
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_process_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_sends_no_data_and_hb_if_data_ret_success_and_proc_fails(
            self, process_data_side_effect, mock_get_data, mock_process_data,
            mock_send_hb, mock_send_data) -> None:
        # TODO: When more sources are added we should add more test cases to
        #       cover the scenario when processing fails after some successful
        #       iterations
        process_data_side_effect_eval = list(map(
            eval, process_data_side_effect))
        mock_process_data.side_effect = process_data_side_effect_eval
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        mock_send_data.return_value = None
        mock_send_hb.return_value = None

        self.test_monitor._monitor()
        mock_send_data.assert_not_called()
        mock_send_hb.assert_not_called()

    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_sends_no_data_and_no_hb_on_get_data_unexpected_exception(
            self, mock_get_data, mock_send_hb, mock_send_data) -> None:
        mock_get_data.side_effect = self.test_exception_1
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        self.assertRaises(PANICException, self.test_monitor._monitor)
        mock_send_data.assert_not_called()
        mock_send_hb.assert_not_called()

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (MessageWasNotDeliveredException,
         MessageWasNotDeliveredException('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_raises_error_if_raised_by_send_data(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_data) -> None:
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        mock_send_data.side_effect = exception_instance
        self.assertRaises(exception_class, self.test_monitor._monitor)

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (MessageWasNotDeliveredException,
         MessageWasNotDeliveredException('test'),),
        (Exception, Exception('test'),),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_raises_error_if_raised_by_send_hb(
            self, exception_class, exception_instance, mock_get_data,
            mock_send_hb, mock_send_data) -> None:
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        mock_send_data.return_value = None
        mock_send_hb.side_effect = exception_instance
        self.assertRaises(exception_class, self.test_monitor._monitor)

    @freeze_time("2012-01-01")
    @mock.patch.object(logging.Logger, "debug")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_logs_data_if_all_sources_enabled_and_no_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        expected_logged_data = self.test_monitor._display_data({
            'websocket': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'parent_id': self.test_monitor.parent_id,
                        'chain_name': self.test_monitor.chain_name,
                        'time': datetime.now().timestamp(),
                        'governance_addresses':
                            self.test_monitor.governance_addresses
                    },
                    'data': self.retrieved_websocket_data,
                }
            }
        })
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        self.test_monitor._monitor()
        mock_log.assert_called_with(expected_logged_data)

    @mock.patch.object(logging.Logger, "debug")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_does_not_log_if_no_retrieval_performed(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        # expected_logged_data contains the data that should be logged if all
        # sources are enabled.
        expected_logged_data = self.test_monitor._display_data({
            'websocket': {},
        })
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        self.received_retrieval_info_all_source_types_enabled['websocket'][
            'monitoring_enabled'] = False
        self.test_monitor._monitor()
        assert_not_called_with(mock_log, expected_logged_data)

    @mock.patch.object(logging.Logger, "debug")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNetworkMonitor, "_send_data")
    @mock.patch.object(SubstrateNetworkMonitor, "_get_data")
    def test_monitor_does_not_log_if_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        # expected_logged_data contains the data that should be logged if all
        # sources are enabled.
        expected_logged_data = self.test_monitor._display_data({
            'websocket': {
                'error': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'parent_id': self.test_monitor.parent_id,
                        'chain_name': self.test_monitor.chain_name,
                        'time': datetime.now().timestamp(),
                        'governance_addresses':
                            self.test_monitor.governance_addresses
                    },
                    'message': self.test_exception_1.message,
                    'code': self.test_exception_1.code,
                }
            },
        })
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled_err
        self.test_monitor._monitor()
        assert_not_called_with(mock_log, expected_logged_data)
