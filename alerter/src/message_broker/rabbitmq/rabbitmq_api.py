import logging
from datetime import timedelta
from typing import List, Optional, Union

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

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def host(self) -> str:
        return self._host

    @property
    def connection(self) -> Optional[pika.BlockingConnection]:
        return self._connection

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
        return self._live_check_limiter

    def _set_as_connected(self) -> None:
        if not self.is_connected:
            self.logger.info('Marking RabbitMQ connection as live.')
        self._is_connected = True

    def _set_as_disconnected(self) -> None:
        if self.is_connected or self.live_check_limiter.can_do_task():
            self.logger.info('Marking RabbitMQ connection as down.')
            self.live_check_limiter.did_task()
        self._is_connected = False

    def _do_not_use_if_recently_disconnected(self) -> bool:
        return not self.is_connected and not self.live_check_limiter \
            .can_do_task()

    def _safe(self, function, args: List, default_return):
        try:
            if self._do_not_use_if_recently_disconnected():
                self.logger.debug('RabbitMQ: Could not execute %s as RabbitMQ '
                                  'is temporarily unusable to improve '
                                  'performance', function.__name__)
                return default_return
            ret = function(*args)
            return ret
        except pika.exceptions.AMQPChannelError as e:
            # Channel errors do not always reflect a connection error, therefore
            # do not set as disconnected
            self.logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            # If the channel error closed the channel, open another channel from
            # the same connection
            if self.channel.is_closed:
                self.new_channel_unsafe()
            raise e
        except Exception as e:
            self.logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            if self.connection is not None:
                self.disconnect_unsafe()
            raise e

    def _connection_initialized(self) -> bool:
        # If a connection has already been initialized return true
        if self.connection is not None:
            return True
        # Otherwise throw a meaningful exception
        else:
            self.logger.info(ConnectionNotInitializedException(
                'RabbitMQ').message)
            raise ConnectionNotInitializedException('RabbitMQ')

    def connect_unsafe(self) -> None:
        if self.is_connected and self.connection.is_open:
            # Avoid creating a lot of connections to avoid memory issues
            self.logger.info('Already connected with RabbitMQ, no need to '
                             're-connect!')
        else:
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

    # Returns the default value on error, otherwise returns 0
    def connect(self) -> Optional[int]:
        return self._safe(self.connect_unsafe, [], -1)

    # Should not be used if connection has not yet been initialized
    def disconnect_unsafe(self) -> None:
        if self.is_connected and self.connection.is_open:
            self.logger.info('Closing connection with RabbitMQ')
            self.connection.close()
            self.logger.info('Connection with RabbitMQ closed. RabbitMQ '
                             'cannot be used temporarily to improve '
                             'performance')
            self._set_as_disconnected()
        elif not self.is_connected and self.connection.is_open:
            self.logger.info('Closing connection with RabbitMQ')
            self.connection.close()
            self.logger.info('Connection with RabbitMQ closed')
        elif self.is_connected and self.connection.is_closed:
            self.logger.info('Closing connection with RabbitMQ')
            self._set_as_disconnected()
            self.logger.info('Connection with RabbitMQ closed. RabbitMQ '
                             'cannot be used temporarily to improve '
                             'performance')
        else:
            self.logger.info('Already disconnected.')

    def disconnect(self) -> Optional[int]:
        if self._connection_initialized():
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
                self.logger.info('Attempting another connection')
                continue

    def queue_declare(self, queue, passive=False, durable=False,
                      exclusive=False, auto_delete=False) \
            -> Optional[Union[int, str]]:
        args = [queue, passive, durable, exclusive, auto_delete]
        if self._connection_initialized():
            return self._safe(self.channel.queue_declare, args, -1)

    def queue_bind(self, queue, exchange, routing_key=None) -> Optional[int]:
        args = [queue, exchange, routing_key]
        if self._connection_initialized():
            return self._safe(self.channel.queue_bind, args, -1)

    def basic_publish(self, exchange, routing_key, body, properties=None,
                      mandatory=False) -> Optional[int]:
        args = [exchange, routing_key, body, properties, mandatory]
        if self._connection_initialized():
            return self._safe(self.channel.basic_publish, args, -1)

    def basic_publish_confirm(self, exchange, routing_key, body,
                              properties=None, mandatory=False) \
            -> Optional[int]:
        try:
            return self.basic_publish(exchange, routing_key, body, properties,
                                      mandatory)
        except pika.exceptions.UnroutableError as e:
            raise MessageWasNotDeliveredException(e)

    def basic_consume(self, queue, on_message_callback, auto_ack=False,
                      exclusive=False, consumer_tag=None) -> Optional[int]:
        args = [queue, on_message_callback, auto_ack, exclusive, consumer_tag]
        if self._connection_initialized():
            return self._safe(self.channel.basic_consume, args, -1)

    def start_consuming(self) -> Optional[int]:
        if self._connection_initialized():
            return self._safe(self.channel.start_consuming, [], -1)

    def basic_ack(self, delivery_tag=0, multiple=False) -> Optional[int]:
        args = [delivery_tag, multiple]
        if self._connection_initialized():
            return self._safe(self.channel.basic_ack, args, -1)

    def basic_qos(self, prefetch_size=0, prefetch_count=0, global_qos=False) \
            -> Optional[int]:
        args = [prefetch_size, prefetch_count, global_qos]
        if self._connection_initialized():
            return self._safe(self.channel.basic_qos, args, -1)

    def exchange_declare(self, exchange, exchange_type='direct', passive=False,
                         durable=False, auto_delete=False, internal=False) \
            -> Optional[int]:
        args = [exchange, exchange_type, passive, durable, auto_delete,
                internal]
        if self._connection_initialized():
            return self._safe(self.channel.exchange_declare, args, -1)

    def confirm_delivery(self) -> Optional[int]:
        if self._connection_initialized():
            return self._safe(self.channel.confirm_delivery, [], -1)

    # Should not be used if connection has not yet been initialized
    def new_channel_unsafe(self) -> None:
        if self.channel.is_open:
            self.logger.info('Closing RabbitMQ Channel')
            self.channel.close()
        self.logger.info('Created a new RabbitMQ Channel')
        self._channel = self.connection.channel()

    def new_channel(self) -> Optional[int]:
        if self._connection_initialized():
            return self._safe(self.new_channel_unsafe, [], -1)

    # TODO: Inline documentation
