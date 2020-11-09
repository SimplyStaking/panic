import json
import logging
from typing import Dict

import pika
import pika.exceptions
from src.alerter.alerters.alerter import Alerter
from src.configs.system_alerts import SystemAlertsConfig
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.alerter.alerts.system_alerts import (
    MemoryUsageIncreasedAlert, MemoryUsageDecreasedAlert,
    MemoryUsageIncreasedAboveCriticalThresholdAlert,
    MemoryUsageIncreasedAboveWarningThresholdAlert,
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
    SystemNetworkUsageIncreasedAlert, SystemNetworkUsageDecreasedAlert,
    SystemNetworkUsageIncreasedAboveCriticalThresholdAlert,
    SystemNetworkUsageIncreasedAboveWarningThresholdAlert,
    ReceivedUnexpectedDataAlert, InvalidUrlAlert,
)


class SystemAlerter(Alerter):
    def __init__(self, alerts_config_name: str,
                 system_alerts_config: SystemAlertsConfig,
                 logger: logging.Logger) -> None:
        super().__init__(alerts_config_name, logger)
        self._system_alerts_config = system_alerts_config

    @property
    def alerts_configs(self) -> SystemAlertsConfig:
        return self._system_alerts_config

    def _initialize_alerter(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange='alerter',
                                       exchange_type='direct', passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare('system_alerter_queue', passive=False,
                                    durable=True, exclusive=False,
                                    auto_delete=False)
        routing_key = 'alerter.system.' + self.alerts_configs.parent
        self.rabbitmq.queue_bind(queue='system_alerter_queue',
                                 exchange='alerter',
                                 routing_key=routing_key)
        # TODO remove for production
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
        if self.alerts_configs.parent in parsed_routing_key:
            if 'result' in data_received:
                metrics = data_received['result']['data']
                self._process_results(data_received['result']['data'],
                                      data_received['result']['meta_data'])
            elif 'error' in data_received:
                self._process_errors(data_received)
            else:
                print("EXCEPTION")
        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_errors(self, error_data: Dict) -> None:
        meta = error_data['error']['meta_data']
        if int(error_data['error']['code']) == 5008:
            alert = ReceivedUnexpectedDataAlert(
                error_data['error']['message'], 'ERROR', meta['time'],
                meta['system_parent_id'], meta['system_id']
            )
            self._send_alert_to_alert_router(alert.alert_data)
        elif int(error_data['error']['code']) == 5009:
            alert = InvalidUrlAlert(
                error_data['error']['message'], 'ERROR', meta['time'],
                meta['system_parent_id'], meta['system_id']
            )
            self._send_alert_to_alert_router(alert.alert_data)
        else:
            print("EXCEPTION")

    def _process_results(self, metrics: Dict, meta_data: Dict) -> None:
        open_fd = self.alerts_configs.open_file_descriptors
        cpu_use = self.alerts_configs.system_cpu_usage
        storage = self.alerts_configs.system_storage_usage
        ram_use = self.alerts_configs.system_ram_usage
        net_use = self.alerts_configs.system_network_usage

        if open_fd['enabled']:
            current = float(metrics['open_file_descriptors']['current'])
            previous = float(metrics['open_file_descriptors']['previous'])
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
            elif current < previous:
                alert = OpenFileDescriptorsDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._send_alert_to_alert_router(alert.alert_data)

        if storage['enabled']:
            current = float(metrics['system_storage_usage']['current'])
            previous = float(metrics['system_storage_usage']['previous'])
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
            elif current < previous:
                alert = SystemStorageUsageDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._send_alert_to_alert_router(alert.alert_data)

        if cpu_use['enabled']:
            current = float(metrics['system_cpu_usage']['current'])
            previous = float(metrics['system_cpu_usage']['previous'])
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
            elif current < previous:
                alert = SystemCPUUsageDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._send_alert_to_alert_router(alert.alert_data)

        if ram_use['enabled']:
            current = float(metrics['system_cpu_usage']['current'])
            previous = float(metrics['system_cpu_usage']['previous'])
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
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
                    self._send_alert_to_alert_router(alert.alert_data)
            elif current < previous:
                alert = SystemRAMUsageDecreasedAlert(
                    self.alerts_configs.parent, meta_data['system_name'],
                    previous, current, 'INFO', meta_data['timestamp'],
                    meta_data['system_parent_id'], meta_data['system_id']
                )
                self._send_alert_to_alert_router(alert.alert_data)

        # if net_use['enabled']:
        #     current = float(metrics['system_network_usage']['current'])
        #     previous = float(metrics['system_network_usage']['previous'])
        #     if current > previous:
        #         if (int(ram_use['warning_threshold']) < current <
        #                 int(ram_use['critical_threshold']) and
        #                 ram_use['warning_enabled']):
        #             alert = \
        #                 SystemRAMUsageIncreasedAboveWarningThresholdAlert(
        #                     self.alerts_configs.parent,
        #                     meta_data['system_name'],
        #                     previous, current, 'WARNING',
        #                     meta_data['timestamp'],
        #                     meta_data['system_parent_id'],
        #                     meta_data['system_id']
        #                 )
        #             self._send_alert_to_alert_router(alert.alert_data)
        #         elif (int(ram_use['critical_threshold']) < current and
        #                 ram_use['critical_enabled']):
        #             alert = \
        #               SystemRAMUsageIncreasedAboveCriticalThresholdAlert(
        #                     self.alerts_configs.parent,
        #                     meta_data['system_name'],
        #                     previous, current, 'CRITICAL',
        #                     meta_data['timestamp'],
        #                     meta_data['system_parent_id'],
        #                     meta_data['system_id']
        #                 )
        #             self._send_alert_to_alert_router(alert.alert_data)
        #         else:
        #             alert = \
        #               SystemRAMUsageIncreasedAlert(
        #                     self.alerts_configs.parent,
        #                     meta_data['system_name'],
        #                     previous, current, 'INFO',
        #                     meta_data['timestamp'],
        #                     meta_data['system_parent_id'],
        #                     meta_data['system_id']
        #                 )
        #             self._send_alert_to_alert_router(alert.alert_data)
        #     elif current < previous:
        #         alert = SystemRAMUsageDecreasedAlert(
        #             self.alerts_configs.parent, meta_data['system_name'],
        #             previous, current, 'INFO', meta_data['timestamp'],
        #             meta_data['system_parent_id'], meta_data['system_id']
        #         )
        #         self._send_alert_to_alert_router(alert.alert_data)

    def _send_alert_to_alert_router(self, alert: Dict) -> None:
        log_and_print('{} started.'.format(alert), self.logger)

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
