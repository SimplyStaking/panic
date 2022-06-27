import copy
import json
import logging
from datetime import datetime
from typing import List, Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel

import src.alerter.alerts.node.substrate as substrate_alerts
from src.alerter.alert_severities import Severity
from src.alerter.alerters.alerter import Alerter
from src.alerter.factory.substrate_node_alerting_factory import (
    SubstrateNodeAlertingFactory)
from src.alerter.grouped_alerts_metric_code.node.substrate_node_metric_code \
    import GroupedSubstrateNodeAlertsMetricCode as MetricCode
from src.configs.alerts.node.substrate import SubstrateNodeAlertsConfig
from src.configs.factory.alerts.substrate_alerts import (
    SubstrateNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.data import VALID_SUBSTRATE_NODE_SOURCES
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY, SUBSTRATE_NODE_ALERT_ROUTING_KEY)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import (
    MessageWasNotDeliveredException, NoSyncedDataSourceWasAccessibleException,
    SubstrateWebSocketDataCouldNotBeObtained, NodeIsDownException,
    SubstrateApiIsNotReachableException)
from src.utils.types import str_to_bool


class SubstrateNodeAlerter(Alerter):
    """
    We will have one alerter for all substrate nodes. The substrate alerter 
    doesn't have to restart if the configurations change, as it will be 
    listening for both data and configs in the same queue.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            rabbitmq: RabbitMQApi,
            substrate_alerts_configs_factory: SubstrateNodeAlertsConfigsFactory,
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = substrate_alerts_configs_factory
        self._alerting_factory = SubstrateNodeAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> SubstrateNodeAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_factory(self) -> SubstrateNodeAlertingFactory:
        return self._alerting_factory

    def _initialise_rabbitmq(self) -> None:
        # An alerter is both a consumer and producer, therefore we need to
        # initialise both the consuming and producing configurations.
        self.rabbitmq.connect_till_successful()

        # Set alerts consuming configuration
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(
            exchange=ALERT_EXCHANGE, exchange_type=TOPIC, passive=False,
            durable=True, auto_delete=False, internal=False)
        self.logger.info("Creating queue '%s'",
                         SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, passive=False,
            durable=True, exclusive=False, auto_delete=False)
        self.logger.info(
            "Binding queue '%s' to exchange '%s' with routing key '%s'",
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, ALERT_EXCHANGE,
            SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
            exchange=ALERT_EXCHANGE,
            routing_key=SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Set configs consuming configuration
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
            SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(
            queue=SUBSTRATE_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
            on_message_callback=self._process_data, auto_ack=False,
            exclusive=False, consumer_tag=None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _process_data(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        """
        This function calls the appropriate processing function depending on
        whether we received configs or transformed data. If none of this is
        received the message is ignored.
        :param ch: The rabbit channel
        :param method: Pika method
        :param properties: Pika properties
        :param body: The message
        :return:
        """
        if method.routing_key == SUBSTRATE_NODE_TRANSFORMED_DATA_ROUTING_KEY:
            self._process_transformed_data(method, body)
        elif 'alerts_config' in method.routing_key:
            self._process_configs(method, body)
        else:
            self.logger.debug("Received unexpected data %s with routing key %s",
                              body, method.routing_key)
            self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_websocket_result(self, websocket_data: Dict,
                                  data_for_alerting: List) -> None:
        meta_data = websocket_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        last_monitored = meta_data['last_monitored']
        token_symbol = meta_data['token_symbol']
        data = websocket_data['data']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, SubstrateNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Check if some errors have been resolved
            self.alerting_factory.classify_websocket_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                (substrate_alerts.
                 ErrorNoSyncedSubstrateWebSocketDataSourcesAlert),
                substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
                data_for_alerting, parent_id, node_id, node_name,
                last_monitored,
                MetricCode.NoSyncedSubstrateWebSocketSource.value, "",
                "The monitor for {} found a websocket synced data "
                "source again.".format(node_name), None
            )
            self.alerting_factory.classify_websocket_error_alert(
                SubstrateWebSocketDataCouldNotBeObtained.code,
                substrate_alerts.SubstrateWebSocketDataCouldNotBeObtainedAlert,
                substrate_alerts.SubstrateWebSocketDataObtainedAlert,
                data_for_alerting, parent_id, node_id, node_name,
                last_monitored,
                MetricCode.SubstrateWebSocketDataNotObtained.value, "",
                "The monitor for {} successfully retrieved websocket data "
                "again.".format(node_name), None
            )

            # Check if the alert rules are satisfied for the metrics
            no_change_in_best_block_configs = (
                configs.no_change_in_best_block_height_validator if is_validator
                else configs.no_change_in_best_block_height_node
            )
            if str_to_bool(no_change_in_best_block_configs['enabled']):
                current = data['best_height']['current']
                previous = data['best_height']['previous']
                if current is not None and previous is not None:
                    self.alerting_factory.classify_no_change_in_alert(
                        current, previous, no_change_in_best_block_configs,
                        substrate_alerts.NoChangeInBestBlockHeightAlert,
                        substrate_alerts.BestBlockHeightUpdatedAlert,
                        data_for_alerting, parent_id, node_id,
                        MetricCode.NoChangeInBestBlockHeight.value, node_name,
                        last_monitored
                    )

            no_change_in_finalized_block_configs = (
                configs.no_change_in_finalized_block_height_validator
                if is_validator
                else configs.no_change_in_finalized_block_height_node
            )
            if str_to_bool(no_change_in_finalized_block_configs['enabled']):
                current = data['finalized_height']['current']
                previous = data['finalized_height']['previous']
                if current is not None and previous is not None:
                    self.alerting_factory.classify_no_change_in_alert(
                        current, previous, no_change_in_finalized_block_configs,
                        substrate_alerts.NoChangeInFinalizedBlockHeightAlert,
                        substrate_alerts.FinalizedBlockHeightUpdatedAlert,
                        data_for_alerting, parent_id, node_id,
                        MetricCode.NoChangeInFinalizedBlockHeight.value,
                        node_name, last_monitored
                    )

            is_syncing_configs = (
                configs.validator_is_syncing if is_validator
                else configs.node_is_syncing
            )
            if str_to_bool(is_syncing_configs['enabled']):
                current_target_height = data['target_height']['current']
                current_best_height = data['best_height']['current']
                if (current_target_height is not None and
                        current_best_height is not None):
                    difference = abs(current_target_height -
                                     current_best_height)
                    self.alerting_factory.classify_thresholded_alert(
                        difference, is_syncing_configs,
                        substrate_alerts.NodeIsSyncingAlert,
                        substrate_alerts.NodeIsNoLongerSyncingAlert,
                        data_for_alerting, parent_id, node_id,
                        MetricCode.NodeIsSyncing.value, node_name,
                        last_monitored
                    )

            not_active_configs = configs.not_active_in_session
            classification_fn = (
                self.alerting_factory
                    .classify_solvable_conditional_alert_no_repetition
            )
            if str_to_bool(not_active_configs['enabled']):
                current_active = data['active']['current']
                if current_active is not None:
                    classification_fn(
                        parent_id, node_id,
                        MetricCode.ValidatorIsNotActive.value,
                        substrate_alerts.ValidatorIsNotActiveAlert,
                        self._is_true_condition_function,
                        [is_validator and not current_active],
                        [node_name, not_active_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting,
                        substrate_alerts.ValidatorIsActiveAlert,
                        [node_name, Severity.INFO.value, last_monitored,
                         parent_id, node_id]
                    )

            is_disabled_configs = configs.is_disabled
            classification_fn = (
                self.alerting_factory
                    .classify_solvable_conditional_alert_no_repetition
            )
            if str_to_bool(is_disabled_configs['enabled']):
                current_disabled = data['disabled']['current']
                if current_disabled is not None:
                    classification_fn(
                        parent_id, node_id,
                        MetricCode.ValidatorIsDisabled.value,
                        substrate_alerts.ValidatorIsDisabledAlert,
                        self._is_true_condition_function,
                        [is_validator and current_disabled],
                        [node_name, is_disabled_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting,
                        substrate_alerts.ValidatorIsNoLongerDisabledAlert,
                        [node_name, Severity.INFO.value, last_monitored,
                         parent_id, node_id]
                    )

            not_elected_configs = configs.not_elected
            classification_fn = (
                self.alerting_factory
                    .classify_solvable_conditional_alert_no_repetition
            )
            if str_to_bool(not_elected_configs['enabled']):
                current_elected = data['elected']['current']
                if current_elected is not None:
                    classification_fn(
                        parent_id, node_id,
                        MetricCode.ValidatorWasNotElected.value,
                        substrate_alerts.ValidatorWasNotElectedAlert,
                        self._is_true_condition_function,
                        [is_validator and not current_elected],
                        [node_name, not_elected_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting,
                        substrate_alerts.ValidatorWasElectedAlert,
                        [node_name, Severity.INFO.value, last_monitored,
                         parent_id, node_id]
                    )

            bonded_amount_change_configs = configs.bonded_amount_change
            if str_to_bool(bonded_amount_change_configs['enabled']):
                current_amount = data['eras_stakers']['current']['total']
                previous_amount = data['eras_stakers']['previous']['total']
                # Here we do not check whether node is validator since previous
                # and current bonded amounts are always 0 for non-validators
                if current_amount is not None and previous_amount is not None:
                    self.alerting_factory.classify_conditional_alert(
                        substrate_alerts.ValidatorBondedAmountChangedAlert,
                        self._not_equal_condition_function,
                        [current_amount, previous_amount],
                        [node_name, current_amount, previous_amount,
                         token_symbol, bonded_amount_change_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting
                    )

            no_heartbeat_did_not_author_block_configs = (
                configs.no_heartbeat_did_not_author_block
            )
            classification_fn = (
                self.alerting_factory.classify_conditional_no_change_in_alert
            )
            conditional_no_change_alert = (
                (substrate_alerts.
                 ValidatorNoHeartbeatAndBlockAuthoredYetAlert))
            if str_to_bool(
                    no_heartbeat_did_not_author_block_configs['enabled']):
                current_session = data['current_session']['current']
                previous_session = data['current_session']['previous']
                current_disabled = data['disabled']['current']
                current_active = data['active']['current']
                current_authored_blocks = data['authored_blocks']['current']
                current_sent_heartbeat = data['sent_heartbeat']['current']
                # Here we do not check whether node is validator since
                # current active is always False for non-validators
                if not current_disabled and current_active:
                    classification_fn(
                        current_session, previous_session,
                        no_heartbeat_did_not_author_block_configs,
                        conditional_no_change_alert,
                        (substrate_alerts.
                         ValidatorHeartbeatSentOrBlockAuthoredAlert),
                        self._is_true_condition_function,
                        [current_authored_blocks == 0 and
                         not current_sent_heartbeat],
                        data_for_alerting, parent_id, node_id,
                        (MetricCode.
                         ValidatorNoHeartbeatAndBlockAuthoredYetAlert.
                         value), node_name, last_monitored
                    )

            offline_configs = configs.offline
            if str_to_bool(offline_configs['enabled']):
                current_historical = data['historical']['current']
                # Here we do not check whether node is validator since
                # historical blocks list is always empty for non-validators
                for block in current_historical:
                    self.alerting_factory.classify_conditional_alert(
                        substrate_alerts.ValidatorWasOfflineAlert,
                        self._is_true_condition_function, [block['is_offline']],
                        [node_name, block['height'],
                         offline_configs['severity'], last_monitored,
                         parent_id, node_id], data_for_alerting
                    )

            slashed_configs = configs.slashed
            if str_to_bool(slashed_configs['enabled']):
                current_historical = data['historical']['current']
                # Here we do not check whether node is validator since
                # historical blocks list is always empty for non-validators
                for block in current_historical:
                    self.alerting_factory.classify_conditional_alert(
                        substrate_alerts.ValidatorWasSlashedAlert,
                        self._is_true_condition_function, [block['slashed']],
                        [node_name, block['slashed_amount'], block['height'],
                         token_symbol, slashed_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting
                    )

            payout_not_claimed_configs = configs.payout_not_claimed
            if str_to_bool(payout_not_claimed_configs['enabled']):
                current_era = data['current_era']['current']
                current_unclaimed_rewards = data['unclaimed_rewards']['current']
                # Here we do not check whether node is validator since
                # unclaimed rewards list is always empty for non-validators
                for unclaimed_reward_era in current_unclaimed_rewards:
                    era_difference = abs(current_era - unclaimed_reward_era)
                    self.alerting_factory.classify_thresholded_era_alert(
                        unclaimed_reward_era, era_difference,
                        payout_not_claimed_configs,
                        substrate_alerts.ValidatorPayoutNotClaimedAlert,
                        data_for_alerting, parent_id, node_id,
                        MetricCode.ValidatorPayoutNotClaimed.value, node_name,
                        last_monitored
                    )

                current_claimed_rewards = data['claimed_rewards']['current']
                previous_claimed_rewards = data['claimed_rewards']['previous']
                new_claimed_rewards = (list(set(current_claimed_rewards) -
                                            set(previous_claimed_rewards)))
                # Here we do not check whether node is validator since
                # claimed rewards list is always empty for non-validators
                for claimed_reward_era in new_claimed_rewards:
                    self.alerting_factory.classify_era_solve_alert(
                        claimed_reward_era,
                        substrate_alerts.ValidatorPayoutClaimedAlert,
                        data_for_alerting, parent_id, node_id, node_name,
                        last_monitored
                    )

            controller_address_change_configs = (
                configs.controller_address_change)
            if str_to_bool(controller_address_change_configs['enabled']):
                current_controller_address = (
                    data['controller_address']['current'])
                previous_controller_address = (
                    data['controller_address']['previous'])
                # Here we do not check whether node is validator since
                # controller addresses are always None for non-validators
                if (current_controller_address is not None and
                        previous_controller_address is not None):
                    self.alerting_factory.classify_conditional_alert(
                        substrate_alerts.ValidatorControllerAddressChangedAlert,
                        self._not_equal_condition_function,
                        [current_controller_address,
                         previous_controller_address],
                        [node_name, current_controller_address,
                         previous_controller_address,
                         controller_address_change_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting
                    )

    def _process_websocket_error(self, websocket_data: Dict,
                                 data_for_alerting: List) -> None:
        meta_data = websocket_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        time = meta_data['time']
        err_message = websocket_data['message']
        err_code = websocket_data['code']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, SubstrateNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_websocket_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                (substrate_alerts.
                 ErrorNoSyncedSubstrateWebSocketDataSourcesAlert),
                substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
                data_for_alerting, parent_id, node_id, node_name, time,
                MetricCode.NoSyncedSubstrateWebSocketSource.value, err_message,
                "The monitor for {} found a websocket synced data source "
                "again.".format(node_name), err_code
            )
            self.alerting_factory.classify_websocket_error_alert(
                SubstrateWebSocketDataCouldNotBeObtained.code,
                substrate_alerts.SubstrateWebSocketDataCouldNotBeObtainedAlert,
                substrate_alerts.SubstrateWebSocketDataObtainedAlert,
                data_for_alerting, parent_id, node_id, node_name, time,
                MetricCode.SubstrateWebSocketDataNotObtained.value, err_message,
                "The monitor for {} successfully retrieved websocket data "
                "again.".format(node_name), err_code
            )

    def _process_downtime(self, trans_data: Dict,
                          data_for_alerting: List) -> None:
        # We will parse some meta_data first, note we will assume that the
        # transformed data has the correct structure, as the data was validated
        # inside the data transformer. The logic found in this function caters
        # for multiple sources despite only having one source currently.
        enabled_source = [
            source for source in VALID_SUBSTRATE_NODE_SOURCES if
            trans_data[source]
        ][0]
        response_index_key = 'result' if 'result' in trans_data[
            enabled_source] else 'error'
        parent_id = trans_data[enabled_source][response_index_key]['meta_data'][
            'node_parent_id']
        origin_id = trans_data[enabled_source][response_index_key]['meta_data'][
            'node_id']
        origin_name = trans_data[enabled_source][response_index_key][
            'meta_data']['node_name']
        is_validator = trans_data[enabled_source][response_index_key][
            'meta_data']['is_validator']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, SubstrateNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, origin_id, configs, is_validator)

            # All sources are down if the enabled sources all returned a
            # NodeIsDown error. Note that we must have at least one enabled
            # source, this has been verified inside the transformer.
            all_sources_down = all([
                'error' in trans_data[source]
                and trans_data[source]['error'][
                    'code'] == NodeIsDownException.code
                for source in VALID_SUBSTRATE_NODE_SOURCES if trans_data[source]
            ])

            # Compute which sources are down
            down_sources = [
                source
                for source in VALID_SUBSTRATE_NODE_SOURCES
                if (trans_data[source]
                    and 'error' in trans_data[source]
                    and trans_data[source]['error'][
                        'code'] == NodeIsDownException.code)
            ]

            # Check for node downtime or node back up.
            downtime_configs = (
                configs.cannot_access_validator if is_validator
                else configs.cannot_access_node
            )
            if str_to_bool(downtime_configs['enabled']):
                if all_sources_down:
                    # A node is declared down if all enabled data sources
                    # returned a downtime error.

                    # Choose the largest went_down_at as that signals when
                    # downtime was detected, as all sources need to be down.
                    current_went_down = max([
                        trans_data[source]['error']['data']['went_down_at'][
                            'current']
                        for source in down_sources
                    ])

                    # Choose the maximum monitoring_timestamp as all sources
                    # were down at that point.
                    monitoring_timestamp = max([
                        trans_data[source]['error']['meta_data']['time']
                        for source in down_sources
                    ])

                    self.alerting_factory.classify_downtime_alert(
                        current_went_down, downtime_configs,
                        substrate_alerts.NodeWentDownAtAlert,
                        substrate_alerts.NodeStillDownAlert,
                        substrate_alerts.NodeBackUpAgainAlert,
                        data_for_alerting,
                        parent_id, origin_id, MetricCode.NodeIsDown.value,
                        origin_name, monitoring_timestamp
                    )
                else:
                    # Choose the minimum monitoring_timestamp from all enabled
                    # non-down sources, as that is the point where downtime is
                    # first solved.
                    monitoring_timestamp = min([
                        trans_data[source]['result']['meta_data'][
                            'last_monitored']
                        if 'result' in trans_data[source]
                        else trans_data[source]['error']['meta_data']['time']
                        for source in VALID_SUBSTRATE_NODE_SOURCES
                        if trans_data[source] and source not in down_sources
                    ])

                    # Classify downtime so that a node back up again alert is
                    # raised if need be.
                    (self.alerting_factory.
                        classify_downtime_alert_with_substrate_api_downtime(
                        None, downtime_configs,
                        substrate_alerts.NodeWentDownAtAlert,
                        substrate_alerts.NodeStillDownAlert,
                        substrate_alerts.NodeBackUpAgainAlert,
                        data_for_alerting, parent_id, origin_id,
                        MetricCode.NodeIsDown.value, origin_name,
                        monitoring_timestamp
                    ))

                    # In the future, if we add more sources, we must check for
                    # the downtime for each source. The classification functions
                    # used should depend on whether the source is related to the
                    # Substrate API or not.

    def _process_substrate_api_error(self, trans_data: Dict,
                                     data_for_alerting: List) -> None:
        # We will parse some meta_data first, note we will assume that the
        # transformed data has the correct structure, as the data was validated
        # inside the data transformer. The logic found in this function caters
        # only for websocket data since this is related to the substrate API.
        if not trans_data['websocket']:
            return

        response_index_key = ('result' if 'result' in trans_data['websocket']
                              else 'error')
        data = trans_data['websocket'][response_index_key]
        is_validator = data['meta_data']['is_validator']
        parent_id = data['meta_data']['node_parent_id']
        node_id = data['meta_data']['node_id']
        node_name = data['meta_data']['node_name']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, SubstrateNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            if response_index_key == 'result':
                # Resolve Substrate API error
                self.alerting_factory.classify_websocket_error_alert(
                    SubstrateApiIsNotReachableException.code,
                    substrate_alerts.SubstrateApiIsNotReachableAlert,
                    substrate_alerts.SubstrateApiIsReachableAlert,
                    data_for_alerting, parent_id, node_id, node_name,
                    data['meta_data']['last_monitored'],
                    MetricCode.SubstrateApiNotReachable.value, "",
                    "The monitor for {} is now reaching the Substrate "
                    "API.".format(node_name), None
                )
            else:
                # Detect whether error needs to be raised, or has been resolved.
                self.alerting_factory.classify_websocket_error_alert(
                    SubstrateApiIsNotReachableException.code,
                    substrate_alerts.SubstrateApiIsNotReachableAlert,
                    substrate_alerts.SubstrateApiIsReachableAlert,
                    data_for_alerting, parent_id, node_id, node_name,
                    data['meta_data']['time'],
                    MetricCode.SubstrateApiNotReachable.value, data['message'],
                    "The monitor for {} is now reaching the Substrate "
                    "API.".format(node_name), data['code']
                )

    def _process_transformed_data(self, method: pika.spec.Basic.Deliver,
                                  body: bytes) -> None:
        data_received = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.",
                          data_received)

        processing_error = False
        data_for_alerting = []
        try:
            configuration = {
                'websocket': {
                    'result': self._process_websocket_result,
                    'error': self._process_websocket_error,
                }
            }
            self._process_substrate_api_error(data_received, data_for_alerting)
            self._process_downtime(data_received, data_for_alerting)
            transformed_data_processing_helper(
                self.alerter_name, configuration, data_received,
                data_for_alerting)
        except Exception as e:
            self.logger.error("Error when processing %s", data_received)
            self.logger.exception(e)
            processing_error = True

        # Place the data on the publishing queue if there is something to send.
        if len(data_for_alerting) != 0:
            self._place_latest_data_on_queue(data_for_alerting)

        # If the data is processed, it can be acknowledged.
        self.rabbitmq.basic_ack(method.delivery_tag, False)

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()

            if not processing_error:
                heartbeat = {
                    'component_name': self.alerter_name,
                    'is_alive': True,
                    'timestamp': datetime.now().timestamp()
                }
                self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise the exception so that the
            # message can be acknowledged and removed from the rabbit queue.
            # Note this message will still reside in the publisher queue.
            self.logger.exception(e)
        except Exception as e:
            # For any other exception acknowledge and raise it, so the
            # message is removed from the rabbit queue as this message will now
            # reside in the publisher queue
            raise e

    def _process_configs(self, method: pika.spec.Basic.Deliver,
                         body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.debug("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        try:
            # Checking if the configuration is empty. If it is empty, remove the
            # stored config (if it exists), and if it is not add it to the list
            # of configurations.
            if bool(sent_configs):
                self.alerts_configs_factory.add_new_config(chain, sent_configs)

                # We must reset the state since some thresholds might have
                # changed. A node's state will be recreated in the next
                # monitoring round automatically. Note we are sure that a
                # parent_id is to be returned, as we have just added the config.
                # NOTE: Internal alerts for metric state reset are to be sent
                #     : by the manager.
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, SubstrateNodeAlertsConfig)
                self.alerting_factory.remove_chain_alerting_state(parent_id)
            else:
                # We must reset the state since a configuration is to be
                # removed. Note that first we need to compute the parent_id, as
                # the parent_id is obtained from the configs to be removed from
                # the factory. If the parent_id cannot be found, it means that
                # no storing took place, therefore in that case do nothing.
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, SubstrateNodeAlertsConfig)
                if parent_id:
                    self.alerting_factory.remove_chain_alerting_state(parent_id)
                    self.alerts_configs_factory.remove_config(chain)
        except Exception as e:
            # Otherwise log and reject the message
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _place_latest_data_on_queue(self, data_list: List) -> None:
        # Place the latest alert data on the publishing queue. If the queue is
        # full, remove old data.
        for alert in data_list:
            self.logger.debug("Adding %s to the publishing queue.", alert)
            if self.publishing_queue.full():
                self.publishing_queue.get()
            self.publishing_queue.put({
                'exchange': ALERT_EXCHANGE,
                'routing_key': SUBSTRATE_NODE_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
