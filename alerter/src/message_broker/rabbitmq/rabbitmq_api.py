import json
import logging
import time
from datetime import timedelta
from typing import List, Optional, Union, Dict, Callable, Any, Sequence

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.utils.exceptions import (ConnectionNotInitialisedException,
                                  MessageWasNotDeliveredException,
                                  BlankCredentialException)
from src.utils.strings import strip_if_not_none
from src.utils.timing import TimedTaskLimiter


# The producer/consumer must perform the error handling himself. For example
# if a basic_publish fails with a connection error, the user must re-connect
# first. This had to be done because a producer/consumer may treat an error
# differently
class RabbitMQApi:
    def __init__(self, logger: logging.Logger, host: str = 'localhost',
                 port: int = 5672, username: str = '', password: str = '',
                 connection_check_time_interval: timedelta = timedelta(
                     seconds=30)) \
            -> None:
        self._logger = logger
        self._host = host
        self._connection = None
        self._channel = None
        self._port = port  # Port used by the AMQP 0-9-1 and 1.0 clients
        self._username = username
        self._password = password
        # The limiter will restrict usage of RabbitMQ whenever it is running
        # into problems so that recovery is faster.
        self._connection_check_limiter = TimedTaskLimiter(
            connection_check_time_interval)
        self._connection_check_time_interval_seconds = \
            connection_check_time_interval.total_seconds()
        # A boolean variable which keeps track of the connection status with
        # RabbitMQ
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def host(self) -> str:
        return self._host

    @property
    def connection(self) -> Optional[pika.BlockingConnection]:
        return self._connection

    @property
    def channel(self) -> Optional[BlockingChannel]:
        return self._channel

    @property
    def port(self) -> int:
        return self._port

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def live_check_limiter(self) -> TimedTaskLimiter:
        return self._connection_check_limiter

    @property
    def connection_check_time_interval_seconds(self) -> float:
        return self._connection_check_time_interval_seconds

    def _set_as_connected(self) -> None:
        if not self.is_connected:
            self._logger.info("RabbitMQ connection is live.")
        self._is_connected = True

    def _set_as_disconnected(self) -> None:
        if self.is_connected or self.live_check_limiter.can_do_task():
            self._logger.info("RabbitMQ is unusable right now. Stopping usage "
                              "temporarily to improve performance.")
            self.live_check_limiter.did_task()
        self._is_connected = False

    def _is_recently_disconnected(self) -> bool:
        # If currently not connected with RabbitMQ and cannot check the
        # connection status return true
        return not self.is_connected and not self.live_check_limiter \
            .can_do_task()

    def _safe(self, function, args: List[Any], default_return: Any):
        # Calls the function with the provided arguments and performs exception
        # handling as well as returns a specified default if RabbtiMQ is running
        # into difficulties. Exceptions are raised to the calling function.
        ERROR_MESSAGE_TEMPALTE = "RabbitMQ error in %s: %r"
        try:
            if self._is_recently_disconnected():
                self._logger.debug("RabbitMQ: Could not execute %s as RabbitMQ "
                                   "is temporarily unusable to improve "
                                   "performance", function.__name__)
                return default_return
            ret = function(*args)
            return ret
        except pika.exceptions.UnroutableError as e:
            # Unroutable errors should be logged and raised
            self._logger.error(ERROR_MESSAGE_TEMPALTE, function.__name__, e)
            raise e
        except pika.exceptions.AMQPChannelError as e:
            # Channel errors do not reflect a connection error, therefore
            # do not set as disconnected
            self._logger.error(ERROR_MESSAGE_TEMPALTE, function.__name__, e)
            # On a channel error, create a new channel
            self.new_channel_unsafe()
            raise e
        except pika.exceptions.AMQPConnectionError as e:
            # For connection related errors, if a connection has been
            # initialised, disconnect and mark the connection as down.
            self._logger.error(ERROR_MESSAGE_TEMPALTE, function.__name__, e)
            if self.connection is not None:
                self.disconnect_unsafe()
            raise e
        except Exception as e:
            # For any other exception, if the connection is broken mark it as
            # down. Also, raise the exception. If connection is not broken, it
            # is up to the user of the class to close it if need be.
            self._logger.error(ERROR_MESSAGE_TEMPALTE, function.__name__, e)
            if self.connection is not None and self.connection.is_closed:
                self.disconnect_unsafe()
            raise e

    def _connection_initialised(self) -> bool:
        # If a connection has already been initialised return true, otherwise
        # throw a meaningful exception.
        if self.connection is not None:
            return True
        else:
            self._logger.info(ConnectionNotInitialisedException(
                'RabbitMQ').message)
            raise ConnectionNotInitialisedException('RabbitMQ')

    def connect_unsafe(self) -> None:
        if self.is_connected and self.connection.is_open:
            # If the connection status is 'connected' and the connection socket
            # is open do not re-connect to avoid memory issues.
            self._logger.info("Already connected with RabbitMQ, no need to "
                              "re-connect!")
        else:
            # Open a new connection depending on whether authentication is
            # needed, and set the connection status as 'connected'
            self._logger.info("Connecting with RabbitMQ...")
            stripped_credentials = {
                'username': strip_if_not_none(self.username),
                'password': strip_if_not_none(self.password)
            }
            if not (stripped_credentials['username'] or stripped_credentials[
                'password']):
                # If both are blank/none/spaces:
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host))
                self._channel = self.connection.channel()
            elif stripped_credentials['username'] and stripped_credentials[
                'password']:
                # Else if neither is blank/none/spaces
                credentials = pika.PlainCredentials(
                    self.username, self.password
                )
                parameters = pika.ConnectionParameters(
                    self.host, self.port, '/', credentials
                )
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self.connection.channel()
            else:
                # Error case if exactly one of them is blank/none/spaces:
                blank_credentials = []
                for label, credential in stripped_credentials.items():
                    if not credential:
                        blank_credentials.append(label)
                raise BlankCredentialException(blank_credentials)
            self._logger.info("Connected with RabbitMQ")
            self._set_as_connected()

    def connect(self) -> Optional[int]:
        return self._safe(self.connect_unsafe, [], -1)

    # Should not be used if connection has not yet been initialised
    def disconnect_unsafe(self) -> None:
        # If the connection is open, close it and mark connection as
        # disconnected to limit usage. Otherwise, just mark as disconnected to
        # try and limit usage.
        if self.connection.is_open:
            self._logger.info("Closing connection with RabbitMQ.")
            self.connection.close()
            self._logger.info("Connection with RabbitMQ closed.")

        self._set_as_disconnected()

    def disconnect(self) -> Optional[int]:
        # Perform operation only if a connection has been initialised,
        # otherwise, this function will throw a not initialised exception
        if self._connection_initialised():
            return self._safe(self.disconnect_unsafe, [], -1)

    def connect_till_successful(self) -> None:
        # Try to connect until successful. All exceptions will be ignored in
        # this case.
        self._logger.info("Attempting to connect with RabbitMQ.")
        while True:
            try:
                # If function returns, the operation was successful, therefore
                # stop the loop
                self.perform_operation_till_successful(self.connect, [], -1)
                break
            except Exception as e:
                self._logger.exception(e)
                self._logger.info("Could not connect. Will attempt to connect "
                                  "in %s seconds",
                                  self.connection_check_time_interval_seconds)
                time.sleep(self.connection_check_time_interval_seconds)
                self._logger.info("Attempting another connection ...")
                continue

    def disconnect_till_successful(self) -> None:
        # Try to disconnect until successful. All exceptions will be ignored in
        # this case.
        self._logger.info("Attempting to disconnect with RabbitMQ.")
        while True:
            try:
                # If function returns, the operation was successful, therefore
                # stop the loop
                self.perform_operation_till_successful(self.disconnect, [], -1)
                break
            except ConnectionNotInitialisedException:
                self._logger.info("No need to disconnect as no connection was "
                                  "initialise with Rabbit.")
                break
            except Exception as e:
                self._logger.exception(e)
                self._logger.info("Could not disconnect. Will attempt to "
                                  "disconnect in %s seconds",
                                  self.connection_check_time_interval_seconds)
                time.sleep(self.connection_check_time_interval_seconds)
                self._logger.info("Attempting another disconnection ...")
                continue

    def queue_declare(self, queue: str, passive: bool = False,
                      durable: bool = False, exclusive: bool = False,
                      auto_delete: bool = False) -> Optional[Union[int, str]]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        args = [queue, passive, durable, exclusive, auto_delete]
        if self._connection_initialised():
            return self._safe(self.channel.queue_declare, args, -1)

    def queue_bind(self, queue: str, exchange: str, routing_key: str = None) \
            -> Optional[int]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        args = [queue, exchange, routing_key]
        if self._connection_initialised():
            return self._safe(self.channel.queue_bind, args, -1)

    def basic_publish(self, exchange: str, routing_key: str,
                      body: Union[str, Dict, bytes], is_body_dict: bool = False,
                      properties: pika.spec.BasicProperties = None,
                      mandatory: bool = False) -> Optional[int]:
        # If the message to be published is a Dict, serialize to json first
        args = [exchange, routing_key,
                json.dumps(body) if is_body_dict else body,
                properties, mandatory]
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.basic_publish, args, -1)

    def basic_publish_confirm(self, exchange: str, routing_key: str,
                              body: Union[str, Dict, bytes],
                              is_body_dict: bool = False,
                              properties: pika.spec.BasicProperties = None,
                              mandatory: bool = False) -> Optional[int]:
        # Attempt a publish and wait until a message is sent to an exchange. If
        # mandatory is set to true, this function will block until the consumer
        # receives the message. Note: self.confirm_delivery() must be called
        # once on a channel for this function to work as expected.
        try:
            return self.basic_publish(exchange, routing_key, body, is_body_dict,
                                      properties, mandatory)
        except pika.exceptions.UnroutableError as e:
            # If a message is not delivered, the exception below is raised.
            raise MessageWasNotDeliveredException(e)

    def basic_consume(self, queue: str, on_message_callback: Callable,
                      auto_ack: bool = False, exclusive: bool = False,
                      consumer_tag: str = None) -> Optional[int]:
        args = [queue, on_message_callback, auto_ack, exclusive, consumer_tag]
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.basic_consume, args, -1)

    def basic_get(self, queue: str, auto_ack: bool = False) -> Optional[int]:
        args = [queue, auto_ack]
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.basic_get, args, -1)

    def start_consuming(self) -> Optional[int]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.start_consuming, [], -1)

    def basic_ack(self, delivery_tag: int = 0, multiple: bool = False) \
            -> Optional[int]:
        args = [delivery_tag, multiple]
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.basic_ack, args, -1)

    def basic_qos(self, prefetch_size: int = 0, prefetch_count: int = 0,
                  global_qos: bool = False) -> Optional[int]:
        args = [prefetch_size, prefetch_count, global_qos]
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.basic_qos, args, -1)

    def exchange_declare(self, exchange: str, exchange_type: str = 'direct',
                         passive: bool = False, durable: bool = False,
                         auto_delete: bool = False, internal: bool = False) \
            -> Optional[int]:
        args = [exchange, exchange_type, passive, durable, auto_delete,
                internal]
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.exchange_declare, args, -1)

    def confirm_delivery(self) -> Optional[int]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.channel.confirm_delivery, [], -1)

    def queue_purge(self, queue: str) -> Optional[int]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        args = [queue]
        if self._connection_initialised():
            return self._safe(self.channel.queue_purge, args, -1)

    def exchange_delete(self, exchange: str = None,
                        if_unused: bool = False) -> Optional[int]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        args = [exchange, if_unused]
        if self._connection_initialised():
            return self._safe(self.channel.exchange_delete, args, -1)

    def queue_delete(self, queue: str, if_unused: bool = False,
                     if_empty: bool = False) -> Optional[int]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        args = [queue, if_unused, if_empty]
        if self._connection_initialised():
            return self._safe(self.channel.queue_delete, args, -1)

    # Should not be used if connection has not yet been initialised
    def new_channel_unsafe(self) -> None:
        # If a channel is open, close it and create a new channel from the
        # current connection
        if self.channel.is_open:
            self._logger.info("Closing RabbitMQ Channel")
            self.channel.close()
        self._logger.info("Created a new RabbitMQ Channel")
        self._channel = self.connection.channel()

    def new_channel(self) -> Optional[int]:
        # Perform operation only if a connection has been initialised, if not,
        # this function will throw a ConnectionNotInitialised exception
        if self._connection_initialised():
            return self._safe(self.new_channel_unsafe, [], -1)

    # Perform an operation with sleeping period in between until successful.
    # This function only works if no exceptions are raised, i.e. till RabbitMQ
    # becomes usable again
    def perform_operation_till_successful(self, function, args: Sequence,
                                          default_return: Any) -> None:
        while function(*args) == default_return:
            time.sleep(self.connection_check_time_interval_seconds)
