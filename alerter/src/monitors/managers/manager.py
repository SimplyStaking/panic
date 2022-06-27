import logging
import sys
from abc import ABC, abstractmethod
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.publisher_subscriber import \
    QueuingPublisherSubscriberComponent
from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants.monitorables import MonitorableType
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY,
    MONITORABLE_EXCHANGE)
from src.utils.logging import log_and_print


class MonitorsManager(QueuingPublisherSubscriberComponent, ABC):
    def __init__(self, logger: logging.Logger, name: str,
                 rabbitmq: RabbitMQApi) -> None:
        self._config_process_dict = {}
        self._name = name

        super().__init__(logger, rabbitmq)

    def __str__(self) -> str:
        return self.name

    @property
    def config_process_dict(self) -> Dict:
        return self._config_process_dict

    @property
    def name(self) -> str:
        return self._name

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def _send_heartbeat(self, data_to_send: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY, body=data_to_send,
            is_body_dict=True, properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

    @abstractmethod
    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    @abstractmethod
    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def start(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialise_rabbitmq()
        while True:
            try:
                self._send_data()
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    @abstractmethod
    def process_and_send_monitorable_data(
            self, base_chain: str, monitorable_type: MonitorableType) -> None:
        pass

    def process_and_send_monitorable_data_generic(
            self, base_chain: str, monitorable_type: MonitorableType) -> None:
        """
        This function processes the required monitorable data which is then
        sent to RabbitMQ. This is done by using the config process dict and
        formed based on the base chain and monitorable types parameters.
        :param base_chain: The name of the base chain that has monitorable data
        :param monitorable_type: The monitorable type to be sent
        """
        monitorable_data = {'manager_name': self._name, 'sources': []}
        for source, source_data in self.config_process_dict.items():
            if base_chain == source_data['base_chain']:
                monitorable_data['sources'].append({
                    'chain_id': source_data['parent_id'],
                    'chain_name': source_data['sub_chain'],
                    'source_id': source,
                    'source_name': source_data['source_name']
                })

        routing_key = '{}.{}'.format(base_chain, monitorable_type.value)
        self.send_monitorable_data(routing_key, monitorable_data)

    def send_monitorable_data(self, routing_key: str, data: Dict) -> None:
        """
        This function sends monitorable data to the monitorable RabbitMQ
        exchange
        :param routing_key: The routing key to use
        :param data: The data to be sent
        """
        properties = pika.spec.BasicProperties(delivery_mode=2)

        self._push_to_queue(data, MONITORABLE_EXCHANGE,
                            routing_key, properties)
        self._send_data()

        self.logger.debug("Sent monitorable data (%s) to '%s' exchange",
                          routing_key, MONITORABLE_EXCHANGE)

    # If termination signals are received, terminate all child process and
    # close the connection with rabbit mq before exiting
    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and any running monitors will be stopped "
                      "gracefully. Afterwards the {} process will exit."
                      .format(self, self), self.logger)
        self.disconnect_from_rabbit()

        for config_id, process_details in self.config_process_dict.items():
            log_and_print("Terminating the process of {}".format(config_id),
                          self.logger)
            process = process_details['process']
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
