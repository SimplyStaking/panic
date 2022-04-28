import copy
import json
import logging
from datetime import datetime
from typing import List, Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel

import src.alerter.alerts.node.cosmos as cosmos_alerts
from src.alerter.alert_severities import Severity
from src.alerter.alerters.alerter import Alerter
from src.alerter.factory.cosmos_node_alerting_factory import (
    CosmosNodeAlertingFactory)
from src.alerter.grouped_alerts_metric_code.node.cosmos_node_metric_code \
    import GroupedCosmosNodeAlertsMetricCode as MetricCode
from src.configs.alerts.node.cosmos import CosmosNodeAlertsConfig
from src.configs.factory.alerts.cosmos_alerts import (
    CosmosNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.cosmos import BOND_STATUS_BONDED
from src.utils.constants.data import VALID_COSMOS_NODE_SOURCES
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY,
    COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    COSMOS_ALERTS_CONFIGS_ROUTING_KEY, COSMOS_NODE_ALERT_ROUTING_KEY)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import (
    MessageWasNotDeliveredException, InvalidUrlException,
    MetricNotFoundException, NoSyncedDataSourceWasAccessibleException,
    CosmosRestServerDataCouldNotBeObtained, TendermintRPCDataCouldNotBeObtained,
    NodeIsDownException)
from src.utils.types import str_to_bool


