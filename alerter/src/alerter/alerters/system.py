import copy
import json
import logging
from datetime import datetime
from typing import Dict, List

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerters.alerter import Alerter
from src.alerter.alerts import system_alerts
from src.alerter.factory.system_alerting_factory import SystemAlertingFactory
from src.alerter.grouped_alerts_metric_code import \
    GroupedSystemAlertsMetricCode as MetricCode
from src.configs.factory.alerts.system_alerts import SystemAlertsConfigsFactory
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE, SYSTEM_ALERT_ROUTING_KEY, TOPIC,
    SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
    SYSTEM_TRANSFORMED_DATA_ROUTING_KEY, ALERTS_CONFIGS_ROUTING_KEY_GEN,
    ALERTS_CONFIGS_ROUTING_KEY_CHAIN)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  ReceivedUnexpectedDataException,
                                  MetricNotFoundException,
                                  SystemIsDownException, InvalidUrlException)
from src.utils.types import str_to_bool


class SystemAlerter(Alerter):
    """
    We will have one alerter for all systems. The system alerter doesn't
    have to restart if the configurations change, as it will be listening
    for both data and configs in the same queue.
    """

    def __init__(self, alerter_name: str, logger: logging.Logger,
                 system_alerts_configs_factory: SystemAlertsConfigsFactory,
                 rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._alerts_configs_factory = system_alerts_configs_factory
        self._alerting_factory = SystemAlertingFactory(logger)

    @property
    def alerts_configs_factory(self) -> SystemAlertsConfigsFactory:
        return self._alerts_configs_factory

    @property
    def alerting_factory(self) -> SystemAlertingFactory:
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
                         SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                                    passive=False, durable=True,
                                    exclusive=False, auto_delete=False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         ALERT_EXCHANGE, SYSTEM_TRANSFORMED_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(
            queue=SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
            exchange=ALERT_EXCHANGE,
            routing_key=SYSTEM_TRANSFORMED_DATA_ROUTING_KEY)

        # Set configs consuming configuration
        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, ALERTS_CONFIGS_ROUTING_KEY_CHAIN)
        self.rabbitmq.queue_bind(
            SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
            ALERTS_CONFIGS_ROUTING_KEY_CHAIN)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "%s'", SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, ALERTS_CONFIGS_ROUTING_KEY_GEN)
        self.rabbitmq.queue_bind(
            SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME, CONFIG_EXCHANGE,
            ALERTS_CONFIGS_ROUTING_KEY_GEN)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(
            queue=SYSTEM_ALERTER_INPUT_CONFIGS_QUEUE_NAME,
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
        if method.routing_key == SYSTEM_TRANSFORMED_DATA_ROUTING_KEY:
            self._process_transformed_data(method, body)
        elif 'alerts_config' in method.routing_key:
            self._process_configs(method, body)
        else:
            self.logger.debug("Received unexpected data %s with routing key %s",
                              body, method.routing_key)
            self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_result(self, transformer_data: Dict,
                        data_for_alerting: List) -> None:
        meta_data = transformer_data['meta_data']
        data = transformer_data['data']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            meta_data['system_parent_id'])
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                meta_data['system_parent_id'], meta_data['system_id'], configs)

            # Check if some errors have been resolved
            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code, system_alerts.InvalidUrlAlert,
                system_alerts.ValidUrlAlert, data_for_alerting,
                meta_data['system_parent_id'], meta_data['system_id'],
                meta_data['system_name'], meta_data['last_monitored'],
                MetricCode.InvalidUrl.value, "", "URL is now valid!."
            )

            self.alerting_factory.classify_error_alert(
                MetricNotFoundException.code,
                system_alerts.MetricNotFoundErrorAlert,
                system_alerts.MetricFoundAlert, data_for_alerting,
                meta_data['system_parent_id'], meta_data['system_id'],
                meta_data['system_name'], meta_data['last_monitored'],
                MetricCode.MetricNotFound.value, "", "Metrics have been found!."
            )

            # Check if the alert rules are satisfied for the metrics
            if str_to_bool(configs.system_is_down['enabled']):
                sub_config = configs.system_is_down
                self.alerting_factory.classify_downtime_alert(
                    None, sub_config,
                    system_alerts.SystemWentDownAtAlert,
                    system_alerts.SystemStillDownAlert,
                    system_alerts.SystemBackUpAgainAlert,
                    data_for_alerting,
                    meta_data['system_parent_id'], meta_data['system_id'],
                    MetricCode.SystemIsDown.value,
                    meta_data['system_name'], meta_data['last_monitored']
                )

            if str_to_bool(configs.open_file_descriptors['enabled']):
                current = data['open_file_descriptors']['current']
                sub_config = configs.open_file_descriptors
                self.alerting_factory.classify_thresholded_alert(
                    current, sub_config,
                    system_alerts.
                        OpenFileDescriptorsIncreasedAboveThresholdAlert,
                    system_alerts.
                        OpenFileDescriptorsDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    meta_data['system_parent_id'], meta_data['system_id'],
                    MetricCode.OpenFileDescriptorsThreshold.value,
                    meta_data['system_name'], meta_data['last_monitored']
                )

            if str_to_bool(configs.system_cpu_usage['enabled']):
                current = data['system_cpu_usage']['current']
                sub_config = configs.system_cpu_usage
                self.alerting_factory.classify_thresholded_alert(
                    current, sub_config,
                    system_alerts.SystemCPUUsageIncreasedAboveThresholdAlert,
                    system_alerts.SystemCPUUsageDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    meta_data['system_parent_id'], meta_data['system_id'],
                    MetricCode.SystemCPUUsageThreshold.value,
                    meta_data['system_name'], meta_data['last_monitored']
                )

            if str_to_bool(configs.system_ram_usage['enabled']):
                current = data['system_ram_usage']['current']
                sub_config = configs.system_ram_usage
                self.alerting_factory.classify_thresholded_alert(
                    current, sub_config,
                    system_alerts.SystemRAMUsageIncreasedAboveThresholdAlert,
                    system_alerts.SystemRAMUsageDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    meta_data['system_parent_id'], meta_data['system_id'],
                    MetricCode.SystemRAMUsageThreshold.value,
                    meta_data['system_name'], meta_data['last_monitored']
                )

            if str_to_bool(configs.system_storage_usage['enabled']):
                current = data['system_storage_usage']['current']
                sub_config = configs.system_storage_usage
                self.alerting_factory.classify_thresholded_alert(
                    current, sub_config,
                    system_alerts.
                        SystemStorageUsageIncreasedAboveThresholdAlert,
                    system_alerts.
                        SystemStorageUsageDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    meta_data['system_parent_id'], meta_data['system_id'],
                    MetricCode.SystemStorageUsageThreshold.value,
                    meta_data['system_name'], meta_data['last_monitored']
                )

    def _process_error(self, data: Dict, data_for_alerting: List) -> None:
        meta_data = data['meta_data']

        # Assert that the alerts_config has been received for the chain.
        chain_name = self.alerts_configs_factory.get_chain_name(
            meta_data['system_parent_id'])
        if chain_name is not None:
            configs = self.alerts_configs_factory.configs[chain_name]
            self.alerting_factory.create_alerting_state(
                meta_data['system_parent_id'], meta_data['system_id'], configs)

            # Detect whether some errors need to be raised, or have been
            # resolved.
            self.alerting_factory.classify_error_alert(
                InvalidUrlException.code, system_alerts.InvalidUrlAlert,
                system_alerts.ValidUrlAlert, data_for_alerting,
                meta_data['system_parent_id'], meta_data['system_id'],
                meta_data['system_name'], meta_data['time'],
                MetricCode.InvalidUrl.value, data['message'],
                "URL is now valid!", data['code']
            )

            self.alerting_factory.classify_error_alert(
                MetricNotFoundException.code,
                system_alerts.MetricNotFoundErrorAlert,
                system_alerts.MetricFoundAlert, data_for_alerting,
                meta_data['system_parent_id'], meta_data['system_id'],
                meta_data['system_name'], meta_data['time'],
                MetricCode.MetricNotFound.value, data['message'],
                "Metrics have been found!", data['code']
            )

            # Check if the alert rules are satisfied for the metrics
            if str_to_bool(configs.system_is_down['enabled']):
                sub_config = configs.system_is_down
                if data['code'] == SystemIsDownException.code:
                    self.alerting_factory.classify_downtime_alert(
                        data['data']['went_down_at']['current'], sub_config,
                        system_alerts.SystemWentDownAtAlert,
                        system_alerts.SystemStillDownAlert,
                        system_alerts.SystemBackUpAgainAlert,
                        data_for_alerting,
                        meta_data['system_parent_id'], meta_data['system_id'],
                        MetricCode.SystemIsDown.value,
                        meta_data['system_name'], meta_data['time']
                    )

    def _process_transformed_data(self, method: pika.spec.Basic.Deliver,
                                  body: bytes) -> None:
        data_received = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.",
                          data_received)

        processing_error = False
        data_for_alerting = []
        try:
            if 'result' in data_received:
                self._process_result(data_received['result'],
                                     data_for_alerting)
            elif 'error' in data_received:
                self._process_error(data_received['error'],
                                    data_for_alerting)
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _process_transformed_data".format(self))
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

        if method.routing_key == ALERTS_CONFIGS_ROUTING_KEY_GEN:
            chain = 'general'
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]

        try:
            # Checking if the configuration is empty. If it is empty, remove the
            # stored config (if it exists), and if it is not, add it to the
            # list of configurations.
            if bool(sent_configs):
                self.alerts_configs_factory.add_new_config(chain, sent_configs)

                # We must reset the state since some thresholds might have
                # changed. A system's state will be recreated in the next
                # monitoring round automatically. Note we are sure that a
                # parent_id is to be returned, as we have just added the config.
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
                'routing_key': SYSTEM_ALERT_ROUTING_KEY,
                'data': copy.deepcopy(alert),
                'properties': pika.BasicProperties(delivery_mode=2),
                'mandatory': True})
            self.logger.debug("%s added to the publishing queue successfully.",
                              alert)
