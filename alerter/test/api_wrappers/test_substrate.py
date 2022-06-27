import logging
import unittest
from unittest import mock

from parameterized import parameterized

from src.api_wrappers.substrate import (
    SubstrateApiWrapper, _SUBSTRATE_API_LOST_NODE_CONNECTION_ERROR_CODE,
    _SUBSTRATE_API_NODE_CONNECTION_INITIALISATION_ERROR_CODE)
from src.utils.exceptions import NodeIsDownException, SubstrateApiCallException


class TestSubstrateApiWrapper(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.api_ip = 'test_api_ip'
        self.api_port = 59
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.verify = True
        self.timeout = 20
        self.api_url = 'https://{}:{}'.format(self.api_ip, self.api_port)
        self.test_node_ws_url = 'test_node_ws_url'
        self.test_node_name = 'test_node_name'
        self.test_block_hash = 'test_block_hash'
        self.test_validator_stash = 'test_validator_stash'
        self.test_block_number = 45346
        self.test_referendum_index = 58
        self.test_session_index = 559
        self.test_auth_index = 10
        self.test_era_index = 60
        self.test_dict = {'test_key': 567}

        # Test instance
        self.test_wrapper = SubstrateApiWrapper(
            self.api_ip, self.api_port, self.dummy_logger, self.verify,
            self.timeout)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_wrapper = None

    def test_api_url_constructed_correctly_on_initialisation(self) -> None:
        self.assertEqual(self.api_url, self.test_wrapper.api_url)

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_slashed_amount_calls_api_correctly(self,
                                                    mock_get_json) -> None:
        self.test_wrapper.get_slashed_amount(
            self.test_node_ws_url, self.test_block_hash,
            self.test_validator_stash)
        api_call = '/api/custom/slash/getSlashedAmount'
        params = {
            'websocket': self.test_node_ws_url,
            'blockHash': self.test_block_hash,
            'accountId': self.test_validator_stash
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_is_offline_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_is_offline(
            self.test_node_ws_url, self.test_block_hash,
            self.test_validator_stash)
        api_call = '/api/custom/offline/isOffline'
        params = {
            'websocket': self.test_node_ws_url,
            'blockHash': self.test_block_hash,
            'accountId': self.test_validator_stash
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_system_health_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_system_health(self.test_node_ws_url)
        api_call = '/api/rpc/system/health'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_system_properties_calls_api_correctly(
            self, mock_get_json) -> None:
        self.test_wrapper.get_system_properties(self.test_node_ws_url)
        api_call = '/api/rpc/system/properties'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_sync_state_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_sync_state(self.test_node_ws_url)
        api_call = '/api/rpc/system/syncState'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_finalized_head_calls_api_correctly(self,
                                                    mock_get_json) -> None:
        self.test_wrapper.get_finalized_head(self.test_node_ws_url)
        api_call = '/api/rpc/chain/getFinalizedHead'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_header_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_header(self.test_node_ws_url,
                                     self.test_block_hash)
        api_call = '/api/rpc/chain/getHeader'
        params = {
            'websocket': self.test_node_ws_url,
            'blockHash': self.test_block_hash
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_block_hash_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_block_hash(self.test_node_ws_url,
                                         self.test_block_number)
        api_call = '/api/rpc/chain/getBlockHash'
        params = {
            'websocket': self.test_node_ws_url,
            'blockNumber': self.test_block_number
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_grandpa_stalled_calls_api_correctly(self,
                                                     mock_get_json) -> None:
        self.test_wrapper.get_grandpa_stalled(self.test_node_ws_url)
        api_call = '/api/query/grandpa/stalled'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_public_prop_count_calls_api_correctly(self,
                                                       mock_get_json) -> None:
        self.test_wrapper.get_public_prop_count(self.test_node_ws_url)
        api_call = '/api/query/democracy/publicPropCount'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_referendum_count_calls_api_correctly(self,
                                                      mock_get_json) -> None:
        self.test_wrapper.get_referendum_count(self.test_node_ws_url)
        api_call = '/api/query/democracy/referendumCount'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_referendum_info_of_calls_api_correctly(self,
                                                        mock_get_json) -> None:
        self.test_wrapper.get_referendum_info_of(self.test_node_ws_url,
                                                 self.test_referendum_index)
        api_call = '/api/query/democracy/referendumInfoOf'
        params = {
            'websocket': self.test_node_ws_url,
            'referendumIndex': self.test_referendum_index
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_current_index_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_current_index(self.test_node_ws_url)
        api_call = '/api/query/session/currentIndex'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_validators_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_validators(self.test_node_ws_url)
        api_call = '/api/query/session/validators'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_disabled_validators_calls_api_correctly(self,
                                                         mock_get_json) -> None:
        self.test_wrapper.get_disabled_validators(self.test_node_ws_url)
        api_call = '/api/query/session/disabledValidators'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_authored_blocks_calls_api_correctly(self,
                                                     mock_get_json) -> None:
        self.test_wrapper.get_authored_blocks(self.test_node_ws_url,
                                              self.test_session_index,
                                              self.test_validator_stash)
        api_call = '/api/query/imOnline/authoredBlocks'
        params = {
            'websocket': self.test_node_ws_url,
            'sessionIndex': self.test_session_index,
            'accountId': self.test_validator_stash
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_received_heartbeats_calls_api_correctly(self,
                                                         mock_get_json) -> None:
        self.test_wrapper.get_received_heartbeats(self.test_node_ws_url,
                                                  self.test_session_index,
                                                  self.test_auth_index)
        api_call = '/api/query/imOnline/receivedHeartbeats'
        params = {
            'websocket': self.test_node_ws_url,
            'sessionIndex': self.test_session_index,
            'authIndex': self.test_auth_index
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_active_era_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_active_era(self.test_node_ws_url)
        api_call = '/api/query/staking/activeEra'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_eras_stakers_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_eras_stakers(self.test_node_ws_url,
                                           self.test_era_index,
                                           self.test_validator_stash)
        api_call = '/api/query/staking/erasStakers'
        params = {
            'websocket': self.test_node_ws_url,
            'eraIndex': self.test_era_index,
            'accountId': self.test_validator_stash
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_eras_reward_points_calls_api_correctly(self,
                                                        mock_get_json) -> None:
        self.test_wrapper.get_eras_reward_points(self.test_node_ws_url,
                                                 self.test_era_index)
        api_call = '/api/query/staking/erasRewardPoints'
        params = {
            'websocket': self.test_node_ws_url,
            'eraIndex': self.test_era_index,
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_staking_ledger_calls_api_correctly(self,
                                                    mock_get_json) -> None:
        self.test_wrapper.get_staking_ledger(self.test_node_ws_url,
                                             self.test_validator_stash)
        api_call = '/api/query/staking/ledger'
        params = {
            'websocket': self.test_node_ws_url,
            'accountId': self.test_validator_stash,
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_history_depth_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_history_depth(self.test_node_ws_url)
        api_call = '/api/query/staking/historyDepth'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_staking_bonded_calls_api_correctly(self,
                                                    mock_get_json) -> None:
        self.test_wrapper.get_staking_bonded(self.test_node_ws_url,
                                             self.test_validator_stash)
        api_call = '/api/query/staking/bonded'
        params = {
            'websocket': self.test_node_ws_url,
            'accountId': self.test_validator_stash
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_system_events_calls_api_correctly(self, mock_get_json) -> None:
        self.test_wrapper.get_system_events(self.test_node_ws_url,
                                            self.test_block_hash)
        api_call = '/api/query/system/events'
        params = {
            'websocket': self.test_node_ws_url,
            'blockHash': self.test_block_hash
        }
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_democracy_referendums_calls_api_correctly(
            self, mock_get_json) -> None:
        self.test_wrapper.get_democracy_referendums(self.test_node_ws_url)
        api_call = '/api/derive/democracy/referendums'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_democracy_proposals_calls_api_correctly(
            self, mock_get_json) -> None:
        self.test_wrapper.get_democracy_proposals(self.test_node_ws_url)
        api_call = '/api/derive/democracy/proposals'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.substrate.get_json")
    def test_get_staking_validators_calls_api_correctly(
            self, mock_get_json) -> None:
        self.test_wrapper.get_staking_validators(self.test_node_ws_url)
        api_call = '/api/derive/staking/validators'
        params = {'websocket': self.test_node_ws_url}
        mock_get_json.assert_called_once_with(
            endpoint="{}{}".format(self.api_url, api_call),
            logger=self.dummy_logger, params=params, verify=self.verify,
            timeout=self.timeout,
        )

    """
    To test SubstrateApiWrapper.execute_with_checks we will be using the
    SubstrateApiWrapper.get_staking_validators function. This will not effect
    the generality of the tests.
    """

    @mock.patch.object(SubstrateApiWrapper, "get_staking_validators")
    def test_execute_with_checks_returns_function_return_if_no_errors_detected(
            self, mock_get_staking_validators) -> None:
        check_for_node_downtime = True
        mock_get_staking_validators.return_value = self.test_dict
        actual_ret = self.test_wrapper.execute_with_checks(
            self.test_wrapper.get_staking_validators, [], self.test_node_name,
            check_for_node_downtime)
        self.assertEqual(self.test_dict, actual_ret)

    @mock.patch.object(SubstrateApiWrapper, "get_staking_validators")
    def test_execute_with_checks_raises_node_down_if_down_return_and_check_true(
            self, mock_get_staking_validators) -> None:
        check_for_node_downtime = True
        mock_get_staking_validators.return_value = {
            'error': {
                'message': 'Node is down',
                'code': _SUBSTRATE_API_LOST_NODE_CONNECTION_ERROR_CODE
            }
        }
        self.assertRaises(
            NodeIsDownException, self.test_wrapper.execute_with_checks,
            self.test_wrapper.get_staking_validators, [], self.test_node_name,
            check_for_node_downtime)

    @parameterized.expand([
        ({'error': {
            'message': 'Could not initialise connection with node',
            'code': _SUBSTRATE_API_NODE_CONNECTION_INITIALISATION_ERROR_CODE
        }},),
        ({'error': {
            'message': 'Lost connection with node',
            'code': _SUBSTRATE_API_LOST_NODE_CONNECTION_ERROR_CODE
        }},),
        ({'error': {'message': 'another err', 'code': 543}},),
    ])
    @mock.patch.object(SubstrateApiWrapper, "get_staking_validators")
    def test_execute_with_checks_raises_substrate_api_call_error_if_no_check(
            self, function_return, mock_get_staking_validators) -> None:
        """
        This test will be performed twice, once for when a node downtime error
        is received, and when a non node downtime error is received
        """
        check_for_node_downtime = False
        mock_get_staking_validators.return_value = function_return
        self.assertRaises(
            SubstrateApiCallException, self.test_wrapper.execute_with_checks,
            self.test_wrapper.get_staking_validators, [], self.test_node_name,
            check_for_node_downtime)

    @parameterized.expand([(True,), (False,)])
    @mock.patch.object(SubstrateApiWrapper, "get_staking_validators")
    def test_execute_with_checks_raises_substrate_api_call_err_if_not_down_err(
            self, check_for_node_downtime, mock_get_staking_validators) -> None:
        """
        This test will be performed twice, once for when
        check_for_node_downtime = True and once for when
        check_for_node_downtime = False
        """
        mock_get_staking_validators.return_value = {
            'error': {
                'message': 'another err',
                'code': 543
            }
        }
        self.assertRaises(
            SubstrateApiCallException, self.test_wrapper.execute_with_checks,
            self.test_wrapper.get_staking_validators, [], self.test_node_name,
            check_for_node_downtime)
