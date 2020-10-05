import logging
from datetime import timedelta
from typing import List, Optional

import pika
import pika.exceptions

from alerter.src.utils.timing import TimedTaskLimiter


class RabbitMQApi:
    def __init__(self, logger: logging.Logger, host: str = 'localhost',
                 port: int = 5672, username: str = '', password: str = '',
                 live_check_time_interval: timedelta = timedelta(seconds=60)) \
            -> None:
        self._logger = logger
        self._host = host
        self._connection = None
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
            raise e
        except Exception as e:
            self._logger.error('RabbitMQ error in %s: %r', function.__name__, e)
            self._logger.warning('Stopping RabbitMQ usage temporarily to '
                                 'improve performance.')
            # If the error did not close the connection, close the connection
            # and mark it as closed. Otherwise just mark it as closed
            if self._connection.is_open:
                self.disconnect()
            else:
                self._set_as_disconnected()
            raise e

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
    # TODO: Test when connection closes (this must be tested by a publish or
    #       something)
    def connect(self) -> Optional[int]:
        return self._safe(self.connect_unsafe, [], -1)

    def disconnect_unsafe(self) -> None:
        if self.is_connected and self._connection.is_open:
            self._logger.info('Closing connection with RabbitMQ')
            self._connection.close()
            self._set_as_disconnected()
            self._logger.info('Connection with RabbitMQ closed')
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

    # The producer/consumer must perform the error handling himself. For example
    # if a basic_publish fails with a connection error, the user must re-connect
    # first
    # Must do all qos, publisher confirms, everything that can be done, publish,
    # subscribe etc must be done in the wrapper
    # In consume we must pass a function from the outside
    # TODO: Inline documentation