class CosmosNodeAlerter(Alerter):
    """
    We will have one alerter for all cosmos nodes. The cosmos alerter doesn't
    have to restart if the configurations change, as it will be listening for
    both data and configs in the same queue.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            rabbitmq: RabbitMQApi,
            cosmos_alerts_configs_factory: CosmosNodeAlertsConfigsFactory,
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = cosmos_alerts_configs_factory
        self._alerting_factory = CosmosNodeAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> CosmosNodeAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_factory(self) -> CosmosNodeAlertingFactory:
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
                         COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, passive=False,
            durable=True, exclusive=False, auto_delete=False)
        self.logger.info(
            "Binding queue '%s' to exchange '%s' with routing key '%s'",
            COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, ALERT_EXCHANGE,
            COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
            exchange=ALERT_EXCHANGE,
            routing_key=COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Set configs consuming configuration
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, COSMOS_ALERTS_CONFIGS_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
            COSMOS_ALERTS_CONFIGS_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(
            queue=COSMOS_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
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
        if method.routing_key == COSMOS_NODE_TRANSFORMED_DATA_ROUTING_KEY:
            self._process_transformed_data(method, body)
        elif 'alerts_config' in method.routing_key:
            self._process_configs(method, body)
        else:
            self.logger.debug("Received unexpected data %s with routing key %s",
                              body, method.routing_key)
            self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_prometheus_result(self, prom_data: Dict,
                                   data_for_alerting: List) -> None:
        meta_data = prom_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        last_monitored = meta_data['last_monitored']
        data = prom_data['data']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Check if some errors have been resolved

            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code,
                cosmos_alerts.PrometheusInvalidUrlAlert,
                cosmos_alerts.PrometheusValidUrlAlert, data_for_alerting,
                parent_id, node_id, node_name, last_monitored,
                MetricCode.PrometheusInvalidUrl.value, "",
                "Prometheus url is now valid!", None
            )
            self.alerting_factory.classify_error_alert(
                MetricNotFoundException.code,
                cosmos_alerts.MetricNotFoundErrorAlert,
                cosmos_alerts.MetricFoundAlert, data_for_alerting,
                parent_id, node_id, node_name, last_monitored,
                MetricCode.MetricNotFound.value, "", "All metrics found!", None
            )

            # Check if the alert rules are satisfied for the metrics

            no_change_in_configs = (
                configs.no_change_in_block_height_validator if is_validator
                else configs.no_change_in_block_height_node
            )
            if str_to_bool(no_change_in_configs['enabled']):
                current = data['current_height']['current']
                previous = data['current_height']['previous']
                if current is not None and previous is not None:
                    self.alerting_factory.classify_no_change_in_alert(
                        current, previous, no_change_in_configs,
                        cosmos_alerts.NoChangeInHeightAlert,
                        cosmos_alerts.BlockHeightUpdatedAlert,
                        data_for_alerting, parent_id, node_id,
                        MetricCode.NoChangeInHeight.value, node_name,
                        last_monitored
                    )

            height_difference_configs = configs.block_height_difference
            if str_to_bool(height_difference_configs['enabled']):
                current = data['current_height']['current']
                if current is not None:
                    # The only data we need is the highest node block height,
                    # we then return the difference between the current
                    # node's height and the maximum height found in the list.
                    # The number can never be negative and the list can never be
                    # empty as we are including our own node.
                    self.alerting_factory.alerting_state[parent_id][node_id][
                        'current_height'] = current
                    node_heights = [
                        state['current_height']
                        for _, state in self.alerting_factory.alerting_state[
                            parent_id].items()
                        if state['current_height'] is not None
                    ]
                    difference = max(node_heights) - current
                    self.alerting_factory.classify_thresholded_alert(
                        difference, height_difference_configs,
                        cosmos_alerts
                            .BlockHeightDifferenceIncreasedAboveThresholdAlert,
                        cosmos_alerts
                            .BlockHeightDifferenceDecreasedBelowThresholdAlert,
                        data_for_alerting, parent_id, node_id,
                        MetricCode.BlockHeightDifferenceThreshold.value,
                        node_name, last_monitored
                    )

    def _process_prometheus_error(self, prom_data: Dict,
                                  data_for_alerting: List) -> None:
        meta_data = prom_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        time = meta_data['time']
        err_message = prom_data['message']
        err_code = prom_data['code']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code,
                cosmos_alerts.PrometheusInvalidUrlAlert,
                cosmos_alerts.PrometheusValidUrlAlert, data_for_alerting,
                parent_id, node_id, node_name, time,
                MetricCode.PrometheusInvalidUrl.value, err_message,
                "Prometheus url is now valid!", err_code
            )
            self.alerting_factory.classify_error_alert(
                MetricNotFoundException.code,
                cosmos_alerts.MetricNotFoundErrorAlert,
                cosmos_alerts.MetricFoundAlert, data_for_alerting, parent_id,
                node_id, node_name, time, MetricCode.MetricNotFound.value,
                err_message, "All metrics found!", err_code
            )

    def _process_cosmos_rest_result(self, rest_data: Dict,
                                    data_for_alerting: List) -> None:
        meta_data = rest_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        last_monitored = meta_data['last_monitored']
        data = rest_data['data']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Check if some errors have been resolved

            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code,
                cosmos_alerts.CosmosRestInvalidUrlAlert,
                cosmos_alerts.CosmosRestValidUrlAlert, data_for_alerting,
                parent_id, node_id, node_name, last_monitored,
                MetricCode.CosmosRestInvalidUrl.value, "",
                "Cosmos-Rest url is now valid!", None
            )
            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
                cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
                data_for_alerting, parent_id, node_id, node_name,
                last_monitored, MetricCode.NoSyncedCosmosRestSource.value, "",
                "The monitor for {} found a Cosmos-Rest synced data "
                "source again".format(node_name), None
            )
            self.alerting_factory.classify_error_alert(
                CosmosRestServerDataCouldNotBeObtained.code,
                cosmos_alerts.CosmosRestServerDataCouldNotBeObtainedAlert,
                cosmos_alerts.CosmosRestServerDataObtainedAlert,
                data_for_alerting, parent_id, node_id, node_name,
                last_monitored, MetricCode.CosmosRestDataNotObtained.value, "",
                "The monitor for {} successfully retrieved Cosmos-Rest data "
                "again.".format(node_name), None
            )

            # Check if the alert rules are satisfied for the metrics

            jailed_configs = configs.validator_is_jailed
            classification_fn = (
                self.alerting_factory
                    .classify_solvable_conditional_alert_no_repetition
            )
            if str_to_bool(jailed_configs['enabled']):
                current = data['jailed']['current']
                if current is not None:
                    classification_fn(
                        parent_id, node_id, MetricCode.ValidatorIsJailed.value,
                        cosmos_alerts.ValidatorIsJailedAlert,
                        self._is_true_condition_function, [current],
                        [node_name, jailed_configs['severity'], last_monitored,
                         parent_id, node_id], data_for_alerting,
                        cosmos_alerts.ValidatorIsNoLongerJailedAlert,
                        [node_name, Severity.INFO.value, last_monitored,
                         parent_id, node_id]
                    )

            not_active_configs = configs.validator_not_active_in_session
            classification_fn = (
                self.alerting_factory
                    .classify_solvable_conditional_alert_no_repetition
            )
            if str_to_bool(not_active_configs['enabled']):
                current = data['bond_status']['current']
                if current is not None:
                    classification_fn(
                        parent_id, node_id,
                        MetricCode.ValidatorIsNotActive.value,
                        cosmos_alerts.ValidatorIsNotActiveAlert,
                        self._node_is_not_active_condition_function,
                        [is_validator, current],
                        [node_name, not_active_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting,
                        cosmos_alerts.ValidatorIsActiveAlert,
                        [node_name, Severity.INFO.value, last_monitored,
                         parent_id, node_id]
                    )

    @staticmethod
    def _node_is_not_active_condition_function(is_validator: bool,
                                               bond_status: str) -> bool:
        """
        We will alert that a node is no longer active if it is a
        validator and its bond status is not bonded.
        :param is_validator: Whether the node is a validator
        :param bond_status: The bond status of the node
        :return: True if we should alert that node is no longer active
               : False otherwise
        """
        return is_validator and bond_status != BOND_STATUS_BONDED

    def _process_cosmos_rest_error(self, rest_data: Dict,
                                   data_for_alerting: List) -> None:
        meta_data = rest_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        time = meta_data['time']
        err_message = rest_data['message']
        err_code = rest_data['code']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code,
                cosmos_alerts.CosmosRestInvalidUrlAlert,
                cosmos_alerts.CosmosRestValidUrlAlert, data_for_alerting,
                parent_id, node_id, node_name, time,
                MetricCode.CosmosRestInvalidUrl.value, err_message,
                "Cosmos-Rest url is now valid!", err_code
            )
            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
                cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
                data_for_alerting, parent_id, node_id, node_name, time,
                MetricCode.NoSyncedCosmosRestSource.value, err_message,
                "The monitor for {} found a Cosmos-Rest synced data source "
                "again".format(node_name), err_code
            )
            self.alerting_factory.classify_error_alert(
                CosmosRestServerDataCouldNotBeObtained.code,
                cosmos_alerts.CosmosRestServerDataCouldNotBeObtainedAlert,
                cosmos_alerts.CosmosRestServerDataObtainedAlert,
                data_for_alerting, parent_id, node_id, node_name, time,
                MetricCode.CosmosRestDataNotObtained.value, err_message,
                "The monitor for {} successfully retrieved Cosmos-Rest data "
                "again.".format(node_name), err_code
            )

    def _process_tendermint_rpc_result(self, tendermint_data: Dict,
                                       data_for_alerting: List) -> None:
        meta_data = tendermint_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        last_monitored = meta_data['last_monitored']
        data = tendermint_data['data']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Check if some errors have been resolved

            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code,
                cosmos_alerts.TendermintRPCInvalidUrlAlert,
                cosmos_alerts.TendermintRPCValidUrlAlert, data_for_alerting,
                parent_id, node_id, node_name, last_monitored,
                MetricCode.TendermintRPCInvalidUrl.value, "",
                "Tendermint-RPC url is now valid!", None
            )
            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                cosmos_alerts.ErrorNoSyncedTendermintRPCDataSourcesAlert,
                cosmos_alerts.SyncedTendermintRPCDataSourcesFoundAlert,
                data_for_alerting, parent_id, node_id, node_name,
                last_monitored, MetricCode.NoSyncedTendermintRPCSource.value,
                "", "The monitor for {} found a Tendermint-RPC synced data "
                    "source again".format(node_name), None
            )
            self.alerting_factory.classify_error_alert(
                TendermintRPCDataCouldNotBeObtained.code,
                cosmos_alerts.TendermintRPCDataCouldNotBeObtainedAlert,
                cosmos_alerts.TendermintRPCDataObtainedAlert, data_for_alerting,
                parent_id, node_id, node_name, last_monitored,
                MetricCode.TendermintRPCDataNotObtained.value, "",
                "The monitor for {} successfully retrieved Tendermint-RPC data "
                "again.".format(node_name), None
            )

            # Check if the alert rules are satisfied for the metrics

            is_syncing_configs = (
                configs.validator_is_syncing if is_validator
                else configs.node_is_syncing
            )
            classification_fn = (
                self.alerting_factory
                    .classify_solvable_conditional_alert_no_repetition
            )
            if str_to_bool(is_syncing_configs['enabled']):
                current = data['is_syncing']['current']
                if current is not None:
                    classification_fn(
                        parent_id, node_id, MetricCode.NodeIsSyncing.value,
                        cosmos_alerts.NodeIsSyncingAlert,
                        self._is_true_condition_function, [current],
                        [node_name, is_syncing_configs['severity'],
                         last_monitored, parent_id, node_id], data_for_alerting,
                        cosmos_alerts.NodeIsNoLongerSyncingAlert,
                        [node_name, Severity.INFO.value, last_monitored,
                         parent_id, node_id]
                    )

            slashed_configs = configs.slashed
            if str_to_bool(slashed_configs['enabled']):
                current = data['slashed']['current']
                was_slashed = current['slashed']
                amounts = current['amount_map']
                if was_slashed:
                    for height, slashed_amount in amounts.items():
                        self.alerting_factory.classify_conditional_alert(
                            cosmos_alerts.ValidatorWasSlashedAlert,
                            self._true_fn, [],
                            [node_name, slashed_amount, int(height),
                             slashed_configs['severity'], last_monitored,
                             parent_id, node_id], data_for_alerting, None, None
                        )

            missed_blocks_configs = configs.missed_blocks
            if str_to_bool(missed_blocks_configs['enabled']):
                current = data['missed_blocks']['current']
                previous = data['missed_blocks']['previous']
                self.alerting_factory.classify_thresholded_in_time_period_alert(
                    current['total_count'], previous['total_count'],
                    missed_blocks_configs,
                    cosmos_alerts.BlocksMissedIncreasedAboveThresholdAlert,
                    cosmos_alerts.BlocksMissedDecreasedBelowThresholdAlert,
                    data_for_alerting, parent_id, node_id,
                    MetricCode.BlocksMissedThreshold.value, node_name,
                    last_monitored
                )

    def _process_tendermint_rpc_error(self, tendermint_data: Dict,
                                      data_for_alerting: List) -> None:
        meta_data = tendermint_data['meta_data']
        is_validator = meta_data['is_validator']
        parent_id = meta_data['node_parent_id']
        node_id = meta_data['node_id']
        node_name = meta_data['node_name']
        time = meta_data['time']
        err_message = tendermint_data['message']
        err_code = tendermint_data['code']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                parent_id, node_id, configs, is_validator)

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code,
                cosmos_alerts.TendermintRPCInvalidUrlAlert,
                cosmos_alerts.TendermintRPCValidUrlAlert, data_for_alerting,
                parent_id, node_id, node_name, time,
                MetricCode.TendermintRPCInvalidUrl.value, err_message,
                "Tendermint-RPC url is now valid!", err_code
            )
            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                cosmos_alerts.ErrorNoSyncedTendermintRPCDataSourcesAlert,
                cosmos_alerts.SyncedTendermintRPCDataSourcesFoundAlert,
                data_for_alerting, parent_id, node_id, node_name, time,
                MetricCode.NoSyncedTendermintRPCSource.value, err_message,
                "The monitor for {} found a Tendermint-RPC synced data source "
                "again".format(node_name), err_code
            )
            self.alerting_factory.classify_error_alert(
                TendermintRPCDataCouldNotBeObtained.code,
                cosmos_alerts.TendermintRPCDataCouldNotBeObtainedAlert,
                cosmos_alerts.TendermintRPCDataObtainedAlert,
                data_for_alerting, parent_id, node_id, node_name, time,
                MetricCode.TendermintRPCDataNotObtained.value, err_message,
                "The monitor for {} successfully retrieved Tendermint-RPC data "
                "again.".format(node_name), err_code
            )

    def _process_downtime(self, trans_data: Dict, data_for_alerting: List):
        # We will parse some meta_data first, note we will assume that the
        # transformed data has the correct structure, as the data was validated
        # inside the data transformer.
        enabled_source = [
            source for source in VALID_COSMOS_NODE_SOURCES if trans_data[source]
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
            parent_id, CosmosNodeAlertsConfig)
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
                for source in VALID_COSMOS_NODE_SOURCES if trans_data[source]
            ])

            # Compute which sources are down
            down_sources = [
                source
                for source in VALID_COSMOS_NODE_SOURCES
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
                        cosmos_alerts.NodeWentDownAtAlert,
                        cosmos_alerts.NodeStillDownAlert,
                        cosmos_alerts.NodeBackUpAgainAlert, data_for_alerting,
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
                        for source in VALID_COSMOS_NODE_SOURCES
                        if trans_data[source] and source not in down_sources
                    ])

                    # Classify downtime so that a node back up again alert is
                    # raised if needbe.
                    self.alerting_factory.classify_downtime_alert(
                        None, downtime_configs,
                        cosmos_alerts.NodeWentDownAtAlert,
                        cosmos_alerts.NodeStillDownAlert,
                        cosmos_alerts.NodeBackUpAgainAlert, data_for_alerting,
                        parent_id, origin_id, MetricCode.NodeIsDown.value,
                        origin_name, monitoring_timestamp
                    )

            # Check for individual sources downtime.

            prometheus_down_configs = (
                configs.cannot_access_prometheus_validator if is_validator
                else configs.cannot_access_prometheus_node
            )
            if (str_to_bool(prometheus_down_configs['enabled'])
                    and trans_data['prometheus']
                    and not all_sources_down):
                current_went_down = (
                    trans_data['prometheus']['error']['data']['went_down_at'][
                        'current']
                    if 'prometheus' in down_sources else None
                )
                response_index_key = (
                    'result' if 'result' in trans_data['prometheus']
                    else 'error'
                )
                monitoring_timestamp = (
                    trans_data['prometheus']['result']['meta_data'][
                        'last_monitored']
                    if response_index_key == 'result'
                    else trans_data['prometheus']['error']['meta_data']['time']
                )
                self.alerting_factory.classify_downtime_alert(
                    current_went_down, prometheus_down_configs,
                    cosmos_alerts.PrometheusSourceIsDownAlert,
                    cosmos_alerts.PrometheusSourceStillDownAlert,
                    cosmos_alerts.PrometheusSourceBackUpAgainAlert,
                    data_for_alerting, parent_id, origin_id,
                    MetricCode.PrometheusSourceIsDown.value, origin_name,
                    monitoring_timestamp
                )

            cosmos_rest_down_configs = (
                configs.cannot_access_cosmos_rest_validator if is_validator
                else configs.cannot_access_cosmos_rest_node
            )
            if (str_to_bool(cosmos_rest_down_configs['enabled'])
                    and trans_data['cosmos_rest']
                    and not all_sources_down):
                current_went_down = (
                    trans_data['cosmos_rest']['error']['data']['went_down_at'][
                        'current']
                    if 'cosmos_rest' in down_sources else None
                )
                response_index_key = (
                    'result' if 'result' in trans_data['cosmos_rest']
                    else 'error'
                )
                monitoring_timestamp = (
                    trans_data['cosmos_rest']['result']['meta_data'][
                        'last_monitored']
                    if response_index_key == 'result'
                    else trans_data['cosmos_rest']['error']['meta_data']['time']
                )
                self.alerting_factory.classify_downtime_alert(
                    current_went_down, cosmos_rest_down_configs,
                    cosmos_alerts.CosmosRestSourceIsDownAlert,
                    cosmos_alerts.CosmosRestSourceStillDownAlert,
                    cosmos_alerts.CosmosRestSourceBackUpAgainAlert,
                    data_for_alerting, parent_id, origin_id,
                    MetricCode.CosmosRestSourceIsDown.value, origin_name,
                    monitoring_timestamp
                )

            tendermint_rpc_down_configs = (
                configs.cannot_access_tendermint_rpc_validator if is_validator
                else configs.cannot_access_tendermint_rpc_node
            )
            if (str_to_bool(tendermint_rpc_down_configs['enabled'])
                    and trans_data['tendermint_rpc']
                    and not all_sources_down):
                current_went_down = (
                    trans_data['tendermint_rpc']['error']['data'][
                        'went_down_at']['current']
                    if 'tendermint_rpc' in down_sources else None
                )
                response_index_key = (
                    'result' if 'result' in trans_data['tendermint_rpc']
                    else 'error'
                )
                monitoring_timestamp = (
                    trans_data['tendermint_rpc']['result']['meta_data'][
                        'last_monitored']
                    if response_index_key == 'result'
                    else trans_data['tendermint_rpc']['error']['meta_data'][
                        'time']
                )
                self.alerting_factory.classify_downtime_alert(
                    current_went_down, tendermint_rpc_down_configs,
                    cosmos_alerts.TendermintRPCSourceIsDownAlert,
                    cosmos_alerts.TendermintRPCSourceStillDownAlert,
                    cosmos_alerts.TendermintRPCSourceBackUpAgainAlert,
                    data_for_alerting, parent_id, origin_id,
                    MetricCode.TendermintRPCSourceIsDown.value, origin_name,
                    monitoring_timestamp
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
                'prometheus': {
                    'result': self._process_prometheus_result,
                    'error': self._process_prometheus_error,
                },
                'cosmos_rest': {
                    'result': self._process_cosmos_rest_result,
                    'error': self._process_cosmos_rest_error,
                },
                'tendermint_rpc': {
                    'result': self._process_tendermint_rpc_result,
                    'error': self._process_tendermint_rpc_error,
                }
            }
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
                    chain, CosmosNodeAlertsConfig)
                self.alerting_factory.remove_chain_alerting_state(parent_id)
            else:
                # We must reset the state since a configuration is to be
                # removed. Note that first we need to compute the parent_id, as
                # the parent_id is obtained from the configs to be removed from
                # the factory. If the parent_id cannot be found, it means that
                # no storing took place, therefore in that case do nothing.
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, CosmosNodeAlertsConfig)
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
                'routing_key': COSMOS_NODE_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
