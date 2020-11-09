import os
import json
import logging
from typing import Dict

import pika.exceptions
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.alerter.alerts.github_alerts import (
    NewGitHubReleaseAlert, CannotAccessGitHubPageAlert
)


class GithubAlerter:
    def __init__(self, logger: logging.Logger, alerter_name: str) -> None:
        self._alerter_name = alerter_name
        self._logger = logger
        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    def __str__(self) -> str:
        return self.alerter_name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def alerter_name(self) -> str:
        return self._alerter_name

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    def _initialize_alerter(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.rabbitmq.exchange_declare(exchange='alerter',
                                       exchange_type='direct', passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)
        self.rabbitmq.queue_declare('github_alerter_queue', passive=False,
                                    durable=True, exclusive=False,
                                    auto_delete=False)
        routing_key = 'alerter.github'
        self.rabbitmq.queue_bind(queue='github_alerter_queue',
                                 exchange='alerter',
                                 routing_key=routing_key)
        # TODO remove for production
        self.rabbitmq.queue_purge('github_alerter_queue')

    def _start_listening(self) -> None:
        self.rabbitmq.basic_consume(queue='github_alerter_queue',
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
        if 'result' in data_received:
            meta = data_received['result']['meta_data']
            data = data_received['result']['data']
            if (data['no_of_releases']['current'] !=
               data['no_of_releases']['previous']):
                for i in data['releases']:
                    alert = NewGitHubReleaseAlert(
                      meta['repo_name'], data['releases'][i]['release_name'],
                      data['releases'][i]['tag_name'], 'INFO',
                      meta['last_monitored'], meta['repo_parent_id'],
                      meta['repo_id']
                    )
        elif 'error' in data_received:
            meta_data = data_received['error']['meta_data']
            alert = CannotAccessGitHubPageAlert(
                        meta_data['repo_name'], 'ERROR',
                        meta_data['time'],
                        meta_data['repo_parent_id'], meta_data['repo_id']
                    )
            self._send_data(alert.alert_data)
        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _send_data(self, alert: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange='alert_router', routing_key='alert_router.github',
            body=alert,
            is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug('Sent data to \'alert_router\' exchange.')

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
