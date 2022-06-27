import logging
import sys
from datetime import datetime
from multiprocessing import Process
from types import FrameType
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.publisher_subscriber import PublisherSubscriberComponent
from src.data_store.starters import (
    start_system_store, start_github_store, start_dockerhub_store,
    start_alert_store, start_chainlink_node_store, start_evm_node_store,
    start_cl_contract_store, start_monitorable_store, start_cosmos_node_store,
    start_cosmos_network_store, start_substrate_node_store,
    start_substrate_network_store
)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.names import (
    SYSTEM_STORE_NAME, GITHUB_STORE_NAME, DOCKERHUB_STORE_NAME,
    ALERT_STORE_NAME, CL_NODE_STORE_NAME, EVM_NODE_STORE_NAME,
    CL_CONTRACT_STORE_NAME, MONITORABLE_STORE_NAME, COSMOS_NODE_STORE_NAME,
    COSMOS_NETWORK_STORE_NAME, SUBSTRATE_NODE_STORE_NAME,
    SUBSTRATE_NETWORK_STORE_NAME
)
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME,
    HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY, PING_ROUTING_KEY, TOPIC)
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
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'",
                         DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.queue_declare(DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME, False,
                                    True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME,
                         HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.rabbitmq.queue_bind(DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME,
                                 HEALTH_CHECK_EXCHANGE, PING_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME)
        self.rabbitmq.basic_consume(DATA_STORES_MAN_HEARTBEAT_QUEUE_NAME,
                                    self._process_ping, True, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

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
        """
        This method starts the data stores in a separate process if they are not
        yet started or not alive. This must be done in case the manager
        restarts.
        :return: None
        """
        configuration = {
            SYSTEM_STORE_NAME: start_system_store,
            GITHUB_STORE_NAME: start_github_store,
            DOCKERHUB_STORE_NAME: start_dockerhub_store,
            ALERT_STORE_NAME: start_alert_store,
            COSMOS_NODE_STORE_NAME: start_cosmos_node_store,
            MONITORABLE_STORE_NAME: start_monitorable_store,
            CL_NODE_STORE_NAME: start_chainlink_node_store,
            EVM_NODE_STORE_NAME: start_evm_node_store,
            CL_CONTRACT_STORE_NAME: start_cl_contract_store,
            COSMOS_NETWORK_STORE_NAME: start_cosmos_network_store,
            SUBSTRATE_NODE_STORE_NAME: start_substrate_node_store,
            SUBSTRATE_NETWORK_STORE_NAME: start_substrate_network_store,
        }
        for store_name, store_starter in configuration.items():
            if store_name not in self._store_process_dict or not \
                    self._store_process_dict[store_name].is_alive():
                log_and_print("Attempting to start the {}.".format(
                    store_name), self.logger)
                transformer_process = Process(target=store_starter, args=())
                transformer_process.daemon = True
                transformer_process.start()
                self._store_process_dict[store_name] = transformer_process

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
