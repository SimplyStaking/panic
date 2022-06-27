import logging
from typing import Dict, Any, List

from src.api_wrappers.api_wrapper import ApiWrapper
from src.utils.data import get_json
from src.utils.exceptions import NodeIsDownException, SubstrateApiCallException

_SUBSTRATE_API_NODE_CONNECTION_INITIALISATION_ERROR_CODE = 532
_SUBSTRATE_API_LOST_NODE_CONNECTION_ERROR_CODE = 533
_SUBSTRATE_API_NODE_CONNECTION_ERROR_CODES = [
    _SUBSTRATE_API_NODE_CONNECTION_INITIALISATION_ERROR_CODE,
    _SUBSTRATE_API_LOST_NODE_CONNECTION_ERROR_CODE
]


class SubstrateApiWrapper(ApiWrapper):
    """
    This API wrapper uses functions from the latest Substrate-API docker
    service.
    """

    def __init__(self, api_ip: str, api_port: int, logger: logging.Logger,
                 verify: bool = False, timeout: int = 35) -> None:
        self._api_url = 'https://{}:{}'.format(api_ip, api_port)
        super().__init__(logger, verify, timeout)

    @property
    def api_url(self) -> str:
        return self._api_url

    def get_slashed_amount(self, node_ws_url: str, block_hash: str,
                           account_id: str) -> Dict:
        """
        This function uses the '/api/custom/slash/getSlashedAmount' endpoint of
        the Substrate-API to check if a validator was slashed at a specific
        block height
        :param node_ws_url: The websocket url of the data source
        :param block_hash: The hash of the block to query
        :param account_id: The stash of the validator
        :return: Retrieves data from the '/api/custom/slash/getSlashedAmount'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/custom/slash/getSlashedAmount'
        params = {'websocket': node_ws_url,
                  'blockHash': block_hash,
                  'accountId': account_id}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_is_offline(self, node_ws_url: str, block_hash: str,
                       account_id: str) -> Dict:
        """
        This function uses the '/api/custom/offline/isOffline' endpoint of the
        Substrate-API to check if a validator was deemed offline at a specific
        block height
        :param node_ws_url: The websocket url of the data source
        :param block_hash: The hash of the block to query
        :param account_id: The stash of the validator
        :return: Retrieves data from the '/api/custom/offline/isOffline'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/custom/offline/isOffline'
        params = {'websocket': node_ws_url,
                  'blockHash': block_hash,
                  'accountId': account_id}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_system_health(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/rpc/system/health' endpoint of the
        Substrate-API to get the health status of a node.
        Note: The health status retrieved belongs to the node with websocket url
              `node_ws_url`
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/rpc/system/health' endpoint of
                 the Substrate API.
        """
        endpoint = self.api_url + '/api/rpc/system/health'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_system_properties(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/rpc/system/properties' endpoint of the
        Substrate-API to get the system/chain properties of a node.
        Note: The system properties retrieved belongs to the node with
              websocket url `node_ws_url`
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/rpc/system/properties' endpoint
                 of the Substrate API.
        """
        endpoint = self.api_url + '/api/rpc/system/properties'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_sync_state(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/rpc/system/syncState' endpoint of the
        Substrate-API to get the sync status of a node.
        Note: The sync status retrieved belongs to the node with websocket url
              `node_ws_url`
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/rpc/system/syncState' endpoint of
                 the Substrate API.
        """
        endpoint = self.api_url + '/api/rpc/system/syncState'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_finalized_head(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/rpc/chain/getFinalizedHead' endpoint of the
        Substrate-API to get the hash of the last finalized block
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/rpc/chain/getFinalizedHead'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/rpc/chain/getFinalizedHead'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_header(self, node_ws_url: str, block_hash: str) -> Dict:
        """
        Given a block hash, this function uses the '/api/rpc/chain/getHeader'
        endpoint of the Substrate-API to get the header of the block
        :param node_ws_url: The websocket url of the data source
        :param block_hash: The hash of the block whose header is to be retrieved
        :return: Retrieves data from the /api/rpc/chain/getHeader' endpoint of
                 the Substrate API.
        """
        endpoint = self.api_url + '/api/rpc/chain/getHeader'
        params = {'websocket': node_ws_url, 'blockHash': block_hash}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_block_hash(self, node_ws_url: str, block_number: int) -> Dict:
        """
        Given a block number, this function uses the
        '/api/rpc/chain/getBlockHash' endpoint of the Substrate-API to get the
        hash of a block
        :param node_ws_url: The websocket url of the data source
        :param block_number: The height of the block whose hash is to be
                             retrieved
        :return: Retrieves data from the '/api/rpc/system/syncState' endpoint of
                 the Substrate API.
        """
        endpoint = self.api_url + '/api/rpc/chain/getBlockHash'
        params = {'websocket': node_ws_url, 'blockNumber': block_number}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_grandpa_stalled(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/grandpa/stalled' endpoint of the
        Substrate-API to get the stalled status of the GRANDPA algorithm
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/grandpa/stalled' endpoint
                 of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/grandpa/stalled'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_public_prop_count(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/democracy/publicPropCount' endpoint
        of the Substrate-API to get the number of public proposals so far
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/democracy/publicPropCount'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/democracy/publicPropCount'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_referendum_count(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/democracy/referendumCount' endpoint
        of the Substrate-API to get the number of referendums so far
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/democracy/referendumCount'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/democracy/referendumCount'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_referendum_info_of(self, node_ws_url: str,
                               referendum_index: int) -> Dict:
        """
        Given a referendum index, this function uses the
        '/api/query/democracy/referendumInfoOf' endpoint of the Substrate-API to
        get information about the referendum
        :param node_ws_url: The websocket url of the data source
        :param referendum_index: The index of the referendum whose information
                                 is to be obtained
        :return: Retrieves data from the '/api/query/democracy/referendumInfoOf'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/democracy/referendumInfoOf'
        params = {'websocket': node_ws_url, 'referendumIndex': referendum_index}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_current_index(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/session/currentIndex' endpoint of the
        Substrate-API to get the index of the current session
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/session/currentIndex'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/session/currentIndex'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_validators(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/session/validators' endpoint of the
        Substrate-API to get the list of active validators
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/session/validators'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/session/validators'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_disabled_validators(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/session/disabledValidators' endpoint
        of the Substrate-API to get the list of disabled validators
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/session/disabledValidators'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/session/disabledValidators'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_authored_blocks(self, node_ws_url: str, session_index: int,
                            account_id: str) -> Dict:
        """
        Given the session index and the stash of the validator, this function
        uses the '/api/query/imOnline/authoredBlocks' endpoint of the
        Substrate-API to get the number of blocks authored by the validator in
        the specified session
        :param node_ws_url: The websocket url of the data source
        :param session_index: The index of the session to query
        :param account_id: The stash of the validator to query
        :return: Retrieves data from the '/api/query/imOnline/authoredBlocks'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/imOnline/authoredBlocks'
        params = {'websocket': node_ws_url,
                  'sessionIndex': session_index,
                  'accountId': account_id}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_received_heartbeats(self, node_ws_url: str, session_index: int,
                                auth_index: int) -> Dict:
        """
        Given the session index and the authority index of the validator, this
        function uses the '/api/query/imOnline/receivedHeartbeats' endpoint of
        the Substrate-API to get the heartbeat status of the validator in the
        specified session
        :param node_ws_url: The websocket url of the data source
        :param session_index: The index of the session to query
        :param auth_index: The authority index of the validator to query
        :return: Retrieves data from the
                 '/api/query/imOnline/receivedHeartbeats' endpoint of the
                 Substrate API.
        """
        endpoint = self.api_url + '/api/query/imOnline/receivedHeartbeats'
        params = {'websocket': node_ws_url,
                  'sessionIndex': session_index,
                  'authIndex': auth_index}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_active_era(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/staking/activeEra' endpoint of the
        Substrate-API to retrieve information about the active era
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/staking/activeEra' endpoint
                 of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/staking/activeEra'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_eras_stakers(self, node_ws_url: str, era_index: int,
                         account_id: str) -> Dict:
        """
        Given the era index and the stash of the validator, this function uses
        the '/api/query/staking/erasStakers' endpoint of the Substrate-API to
        retrieve staking information about the validator for the specified era
        :param node_ws_url: The websocket url of the data source
        :param era_index: The index of the era to be queried
        :param account_id: The stash of the validator
        :return: Retrieves data from the '/api/query/staking/erasStakers'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/staking/erasStakers'
        params = {'websocket': node_ws_url,
                  'eraIndex': era_index,
                  'accountId': account_id}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_eras_reward_points(self, node_ws_url: str, era_index: int) -> Dict:
        """
        Given the era index, this function uses the
        '/api/query/staking/erasRewardPoints' endpoint of the Substrate-API to
        retrieve the points awarded to each validator in the specified era
        :param node_ws_url: The websocket url of the data source
        :param era_index: The index of the era to be queried
        :return: Retrieves data from the '/api/query/staking/erasRewardPoints'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/staking/erasRewardPoints'
        params = {'websocket': node_ws_url, 'eraIndex': era_index}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_staking_ledger(self, node_ws_url: str, account_id: str) -> Dict:
        """
        Given the stash of the validator, this function uses the
        '/api/query/staking/ledger' endpoint of the Substrate-API to retrieve
        staking information
        :param node_ws_url: The websocket url of the data source
        :param account_id: The controller of the validator to be queried
        :return: Retrieves data from the '/api/query/staking/ledger' endpoint of
                 the Substrate API.
        """
        endpoint = self.api_url + '/api/query/staking/ledger'
        params = {'websocket': node_ws_url, 'accountId': account_id}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_history_depth(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/query/staking/historyDepth' endpoint of the
        Substrate-API to get the number of historic eras kept in a Substrate
        chain
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/query/staking/historyDepth'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/query/staking/historyDepth'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_staking_bonded(self, node_ws_url: str, account_id: str) -> Dict:
        """
        Given the stash of the validator, this function uses the
        '/api/query/staking/bonded' endpoint of the Substrate-API to get the
        controller address of the specified validator
        :param node_ws_url: The websocket url of the data source
        :param account_id: The stash of the validator to be queried
        :return: Retrieves data from the '/api/query/staking/bonded' endpoint of
                 the Substrate API.
        """
        endpoint = self.api_url + '/api/query/staking/bonded'
        params = {'websocket': node_ws_url, 'accountId': account_id}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_system_events(self, node_ws_url: str, block_hash: str) -> Dict:
        """
        Given a block hash, this function uses the '/api/query/system/events'
        endpoint of the Substrate-API to get all the events attached to the
        specified block
        :param node_ws_url: The websocket url of the data source
        :param block_hash: The hash of the block to be queried
        :return: Retrieves data from the '/api/query/system/events' endpoint of
                 the Substrate API.
        """
        endpoint = self.api_url + '/api/query/system/events'
        params = {'websocket': node_ws_url, 'blockHash': block_hash}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_democracy_referendums(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/derive/democracy/referendums' endpoint of
        the Substrate-API to get further information about active referendums
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/derive/democracy/referendums'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/derive/democracy/referendums'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_democracy_proposals(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/derive/democracy/proposals' endpoint of
        the Substrate-API to get further information about active proposals
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/derive/democracy/proposals'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/derive/democracy/proposals'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def get_staking_validators(self, node_ws_url: str) -> Dict:
        """
        This function uses the '/api/derive/staking/validators' endpoint of
        the Substrate-API to get further information about staking
        :param node_ws_url: The websocket url of the data source
        :return: Retrieves data from the '/api/derive/staking/validators'
                 endpoint of the Substrate API.
        """
        endpoint = self.api_url + '/api/derive/staking/validators'
        params = {'websocket': node_ws_url}
        return get_json(endpoint=endpoint, logger=self.logger, params=params,
                        verify=self.verify, timeout=self.timeout)

    def execute_with_checks(self, function, args: List[Any], node_name: str,
                            check_for_node_downtime: bool) -> Any:
        """
        This function executes an API call and returns its return if successful.
        If the API call returns an error, it will raise a corresponding
        exception
        :param function: The Substrate Api call to execute
        :param args: The arguments to be passed to the API call
        :param node_name: The name of the node to check downtime for
        :param check_for_node_downtime: Whether to check for downtime or not (
                                      : Some components may use data sources
                                      : indirectly).
        :return: The function return if successful
               : NodeIsDownException if node downtime check is enabled and a
                 node connection related error is returned
               : SubstrateApiCallException otherwise.
        """
        ret = function(*args)
        if 'error' in ret:
            if (check_for_node_downtime and ret['error']['code'] in
                    _SUBSTRATE_API_NODE_CONNECTION_ERROR_CODES):
                raise NodeIsDownException(node_name)
            else:
                self.logger.error(
                    'Error while performing an API call. Error: %s',
                    ret['error']['message'])
                raise SubstrateApiCallException(function,
                                                ret['error']['message'])

        return ret
