import logging
import os
import signal
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from src.utils.constants import HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class MonitorsManager(ABC):
    def __init__(self, logger: logging.Logger, name: str):
        self._logger = logger
        self._config_process_dict = {}
        self._name = name

        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

        # Handle termination signals by stopping the manager gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def config_process_dict(self) -> Dict:
        return self._config_process_dict

    @property
    def name(self) -> str:
        return self._name

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '{}' exchange".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue 'github_monitors_manager_ping_queue'")
        self.rabbitmq.queue_declare('github_monitors_manager_ping_queue',
                                    False, True, False, False)
        self.logger.info("Binding queue 'github_monitors_manager_ping_queue' "
                         "to exchange '{}' with routing key "
                         "'ping'".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.queue_bind('github_monitors_manager_ping_queue',
                                 HEALTH_CHECK_EXCHANGE, 'ping')
        self.logger.info("Declaring consuming intentions on "
                         "'github_monitors_manager_ping_queue'")
        self.rabbitmq.basic_consume('github_monitors_manager_ping_queue',
                                    self._process_ping, True, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def _send_heartbeat(self, data_to_send: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.manager',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.info("Sent heartbeat to '{}' exchange".format(
            HEALTH_CHECK_EXCHANGE))

    @abstractmethod
    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.info("Received {}".format(data))

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.name
            heartbeat['running_processes'] = []
            heartbeat['dead_processes'] = []
            for _, process_details in self.config_process_dict.items():
                process = process_details['process']
                component_name = process_details['component_name']
                if process.is_alive():
                    heartbeat['running_processes'].append(component_name)
                else:
                    heartbeat['dead_processes'].append(component_name)
                    process.join()  # Just in case, to release resources
            heartbeat['timestamp'] = datetime.now().timestamp()
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing {}".format(data))
            self.logger.exception(e)
            return

        # Send heartbeat if processing was successful
        try:
            self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as there is no use in
            # re-trying to send a heartbeat
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it.
            raise e

    def manage(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialize_rabbitmq()
        while True:
            try:
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    # If termination signals are received, terminate all child process and
    # close the connection with rabbit mq before exiting
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and any running monitors will be stopped "
                      "gracefully. Afterwards the {} process will exit."
                      .format(self, self), self.logger)
        self.rabbitmq.disconnect_till_successful()

        for config_id, process in self.config_process_dict.items():
            log_and_print("Terminating the process of {}".format(config_id),
                          self.logger)
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
