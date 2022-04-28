import logging
from typing import Dict, Any, List

from requests import Response

from src.api_wrappers.api_wrapper import ApiWrapper
from src.utils.data import get_cosmos_json
from src.utils.exceptions import (
    CosmosSDKVersionIncompatibleException, CosmosRestServerApiCallException,
    TendermintRPCCallException, TendermintRPCIncompatibleException)


class CosmosRestServerApiWrapper(ApiWrapper):
    """
    This API wrapper uses Cosmos Rest Server functions from versions v0.39.2 and
    v0.42.6 of the Cosmos SDK. Apart from these two versions, this API wrapper
    is also compatible with Cosmos Rest Server versions which implement these
    functions. Please visit https://v1.cosmos.network/rpc to make sure that the
    functions which you are using are compatible with your node.

    NOTE: When developing new function parameters always put 'params' as the
        : last argument if it is needed. This is a requirement if you want to
        : use CosmosMonitor._get_rest_data_with_pagination_keys
    """

    def __init__(self, logger: logging.Logger, verify: bool = False,
                 timeout: int = 10) -> None:
        super().__init__(logger, verify, timeout)

    def get_syncing(self, cosmos_rest_url: str) -> Dict:
        """
        This function retrieves data from the cosmos_rest_url/syncing endpoint,
        and is compatible with both v0.39.2 and v0.42.6 of the Cosmos SDK
        :param cosmos_rest_url: The Cosmos REST url of the data source
        :return: Retrieves data from the cosmos_rest_url/syncing endpoint
        """
        endpoint = cosmos_rest_url + '/syncing'
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               verify=self.verify, timeout=self.timeout)

    def get_staking_validators_v0_39_2(
            self, cosmos_rest_url: str, validator_address: str = None,
            params: Dict = None) -> Dict:
        """
        This function retrieves data from the cosmos_rest_url/staking/validators
        and cosmos_rest_url/staking/validators/{validatorAddr} endpoints,
        depending on the inputted function parameters. Note that this function
        is only compatible with v0.39.2 of the Cosmos SDK, for other versions
        unexpected behaviour might occur.
        :param cosmos_rest_url: The Cosmos REST url of the data source
        :param params: Parameters that need to be added to the endpoint
        :param validator_address: The address of the validator you want to query
        :return: Retrieves data from the cosmos_rest_url/staking/validators or
                 cosmos_rest_url/staking/validators/{validatorAddr} endpoints
        """
        cosmos_fn = ('/staking/validators' if validator_address is None
                     else '/staking/validators/{}'.format(validator_address))
        endpoint = cosmos_rest_url + cosmos_fn
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               params=params, verify=self.verify,
                               timeout=self.timeout)

    def get_staking_validators_v0_42_6(
            self, cosmos_rest_url: str, validator_address: str = None,
            params: Dict = None) -> Dict:
        """
        This function retrieves data from the
        cosmos_rest_url/cosmos/staking/v1beta1/validators and
        cosmos_rest_url/cosmos/staking/v1beta1/validators/{validatorAddr}
        endpoints, depending on the inputted function parameters. Note that this
        function is only compatible with v0.42.6 of the Cosmos SDK, for other
        versions unexpected behaviour might occur.
        :param cosmos_rest_url: The Cosmos REST url of the data source
        :param params: Parameters that need to be added to the endpoint
        :param validator_address: The address of the validator you want to query
        :return: Retrieves data from the
               : cosmos_rest_url/cosmos/staking/v1beta1/validators or
               : cosmos_rest_url/cosmos/staking/v1beta1/validators/{
               : validatorAddr} endpoints
        """
        cosmos_fn = (
            '/cosmos/staking/v1beta1/validators' if validator_address is None
            else '/cosmos/staking/v1beta1/validators/{}'.format(
                validator_address)
        )
        endpoint = cosmos_rest_url + cosmos_fn
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               params=params, verify=self.verify,
                               timeout=self.timeout)

    def get_proposals_v0_39_2(
            self, cosmos_rest_url: str, proposal_id: int = None,
            params: Dict = None) -> Dict:
        """
        This function retrieves data from the cosmos_rest_url/gov/proposals
        and cosmos_rest_url/gov/proposals/{proposalId} endpoints,
        depending on the inputted function parameters. Note that this function
        is only compatible with v0.39.2 of the Cosmos SDK, for other versions
        unexpected behaviour might occur.
        :param cosmos_rest_url: The Cosmos REST url of the data source
        :param params: Parameters that need to be added to the endpoint
        :param proposal_id: The ID of the proposal you want to query
        :return: Retrieves data from the cosmos_rest_url/gov/proposals or
                 cosmos_rest_url/gov/proposals/{proposalId} endpoints
        """
        cosmos_fn = ('/gov/proposals' if proposal_id is None
                     else '/gov/proposals/{}'.format(proposal_id))
        endpoint = cosmos_rest_url + cosmos_fn
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               params=params, verify=self.verify,
                               timeout=self.timeout)

    def get_proposals_v0_42_6(
            self, cosmos_rest_url: str, proposal_id: int = None,
            params: Dict = None) -> Dict:
        """
        This function retrieves data from the
        cosmos_rest_url/cosmos/gov/v1beta1/proposals and
        cosmos_rest_url/cosmos/gov/v1beta1/proposals/{proposalId}
        endpoints, depending on the inputted function parameters. Note that this
        function is only compatible with v0.42.6 of the Cosmos SDK, for other
        versions unexpected behaviour might occur.
        :param cosmos_rest_url: The Cosmos REST url of the data source
        :param params: Parameters that need to be added to the endpoint
        :param proposal_id: The ID of the proposal you want to query
        :return: Retrieves data from the
               : cosmos_rest_url/cosmos/gov/v1beta1/proposals or
               : cosmos_rest_url/cosmos/gov/v1beta1/proposals/{
               : proposalId} endpoints
        """
        cosmos_fn = (
            '/cosmos/gov/v1beta1/proposals' if proposal_id is None
            else '/cosmos/gov/v1beta1/proposals/{}'.format(
                proposal_id)
        )
        endpoint = cosmos_rest_url + cosmos_fn
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               params=params, verify=self.verify,
                               timeout=self.timeout)

    def execute_with_checks(self, function, args: List[Any],
                            node_name: str, sdk_version: str) -> Any:
        """
        This function executes a wrapper call and returns its return if
        successful. Otherwise, it will perform incompatibility and API call
        error checks.
        If the API call returns a "not implemented error" or a 404 error, this
        function will raise a CosmosSDKVersionIncompatibleException. This is
        because for nodes with cosmos sdk version <= v0.39.2, if a page is not
        found then a 404 not found error is raised. In the case of nodes with
        cosmos sdk version >=v0.42.6, a "not implemented error" is returned if a
        page is not found.
        Apart from version compatibility we will also check if an error is
        returned by the API call. In that case a
        CosmosRestServerApiCallException will be raised.
        :param function: The wrapper call to execute
        :param args: The arguments to be passed to the API call
        :param node_name: The name of the data source
        :param sdk_version: The Cosmos SDK version being checked for
        :return: The function return if successful
               : CosmosSDKVersionIncompatibleException if the API call is not
                 supported by the node's cosmos sdk version.
               : CosmosRestServerApiCallException if any other error is returned
                 by the API Call
        """
        ret = function(*args)

        if isinstance(ret, Dict) and 'code' in ret and 'message' in ret:
            if (int(ret['code']) == 12
                    and ret['message'].lower() == 'not implemented'):
                self.logger.error('The Cosmos SDK version of node {} does not '
                                  'support function {}.'.format(node_name,
                                                                function))
                raise CosmosSDKVersionIncompatibleException(node_name,
                                                            sdk_version)
            else:
                # Some errors might be raised without being preceded with
                # `error`. Normally, the data structure would still contain
                # `code` and `message`
                self.logger.error('Function {} failed. Error: {}'.format(
                    function, ret['message']))
                raise CosmosRestServerApiCallException(function,
                                                       ret['message'])
        elif isinstance(ret, Dict) and 'error' in ret:
            self.logger.error('Function {} failed. Error: {}'.format(
                function, ret['error']))
            raise CosmosRestServerApiCallException(function, ret['error'])
        elif type(ret) == Response and ret.status_code == 404:
            self.logger.error('The Cosmos SDK version of node {} does not '
                              'support function {}.'.format(node_name,
                                                            function))
            raise CosmosSDKVersionIncompatibleException(node_name, sdk_version)

        return ret


