import logging

from alerter.src.data_store.redis.redis_api import RedisApi
from alerter.src.data_transformers.data_transformer import DataTransformer
from alerter.src.moniterables.system import System


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
    def load_state(self, moniterable: System) -> None:
        pass

    def _listen_for_data(self) -> None:
        pass

    def _transform_data_for_storage(self) -> None:
        pass

    def _transform_data_for_alerting(self) -> None:
        pass

    def _transform_data(self) -> None:
        pass

    def start(self) -> None:
        pass
