import copy
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Type, List

import pika.exceptions

from src.alerter.alert_severities import Severity
from src.alerter.alerters.alerter import Alerter
from src.alerter.alerts.system_alerts import (
    InvalidUrlAlert, OpenFileDescriptorsIncreasedAboveThresholdAlert,
    SystemBackUpAgainAlert,
    SystemCPUUsageDecreasedBelowThresholdAlert,
    SystemCPUUsageIncreasedAboveThresholdAlert,
    SystemRAMUsageDecreasedBelowThresholdAlert,
    SystemRAMUsageIncreasedAboveThresholdAlert, SystemStillDownAlert,
    SystemStorageUsageDecreasedBelowThresholdAlert,
    SystemStorageUsageIncreasedAboveThresholdAlert, SystemWentDownAtAlert,
    OpenFileDescriptorsDecreasedBelowThresholdAlert, MetricNotFoundErrorAlert,
    ValidUrlAlert, MetricFoundAlert)
from src.alerter.grouped_alerts_metric_code import GroupedSystemAlertsMetricCode
from src.configs.alerts.system import SystemAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.rabbitmq import (
    ALERT_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    SYS_ALERTER_INPUT_QUEUE_NAME_TEMPLATE, SYSTEM_ALERT_ROUTING_KEY,
    SYSTEM_TRANSFORMED_DATA_ROUTING_KEY_TEMPLATE, TOPIC)
from src.utils.exceptions import (MessageWasNotDeliveredException,
                                  ReceivedUnexpectedDataException)
from src.utils.timing import TimedTaskLimiter
from src.utils.types import (IncreasedAboveThresholdSystemAlert,
                             DecreasedBelowThresholdSystemAlert, str_to_bool,
                             convert_to_float)


