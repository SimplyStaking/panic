import logging
import unittest
from unittest import mock

from requests import Response

from src.api_wrappers.cosmos import (CosmosRestServerApiWrapper,
                                     TendermintRpcApiWrapper)
from src.utils.exceptions import (
    CosmosSDKVersionIncompatibleException, CosmosRestServerApiCallException,
    TendermintRPCIncompatibleException, TendermintRPCCallException)


class TestCosmosRestServerApiWrapper(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.verify = True
        self.timeout = 20
        self.cosmos_rest_url = 'test_cosmos_rest_url'
        self.validator_address = 'test_validator_address'
        self.proposal_id = 1
        self.test_params = {'param_key': 'val'}
        self.test_dict = {'test_key': 567}
        self.supported_version = 'v0.39.2'
        self.node_name = 'test_node_name'

        # Test instance
        self.test_wrapper = CosmosRestServerApiWrapper(self.dummy_logger,
                                                       self.verify,
                                                       self.timeout)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_wrapper = None

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_syncing_calls_api_correctly(
            self, mock_get_cosmos_json) -> None:
        self.test_wrapper.get_syncing(self.cosmos_rest_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/syncing".format(self.cosmos_rest_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout)

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_staking_validators_v0_39_2_calls_api_correctly(
            self, mock_get_cosmos_json) -> None:
        # Test when validator_address and params are None
        self.test_wrapper.get_staking_validators_v0_39_2(self.cosmos_rest_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/staking/validators".format(self.cosmos_rest_url),
            logger=self.dummy_logger, params=None, verify=self.verify,
            timeout=self.timeout)
        mock_get_cosmos_json.reset_mock()

        # Test when validator_address and params are not None
        self.test_wrapper.get_staking_validators_v0_39_2(self.cosmos_rest_url,
                                                         self.validator_address,
                                                         self.test_params)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/staking/validators/{}".format(self.cosmos_rest_url,
                                                       self.validator_address),
            logger=self.dummy_logger, params=self.test_params,
            verify=self.verify, timeout=self.timeout)

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_staking_validators_v0_42_6_calls_api_correctly(
            self, mock_get_cosmos_json) -> None:
        # Test when validator_address and params are None
        self.test_wrapper.get_staking_validators_v0_42_6(self.cosmos_rest_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/cosmos/staking/v1beta1/validators".format(
                self.cosmos_rest_url), logger=self.dummy_logger, params=None,
            verify=self.verify, timeout=self.timeout)
        mock_get_cosmos_json.reset_mock()

        # Test when validator_address and params are not None
        self.test_wrapper.get_staking_validators_v0_42_6(self.cosmos_rest_url,
                                                         self.validator_address,
                                                         self.test_params)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/cosmos/staking/v1beta1/validators/{}".format(
                self.cosmos_rest_url, self.validator_address),
            logger=self.dummy_logger, params=self.test_params,
            verify=self.verify, timeout=self.timeout)

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_proposals_v0_39_2_calls_api_correctly(
            self, mock_get_cosmos_json) -> None:
        # Test when proposal_id and params are None
        self.test_wrapper.get_proposals_v0_39_2(self.cosmos_rest_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/gov/proposals".format(self.cosmos_rest_url),
            logger=self.dummy_logger, params=None, verify=self.verify,
            timeout=self.timeout)
        mock_get_cosmos_json.reset_mock()

        # Test when proposal_id and params are not None
        self.test_wrapper.get_proposals_v0_39_2(self.cosmos_rest_url,
                                                self.proposal_id,
                                                self.test_params)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/gov/proposals/{}".format(self.cosmos_rest_url,
                                                  self.proposal_id),
            logger=self.dummy_logger, params=self.test_params,
            verify=self.verify, timeout=self.timeout)

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_proposals_v0_42_6_calls_api_correctly(
            self, mock_get_cosmos_json) -> None:
        # Test when proposal_id and params are None
        self.test_wrapper.get_proposals_v0_42_6(self.cosmos_rest_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/cosmos/gov/v1beta1/proposals".format(
                self.cosmos_rest_url), logger=self.dummy_logger, params=None,
            verify=self.verify, timeout=self.timeout)
        mock_get_cosmos_json.reset_mock()

        # Test when proposal_id and params are not None
        self.test_wrapper.get_proposals_v0_42_6(self.cosmos_rest_url,
                                                self.proposal_id,
                                                self.test_params)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/cosmos/gov/v1beta1/proposals/{}".format(
                self.cosmos_rest_url, self.proposal_id),
            logger=self.dummy_logger, params=self.test_params,
            verify=self.verify, timeout=self.timeout)

    """
    To test CosmosRestServerApiWrapper.execute_with_checks we will be using the
    CosmosRestServerApiWrapper.get_syncing function. This will not effect the
    generality of the tests.
    """

    @mock.patch.object(CosmosRestServerApiWrapper, "get_syncing")
    def test_execute_with_checks_returns_function_return_if_no_errors_detected(
            self, mock_get_syncing) -> None:
        mock_get_syncing.return_value = self.test_dict
        actual_ret = self.test_wrapper.execute_with_checks(
            self.test_wrapper.get_syncing, [], self.node_name,
            self.supported_version)
        self.assertEqual(self.test_dict, actual_ret)

    @mock.patch.object(CosmosRestServerApiWrapper, "get_syncing")
    def test_execute_with_checks_raises_incompatibility_exception(
            self, mock_get_syncing) -> None:
        """
        In this test we will check that a CosmosSDKVersionIncompatibleException
        is raised by the function if either a 404 page not found error is
        returned or a {code: 12, message: "Not Implemented", details: []} is
        returned
        """
        return_1 = {'code': 12, 'message': "Not Implemented", 'details': []}
        return_2 = Response()
        return_2.__setstate__({"status_code": 404})
        mock_get_syncing.side_effect = [return_1, return_2]

        # First check for return_1
        self.assertRaises(CosmosSDKVersionIncompatibleException,
                          self.test_wrapper.execute_with_checks,
                          self.test_wrapper.get_syncing, [], self.node_name,
                          self.supported_version)

        # Now check for return_2
        self.assertRaises(CosmosSDKVersionIncompatibleException,
                          self.test_wrapper.execute_with_checks,
                          self.test_wrapper.get_syncing, [], self.node_name,
                          self.supported_version)

    @mock.patch.object(CosmosRestServerApiWrapper, "get_syncing")
    def test_execute_with_checks_raises_rest_server_api_call_err_if_check_true(
            self, mock_get_syncing) -> None:
        """
        In this test we will check that a CosmosRestServerApiCallException
        is raised by the function if either {'error': msg} is returned or
        {code: 12, message: msg, details: []} is returned
        """
        return_1 = {'code': 11, 'message': "Bad Error", 'details': []}
        return_2 = {'error': 'error message'}
        mock_get_syncing.side_effect = [return_1, return_2]

        # First check for return_1
        self.assertRaises(CosmosRestServerApiCallException,
                          self.test_wrapper.execute_with_checks,
                          self.test_wrapper.get_syncing, [], self.node_name,
                          self.supported_version)

        # Now check for return_2
        self.assertRaises(CosmosRestServerApiCallException,
                          self.test_wrapper.execute_with_checks,
                          self.test_wrapper.get_syncing, [], self.node_name,
                          self.supported_version)


