# TODO: A system monitor starter -> Handling all errors from monitoring and
#     : always restarting on error
# TODO: A configs manager communicator, determining how many processes to start
#     : according to the configs manager message. We must kill and create
#     : processes dynamically
# TODO: Must tackle if parent dies, children must die also
import logging
import os
import time
from typing import Dict

from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.message_broker.rabbitmq.rabbitmq_api import RabbitMQApi
from alerter.src.moniterables.system import System
from alerter.src.monitors.system import SystemMonitor
from alerter.src.utils.logging import log_and_print, create_logger


class MonitorsManager:

    def __init__(self, logger: logging.Logger, redis: RedisApi) -> None:
        # TODO: Must have a process [id, name] and chain general configs field
        self._logger = logger  # TODO: General logger to be passed from outside
        self._redis = redis
        self._systems = {}

        rabbit_ip = os.environ["RABBIT_IP"]
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def systems(self) -> Dict[System]:
        return self._systems

    def _listen_for_configs(self) -> None:
        # TODO: Must do rabbit error handling qos etc
        pass

    def _process_configs(self) -> None:
        # TODO: From the chain and general configs infer systems
        pass

    def _initialize_system_monitor(self, system: System) -> SystemMonitor:
        # Monitor name based on system
        monitor_name = 'System monitor ({})'.format(system.name)

        # Try initializing a monitor until successful
        while True:
            try:
                system_monitor_logger = create_logger(
                    os.environ["SYSTEM_MONITOR_LOG_FILE_TEMPLATE"], system.name,
                    os.environ["LOGGING_LEVEL"], rotating=True)
                system_monitor = SystemMonitor(monitor_name, system,
                                               system_monitor_logger,
                                               self.redis)
                log_and_print("Successfully initialized {}"
                              .format(monitor_name), self.logger)
                break
            except Exception as e:
                msg = '!!! Error when initialising {}: {} !!!'.format(
                    monitor_name, e)
                log_and_print(msg, self.logger)
                time.sleep(10)  # sleep 10 seconds before trying again

        return system_monitor

    def _start_system_monitor(self, system: System) -> None:
        # TODO: Must do all type of error handling. When monitors stop, make
        #     : sure to close the rabbit connection. Also handle the case when
        #     : rabbit is temporarily down
        system_monitor = self._initialize_system_monitor(system)

        while True:
            try:
                log_and_print('{} started.'.format(system_monitor), self.logger)
                system_monitor.start()
            except Exception as e:
                # TODO: Depends on what we do in start
                #     : Might use system_monitor.stop()
                pass

    def manage(self) -> None:
        pass

# TODO: On the outside must handle when the manager stops, stop rabbit
#     : connection in that case
