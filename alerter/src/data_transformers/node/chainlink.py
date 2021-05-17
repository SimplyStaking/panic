import logging

from src.data_store.redis import RedisApi
from src.data_transformers.data_transformer import DataTransformer
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (RAW_DATA_EXCHANGE, CL_NODE_DT_INPUT_QUEUE_NAME,
                                 CHAINLINK_NODE_RAW_DATA_ROUTING_KEY,
                                 STORE_EXCHANGE, ALERT_EXCHANGE,
                                 HEALTH_CHECK_EXCHANGE)
from src.utils.types import Monitorable


class ChainlinkNodeDataTransformer(DataTransformer):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi, rabbitmq: RabbitMQApi,
                 max_queue_size: int = 0) -> None:
        super().__init__(transformer_name, logger, redis, rabbitmq,
                         max_queue_size)

    def _initialise_rabbitmq(self) -> None:
        # A data transformer is both a consumer and producer, therefore we need
        # to initialise both the consuming and producing configurations.
        self.rabbitmq.connect_till_successful()

        # Set consuming configuration
        self.logger.info("Creating '%s' exchange", RAW_DATA_EXCHANGE)
        self.rabbitmq.exchange_declare(RAW_DATA_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'", CL_NODE_DT_INPUT_QUEUE_NAME)
        self.rabbitmq.queue_declare(CL_NODE_DT_INPUT_QUEUE_NAME, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", CL_NODE_DT_INPUT_QUEUE_NAME,
                         RAW_DATA_EXCHANGE, CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)
        self.rabbitmq.queue_bind(CL_NODE_DT_INPUT_QUEUE_NAME, RAW_DATA_EXCHANGE,
                                 CHAINLINK_NODE_RAW_DATA_ROUTING_KEY)

        # Pre-fetch count is 5 times less the maximum queue size
        prefetch_count = round(self.publishing_queue.maxsize / 5)
        self.rabbitmq.basic_qos(prefetch_count=prefetch_count)
        self.logger.debug("Declaring consuming intentions")
        self.rabbitmq.basic_consume(CL_NODE_DT_INPUT_QUEUE_NAME,
                                    self._process_raw_data, False, False, None)

        # Set producing configuration
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()
        self.logger.info("Creating '%s' exchange", STORE_EXCHANGE)
        self.rabbitmq.exchange_declare(STORE_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", ALERT_EXCHANGE)
        self.rabbitmq.exchange_declare(ALERT_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)

    def load_state(self, system: Monitorable) -> Monitorable:
        # If Redis is down, the data passed as default will be stored as
        # the system state.

        self.logger.debug("Loading the state of %s from Redis", system)
        redis_hash = Keys.get_hash_parent(system.parent_id)
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

        # Load network_transmit_bytes_total from Redis
        state_network_transmit_bytes_total = system.network_transmit_bytes_total
        redis_network_transmit_bytes_total = self.redis.hget(
            redis_hash, Keys.get_system_network_transmit_bytes_total(system_id),
            state_network_transmit_bytes_total)
        network_transmit_bytes_total = \
            convert_to_float_if_not_none(redis_network_transmit_bytes_total,
                                         None)
        system.set_network_transmit_bytes_total(network_transmit_bytes_total)

        # Load network_receive_bytes_total from Redis
        state_network_receive_bytes_total = system.network_receive_bytes_total
        redis_network_receive_bytes_total = self.redis.hget(
            redis_hash, Keys.get_system_network_receive_bytes_total(system_id),
            state_network_receive_bytes_total)
        network_receive_bytes_total = \
            convert_to_float_if_not_none(redis_network_receive_bytes_total,
                                         None)
        system.set_network_receive_bytes_total(network_receive_bytes_total)

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

        # Load disk_io_time_seconds_total from Redis
        state_disk_io_time_seconds_total = system.disk_io_time_seconds_total
        redis_disk_io_time_seconds_total = self.redis.hget(
            redis_hash, Keys.get_system_disk_io_time_seconds_total(system_id),
            state_disk_io_time_seconds_total)
        disk_io_time_seconds_total = \
            convert_to_float_if_not_none(redis_disk_io_time_seconds_total, None)
        system.set_disk_io_time_seconds_total(disk_io_time_seconds_total)

        # Load last_monitored from Redis
        state_last_monitored = system.last_monitored
        redis_last_monitored = self.redis.hget(
            redis_hash, Keys.get_system_last_monitored(system_id),
            state_last_monitored)
        last_monitored = convert_to_float_if_not_none(redis_last_monitored,
                                                      None)
        system.set_last_monitored(last_monitored)

        # Load went_down_at from Redis
        state_went_down_at = system.went_down_at
        redis_went_down_at = self.redis.hget(
            redis_hash, Keys.get_system_went_down_at(system_id),
            state_went_down_at)
        went_down_at = convert_to_float_if_not_none(redis_went_down_at, None)
        system.set_went_down_at(went_down_at)

        self.logger.debug(
            "Restored %s state: _process_cpu_seconds_total=%s, "
            "_process_memory_usage=%s, _virtual_memory_usage=%s, "
            "_open_file_descriptors=%s, _system_cpu_usage=%s, "
            "_system_ram_usage=%s, _system_storage_usage=%s, "
            "_network_transmit_bytes_per_second=%s, "
            "_network_receive_bytes_per_second=%s, "
            "_network_transmit_bytes_total=%s, "
            "_network_receive_bytes_total=%s, "
            "_disk_io_time_seconds_in_interval=%s, "
            "_disk_io_time_seconds_total=%s, _last_monitored=%s, "
            "_went_down_at=%s", system, process_cpu_seconds_total,
            process_memory_usage, virtual_memory_usage, open_file_descriptors,
            system_cpu_usage, system_ram_usage, system_storage_usage,
            network_transmit_bytes_per_second, network_receive_bytes_per_second,
            network_transmit_bytes_total, network_receive_bytes_total,
            disk_io_time_seconds_in_interval, disk_io_time_seconds_total,
            last_monitored, went_down_at)

        return system