class TestTendermintRpcApiWrapper(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.verify = True
        self.timeout = 20
        self.tendermint_rpc_url = 'test_tendermint_rpc_url'
        self.test_params = {'param_key': 'val'}
        self.test_dict = {'test_key': 567}
        self.node_name = 'test_node_name'

        # Test instance
        self.test_wrapper = TendermintRpcApiWrapper(self.dummy_logger,
                                                    self.verify,
                                                    self.timeout)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_wrapper = None

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_block_calls_api_correctly(self, mock_get_cosmos_json) -> None:
        # First test with parameters not None
        self.test_wrapper.get_block(self.tendermint_rpc_url, self.test_params)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/block".format(self.tendermint_rpc_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout,
            params=self.test_params
        )
        mock_get_cosmos_json.reset_mock()

        # Test with parameters None
        self.test_wrapper.get_block(self.tendermint_rpc_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/block".format(self.tendermint_rpc_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout,
            params=None
        )

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_block_results_calls_api_correctly(
            self, mock_get_cosmos_json) -> None:
        # First test with parameters not None
        self.test_wrapper.get_block_results(self.tendermint_rpc_url,
                                            self.test_params)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/block_results".format(self.tendermint_rpc_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout,
            params=self.test_params
        )
        mock_get_cosmos_json.reset_mock()

        # Test with parameters None
        self.test_wrapper.get_block_results(self.tendermint_rpc_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/block_results".format(self.tendermint_rpc_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout,
            params=None
        )

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_status_calls_api_correctly(self, mock_get_cosmos_json) -> None:
        self.test_wrapper.get_status(self.tendermint_rpc_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/status".format(self.tendermint_rpc_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout,
        )

    @mock.patch("src.api_wrappers.cosmos.get_cosmos_json")
    def test_get_validators_calls_api_correctly(
            self, mock_get_cosmos_json) -> None:
        # First test with parameters not None
        self.test_wrapper.get_validators(self.tendermint_rpc_url,
                                         self.test_params)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/validators".format(self.tendermint_rpc_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout,
            params=self.test_params
        )
        mock_get_cosmos_json.reset_mock()

        # Test with parameters None
        self.test_wrapper.get_validators(self.tendermint_rpc_url)
        mock_get_cosmos_json.assert_called_once_with(
            endpoint="{}/validators".format(self.tendermint_rpc_url),
            logger=self.dummy_logger, verify=self.verify, timeout=self.timeout,
            params=None
        )

    """
    To test TendermintRpcApiWrapper.execute_with_checks we will be using the
    TendermintRpcApiWrapper.get_status function. This will not effect the
    generality of the tests.
    """

    @mock.patch.object(TendermintRpcApiWrapper, "get_status")
    def test_execute_with_checks_returns_function_return_if_no_errors_detected(
            self, mock_get_status) -> None:
        mock_get_status.return_value = self.test_dict
        actual_ret = self.test_wrapper.execute_with_checks(
            self.test_wrapper.get_status, [self.tendermint_rpc_url],
            self.node_name)
        self.assertEqual(self.test_dict, actual_ret)

    @mock.patch.object(TendermintRpcApiWrapper, "get_status")
    def test_execute_with_checks_raises_incompatibility_exception(
            self, mock_get_status) -> None:
        """
        In this test we will check that a TendermintRPCIncompatibleException is
        raised by the function if a 404 page not found error is returned
        """
        fn_return = Response()
        fn_return.__setstate__({"status_code": 404})
        mock_get_status.return_value = fn_return
        self.assertRaises(
            TendermintRPCIncompatibleException,
            self.test_wrapper.execute_with_checks, self.test_wrapper.get_status,
            [self.tendermint_rpc_url], self.node_name)

    @mock.patch.object(TendermintRpcApiWrapper, "get_status")
    def test_execute_with_checks_raises_tendermint_rpc_call_error_if_check_true(
            self, mock_get_status) -> None:
        """
        In this test we will check that a TendermintRPCCallException is raised
        by the function if {error: {message: msg, data: data, code: code}}
        """
        fn_return = {
            "error": {
                "code": -32602,
                "message": "Invalid params",
                "data": "error converting http params to arguments:"
            }}
        mock_get_status.return_value = fn_return
        self.assertRaises(
            TendermintRPCCallException, self.test_wrapper.execute_with_checks,
            self.test_wrapper.get_status, [self.tendermint_rpc_url],
            self.node_name)
