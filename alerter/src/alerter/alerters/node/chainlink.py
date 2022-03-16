import copy
import json
import logging
import sys
from datetime import datetime
from typing import List, Dict, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel

import src.alerter.alerts.node.chainlink as cl_alerts
from src.alerter.alert_severities import Severity
from src.alerter.alerters.alerter import Alerter
from src.alerter.factory.chainlink_node_alerting_factory import (
    ChainlinkNodeAlertingFactory)
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode as MetricCode
from src.configs.alerts.node.chainlink import ChainlinkNodeAlertsConfig
from src.configs.factory.node.chainlink_alerts import (
    ChainlinkNodeAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.data import VALID_CHAINLINK_SOURCES
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    CL_NODE_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE,
    CONFIG_EXCHANGE, CL_NODE_ALERT_ROUTING_KEY, CL_ALERTS_CONFIGS_ROUTING_KEY)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.types import str_to_bool


class ChainlinkNodeAlerter(Alerter):
    """
    We will have one alerter for all chainlink nodes. The chainlink alerter
    doesn't have to restart if the configurations change, as it will be
    listening for both data and configs in the same queue.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            rabbitmq: RabbitMQApi,
            cl_alerts_configs_factory: ChainlinkNodeAlertsConfigsFactory,
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = cl_alerts_configs_factory
        self._alerting_factory = ChainlinkNodeAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> ChainlinkNodeAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_factory(self) -> ChainlinkNodeAlertingFactory:
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
                         CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         ALERT_EXCHANGE, CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
            exchange=ALERT_EXCHANGE,
            routing_key=CL_NODE_TRANSFORMED_DATA_ROUTING_KEY)

        # Set configs consuming configuration
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, CL_ALERTS_CONFIGS_ROUTING_KEY)
        self.rabbitmq.queue_bind(CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, CL_ALERTS_CONFIGS_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(
            queue=CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
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
        This function calls the appropriate processing function, depending on
        whether we received configs or transformed data. If none of this is
        received the message is ignored.
        :param ch: The rabbit channel
        :param method: Pika method
        :param properties: Pika properties
        :param body: The message
        :return:
        """
        if method.routing_key == CL_NODE_TRANSFORMED_DATA_ROUTING_KEY:
            self._process_transformed_data(ch, method, properties, body)
        elif 'alerts_config' in method.routing_key:
            self._process_configs(ch, method, properties, body)
        else:
            self.logger.debug("Received unexpected data %s with routing key %s",
                              body, method.routing_key)
            self.rabbitmq.basic_ack(method.delivery_tag, False)

    @staticmethod
    def _prometheus_is_down_condition_function(index_key: Optional[str],
                                               code: Optional[int]) -> bool:
        return (index_key == 'error' and code == 5015)

    def _process_prometheus_result(self, prom_data: Dict,
                                   data_for_alerting: List) -> None:
        meta_data = prom_data['meta_data']
        data = prom_data['data']

        # We must make sure that the alerts_config has been received for the
        # chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            meta_data['node_parent_id'], ChainlinkNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                meta_data['node_parent_id'], meta_data['node_id'], configs)

            # Check if some errors have been resolved
            self.alerting_factory.classify_error_alert(
                5009,
                cl_alerts.InvalidUrlAlert, cl_alerts.ValidUrlAlert,
                data_for_alerting, meta_data['node_parent_id'],
                meta_data['node_id'], meta_data['node_name'],
                meta_data['last_monitored'], MetricCode.InvalidUrl.value,
                "", "Prometheus url is now valid!. Last source used {}.".format(
                    meta_data['last_source_used']['current']), None
            )
            self.alerting_factory.classify_error_alert(
                5003,
                cl_alerts.MetricNotFoundErrorAlert,
                cl_alerts.MetricFoundAlert, data_for_alerting,
                meta_data['node_parent_id'], meta_data['node_id'],
                meta_data['node_name'], meta_data['last_monitored'],
                MetricCode.MetricNotFound.value, "",
                "All metrics found!. Last source used {}.".format(
                    meta_data['last_source_used']['current']), None
            )

            # Check if the alert rules are satisfied for the metrics
            if str_to_bool(configs.head_tracker_current_head['enabled']):
                current = data['current_height']['current']
                previous = data['current_height']['previous']
                sub_config = configs.head_tracker_current_head
                if current is not None and previous is not None:
                    self.alerting_factory.classify_no_change_in_alert(
                        current, previous, sub_config,
                        cl_alerts.NoChangeInHeightAlert,
                        cl_alerts.BlockHeightUpdatedAlert, data_for_alerting,
                        meta_data['node_parent_id'], meta_data['node_id'],
                        MetricCode.NoChangeInHeight.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(
                    configs.head_tracker_heads_received_total['enabled']):
                current = data['total_block_headers_received']['current']
                previous = data['total_block_headers_received']['previous']
                sub_config = configs.head_tracker_heads_received_total
                if current is not None and previous is not None:
                    self.alerting_factory.classify_no_change_in_alert(
                        current, previous, sub_config,
                        cl_alerts.NoChangeInTotalHeadersReceivedAlert,
                        cl_alerts.ReceivedANewHeaderAlert, data_for_alerting,
                        meta_data['node_parent_id'], meta_data['node_id'],
                        MetricCode.NoChangeInTotalHeadersReceived.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.max_unconfirmed_blocks['enabled']):
                current = data['max_pending_tx_delay']['current']
                sub_config = configs.max_unconfirmed_blocks
                if current is not None:
                    self.alerting_factory. \
                        classify_thresholded_time_window_alert(
                        current, sub_config,
                        cl_alerts.
                            MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
                        cl_alerts.
                            MaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        MetricCode.MaxUnconfirmedBlocksThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.process_start_time_seconds['enabled']):
                current = data['process_start_time_seconds']['current']
                previous = data['process_start_time_seconds']['previous']
                new_source = meta_data['last_source_used']['current']
                sub_config = configs.process_start_time_seconds
                if current is not None and previous is not None:
                    self.alerting_factory.classify_conditional_alert(
                        cl_alerts.ChangeInSourceNodeAlert,
                        self._not_equal_condition_function, [
                            current, previous],
                        [
                            meta_data['node_name'], new_source,
                            sub_config['severity'], meta_data['last_monitored'],
                            meta_data['node_parent_id'], meta_data['node_id']
                        ], data_for_alerting,
                    )
            if str_to_bool(
                    configs.tx_manager_gas_bump_exceeds_limit_total['enabled']):
                current = data['total_gas_bumps_exceeds_limit']['current']
                previous = data['total_gas_bumps_exceeds_limit']['previous']
                sub_config = configs.tx_manager_gas_bump_exceeds_limit_total
                if current is not None and previous is not None:
                    self.alerting_factory.classify_conditional_alert(
                        cl_alerts.GasBumpIncreasedOverNodeGasPriceLimitAlert,
                        self._greater_than_condition_function, [
                            current, previous], [
                            meta_data['node_name'], sub_config['severity'],
                            meta_data['last_monitored'],
                            meta_data['node_parent_id'], meta_data['node_id']
                        ], data_for_alerting
                    )
            if str_to_bool(configs.unconfirmed_transactions['enabled']):
                current = data['no_of_unconfirmed_txs']['current']
                sub_config = configs.unconfirmed_transactions
                if current is not None:
                    self.alerting_factory. \
                        classify_thresholded_time_window_alert(
                        current, sub_config,
                        cl_alerts.
                            NoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
                        cl_alerts.
                            NoOfUnconfirmedTxsDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        MetricCode.NoOfUnconfirmedTxsThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.run_status_update_total['enabled']):
                current = data['total_errored_job_runs']['current']
                previous = data['total_errored_job_runs']['previous']
                sub_config = configs.run_status_update_total
                if current is not None and previous is not None:
                    self.alerting_factory \
                        .classify_thresholded_in_time_period_alert(
                        current, previous, sub_config,
                        cl_alerts.
                            TotalErroredJobRunsIncreasedAboveThresholdAlert,
                        cl_alerts.
                            TotalErroredJobRunsDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        MetricCode.TotalErroredJobRunsThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.eth_balance_amount['enabled']):
                current = data['eth_balance_info']['current']
                sub_config = configs.eth_balance_amount
                if current != {}:
                    self.alerting_factory.classify_thresholded_alert_reverse(
                        current['balance'], sub_config,
                        cl_alerts.EthBalanceIncreasedAboveThresholdAlert,
                        cl_alerts.EthBalanceDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        MetricCode.EthBalanceThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.eth_balance_amount_increase['enabled']):
                current = data['eth_balance_info']['current']
                previous = data['eth_balance_info']['previous']
                sub_config = configs.eth_balance_amount_increase
                if current != {} and previous != {}:
                    increase = current['balance'] - previous['balance']
                    self.alerting_factory.classify_conditional_alert(
                        cl_alerts.EthBalanceToppedUpAlert,
                        self._greater_than_condition_function,
                        [current['balance'], previous['balance']], [
                            meta_data['node_name'], current['balance'],
                            increase, sub_config['severity'],
                            meta_data['last_monitored'],
                            meta_data['node_parent_id'], meta_data['node_id']
                        ], data_for_alerting
                    )

    def _process_prometheus_error(self, prom_data: Dict,
                                  data_for_alerting: List) -> None:
        meta_data = prom_data['meta_data']

        # We must make sure that the alerts_config has been received for the
        # chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            meta_data['node_parent_id'], ChainlinkNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                meta_data['node_parent_id'], meta_data['node_id'], configs)

            # Check if the source has been changed, if yes alert accordingly
            if str_to_bool(configs.process_start_time_seconds['enabled']):
                # Unlike for the process_prometheus_result fn, we need to use
                # last source used instead of process_start_time_seconds because
                # the metrics won't be sent
                current = meta_data['last_source_used']['current']
                previous = meta_data['last_source_used']['previous']
                sub_config = configs.process_start_time_seconds
                if current is not None and previous is not None:
                    self.alerting_factory.classify_conditional_alert(
                        cl_alerts.ChangeInSourceNodeAlert,
                        self._not_equal_condition_function, [
                            current, previous],
                        [
                            meta_data['node_name'], current,
                            sub_config['severity'], meta_data['time'],
                            meta_data['node_parent_id'], meta_data['node_id']
                        ], data_for_alerting,
                    )

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_error_alert(
                5009,
                cl_alerts.InvalidUrlAlert, cl_alerts.ValidUrlAlert,
                data_for_alerting, meta_data['node_parent_id'],
                meta_data['node_id'], meta_data['node_name'], meta_data['time'],
                MetricCode.InvalidUrl.value, prom_data['message'],
                "Prometheus url is now valid!. Last source used {}.".format(
                    meta_data['last_source_used']['current']),
                prom_data['code']
            )
            self.alerting_factory.classify_error_alert(
                5003,
                cl_alerts.MetricNotFoundErrorAlert,
                cl_alerts.MetricFoundAlert, data_for_alerting,
                meta_data['node_parent_id'], meta_data['node_id'],
                meta_data['node_name'], meta_data['time'],
                MetricCode.MetricNotFound.value, prom_data['message'],
                "All metrics found!. Last source used {}.".format(
                    meta_data['last_source_used']['current']),
                prom_data['code']
            )

    def _process_downtime(self, trans_data: Dict, data_for_alerting: List):
        # We will parse some meta_data first, note we will assume that the
        # transformed data has correct structure and valid data.
        parent_id = ""
        origin_id = ""
        origin_name = ""
        for source in VALID_CHAINLINK_SOURCES:
            if trans_data[source]:
                response_index_key = 'result' if 'result' in trans_data[
                    source] else 'error'
                parent_id = trans_data[source][response_index_key]['meta_data'][
                    'node_parent_id']
                origin_id = trans_data[source][response_index_key]['meta_data'][
                    'node_id']
                origin_name = trans_data[source][response_index_key][
                    'meta_data']['node_name']
                break

        # We must make sure that the alerts_config has been received for the
        # chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, ChainlinkNodeAlertsConfig)
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(parent_id, origin_id,
                                                        configs)

            # Check if downtime is enabled.
            if str_to_bool(configs.node_is_down['enabled']):
                # Check if all sources are down, if yes classify the node as
                # down.
                all_sources_down = True
                for source in VALID_CHAINLINK_SOURCES:
                    if trans_data[source]:
                        response_index_key = 'result' if 'result' in trans_data[
                            source] else 'error'
                        data = trans_data[source][response_index_key]
                        if (response_index_key != 'error' or data['code'] !=
                                5015):
                            all_sources_down = False
                            break

                if all_sources_down:
                    # Choose the smallest timing variables for downtime
                    current_went_down = sys.float_info.max
                    monitoring_timestamp = sys.float_info.max
                    for source in VALID_CHAINLINK_SOURCES:
                        if trans_data[source]:
                            data = trans_data[source]['error']
                            new_went_down = data['data']['went_down_at'][
                                'current']
                            new_monitoring_timestamp = data['meta_data']['time']
                            current_went_down = current_went_down \
                                if current_went_down <= new_went_down \
                                else new_went_down
                            monitoring_timestamp = monitoring_timestamp \
                                if monitoring_timestamp <= \
                                   new_monitoring_timestamp \
                                else new_monitoring_timestamp

                    self.alerting_factory.classify_downtime_alert(
                        current_went_down, configs.node_is_down,
                        cl_alerts.NodeWentDownAtAlert,
                        cl_alerts.NodeStillDownAlert,
                        cl_alerts.NodeBackUpAgainAlert, data_for_alerting,
                        parent_id, origin_id, MetricCode.NodeIsDown.value,
                        origin_name, monitoring_timestamp
                    )
                else:
                    # Choose the smallest timing variables for downtime
                    monitoring_timestamp = sys.float_info.max
                    for source in VALID_CHAINLINK_SOURCES:
                        if trans_data[source]:
                            response_index_key = \
                                'result' if 'result' in trans_data[
                                    source] else 'error'
                            data = trans_data[source][response_index_key]
                            new_monitoring_timestamp = data['meta_data'][
                                'last_monitored'] \
                                if response_index_key == 'result' \
                                else data['meta_data']['time']
                            monitoring_timestamp = monitoring_timestamp \
                                if monitoring_timestamp <= \
                                   new_monitoring_timestamp \
                                else new_monitoring_timestamp

                    # Classify downtime so that a node back up again alert is
                    # raised.
                    self.alerting_factory.classify_downtime_alert(
                        None, configs.node_is_down,
                        cl_alerts.NodeWentDownAtAlert,
                        cl_alerts.NodeStillDownAlert,
                        cl_alerts.NodeBackUpAgainAlert, data_for_alerting,
                        parent_id, origin_id, MetricCode.NodeIsDown.value,
                        origin_name, monitoring_timestamp
                    )

                    # Classify to check if prometheus is down or back up
                    if trans_data['prometheus']:
                        response_index_key = 'result' if 'result' in trans_data[
                            'prometheus'] else 'error'
                        error_code = None if response_index_key == 'result' \
                            else trans_data['prometheus']['error']['code']
                        monitoring_timestamp = trans_data['prometheus'][
                            'result']['meta_data']['last_monitored'] \
                            if response_index_key == 'result' \
                            else trans_data['prometheus']['error']['meta_data'][
                            'time']
                    else:
                        # This condition covers the case for when prometheus
                        # is disabled and we had a prometheus down alert before
                        # hand.
                        response_index_key = None
                        error_code = None

                    self.alerting_factory.classify_source_downtime_alert(
                        cl_alerts.PrometheusSourceIsDownAlert,
                        self._prometheus_is_down_condition_function,
                        [response_index_key, error_code], [
                            origin_name, Severity.WARNING.value,
                            monitoring_timestamp, parent_id, origin_id
                        ], data_for_alerting, parent_id, origin_id,
                        MetricCode.PrometheusSourceIsDown.value,
                        cl_alerts.PrometheusSourceBackUpAgainAlert, [
                            origin_name, Severity.INFO.value,
                            monitoring_timestamp, parent_id, origin_id
                        ]
                    )

    def _process_transformed_data(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
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
                }
            }
            transformed_data_processing_helper(
                self.alerter_name, configuration, data_received,
                data_for_alerting)
            self._process_downtime(data_received, data_for_alerting)
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

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.debug("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        try:
            # Checking if the configuration is empty. If it is empty, remove the
            # stored config (if it exists), and if it not add it to the list of
            # configurations.
            if bool(sent_configs):
                self.alerts_configs_factory.add_new_config(chain, sent_configs)

                # We must reset the state since some thresholds might have
                # changed. A node's state will be recreated in the next
                # monitoring round automatically. Note we are sure that a
                # parent_id is to be returned, as we have just added the config
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, ChainlinkNodeAlertsConfig)
                self.alerting_factory.remove_chain_alerting_state(parent_id)
            else:
                # We must reset the state since a configuration is to be
                # removed. Note that first we need to compute the parent_id, as
                # the parent_id is obtained from the configs to be removed from
                # the factory. If the parent_id cannot be found, it means that
                # no storing took place, therefore in that case do nothing.
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, ChainlinkNodeAlertsConfig)
                if parent_id:
                    self.alerting_factory.remove_chain_alerting_state(
                        parent_id)
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
                'routing_key': CL_NODE_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
