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
from src.monitors.node.substrate import SubstrateNodeMonitor
from src.utils import env
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE,
    SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    PANICException, NoSyncedDataSourceWasAccessibleException,
    SubstrateApiIsNotReachableException, DataReadingException,
    IncorrectJSONRetrievedException, NodeIsDownException,
    SubstrateApiCallException, SubstrateWebSocketDataCouldNotBeObtained,
    MessageWasNotDeliveredException)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit, assert_not_called_with)
from test.utils.substrate.substrate import SubstrateTestNodes


class TestSubstrateNodeMonitor(unittest.TestCase):
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
        self.stash_address_1 = 'stash_address_1'
        self.controller_address_1 = 'controller_address_1'

        # --------------- Data retrieval variables and examples ---------------

        # Websocket
        self.retrieved_websocket_direct_data = {
            'best_height': 1000,
            'target_height': 1200,
            'finalized_height': 900
        }
        self.retrieved_websocket_indirect_data_validator = {
            'current_session': 50,
            'current_era': 23,
            'authored_blocks': "0x00000005",
            'active': True,
            'elected': True,
            'disabled': False,
            'eras_stakers': {
                "total": "0x00000000000000000048a4faa9941924",
                "own": 100001845000000,
                "others": [
                    {
                        "who": "1481ZvmVcwvH4tEpRJ66x199EQCWJg8vqAd8oYfnMw",
                        "value": 2696607929740009
                    },
                ]
            },
            'sent_heartbeat': False,
            'controller_address': self.controller_address_1,
            'history_depth_eras': 84,
            'unclaimed_rewards': [0, 8, 9, 14, 16, 17, 18, 19, 20, 21],
            'claimed_rewards': [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 15, 22],
            'previous_era_rewards': 14360,
            'system_properties': {
                'ss58Format': 2,
                'tokenDecimals': [12],
                'tokenSymbol': ['TEST']
            }
        }
        self.retrieved_websocket_indirect_data_non_validator = {
            'current_session': 50,
            'current_era': 23,
            'authored_blocks': 0,
            'active': False,
            'elected': False,
            'disabled': False,
            'eras_stakers': {"total": None, "own": None, "others": []},
            'sent_heartbeat': False,
            'controller_address': None,
            'history_depth_eras': 84,
            'unclaimed_rewards': [],
            'claimed_rewards': [],
            'previous_era_rewards': 0,
            'system_properties': {
                'ss58Format': 2,
                'tokenDecimals': [12],
                'tokenSymbol': ['TEST']
            }
        }
        self.retrieved_websocket_archive_data_validator = {
            'historical': [
                {
                    'height': 52,
                    'slashed': True,
                    'slashed_amount': 1234560000000,
                    'is_offline': False,
                },
                {
                    'height': 51,
                    'slashed': False,
                    'slashed_amount': 0,
                    'is_offline': True,
                },
                {
                    'height': 50,
                    'slashed': False,
                    'slashed_amount': 0,
                    'is_offline': False,
                },
            ],
        }
        self.retrieved_websocket_archive_data_non_validator = {'historical': []}
        self.retrieved_websocket_data_validator = {
            **self.retrieved_websocket_direct_data,
            **self.retrieved_websocket_indirect_data_validator,
            **self.retrieved_websocket_archive_data_validator
        }
        self.retrieved_websocket_data_non_validator = {
            **self.retrieved_websocket_direct_data,
            **self.retrieved_websocket_indirect_data_non_validator,
            **self.retrieved_websocket_archive_data_non_validator
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
        self.test_monitor = SubstrateNodeMonitor(
            self.monitor_name, self.data_sources[2], self.dummy_logger,
            self.monitoring_period, self.rabbitmq, self.data_sources,
        )

        self.received_retrieval_info_all_source_types_enabled = {
            'websocket': {
                'data': self.retrieved_websocket_data_validator,
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

    def test_node_config_returns_node_config(self) -> None:
        self.assertEqual(self.data_sources[2], self.test_monitor.node_config)

    def test_pruning_catchup_blocks_returns_pruning_catchup_blocks(
            self) -> None:
        # Test that on init, pruning_catchup_blocks is 246
        self.assertEqual(246, self.test_monitor.pruning_catchup_blocks)

        # Test that the property returns the correct value
        self.test_monitor._pruning_catchup_blocks = 100
        self.assertEqual(100, self.test_monitor.pruning_catchup_blocks)

    def test_max_catchup_blocks_returns_max_catchup_blocks(self) -> None:
        # Test that on init, max_catchup_blocks is 300
        self.assertEqual(300, self.test_monitor.max_catchup_blocks)

        # Test that the property returns the correct value
        self.test_monitor._max_catchup_blocks = 400
        self.assertEqual(400, self.test_monitor.max_catchup_blocks)

    def test_archive_nodes_returns_archive_nodes(self) -> None:
        self.assertEqual([self.data_sources[1], self.data_sources[2]],
                         self.test_monitor.archive_nodes)

    def test_last_height_monitored_websocket_returns_lh_monitored_websocket(
            self) -> None:
        # Test that on init, last_height_monitored_tendermint is None
        self.assertIsNone(self.test_monitor.last_height_monitored_websocket)

        # Test that the property returns the correct value
        self.test_monitor._last_height_monitored_websocket = 500
        self.assertEqual(500, self.test_monitor.last_height_monitored_websocket)

    @mock.patch.object(SubstrateApiWrapper, 'get_finalized_head')
    @mock.patch.object(SubstrateApiWrapper, 'get_sync_state')
    @mock.patch.object(SubstrateApiWrapper, 'get_header')
    def test_get_websocket_direct_data_return(
            self, mock_get_header, mock_get_sync_state,
            mock_get_finalized_head) -> None:
        mock_get_finalized_head.return_value = {
            "result": "0x32e3e412ccb6a2804587f17f25b37fef6c195ef786ed6e82e9bc"
        }
        mock_get_sync_state.return_value = {
            "result": {
                "startingBlock": 5,
                "currentBlock":
                    self.retrieved_websocket_direct_data['best_height'],
                "highestBlock":
                    self.retrieved_websocket_direct_data['target_height']
            }
        }
        mock_get_header.return_value = {
            "result": {
                "parentHash": "0xf8b3412e4c40f4311fbfef8e18117084ef074b8",
                "number":
                    self.retrieved_websocket_direct_data['finalized_height']
            }
        }
        actual_return = self.test_monitor._get_websocket_direct_data()
        self.assertEqual(self.retrieved_websocket_direct_data, actual_return)

    @mock.patch.object(SubstrateApiWrapper, 'get_received_heartbeats')
    @mock.patch.object(SubstrateApiWrapper, 'get_eras_reward_points')
    @mock.patch.object(SubstrateApiWrapper, 'get_staking_ledger')
    @mock.patch.object(SubstrateApiWrapper, 'get_eras_stakers')
    @mock.patch.object(SubstrateApiWrapper, 'get_authored_blocks')
    @mock.patch.object(SubstrateApiWrapper, 'get_system_properties')
    @mock.patch.object(SubstrateApiWrapper, 'get_staking_bonded')
    @mock.patch.object(SubstrateApiWrapper, 'get_disabled_validators')
    @mock.patch.object(SubstrateApiWrapper, 'get_staking_validators')
    @mock.patch.object(SubstrateApiWrapper, 'get_history_depth')
    @mock.patch.object(SubstrateApiWrapper, 'get_active_era')
    @mock.patch.object(SubstrateApiWrapper, 'get_current_index')
    def test_get_websocket_indirect_data_validator_return(
            self, mock_get_current_index, mock_get_active_era,
            mock_get_history_depth, mock_get_staking_validators,
            mock_get_disabled_validators, mock_get_staking_bonded,
            mock_get_system_properties, mock_get_authored_blocks,
            mock_get_eras_stakers, mock_get_staking_ledger,
            mock_get_eras_reward_points, mock_get_received_heartbeats) -> None:
        mock_get_current_index.return_value = {"result": "0x00000032"}
        mock_get_active_era.return_value = {"result": {"index": 23}}
        mock_get_history_depth.return_value = {"result": "0x00000054"}
        mock_get_staking_validators.return_value = {
            "result": {
                "nextElected": ['stash_2', 'stash_3', self.stash_address_1],
                "validators": ['stash_2', self.stash_address_1, 'stash_3']
            }
        }
        mock_get_disabled_validators.return_value = {"result": []}
        mock_get_staking_bonded.return_value = {
            "result": self.controller_address_1
        }
        mock_get_system_properties.return_value = {
            'result': {
                'ss58Format': 2,
                'tokenDecimals': [12],
                'tokenSymbol': ['TEST']
            }
        }
        mock_get_authored_blocks.return_value = {"result": "0x00000005"}
        mock_get_eras_stakers.return_value = {
            "result": {
                "total": "0x00000000000000000048a4faa9941924",
                "own": 100001845000000,
                "others": [
                    {
                        "who": "1481ZvmVcwvH4tEpRJ66x199EQCWJg8vqAd8oYfnMw",
                        "value": 2696607929740009
                    },
                ]
            }
        }
        mock_get_staking_ledger.return_value = {
            "result": {
                "stash": self.stash_address_1,
                "total": 200001845000000,
                "active": 100001845000000,
                "unlocking": [
                    {
                        "value": 100000000000000,
                        "era": 698
                    }
                ],
                "claimedRewards": [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 15, 22]
            }
        }
        mock_get_eras_reward_points.return_value = {
            "result": {
                "total": 8065560,
                "individual": {
                    "stash2": 14360,
                    "stash3": 14420,
                    self.stash_address_1: 14360
                }
            }
        }
        mock_get_received_heartbeats.return_value = {"result": None}

        self.assertTrue(
            self.test_monitor.system_properties_limiter.can_do_task())

        actual_return = (
            self.test_monitor._get_websocket_indirect_data_validator(
                self.data_sources[0]))

        self.assertEqual(self.retrieved_websocket_indirect_data_validator,
                         actual_return)

        self.assertFalse(
            self.test_monitor.system_properties_limiter.can_do_task())

    @mock.patch.object(SubstrateApiWrapper, 'get_system_properties')
    @mock.patch.object(SubstrateApiWrapper, 'get_history_depth')
    @mock.patch.object(SubstrateApiWrapper, 'get_active_era')
    @mock.patch.object(SubstrateApiWrapper, 'get_current_index')
    def test_get_websocket_indirect_data_non_validator_return(
            self, mock_get_current_index, mock_get_active_era,
            mock_get_history_depth, mock_get_system_properties) -> None:
        mock_get_current_index.return_value = {"result": "0x00000032"}
        mock_get_active_era.return_value = {"result": {"index": 23}}
        mock_get_history_depth.return_value = {"result": "0x00000054"}
        mock_get_system_properties.return_value = {
            'result': {
                'ss58Format': 2,
                'tokenDecimals': [12],
                'tokenSymbol': ['TEST']
            }
        }

        actual_return = \
            self.test_monitor._get_websocket_indirect_data_non_validator(
                self.data_sources[0])

        self.assertEqual(self.retrieved_websocket_indirect_data_non_validator,
                         actual_return)

    def test_get_websocket_indirect_data_return_if_empty_source_url(
            self) -> None:
        """
        We will perform this test for both when the node being monitored is a
        validator, and for when it is not
        """
        expected_ret = {
            'current_session': None,
            'current_era': None,
            'authored_blocks': None,
            'active': None,
            'elected': None,
            'disabled': None,
            'eras_stakers': None,
            'sent_heartbeat': None,
            'controller_address': None,
            'history_depth_eras': None,
            'unclaimed_rewards': None,
            'claimed_rewards': None,
            'previous_era_rewards': None,
            'system_properties': None
        }
        self.data_sources[0]._node_ws_url = ''

        # Test for when the node being monitored is a validator
        self.test_monitor.node_config._is_validator = True
        actual_ret = self.test_monitor._get_websocket_indirect_data(
            self.data_sources[0])
        self.assertEqual(expected_ret, actual_ret)

        # Test for when the node being monitored is a non-validator
        self.test_monitor.node_config._is_validator = False
        actual_ret = self.test_monitor._get_websocket_indirect_data(
            self.data_sources[0])
        self.assertEqual(expected_ret, actual_ret)

    @mock.patch.object(SubstrateNodeMonitor,
                       '_get_websocket_indirect_data_validator')
    @mock.patch.object(SubstrateNodeMonitor,
                       '_get_websocket_indirect_data_non_validator')
    def test_get_websocket_indirect_data_return(self, mock_get_non_validator,
                                                mock_get_validator) -> None:
        """
        This test will be performed for both when the node being monitored is
        a validator, and for when it is not a validator. Note that we will
        assume that a data source with a proper websocket url was selected.
        """
        mock_get_non_validator.return_value = \
            self.retrieved_websocket_indirect_data_non_validator
        mock_get_validator.return_value = \
            self.retrieved_websocket_indirect_data_validator

        # Test for when the node being monitored is a validator
        self.test_monitor.node_config._is_validator = True
        actual_ret = self.test_monitor._get_websocket_indirect_data(
            self.data_sources[0])
        self.assertEqual(self.retrieved_websocket_indirect_data_validator,
                         actual_ret)

        # Test for when the node being monitored is a non-validator
        self.test_monitor.node_config._is_validator = False
        actual_ret = self.test_monitor._get_websocket_indirect_data(
            self.data_sources[0])
        self.assertEqual(self.retrieved_websocket_indirect_data_non_validator,
                         actual_ret)

    @parameterized.expand([
        (None, 1000, True, 999,),
        (None, 1000, False, 999,),
        (988, 1000, True, 988,),
        (988, 1000, False, 988,),
        (754, 1000, True, 754,),
        (754, 1000, False, 754,),
        (753, 1000, True, 753,),
        (753, 1000, False, 754,),
        (743, 1000, False, 754,),
        (700, 1000, True, 700,),
        (699, 1000, True, 700,),
    ])
    def test_determine_last_height_monitored_websocket(
            self, current_last_height, current_height, is_source_archive,
            expected_return) -> None:
        """
        In this test we will check that
        _determine_last_height_monitored_websocket is determined correctly for
        different input types.
        """
        actual_return = \
            self.test_monitor._determine_last_height_monitored_websocket(
                current_last_height, current_height, is_source_archive)
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(SubstrateApiWrapper, 'get_is_offline')
    @mock.patch.object(SubstrateApiWrapper, 'get_slashed_amount')
    @mock.patch.object(SubstrateApiWrapper, 'get_block_hash')
    @mock.patch.object(SubstrateNodeMonitor,
                       '_determine_last_height_monitored_websocket')
    @mock.patch.object(SubstrateApiWrapper, 'get_header')
    @mock.patch.object(SubstrateApiWrapper, 'get_finalized_head')
    def test_get_websocket_archive_data_validator_return(
            self, mock_get_finalized_head, mock_get_header, mock_determine_lhm,
            mock_get_block_hash, mock_get_slashed_amount,
            mock_get_is_offline) -> None:
        mock_get_finalized_head.return_value = {
            "result": "0xe27d6f3cc8976a1b88d4e88c77be1b0d19c347b13185bd0d806646"
        }
        mock_get_header.return_value = {"result": {"number": 52}}
        mock_determine_lhm.return_value = 49
        mock_get_block_hash.return_value = {
            "result": "0xed3c6d5e806a89f7945fad7db543f90f8ffceef9e1079d7a6669ab"
        }
        mock_get_slashed_amount.side_effect = [
            {"result": 0}, {"result": 0}, {"result": 1234560000000}
        ]
        mock_get_is_offline.side_effect = [
            {"result": False}, {"result": True}, {"result": False}
        ]

        actual_return = \
            self.test_monitor._get_websocket_archive_data_validator(
                self.data_sources[1])

        self.assertEqual(self.retrieved_websocket_archive_data_validator,
                         actual_return)

    def test_get_websocket_archive_data_non_validator_return(self) -> None:
        actual_return = \
            self.test_monitor._get_websocket_archive_data_non_validator()
        self.assertEqual(self.retrieved_websocket_archive_data_non_validator,
                         actual_return)

    def test_get_websocket_archive_data_return_if_empty_source_url(
            self) -> None:
        """
        We will perform this test for both when the node being monitored is a
        validator, and for when it is not
        """
        expected_ret = {'historical': None}
        self.data_sources[1]._node_ws_url = ''

        # Test for when the node being monitored is a validator
        self.test_monitor.node_config._is_validator = True
        actual_ret = self.test_monitor._get_websocket_archive_data(
            self.data_sources[1])
        self.assertEqual(expected_ret, actual_ret)

        # Test for when the node being monitored is a non-validator
        self.test_monitor.node_config._is_validator = False
        actual_ret = self.test_monitor._get_websocket_archive_data(
            self.data_sources[1])
        self.assertEqual(expected_ret, actual_ret)

    @mock.patch.object(SubstrateNodeMonitor,
                       '_get_websocket_archive_data_validator')
    @mock.patch.object(SubstrateNodeMonitor,
                       '_get_websocket_archive_data_non_validator')
    def test_get_websocket_archive_data_return(self, mock_get_non_validator,
                                               mock_get_validator) -> None:
        """
        This test will be performed for both when the node being monitored is
        a validator, and for when it is not a validator. Note that we will
        assume that a data source with a proper websocket url was selected.
        """
        mock_get_non_validator.return_value = \
            self.retrieved_websocket_archive_data_non_validator
        mock_get_validator.return_value = \
            self.retrieved_websocket_archive_data_validator

        # Test for when the node being monitored is a validator
        self.test_monitor.node_config._is_validator = True
        actual_ret = self.test_monitor._get_websocket_archive_data(
            self.data_sources[1])
        self.assertEqual(self.retrieved_websocket_archive_data_validator,
                         actual_ret)

        # Test for when the node being monitored is a non-validator
        self.test_monitor.node_config._is_validator = False
        actual_ret = self.test_monitor._get_websocket_archive_data(
            self.data_sources[1])
        self.assertEqual(self.retrieved_websocket_archive_data_non_validator,
                         actual_ret)

    @mock.patch.object(SubstrateNodeMonitor, '_select_websocket_node')
    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_direct_data')
    def test_get_websocket_data_return_if_no_indirect_source_selected(
            self, mock_get_direct_data, mock_select_websocket_node) -> None:
        mock_get_direct_data.return_value = self.retrieved_websocket_direct_data
        mock_select_websocket_node.return_value = None
        expected_return = ({}, True, NoSyncedDataSourceWasAccessibleException(
            self.monitor_name, 'indirect Substrate websocket node'))

        actual_return = self.test_monitor._get_websocket_data()
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_archive_data')
    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_indirect_data')
    @mock.patch.object(SubstrateNodeMonitor, '_select_websocket_node')
    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_direct_data')
    def test_get_websocket_data_uses_indirect_source_as_archive_if_no_selected(
            self, mock_get_direct_data, mock_select_node, mock_get_indirect,
            mock_get_archive) -> None:
        mock_get_direct_data.return_value = self.retrieved_websocket_direct_data
        mock_select_node.side_effect = [self.data_sources[0], None]
        mock_get_indirect.return_value = \
            self.retrieved_websocket_indirect_data_validator
        mock_get_archive.return_value = \
            self.retrieved_websocket_archive_data_validator

        self.test_monitor._get_websocket_data()
        mock_get_archive.assert_called_once_with(self.data_sources[0])

    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_archive_data')
    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_indirect_data')
    @mock.patch.object(SubstrateNodeMonitor, '_select_websocket_node')
    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_direct_data')
    def test_get_websocket_data_return_if_data_retrieval_successful(
            self, mock_get_direct_data, mock_select_node, mock_get_indirect,
            mock_get_archive) -> None:
        mock_get_direct_data.return_value = self.retrieved_websocket_direct_data
        mock_select_node.side_effect = [self.data_sources[0],
                                        self.data_sources[1]]
        mock_get_indirect.return_value = \
            self.retrieved_websocket_indirect_data_validator
        mock_get_archive.return_value = \
            self.retrieved_websocket_archive_data_validator

        expected_return = (self.retrieved_websocket_data_validator, False, None)
        actual_return = self.test_monitor._get_websocket_data()
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        (SubstrateApiIsNotReachableException('test_monitor', 'api_url'),
         SubstrateApiIsNotReachableException),
        (DataReadingException('test_monitor', 'ws_url_1'),
         DataReadingException),
        (IncorrectJSONRetrievedException('substrate_api', 'err'),
         SubstrateWebSocketDataCouldNotBeObtained),
        (NodeIsDownException('node_name_1'), NodeIsDownException),
        (SubstrateApiCallException('api_call', 'err'),
         SubstrateApiCallException),
    ])
    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_direct_data')
    def test_get_websocket_data_return_if_expected_error_in_data_retrieval(
            self, error_raised, error_instance_returned,
            mock_get_direct_data) -> None:
        mock_get_direct_data.side_effect = error_raised
        actual_return = self.test_monitor._get_websocket_data()
        self.assertEqual({}, actual_return[0])
        self.assertEqual(True, actual_return[1])
        self.assertIsInstance(actual_return[2], error_instance_returned)

    @parameterized.expand([
        ('self.received_retrieval_info_all_source_types_enabled',
         ['self.retrieved_websocket_data_validator', False, None], True),
        ('self.received_retrieval_info_some_sources_disabled', None, False),
        ('self.received_retrieval_info_all_source_types_enabled_err',
         [{}, True, PANICException('test_exception_1', 1)], True),
    ])
    @mock.patch.object(SubstrateNodeMonitor, '_get_websocket_data')
    def test_get_data_return(
            self, expected_ret, retrieved_websocket_data, monitor_websocket,
            mock_get_websocket_data) -> None:
        """
        In this test we will check that the retrieval info is returned correctly
        for every possible test case. We will use parameterized.expand to
        explore all possible cases.
        TODO: Once we add more data sources this test must be populated with
              more cases. Also, the logic would no longer have
              monitor_node <=> monitor_websocket
        """
        if monitor_websocket:
            # If websocket is to be monitored, then we have a list which needs
            # to be converted to a tuple
            if retrieved_websocket_data[0]:
                # If the first element is a variable evaluate it
                retrieved_websocket_data[0] = eval(retrieved_websocket_data[0])
            mock_get_websocket_data.return_value = tuple(
                retrieved_websocket_data)
        self.test_monitor._node_config._monitor_node = monitor_websocket

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
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp(),
                    'is_validator': self.test_monitor.node_config.is_validator,
                    'stash_address': self.test_monitor.node_config.stash_address
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
                    'monitor_name': self.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_validator': self.test_monitor.node_config.is_validator,
                    'stash_address': self.test_monitor.node_config.stash_address
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
            routing_key=SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY)

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
        self.assertEqual(self.test_data_dict,
                         json.loads(body))

    @freeze_time("2012-01-01")
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data, mock_send_heartbeat, mock_send_data) -> None:
        # Here we are assuming that all sources are enabled.
        expected_output_data = {
            'websocket': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp(),
                        'is_validator':
                            self.test_monitor.node_config.is_validator,
                        'stash_address':
                            self.test_monitor.node_config.stash_address
                    },
                    'data': self.retrieved_websocket_data_validator,
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
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
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
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_process_data")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
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

    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
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
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
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
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
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
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
    def test_monitor_logs_data_if_all_sources_enabled_and_no_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        expected_logged_data = self.test_monitor._display_data({
            'websocket': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp(),
                        'is_validator':
                            self.test_monitor.node_config.is_validator,
                        'stash_address':
                            self.test_monitor.node_config.stash_address
                    },
                    'data': self.retrieved_websocket_data_validator,
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
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
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
    @mock.patch.object(SubstrateNodeMonitor, "_send_heartbeat")
    @mock.patch.object(SubstrateNodeMonitor, "_send_data")
    @mock.patch.object(SubstrateNodeMonitor, "_get_data")
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
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp(),
                        'is_validator':
                            self.test_monitor.node_config.is_validator,
                        'stash_address':
                            self.test_monitor.node_config.stash_address
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