class SystemAlerter(Alerter):
    def __init__(self, alerter_name: str,
                 system_alerts_config: SystemAlertsConfig,
                 logger: logging.Logger, rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0) -> None:
        super().__init__(alerter_name, logger, rabbitmq, max_queue_size)

        self._system_alerts_config = system_alerts_config
        self._queue_used = ''
        self._invalid_url = {}
        self._metric_not_found = {}
        self._warning_sent = {}
        self._critical_sent = {}
        self._system_initial_alert_sent = {}
        self._system_critical_timed_task_limiters = {}

    @property
    def alerts_configs(self) -> SystemAlertsConfig:
        return self._system_alerts_config

    def _create_state_for_system(self, system_id: str) -> None:
        # This is for alerts were we want to check if an initial alert was sent
        # for that metric, irrespective of the severity.
        if system_id not in self._system_initial_alert_sent:
            self._system_initial_alert_sent[system_id] = {
                GroupedSystemAlertsMetricCode.SystemIsDown.value: False,
            }

        # This is for alerts were we want to check if a warning alert was sent
        # for a metric
        if system_id not in self._warning_sent:
            self._warning_sent[system_id] = {
                GroupedSystemAlertsMetricCode.OpenFileDescriptorsThreshold
                    .value: False,
                GroupedSystemAlertsMetricCode.SystemCPUUsageThreshold
                    .value: False,
                GroupedSystemAlertsMetricCode.SystemStorageUsageThreshold
                    .value: False,
                GroupedSystemAlertsMetricCode.SystemRAMUsageThreshold
                    .value: False,
            }

        # This is for alerts were we want to check if a critical alert was sent
        # for a metric
        if system_id not in self._critical_sent:
            self._critical_sent[system_id] = {
                GroupedSystemAlertsMetricCode.OpenFileDescriptorsThreshold
                    .value: False,
                GroupedSystemAlertsMetricCode.SystemCPUUsageThreshold
                    .value: False,
                GroupedSystemAlertsMetricCode.SystemStorageUsageThreshold
                    .value: False,
                GroupedSystemAlertsMetricCode.SystemRAMUsageThreshold
                    .value: False,
            }

        """
        These are used to indicate that the source that was having issues
        in the form of `Invalid URL` or `Metric Not Found` is no longer
        having those issues. By sending out the opposite alerts we can overwrite
        the REDIS metric data which is displayed in the UI. This also informs
        the user that the issue has been resolved.
        """
        if system_id not in self._invalid_url:
            self._invalid_url[system_id] = False

        if system_id not in self._metric_not_found:
            self._metric_not_found[system_id] = False

        # initialise timed task limiters
        if system_id not in self._system_critical_timed_task_limiters:
            open_fd = self.alerts_configs.open_file_descriptors
            cpu_use = self.alerts_configs.system_cpu_usage
            storage = self.alerts_configs.system_storage_usage
            ram_use = self.alerts_configs.system_ram_usage
            is_down = self.alerts_configs.system_is_down

            self._system_critical_timed_task_limiters[system_id] = {}
            system_critical_limiters = \
                self._system_critical_timed_task_limiters[system_id]

            open_fd_critical_repeat = convert_to_float(
                open_fd['critical_repeat'], timedelta.max.total_seconds() - 1)
            cpu_use_critical_repeat = convert_to_float(
                cpu_use['critical_repeat'], timedelta.max.total_seconds() - 1)
            storage_critical_repeat = convert_to_float(
                storage['critical_repeat'], timedelta.max.total_seconds() - 1)
            ram_use_critical_repeat = convert_to_float(
                ram_use['critical_repeat'], timedelta.max.total_seconds() - 1)
            is_down_critical_repeat = convert_to_float(
                is_down['critical_repeat'], timedelta.max.total_seconds() - 1)

            system_critical_limiters[
                GroupedSystemAlertsMetricCode.OpenFileDescriptorsThreshold
                    .value] = TimedTaskLimiter(timedelta(seconds=float(
                open_fd_critical_repeat)))
            system_critical_limiters[
                GroupedSystemAlertsMetricCode.SystemCPUUsageThreshold.value] = \
                TimedTaskLimiter(timedelta(seconds=float(
                    cpu_use_critical_repeat)))
            system_critical_limiters[
                GroupedSystemAlertsMetricCode.SystemStorageUsageThreshold
                    .value] = TimedTaskLimiter(
                timedelta(seconds=float(storage_critical_repeat))
            )
            system_critical_limiters[
                GroupedSystemAlertsMetricCode.SystemRAMUsageThreshold.value] = \
                TimedTaskLimiter(timedelta(seconds=float(
                    ram_use_critical_repeat)))
            system_critical_limiters[
                GroupedSystemAlertsMetricCode.SystemIsDown
                    .value] = TimedTaskLimiter(
                timedelta(seconds=float(is_down_critical_repeat)))

    def _initialise_rabbitmq(self) -> None:
        # An alerter is both a consumer and producer, therefore we need to
        # initialise both the consuming and producing configurations.
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(exchange=ALERT_EXCHANGE,
                                       exchange_type=TOPIC, passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self._queue_used = SYS_ALERTER_INPUT_QUEUE_NAME_TEMPLATE.format(
            self.alerts_configs.parent_id)
        self.logger.info("Creating queue '%s'", self._queue_used)
        self.rabbitmq.queue_declare(self._queue_used, passive=False,
                                    durable=True, exclusive=False,
                                    auto_delete=False)
        routing_key = SYSTEM_TRANSFORMED_DATA_ROUTING_KEY_TEMPLATE.format(
            self.alerts_configs.parent_id)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", self._queue_used, ALERT_EXCHANGE,
                         routing_key)
        self.rabbitmq.queue_bind(queue=self._queue_used,
                                 exchange=ALERT_EXCHANGE,
                                 routing_key=routing_key)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(queue=self._queue_used,
                                    on_message_callback=self._process_data,
                                    auto_ack=False, exclusive=False,
                                    consumer_tag=None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        data_received = json.loads(body)
        self.logger.debug("Received %s. Now processing this data.",
                          data_received)

        parsed_routing_key = method.routing_key.split('.')
        processing_error = False
        data_for_alerting = []
        try:
            if self.alerts_configs.parent_id in parsed_routing_key:
                if 'result' in data_received:
                    data = data_received['result']['data']
                    meta_data = data_received['result']['meta_data']
                    self._create_state_for_system(meta_data['system_id'])
                    self._process_results(data, meta_data, data_for_alerting)
                elif 'error' in data_received:
                    self._create_state_for_system(
                        data_received['error']['meta_data']['system_id'])
                    self._process_errors(data_received['error'],
                                         data_for_alerting)
                else:
                    raise ReceivedUnexpectedDataException(
                        "{}: _process_data".format(self))
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _process_data".format(self))
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

    def _process_errors(self, error_data: Dict,
                        data_for_alerting: List) -> None:
        is_down = self.alerts_configs.system_is_down
        meta_data = error_data['meta_data']

        if self._invalid_url[meta_data['system_id']] and \
                int(error_data['code']) != 5009:
            alert = ValidUrlAlert(
                meta_data['system_name'], "Url is valid!",
                Severity.INFO.value, meta_data['time'],
                meta_data['system_parent_id'],
                meta_data['system_id']
            )
            data_for_alerting.append(alert.alert_data)
            self.logger.debug("Successfully classified alert %s",
                              alert.alert_data)
            self._invalid_url[meta_data['system_id']] = False

        if self._metric_not_found[meta_data['system_id']] and \
                int(error_data['code']) != 5003:
            alert = MetricFoundAlert(
                meta_data['system_name'], "Metrics have been found!",
                Severity.INFO.value, meta_data['time'],
                meta_data['system_parent_id'],
                meta_data['system_id']
            )
            data_for_alerting.append(alert.alert_data)
            self.logger.debug("Successfully classified alert %s",
                              alert.alert_data)
            self._metric_not_found[meta_data['system_id']] = False

        """
        `MetricNotFoundErrorAlert` and `InvalidUrlAlert` repeat every
        monitoring round (DEFAULT: 60 seconds). This is done without delays as
        it's indication that the configuration is wrong.
        """
        if int(error_data['code']) == 5003:
            alert = MetricNotFoundErrorAlert(
                meta_data['system_name'], error_data['message'],
                Severity.ERROR.value, meta_data['time'],
                meta_data['system_parent_id'],
                meta_data['system_id']
            )
            data_for_alerting.append(alert.alert_data)
            self.logger.debug("Successfully classified alert %s",
                              alert.alert_data)
            self._metric_not_found[meta_data['system_id']] = True
        elif int(error_data['code']) == 5009:
            alert = InvalidUrlAlert(
                meta_data['system_name'], error_data['message'],
                Severity.ERROR.value, meta_data['time'],
                meta_data['system_parent_id'],
                meta_data['system_id']
            )
            data_for_alerting.append(alert.alert_data)
            self.logger.debug("Successfully classified alert %s",
                              alert.alert_data)
            self._invalid_url[meta_data['system_id']] = True
        elif int(error_data['code']) == 5004:
            if str_to_bool(is_down['enabled']):
                data = error_data['data']
                current = float(data['went_down_at']['current'])
                monitoring_timestamp = float(meta_data['time'])
                monitoring_datetime = datetime.fromtimestamp(
                    monitoring_timestamp)
                is_down_critical_limiter = \
                    self._system_critical_timed_task_limiters[
                        meta_data['system_id']][
                        GroupedSystemAlertsMetricCode.SystemIsDown.value]
                initial_downtime_alert_sent = \
                    self._system_initial_alert_sent[meta_data['system_id']][
                        GroupedSystemAlertsMetricCode.SystemIsDown.value]
                downtime = monitoring_timestamp - current
                critical_threshold = convert_to_float(
                    is_down['critical_threshold'], None)
                critical_enabled = str_to_bool(is_down['critical_enabled'])
                critical_repeat_enabled = str_to_bool(
                    is_down['critical_repeat_enabled'])
                warning_threshold = convert_to_float(
                    is_down['warning_threshold'], None)
                warning_enabled = str_to_bool(is_down['warning_enabled'])

                if not initial_downtime_alert_sent:
                    if critical_enabled and critical_threshold <= downtime:
                        alert = SystemWentDownAtAlert(
                            meta_data['system_name'], Severity.CRITICAL.value,
                            meta_data['time'], meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                        data_for_alerting.append(alert.alert_data)
                        self.logger.debug("Successfully classified alert %s",
                                          alert.alert_data)
                        is_down_critical_limiter.set_last_time_that_did_task(
                            monitoring_datetime)
                        self._system_initial_alert_sent[meta_data['system_id']][
                            GroupedSystemAlertsMetricCode.SystemIsDown
                                .value] = True
                    elif warning_enabled and warning_threshold <= downtime:
                        alert = SystemWentDownAtAlert(
                            meta_data['system_name'], Severity.WARNING.value,
                            meta_data['time'], meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                        data_for_alerting.append(alert.alert_data)
                        self.logger.debug("Successfully classified alert %s",
                                          alert.alert_data)
                        is_down_critical_limiter.set_last_time_that_did_task(
                            monitoring_datetime)
                        self._system_initial_alert_sent[meta_data['system_id']][
                            GroupedSystemAlertsMetricCode.SystemIsDown
                                .value] = True
                else:
                    if critical_enabled and critical_repeat_enabled and \
                            is_down_critical_limiter.can_do_task(
                                monitoring_datetime):
                        alert = SystemStillDownAlert(
                            meta_data['system_name'], downtime,
                            Severity.CRITICAL.value,
                            meta_data['time'], meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                        data_for_alerting.append(alert.alert_data)
                        self.logger.debug("Successfully classified alert %s",
                                          alert.alert_data)
                        is_down_critical_limiter.set_last_time_that_did_task(
                            monitoring_datetime)

    def _process_results(self, metrics: Dict, meta_data: Dict,
                         data_for_alerting: List) -> None:
        open_fd = self.alerts_configs.open_file_descriptors
        cpu_use = self.alerts_configs.system_cpu_usage
        storage = self.alerts_configs.system_storage_usage
        ram_use = self.alerts_configs.system_ram_usage
        is_down = self.alerts_configs.system_is_down

        if self._invalid_url[meta_data['system_id']]:
            alert = ValidUrlAlert(
                meta_data['system_name'], "Url is valid!",
                Severity.INFO.value, meta_data['last_monitored'],
                meta_data['system_parent_id'],
                meta_data['system_id']
            )
            data_for_alerting.append(alert.alert_data)
            self.logger.debug("Successfully classified alert %s",
                              alert.alert_data)
            self._invalid_url[meta_data['system_id']] = False
        if self._metric_not_found[meta_data['system_id']]:
            alert = MetricFoundAlert(
                meta_data['system_name'], "Metrics have been found!",
                Severity.INFO.value, meta_data['last_monitored'],
                meta_data['system_parent_id'],
                meta_data['system_id']
            )
            data_for_alerting.append(alert.alert_data)
            self.logger.debug("Successfully classified alert %s",
                              alert.alert_data)
            self._metric_not_found[meta_data['system_id']] = False

        if str_to_bool(is_down['enabled']):
            previous = metrics['went_down_at']['previous']
            is_down_critical_limiter = \
                self._system_critical_timed_task_limiters[
                    meta_data['system_id']][
                    GroupedSystemAlertsMetricCode.SystemIsDown.value]
            initial_downtime_alert_sent = \
                self._system_initial_alert_sent[meta_data['system_id']][
                    GroupedSystemAlertsMetricCode.SystemIsDown.value]

            if previous is not None or initial_downtime_alert_sent:
                alert = SystemBackUpAgainAlert(
                    meta_data['system_name'], Severity.INFO.value,
                    meta_data['last_monitored'], meta_data['system_parent_id'],
                    meta_data['system_id']
                )
                data_for_alerting.append(alert.alert_data)
                self.logger.debug("Successfully classified alert %s",
                                  alert.alert_data)
                self._system_initial_alert_sent[meta_data['system_id']][
                    GroupedSystemAlertsMetricCode.SystemIsDown.value] = False
                is_down_critical_limiter.reset()

        if str_to_bool(open_fd['enabled']):
            current = metrics['open_file_descriptors']['current']
            if current is not None:
                self._classify_alert(
                    current, open_fd, meta_data,
                    OpenFileDescriptorsIncreasedAboveThresholdAlert,
                    OpenFileDescriptorsDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    GroupedSystemAlertsMetricCode.OpenFileDescriptorsThreshold
                        .value
                )
        if str_to_bool(storage['enabled']):
            current = metrics['system_storage_usage']['current']
            if current is not None:
                self._classify_alert(
                    current, storage, meta_data,
                    SystemStorageUsageIncreasedAboveThresholdAlert,
                    SystemStorageUsageDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    GroupedSystemAlertsMetricCode.SystemStorageUsageThreshold
                        .value
                )
        if str_to_bool(cpu_use['enabled']):
            current = metrics['system_cpu_usage']['current']
            if current is not None:
                self._classify_alert(
                    current, cpu_use, meta_data,
                    SystemCPUUsageIncreasedAboveThresholdAlert,
                    SystemCPUUsageDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    GroupedSystemAlertsMetricCode.SystemCPUUsageThreshold.value
                )
        if str_to_bool(ram_use['enabled']):
            current = metrics['system_ram_usage']['current']
            if current is not None:
                self._classify_alert(
                    current, ram_use, meta_data,
                    SystemRAMUsageIncreasedAboveThresholdAlert,
                    SystemRAMUsageDecreasedBelowThresholdAlert,
                    data_for_alerting,
                    GroupedSystemAlertsMetricCode.SystemRAMUsageThreshold.value
                )

    def _classify_alert(
            self, current: float, config: Dict, meta_data: Dict,
            increased_above_threshold_alert:
            Type[IncreasedAboveThresholdSystemAlert],
            decreased_below_threshold_alert:
            Type[DecreasedBelowThresholdSystemAlert], data_for_alerting: List,
            metric_name: str
    ) -> None:
        warning_threshold = convert_to_float(config['warning_threshold'], None)
        critical_threshold = convert_to_float(config['critical_threshold'],
                                              None)
        warning_enabled = str_to_bool(config['warning_enabled'])
        critical_enabled = str_to_bool(config['critical_enabled'])
        critical_repeat_enabled = str_to_bool(config['critical_repeat_enabled'])
        critical_limiter = self._system_critical_timed_task_limiters[
            meta_data['system_id']][metric_name]
        warning_sent = self._warning_sent[meta_data['system_id']][metric_name]
        critical_sent = self._critical_sent[meta_data['system_id']][metric_name]
        monitoring_datetime = datetime.fromtimestamp(
            float(meta_data['last_monitored']))

        if warning_enabled and critical_enabled:
            # If both warning and critical are enabled, we are combining alerts
            # so that only one alert is received, depending on the current
            # value.

            if (warning_threshold <= current < critical_threshold) \
                    and (not warning_sent) and (not critical_sent):
                # We do not use previous here so that an alert is raised if the
                # alerter is restarted with a different configuration

                alert = increased_above_threshold_alert(
                    meta_data['system_name'], current, Severity.WARNING.value,
                    meta_data['last_monitored'], Severity.WARNING.value,
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                data_for_alerting.append(alert.alert_data)
                self.logger.debug("Successfully classified alert %s",
                                  alert.alert_data)
                self._warning_sent[meta_data['system_id']][metric_name] = True
            elif warning_threshold < critical_threshold <= current:

                # We want to send a critical alert if no critical alert was
                # sent yet, or repeating is enabled and the repeating threshold
                # has been exceeded
                if not critical_sent or (
                        critical_repeat_enabled and
                        critical_limiter.can_do_task(monitoring_datetime)):
                    # We do not use previous here so that an alert is raised if
                    # the alerter is restarted with a different configuration

                    alert = increased_above_threshold_alert(
                        meta_data['system_name'], current,
                        Severity.CRITICAL.value, meta_data['last_monitored'],
                        Severity.CRITICAL.value, meta_data['system_parent_id'],
                        meta_data['system_id']
                    )
                    data_for_alerting.append(alert.alert_data)
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    critical_limiter.set_last_time_that_did_task(
                        monitoring_datetime)
                    self._critical_sent[meta_data['system_id']][
                        metric_name] = True
            elif current < warning_threshold and (
                    warning_sent or critical_sent):
                # We do not use previous here so that an alert is raised if the
                # alerter is restarted with a different configuration

                alert = decreased_below_threshold_alert(
                    meta_data['system_name'], current, Severity.INFO.value,
                    meta_data['last_monitored'], Severity.WARNING.value,
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                data_for_alerting.append(alert.alert_data)
                self.logger.debug("Successfully classified alert %s",
                                  alert.alert_data)
                self._warning_sent[meta_data['system_id']][metric_name] = False
                self._critical_sent[meta_data['system_id']][metric_name] = False
                critical_limiter.reset()
            elif current < critical_threshold and critical_sent:
                # We need to use previous here so that we don't get repetitive
                # alerts if this condition is met.

                alert = decreased_below_threshold_alert(
                    meta_data['system_name'], current, Severity.INFO.value,
                    meta_data['last_monitored'], Severity.CRITICAL.value,
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                data_for_alerting.append(alert.alert_data)
                self.logger.debug("Successfully classified alert %s",
                                  alert.alert_data)
                self._critical_sent[meta_data['system_id']][metric_name] = False
                self._warning_sent[meta_data['system_id']][metric_name] = False
                critical_limiter.reset()
        elif warning_enabled:
            # This case would be triggered if only warning is enabled.

            if (warning_threshold <= current) and not warning_sent:
                alert = increased_above_threshold_alert(
                    meta_data['system_name'], current,
                    Severity.WARNING.value,
                    meta_data['last_monitored'], Severity.WARNING.value,
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                data_for_alerting.append(alert.alert_data)
                self.logger.debug("Successfully classified alert %s",
                                  alert.alert_data)
                self._warning_sent[meta_data['system_id']][
                    metric_name] = True
            elif current < warning_threshold and warning_sent:
                alert = decreased_below_threshold_alert(
                    meta_data['system_name'], current, Severity.INFO.value,
                    meta_data['last_monitored'], Severity.WARNING.value,
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                data_for_alerting.append(alert.alert_data)
                self.logger.debug("Successfully classified alert %s",
                                  alert.alert_data)
                self._warning_sent[meta_data['system_id']][
                    metric_name] = False
        elif critical_enabled:
            # This case would be triggered if only critical is enabled

            if critical_threshold <= current:
                # We want to send a critical alert if no critical alert was
                # sent yet, or repeating is enabled and the repeating threshold
                # has been exceeded
                if not critical_sent or (
                        critical_repeat_enabled and
                        critical_limiter.can_do_task(monitoring_datetime)):
                    alert = increased_above_threshold_alert(
                        meta_data['system_name'], current,
                        Severity.CRITICAL.value,
                        meta_data['last_monitored'], Severity.CRITICAL.value,
                        meta_data['system_parent_id'], meta_data['system_id']
                    )
                    data_for_alerting.append(alert.alert_data)
                    self.logger.debug("Successfully classified alert %s",
                                      alert.alert_data)
                    critical_limiter.set_last_time_that_did_task(
                        monitoring_datetime)
                    self._critical_sent[meta_data['system_id']][
                        metric_name] = True
            elif current < critical_threshold and critical_sent:
                alert = decreased_below_threshold_alert(
                    meta_data['system_name'], current, Severity.INFO.value,
                    meta_data['last_monitored'], Severity.CRITICAL.value,
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                data_for_alerting.append(alert.alert_data)
                self.logger.debug("Successfully classified alert %s",
                                  alert.alert_data)
                self._critical_sent[meta_data['system_id']][
                    metric_name] = False
                critical_limiter.reset()

    def _place_latest_data_on_queue(self, data_list: List) -> None:
        # Place the latest alert data on the publishing queue. If the
        # queue is full, remove old data.
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
