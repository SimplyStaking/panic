import logging
from datetime import timedelta
from typing import List, Optional, Union

import pika
import pika.exceptions

from alerter.src.utils.exceptions import ConnectionNotInitializedException,\
    MessageWasNotDeliveredException
from alerter.src.utils.timing import TimedTaskLimiter


# The producer/consumer must perform the error handling himself. For example
# if a basic_publish fails with a connection error, the user must re-connect
# first. This had to be done because a producer/consumer may treat an error
# differently

class RabbitMQApi:
    def __init__(self, logger: logging.Logger, host: str = 'localhost',
                 port: int = 5672, username: str = '', password: str = '',
                 live_check_time_interval: timedelta = timedelta(seconds=60)) \
            -> None:
        self._logger = logger
        self._host = host
        self._connection = None
        # TODO: We may need two channels, one for outputting and one for
        #     : inputting. But it seems that this is not the case for now. If
        #     : this will be the case, error handling must be improved to cater
        #     : for two channels.
        self._channel = None
        self._port = port
        self._username = username
        self._password = password
        self._live_check_limiter = TimedTaskLimiter(live_check_time_interval)
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def _set_as_connected(self) -> None:
        self._is_connected = True

    def _set_as_disconnected(self) -> None:
        if self.is_connected or self._live_check_limiter.can_do_task():
            self._live_check_limiter.did_task()
        self._is_connected = False

    def _do_not_use_if_recently_disconnected(self) -> bool:
        return not self.is_connected and not self._live_check_limiter \
            .can_do_task()

    def _safe(self, function, args: List, default_return):
        try:
            if self._do_not_use_if_recently_disconnected():
                return default_return
            ret = function(*args)
            return ret
        except pika.exceptions.AMQPChannelError as e:
            # Channel errors do not always reflect a connection error, therefore
            # do not set as disconnected
            self._logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            # If the channel error closed the channel, open another channel from
            # the same connection
            if self._channel.is_closed:
                self._channel = self._connection.channel()
            raise e
        except Exception as e:
            self._logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            self.disconnect_unsafe()
            raise e

    def _execute_if_connection_initialized(self, function, args,
                                           default_return) -> Optional[int]:
        def connection_initialized() -> bool:
            # If a connection has already been initialized return true
            if self._connection is not None:
                return True
            # Otherwise throw a meaningful exception
            else:
                raise ConnectionNotInitializedException('RabbitMQ')

        # If a connection has already been initialized perform the operation,
        # otherwise throw the exception raised by _connection_is_initialized
        if connection_initialized():
            return self._safe(function, args, default_return)

    def connect_unsafe(self) -> None:
        if self.is_connected:
            # Avoid creating a lot of connections to avoid memory issues
            self._logger.info('Already connected with RabbitMQ, no need to '
                              're-connect!')
        else:
            self._logger.info('Connecting with RabbitMQ...')
            if self._password == '':
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self._host))
                self._channel = self._connection.channel()
            else:
                credentials = pika.PlainCredentials(self._username,
                                                    self._password)
                parameters = pika.ConnectionParameters(
                    self._host, self._port, '/', credentials)
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
            self._logger.info('Connected with RabbitMQ')
            self._set_as_connected()

    # Returns the default value on error, otherwise returns 0
    def connect(self) -> Optional[int]:
        return self._safe(self.connect_unsafe, [], -1)

    def disconnect_unsafe(self) -> None:
        if self.is_connected and self._connection.is_open:
            self._logger.info('Closing connection with RabbitMQ')
            self._connection.close()
            self._set_as_disconnected()
            self._logger.info('Connection with RabbitMQ closed. RabbitMQ '
                              'cannot be used temporarily to improve '
                              'performance')
        elif not self._is_connected and self._connection.is_open:
            self._logger.info('Closing connection with RabbitMQ')
            self._connection.close()
            self._logger.info('Connection with RabbitMQ closed')
        elif self._is_connected and self._connection.is_closed:
            self._logger.info('Marking connection with RabbitMQ as closed')
            self._set_as_disconnected()
            self._logger.info('Connection with RabbitMQ marked as closed. '
                              'RabbitMQ cannot be used temporarily to improve '
                              'performance')
        else:
            self._logger.info('Already disconnected.')

    # Should be called on open connections only
    def disconnect(self) -> Optional[int]:
        return self._safe(self.disconnect_unsafe, [], -1)

    def connect_till_successful(self) -> None:
        while True:
            try:
                ret = self.connect()
                # If None is returned, Rabbit is not experiencing issues,
                # therefore the API must have connected to Rabbit
                if ret is None:
                    break
            except Exception:
                continue

    def queue_declare(self, queue, passive=False, durable=False,
                      exclusive=False, auto_delete=False) \
            -> Optional[Union[int, str]]:
        args = [queue, passive, durable, exclusive, auto_delete]
        return self._execute_if_connection_initialized(
            self._channel.queue_declare, args, -1)

    def queue_bind(self, queue, exchange, routing_key=None) -> Optional[int]:
        args = [queue, exchange, routing_key]
        return self._execute_if_connection_initialized(self._channel.queue_bind,
                                                       args, -1)

    def basic_publish(self, exchange, routing_key, body, properties=None,
                      mandatory=False) -> Optional[int]:
        args = [exchange, routing_key, body, properties, mandatory]
        return self._execute_if_connection_initialized(
            self._channel.basic_publish, args, -1)

    def basic_publish_confirm(self, exchange, routing_key, body,
                              properties=None, mandatory=False) \
            -> Optional[int]:
        args = [exchange, routing_key, body, properties, mandatory]
        try:
            return self._execute_if_connection_initialized(
                self._channel.basic_publish, args, -1)
        except pika.exceptions.UnroutableError as e:
            raise MessageWasNotDeliveredException(e)

    def basic_consume(self, queue, on_message_callback, auto_ack=False,
                      exclusive=False, consumer_tag=None) -> Optional[int]:
        args = [queue, on_message_callback, auto_ack, exclusive, consumer_tag]
        return self._execute_if_connection_initialized(
            self._channel.basic_consume, args, -1)

    def start_consuming(self) -> Optional[int]:
        return self._execute_if_connection_initialized(
            self._channel.start_consuming, [], -1)

    def basic_ack(self, delivery_tag=0, multiple=False) -> Optional[int]:
        args = [delivery_tag, multiple]
        return self._execute_if_connection_initialized(self._channel.basic_ack,
                                                       args, -1)

    def basic_qos(self, prefetch_size=0, prefetch_count=0, global_qos=False) \
            -> Optional[int]:
        args = [prefetch_size, prefetch_count, global_qos]
        return self._execute_if_connection_initialized(self._channel.basic_qos,
                                                       args, -1)

    def exchange_declare(self, exchange, exchange_type='direct', passive=False,
                         durable=False, auto_delete=False, internal=False) \
            -> Optional[int]:
        args = [exchange, exchange_type, passive, durable, auto_delete,
                internal]
        return self._execute_if_connection_initialized(
            self._channel.exchange_declare, args, -1)

    def confirm_delivery(self) -> Optional[int]:
        return self._execute_if_connection_initialized(
            self._channel.confirm_delivery, [], -1)

    # TODO: Way to create a new channel based on the same connection
    # TODO: Add logging to all functions
    # TODO: Inline documentation
