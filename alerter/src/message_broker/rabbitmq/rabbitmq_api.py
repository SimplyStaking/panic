import json
import logging
import time
from datetime import timedelta
from typing import List, Optional, Union, Dict, Callable, Any

import pika
import pika.exceptions

from alerter.src.utils.exceptions import ConnectionNotInitializedException, \
    MessageWasNotDeliveredException
from alerter.src.utils.timing import TimedTaskLimiter


# The producer/consumer must perform the error handling himself. For example
# if a basic_publish fails with a connection error, the user must re-connect
# first. This had to be done because a producer/consumer may treat an error
# differently

class RabbitMQApi:
    def __init__(self, logger: logging.Logger, host: str = 'localhost',
                 port: int = 5672, username: str = '', password: str = '',
                 connection_check_time_interval: timedelta = timedelta(
                     seconds=60)) \
            -> None:
        self._logger = logger
        self._host = host
        self._connection = None
        # TODO: We may need two channels, one for outputting and one for
        #     : inputting. But it seems that this is not the case for now. If
        #     : this will be the case, error handling must be improved to cater
        #     : for two channels.
        self._channel = None
        self._port = port  # Port used by the AMQP 0-9-1 and 1.0 clients
        self._username = username
        self._password = password
        # The limiter will restrict usage of RabbitMQ whenever it is running
        # into problems so that recovery is faster.
        self._connection_check_limiter = TimedTaskLimiter(
            connection_check_time_interval)
        # A boolean variable which keeps track of the connection status with
        # RabbitMQ
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def host(self) -> str:
        return self._host

    @property
    def connection(self) -> Optional[pika.BlockingConnection]:
        return self._connection

    # The output type is Optional[pika.BlockingConnection.BlockingChannel].
    # Strangely, pika.BlockingConnection.BlockingChannel cannot be imported
    @property
    def channel(self):
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

    def _set_as_connected(self) -> None:
        if not self.is_connected:
            self.logger.info('RabbitMQ connection is live.')
        self._is_connected = True

    def _set_as_disconnected(self) -> None:
        if self.is_connected or self.live_check_limiter.can_do_task():
            self.logger.info('RabbitMQ is unusable right now. Stopping usage '
                             'temporarily to improve performance')
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
        try:
            if self._is_recently_disconnected():
                self.logger.debug('RabbitMQ: Could not execute %s as RabbitMQ '
                                  'is temporarily unusable to improve '
                                  'performance', function.__name__)
                return default_return
            ret = function(*args)
            return ret
        except pika.exceptions.AMQPChannelError as e:
            # Channel errors do not reflect a connection error, therefore
            # do not set as disconnected
            self.logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            # If the channel error closed the communication channel, open
            # another channel using the same connection
            if self.channel.is_closed:
                self.new_channel_unsafe()
            raise e
        except pika.exceptions.AMQPConnectionError as e:
            # For connection related errors, if a connection has been
            # initialized, disconnect and mark the connection as down.
            self.logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            if self.connection is not None:
                self.disconnect_unsafe()
            raise e
        except Exception as e:
            # For any other exception, if the connection is broken mark it as
            # down. Also, raise the exception. If connection is not broken, it
            # is up to the user of the class to close it if need be.
            self.logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            if self.connection is not None and self.connection.is_closed:
                self.disconnect_unsafe()
            raise e

    def _connection_initialized(self) -> bool:
        # If a connection has already been initialized return true, otherwise
        # throw a meaningful exception.
        if self.connection is not None:
            return True
        else:
            self.logger.info(ConnectionNotInitializedException(
                'RabbitMQ').message)
            raise ConnectionNotInitializedException('RabbitMQ')

    def connect_unsafe(self) -> None:
        if self.is_connected and self.connection.is_open:
            # If the connection status is 'connected' and the connection socket
            # is open do not re-connect to avoid memory issues.
            self.logger.info('Already connected with RabbitMQ, no need to '
                             're-connect!')
        else:
            # Open a new connection depending on whether authentication is
            # needed, and set the connection status as 'connected'
            self.logger.info('Connecting with RabbitMQ...')
            if self.password == '':
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host))
                self._channel = self.connection.channel()
            else:
                credentials = pika.PlainCredentials(self.username,
                                                    self.password)
                parameters = pika.ConnectionParameters(
                    self.host, self.port, '/', credentials)
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self.connection.channel()
            self.logger.info('Connected with RabbitMQ')
            self._set_as_connected()

    def connect(self) -> Optional[int]:
        return self._safe(self.connect_unsafe, [], -1)

    # Should not be used if connection has not yet been initialized
    def disconnect_unsafe(self) -> None:
        # If the connection is open, close it and mark connection as
        # disconnected to limit usage. Otherwise, just mark as disconnected to
        # try and limit usage.
        if self.connection.is_open:
            self.logger.info('Closing connection with RabbitMQ')
            self.connection.close()
            self.logger.info('Connection with RabbitMQ closed.')

        self._set_as_disconnected()

    def disconnect(self) -> Optional[int]:
        # Perform operation only if a connection has been initialized,
        # otherwise, this function will throw a not initialized exception
        if self._connection_initialized():
            return self._safe(self.disconnect_unsafe, [], -1)

    def connect_till_successful(self) -> None:
        # Try to connect until successful. All exceptions will be ignored in
        # this case.
        self.logger.info('Attempting to connect with RabbitMQ.')
        while True:
            try:
                # If function returns, the operation was successful, therefore
                # stop the loop
                self.perform_operation_till_successful(self.connect, [], -1)
                break
            except Exception:
                self.logger.info('Attempting another connection when '
                                 'RabbitMQ becomes usable again.')
                continue

    def disconnect_till_successful(self) -> None:
        # Try to disconnect until successful. All exceptions will be ignored in
        # this case.
        self.logger.info('Attempting to disconnect with RabbitMQ.')
        while True:
            try:
                # If function returns, the operation was successful, therefore
                # stop the loop
                self.perform_operation_till_successful(self.disconnect, [], -1)
                break
            except Exception:
                self.logger.info('Attempting another disconnection')
                continue

    def queue_declare(self, queue: str, passive: bool = False,
                      durable: bool = False, exclusive: bool = False,
                      auto_delete: bool = False) -> Optional[Union[int, str]]:
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        args = [queue, passive, durable, exclusive, auto_delete]
        if self._connection_initialized():
            return self._safe(self.channel.queue_declare, args, -1)

    def queue_bind(self, queue: str, exchange: str, routing_key: str = None) \
            -> Optional[int]:
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        args = [queue, exchange, routing_key]
        if self._connection_initialized():
            return self._safe(self.channel.queue_bind, args, -1)

    def basic_publish(self, exchange: str, routing_key: str,
                      body: Union[str, Dict, bytes], is_body_dict: bool = False,
                      properties: pika.spec.BasicProperties = None,
                      mandatory: bool = False) -> Optional[int]:
        # If the message to be published is a Dict, serialize to json first
        args = [exchange, routing_key,
                json.dumps(body) if is_body_dict else body,
                properties, mandatory]
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
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
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
            return self._safe(self.channel.basic_consume, args, -1)

    def start_consuming(self) -> Optional[int]:
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
            return self._safe(self.channel.start_consuming, [], -1)

    def basic_ack(self, delivery_tag: int = 0, multiple: bool = False) \
            -> Optional[int]:
        args = [delivery_tag, multiple]
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
            return self._safe(self.channel.basic_ack, args, -1)

    def basic_qos(self, prefetch_size: int = 0, prefetch_count: int = 0,
                  global_qos: bool = False) -> Optional[int]:
        args = [prefetch_size, prefetch_count, global_qos]
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
            return self._safe(self.channel.basic_qos, args, -1)

    def exchange_declare(self, exchange: str, exchange_type: str = 'direct',
                         passive: bool = False, durable: bool = False,
                         auto_delete: bool = False, internal: bool = False) \
            -> Optional[int]:
        args = [exchange, exchange_type, passive, durable, auto_delete,
                internal]
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
            return self._safe(self.channel.exchange_declare, args, -1)

    def confirm_delivery(self) -> Optional[int]:
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
            return self._safe(self.channel.confirm_delivery, [], -1)

    # Should not be used if connection has not yet been initialized
    def new_channel_unsafe(self) -> None:
        # If a channel is open, close it and create a new channel from the
        # current connection
        if self.channel.is_open:
            self.logger.info('Closing RabbitMQ Channel')
            self.channel.close()
        self.logger.info('Created a new RabbitMQ Channel')
        self._channel = self.connection.channel()

    def new_channel(self) -> Optional[int]:
        # Perform operation only if a connection has been initialized, if not,
        # this function will throw a ConnectionNotInitialized exception
        if self._connection_initialized():
            return self._safe(self.new_channel_unsafe, [], -1)

    # Perform an operation with sleeping period in between until successful
    @staticmethod
    def perform_operation_till_successful(function, args: List[Any],
                                          default_return: Any) -> None:
        while function(*args) == default_return:
            time.sleep(5)
