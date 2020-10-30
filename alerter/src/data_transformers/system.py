import copy
import logging
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.data_store.redis.redis_api import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_transformers.data_transformer import DataTransformer
from src.moniterables.system import System
from src.utils.exceptions import ReceivedUnexpectedDataException, \
    SystemIsDownException
from src.utils.types import convert_to_float_if_not_none


class SystemDataTransformer(DataTransformer):
    def __init__(self, transformer_name: str, logger: logging.Logger,
                 redis: RedisApi) -> None:
        super().__init__(transformer_name, logger, redis)

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
                                    self._process_raw_data, False, False, None)

        # Set producing configuration
        self.logger.info('Setting delivery confirmation on RabbitMQ channel')
        self.rabbitmq.confirm_delivery()
        self.logger.info('Creating \'store\' exchange')
        self.rabbitmq.exchange_declare('store', 'direct', False, True, False,
                                       False)
        self.logger.info('Creating \'alert\' exchange')
        self.rabbitmq.exchange_declare('alert', 'topic', False, True, False,
                                       False)

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    # TODO: Need to change output type to Union[System, Repo]
    def load_system_state(self, system: System) -> None:
        # If Redis is down, the data passed as default will be stored as
        # the system state.

        self.logger.info('Loading the state of {} from Redis'.format(system))
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

        self.logger.info(
            'Restored %s state: _process_cpu_seconds_total=%s, '
            '_process_memory_usage=%s, _virtual_memory_usage=%s, '
            '_open_file_descriptors=%s, _system_cpu_usage=%s, '
            '_system_ram_usage=%s, _system_storage_usage=%s, '
            '_network_transmit_bytes_per_second=%s, '
            '_network_receive_bytes_per_second=%s, '
            '_network_transmit_bytes_total=%s, '
            '_network_receive_bytes_total=%s, '
            '_disk_io_time_seconds_in_interval=%s, '
            '_disk_io_time_seconds_total=%s, _last_monitored=%s, '
            '_went_down_at=%s', system, process_cpu_seconds_total,
            process_memory_usage, virtual_memory_usage, open_file_descriptors,
            system_cpu_usage, system_ram_usage, system_storage_usage,
            network_transmit_bytes_per_second, network_receive_bytes_per_second,
            network_transmit_bytes_total, network_receive_bytes_total,
            disk_io_time_seconds_in_interval, disk_io_time_seconds_total,
            last_monitored, went_down_at)

    def _update_state(self) -> None:
        if 'result' in self.transformed_data:
            meta_data = self.transformed_data['result']['meta_data']
            metrics = self.transformed_data['result']['data']
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            system_name = meta_data['system_name']
            system = self.state[system_id]

            # Set system details just in case the configs have changed
            system.set_parent_id(parent_id)
            system.set_system_name(system_name)

            # Save the new metrics
            system.set_last_monitored(meta_data['last_monitored'])
            system.set_process_cpu_seconds_total(
                metrics['process_cpu_seconds_total'])
            system.set_process_memory_usage(metrics['process_memory_usage'])
            system.set_virtual_memory_usage(metrics['virtual_memory_usage'])
            system.set_open_file_descriptors(metrics['open_file_descriptors'])
            system.set_system_cpu_usage(metrics['system_cpu_usage'])
            system.set_system_ram_usage(metrics['system_ram_usage'])
            system.set_system_storage_usage(metrics['system_storage_usage'])
            system.set_network_receive_bytes_total(
                metrics['network_receive_bytes_total'])
            system.set_network_transmit_bytes_total(
                metrics['network_transmit_bytes_total'])
            system.set_disk_io_time_seconds_total(
                metrics['disk_io_time_seconds_total'])
            system.set_network_transmit_bytes_per_second(
                metrics['network_transmit_bytes_per_second'])
            system.set_network_receive_bytes_per_second(
                metrics['network_receive_bytes_per_second'])
            system.set_disk_io_time_seconds_in_interval(
                metrics['disk_io_time_seconds_in_interval'])
            system.set_as_up()
        elif 'error' in self.transformed_data:
            meta_data = self.transformed_data['error']['meta_data']
            system_name = meta_data['system_name']
            system_id = meta_data['system_id']
            parent_id = meta_data['system_parent_id']
            time_of_error = meta_data['time']
            downtime_exception = SystemIsDownException(system_name)
            system = self.state[system_id]

            # Set system details just in case the configs have changed
            system.set_parent_id(parent_id)
            system.set_system_name(system_name)

            if self.transformed_data['code'] == downtime_exception.code:
                system.set_as_down(time_of_error)
        else:
            raise ReceivedUnexpectedDataException(
                '{}: _update_state'.format(self))

    def _process_transformed_data_for_storage(self) -> None:
        if 'result' in self.transformed_data:
            processed_data = copy.deepcopy(self.transformed_data)
        elif 'error' in self.transformed_data:
            meta_data = self.transformed_data['error']['meta_data']
            system_name = meta_data['system_name']
            time_of_error = meta_data['time']
            downtime_exception = SystemIsDownException(system_name)

            processed_data = copy.deepcopy(self.transformed_data)

            if self.transformed_data['code'] == downtime_exception.code:
                processed_data['data'] = {}
                processed_data['data']['went_down_at'] = time_of_error
        else:
            raise ReceivedUnexpectedDataException(
                '{}: _process_transformed_data_for_storage'.format(self))

        self._data_for_storage = processed_data

    def _process_transformed_data_for_alerting(self) -> None:
        if 'result' in self.transformed_data:
            meta_data = self.transformed_data['result']['meta_data']
            system_id = meta_data['system_id']
            system = self.state[system_id]
            data = self.transformed_data['result']['data']

            processed_data = {
                'result': {
                    'meta_data': meta_data,
                    'data': {}
                }
            }

            # Reformat the data in such a way that both the previous and current
            # states are sent to the alerter
            processed_data_metrics = processed_data['result']['data']
            for metric, value in data.items():
                processed_data_metrics[metric] = {}
                processed_data_metrics[metric]['current'] = value

            processed_data_metrics['process_cpu_seconds_total']['previous'] = \
                system.process_cpu_seconds_total
            processed_data_metrics['process_memory_usage']['previous'] = \
                system.process_memory_usage
            processed_data_metrics['virtual_memory_usage']['previous'] = \
                system.virtual_memory_usage
            processed_data_metrics['open_file_descriptors']['previous'] = \
                system.open_file_descriptors
            processed_data_metrics['system_cpu_usage']['previous'] = \
                system.system_cpu_usage
            processed_data_metrics['system_ram_usage']['previous'] = \
                system.system_ram_usage
            processed_data_metrics['system_storage_usage']['previous'] = \
                system.system_storage_usage
            processed_data_metrics['network_receive_bytes_total']['previous'] \
                = system.network_receive_bytes_total
            processed_data_metrics['network_transmit_bytes_total']['previous'] \
                = system.network_transmit_bytes_total
            processed_data_metrics['disk_io_time_seconds_total']['previous'] \
                = system.disk_io_time_seconds_total
            processed_data_metrics['network_transmit_bytes_per_second'][
                'previous'] = system.network_transmit_bytes_per_second
            processed_data_metrics['network_receive_bytes_per_second'][
                'previous'] = system.network_receive_bytes_per_second
            processed_data_metrics['disk_io_time_seconds_in_interval'][
                'previous'] = system.disk_io_time_seconds_in_interval
            processed_data_metrics['went_down_at'][
                'previous'] = system.went_down_at
        elif 'error' in self.transformed_data:
            meta_data = self.transformed_data['error']['meta_data']
            system_id = meta_data['system_id']
            system_name = meta_data['system_name']
            time_of_error = meta_data['time']
            system = self.state[system_id]
            downtime_exception = SystemIsDownException(system_name)

            processed_data = copy.deepcopy(self.transformed_data)

            if self.transformed_data['code'] == downtime_exception.code:
                processed_data['data'] = {}
                processed_data['data']['went_down_at'] = {}
                processed_data['data']['current'] = time_of_error
                processed_data['data']['previous'] = system.went_down_at
        else:
            raise ReceivedUnexpectedDataException(
                '{}: _process_transformed_data_for_alerting'.format(self))

        self._data_for_alerting = processed_data

    def _transform_data(self, data: Dict) -> None:
        if 'result' in data:
            meta_data = data['result']['meta_data']
            system_data = data['result']['data']
            system_id = meta_data['system_id']
            system = self.state[system_id]

            # Compute the network receive/transmit bytes per second based on the
            # totals and the saved last monitoring round
            transmit_bytes_total = system_data['network_transmit_bytes_total']
            receive_bytes_total = system_data['network_receive_bytes_total']
            network_transmit_bytes_per_second = None
            network_receive_bytes_per_second = None

            # If we have values to compare to (i.e. not the first ever
            # transformation) compute the bytes per second transmitted/received
            if system.last_monitored is not None:
                network_transmit_bytes_per_second = \
                    (transmit_bytes_total -
                     system.network_transmit_bytes_total) \
                    / (meta_data['time'] - system.last_monitored)
                network_receive_bytes_per_second = \
                    (receive_bytes_total - system.network_receive_bytes_total) \
                    / (meta_data['time'] - system.last_monitored)

            # Compute the time spent doing io since the last time we received
            # data for this system
            disk_io_time_seconds_total = system_data[
                'disk_io_time_seconds_total']
            disk_io_time_seconds_in_interval = None

            # If we have values to compare to (i.e. not the first ever
            # transformation) compute the time spent doing io since the last
            # monitoring round
            if system.last_monitored is not None:
                disk_io_time_seconds_in_interval = \
                    disk_io_time_seconds_total - \
                    system.disk_io_time_seconds_total

            transformed_data = copy.deepcopy(data)
            td_meta_data = transformed_data['result']['meta_data']
            td_metrics = transformed_data['result']['data']

            # Transform the meta_data by deleting the monitor_name and changing
            # the time key to last_monitored key
            del td_meta_data['monitor_name']
            del td_meta_data['time']
            td_meta_data['last_monitored'] = meta_data['time']

            # Transform the data by adding the new processed data.
            td_metrics['network_transmit_bytes_per_second'] = \
                network_transmit_bytes_per_second
            td_metrics['network_receive_bytes_per_second'] = \
                network_receive_bytes_per_second
            td_metrics['disk_io_time_seconds_in_interval'] = \
                disk_io_time_seconds_in_interval
            td_metrics['went_down_at'] = None
        elif 'error' in data:
            # In case of errors in the sent messages only remove the
            # monitor_name from the data
            transformed_data = copy.deepcopy(data)
            del transformed_data['error']['meta_data']['monitor_name']
        else:
            raise ReceivedUnexpectedDataException(
                '{}: _transform_data'.format(self))

        self._transformed_data = transformed_data
        self._process_transformed_data_for_alerting()
        self._process_transformed_data_for_storage()

    def _send_data_for_saving(self) -> None:
        pass

    def _send_data_for_alerting(self) -> None:
        pass

    def _send_data(self) -> None:
        # TODO: Must catch all exceptions here also
        pass

    def _process_raw_data(self, ch: BlockingChannel,
                          method: pika.spec.Basic.Deliver,
                          properties: pika.spec.BasicProperties, body: bytes) \
            -> None:
        # TODO: When getting data, we need to always set the parent_id just
        #     : in case it changes. When creating also pass the parent_id. Note
        #     : loading is done only once, so it does not effect if the
        #     : parent_id changes eventually. But this is done just in case,
        #     : same for system_name.
        # if loading fails do not send data also
        # TODO: Upon good processing add sending of data to the publisher queue
        pass

    def start(self) -> None:
        pass

# TODO: If the transformation fails, data should not be sent but logged. This
#     : also includes the update system state. We must make sure that the
#     : message is acknowledged so that the message is removed from the queue

# TODO: In case UnexpectedDataException, handle it, log it and continue.
#     : Therefore do not send the data

# TODO: If the sending fails, should we spawn a new process which sends the
#     : data by consuming from a python queue?
