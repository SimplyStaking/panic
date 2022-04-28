import copy
import json
import logging
from datetime import datetime
from typing import Dict, List

import pika
from pika.adapters.blocking_connection import BlockingChannel

import src.alerter.alerts.network.cosmos as cosmos_alerts
from src.alerter.alerters.alerter import Alerter
from src.alerter.factory.cosmos_network_alerting_factory import (
    CosmosNetworkAlertingFactory)
from src.alerter.grouped_alerts_metric_code.network.cosmos_network_metric_code \
    import GroupedCosmosNetworkAlertsMetricCode as MetricCode
from src.configs.alerts.network.cosmos import CosmosNetworkAlertsConfig
from src.configs.factory.alerts.cosmos_alerts import (
    CosmosNetworkAlertsConfigsFactory)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.cosmos import PROPOSAL_STATUS_VOTING_PERIOD
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, TOPIC, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    COSMOS_ALERTS_CONFIGS_ROUTING_KEY,
    COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
    COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY,
    COSMOS_NETWORK_ALERT_ROUTING_KEY)
from src.utils.data import transformed_data_processing_helper
from src.utils.exceptions import (
    NoSyncedDataSourceWasAccessibleException,
    CosmosNetworkDataCouldNotBeObtained, MessageWasNotDeliveredException)
from src.utils.types import str_to_bool


