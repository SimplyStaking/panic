import json
import logging
from typing import Dict

import pika
import pika.exceptions
from src.alerter.alerters.alerter import Alerter
from src.configs.system_alerts import SystemAlertsConfig
from src.utils.logging import log_and_print
from src.utils.exceptions import MessageWasNotDeliveredException


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
        self.rabbitmq.queue_bind(queue='system_alerter_queue',
                                 exchange='alerter',
                                 routing_key='alerter.system.*')
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
            print(data_received)
            # THIS IS WHAT THE DATA SHOULD LOOK LIKE
            # 'result': {
            # 	'meta_data': '',
            # 	'data: {
            # 		'process_cpu_seconds_total': {result: 120, previous: 110 },
            # 		'process_memory_usage': {result: 120, previous: 110 },
            # 		'virtual_memory_usage': {result: 120, previous: 110 },
            # 		'open_file_descriptors': {result: 120, previous: 110 },
            # 		'system_cpu_usage': {result: 120, previous: 110 },
            # 		'system_ram_usage': {result: 120, previous: 110 },
            # 		'network_receive_bytes_total': {result: 120, previous: 110 },
            # 		'network_transmit_bytes_total': {result: 120, previous: 110 },
            # 		'disk_io_time_seconds_total': {result: 120, previous: 110 },
            # 		'network_transmit_bytes_per_second': {result: 120, previous: 110 },
            # 		'network_receive_bytes_per_second': {result: 120, previous: 110 },
            # 		'disk_io_time_seconds_in_interval': {result: 120, previous: 110 },
            # 	}
            # }
            # Process the received alerts and then send to router

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _send_data_to_alert_router(self) -> None:
        print("Sending processed data")
        
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
