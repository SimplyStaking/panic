import logging
import signal
import sys
from datetime import datetime
from multiprocessing import Process
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.publisher_subscriber import PublisherSubscriberComponent
from src.data_store.starters import (start_system_store, start_github_store,
                                     start_alert_store, start_config_store)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (HEALTH_CHECK_EXCHANGE, SYSTEM_STORE_NAME,
                                 GITHUB_STORE_NAME, ALERT_STORE_NAME,
                                 DATA_STORE_MAN_INPUT_QUEUE,
                                 DATA_STORE_MAN_INPUT_ROUTING_KEY,
                                 CONFIG_STORE_NAME)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class StoreManager(PublisherSubscriberComponent):
    def __init__(self, logger: logging.Logger, name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, rabbitmq)
        self._name = name
        self._store_process_dict = {}

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'", DATA_STORE_MAN_INPUT_QUEUE)
        self.rabbitmq.queue_declare(DATA_STORE_MAN_INPUT_QUEUE, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", DATA_STORE_MAN_INPUT_QUEUE,
                         HEALTH_CHECK_EXCHANGE,
                         DATA_STORE_MAN_INPUT_ROUTING_KEY)
        self.rabbitmq.queue_bind(DATA_STORE_MAN_INPUT_QUEUE,
                                 HEALTH_CHECK_EXCHANGE,
                                 DATA_STORE_MAN_INPUT_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          DATA_STORE_MAN_INPUT_QUEUE)
        self.rabbitmq.basic_consume(DATA_STORE_MAN_INPUT_QUEUE,
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
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.debug("Received %s", data)

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.name
            heartbeat['running_processes'] = []
            heartbeat['dead_processes'] = []
            for store_name, process in self._store_process_dict.items():
                if process.is_alive():
                    heartbeat['running_processes'].append(store_name)
                else:
                    heartbeat['dead_processes'].append(store_name)
                    process.join()  # Just in case, to release resources
            heartbeat['timestamp'] = datetime.now().timestamp()

            # Restart dead stores
            if len(heartbeat['dead_processes']) != 0:
                self._start_stores_processes()
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing %s", data)
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

    def _start_stores_processes(self) -> None:
        # Start each store in a separate process if it is not yet started or it
        # is not alive. This must be done in case of a restart of the manager.
        if SYSTEM_STORE_NAME not in self._store_process_dict or \
                not self._store_process_dict[SYSTEM_STORE_NAME].is_alive():
            log_and_print("Attempting to start the {}.".format(
                SYSTEM_STORE_NAME), self.logger)
            system_store_process = Process(target=start_system_store, args=())
            system_store_process.daemon = True
            system_store_process.start()
            self._store_process_dict[SYSTEM_STORE_NAME] = system_store_process

        if GITHUB_STORE_NAME not in self._store_process_dict or \
                not self._store_process_dict[GITHUB_STORE_NAME].is_alive():
            log_and_print("Attempting to start the {}.".format(
                GITHUB_STORE_NAME), self.logger)
            github_store_process = Process(target=start_github_store, args=())
            github_store_process.daemon = True
            github_store_process.start()
            self._store_process_dict[GITHUB_STORE_NAME] = github_store_process

        if ALERT_STORE_NAME not in self._store_process_dict or \
                not self._store_process_dict[ALERT_STORE_NAME].is_alive():
            log_and_print("Attempting to start the {}.".format(
                ALERT_STORE_NAME), self.logger)
            alert_store_process = Process(target=start_alert_store, args=())
            alert_store_process.daemon = True
            alert_store_process.start()
            self._store_process_dict[ALERT_STORE_NAME] = alert_store_process

        if CONFIG_STORE_NAME not in self._store_process_dict or \
                not self._store_process_dict[CONFIG_STORE_NAME].is_alive():
            log_and_print("Attempting to start the {}.".format(
                CONFIG_STORE_NAME), self.logger)
            config_store_process = Process(target=start_config_store, args=())
            config_store_process.daemon = True
            config_store_process.start()
            self._store_process_dict[CONFIG_STORE_NAME] = config_store_process

    def start(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialise_rabbitmq()
        while True:
            try:
                self._start_stores_processes()
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

    # If termination signals are received, terminate all child process and exit
    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print(
            "{} is terminating. Connections with RabbitMQ will be closed, and "
            "any running stores will be stopped gracefully. Afterwards the {} "
            "process will exit.".format(self, self), self.logger)
        self.disconnect_from_rabbit()

        for store, process in self._store_process_dict.items():
            log_and_print("Terminating the process of {}".format(store),
                          self.logger)
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _send_data(self, *args) -> None:
        """
        We are not implementing the _send_data function because wrt rabbit,
        the channel's manager only sends heartbeats.
        """
        pass
