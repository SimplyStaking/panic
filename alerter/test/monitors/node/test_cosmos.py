import copy
import json
import logging
import unittest
from datetime import timedelta, datetime
from http.client import IncompleteRead
from typing import Dict
from unittest import mock

from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from requests.exceptions import (ConnectionError as ReqConnectionError,
                                 ReadTimeout, ChunkedEncodingError,
                                 MissingSchema, InvalidSchema, InvalidURL)
from urllib3.exceptions import ProtocolError

from src.api_wrappers.cosmos import (CosmosRestServerApiWrapper,
                                     TendermintRpcApiWrapper)
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.node.cosmos import CosmosNodeMonitor
from src.utils import env
from src.utils.constants.cosmos import (
    BOND_STATUS_BONDED, BOND_STATUS_UNBONDED, BOND_STATUS_UNBONDING,
    BOND_STATUS_INVALID)
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, RAW_DATA_EXCHANGE, COSMOS_NODE_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    PANICException, NoSyncedDataSourceWasAccessibleException,
    NodeIsDownException, InvalidUrlException,
    CosmosSDKVersionIncompatibleException, CosmosRestServerApiCallException,
    DataReadingException, CannotConnectWithDataSourceException,
    IncorrectJSONRetrievedException, CosmosRestServerDataCouldNotBeObtained,
    TendermintRPCCallException, TendermintRPCDataCouldNotBeObtained,
    TendermintRPCIncompatibleException, MetricNotFoundException,
    MessageWasNotDeliveredException)
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit, assert_not_called_with)
from test.utils.cosmos.cosmos import CosmosTestNodes


