import json
import logging
import multiprocessing
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel
from src.alerter.alerter_starters import start_system_alerter
from src.alerter.managers.manager import AlertersManager
from src.configs.system_alerts import SystemAlertsConfig
from src.utils.configs import (get_modified_configs, get_newly_added_configs,
                               get_removed_configs)
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration
from src.utils.logging import log_and_print


class SystemAlertersManager(AlertersManager):

    def __init__(self, logger: logging.Logger, manager_name: str) -> None:
        super().__init__(logger, manager_name)
        self._systems_configs = {}

    @property
    def systems_configs(self) -> Dict:
        return self._systems_configs

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info('Creating exchange \'config\'')
        self.rabbitmq.exchange_declare('config', 'topic', False, True,
                                       False, False)
        self.logger.info(
            'Creating queue \'system_alerters_manager_configs_queue\'')
        self.rabbitmq.queue_declare(
            'system_alerters_manager_configs_queue', False, True, False, False)
        self.logger.info(
            'Binding queue \'system_alerters_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'chains.*.*.alerts_config\'')
        self.rabbitmq.queue_bind('system_alerters_manager_configs_queue',
                                 'config',
                                 'chains.*.*.alerts_config')
        self.logger.info(
            'Binding queue \'system_alerters_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'general.alerts_config\'')
        self.rabbitmq.queue_bind('system_alerters_manager_configs_queue',
                                 'config', 'general.alerts_config')
        # TODO remove for production
        self.rabbitmq.queue_purge('system_alerters_manager_configs_queue')
        self.logger.info('Declaring consuming intentions')
        self.rabbitmq.basic_consume('system_alerters_manager_configs_queue',
                                    self._process_configs, False, False, None)

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        self.logger.info('Received configs {}'.format(sent_configs))

        try:
            # Check if all the parent_ids in the received configuration
            # are the same
            parent_id = sent_configs['1']['parent_id']
            for i in sent_configs:
                if parent_id != sent_configs[i]['parent_id']:
                    raise ParentIdsMissMatchInAlertsConfiguration(
                          '{}: _process_data'.format(self))

            filtered = {}
            for i in sent_configs:
                filtered[sent_configs[i]['name']] = sent_configs[i]

            system_alerts_config = SystemAlertsConfig(
                parent_id=parent_id,
                open_file_descriptors=filtered['open_file_descriptors'],
                system_cpu_usage=filtered['system_cpu_usage'],
                system_storage_usage=filtered['system_storage_usage'],
                system_ram_usage=filtered['system_ram_usage'],
                system_is_down=filtered['system_is_down'],
            )

            if parent_id in self.systems_configs:
                previous_process = self.config_process_dict[parent_id]
                previous_process.terminate()
                previous_process.join()

                log_and_print('Restarting the system alerter of {} with latest'
                              ' configuration'.format(parent_id), self.logger)

                process = multiprocessing.Process(target=start_system_alerter,
                                                  args=(system_alerts_config,))
                process.daemon = True
                log_and_print('Creating a new process for the system alerter '
                              'of {}'.format(system_alerts_config.parent_id),
                              self.logger)
                process.start()
                self._config_process_dict[parent_id] = process
            else:
                process = multiprocessing.Process(target=start_system_alerter,
                                                  args=(system_alerts_config,))
                process.daemon = True
                log_and_print('Creating a new process for the system alerter '
                              'of {}'.format(system_alerts_config.parent_id),
                              self.logger)
                process.start()
                self._config_process_dict[parent_id] = process

            # To avoid non-moniterable systems
            self._systems_configs[parent_id] = {
                parent_id:  sent_configs
            }
        except Exception as e:
            self.logger.exception(e)
            raise e

        self.rabbitmq.basic_ack(method.delivery_tag, False)
