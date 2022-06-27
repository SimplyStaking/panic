import copy
import json
import logging
from datetime import datetime
from typing import Dict, List

import pika
from pika.adapters.blocking_connection import BlockingChannel

import src.alerter.alerts.network.substrate as substrate_alerts
from src.alerter.alert_severities import Severity
from src.alerter.alerters.alerter import Alerter
from src.alerter.factory.substrate_network_alerting_factory import (
    SubstrateNetworkAlertingFactory)
from src.alerter.grouped_alerts_metric_code.network \
    .substrate_network_metric_code \
    import GroupedSubstrateNetworkAlertsMetricCode as MetricCode
from src.configs.alerts.network.substrate import SubstrateNetworkAlertsConfig
from src.configs.factory.alerts.substrate_alerts import (
    SubstrateNetworkAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY,
    SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY,
    SUBSTRATE_NETWORK_ALERT_ROUTING_KEY)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import (
    NoSyncedDataSourceWasAccessibleException,
    SubstrateNetworkDataCouldNotBeObtained, MessageWasNotDeliveredException,
    SubstrateApiIsNotReachableException)
from src.utils.types import str_to_bool


class SubstrateNetworkAlerter(Alerter):
    """
    We will have one alerter for all substrate networks. The substrate alerter
    doesn't have to restart if the configurations change, as it will be
    listening for both data and configs in the same queue.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            rabbitmq: RabbitMQApi,
            substrate_alerts_configs_factory:
            SubstrateNetworkAlertsConfigsFactory,
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = substrate_alerts_configs_factory
        self._alerting_factory = SubstrateNetworkAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> SubstrateNetworkAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_factory(self) -> SubstrateNetworkAlertingFactory:
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
                         SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, passive=False,
            durable=True, exclusive=False, auto_delete=False)
        self.logger.info(
            "Binding queue '%s' to exchange '%s' with routing key '%s'",
            SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, ALERT_EXCHANGE,
            SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
            exchange=ALERT_EXCHANGE,
            routing_key=SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)

        # Set configs consuming configuration
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'",
                         SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
            SUBSTRATE_ALERTS_CONFIGS_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(
            queue=SUBSTRATE_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
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
        if method.routing_key == SUBSTRATE_NETWORK_TRANSFORMED_DATA_ROUTING_KEY:
            self._process_transformed_data(method, body)
        elif 'alerts_config' in method.routing_key:
            self._process_configs(method, body)
        else:
            self.logger.debug("Received unexpected data %s with routing key %s",
                              body, method.routing_key)
            self.rabbitmq.basic_ack(method.delivery_tag, False)

    @staticmethod
    def _alert_new_referendum(
            previous_referendums: List, new_referendum: bool) -> bool:
        """
        We will alert on a new referendum if this is not the first monitoring
        round (i.e. previous != []), and the referendum is new.
        :param previous_referendums: The list of previous referendums
        :param new_referendum: Whether the referendum is new or not
        :return: True if we should alert on the referendum
               : False otherwise
        """
        return previous_referendums != [] and new_referendum

    @staticmethod
    def _alert_referendum_conclusion(
            was_ongoing: bool, is_ongoing: bool) -> bool:
        """
        We will alert on a concluded referendum if it was ongoing, and now it
        is no longer ongoing.
        :param was_ongoing: Whether the referendum was previously ongoing
        :param is_ongoing: Whether the referendum is currently ongoing
        :return: True if we should alert on the referendum
               : False otherwise
        """
        return was_ongoing and not is_ongoing

    def _process_websocket_result(
            self, websocket_data: Dict, data_for_alerting: List) -> None:
        meta_data = websocket_data['meta_data']
        parent_id = meta_data['parent_id']
        sub_chain_name = meta_data['chain_name']
        last_monitored = meta_data['last_monitored']
        data = websocket_data['data']

        # Assert that the alerts_config has been received for the chain.
        full_chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, SubstrateNetworkAlertsConfig)
        if full_chain_name is not None:
            configs = self.alerts_configs_factory.configs[full_chain_name]
            self.alerting_factory.create_alerting_state(parent_id)

            # Check if some errors have been resolved

            self.alerting_factory.classify_error_alert(
                SubstrateApiIsNotReachableException.code,
                substrate_alerts.SubstrateApiIsNotReachableAlert,
                substrate_alerts.SubstrateApiIsReachableAlert,
                data_for_alerting, parent_id, parent_id, sub_chain_name,
                last_monitored,
                MetricCode.SubstrateApiNotReachable.value, "",
                "The Network Monitor for {} is now reaching the Substrate "
                "API.".format(sub_chain_name), None
            )
            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                substrate_alerts.
                    ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
                substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
                data_for_alerting, parent_id, parent_id, sub_chain_name,
                last_monitored,
                MetricCode.NoSyncedSubstrateWebSocketDataSource.value, "",
                "The Network Monitor for {} found a websocket synced data "
                "source again.".format(sub_chain_name), None
            )
            self.alerting_factory.classify_error_alert(
                SubstrateNetworkDataCouldNotBeObtained.code,
                substrate_alerts.SubstrateNetworkDataCouldNotBeObtainedAlert,
                substrate_alerts.SubstrateNetworkDataObtainedAlert,
                data_for_alerting, parent_id, parent_id, sub_chain_name,
                last_monitored,
                MetricCode.SubstrateNetworkDataNotObtained.value, "",
                "The Network Monitor for {} successfully retrieved network "
                "data again.".format(sub_chain_name), None
            )

            # Check if the alert rules are satisfied for the metrics
            grandpa_is_stalled_configs = configs.grandpa_is_stalled
            classification_fn = (
                self.alerting_factory
                    .classify_solvable_conditional_alert_no_repetition
            )
            if str_to_bool(grandpa_is_stalled_configs['enabled']):
                current = data['grandpa_stalled']['current']
                if current is not None:
                    classification_fn(
                        parent_id, parent_id, MetricCode.GrandpaIsStalled.value,
                        substrate_alerts.GrandpaIsStalledAlert,
                        self._is_true_condition_function, [current],
                        [sub_chain_name, grandpa_is_stalled_configs['severity'],
                         last_monitored, parent_id, parent_id],
                        data_for_alerting,
                        substrate_alerts.GrandpaIsNoLongerStalledAlert,
                        [sub_chain_name, Severity.INFO.value, last_monitored,
                         parent_id, parent_id]
                    )

            current_prop_count: int = (
                data['public_prop_count']['current'] if
                data['public_prop_count']['current'] else 0
            )
            previous_prop_count: int = (
                data['public_prop_count']['previous'] if
                data['public_prop_count']['previous'] else 0
            )
            current_ref_count: int = (
                data['referendum_count']['current'] if
                data['referendum_count']['current'] else 0
            )
            previous_ref_count: int = (
                data['referendum_count']['previous'] if
                data['referendum_count']['previous'] else 0
            )

            # Perform some transformations to the proposals list for easier
            # logic later on. We will ignore proposals with index None as this
            # means that the Data Transformer could not parse the proposal
            # correctly
            current_proposals = data['active_proposals']['current']
            previous_proposals = data['active_proposals']['previous']
            current_active_proposals = [
                proposal for proposal in current_proposals
                if proposal['index'] is not None
            ]
            previous_active_proposal_ids = [
                proposal['index'] for proposal in previous_proposals
                if proposal['index'] is not None
            ] if previous_proposals else None

            if previous_active_proposal_ids:
                for proposal_id in range(previous_prop_count,
                                         current_prop_count):
                    # Get proposal from current proposals and skip this proposal
                    # if it is not found in the list
                    proposal = next((prop for prop in current_active_proposals
                                     if prop['index'] == proposal_id), None)
                    if not proposal:
                        continue
                    new_proposal = (proposal_id not in
                                    previous_active_proposal_ids)
                    new_proposal_configs = configs.new_proposal
                    if str_to_bool(new_proposal_configs['enabled']):
                        self.alerting_factory.classify_conditional_alert(
                            substrate_alerts.NewProposalSubmittedAlert,
                            self._is_true_condition_function, [new_proposal],
                            [sub_chain_name, proposal_id, proposal['seconded'],
                             new_proposal_configs['severity'], last_monitored,
                             parent_id, parent_id], data_for_alerting,
                        )

            # Perform some transformations to the referendums list for easier
            # logic later on. We will ignore referendums with index None as this
            # means that the Data Transformer could not parse the referendum
            # correctly
            current_referendums = data['referendums']['current']
            previous_referendums = data['referendums']['previous']
            current_ongoing_referendums = [
                referendum for referendum in current_referendums
                if (referendum['index'] is not None and
                    referendum['status'] == 'ongoing')
            ]
            current_ongoing_referendum_ids = [
                referendum['index'] for referendum
                in current_ongoing_referendums
            ]
            previous_ongoing_referendums = [
                referendum for referendum in previous_referendums
                if (referendum['index'] is not None and
                    referendum['status'] == 'ongoing')
            ]
            previous_ongoing_referendum_ids = [
                referendum['index'] for referendum
                in previous_ongoing_referendums
            ]

            for referendum_id in range(previous_ref_count, current_ref_count):
                # Get referendum from current referendums and skip this
                # referendum if it is not found in the list
                referendum = next((ref for ref in current_ongoing_referendums
                                   if ref['index'] == referendum_id), None)
                if not referendum:
                    continue
                new_referendum = (referendum not in
                                  previous_ongoing_referendum_ids)
                new_referendum_configs = configs.new_referendum
                if str_to_bool(new_referendum_configs['enabled']):
                    self.alerting_factory.classify_conditional_alert(
                        substrate_alerts.NewReferendumSubmittedAlert,
                        self._alert_new_referendum,
                        [previous_referendums, new_referendum],
                        [sub_chain_name, referendum_id,
                         referendum['data']['isPassing'], referendum['end'],
                         referendum['data']['voted'],
                         new_referendum_configs['severity'], last_monitored,
                         parent_id, parent_id], data_for_alerting,
                    )

            for referendum in previous_ongoing_referendums:
                referendum_id = referendum['index']
                is_ongoing = referendum_id in current_ongoing_referendum_ids
                referendum_concluded_configs = configs.referendum_concluded
                if str_to_bool(referendum_concluded_configs['enabled']):
                    self.alerting_factory.classify_conditional_alert(
                        substrate_alerts.ReferendumConcludedAlert,
                        self._alert_referendum_conclusion, [True, is_ongoing],
                        [sub_chain_name, referendum_id, referendum['approved'],
                         referendum_concluded_configs['severity'],
                         last_monitored, parent_id, parent_id],
                        data_for_alerting,
                    )

    def _process_websocket_error(
            self, websocket_data: Dict, data_for_alerting: List) -> None:
        meta_data = websocket_data['meta_data']
        parent_id = meta_data['parent_id']
        sub_chain_name = meta_data['chain_name']
        time = meta_data['time']
        err_message = websocket_data['message']
        err_code = websocket_data['code']

        # Assert that the alerts_config has been received for the chain.
        full_chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, SubstrateNetworkAlertsConfig)
        if full_chain_name is not None:
            self.alerting_factory.create_alerting_state(parent_id)

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_error_alert(
                SubstrateApiIsNotReachableException.code,
                substrate_alerts.SubstrateApiIsNotReachableAlert,
                substrate_alerts.SubstrateApiIsReachableAlert,
                data_for_alerting, parent_id, parent_id, sub_chain_name, time,
                MetricCode.SubstrateApiNotReachable.value, err_message,
                "The Network Monitor for {} is now reaching the Substrate "
                "API.".format(sub_chain_name), err_code
            )
            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                substrate_alerts.
                    ErrorNoSyncedSubstrateWebSocketDataSourcesAlert,
                substrate_alerts.SyncedSubstrateWebSocketDataSourcesFoundAlert,
                data_for_alerting, parent_id, parent_id, sub_chain_name, time,
                MetricCode.NoSyncedSubstrateWebSocketDataSource.value,
                err_message, "The Network Monitor for {} found a websocket "
                             "synced data source again.".format(sub_chain_name),
                err_code
            )
            self.alerting_factory.classify_error_alert(
                SubstrateNetworkDataCouldNotBeObtained.code,
                substrate_alerts.SubstrateNetworkDataCouldNotBeObtainedAlert,
                substrate_alerts.SubstrateNetworkDataObtainedAlert,
                data_for_alerting,
                parent_id, parent_id, sub_chain_name, time,
                MetricCode.SubstrateNetworkDataNotObtained.value, err_message,
                "The Network Monitor for {} successfully retrieved network "
                "data again.".format(sub_chain_name), err_code
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
                },
            }
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
                # changed. A network's state will be recreated in the next
                # monitoring round automatically. Note we are sure that a
                # parent_id is to be returned, as we have just added the config.
                # NOTE: Internal alerts for metric state reset are to be sent
                #     : by the manager.
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, SubstrateNetworkAlertsConfig)
                self.alerting_factory.remove_chain_alerting_state(parent_id)
            else:
                # We must reset the state since a configuration is to be
                # removed. Note that first we need to compute the parent_id, as
                # the parent_id is obtained from the configs to be removed from
                # the factory. If the parent_id cannot be found, it means that
                # no storing took place, therefore in that case do nothing.
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, SubstrateNetworkAlertsConfig)
                if parent_id:
                    self.alerting_factory.remove_chain_alerting_state(parent_id)
                    self.alerts_configs_factory.remove_config(chain)
        except Exception as e:
            # Otherwise, log and reject the message
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
                'routing_key': SUBSTRATE_NETWORK_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
