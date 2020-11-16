import copy
import json
import logging
from typing import Dict

import pika
import pika.exceptions
from src.alerter.alerters.alerter import Alerter
from src.configs.system_alerts import SystemAlertsConfig
from src.utils.exceptions import (
    ReceivedUnexpectedDataException, MessageWasNotDeliveredException
)
from src.utils.logging import log_and_print
from src.alerter.alerts.system_alerts import (
    OpenFileDescriptorsIncreasedAlert, OpenFileDescriptorsDecreasedAlert,
    OpenFileDescriptorsIncreasedAboveCriticalThresholdAlert,
    OpenFileDescriptorsIncreasedAboveWarningThresholdAlert,
    SystemCPUUsageIncreasedAlert, SystemCPUUsageDecreasedAlert,
    SystemCPUUsageIncreasedAboveCriticalThresholdAlert,
    SystemCPUUsageIncreasedAboveWarningThresholdAlert,
    SystemRAMUsageIncreasedAlert, SystemRAMUsageDecreasedAlert,
    SystemRAMUsageIncreasedAboveCriticalThresholdAlert,
    SystemRAMUsageIncreasedAboveWarningThresholdAlert,
    SystemStorageUsageIncreasedAlert, SystemStorageUsageDecreasedAlert,
    SystemStorageUsageIncreasedAboveCriticalThresholdAlert,
    SystemStorageUsageIncreasedAboveWarningThresholdAlert,
    ReceivedUnexpectedDataAlert, InvalidUrlAlert, SystemWentUpAt,
    SystemWentDownAt
)


