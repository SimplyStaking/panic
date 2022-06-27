import copy
import logging
from ast import literal_eval
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Callable

import pika

from src.configs.nodes.substrate import SubstrateNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.substrate import (
    SubstrateMonitor, _VERSION_INCOMPATIBILITY_EXCEPTIONS)
from src.utils.constants.rabbitmq import (
    RAW_DATA_EXCHANGE, SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY)
from src.utils.exceptions import (
    SubstrateApiIsNotReachableException, IncorrectJSONRetrievedException,
    NodeIsDownException, DataReadingException, SubstrateApiCallException,
    NoSyncedDataSourceWasAccessibleException,
    SubstrateWebSocketDataCouldNotBeObtained, PANICException)
from src.utils.timing import TimedTaskLimiter


class SubstrateNodeMonitor(SubstrateMonitor):
    """
    The SubstrateNodeMonitor is able to monitor node related substrate metrics
    by obtaining data from the Substrate-API docker service.
    """

    def __init__(self, monitor_name: str, node_config: SubstrateNodeConfig,
                 logger: logging.Logger, monitor_period: int,
                 rabbitmq: RabbitMQApi,
                 data_sources: List[SubstrateNodeConfig]) -> None:
        super().__init__(monitor_name, data_sources, logger, monitor_period,
                         rabbitmq)
        self._node_config = node_config

        # If for archive data retrieval the selected data source is not an
        # archive node (could be that no archive node satisfied the selection
        # criteria or none were given by the user), the monitor won't go back
        # more than self._pruning_catchup_blocks due to a pruned state. In
        # substrate this value is normally set to 256, however we will use 246
        # to cater for some possible delays in the data retrieval process.
        self._pruning_catchup_blocks = 246

        # If the node is down for a long time, there might be a big discrepancy
        # between the last_height_monitored_<interface> and the current
        # finalized height and thus there might be a lot of data to retrieve +
        # blocks to traverse, possibly retrieving data which is no longer
        # relevant. Therefore, this variable will store the max number of blocks
        # the monitor goes back to (only if the node is archive as this is a
        # large number)
        self._max_catchup_blocks = 300

        # Construct list of archive nodes from data sources
        self._archive_nodes = [
            node for node in self.data_sources if node.is_archive_node
        ]

        # This will store the last height that the monitor queried when
        # retrieving historical data from the websocket
        self._last_height_monitored_websocket = None

        # System properties data retrieval limiter
        self._system_properties_limiter = TimedTaskLimiter(timedelta(hours=24))

        # This will store the system properties that the monitor queried when
        # retrieving system properties data from the websocket
        self._system_properties = None

    @property
    def node_config(self) -> SubstrateNodeConfig:
        return self._node_config

    @property
    def pruning_catchup_blocks(self) -> int:
        return self._pruning_catchup_blocks

    @property
    def max_catchup_blocks(self) -> int:
        return self._max_catchup_blocks

    @property
    def archive_nodes(self) -> List[SubstrateNodeConfig]:
        return self._archive_nodes

    @property
    def last_height_monitored_websocket(self) -> Optional[int]:
        return self._last_height_monitored_websocket

    @property
    def system_properties_limiter(self) -> TimedTaskLimiter:
        return self._system_properties_limiter

    @property
    def system_properties(self) -> Dict:
        return self._system_properties

    def _get_websocket_direct_data(self) -> Dict:
        """
        This function retrieves node specific metrics directly from the node
        being monitored. This data is obtained directly from the node as it
        cannot be obtained otherwise.
        :return: A dict containing all direct metrics
        """
        node_ws_url = self.node_config.node_ws_url
        node_name = self.node_config.node_name

        def retrieval_process() -> Dict:
            finalized_head = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_finalized_head, [node_ws_url],
                node_name, True)
            sync_state = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_sync_state, [node_ws_url],
                node_name, True)
            finalized_header = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_header,
                [node_ws_url, finalized_head['result']], node_name, True)

            return {
                'best_height': sync_state['result']['currentBlock'],
                'target_height': sync_state['result']['highestBlock'],
                'finalized_height': finalized_header['result']['number']
            }

        return self._execute_websocket_retrieval_with_exceptions(
            retrieval_process, self.node_config)

    def _get_websocket_indirect_data_validator(
            self, source: SubstrateNodeConfig) -> Dict:
        """
        This function retrieves validator node specific metrics using a
        different node as data source. We do not use the node directly since the
        node may be offline or syncing, thus the data may be corrupt. Note that
        as a last resource the manager may supply the node itself as data source
        :param source: The chosen data source
        :return: A dict containing all indirect metrics
        """
        source_ws_url = source.node_ws_url
        source_name = source.node_name
        stash_address = self.node_config.stash_address

        def retrieval_process() -> Dict:

            # Get some data
            session_index = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_current_index, [source_ws_url],
                source_name, False)
            active_era = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_active_era, [source_ws_url],
                source_name, False)
            history_depth = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_history_depth, [source_ws_url],
                source_name, False)
            staking_validators = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_staking_validators,
                [source_ws_url], source_name, False)
            disabled_validators = \
                self.substrate_api_wrapper.execute_with_checks(
                    self.substrate_api_wrapper.get_disabled_validators,
                    [source_ws_url], source_name, False)
            staking_bonded = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_staking_bonded,
                [source_ws_url, stash_address], source_name, False)
            if self.system_properties_limiter.can_do_task():
                system_properties = (
                    self.substrate_api_wrapper.execute_with_checks(
                        self.substrate_api_wrapper.get_system_properties,
                        [source_ws_url], source_name, False))
                self._system_properties = system_properties['result']
                if self.system_properties:
                    self.system_properties_limiter.did_task()

            # Parse these values because they might be hex, and they are to be
            # used in other API calls
            session_index = literal_eval(str(session_index['result']))
            active_era = literal_eval(str(active_era['result']['index']))
            history_depth = literal_eval(str(history_depth['result']))

            # Infer some data for more readable queries
            controller_address = staking_bonded['result']

            # Get more data based on the previously fetched data
            authored_blocks = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_authored_blocks,
                [source_ws_url, session_index, stash_address], source_name,
                False)
            eras_stakers = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_eras_stakers,
                [source_ws_url, active_era, stash_address], source_name, False)
            staking_ledger = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_staking_ledger,
                [source_ws_url, controller_address], source_name, False)
            eras_reward_points = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_eras_reward_points,
                [source_ws_url, active_era - 1], source_name, False)

            # Construct and infer new data from the retrieved data
            validators = staking_validators['result']['validators']
            next_elected = staking_validators['result']['nextElected']
            active = stash_address in validators
            elected = stash_address in next_elected
            authored_blocks = authored_blocks['result']
            stake_info = eras_stakers['result']

            # Construct data based on whether the validator is active or not
            disabled = False
            sent_heartbeat = False
            if active:
                # If the validator is in the active set, check if its index is
                # in the list of disabled validators
                auth_index = validators.index(stash_address)
                disabled = auth_index in disabled_validators['result']

                # Get current heartbeat status and set sent_heartbeat to True if
                # the node sent a heartbeat, otherwise set to false.
                received_heartbeats = \
                    self.substrate_api_wrapper.execute_with_checks(
                        self.substrate_api_wrapper.get_received_heartbeats,
                        [source_ws_url, session_index, auth_index], source_name,
                        False)
                sent_heartbeat = (
                    True if received_heartbeats['result'] else False
                )

            # Construct the unclaimed rewards. Since history_depth stores the
            # maximum number of eras stored on chain, start from 83 eras ago and
            # finish at current_era - 1
            unclaimed_rewards = []
            finishing_era = active_era
            starting_era = (
                active_era - history_depth + 1
                if active_era - history_depth >= 0
                else 0
            )
            claimed_rewards = staking_ledger['result']['claimedRewards']
            for eraIndex in range(starting_era, finishing_era):
                if eraIndex not in claimed_rewards:
                    # If the reward for the specified era was not claimed, check
                    # if the validator was active (total stake for that era
                    # non 0 if active). If the validator was active at that era
                    # then that must indicate a pending payout.
                    eras_stakers_for_era = \
                        self.substrate_api_wrapper.execute_with_checks(
                            self.substrate_api_wrapper.get_eras_stakers,
                            [source_ws_url, eraIndex, stash_address],
                            source_name, False)
                    total_stake_in_era = literal_eval(str(
                        eras_stakers_for_era['result']['total']))

                    if total_stake_in_era != 0:
                        unclaimed_rewards.append(eraIndex)

            # Construct rewards of the previous era
            previous_era_rewards = 0
            individual_awards = eras_reward_points['result']['individual']
            if stash_address in individual_awards:
                previous_era_rewards = literal_eval(str(
                    individual_awards[stash_address]))

            return {
                'current_session': session_index,
                'current_era': active_era,
                'authored_blocks': authored_blocks,
                'active': active,
                'elected': elected,
                'disabled': disabled,
                'eras_stakers': stake_info,
                'sent_heartbeat': sent_heartbeat,
                'controller_address': controller_address,
                'history_depth_eras': history_depth,
                'unclaimed_rewards': unclaimed_rewards,
                'claimed_rewards': claimed_rewards,
                'previous_era_rewards': previous_era_rewards,
                'system_properties': self.system_properties
            }

        return self._execute_websocket_retrieval_with_exceptions(
            retrieval_process, source)

    def _get_websocket_indirect_data_non_validator(
            self, source: SubstrateNodeConfig) -> Dict:
        """
        This function retrieves non-validator node specific metrics using a
        different node as data source. We do not use the node directly since the
        node may be offline or syncing, thus the data may be corrupt. Note that
        as a last resource the manager may supply the node itself as data
        source
        :param source: The chosen data source
        :return: A dict containing all indirect metrics
        """
        source_ws_url = source.node_ws_url
        source_name = source.node_name

        def retrieval_process() -> Dict:
            # Get some data
            session_index = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_current_index, [source_ws_url],
                source_name, False)
            active_era = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_active_era, [source_ws_url],
                source_name, False)
            history_depth = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_history_depth, [source_ws_url],
                source_name, False)
            if self.system_properties_limiter.can_do_task():
                system_properties = (
                    self.substrate_api_wrapper.execute_with_checks(
                        self.substrate_api_wrapper.get_system_properties,
                        [source_ws_url], source_name, False))
                self._system_properties = system_properties['result']
                self.system_properties_limiter.did_task()

            # Parse these values because they might be hex, and they are to be
            # used later
            session_index = literal_eval(str(session_index['result']))
            active_era = literal_eval(str(active_era['result']['index']))
            history_depth = literal_eval(str(history_depth['result']))

            return {
                'current_session': session_index,
                'current_era': active_era,
                'authored_blocks': 0,
                'active': False,
                'elected': False,
                'disabled': False,
                'eras_stakers': {"total": None, "own": None, "others": []},
                'sent_heartbeat': False,
                'controller_address': None,
                'history_depth_eras': history_depth,
                'unclaimed_rewards': [],
                'claimed_rewards': [],
                'previous_era_rewards': 0,
                'system_properties': self.system_properties
            }

        return self._execute_websocket_retrieval_with_exceptions(
            retrieval_process, source)

    def _get_websocket_indirect_data(self, source: SubstrateNodeConfig) -> Dict:
        """
        This function returns the indirect metrics of the substrate node from
        the websocket interface depending on whether the node is a validator or
        a non-validator
        :param source: The data source
        :return: The websocket indirect metrics of the Substrate node
        """
        source_url = source.node_ws_url
        is_validator = self.node_config.is_validator
        if not source_url:
            return {
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

        if is_validator:
            return self._get_websocket_indirect_data_validator(source)
        else:
            return self._get_websocket_indirect_data_non_validator(source)

    def _determine_last_height_monitored_websocket(
            self, current_last_height: int, current_height: int,
            is_source_archive: bool) -> int:
        """
        This function checks whether last_height_monitored_archive satisfies
        some conditions in order to determine its correct value for the upcoming
        monitoring round. These conditions are based on the current finalized
        height of the chain and whether the source node is archive or not.
        Note, this check must be done before retrieving any archive websocket
        data
        :param current_last_height:
        The value of self._last_height_monitored_websocket
        :param current_height:
        The current finalized height of the chain
        :param is_source_archive:
        If the source being used is an archive node or not
        :return:
        The value of last_height_monitored_websocket to be used in the upcoming
        monitoring round
        """
        if current_last_height is None:
            # On start-up we need to start retrieving data from the current
            # block. Therefore, the last height monitored is current - 1
            return current_height - 1
        elif (current_height - current_last_height > self.max_catchup_blocks
              and is_source_archive):
            # If the monitor is not keeping up with the chain and the data
            # source is archive, skip some blocks.
            return current_height - self.max_catchup_blocks
        elif (current_height - current_last_height
              > self.pruning_catchup_blocks and not is_source_archive):
            # If the monitor is not keeping up with the chain and the data
            # source is not archive, skip some blocks keeping in mind the
            # pruning state of the node.
            return current_height - self.pruning_catchup_blocks

        return current_last_height

    def _get_websocket_archive_data_validator(
            self, source: SubstrateNodeConfig) -> Dict:
        """
        This function retrieves validator node specific metrics using a
        different node as data source. We do not use the node directly since the
        node may be offline or syncing, thus the data may be corrupt. Note that
        as a last resource the manager may supply the node itself as data
        source
        :param source: The chosen data source
        :return: A dict containing all archive metrics
        """
        source_ws_url = source.node_ws_url
        source_name = source.node_name
        is_source_archive = source.is_archive_node
        stash_address = self.node_config.stash_address

        def retrieval_process() -> Dict:
            # Get the height of the last finalized block of the archive source.
            finalized_head = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_finalized_head, [source_ws_url],
                source_name, False)
            finalized_header = self.substrate_api_wrapper.execute_with_checks(
                self.substrate_api_wrapper.get_header,
                [source_ws_url, finalized_head['result']], source_name, False)
            current_finalized_height = literal_eval(str(
                finalized_header['result']['number']))
            self._last_height_monitored_websocket = \
                self._determine_last_height_monitored_websocket(
                    self.last_height_monitored_websocket,
                    current_finalized_height, is_source_archive)
            starting_height = self.last_height_monitored_websocket + 1
            stopping_height = current_finalized_height + 1
            historical_data = []

            for height_to_monitor in range(starting_height, stopping_height):
                block_hash = self.substrate_api_wrapper.execute_with_checks(
                    self.substrate_api_wrapper.get_block_hash,
                    [source_ws_url, height_to_monitor], source_name, False)
                slashed_amount = self.substrate_api_wrapper.execute_with_checks(
                    self.substrate_api_wrapper.get_slashed_amount,
                    [source_ws_url, block_hash['result'], stash_address],
                    source_name, False)
                is_offline = self.substrate_api_wrapper.execute_with_checks(
                    self.substrate_api_wrapper.get_is_offline,
                    [source_ws_url, block_hash['result'], stash_address],
                    source_name, False)

                historical_data.append({
                    'height': height_to_monitor,
                    'slashed': slashed_amount['result'] > 0,
                    'slashed_amount': slashed_amount['result'],
                    'is_offline': is_offline['result']
                })

            self._last_height_monitored_websocket = current_finalized_height

            # We need to reverse the historical data to show info about the
            # latest block first
            historical_data.reverse()
            return {'historical': historical_data}

        return self._execute_websocket_retrieval_with_exceptions(
            retrieval_process, source)

    @staticmethod
    def _get_websocket_archive_data_non_validator() -> Dict:
        """
        This function retrieves non-validator node specific metrics. Note that
        since non-validators cannot be slashed nor be deemed as offline, we
        return an empty list for the historical_data metric.
        :return: A dict containing all archive metrics
        """

        return {
            'historical': []
        }

    def _get_websocket_archive_data(self, source: SubstrateNodeConfig) -> Dict:
        """
        This function returns the archive metrics of the substrate node from
        the websocket interface depending on whether the node is a validator or
        a non-validator
        :param source: The data source
        :return: The websocket archive metrics of the Substrate node
        """
        source_url = source.node_ws_url
        is_validator = self.node_config.is_validator
        if not source_url:
            return {
                'historical': None,
            }

        if is_validator:
            return self._get_websocket_archive_data_validator(source)
        else:
            return self._get_websocket_archive_data_non_validator()

    def _get_websocket_data(self) -> (Dict, bool, Optional[Exception]):
        """
        This function attempts to retrieve the Websocket metrics.
        :return: If data retrieval successful :
                 ({direct_data, indirect_data, archive_data}, False, None)
               : If expected error raised while retrieving data:
                ({}, True, Raised_Error)
        """
        try:
            # First get the data directly
            direct_data = self._get_websocket_direct_data()

            # Select an indirect node for indirect data retrieval and perform
            # the retrieval
            selected_indirect_node = self._select_websocket_node(
                self.data_sources)
            if selected_indirect_node is None:
                self.logger.error(
                    'No synced indirect Substrate websocket data source was '
                    'accessible.')
                return {}, True, NoSyncedDataSourceWasAccessibleException(
                    self.monitor_name, 'indirect Substrate websocket node')
            indirect_data = self._get_websocket_indirect_data(
                selected_indirect_node)

            # Select an archive node for archive data retrieval and perform the
            # retrieval. If no archive node is accessible, or given by the user,
            # try getting data with the previously selected indirect node.
            selected_archive_node = self._select_websocket_node(
                self.archive_nodes)
            if selected_archive_node is None:
                selected_archive_node = selected_indirect_node
            archive_data = self._get_websocket_archive_data(
                selected_archive_node)

            retrieved_data = {**direct_data, **indirect_data, **archive_data}
            self.logger.debug((retrieved_data, False, None))
            return retrieved_data, False, None
        except (SubstrateApiIsNotReachableException, DataReadingException,
                IncorrectJSONRetrievedException, NodeIsDownException,
                SubstrateApiCallException) as e:
            if type(e) in _VERSION_INCOMPATIBILITY_EXCEPTIONS:
                # If we have an incompatibility issue raise a more meaningful
                # error
                self.logger.error(
                    'Substrate websocket data could not be obtained for '
                    '{}'.format(self.node_config.node_name))
                return {}, True, SubstrateWebSocketDataCouldNotBeObtained(
                    self.node_config.node_name)

            self.logger.debug(({}, True, e))
            return {}, True, e

    def _get_data(self) -> Dict:
        """
        This function retrieves the data from various data sources. Due to
        multiple data sources being processed, this function also returns some
        data retrieval information for further processing.
        :return: A dict containing all node metrics.
        """
        # TODO: If we add more interface data sources in the future we need to
        #     : change the `monitoring_enabled` field to the individual
        #     : monitor_<interface> switch
        retrieval_info = {
            'websocket': {
                'data': {},
                'data_retrieval_failed': True,
                'data_retrieval_exception': None,
                'get_function': self._get_websocket_data,
                'processing_function': self._process_retrieved_websocket_data,
                'monitoring_enabled': self.node_config.monitor_node
            }
        }

        for source, info in retrieval_info.items():
            if info['monitoring_enabled']:
                ret = info['get_function']()
                info['data'] = ret[0]
                info['data_retrieval_failed'] = ret[1]
                info['data_retrieval_exception'] = ret[2]

        return retrieval_info

    def _process_error(self, error: PANICException) -> Dict:
        """
        This function attempts to process the error which occurred when
        retrieving data
        :param error: The detected error
        :return: A dict with the error data together with some meta data
        """
        processed_data = {
            'error': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_validator': self.node_config.is_validator,
                    'stash_address': self.node_config.stash_address,
                },
                'message': error.message,
                'code': error.code,
            }
        }

        return processed_data

    def _process_retrieved_websocket_data(self, data: Dict) -> Dict:
        """
        This function attempts to process the retrieved Substrate websocket data
        :param data: The retrieved Substrate websocket data
        :return: A dict with the retrieved data together with some meta-data
        """
        # Add some meta-data to the processed data
        processed_data = {
            'result': {
                'meta_data': {
                    'monitor_name': self.monitor_name,
                    'node_name': self.node_config.node_name,
                    'node_id': self.node_config.node_id,
                    'node_parent_id': self.node_config.parent_id,
                    'time': datetime.now().timestamp(),
                    'is_validator': self.node_config.is_validator,
                    'stash_address': self.node_config.stash_address,
                },
                'data': copy.deepcopy(data),
            }
        }

        return processed_data

    @staticmethod
    def _process_retrieved_data(processing_fn: Callable, data: Dict) -> Dict:
        return processing_fn(data)

    def _send_data(self, data: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=RAW_DATA_EXCHANGE,
            routing_key=SUBSTRATE_NODE_RAW_DATA_ROUTING_KEY, body=data,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent data to '%s' exchange", RAW_DATA_EXCHANGE)

    def _monitor(self) -> None:
        retrieval_info = self._get_data()
        processed_data = {}
        for source, info in retrieval_info.items():
            if info['monitoring_enabled']:
                try:
                    processed_data[source] = self._process_data(
                        info['data_retrieval_failed'],
                        [info['data_retrieval_exception']],
                        [info['processing_function'], info['data']],
                    )
                except Exception as error:
                    self.logger.error("Error when processing data: %s", error)
                    self.logger.exception(error)
                    # Do not send data if we experienced processing errors
                    return
            else:
                processed_data[source] = {}

        self._send_data(processed_data)

        data_retrieval_failed_list = [
            info['data_retrieval_failed']
            for _, info in retrieval_info.items() if info['monitoring_enabled']
        ]

        # Only output the gathered data if at least one retrieval occurred and
        # there was no error in the entire retrieval process
        if data_retrieval_failed_list and not any(data_retrieval_failed_list):
            self.logger.debug(self._display_data(processed_data))

        # Send a heartbeat only if the entire round was successful
        heartbeat = {
            'component_name': self.monitor_name,
            'is_alive': True,
            'timestamp': datetime.now().timestamp()
        }
        self._send_heartbeat(heartbeat)