class TendermintRpcApiWrapper(ApiWrapper):
    """
    This API acts as a wrapper around the Tendermint RPC interface. The
    functions implemented in this API wrapper are currently implemented for all
    Tendermint versions which were considered during development, however, for
    different versions, different data structures may be obtained. Therefore,
    the client must make sure to cater for all possible differences in the data
    received.
    Docs: https://docs.tendermint.com/master/spec/rpc/
    Considered Tendermint Versions: v0.33.7, v0.33.8, v0.33.9, v0.34.11,
                                    v0.34.12, v0.34.14

    NOTE: When developing new function parameters always put 'params' as the
        : last argument if it is needed. This is a requirement if you want to
        : use CosmosMonitor._get_tendermint_data_with_count
    """

    def __init__(self, logger: logging.Logger, verify: bool = False,
                 timeout: int = 10) -> None:
        super().__init__(logger, verify, timeout)

    def get_block(self, tendermint_rpc_url: str, params: Dict = None) -> Dict:
        """
        This function retrieves data from the
        tendermint_rpc_url/block?height=<height> endpoint if height is included
        in the params Dict. Otherwise, it retrieves data from the
        tendermint_rpc_url/block endpoint
        :param tendermint_rpc_url: The tendermint RPC url of the data source
        :param params: Parameters that need to be added to the endpoint
        :return: Data from tendermint_rpc_url/block?height=<height> if height is
                 included in the params Dict. Otherwise it retrieves data from
                 the tendermint_rpc_url/block endpoint
        """
        endpoint = tendermint_rpc_url + '/block'
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               verify=self.verify, timeout=self.timeout,
                               params=params)

    def get_block_results(self, tendermint_rpc_url: str,
                          params: Dict = None) -> Dict:
        """
        This function retrieves data from the
        tendermint_rpc_url/block_results?height=<height> endpoint if height is
        included in the params Dict. Otherwise, it retrieves data from the
        tendermint_rpc_url/block_results endpoint
        :param tendermint_rpc_url: The tendermint RPC url of the data source
        :param params: Parameters that need to be added to the endpoint
        :return: Data from tendermint_rpc_url/block_results?height=<height> if
                 height is included in the params Dict. Otherwise it retrieves
                 data from the tendermint_rpc_url/block_results endpoint
        """
        endpoint = tendermint_rpc_url + '/block_results'
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               verify=self.verify, timeout=self.timeout,
                               params=params)

    def get_status(self, tendermint_rpc_url: str) -> Dict:
        """
        This function retrieves data from the tendermint_rpc_url/status endpoint
        :param tendermint_rpc_url: The tendermint RPC url of the data source
        :return: Data from tendermint_rpc_url/status
        """
        endpoint = tendermint_rpc_url + '/status'
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               verify=self.verify, timeout=self.timeout)

    def get_validators(self, tendermint_rpc_url: str,
                       params: Dict = None) -> Dict:
        """
        This function retrieves data from the tendermint_rpc_url/validators?
        height=<height>&page=<page>&per_page=<per_page> endpoint if a
        combination of height, per_page and page is included in the params Dict.
        Otherwise, it retrieves data from the tendermint_rpc_url/validators
        endpoint
        :param tendermint_rpc_url: The tendermint RPC url of the data source
        :param params: Parameters that need to be added to the endpoint
        :return: Data from tendermint_rpc_url/validators?
                 height=<height>&page=<page>&per_page=<per_page> if a
                 combination of height, per_page and page is included in the
                 params Dict. Otherwise, it retrieves data from the
                 tendermint_rpc_url/validators endpoint
        """
        endpoint = tendermint_rpc_url + '/validators'
        return get_cosmos_json(endpoint=endpoint, logger=self.logger,
                               verify=self.verify, timeout=self.timeout,
                               params=params)

    def execute_with_checks(self, function, args: List[Any],
                            node_name: str) -> Any:
        """
        This function executes a wrapper call and returns its return if
        successful. Otherwise, it will perform incompatibility and API call
        error checks.
        If the API call returns a 404 error, this function will raise a
        TendermintRPCIncompatibleException as this means that the endpoint
        cannot be found at the node's Tendermint RPC interface.
        Apart from version compatibility we will also check if an error is
        returned by the API call. In that case a TendermintRPCCallException will
        be raised.
        :param function: The wrapper call to execute
        :param args: The arguments to be passed to the API call
        :param node_name: The name of the data source.
        :return: The function return if successful
               : TendermintRPCIncompatibleException if the API call is not
                 supported by the node's Tendermint RPC version.
               : TendermintRPCCallException if an error is returned by the API
                 Call
        """
        ret = function(*args)

        if (isinstance(ret, Dict)
                and 'error' in ret
                and 'message' in ret['error']
                and 'data' in ret['error']):
            error_msg = "{}, {}".format(ret['error']['message'],
                                        ret['error']['data'])
            self.logger.error('Function {} failed. Error: {}'.format(
                function, error_msg))
            raise TendermintRPCCallException(function, error_msg)
        elif type(ret) == Response and ret.status_code == 404:
            self.logger.error('The Tendermint RPC version of node {} does not '
                              'support function {}.'.format(node_name,
                                                            function))
            raise TendermintRPCIncompatibleException(node_name)

        return ret
