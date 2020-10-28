import logging

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis.redis_api import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_transformers.data_transformer import DataTransformer
from src.moniterables.system import System
from src.utils.types import convert_to_float_if_not_none


class SystemDataTransformer(DataTransformer):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi) -> None:
        super().__init__(transformer_name, logger, redis)
        self.load_transformer_state()

    def _initialize_rabbitmq(self) -> None:
        # A data transformer is both a consumer and producer, therefore we need
        # to initialize both the consuming and producing configurations.

        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info('Creating \'raw_data\' exchange')
        self.rabbitmq.exchange_declare('raw_data', 'direct', False, True, False,
                                       False)
        self.logger.info(
            'Creating queue \'system_data_transformer_raw_data_queue\'')
        self.rabbitmq.queue_declare(
            'system_data_transformer_raw_data_queue', False, True, False,
            False)
        self.logger.info(
            'Binding queue \'system_data_transformer_raw_data_queue\' to '
            'exchange \'raw_data\' with routing key \'system\'')
        self.rabbitmq.queue_bind('system_data_transformer_raw_data_queue',
                                 'raw_data', 'system')
        self.logger.info('Declaring consuming intentions')
        self.rabbitmq.basic_consume('system_data_transformer_raw_data_queue',
                                    self._transform_data, False, False, None)

        # Set producing configuration
        self.logger.info('Setting delivery confirmation on RabbitMQ channel')
        self.rabbitmq.confirm_delivery()
        self.logger.info('Creating \'store\' exchange')
        self.rabbitmq.exchange_declare('store', 'direct', False, True, False,
                                       False)
        self.logger.info('Creating \'alert\' exchange')
        self.rabbitmq.exchange_declare('alert', 'topic', False, True, False,
                                       False)

    # TODO: Need to change output type to Union[System, Repo]
    def load_system_state(self, system: System) -> None:
        # If Redis is down, the data passed as default will be stored as
        # the system state.

        self.logger.info('Loading the state of {} from Redis'.format(system))
        redis_hash = Keys.get_hash_blockchain(system.parent_id)
        system_id = system.system_id

        # Below, we will try and get the data stored in redis and store it
        # in the system's state. If the data from Redis cannot be obtained, the
        # state won't be updated.

        # Load process_cpu_seconds_total from Redis
        state_process_cpu_seconds_total = system.process_cpu_seconds_total
        redis_process_cpu_seconds_total = self.redis.hget(
            redis_hash, Keys.get_system_process_cpu_seconds_total(system_id),
            state_process_cpu_seconds_total)
        process_cpu_seconds_total = \
            convert_to_float_if_not_none(redis_process_cpu_seconds_total, None)
        system.set_process_cpu_seconds_total(process_cpu_seconds_total)

        # Load process_memory_usage from Redis
        state_process_memory_usage = system.process_memory_usage
        redis_process_memory_usage = self.redis.hget(
            redis_hash, Keys.get_system_process_memory_usage(system_id),
            state_process_memory_usage)
        process_memory_usage = \
            convert_to_float_if_not_none(redis_process_memory_usage, None)
        system.set_process_memory_usage(process_memory_usage)

        # Load virtual_memory_usage from Redis
        state_virtual_memory_usage = system.virtual_memory_usage
        redis_virtual_memory_usage = self.redis.hget(
            redis_hash, Keys.get_system_virtual_memory_usage(system_id),
            state_virtual_memory_usage)
        virtual_memory_usage = \
            convert_to_float_if_not_none(redis_virtual_memory_usage, None)
        system.set_virtual_memory_usage(virtual_memory_usage)

        # Load open_file_descriptors from Redis
        state_open_file_descriptors = system.open_file_descriptors
        redis_open_file_descriptors = self.redis.hget(
            redis_hash, Keys.get_system_open_file_descriptors(system_id),
            state_open_file_descriptors)
        open_file_descriptors = \
            convert_to_float_if_not_none(redis_open_file_descriptors, None)
        system.set_open_file_descriptors(open_file_descriptors)

        # Load system_cpu_usage from Redis
        state_system_cpu_usage = system.system_cpu_usage
        redis_system_cpu_usage = self.redis.hget(
            redis_hash, Keys.get_system_system_cpu_usage(system_id),
            state_system_cpu_usage)
        system_cpu_usage = \
            convert_to_float_if_not_none(redis_system_cpu_usage, None)
        system.set_system_cpu_usage(system_cpu_usage)

        # Load system_ram_usage from Redis
        state_system_ram_usage = system.system_ram_usage
        redis_system_ram_usage = self.redis.hget(
            redis_hash, Keys.get_system_system_ram_usage(system_id),
            state_system_ram_usage)
        system_ram_usage = \
            convert_to_float_if_not_none(redis_system_ram_usage, None)
        system.set_system_ram_usage(system_ram_usage)

        # Load system_storage_usage from Redis
        state_system_storage_usage = system.system_storage_usage
        redis_system_storage_usage = self.redis.hget(
            redis_hash, Keys.get_system_system_storage_usage(system_id),
            state_system_storage_usage)
        system_storage_usage = \
            convert_to_float_if_not_none(redis_system_storage_usage, None)
        system.set_system_storage_usage(system_storage_usage)

        # Load network_transmit_bytes_per_second from Redis
        state_network_transmit_bytes_per_second = \
            system.network_transmit_bytes_per_second
        redis_network_transmit_bytes_per_second = self.redis.hget(
            redis_hash,
            Keys.get_system_network_transmit_bytes_per_second(system_id),
            state_network_transmit_bytes_per_second)
        network_transmit_bytes_per_second = \
            convert_to_float_if_not_none(
                redis_network_transmit_bytes_per_second, None)
        system.set_network_transmit_bytes_per_second(
            network_transmit_bytes_per_second)

        # Load network_receive_bytes_per_second from Redis
        state_network_receive_bytes_per_second = \
            system.network_receive_bytes_per_second
        redis_network_receive_bytes_per_second = self.redis.hget(
            redis_hash,
            Keys.get_system_network_receive_bytes_per_second(system_id),
            state_network_receive_bytes_per_second)
        network_receive_bytes_per_second = \
            convert_to_float_if_not_none(
                redis_network_receive_bytes_per_second, None)
        system.set_network_receive_bytes_per_second(
            network_receive_bytes_per_second)

        # Load disk_io_time_seconds_in_interval from Redis
        state_disk_io_time_seconds_in_interval = \
            system.disk_io_time_seconds_in_interval
        redis_disk_io_time_seconds_in_interval = self.redis.hget(
            redis_hash,
            Keys.get_system_disk_io_time_seconds_in_interval(system_id),
            state_disk_io_time_seconds_in_interval)
        disk_io_time_seconds_in_interval = \
            convert_to_float_if_not_none(
                redis_disk_io_time_seconds_in_interval, None)
        system.set_disk_io_time_seconds_in_interval(
            disk_io_time_seconds_in_interval)

        self.logger.info(
            'Restored %s state: _process_cpu_seconds_total=%s, '
            '_process_memory_usage=%s, _virtual_memory_usage=%s, '
            '_open_file_descriptors=%s, _system_cpu_usage=%s, '
            '_system_ram_usage=%s, _system_storage_usage=%s, '
            '_network_transmit_bytes_per_second=%s, '
            '_network_receive_bytes_per_second=%s, '
            '_disk_io_time_seconds_in_interval=%s', system,
            process_cpu_seconds_total, process_memory_usage,
            virtual_memory_usage, open_file_descriptors, system_cpu_usage,
            system_ram_usage, system_storage_usage,
            network_transmit_bytes_per_second,
            redis_network_receive_bytes_per_second,
            disk_io_time_seconds_in_interval)

    def load_transformer_state(self) -> None:
        pass

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def _transform_data_for_storage(self) -> None:
        pass

    def _transform_data_for_alerting(self) -> None:
        pass

    def _send_data_for_saving(self) -> None:
        pass

    def _send_data_for_alerting(self) -> None:
        pass

    # TODO: This is what should be done next
    def _transform_data(self, ch: BlockingChannel,
                        method: pika.spec.Basic.Deliver,
                        properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        # TODO: When getting data, we need to always set the parent_id just
        #     : in case it changes. When creating also pass the parent_id. Note
        #     : loading is done only once, so it does not effect if the
        #     : parent_id changes eventually. But this is done just in case,
        #     : same for system_name
        pass

    def start(self) -> None:
        pass