class SystemAlerter(Alerter):
    def __init__(self, alerts_config_name: str,
                 system_alerts_config: SystemAlertsConfig,
                 logger: logging.Logger) -> None:
        super().__init__(alerts_config_name, logger)
        self._system_alerts_config = system_alerts_config
        self._down_time_counter = 0

    @property
    def alerts_configs(self) -> SystemAlertsConfig:
        return self._system_alerts_config

    def _initialize_alerter(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info('Creating \'alerter\' exchange')
        self.rabbitmq.exchange_declare(exchange='alerter',
                                       exchange_type='direct', passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.logger.info('Creating queue \'system_alerter_queue\'')
        self.rabbitmq.queue_declare('system_alerter_queue', passive=False,
                                    durable=True, exclusive=False,
                                    auto_delete=False)
        routing_key = 'alerter.system.' + self.alerts_configs.parent
        self.logger.info('Binding queue \'system_alerter_queue\' to exchange '
                         '\'alerter\' with routing key \'{}\''
                         ''.format(routing_key))
        self.rabbitmq.queue_bind(queue='system_alerter_queue',
                                 exchange='alerter',
                                 routing_key=routing_key)

        # Pre-fetch count is 10 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.info('Declaring consuming intentions')

        # Set producing configuration
        self.logger.info('Setting delivery confirmation on RabbitMQ channel')
        self.rabbitmq.confirm_delivery()
        self.logger.info('Creating \'alert_router\' exchange')
        self.rabbitmq.exchange_declare(exchange='alert_router',
                                       exchange_type='direct', passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_purge('system_alerter_queue')

    def _start_listening(self) -> None:
        self.rabbitmq.basic_consume(queue='system_alerter_queue',
                                    on_message_callback=self._process_data,
                                    auto_ack=False,
                                    exclusive=False,
                                    consumer_tag=None)
        self.rabbitmq.start_consuming()

    def _process_data(self,
                      ch: pika.adapters.blocking_connection.BlockingChannel,
                      method: pika.spec.Basic.Deliver,
                      properties: pika.spec.BasicProperties,
                      body: bytes) -> None:
        data_received = json.loads(body.decode())
        parsed_routing_key = method.routing_key.split('.')
        try:
            if self.alerts_configs.parent in parsed_routing_key:
                if 'result' in data_received:
                    metrics = data_received['result']['data']
                    self._process_results(data_received['result']['data'],
                                          data_received['result']['meta_data'])
                elif 'error' in data_received:
                    self._process_errors(data_received['error'])
                else:
                    raise ReceivedUnexpectedDataException(
                        '{}: _process_data'.format(self))
        except Exception as e:
            self.logger.error("Error when processing {}".format(data_received))
            self.logger.exception(e)

        # Send any data waiting in the publisher queue, if any
        try:
            self._send_data()
        except (pika.exceptions.AMQPChannelError,
                pika.exceptions.AMQPConnectionError) as e:
            # No need to acknowledge in this case as channel is closed. Logging
            # would have also been done by RabbitMQ.
            raise e
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise the exception so that the
            # message can be acknowledged and removed from the rabbit queue.
            # Note this message will still reside in the publisher queue.
            self.logger.exception(e)
        except Exception as e:
            # For any other exception acknowledge and raise it, so the
            # message is removed from the rabbit queue as this message will now
            # reside in the publisher queue
            self.rabbitmq.basic_ack(method.delivery_tag, False)
            raise e

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_errors(self, error_data: Dict) -> None:
        is_down = self.alerts_configs.system_is_down
        meta_data = error_data['meta_data']
        if int(error_data['code']) == 5008:
            alert = ReceivedUnexpectedDataAlert(
                error_data['message'], 'ERROR', meta_data['time'],
                meta_data['system_parent_id'], meta_data['system_id']
            )
            self._data_for_alerting = alert.alert_data
            self.logger.debug('Successfully classified alert {}'
                              ''.format(alert.alert_data))
            self._place_latest_data_on_queue()
        elif int(error_data['code']) == 5009:
            alert = InvalidUrlAlert(
                error_data['message'], 'ERROR', meta_data['time'],
                meta_data['system_parent_id'], meta_data['system_id']
            )
            self._data_for_alerting = alert.alert_data
            self.logger.debug('Successfully classified alert {}'
                              ''.format(alert.alert_data))
            self._place_latest_data_on_queue()
        elif int(error_data['code']) == 5004:
            if is_down['enabled']:
                current = int(error_data['went_down_at']['current'] or 0)
                previous = int(error_data['went_down_at']['previous'] or 0)
                difference = current-previous
                self._down_time_counter += difference
                if (int(is_down['warning_threshold']) < self._down_time_counter
                    < int(is_down['critical_threshold']) and
                        is_down['warning_enabled']):
                    alert = SystemWentDownAt(
                                self.alerts_configs.parent,
                                meta_data['system_name'],
                                self._down_time_counter, 'WARNING',
                                meta_data['time'],
                                meta_data['system_parent_id'],
                                meta_data['system_id']
                            )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                elif (self._down_time_counter >
                      int(is_down['critical_threshold'])
                      and is_down['critical_enabled']):
                    alert = SystemWentDownAt(
                        self.alerts_configs.parent,
                        meta_data['system_name'],
                        self._down_time_counter, 'CRITICAL',
                        meta_data['time'],
                        meta_data['system_parent_id'],
                        meta_data['system_id']
                    )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                else:
                    alert = SystemWentDownAt(
                        self.alerts_configs.parent,
                        meta_data['system_name'],
                        self._down_time_counter, 'INFO',
                        meta_data['time'],
                        meta_data['system_parent_id'],
                        meta_data['system_id']
                    )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
        else:
            raise ReceivedUnexpectedDataException(
                        '{}: _process_errors'.format(self))

    def _process_results(self, metrics: Dict, meta_data: Dict) -> None:
        open_fd = self.alerts_configs.open_file_descriptors
        cpu_use = self.alerts_configs.system_cpu_usage
        storage = self.alerts_configs.system_storage_usage
        ram_use = self.alerts_configs.system_ram_usage
        is_down = self.alerts_configs.system_is_down

        if is_down['enabled']:
            current = int(metrics['went_down_at']['current'] or 0)
            previous = int(metrics['went_down_at']['previous'] or 0)
            difference = current-previous
            self._down_time_counter = 0
            alert = SystemWentUpAt(
                        self.alerts_configs.parent,
                        meta_data['system_name'],
                        difference, 'INFO',
                        meta_data['timestamp'],
                        meta_data['system_parent_id'],
                        meta_data['system_id']
                    )
            self._data_for_alerting = alert.alert_data
            self.logger.debug('Successfully classified alert {}'
                              ''.format(alert.alert_data))
            self._place_latest_data_on_queue()

        if open_fd['enabled']:
            current = int(metrics['open_file_descriptors']['current'] or 0)
            previous = int(metrics['open_file_descriptors']['previous'] or 0)
            if current > previous:
                if (int(open_fd['warning_threshold']) < current <
                        int(open_fd['critical_threshold']) and
                        open_fd['warning_enabled']):
                    alert = \
                        OpenFileDescriptorsIncreasedAboveWarningThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'WARNING',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                elif (int(open_fd['critical_threshold']) < current and
                        open_fd['critical_enabled']):
                    alert = \
                      OpenFileDescriptorsIncreasedAboveCriticalThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'CRITICAL',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                else:
                    alert = \
                      OpenFileDescriptorsIncreasedAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'INFO',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
            elif current < previous:
                alert = OpenFileDescriptorsDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._data_for_alerting = alert.alert_data
                self.logger.debug('Successfully classified alert {}'
                                  ''.format(alert.alert_data))
                self._place_latest_data_on_queue()

        if storage['enabled']:
            current = int(metrics['system_storage_usage']['current'] or 0)
            previous = int(metrics['system_storage_usage']['previous'] or 0)
            if current > previous:
                if (int(storage['warning_threshold']) < current <
                        int(storage['critical_threshold']) and
                        storage['warning_enabled']):
                    alert = \
                        SystemStorageUsageIncreasedAboveWarningThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'WARNING',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                elif (int(storage['critical_threshold']) < current and
                        storage['critical_enabled']):
                    alert = \
                      SystemStorageUsageIncreasedAboveCriticalThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'CRITICAL',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                else:
                    alert = \
                      SystemStorageUsageIncreasedAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'INFO',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
            elif current < previous:
                alert = SystemStorageUsageDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._data_for_alerting = alert.alert_data
                self.logger.debug('Successfully classified alert {}'
                                  ''.format(alert.alert_data))
                self._place_latest_data_on_queue()

        if cpu_use['enabled']:
            current = int(metrics['system_cpu_usage']['current'] or 0)
            previous = int(metrics['system_cpu_usage']['previous'] or 0)
            if current > previous:
                if (int(cpu_use['warning_threshold']) < current <
                        int(cpu_use['critical_threshold']) and
                        cpu_use['warning_enabled']):
                    alert = \
                        SystemCPUUsageIncreasedAboveWarningThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'WARNING',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                elif (int(cpu_use['critical_threshold']) < current and
                        cpu_use['critical_enabled']):
                    alert = \
                      SystemCPUUsageIncreasedAboveCriticalThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'CRITICAL',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                else:
                    alert = \
                      SystemCPUUsageIncreasedAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'INFO',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
            elif current < previous:
                alert = SystemCPUUsageDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._data_for_alerting = alert.alert_data
                self.logger.debug('Successfully classified alert {}'
                                  ''.format(alert.alert_data))
                self._place_latest_data_on_queue()

        if ram_use['enabled']:
            current = int(metrics['system_cpu_usage']['current'] or 0)
            previous = int(metrics['system_cpu_usage']['previous'] or 0)
            if current > previous:
                if (int(ram_use['warning_threshold']) < current <
                        int(ram_use['critical_threshold']) and
                        ram_use['warning_enabled']):
                    alert = \
                        SystemRAMUsageIncreasedAboveWarningThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'WARNING',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                elif (int(ram_use['critical_threshold']) < current and
                        ram_use['critical_enabled']):
                    alert = \
                      SystemRAMUsageIncreasedAboveCriticalThresholdAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'CRITICAL',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
                else:
                    alert = \
                      SystemRAMUsageIncreasedAlert(
                            self.alerts_configs.parent,
                            meta_data['system_name'],
                            previous, current, 'INFO',
                            meta_data['timestamp'],
                            meta_data['system_parent_id'],
                            meta_data['system_id']
                        )
                    self._data_for_alerting = alert.alert_data
                    self.logger.debug('Successfully classified alert {}'
                                      ''.format(alert.alert_data))
                    self._place_latest_data_on_queue()
            elif current < previous:
                alert = SystemRAMUsageDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._data_for_alerting = alert.alert_data
                self.logger.debug('Successfully classified alert {}'
                                  ''.format(alert.alert_data))
                self._place_latest_data_on_queue()

    def _place_latest_data_on_queue(self) -> None:
        self.logger.debug("Adding alert data to the publishing queue ...")

        # Place the latest alert data on the publishing queue. If the
        # queue is full, remove old data.
        if self.publishing_queue.full():
            self.publishing_queue.get()
            self.publishing_queue.get()
        self.publishing_queue.put({
            'exchange': 'alert_router',
            'routing_key': 'alert.system',
            'data': copy.deepcopy(self.data_for_alerting)})

        self.logger.debug("Alert data added to the publishing queue "
                          "successfully.")

    def _alert_classifier_process(self) -> None:
        self._initialize_alerter()
        log_and_print('{} started.'.format(self), self.logger)
        while True:
            try:
                self._start_listening()
            except pika.exceptions.AMQPChannelError:
                # Error would have already been logged by RabbitMQ logger. If
                # there is a channel error, the RabbitMQ interface creates a
                # new channel, therefore perform another managing round without
                # sleeping
                continue
            except pika.exceptions.AMQPConnectionError as e:
                # Error would have already been logged by RabbitMQ logger.
                # Since we have to re-connect just break the loop.
                raise e
            except MessageWasNotDeliveredException as e:
                # Log the fact that the message could not be sent and re-try
                # another monitoring round without sleeping
                self.logger.exception(e)
                continue
            except Exception as e:
                self.logger.exception(e)
                raise e
