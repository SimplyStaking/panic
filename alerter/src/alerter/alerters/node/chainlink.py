import copy
import json
import logging
from typing import List, Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerters.alerter import Alerter
from src.alerter.alerts.node.chainlink import *
from src.alerter.factory.chainlink_node_alerting_factory import \
    ChainlinkNodeAlertingFactory
from src.alerter.grouped_alerts_metric_code.node.chainlink_node_metric_code \
    import GroupedChainlinkNodeAlertsMetricCode
from src.configs.factory.chainlink_alerts_configs_factory import (
    ChainlinkAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CL_NODE_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    CL_NODE_TRANSFORMED_DATA_ROUTING_KEY, HEALTH_CHECK_EXCHANGE,
    CONFIG_EXCHANGE, CL_NODE_ALERT_ROUTING_KEY, CL_ALERTS_CONFIGS_ROUTING_KEY)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.types import str_to_bool


class ChainlinkNodeAlerter(Alerter):
    """
    We will have one chainlink node alerter for all chainlink nodes. Also the
    chainlink alerter doesn't have to restart if the configurations change, as
    it will be listening for both data and configs in the same queue. Ideally,
    this is to be done for every other alerter when refactoring.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            rabbitmq: RabbitMQApi,
            cl_alerts_configs_factory: ChainlinkAlertsConfigsFactory,
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = cl_alerts_configs_factory
        self._alerting_factory = ChainlinkNodeAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> ChainlinkAlertsConfigsFactory:
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
            self.rabbitmq.basic_ack(method.delivery_tag, False)

    # TODO: Create state for node must be done when trans data is received, just
    #     : in case some thresholds change. The process_configs will reset
    #     : related state.

    # TODO: When processing alerts check if config is available first, if not
    #     : skip alerts.

    # TODO: Don't forget to make the class compatible with multiple sources
    #     : immediately

    # TODO: If warning_set or critical_sent for downtime, don't raise prom down

    # TODO: Don't forget that some metrics can be None.

    def _process_prometheus_result(self, prom_data: Dict,
                                   data_for_alerting: List) -> None:
        meta_data = prom_data['result']['meta_data']
        data = prom_data['result']['data']

        # We must make sure that the alerts_config has been received for the
        # chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            meta_data['node_parent_id'])
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                meta_data['node_parent_id'], meta_data['node_id'], configs)
            if str_to_bool(configs.head_tracker_current_head['enabled']):
                current = data['current_height']['current']
                previous = data['current_height']['previous']
                sub_config = configs.head_tracker_current_head
                if current is not None:
                    self.alerting_factory.classify_no_change_in_alert(
                        current, previous, sub_config, NoChangeInHeightAlert,
                        BlockHeightUpdatedAlert, data_for_alerting,
                        meta_data['node_parent_id'], meta_data['node_id'],
                        GroupedChainlinkNodeAlertsMetricCode.NoChangeInHeight
                            .value, meta_data['node_name'],
                        meta_data['last_monitored']
                    )
            if str_to_bool(configs.head_tracker_heads_in_queue['enabled']):
                current = data['eth_blocks_in_queue']['current']
                sub_config = configs.head_tracker_heads_in_queue
                if current is not None:
                    self.alerting_factory. \
                        classify_thresholded_time_window_alert(
                        current, sub_config,
                        HeadsInQueueIncreasedAboveThresholdAlert,
                        HeadsInQueueDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        GroupedChainlinkNodeAlertsMetricCode.
                            HeadsInQueueThreshold.value, meta_data['node_name'],
                        meta_data['last_monitored']
                    )
            if str_to_bool(
                    configs.head_tracker_heads_received_total['enabled']):
                current = data['total_block_headers_received']['current']
                previous = data['total_block_headers_received']['previous']
                sub_config = configs.head_tracker_heads_received_total
                if current is not None:
                    self.alerting_factory.classify_no_change_in_alert(
                        current, previous, sub_config,
                        NoChangeInTotalHeadersReceivedAlert,
                        ReceivedANewHeaderAlert, data_for_alerting,
                        meta_data['node_parent_id'], meta_data['node_id'],
                        GroupedChainlinkNodeAlertsMetricCode.
                            NoChangeInTotalHeadersReceived.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(
                    configs.head_tracker_num_heads_dropped_total['enabled']):
                current = data['total_block_headers_dropped']['current']
                previous = data['total_block_headers_dropped']['previous']
                sub_config = configs.head_tracker_num_heads_dropped_total
                if current is not None:
                    self.alerting_factory \
                        .classify_thresholded_in_time_period_alert(
                        current, previous, sub_config,
                        DroppedBlockHeadersIncreasedAboveThresholdAlert,
                        DroppedBlockHeadersDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        GroupedChainlinkNodeAlertsMetricCode.
                            DroppedBlockHeadersThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.max_unconfirmed_blocks['enabled']):
                current = data['max_pending_tx_delay']['current']
                sub_config = configs.max_unconfirmed_blocks
                if current is not None:
                    self.alerting_factory. \
                        classify_thresholded_time_window_alert(
                        current, sub_config,
                        MaxUnconfirmedBlocksIncreasedAboveThresholdAlert,
                        MaxUnconfirmedBlocksDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        GroupedChainlinkNodeAlertsMetricCode.
                            MaxUnconfirmedBlocksThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.process_start_time_seconds['enabled']):
                current = data['process_start_time_seconds']['current']
                previous = data['process_start_time_seconds']['previous']
                new_source = meta_data['last_source_used']['current']
                sub_config = configs.process_start_time_seconds
                if current is not None:
                    def condition_function(current_start_time: float,
                                           previous_start_time: float) -> bool:
                        return current_start_time != previous_start_time

                    self.alerting_factory.classify_conditional_alert(
                        ChangeInSourceNodeAlert, condition_function,
                        [current, previous], [
                            meta_data['node_name'], new_source,
                            sub_config['severity'], meta_data['last_monitored'],
                            meta_data['node_parent_id'], meta_data['node_id']
                        ], data_for_alerting,
                    )
            if str_to_bool(
                    configs.tx_manager_gas_bump_exceeds_limit_total['enabled']):
                current = data['total_gas_bumps']['current']
                previous = data['total_gas_bumps']['previous']
                sub_config = configs.tx_manager_gas_bump_exceeds_limit_total
                if current is not None:
                    def condition_function(current_gas_bumps: float,
                                           previous_gas_bumps: float) -> bool:
                        return current_gas_bumps > previous_gas_bumps

                    self.alerting_factory.classify_conditional_alert(
                        GasBumpIncreasedOverNodeGasPriceLimitAlert,
                        condition_function, [current, previous], [
                            meta_data['node_name'], sub_config['severity'],
                            meta_data['last_monitored'],
                            meta_data['node_parent_id'], meta_data['node_id']
                        ], data_for_alerting
                    )
            if str_to_bool(configs.unconfirmed_transactions['enabled']):
                current = data['no_of_unconfirmed_txs']['current']
                sub_config = configs.unconfirmed_transactions
                if current is not None:
                    self.alerting_factory.\
                        classify_thresholded_time_window_alert(
                        current, sub_config,
                        NoOfUnconfirmedTxsIncreasedAboveThresholdAlert,
                        NoOfUnconfirmedTxsDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        GroupedChainlinkNodeAlertsMetricCode.
                            NoOfUnconfirmedTxsThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.run_status_update_total['enabled']):
                current = data['total_errored_job_runs']['current']
                previous = data['total_errored_job_runs']['previous']
                sub_config = configs.run_status_update_total
                if current is not None:
                    self.alerting_factory \
                        .classify_thresholded_in_time_period_alert(
                        current, previous, sub_config,
                        TotalErroredJobRunsIncreasedAboveThresholdAlert,
                        TotalErroredJobRunsDecreasedBelowThresholdAlert,
                        data_for_alerting, meta_data['node_parent_id'],
                        meta_data['node_id'],
                        GroupedChainlinkNodeAlertsMetricCode.
                            TotalErroredJobRunsThreshold.value,
                        meta_data['node_name'], meta_data['last_monitored']
                    )
            if str_to_bool(configs.eth_balance_amount['enabled']):
                # TODO: Eth balance threshold and top up alerts must cater for
                #     : multiple addresses. Or we might need to make it monitor
                #     : 1 ether address only
                current = data['']['current']

    def _process_prometheus_error(self, prom_data: Dict,
                                  data_for_alerting: List) -> None:
        meta_data = prom_data['error']['meta_data']
        # TODO: Change is source can also happen here

        # We must make sure that the alerts_config has been received for the
        # chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            meta_data['parent_id'])
        if chain_name is not None:
            pass

    def _process_downtime(self, trans_data: Dict):
        # TODO: Check for alerts configs by getting one of the parent_ids.
        #     : Assuming that all parent-ids are equal. If you want add a
        #     : private function for this. We can assume here that the data is
        #     : well formed, as otherwise the previous 2 functions would have
        #     : errorred.
        # TODO: Downtime must be compared holistically on all the data because
        #     : we need visibility in entire data. The other processing
        #     : functions will process for individual alerts.
        pass

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
            self._process_downtime(data_received)
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

        self.logger.info("Received configs %s", sent_configs)

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
                parent_id = self.alerts_configs_factory.get_parent_id(chain)
                self.alerting_factory.remove_chain_alerting_state(parent_id)
            else:
                # We must reset the state since a configuration is to be
                # removed. Note that first we need to compute the parent_id, as
                # the parent_id is obtained from the configs to be removed from
                # the factory. If the parent_id cannot be found, it means that
                # no storing took place, therefore in that case do nothing.
                parent_id = self.alerts_configs_factory.get_parent_id(chain)
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
                'routing_key': CL_NODE_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
