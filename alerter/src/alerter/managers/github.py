import logging
import sys
import copy
from datetime import datetime
from multiprocessing import Process
from types import FrameType
from typing import Dict

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerter_starters import start_github_alerter
from src.alerter.managers.manager import AlertersManager
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (HEALTH_CHECK_EXCHANGE, GITHUB_ALERTER_NAME,
                                 GITHUB_MANAGER_INPUT_QUEUE,
                                 GITHUB_MANAGER_INPUT_ROUTING_KEY,
                                 ALERT_EXCHANGE,
                                 ALERT_ROUTER_GITHUB_ROUTING_KEY)
from src.alerter.alerts.internal_alerts import (ComponentReset)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print


class GithubAlerterManager(AlertersManager):
    def __init__(self, logger: logging.Logger, name: str,
                 rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, name, rabbitmq)
        self._alerter_process_dict = {}

    @property
    def alerter_process_dict(self) -> Dict:
        return self._alerter_process_dict

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare exchange to send data to
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(exchange=ALERT_EXCHANGE,
                                       exchange_type='topic', passive=False,
                                       durable=True, auto_delete=False,
                                       internal=False)

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'", GITHUB_MANAGER_INPUT_QUEUE)
        self.rabbitmq.queue_declare(GITHUB_MANAGER_INPUT_QUEUE, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", GITHUB_MANAGER_INPUT_QUEUE,
                         HEALTH_CHECK_EXCHANGE,
                         GITHUB_MANAGER_INPUT_ROUTING_KEY)
        self.rabbitmq.queue_bind(GITHUB_MANAGER_INPUT_QUEUE,
                                 HEALTH_CHECK_EXCHANGE,
                                 GITHUB_MANAGER_INPUT_ROUTING_KEY)
        self.logger.info("Declaring consuming intentions on '%s'",
                         GITHUB_MANAGER_INPUT_QUEUE)
        self.rabbitmq.basic_consume(GITHUB_MANAGER_INPUT_QUEUE,
                                    self._process_ping, True, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel.")
        self.rabbitmq.confirm_delivery()

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
            for alerter_name, process in self.alerter_process_dict.items():
                if process.is_alive():
                    heartbeat['running_processes'].append(alerter_name)
                else:
                    heartbeat['dead_processes'].append(alerter_name)
                    process.join()  # Just in case, to release resources
            heartbeat['timestamp'] = datetime.now().timestamp()

            # Restart dead transformers
            if len(heartbeat['dead_processes']) != 0:
                self._start_alerters_processes()
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

    def _start_alerters_processes(self) -> None:
        """
        Start the system data transformer in a separate process if it is not
        yet started or it is not alive. This must be done in case of a
        restart of the manager.
        """
        if GITHUB_ALERTER_NAME not in self.alerter_process_dict or \
                not self.alerter_process_dict[GITHUB_ALERTER_NAME].is_alive():
            log_and_print("Attempting to start the {}.".format(
                GITHUB_ALERTER_NAME), self.logger)
            github_alerter_process = Process(target=start_github_alerter,
                                             args=())
            github_alerter_process.daemon = True
            github_alerter_process.start()
            self._alerter_process_dict[GITHUB_ALERTER_NAME] = \
                github_alerter_process

            """
            We must clear out all the metrics which are found in REDIS,
            sending this alert to the data store will achieve this.
            """
            alert = ComponentReset(type(self).__name__,
                                   datetime.now().timestamp(),
                                   type(self).__name__,
                                   type(self).__name__)
            self._push_latest_data_to_queue_and_send(alert.alert_data)

    def start(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialise_rabbitmq()
        while True:
            try:
                self._start_alerters_processes()
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
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and any running github alerters will be "
                      "stopped gracefully. Afterwards the {} process will "
                      "exit.".format(self, self), self.logger)

        for alerter, process in self.alerter_process_dict.items():
            log_and_print("Terminating the process of {}".format(alerter),
                          self.logger)
            process.terminate()
            process.join()
            alert = ComponentReset(type(self).__name__,
                                   datetime.now().timestamp(),
                                   type(self).__name__,
                                   type(self).__name__)
            self._push_latest_data_to_queue_and_send(alert.alert_data)

        self.disconnect_from_rabbit()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    # The GitHub Alerters Manager does not listen for configs
    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def _push_latest_data_to_queue_and_send(self, alert: Dict) -> None:
        self._push_to_queue(
            data=copy.deepcopy(alert), exchange=ALERT_EXCHANGE,
            routing_key=ALERT_ROUTER_GITHUB_ROUTING_KEY,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True
        )
        self._send_data()