class TestCosmosNodeMonitor(unittest.TestCase):
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
        self.test_exception_2 = PANICException('test_exception_2', 2)
        self.test_exception_3 = PANICException('test_exception_3', 3)
        self.sdk_version_0_39_2 = 'v0.39.2'
        self.sdk_version_0_42_6 = 'v0.42.6'
        self.test_consensus_address = 'test_consensus_address'
        self.test_is_syncing = False
        self.test_is_peered_with_sentinel = True


        # --------------- Data retrieval variables and examples ---------------
        # Prometheus
        self.prometheus_metrics = {
            'tendermint_consensus_latest_block_height': 'strict',
            'tendermint_consensus_validator_power': 'optional',
        }
        self.retrieved_prometheus_data_example_1 = {
            'tendermint_consensus_latest_block_height': {
                '{"chain_id": "cosmoshub-4"}': 8137538.0
            },
            'tendermint_consensus_validator_power': {
                '{"chain_id": "cosmoshub-4", "validator_address": '
                '"7B3D01F754DFF8474ED0E358812FD437E09389DC"}': 725315.0
            }
        }
        self.retrieved_prometheus_data_example_2 = {
            'tendermint_consensus_latest_block_height': {
                '{"chain_id": "cosmoshub-4"}': 538.0
            },
            'tendermint_consensus_validator_power': {
                '{"chain_id": "cosmoshub-4", "validator_address": '
                '"7B3D01F754DFF8474ED0E358812FD437E09389DC"}': None
            }
        }

        # Rest
        self.retrieved_cosmos_rest_indirect_data_1 = {
            'bond_status': BOND_STATUS_BONDED,
            'jailed': False
        }
        self.retrieved_cosmos_rest_indirect_data_2 = {
            'bond_status': BOND_STATUS_UNBONDED,
            'jailed': True
        }
        self.retrieved_cosmos_rest_data_1 = {
            **self.retrieved_cosmos_rest_indirect_data_1,
        }

        # Tendermint
        self.retrieved_tendermint_direct_data_mev = {
            'consensus_hex_address': self.test_consensus_address,
            'is_syncing': self.test_is_syncing,
            'is_peered_with_sentinel': True,
        }

        self.retrieved_tendermint_direct_data_not_mev = {
            'consensus_hex_address': self.test_consensus_address,
            'is_syncing': self.test_is_syncing,
        }

        self.retrieved_tendermint_archive_data = {
            'historical': [
                {
                    'height': 52,
                    'active_in_prev_block': True,
                    'signed_prev_block': True,
                    'slashed': True,
                    'slashed_amount': 1000
                },
                {
                    'height': 51,
                    'active_in_prev_block': True,
                    'signed_prev_block': False,
                    'slashed': False,
                    'slashed_amount': None
                },
                {
                    'height': 50,
                    'active_in_prev_block': False,
                    'signed_prev_block': False,
                    'slashed': True,
                    'slashed_amount': None,
                },
            ],
        }
        self.retrieved_tendermint_rpc_data_not_mev = {
            **self.retrieved_tendermint_archive_data,
            'is_syncing': self.test_is_syncing,
        }

        self.retrieved_tendermint_rpc_data_mev = {
            **self.retrieved_tendermint_archive_data,
            'is_syncing': self.test_is_syncing,
            'is_peered_with_sentinel': True,
        }

        # Processed retrieved data example
        self.processed_prometheus_data_example_1 = {
            'tendermint_consensus_latest_block_height': 8137538.0,
            'tendermint_consensus_validator_power': 725315.0,
        }
        self.processed_prometheus_data_example_2 = {
            'tendermint_consensus_latest_block_height': 538.0,
            'tendermint_consensus_validator_power': 0,
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
        self.test_monitor = CosmosNodeMonitor(
            self.monitor_name, self.data_sources[2], self.dummy_logger,
            self.monitoring_period, self.rabbitmq, self.data_sources,
        )

        ## construct a node monintor for a mev-tendermint node
        self.test_monitor_mev = CosmosNodeMonitor(
            self.monitor_name, self.cosmos_test_nodes.is_mev_tendermint_node, self.dummy_logger,
            self.monitoring_period, self.rabbitmq, self.data_sources,
        )

        self.received_retrieval_info_all_source_types_enabled = {
            'prometheus': {
                'data': self.retrieved_prometheus_data_example_1,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_prometheus_data,
                'processing_function':
                    self.test_monitor._process_retrieved_prometheus_data,
                'monitoring_enabled': True
            },
            'cosmos_rest': {
                'data': self.retrieved_cosmos_rest_data_1,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_cosmos_rest_data,
                'processing_function':
                    self.test_monitor._process_retrieved_cosmos_rest_data,
                'monitoring_enabled': True
            },
            'tendermint_rpc': {
                'data': self.retrieved_tendermint_rpc_data_not_mev,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_tendermint_rpc_data,
                'processing_function':
                    self.test_monitor._process_retrieved_tendermint_rpc_data,
                'monitoring_enabled': True
            },
        }
        self.received_retrieval_info_some_sources_disabled = {
            'prometheus': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_prometheus_data,
                'processing_function':
                    self.test_monitor._process_retrieved_prometheus_data,
                'monitoring_enabled': False
            },
            'cosmos_rest': {
                'data': self.retrieved_cosmos_rest_data_1,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_cosmos_rest_data,
                'processing_function':
                    self.test_monitor._process_retrieved_cosmos_rest_data,
                'monitoring_enabled': True
            },
            'tendermint_rpc': {
                'data': self.retrieved_tendermint_rpc_data_mev,
                'data_retrieval_failed': False,
                'data_retrieval_exception': None,
                'get_function': self.test_monitor._get_tendermint_rpc_data,
                'processing_function':
                    self.test_monitor._process_retrieved_tendermint_rpc_data,
                'monitoring_enabled': True
            },
        }
        self.received_retrieval_info_all_source_types_enabled_err = {
            'prometheus': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': self.test_exception_1,
                'get_function': self.test_monitor._get_prometheus_data,
                'processing_function':
                    self.test_monitor._process_retrieved_prometheus_data,
                'monitoring_enabled': True
            },
            'cosmos_rest': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': self.test_exception_2,
                'get_function': self.test_monitor._get_cosmos_rest_data,
                'processing_function':
                    self.test_monitor._process_retrieved_cosmos_rest_data,
                'monitoring_enabled': True
            },
            'tendermint_rpc': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': self.test_exception_3,
                'get_function': self.test_monitor._get_tendermint_rpc_data,
                'processing_function':
                    self.test_monitor._process_retrieved_tendermint_rpc_data,
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
        self.test_exception_2 = None
        self.test_exception_3 = None
        self.cosmos_test_nodes.clear_attributes()
        self.cosmos_test_nodes = None
        self.test_monitor = None

    def test_node_config_returns_node_config(self) -> None:
        self.assertEqual(self.data_sources[2], self.test_monitor.node_config)

    def test_pruning_catchup_blocks_returns_pruning_catchup_blocks(
            self) -> None:
        # Test that on init, pruning_catchup_blocks is 90
        self.assertEqual(90, self.test_monitor.pruning_catchup_blocks)

        # Test that the property returns the correct value
        self.test_monitor._pruning_catchup_blocks = 100
        self.assertEqual(100, self.test_monitor.pruning_catchup_blocks)

    def test_max_catchup_blocks_returns_max_catchup_blocks(self) -> None:
        # Test that on init, max_catchup_blocks is 300
        self.assertEqual(300, self.test_monitor.max_catchup_blocks)

        # Test that the property returns the correct value
        self.test_monitor._max_catchup_blocks = 400
        self.assertEqual(400, self.test_monitor.max_catchup_blocks)

    def test_archive_nodes_returns_archive_nodes(
            self) -> None:
        self.assertEqual([self.data_sources[1], self.data_sources[2]],
                         self.test_monitor.archive_nodes)

    def test_prometheus_metrics_returns_prometheus_metrics(self) -> None:
        self.assertEqual(self.prometheus_metrics,
                         self.test_monitor.prometheus_metrics)

    def test_last_height_monitored_tendermint_ret_lh_monitored_tendermint(
            self) -> None:
        # Test that on init, last_height_monitored_tendermint is None
        self.assertIsNone(self.test_monitor.last_height_monitored_tendermint)

        # Test that the property returns the correct value
        self.test_monitor._last_height_monitored_tendermint = 500
        self.assertEqual(500,
                         self.test_monitor.last_height_monitored_tendermint)

    def test_validator_consensus_address_returns_validator_consensus_address(
            self) -> None:
        # Test that on init, validator_consensus_address is None
        self.assertIsNone(self.test_monitor.validator_consensus_address)

        # Test that the property returns the correct value
        self.test_monitor._validator_consensus_address = "test_val_1"
        self.assertEqual("test_val_1",
                         self.test_monitor.validator_consensus_address)

    @parameterized.expand([
        (0, BOND_STATUS_UNBONDED,),
        ('BOND_STATUS_UNBONDED', BOND_STATUS_UNBONDED,),
        (1, BOND_STATUS_UNBONDING,),
        ('BOND_STATUS_UNBONDING', BOND_STATUS_UNBONDING,),
        (2, BOND_STATUS_BONDED,),
        ('BOND_STATUS_BONDED', BOND_STATUS_BONDED,),
        ('INVALID_STATUS', BOND_STATUS_INVALID,),
        (45, BOND_STATUS_INVALID,),
    ])
    def test_parse_validator_status_return(
            self, validator_status, expected_return) -> None:
        """
        We will test that given the validator status, this function returns the
        correct status which is going to be consumed by all PANIC components.
        """
        actual_return = self.test_monitor._parse_validator_status(
            validator_status)
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ({"result": {"jailed": True, "status": 2, }},
         {'jailed': True, 'bond_status': BOND_STATUS_BONDED},),
        ({"result": {"jailed": False, "status": 1, }},
         {'jailed': False, 'bond_status': BOND_STATUS_UNBONDING},),
        ({"result": {"jailed": False, "status": 0, }},
         {'jailed': False, 'bond_status': BOND_STATUS_UNBONDED},),
    ])
    @mock.patch.object(CosmosRestServerApiWrapper,
                       'get_staking_validators_v0_39_2')
    def test_get_cosmos_rest_v0_39_2_indirect_data_validator_return(
            self, staking_validators_return, expected_return,
            mock_staking_validators) -> None:
        """
        We will check that the return is as expected for all cases
        """
        mock_staking_validators.return_value = staking_validators_return
        actual_return = \
            self.test_monitor._get_cosmos_rest_v0_39_2_indirect_data_validator(
                self.data_sources[0])
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ({"validator": {"jailed": True, "status": "BOND_STATUS_BONDED", }},
         {'jailed': True, 'bond_status': BOND_STATUS_BONDED},),
        ({"validator": {"jailed": False, "status": "BOND_STATUS_UNBONDING", }},
         {'jailed': False, 'bond_status': BOND_STATUS_UNBONDING},),
        ({"validator": {"jailed": False, "status": "BOND_STATUS_UNBONDED", }},
         {'jailed': False, 'bond_status': BOND_STATUS_UNBONDED},),
    ])
    @mock.patch.object(CosmosRestServerApiWrapper,
                       'get_staking_validators_v0_42_6')
    def test_get_cosmos_rest_v0_42_6_indirect_data_validator_return(
            self, staking_validators_return, expected_return,
            mock_staking_validators) -> None:
        """
        We will check that the return is as expected for all cases
        """
        mock_staking_validators.return_value = staking_validators_return
        actual_return = \
            self.test_monitor._get_cosmos_rest_v0_42_6_indirect_data_validator(
                self.data_sources[0])
        self.assertEqual(expected_return, actual_return)

    def test_get_cosmos_rest_indirect_data_return_if_empty_source_url(
            self) -> None:
        expected_ret = {
            'jailed': None,
            'bond_status': None,
        }
        self.data_sources[0]._cosmos_rest_url = ''

        # Test for v0.39.2
        actual_ret = self.test_monitor._get_cosmos_rest_indirect_data(
            self.data_sources[0], self.sdk_version_0_39_2)
        self.assertEqual(expected_ret, actual_ret)

        # Test for v0.42.6
        actual_ret = self.test_monitor._get_cosmos_rest_indirect_data(
            self.data_sources[0], self.sdk_version_0_42_6)
        self.assertEqual(expected_ret, actual_ret)

    def test_get_cosmos_rest_indirect_data_return_if_non_validator_node(
            self) -> None:
        expected_ret = {
            'jailed': False,
            'bond_status': BOND_STATUS_UNBONDED,
        }
        self.test_monitor.node_config._is_validator = False

        # Test for v0.39.2
        actual_ret = self.test_monitor._get_cosmos_rest_indirect_data(
            self.data_sources[0], self.sdk_version_0_39_2)
        self.assertEqual(expected_ret, actual_ret)

        # Test for v0.42.6
        actual_ret = self.test_monitor._get_cosmos_rest_indirect_data(
            self.data_sources[0], self.sdk_version_0_42_6)
        self.assertEqual(expected_ret, actual_ret)

    @mock.patch.object(CosmosNodeMonitor,
                       '_get_cosmos_rest_v0_39_2_indirect_data_validator')
    @mock.patch.object(CosmosNodeMonitor,
                       '_get_cosmos_rest_v0_42_6_indirect_data_validator')
    def test_get_cosmos_rest_indirect_data_return_if_validator_node(
            self, mock_get_42_indirect, mock_get_39_indirect) -> None:
        mock_get_42_indirect.return_value = \
            self.retrieved_cosmos_rest_indirect_data_1
        mock_get_39_indirect.return_value = \
            self.retrieved_cosmos_rest_indirect_data_2
        expected_invalid_version = {
            'bond_status': None,
            'jailed': None
        }

        # Test for v0.42.6
        actual_ret = self.test_monitor._get_cosmos_rest_indirect_data(
            self.data_sources[0], self.sdk_version_0_42_6)
        self.assertEqual(self.retrieved_cosmos_rest_indirect_data_1, actual_ret)

        # Test for v0.39.2
        actual_ret = self.test_monitor._get_cosmos_rest_indirect_data(
            self.data_sources[0], self.sdk_version_0_39_2)
        self.assertEqual(self.retrieved_cosmos_rest_indirect_data_2, actual_ret)

        # Test for invalid version
        actual_ret = self.test_monitor._get_cosmos_rest_indirect_data(
            self.data_sources[0], 'invalid_version')
        self.assertEqual(expected_invalid_version, actual_ret)

    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_rest_node')
    @mock.patch.object(CosmosNodeMonitor, '_cosmos_rest_reachable')
    def test_get_cosmos_rest_version_data_return_if_no_indirect_source_selected(
            self, mock_cosmos_rest_reachable, mock_select_cosmos_rest_node
    ) -> None:
        """
        We will test that if no indirect source is selected, the function
        returns ({}, True, NoSyncedDataSourceWasAccessibleException). This test
        will be performed for every supported cosmos sdk REST server version

        We assume the cosmos rest is reachable
        """
        mock_select_cosmos_rest_node.return_value = None
        mock_cosmos_rest_reachable.return_value = True, None
        actual_ret_v0_42_6 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_42_6)
        actual_ret_v0_39_2 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_39_2)
        self.assertEqual(({}, True, NoSyncedDataSourceWasAccessibleException(
            self.monitor_name, 'indirect Cosmos REST node')),
                         actual_ret_v0_42_6)
        self.assertEqual(({}, True, NoSyncedDataSourceWasAccessibleException(
            self.monitor_name, 'indirect Cosmos REST node')),
                         actual_ret_v0_39_2)

    @parameterized.expand([
        (NodeIsDownException('node_name_1'),),
        (DataReadingException('test_monitor', 'cosmos_rest_url_1'),),
        (InvalidUrlException('cosmos_rest_url_1'),),
        (CosmosSDKVersionIncompatibleException('node_name_1', 'v0.39.2'),),
        (CosmosRestServerApiCallException('test_call', 'err_msg'),),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_cosmos_rest_reachable')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_rest_node')
    def test_get_cosmos_rest_version_data_ret_if_node_not_reachable_at_rest_url(
            self, err, mock_select_cosmos_rest_node,
            mock_cosmos_rest_reachable) -> None:
        """
        We will test that if the node is not reachable at the cosmos REST url,
        then the function will return ({}, True, err), depending on which error
        is returned by the function. We will test different error returns via
        parameterized.expand, and test for all supported cosmos sdk versions
        """
        mock_select_cosmos_rest_node.return_value = self.data_sources[0]
        mock_cosmos_rest_reachable.return_value = (False, err)
        actual_ret_v0_42_6 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_42_6)
        actual_ret_v0_39_2 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_39_2)
        self.assertEqual(({}, True, err), actual_ret_v0_42_6)
        self.assertEqual(({}, True, err), actual_ret_v0_39_2)

    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_indirect_data')
    @mock.patch.object(CosmosNodeMonitor, '_cosmos_rest_reachable')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_rest_node')
    def test_get_cosmos_rest_version_data_return_if_data_obtained_successfully(
            self, mock_select_cosmos_rest_node, mock_cosmos_rest_reachable,
            mock_get_indirect_data) -> None:
        """
        In this test we will check that if indirect data is obtained
        successfully, the function returns ({indirect_data}, False, None). Note
        that this function assumes that the indirect source has been
        successfully chosen, and that the cosmos REST url of the node is
        directly reachable. In addition to this, we will perform this test for
        all supported cosmos sdk versions.
        """
        mock_select_cosmos_rest_node.return_value = self.data_sources[1]
        mock_cosmos_rest_reachable.return_value = (True, None)
        mock_get_indirect_data.side_effect = [
            self.retrieved_cosmos_rest_indirect_data_1,
            self.retrieved_cosmos_rest_indirect_data_2
        ]
        actual_ret_v0_42_6 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_42_6)
        actual_ret_v0_39_2 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_39_2)
        self.assertEqual(
            (self.retrieved_cosmos_rest_indirect_data_1, False, None),
            actual_ret_v0_42_6)
        self.assertEqual(
            (self.retrieved_cosmos_rest_indirect_data_2, False, None),
            actual_ret_v0_39_2)

    @parameterized.expand([
        (CannotConnectWithDataSourceException('test_monitor', 'node_name_1',
                                              'err'),),
        (DataReadingException('test_monitor', 'cosmos_rest_url_1'),),
        (InvalidUrlException('cosmos_rest_url_1'),),
        (CosmosSDKVersionIncompatibleException('node_name_1', 'v0.39.2'),),
        (CosmosRestServerApiCallException('test_call', 'err_msg'),),
        (IncorrectJSONRetrievedException('REST', 'err'),)
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_indirect_data')
    @mock.patch.object(CosmosNodeMonitor, '_cosmos_rest_reachable')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_rest_node')
    def test_get_cosmos_rest_version_data_ret_if_expected_err_in_data_retrieval(
            self, err, mock_select_cosmos_rest_node, mock_cosmos_rest_reachable,
            mock_get_indirect_data) -> None:
        """
        In this test we will check that if an expected error is returned while
        retrieving indirect data, the function returns ({}, True, err) depending
        on which error is returned. We will use parameterized.expand to test for
        multiple errors, and we will test for all supported sdk versions.
        """
        mock_select_cosmos_rest_node.return_value = self.data_sources[1]
        mock_cosmos_rest_reachable.return_value = (True, None)
        mock_get_indirect_data.side_effect = err
        actual_ret_v0_42_6 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_42_6)
        actual_ret_v0_39_2 = self.test_monitor._get_cosmos_rest_version_data(
            self.sdk_version_0_39_2)
        self.assertEqual(({}, True, err), actual_ret_v0_42_6)
        self.assertEqual(({}, True, err), actual_ret_v0_39_2)

    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_version_data')
    def test_get_cosmos_rest_v0_39_2_data_calls_get_cosmos_rest_version_data(
            self, mock_get_rest_version) -> None:
        """
        In this test we will be checking that self._get_cosmos_rest_v0_39_2_data
        calls self._get_cosmos_rest_version_data correctly.
        """
        mock_get_rest_version.return_value = None
        self.test_monitor._get_cosmos_rest_v0_39_2_data()
        mock_get_rest_version.assert_called_once_with(self.sdk_version_0_39_2)

    @parameterized.expand([
        (({}, True,
          CannotConnectWithDataSourceException('test_monitor', 'node_name_1',
                                               'err')),),
        (({}, True,
          DataReadingException('test_monitor', 'cosmos_rest_url_1')),),
        (({}, True, InvalidUrlException('cosmos_rest_url_1')),),
        (({}, True,
          CosmosSDKVersionIncompatibleException('node_name_1', 'v0.39.2')),),
        (({}, True, CosmosRestServerApiCallException('test_call', 'err_msg')),),
        (({}, True, IncorrectJSONRetrievedException('REST', 'err')),),
        (({}, True, NoSyncedDataSourceWasAccessibleException(
            'test_monitor_name', 'indirect Cosmos REST node')),),
        (({}, True, NodeIsDownException('node_name_1')),),
        (({'indirect_key': 34}, False, None),),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_version_data')
    def test_get_cosmos_rest_v0_39_2_data_returns_get_cosmos_rest_ver_data_ret(
            self, get_rest_version_data_ret, mock_get_rest_version) -> None:
        """
        In this test we will be checking that self._get_cosmos_rest_v0_39_2_data
        returns the value returned by self._get_cosmos_rest_version_data. We
        will test for every possible return that
        self._get_cosmos_rest_version_data might return using
        parameterized.expand
        """
        mock_get_rest_version.return_value = get_rest_version_data_ret
        actual_ret = self.test_monitor._get_cosmos_rest_v0_39_2_data()
        self.assertEqual(get_rest_version_data_ret, actual_ret)

    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_version_data')
    def test_get_cosmos_rest_v0_42_6_data_calls_get_cosmos_rest_version_data(
            self, mock_get_rest_version) -> None:
        """
        In this test we will be checking that self._get_cosmos_rest_v0_42_6_data
        calls self._get_cosmos_rest_version_data correctly.
        """
        mock_get_rest_version.return_value = None
        self.test_monitor._get_cosmos_rest_v0_42_6_data()
        mock_get_rest_version.assert_called_once_with(self.sdk_version_0_42_6)

    @parameterized.expand([
        (({}, True,
          CannotConnectWithDataSourceException('test_monitor', 'node_name_1',
                                               'err')),),
        (({}, True,
          DataReadingException('test_monitor', 'cosmos_rest_url_1')),),
        (({}, True, InvalidUrlException('cosmos_rest_url_1')),),
        (({}, True,
          CosmosSDKVersionIncompatibleException('node_name_1', 'v0.42.6')),),
        (({}, True, CosmosRestServerApiCallException('test_call', 'err_msg')),),
        (({}, True, IncorrectJSONRetrievedException('REST', 'err')),),
        (({}, True, NoSyncedDataSourceWasAccessibleException(
            'test_monitor_name', 'indirect Cosmos REST node')),),
        (({}, True, NodeIsDownException('node_name_1')),),
        (({'indirect_key': 34}, False, None),),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_version_data')
    def test_get_cosmos_rest_v0_42_6_data_returns_get_cosmos_rest_ver_data_ret(
            self, get_rest_version_data_ret, mock_get_rest_version) -> None:
        """
        In this test we will be checking that self._get_cosmos_rest_v0_42_6_data
        returns the value returned by self._get_cosmos_rest_version_data. We
        will test for every possible return that
        self._get_cosmos_rest_version_data might return using
        parameterized.expand
        """
        mock_get_rest_version.return_value = get_rest_version_data_ret
        actual_ret = self.test_monitor._get_cosmos_rest_v0_42_6_data()
        self.assertEqual(get_rest_version_data_ret, actual_ret)

    @parameterized.expand([
        (({}, True,
          CannotConnectWithDataSourceException('test_monitor', 'node_name_1',
                                               'err')),),
        (({}, True,
          DataReadingException('test_monitor', 'cosmos_rest_url_1')),),
        (({}, True, InvalidUrlException('cosmos_rest_url_1')),),
        (({}, True, CosmosRestServerApiCallException('test_call', 'err_msg')),),
        (({}, True, NoSyncedDataSourceWasAccessibleException(
            'test_monitor_name', 'indirect Cosmos REST node')),),
        (({}, True, NodeIsDownException('node_name_1')),),
        (({'indirect_key': 34}, False, None),),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_42_6_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_39_2_data')
    def test_get_cosmos_rest_data_uses_last_retrieval_fn_used_first(
            self, retrieval_ret, mock_get_cosmos_rest_v0_39_2,
            mock_get_cosmos_rest_v0_42_6) -> None:
        """
        In this test we will check that first the self._get_cosmos_rest_data
        function first attempts to retrieve data using the last used retrieval
        function. In order to test this we need to assume that no
        incompatibility error is raised by the retrieval fn, otherwise the other
        retrievals will be executed. For this test we will set
        _last_rest_retrieval_version to different values to make sure that the
        test is sound
        """
        mock_get_cosmos_rest_v0_39_2.return_value = retrieval_ret
        mock_get_cosmos_rest_v0_42_6.return_value = retrieval_ret

        # Test for v0.39.2
        self.test_monitor._last_rest_retrieval_version = self.sdk_version_0_39_2
        self.test_monitor._get_cosmos_rest_data()
        mock_get_cosmos_rest_v0_39_2.assert_called_once()
        mock_get_cosmos_rest_v0_42_6.assert_not_called()
        mock_get_cosmos_rest_v0_39_2.reset_mock()
        mock_get_cosmos_rest_v0_42_6.reset_mock()

        # Test for v0.42.6
        self.test_monitor._last_rest_retrieval_version = self.sdk_version_0_42_6
        self.test_monitor._get_cosmos_rest_data()
        mock_get_cosmos_rest_v0_39_2.assert_not_called()
        mock_get_cosmos_rest_v0_42_6.assert_called_once()

    @parameterized.expand([
        (({}, True, IncorrectJSONRetrievedException('REST', 'err')),),
        (({}, True,
          CosmosSDKVersionIncompatibleException('node_name_1', 'version')),),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_42_6_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_39_2_data')
    def test_get_cosmos_rest_data_attempts_other_rets_if_last_incompatible(
            self, retrieval_ret, mock_get_cosmos_rest_v0_39_2,
            mock_get_cosmos_rest_v0_42_6) -> None:
        """
        In this test we will check that other retrievals are performed if the
        last retrieval performed raises an incompatibility error
        """
        # Test for v0.39.2
        mock_get_cosmos_rest_v0_39_2.return_value = retrieval_ret
        mock_get_cosmos_rest_v0_42_6.return_value = \
            (self.retrieved_cosmos_rest_data_1, False, None)
        self.test_monitor._last_rest_retrieval_version = self.sdk_version_0_39_2
        self.test_monitor._get_cosmos_rest_data()
        mock_get_cosmos_rest_v0_39_2.assert_called_once()
        mock_get_cosmos_rest_v0_42_6.assert_called_once()
        mock_get_cosmos_rest_v0_39_2.reset_mock()
        mock_get_cosmos_rest_v0_42_6.reset_mock()

        # Test for v0.42.6
        mock_get_cosmos_rest_v0_39_2.return_value = \
            (self.retrieved_cosmos_rest_data_1, False, None)
        mock_get_cosmos_rest_v0_42_6.return_value = retrieval_ret
        self.test_monitor._last_rest_retrieval_version = self.sdk_version_0_42_6
        self.test_monitor._get_cosmos_rest_data()
        mock_get_cosmos_rest_v0_39_2.assert_called_once()
        mock_get_cosmos_rest_v0_42_6.assert_called_once()

    @parameterized.expand([
        (({}, True,
          CannotConnectWithDataSourceException('test_monitor', 'node_name_1',
                                               'err')),),
        (({}, True,
          DataReadingException('test_monitor', 'cosmos_rest_url_1')),),
        (({}, True, InvalidUrlException('cosmos_rest_url_1')),),
        (({}, True, CosmosRestServerApiCallException('test_call', 'err_msg')),),
        (({}, True, NoSyncedDataSourceWasAccessibleException(
            'test_monitor_name', 'indirect Cosmos REST node')),),
        (({}, True, NodeIsDownException('node_name_1')),),
        (({'indirect_key': 34}, False, None),),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_42_6_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_39_2_data')
    def test_get_cosmos_rest_data_ret_retrieval_ret_if_no_incompatibility_err(
            self, retrieval_ret, mock_get_cosmos_rest_v0_39_2,
            mock_get_cosmos_rest_v0_42_6) -> None:
        """
        In this test we will check that if data retrieval occurs without an
        incompatibility error being returned, then the function returns whatever
        the retrieval returns. We will perform this test using
        parameterized.expand to cater for all possible avenues. Note that first
        we will test for when the last retrieval used function is successful,
        and then for when the last retrieval used function returns an
        incompatibility error and another supported version is successful.
        """
        self.test_monitor._last_rest_retrieval_version = self.sdk_version_0_42_6

        # Test for when the last used retrieval function does not return an
        # incompatibility error
        mock_get_cosmos_rest_v0_42_6.return_value = retrieval_ret
        actual_ret = self.test_monitor._get_cosmos_rest_data()
        self.assertEqual(retrieval_ret, actual_ret)
        mock_get_cosmos_rest_v0_42_6.reset_mock()

        # Test for when the last used retrieval function returns an
        # incompatibility error but other retrieval functions do not
        mock_get_cosmos_rest_v0_42_6.return_value = \
            ({}, True,
             CosmosSDKVersionIncompatibleException('node_name_1', 'v0.42.6'))
        mock_get_cosmos_rest_v0_39_2.return_value = retrieval_ret
        actual_ret = self.test_monitor._get_cosmos_rest_data()
        self.assertEqual(retrieval_ret, actual_ret)

    @parameterized.expand([
        (({}, True, IncorrectJSONRetrievedException('REST', 'err')),),
        (({}, True,
          CosmosSDKVersionIncompatibleException('node_name_1', 'version')),),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_42_6_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_v0_39_2_data')
    def test_get_cosmos_rest_data_ret_if_incompatibility_issue_and_unsuccessful(
            self, retrieval_ret, mock_get_cosmos_rest_v0_39_2,
            mock_get_cosmos_rest_v0_42_6) -> None:
        """
        In this test we will check that if incompatibility issues persist for
        every supported version, then the function returns ({}, True,
        CosmosRestServerDataCouldNotBeObtained). We will use
        parameterized.expand to perform this test in order to cater for every
        possible incompatibility error
        """
        mock_get_cosmos_rest_v0_39_2.return_value = retrieval_ret
        mock_get_cosmos_rest_v0_42_6.return_value = retrieval_ret
        actual_ret = self.test_monitor._get_cosmos_rest_data()
        expected_ret = ({}, True, CosmosRestServerDataCouldNotBeObtained(
            self.data_sources[2].node_name))
        self.assertEqual(expected_ret, actual_ret)

    @mock.patch.object(TendermintRpcApiWrapper, 'get_status')
    def test_get_tendermint_rpc_direct_data_return(
            self, mock_get_status) -> None:
        """
        We will check that the return is as expected for all cases
        """
        mock_get_status.return_value = {
            'result': {
                'validator_info': {
                    'address': self.test_consensus_address
                },
                'sync_info': {
                    'catching_up': self.test_is_syncing
                },
                'mev_info' : {
                    'is_peered_with_sentinel' : self.test_is_peered_with_sentinel,
                },
            }
        }

        actual_return_mev = self.test_monitor_mev._get_tendermint_rpc_direct_data()
        self.assertEqual(self.retrieved_tendermint_direct_data_mev, actual_return_mev)

    @parameterized.expand([
        (None, 1000, True, 999,),
        (None, 1000, False, 999,),
        (988, 1000, True, 988,),
        (988, 1000, False, 988,),
        (910, 1000, False, 911,),
        (909, 1000, True, 909,),
        (699, 1000, True, 700,),
        (699, 1000, False, 911,),
    ])
    def test_determine_last_height_monitored_tendermint(
            self, current_last_height, current_height, is_source_archive,
            expected_return) -> None:
        """
        In this test we will check that
        _determine_last_height_monitored_tendermint is determined correctly for
        different input types.
        """
        actual_return = \
            self.test_monitor._determine_last_height_monitored_tendermint(
                current_last_height, current_height, is_source_archive)
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ([{
            "jsonrpc": "2.0",
            "id": -1,
            "result": {
                "block_height": "3664035",
                "validators": [
                    {
                        "address": "addr_1",
                        "voting_power": "43",
                    },
                    {
                        "address": "addr_2",
                        "voting_power": "44",
                    }
                ]
            }
        }, {
            "jsonrpc": "2.0",
            "id": -1,
            "result": {
                "block_height": "3664035",
                "validators": [
                    {
                        "address": "addr_3",
                        "voting_power": "45",
                    },
                    {
                        "address": "addr_4",
                        "voting_power": "46",
                    }
                ]
            }
        }], [
             {
                 "address": "addr_1",
                 "voting_power": "43",
             },
             {
                 "address": "addr_2",
                 "voting_power": "44",
             },
             {
                 "address": "addr_3",
                 "voting_power": "45",
             },
             {
                 "address": "addr_4",
                 "voting_power": "46",
             }
         ],),
        ([{
            "jsonrpc": "2.0",
            "id": -1,
            "result": {
                "block_height": "3664035",
                "validators": []
            }
        }, {
            "jsonrpc": "2.0",
            "id": -1,
            "result": {
                "block_height": "3664035",
                "validators": []
            }
        }], [],),
        ([], [],)
    ])
    def test_parse_validators_list_parses_correctly(
            self, paginated_validators, expected_return) -> None:
        """
        In this test we will check that given a list of validators info, the
        _parse_validators_list function combines the validators list into one
        list
        """
        actual_return = self.test_monitor._parse_validators_list(
            paginated_validators)
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ([
             {
                 "address": "addr_1",
                 "voting_power": "43",
             },
             {
                 "address": "addr_2",
                 "voting_power": "44",
             },
             {
                 "address": "addr_3",
                 "voting_power": "45",
             },
             {
                 "address": "addr_4",
                 "voting_power": "46",
             }
         ], 'addr_4', True,),
        ([
             {
                 "address": "addr_1",
                 "voting_power": "43",
             },
             {
                 "address": "addr_2",
                 "voting_power": "44",
             },
             {
                 "address": "addr_3",
                 "voting_power": "45",
             },
             {
                 "address": "addr_4",
                 "voting_power": "46",
             }
         ], 'addr_5', False,),
        ([
             {
                 "address": "addr_1",
                 "voting_power": "43",
             },
             {
                 "address": "addr_2",
                 "voting_power": "44",
             },
             {
                 "address": "addr_3",
                 "voting_power": "45",
             },
             {
                 "address": "addr_4",
                 "voting_power": "46",
             }
         ], None, False,),
        ([
             {
                 "address": "addr_1",
                 "voting_power": "43",
             },
             {
                 "address": "addr_2",
                 "voting_power": "44",
             },
             {
                 "address": "addr_3",
                 "voting_power": "45",
             },
             {
                 "address": "addr_4",
                 "voting_power": "46",
             }
         ], "", False,),
        ([], "addr_1", False,),
    ])
    def test_is_validator_active_returns_correctly(
            self, validators, consensus_address, expected_return) -> None:
        """
        Given a number of scenarios we will check that the is_validator_active
        function will correctly determine if a validator is active or not
        """
        self.test_monitor._validator_consensus_address = consensus_address
        actual_return = self.test_monitor._is_validator_active(validators)
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ([
             {"type": "transfer"},
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "YWRkcmVzcw==",
                         "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sdXl3bmtzdWR2'
                                  'Z3p0NzV4bHNmOHp3dXpzcThyMw==',
                         "index": True
                     },
                     {
                         "key": "cG93ZXI=",
                         "value": "MTM2NTk2NTY2NDg=",
                         "index": True
                     },
                     {
                         "key": "cmVhc29u",
                         "value": "ZG91YmxlX3NpZ24=",
                         "index": True
                     }
                 ]
             },
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "amFpbGVk",
                         "value": "MTM2NTk2NTY2NDg=",
                         "index": True
                     }
                 ]
             }
         ], '7B3D01F754DFF8474ED0E358812FD437E09389DC', (True, None),),
        ([
             {"type": "transfer"},
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "YWRkcmVzcw==",
                         "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sdXl3b'
                                  'mtzdWR2Z3p0NzV4bHNmOHp3dXpzcThyMw==',
                         "index": True
                     },
                     {
                         "key": "cG93ZXI=",
                         "value": "MTM2NTk2NTY2NDg=",
                         "index": True
                     },
                     {
                         "key": "cmVhc29u",
                         "value": "ZG91YmxlX3NpZ24=",
                         "index": True
                     },
                     {
                         "key": "YnVybmVkX2NvaW5z",
                         "value": "MTAwMA==",
                         "index": True
                     }
                 ]
             },
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "YWRkcmVzcw==",
                         "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sdXl3bmt'
                                  'zdWR2Z3p0NzV4bHNmOHp3dXpzcThyMw==',
                         "index": True
                     },
                     {
                         "key": "cG93ZXI=",
                         "value": "MTM2NTk2NTY2NDg=",
                         "index": True
                     },
                     {
                         "key": "cmVhc29u",
                         "value": "ZG91YmxlX3NpZ24=",
                         "index": True
                     },
                     {
                         "key": "YnVybmVkX2NvaW5z",
                         "value": "MTAwMA==",
                         "index": True
                     }
                 ]
             },
         ], '7B3D01F754DFF8474ED0E358812FD437E09389DC', (True, 2000),),
        ([
             {"type": "transfer"},
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "YWRkcmVzcw==",
                         "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sdXl3bmtzdWR2'
                                  'Z3p0NzV4bHNmOHp3dXpzcThyMw==',
                         "index": True
                     },
                     {
                         "key": "cG93ZXI=",
                         "value": "MTM2NTk2NTY2NDg=",
                         "index": True
                     },
                     {
                         "key": "cmVhc29u",
                         "value": "ZG91YmxlX3NpZ24=",
                         "index": True
                     },
                     {
                         "key": "YnVybmVkX2NvaW5z",
                         "value": "MTAwMA==",
                         "index": True
                     }
                 ]
             },
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "amFpbGVk",
                         "value": "MTM2NTk2NTY2NDg=",
                         "index": True
                     }
                 ]
             },
         ], 'addr_1', (False, None),),
        ([
             {"type": "transfer"},
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "YWRkcmVzcw==",
                         "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sdXl3bmtzdWR'
                                  '2Z3p0NzV4bHNmOHp3dXpzcThyMw==',
                         "index": True
                     },
                 ]
             },
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "amFpbGVk",
                         "value": "cmVnZW52YWxjb25HF1bm5ldnN6M3R3dW1o",
                         "index": True
                     }
                 ]
             },
         ], None, (False, None),),
        ([
             {"type": "transfer"},
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "YWRkcmVzcw==",
                         "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sdXl3bmtzdWR2'
                                  'Z3p0NzV4bHNmOHp3dXpzcThyMw==',
                         "index": True
                     },
                 ]
             },
             {
                 "type": "slash",
                 "attributes": [
                     {
                         "key": "amFpbGVk",
                         "value": "cmVnZW52YWxjb25HF1bm5ldnN6M3R3dW1o",
                         "index": True
                     }
                 ]
             },
         ], "", (False, None),),
    ])
    def test_validator_was_slashed_returns_correctly(
            self, begin_block_events, consensus_address,
            expected_return) -> None:
        """
        Given a number of scenarios we will check that the
        _validator_was_slashed function will correctly determine if a validator
        was slashed or not, and will give the amount if available.
        """
        self.test_monitor._validator_consensus_address = consensus_address
        actual_return = self.test_monitor._validator_was_slashed(
            begin_block_events)
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(TendermintRpcApiWrapper, 'get_block')
    @mock.patch.object(TendermintRpcApiWrapper, 'get_validators')
    @mock.patch.object(TendermintRpcApiWrapper, 'get_block_results')
    def test_get_tendermint_rpc_archive_data_validator_return(
            self, mock_get_block_results, mock_get_validators,
            mock_get_block) -> None:
        """
        We will check that the return is as expected for all cases
        """
        test_hex_address = "7B3D01F754DFF8474ED0E358812FD437E09389DC"
        self.test_monitor._validator_consensus_address = test_hex_address
        self.test_monitor._last_height_monitored_tendermint = 49
        mock_get_block.side_effect = [
            {
                "result": {
                    "block": {
                        "header": {
                            "height": "52"
                        }
                    },
                }
            },
            {
                "result": {
                    "block": {
                        "last_commit": {
                            "signatures": [
                                {
                                    "validator_address": "0736A27C42B775871326",
                                    "signature": "X4s29VIs3BCruDsas0Rhgkci2BQ=="
                                },
                                {
                                    "validator_address": "",
                                    "signature": None
                                },
                            ]
                        }
                    },
                },
            },
            {
                "result": {
                    "block": {
                        "last_commit": {
                            "signatures": [
                                {
                                    "validator_address": "0736A27C42B775881D26",
                                    "signature": "X4s29VIs3BCruDsas0Rhgkck2BQ=="
                                },
                                {
                                    "validator_address": "",
                                    "signature": None
                                },
                                {
                                    "validator_address": test_hex_address,
                                    "signature": None
                                },
                            ]
                        }
                    },
                },
            },
            {
                "result": {
                    "block": {
                        "last_commit": {
                            "signatures": [
                                {
                                    "validator_address": "0736A27C42B775871D26",
                                    "signature": "X4s29VIs3BCruDsas0Rhgkpk2BQ=="
                                },
                                {
                                    "validator_address": "",
                                    "signature": None
                                },
                                {
                                    "validator_address": test_hex_address,
                                    "signature": "X4s29VIs3BCruDas0RhgkciO2BQ=="
                                },
                            ]
                        }
                    },
                },
            },
        ]
        mock_get_validators.side_effect = [
            {
                "result": {
                    "validators": [{"address": "other_address"}],
                    'count': "1",
                    'total': "1",
                }
            },
            {
                "result": {
                    "validators": [{"address": test_hex_address}],
                    'count': "1",
                    'total': "1",
                }
            },
            {
                "result": {
                    "validators": [{"address": test_hex_address}],
                    'count': "1",
                    'total': "1",
                }
            },
        ]
        mock_get_block_results.side_effect = [
            {
                'result': {
                    'begin_block_events': [
                        {
                            "type": "slash",
                            "attributes": [
                                {
                                    "key": "YWRkcmVzcw==",
                                    "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sd'
                                             'Xl3bmtzdWR2Z3p0NzV4bHNmOHp3dXpzcT'
                                             'hyMw==',
                                    "index": True
                                },
                                {
                                    "key": "cG93ZXI=",
                                    "value": "MTM2NTk2NTY2NDg=",
                                    "index": True
                                },
                                {
                                    "key": "cmVhc29u",
                                    "value": "ZG91YmxlX3NpZ24=",
                                    "index": True
                                }
                            ]
                        },
                    ]
                }
            },
            {
                'result': {
                    'begin_block_events': [
                        {
                            "type": "slash",
                            "attributes": [
                                {
                                    "key": "YWRkcmVzcw==",
                                    "value": 'cmVnZW52YWxjb25zMTY2ZWV5a3ZnenVmc'
                                             'zhlOGthcnV5Z2ZzcHF1bm5ldnN6M3R3d'
                                             'W1o',
                                    "index": True
                                },
                                {
                                    "key": "cG93ZXI=",
                                    "value": "MTM2NTk2NTY2NDg=",
                                    "index": True
                                },
                                {
                                    "key": "cmVhc29u",
                                    "value": "ZG91YmxlX3NpZ24=",
                                    "index": True
                                }
                            ]
                        },
                    ]
                }
            },
            {
                'result': {
                    'begin_block_events': [
                        {
                            "type": "slash",
                            "attributes": [
                                {
                                    "key": "YWRkcmVzcw==",
                                    "value": 'Y29zbW9zdmFsY29uczEwdjdzcmE2NW1sd'
                                             'Xl3bmtzdWR2Z3p0NzV4bHNmOHp3dXpzcT'
                                             'hyMw==',
                                    "index": True
                                },
                                {
                                    "key": "cG93ZXI=",
                                    "value": "MTM2NTk2NTY2NDg=",
                                    "index": True
                                },
                                {
                                    "key": "cmVhc29u",
                                    "value": "ZG91YmxlX3NpZ24=",
                                    "index": True
                                },
                                {
                                    "key": "YnVybmVkX2NvaW5z",
                                    "value": "MTAwMA==",
                                    "index": True
                                }
                            ]
                        },
                    ]
                }
            }
        ]

        actual_return = \
            self.test_monitor._get_tendermint_rpc_archive_data_validator(
                self.data_sources[0])
        self.assertEqual(self.retrieved_tendermint_archive_data, actual_return)
        self.assertEqual(52, self.test_monitor.last_height_monitored_tendermint)

    @parameterized.expand([
        (False,),
        ('',),
        (None,)
    ])
    def test_get_tendermint_rpc_archive_data_return_if_source_url_falsy(
            self, tendermint_rpc_url) -> None:
        """
        In this test we will check that if the node passed as data source has
        a falsy tendermint_rpc_url, then the function will return default data
        """
        data_source = self.data_sources[0]
        data_source._tendermint_rpc_url = tendermint_rpc_url
        actual_ret = self.test_monitor._get_tendermint_rpc_archive_data(
            data_source)
        self.assertEqual({'historical': None}, actual_ret)

    @mock.patch.object(CosmosNodeMonitor,
                       '_get_tendermint_rpc_archive_data_validator')
    def test_get_tendermint_rpc_archive_data_return_if_validator(
            self, mock_get_archive) -> None:
        """
        In this test we will check that if the node being monitored is a
        validator, then the function will return the retrieved archive metrics
        """
        mock_get_archive.return_value = self.retrieved_tendermint_archive_data
        actual_ret = self.test_monitor._get_tendermint_rpc_archive_data(
            self.data_sources[0])
        self.assertEqual(self.retrieved_tendermint_archive_data, actual_ret)

    def test_get_tendermint_rpc_archive_data_return_if_non_validator(
            self) -> None:
        """
        In this test we will check that if the node being monitored is not a
        validator, then default data will be returned by
        _get_tendermint_rpc_archive_data
        """
        self.test_monitor._node_config._is_validator = False
        actual_ret = self.test_monitor._get_tendermint_rpc_archive_data(
            self.data_sources[0])
        self.assertEqual({'historical': []}, actual_ret)

    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_tendermint_node')
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_direct_data')
    def test_get_tendermint_rpc_data_return_if_no_archive_source_selected(
            self, mock_select_node, mock_direct_data_retrieval) -> None:
        # This test assumes that the direct data retrieval is successful
        mock_direct_data_retrieval.return_value = None
        mock_select_node.return_value = {'consensus_hex_address':
                                             self.test_consensus_address,
                                         'is_syncing':
                                             self.test_is_syncing}
        actual_ret = self.test_monitor._get_tendermint_rpc_data()
        self.assertEqual(
            ({}, True, NoSyncedDataSourceWasAccessibleException(
                self.monitor_name, 'archive/indirect Tendermint RPC node')),
            actual_ret)

    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_archive_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_direct_data')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_tendermint_node')
    def test_get_tendermint_rpc_data_sets_cons_address_if_not_None_or_empty(
            self, mock_select_node, mock_get_direct_data,
            mock_get_archive_data) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_direct_data.return_value = \
            self.retrieved_tendermint_direct_data_not_mev
        mock_get_archive_data.return_value = \
            self.retrieved_tendermint_archive_data

        self.test_monitor._get_tendermint_rpc_data()
        self.assertEqual(self.test_consensus_address,
                         self.test_monitor.validator_consensus_address)

    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_archive_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_direct_data')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_tendermint_node')
    def test_get_tendermint_rpc_data_sets_peered_with_sentinel(
            self, mock_select_node, mock_get_direct_data,
            mock_get_archive_data) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_direct_data.return_value = \
            self.retrieved_tendermint_direct_data_mev
        mock_get_archive_data.return_value = \
            self.retrieved_tendermint_archive_data

        actual_return = self.test_monitor_mev._get_tendermint_rpc_data()
        self.assertEqual(actual_return[0],
                         self.retrieved_tendermint_rpc_data_mev)

    @parameterized.expand([
        ('',),
        (None,),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_archive_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_direct_data')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_tendermint_node')
    def test_get_tendermint_rpc_data_does_not_set_cons_address_if_empty_or_None(
            self, retrieved_cons_address, mock_select_node,
            mock_get_direct_data, mock_get_archive_data) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_direct_data.return_value = {
            'consensus_hex_address': retrieved_cons_address
        }
        mock_get_archive_data.return_value = \
            self.retrieved_tendermint_archive_data

        self.test_monitor._get_tendermint_rpc_data()
        self.assertIsNone(self.test_monitor.validator_consensus_address)

    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_archive_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_direct_data')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_tendermint_node')
    def test_get_tendermint_rpc_data_ret_if_archive_data_retrieved_successfully(
            self, mock_select_node, mock_get_direct_data,
            mock_get_archive_data) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_direct_data.return_value = \
            self.retrieved_tendermint_direct_data_not_mev
        mock_get_archive_data.return_value = \
            self.retrieved_tendermint_archive_data
        actual_ret = self.test_monitor._get_tendermint_rpc_data()
        self.assertEqual((self.retrieved_tendermint_rpc_data_not_mev, False, None),
                         actual_ret)
        ## update mock direct response data
        mock_get_direct_data.return_value = \
            self.retrieved_tendermint_direct_data_mev
        actual_ret_mev = self.test_monitor_mev._get_tendermint_rpc_data()
        self.assertEqual((self.retrieved_tendermint_rpc_data_mev, False, None), actual_ret_mev)


    @parameterized.expand([
        (NodeIsDownException('node_name_1'),
         NodeIsDownException('node_name_1'),),
        (DataReadingException('test_monitor', 'tendermint_rpc_url_1'),
         DataReadingException('test_monitor', 'tendermint_rpc_url_1')),
        (InvalidUrlException('tendermint_rpc_url_1'),
         InvalidUrlException('tendermint_rpc_url_1')),
        (IncorrectJSONRetrievedException('REST', 'err'),
         TendermintRPCDataCouldNotBeObtained('node_name_1')),
        (TendermintRPCCallException('call', 'call_failed'),
         TendermintRPCCallException('call', 'call_failed')),
        (TendermintRPCIncompatibleException('node_name_1'),
         TendermintRPCDataCouldNotBeObtained('node_name_1')),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_direct_data')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_tendermint_node')
    def test_get_tendermint_rpc_data_ret_if_direct_data_retrieval_error(
            self, raised_err, returned_err, mock_select_node,
            mock_get_direct) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_direct.side_effect = raised_err
        actual_ret = self.test_monitor._get_tendermint_rpc_data()
        self.assertEqual(({}, True, returned_err), actual_ret)

    @parameterized.expand([
        (CannotConnectWithDataSourceException('test_monitor', 'node_name_1',
                                              'err'),
         CannotConnectWithDataSourceException('test_monitor', 'node_name_1',
                                              'err'),),
        (DataReadingException('test_monitor', 'tendermint_rpc_url_1'),
         DataReadingException('test_monitor', 'tendermint_rpc_url_1')),
        (InvalidUrlException('tendermint_rpc_url_1'),
         InvalidUrlException('tendermint_rpc_url_1')),
        (IncorrectJSONRetrievedException('REST', 'err'),
         TendermintRPCDataCouldNotBeObtained('node_name_1')),
        (TendermintRPCCallException('call', 'call_failed'),
         TendermintRPCCallException('call', 'call_failed')),
        (TendermintRPCIncompatibleException('node_name_1'),
         TendermintRPCDataCouldNotBeObtained('node_name_1')),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_archive_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_direct_data')
    @mock.patch.object(CosmosNodeMonitor, '_select_cosmos_tendermint_node')
    def test_get_tendermint_rpc_data_ret_if_archive_data_retrieval_error(
            self, raised_err, returned_err, mock_select_node,
            mock_get_direct, mock_get_archive) -> None:
        mock_select_node.return_value = self.data_sources[0]
        mock_get_direct.return_value = self.retrieved_tendermint_direct_data_not_mev
        mock_get_archive.side_effect = raised_err
        actual_ret = self.test_monitor._get_tendermint_rpc_data()
        self.assertEqual(({}, True, returned_err), actual_ret)

    @mock.patch("src.monitors.node.cosmos.get_prometheus_metrics_data")
    def test_get_prometheus_data_return_if_retrieval_successful(
            self, mock_get_prometheus) -> None:
        """
        If retrieval is successful `get_prometheus_data` should return
        (retrieved data, False, None)
        """
        mock_get_prometheus.return_value = \
            self.retrieved_prometheus_data_example_1
        ret = self.test_monitor._get_prometheus_data()
        self.assertEqual(self.retrieved_prometheus_data_example_1, ret[0])
        self.assertEqual(False, ret[1])
        self.assertEqual(None, ret[2])

    @mock.patch("src.monitors.node.cosmos.get_prometheus_metrics_data")
    def test_get_prometheus_data_return_if_retrieval_fails_with_expected_error(
            self, mock_get_prometheus) -> None:
        """
        If prometheus retrieval fails with an expected error, then
        `get_prometheus_data` should return ({}, True, Related Error)
        """
        node_name = self.data_sources[2].node_name
        node_url = self.data_sources[2].prometheus_url
        errors_raised_and_retrieved = {
            ReadTimeout('test'): NodeIsDownException(node_name),
            ReqConnectionError('test'): NodeIsDownException(node_name),
            IncompleteRead('test'): DataReadingException(self.monitor_name,
                                                         node_url),
            ChunkedEncodingError('test'): DataReadingException(
                self.monitor_name, node_url),
            ProtocolError('test'): DataReadingException(self.monitor_name,
                                                        node_url),
            InvalidURL('test'): InvalidUrlException(node_url),
            InvalidSchema('test'): InvalidUrlException(node_url),
            MissingSchema('test'): InvalidUrlException(node_url),
            MetricNotFoundException('test_metric', 'test_endpoint'):
                MetricNotFoundException('test_metric', 'test_endpoint'),
        }
        for error_raised, expected_error in errors_raised_and_retrieved.items():
            mock_get_prometheus.side_effect = error_raised
            ret = self.test_monitor._get_prometheus_data()
            self.assertEqual({}, ret[0])
            self.assertEqual(True, ret[1])
            self.assertEqual(expected_error, ret[2])
            mock_get_prometheus.reset_mock(side_effect=True)

    @parameterized.expand([
        ('self.received_retrieval_info_all_source_types_enabled',
         ['self.retrieved_prometheus_data_example_1', False, None], True,
         ['self.retrieved_cosmos_rest_data_1', False, None], True,
         ['self.retrieved_tendermint_rpc_data_not_mev', False, None], True, False),
        ('self.received_retrieval_info_some_sources_disabled', None, False,
         ['self.retrieved_cosmos_rest_data_1', False, None], True,
         ['self.retrieved_tendermint_rpc_data_mev', False, None], True, True),
        ('self.received_retrieval_info_all_source_types_enabled_err',
         [{}, True, PANICException('test_exception_1', 1)], True,
         [{}, True, PANICException('test_exception_2', 2)], True,
         [{}, True, PANICException('test_exception_3', 3)], True, False),
    ])
    @mock.patch.object(CosmosNodeMonitor, '_get_tendermint_rpc_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_cosmos_rest_data')
    @mock.patch.object(CosmosNodeMonitor, '_get_prometheus_data')
    def test_get_data_return(
            self, expected_ret, retrieved_prom_data, monitor_prom,
            retrieved_cosmos_rest_data, monitor_cosmos_rest,
            retrieved_tendermint_rpc_data, monitor_tendermint_rpc, is_mev,
            mock_get_prom_data, mock_get_cosmos_rest_data,
            mock_get_tendermint_rpc_data) -> None:
        """
        In this test we will check that the retrieval info is returned correctly
        for every possible test case. We will use parameterized.expand to
        explore all possible cases
        """
        monitor = self.test_monitor

        if monitor_prom:
            # If prometheus is to be monitored, then we have a list which needs
            # to be converted to a tuple
            if retrieved_prom_data[0]:
                # If the first element is a variable evaluate it
                retrieved_prom_data[0] = eval(retrieved_prom_data[0])
            mock_get_prom_data.return_value = tuple(retrieved_prom_data)
        if monitor_cosmos_rest:
            # If cosmos_rest is to be monitored, then we have a list which needs
            # to be converted to a tuple
            if retrieved_cosmos_rest_data[0]:
                # If the first element is a variable evaluate it
                retrieved_cosmos_rest_data[0] = eval(
                    retrieved_cosmos_rest_data[0])
            mock_get_cosmos_rest_data.return_value = tuple(
                retrieved_cosmos_rest_data)
        if monitor_tendermint_rpc:
            # If tendermint_rpc is to be monitored, then we have a list which
            # needs to be converted to a tuple
            if retrieved_tendermint_rpc_data[0]:
                # If the first element is a variable evaluate it
                retrieved_tendermint_rpc_data[0] = eval(
                    retrieved_tendermint_rpc_data[0])
            mock_get_tendermint_rpc_data.return_value = tuple(
                retrieved_tendermint_rpc_data)
        monitor._node_config._monitor_prometheus = monitor_prom
        monitor._node_config._monitor_cosmos_rest = \
            monitor_cosmos_rest

        monitor._node_config._monitor_tendermint_rpc = \
            monitor_tendermint_rpc
        monitor._node_config._is_mev_tendermint_node = True

        actual_ret = monitor._get_data()
        expected_ret = eval(expected_ret)
        expected_ret['cosmos_rest']['get_function'] = mock_get_cosmos_rest_data
        expected_ret['prometheus']['get_function'] = mock_get_prom_data
        expected_ret['tendermint_rpc']['get_function'] = \
            mock_get_tendermint_rpc_data

        print(expected_ret)
        print(actual_ret)

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
                    'operator_address':
                        self.test_monitor.node_config.operator_address
                },
                'message': self.test_exception_1.message,
                'code': self.test_exception_1.code,
            }
        }
        actual_output = self.test_monitor._process_error(self.test_exception_1)
        self.assertEqual(expected_output, actual_output)

    @freeze_time("2012-01-01")
    def test_process_retrieved_cosmos_rest_data_returns_expected_data(
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
                    'operator_address':
                        self.test_monitor.node_config.operator_address,
                },
                'data': copy.deepcopy(self.test_data_dict),
            }
        }
        actual_ret = self.test_monitor._process_retrieved_cosmos_rest_data(
            self.test_data_dict)
        self.assertEqual(expected_ret, actual_ret)

    @freeze_time("2012-01-01")
    def test_process_retrieved_tendermint_rpc_data_returns_expected_data(
            self) -> None:
        expected_ret = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_mev_tendermint_node': False,
                    'is_validator': self.test_monitor.node_config.is_validator,
                    'operator_address':
                        self.test_monitor.node_config.operator_address,
                },
                'data': copy.deepcopy(self.test_data_dict),
            }
        }
        actual_ret = self.test_monitor._process_retrieved_tendermint_rpc_data(
            self.test_data_dict)
        self.assertEqual(expected_ret, actual_ret)

    @parameterized.expand([
        ("self.processed_prometheus_data_example_1",
         "self.retrieved_prometheus_data_example_1"),
        ("self.processed_prometheus_data_example_2",
         "self.retrieved_prometheus_data_example_2"),
    ])
    @freeze_time("2012-01-01")
    def test_process_retrieved_prometheus_data_returns_expected_data(
            self, expected_data_output, retrieved_data) -> None:
        expected_output = {
            'result': {
                'meta_data': {
                    'monitor_name': self.test_monitor.monitor_name,
                    'node_name': self.test_monitor.node_config.node_name,
                    'node_id': self.test_monitor.node_config.node_id,
                    'node_parent_id': self.test_monitor.node_config.parent_id,
                    'time': datetime(2012, 1, 1).timestamp(),
                    'is_validator': self.test_monitor.node_config.is_validator,
                    'operator_address':
                        self.test_monitor.node_config.operator_address
                },
                'data': eval(expected_data_output),
            }
        }

        actual_output = self.test_monitor._process_retrieved_prometheus_data(
            eval(retrieved_data))
        self.assertEqual(expected_output, actual_output)

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
        # routing key as the ones sent by send_data, and checks that the
        # data is received
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
            routing_key=COSMOS_NODE_RAW_DATA_ROUTING_KEY)

        self.test_monitor._send_data(self.processed_prometheus_data_example_1)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_monitor.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the processed data
        _, _, body = self.test_monitor.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.processed_prometheus_data_example_1,
                         json.loads(body))

    @freeze_time("2012-01-01")
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
    def test_monitor_sends_data_and_hb_if_data_retrieve_and_processing_success(
            self, mock_get_data, mock_send_heartbeat, mock_send_data) -> None:
        # Here we are assuming that all sources are enabled.
        expected_output_data = {
            'prometheus': {
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
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.processed_prometheus_data_example_1,
                }
            },
            'cosmos_rest': {
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
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.retrieved_cosmos_rest_data_1,
                }
            },
            'tendermint_rpc': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp(),
                        'is_mev_tendermint_node': False,
                        'is_validator':
                            self.test_monitor.node_config.is_validator,
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.retrieved_tendermint_rpc_data_not_mev,
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
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
    def test_monitor_sends_empty_dict_for_disabled_sources(
            self, mock_get_data, mock_send_heartbeat, mock_send_data) -> None:
        expected_output_data = {
            'prometheus': {},
            'cosmos_rest': {
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
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.retrieved_cosmos_rest_data_1,
                }
            },
            'tendermint_rpc': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp(),
                        'is_mev_tendermint_node': True,
                        'is_validator':
                            self.test_monitor.node_config.is_validator,
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.retrieved_tendermint_rpc_data_mev,
                }
            },
        }
        expected_output_hb = {
            'component_name': self.test_monitor.monitor_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }
        mock_get_data.return_value = \
            self.received_retrieval_info_some_sources_disabled
        mock_send_data.return_value = None
        mock_send_heartbeat.return_value = None
        # update node_config on test_monitor temporarily
        self.test_monitor.node_config._is_mev_tendermint_node = True
        self.test_monitor._monitor()
        mock_send_data.assert_called_once_with(expected_output_data)
        mock_send_heartbeat.assert_called_once_with(expected_output_hb)

    @parameterized.expand([
        (['self.test_exception_1'],),
        (['self.processed_prometheus_data_example_1',
          'self.test_exception_1'],),
    ])
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_process_data")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
    def test_monitor_sends_no_data_and_hb_if_data_ret_success_and_proc_fails(
            self, process_data_side_effect, mock_get_data,
            mock_process_data, mock_send_hb, mock_send_data) -> None:
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

    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
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
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
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
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
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
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
    def test_monitor_logs_data_if_all_sources_enabled_and_no_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        expected_logged_data = self.test_monitor._display_data({
            'prometheus': {
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
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.processed_prometheus_data_example_1,
                }
            },
            'cosmos_rest': {
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
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.retrieved_cosmos_rest_data_1,
                }
            },
            'tendermint_rpc': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp(),
                        'is_mev_tendermint_node': False,
                        'is_validator':
                            self.test_monitor.node_config.is_validator,
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'data': self.retrieved_tendermint_rpc_data_not_mev,
                }
            },
        })
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        self.test_monitor._monitor()
        mock_log.assert_called_with(expected_logged_data)

    @mock.patch.object(logging.Logger, "debug")
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
    def test_monitor_does_not_log_if_no_retrieval_performed(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        # expected_logged_data contains the data that should be logged if all
        # sources are enabled.
        expected_logged_data = self.test_monitor._display_data({
            'prometheus': {},
            'cosmos_rest': {},
            'tendermint_rpc': {},
        })
        mock_send_data.return_value = None
        mock_send_hb.return_value = None
        mock_get_data.return_value = \
            self.received_retrieval_info_all_source_types_enabled
        self.received_retrieval_info_all_source_types_enabled['prometheus'][
            'monitoring_enabled'] = False
        self.received_retrieval_info_all_source_types_enabled['cosmos_rest'][
            'monitoring_enabled'] = False
        self.received_retrieval_info_all_source_types_enabled['tendermint_rpc'][
            'monitoring_enabled'] = False
        self.test_monitor._monitor()
        assert_not_called_with(mock_log, expected_logged_data)

    @mock.patch.object(logging.Logger, "debug")
    @mock.patch.object(CosmosNodeMonitor, "_send_heartbeat")
    @mock.patch.object(CosmosNodeMonitor, "_send_data")
    @mock.patch.object(CosmosNodeMonitor, "_get_data")
    def test_monitor_does_not_log_if_retrieval_error(
            self, mock_get_data, mock_send_data, mock_send_hb,
            mock_log) -> None:
        # expected_logged_data contains the data that should be logged if all
        # sources are enabled.
        expected_logged_data = self.test_monitor._display_data({
            'prometheus': {
                'result': {
                    'meta_data': {
                        'monitor_name': self.test_monitor.monitor_name,
                        'node_name': self.test_monitor.node_config.node_name,
                        'node_id': self.test_monitor.node_config.node_id,
                        'node_parent_id':
                            self.test_monitor.node_config.parent_id,
                        'time': datetime(2012, 1, 1).timestamp(),
                        'is_validator':
                            self.test_monitor.node_config.is_validator
                    },
                    'message': self.test_exception_1.message,
                    'code': self.test_exception_1.code,
                }
            },
            'cosmos_rest': {
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
                        'operator_address':
                            self.test_monitor.node_config.operator_address
                    },
                    'message': self.test_exception_1.message,
                    'code': self.test_exception_1.code,
                }
            },
            'tendermint_rpc': {
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
                        'operator_address':
                            self.test_monitor.node_config.operator_address
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
