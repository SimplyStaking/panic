import logging
from datetime import timedelta
from typing import List

import pika
import pika.exceptions

from alerter.src.utils.logging import DUMMY_LOGGER
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
        if not self.is_connected:
            self._logger.info('Connected with RabbitMQ again.')
        self._is_connected = True

    def _set_as_disconnected(self) -> None:
        if self.is_connected or self._live_check_limiter.can_do_task():
            self._live_check_limiter.did_task()
            self._logger.critical('Connection with RabbitMQ is down for some '
                                  'reason. Stopping usage temporarily to '
                                  'improve performance.')
        self._is_connected = False

    def _do_not_use_if_recently_disconnected(self) -> bool:
        return not self.is_connected and not self._live_check_limiter\
            .can_do_task()

    def _safe(self, function, args: List, default_return):
        try:
            if self._do_not_use_if_recently_disconnected():
                return default_return
            ret = function(*args)
            self._set_as_connected()
            return ret
        except pika.exceptions.AMQPChannelError as e:
            # Channel errors do not always reflect a connection error
            self._logger.error('RabbitMQ error in %s: %s', function.__name__, e)
            return default_return
        except Exception as e:
            # TODO: Need to test if Pika exceptions fall into this category
            print(e) # TODO: Why errors not outputted?
            self._logger.error('RabbitMQ error in %s: %s', function.__name__, e)
            self._set_as_disconnected()
            return default_return

    def connect_unsafe(self) -> None:
        self._logger.info('Connecting with RabbitMQ...')
        if self._password == '':
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self._host))
            self._channel = self._connection.channel()
        else:
            # TODO: Need to test authentication
            credentials = pika.PlainCredentials(self._username, self._password)
            parameters = pika.ConnectionParameters(
                self._host, self._port, '/', credentials)
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
        self._set_as_connected()

    # Returns the default value on error, otherwise returns 0
    # TODO: Need to test this function to the whole with errors etc. When
    #     : connection is good all seems ok. Need to test when service offline,
    #     : and connection closes (this must be tested by a publish or something)
    def connect(self, default=-1) -> int:
        ret = self._safe(self.connect_unsafe, [], default)
        if ret == default:
            self._logger.info(
                'Connection could not be established with RabbitMQ')
            return default
        else:
            self._logger.info('Successfully connected with RabbitMQ')
            return 0

    def disconnect(self) -> None:
        # TODO: Need to check if connection still open first, and do not forget
        #       to disconnect
        # def close_connection(self): this is repo code
        #     self._consuming = False
        #     if self._connection.is_closing or self._connection.is_closed:
        #         LOGGER.info('Connection is closing or already closed')
        #     else:
        #         LOGGER.info('Closing connection')
        #         self._connection.close()
        return None

    # Connections and disconnecitons should be functions or their own
    # Each method should have a safe function to check that connection is not lost
    # Channel error we may need to reconnect
    # Need to test pass authentication
    # Logger, set_as live etc we used to do in the constructor before must be
    # set in connect and disconnect
    # Must do all qos, publisher confirms, everything that can be done, publish,
    # subscribe etc must be done in the wrapper
    # For now, no data should be raised to the outside, attempt re-connection here
    # In disconnect we need to test connection
    # TODO: Inline documentation


rabbitMQAPI = RabbitMQApi(DUMMY_LOGGER)
rabbitMQAPI.connect()
