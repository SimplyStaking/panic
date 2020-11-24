import json
import logging
import os
import signal
import sys
from datetime import datetime
from types import FrameType

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis.redis_api import RedisApi
from src.data_store.redis.store_keys import Keys
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import HEALTH_CHECK_EXCHANGE
from src.utils.exceptions import ReceivedUnexpectedDataException
from src.utils.logging import log_and_print
from src.utils.types import RedisType


class HeartbeatHandler:
    def __init__(self, logger: logging.Logger, redis: RedisApi, name: str) \
            -> None:
        self._name = name
        self._logger = logger
        self._redis = redis

        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

        # This dict stores the keys-values that should have been stored to redis
        # but where not saved due to an error in redis. This is done so that the
        # heartbeats are saved eventually redis is back online
        self._unsavable_redis_data = {}

        # Handle termination signals by stopping the monitor gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        self.logger.info("Creating '{}' exchange".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue 'heartbeat_handler_queue'")
        self.rabbitmq.queue_declare('heartbeat_handler_queue', False, True,
                                    False, False)
        self.logger.info(
            "Binding queue 'heartbeat_handler_queue' to exchange '{}' with "
            "routing key 'heartbeat.*'".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.queue_bind('heartbeat_handler_queue',
                                 HEALTH_CHECK_EXCHANGE, 'heartbeat.*')

        # Pre-fetch count is set to 300
        prefetch_count = round(300)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.info("Declaring consuming intentions")
        self.rabbitmq.basic_consume('heartbeat_handler_queue',
                                    self._process_heartbeat, False, False, None)

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def _save_to_redis_and_add_to_state_if_fail(
            self, key: str, value: RedisType) -> None:
        self.logger.debug('Saving %s=%s to Redis', key, value)
        ret = self.redis.set(key, value)

        # If None is returned it means that saving failed. Therefore store
        # this in the dict. If execution reaches the second condition it means
        # that saving was successful. Therefore remove the key from the dict if
        # it is present.
        if ret is None:
            self.logger.error('Could not save %s=%s to Redis. Storing it in '
                              'state so that it can be saved later.',
                              key, value)
            self._unsavable_redis_data[key] = value
        elif key in self._unsavable_redis_data:
            self.logger.debug('Removing %s=%s from state', key, value)
            del self._unsavable_redis_data[key]

        self.logger.debug('Successfully saved %s=%s to Redis', key, value)

    def _dump_unsavable_redis_data(self) -> None:
        if len(self._unsavable_redis_data) == 0:
            return

        self.logger.debug('Attempting to save data that was not able to be '
                          'saved to redis.')
        for key, value in self._unsavable_redis_data.items():
            ret = self.redis.set(key, value)
            if ret is not None:
                self.logger.debug('Removing %s=%s from state', key, value)
                del self._unsavable_redis_data[key]

        if len(self._unsavable_redis_data) == 0:
            self.logger.info('Successfully saved all redis data in waiting '
                             'state.')
        else:
            self.logger.debug('Could not save all data to Redis.')

    def _process_heartbeat(self, ch: BlockingChannel,
                           method: pika.spec.Basic.Deliver,
                           properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        heartbeat = json.loads(body)
        self.logger.info("Received {}. Now processing this data.".format(
            heartbeat))

        try:
            if method.routing_key == 'heartbeat.worker' or \
                    method.routing_key == 'heartbeat.manager':
                component_name = heartbeat['component_name']

                key_heartbeat = Keys.get_component_heartbeat(component_name)
                transformed_heartbeat = json.dumps(heartbeat)
                self._save_to_redis_and_add_to_state_if_fail(
                    key_heartbeat, transformed_heartbeat)

                self._dump_unsavable_redis_data()

                self.logger.info("Successfully processed {}".format(heartbeat))
            else:
                raise ReceivedUnexpectedDataException(
                    "{}: _process_heartbeat".format(self))
        except Exception as e:
            self.logger.error("Error when processing {}".format(heartbeat))
            self.logger.exception(e)

        self.rabbitmq.basic_ack(method.delivery_tag, False)

        self.logger.debug('Saving {} heartbeat to Redis'.format(self))
        key_heartbeat = Keys.get_component_heartbeat(self.name)
        handler_heartbeat = {'component_name': self.name,
                             'timestamp': datetime.now().timestamp()}
        transformed_handler_heartbeat = json.dumps(handler_heartbeat)
        self.redis.set(key_heartbeat, transformed_handler_heartbeat)

    def start(self) -> None:
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

    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print("{} is terminating. Connections with RabbitMQ will be "
                      "closed, and afterwards the process will exit."
                      .format(self), self.logger)
        self.rabbitmq.disconnect_till_successful()
        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