class CosmosNetworkAlerter(Alerter):
    """
    We will have one alerter for all cosmos networks. The cosmos alerter doesn't
    have to restart if the configurations change, as it will be listening for
    both data and configs in the same queue.
    """

    def __init__(
            self, alerter_name: str, logger: logging.Logger,
            rabbitmq: RabbitMQApi,
            cosmos_alerts_configs_factory: CosmosNetworkAlertsConfigsFactory,
            max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = cosmos_alerts_configs_factory
        self._alerting_factory = CosmosNetworkAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> CosmosNetworkAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_factory(self) -> CosmosNetworkAlertingFactory:
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
                         COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, passive=False,
            durable=True, exclusive=False, auto_delete=False)
        self.logger.info(
            "Binding queue '%s' to exchange '%s' with routing key '%s'",
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, ALERT_EXCHANGE,
            COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
            exchange=ALERT_EXCHANGE,
            routing_key=COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY)

        # Set configs consuming configuration
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, COSMOS_ALERTS_CONFIGS_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
            COSMOS_ALERTS_CONFIGS_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(
            queue=COSMOS_NETWORK_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
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
        if method.routing_key == COSMOS_NETWORK_TRANSFORMED_DATA_ROUTING_KEY:
            self._process_transformed_data(method, body)
        elif 'alerts_config' in method.routing_key:
            self._process_configs(method, body)
        else:
            self.logger.debug("Received unexpected data %s with routing key %s",
                              body, method.routing_key)
            self.rabbitmq.basic_ack(method.delivery_tag, False)

    @staticmethod
    def _alert_new_proposal(is_active: bool, previous_proposals: List,
                            new_proposal: bool, was_not_active: bool) -> bool:
        """
        We will alert on a new proposal if currently it is in voting period, and
        this is not the first monitoring round (i.e. previous != []), and the
        proposal is either new or was not active (in voting period)
        :param is_active: Whether the proposal is currently in voting period
        :param previous_proposals: The list of previous proposals
        :param new_proposal: Whether the proposal is a new proposal or not
        :param was_not_active: Whether the proposal was in voting period or not
        :return: True if we should alert on the proposal
               : False otherwise
        """
        return (is_active
                and previous_proposals != []
                and (new_proposal or was_not_active))

    @staticmethod
    def _alert_proposal_conclusion(is_active: bool, was_active: bool) -> bool:
        """
        We will alert on a concluded proposal if it was active
        (in voting period) and now it is no longer active.
        :param is_active: Whether the proposal is currently active
        :param was_active: Whether the proposal was previously active
        :return: True if we should alert on the proposal
               : False otherwise
        """
        return was_active and not is_active

    def _process_cosmos_rest_result(self, rest_data: Dict,
                                    data_for_alerting: List) -> None:
        meta_data = rest_data['meta_data']
        parent_id = meta_data['parent_id']
        sub_chain_name = meta_data['chain_name']
        last_monitored = meta_data['last_monitored']
        data = rest_data['data']

        # Assert that the alerts_config has been received for the chain.
        full_chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNetworkAlertsConfig)
        if full_chain_name is not None:
            configs = self.alerts_configs_factory.configs[full_chain_name]
            self.alerting_factory.create_alerting_state(parent_id)

            # Check if some errors have been resolved

            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
                cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
                data_for_alerting, parent_id, parent_id, sub_chain_name,
                last_monitored, MetricCode.NoSyncedCosmosRestSource.value, "",
                "The Network Monitor for {} found a Cosmos-Rest synced data "
                "source again".format(sub_chain_name), None
            )
            self.alerting_factory.classify_error_alert(
                CosmosNetworkDataCouldNotBeObtained.code,
                cosmos_alerts.CosmosNetworkDataCouldNotBeObtainedAlert,
                cosmos_alerts.CosmosNetworkDataObtainedAlert, data_for_alerting,
                parent_id, parent_id, sub_chain_name, last_monitored,
                MetricCode.CosmosNetworkDataNotObtained.value, "",
                "The Network Monitor for {} successfully retrieved network "
                "data again.".format(sub_chain_name), None
            )

            # Check if the alert rules are satisfied for the metrics

            # Perform some transformations to the proposals list for easier
            # logic later on. We will ignore proposals with ID None as this
            # means that the Data Transformer could not parse the proposal
            # correctly
            current_proposals = data['proposals']['current']
            previous_proposals = data['proposals']['previous']
            current_filtered_proposals = [
                proposal
                for proposal in current_proposals
                if proposal['proposal_id'] is not None
            ]
            previous_filtered_proposals = [
                proposal
                for proposal in previous_proposals
                if proposal['proposal_id'] is not None
            ]
            current_active_proposals = [
                proposal
                for proposal in current_filtered_proposals
                if proposal['status'] == PROPOSAL_STATUS_VOTING_PERIOD
            ]
            current_non_active_proposals = [
                proposal
                for proposal in current_filtered_proposals
                if proposal['status'] != PROPOSAL_STATUS_VOTING_PERIOD
            ]
            previous_proposal_ids = [
                proposal['proposal_id']
                for proposal in previous_filtered_proposals
            ]
            previous_non_active_proposal_ids = [
                proposal['proposal_id']
                for proposal in previous_filtered_proposals
                if proposal['status'] != PROPOSAL_STATUS_VOTING_PERIOD
            ]
            previous_active_proposal_ids = [
                proposal['proposal_id']
                for proposal in previous_filtered_proposals
                if proposal['status'] == PROPOSAL_STATUS_VOTING_PERIOD
            ]

            for proposal in current_active_proposals:
                proposal_id = proposal['proposal_id']
                new_proposal = proposal_id not in previous_proposal_ids
                was_not_active = proposal_id in previous_non_active_proposal_ids
                new_proposal_configs = configs.new_proposal
                if str_to_bool(new_proposal_configs['enabled']):
                    self.alerting_factory.classify_conditional_alert(
                        cosmos_alerts.NewProposalSubmittedAlert,
                        self._alert_new_proposal,
                        [True, previous_proposals, new_proposal,
                         was_not_active],
                        [sub_chain_name, proposal_id, proposal['title'],
                         proposal['voting_end_time'],
                         new_proposal_configs['severity'], last_monitored,
                         parent_id, parent_id], data_for_alerting,
                    )

                if not self.alerting_factory.proposal_active(parent_id,
                                                             proposal_id):
                    self.alerting_factory.add_active_proposal(
                        parent_id, proposal, proposal_id)

            for proposal in current_non_active_proposals:
                proposal_id = proposal['proposal_id']
                was_active = proposal_id in previous_active_proposal_ids
                proposal_concluded_configs = configs.proposal_concluded
                if str_to_bool(proposal_concluded_configs['enabled']):
                    self.alerting_factory.classify_conditional_alert(
                        cosmos_alerts.ProposalConcludedAlert,
                        self._alert_proposal_conclusion, [False, was_active],
                        [sub_chain_name, proposal_id, proposal['title'],
                         proposal['status'], proposal['final_tally_result'],
                         proposal_concluded_configs['severity'], last_monitored,
                         parent_id, parent_id], data_for_alerting,
                    )

                self.alerting_factory.remove_active_proposal(parent_id,
                                                             proposal_id)

    def _process_cosmos_rest_error(self, rest_data: Dict,
                                   data_for_alerting: List) -> None:
        meta_data = rest_data['meta_data']
        parent_id = meta_data['parent_id']
        sub_chain_name = meta_data['chain_name']
        time = meta_data['time']
        err_message = rest_data['message']
        err_code = rest_data['code']

        # Assert that the alerts_config has been received for the chain.
        full_chain_name = self.alerts_configs_factory.get_chain_name(
            parent_id, CosmosNetworkAlertsConfig)
        if full_chain_name is not None:
            self.alerting_factory.create_alerting_state(parent_id)

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_error_alert(
                NoSyncedDataSourceWasAccessibleException.code,
                cosmos_alerts.ErrorNoSyncedCosmosRestDataSourcesAlert,
                cosmos_alerts.SyncedCosmosRestDataSourcesFoundAlert,
                data_for_alerting, parent_id, parent_id, sub_chain_name, time,
                MetricCode.NoSyncedCosmosRestSource.value, err_message,
                "The Network Monitor for {} found a Cosmos-Rest synced data "
                "source again".format(sub_chain_name), err_code
            )
            self.alerting_factory.classify_error_alert(
                CosmosNetworkDataCouldNotBeObtained.code,
                cosmos_alerts.CosmosNetworkDataCouldNotBeObtainedAlert,
                cosmos_alerts.CosmosNetworkDataObtainedAlert, data_for_alerting,
                parent_id, parent_id, sub_chain_name, time,
                MetricCode.CosmosNetworkDataNotObtained.value, err_message,
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
                'cosmos_rest': {
                    'result': self._process_cosmos_rest_result,
                    'error': self._process_cosmos_rest_error,
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
                    chain, CosmosNetworkAlertsConfig)
                self.alerting_factory.remove_chain_alerting_state(parent_id)
            else:
                # We must reset the state since a configuration is to be
                # removed. Note that first we need to compute the parent_id, as
                # the parent_id is obtained from the configs to be removed from
                # the factory. If the parent_id cannot be found, it means that
                # no storing took place, therefore in that case do nothing.
                parent_id = self.alerts_configs_factory.get_parent_id(
                    chain, CosmosNetworkAlertsConfig)
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
                'routing_key': COSMOS_NETWORK_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
