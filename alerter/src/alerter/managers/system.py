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
            '\'chains.*.*.threshold_alerts_config\'')
        self.rabbitmq.queue_bind('system_alerters_manager_configs_queue',
                                 'config',
                                 'chains.*.*.threshold_alerts_config')
        self.logger.info(
            'Binding queue \'system_alerters_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'general.threshold_alerts_config\'')
        self.rabbitmq.queue_bind('system_alerters_manager_configs_queue',
                                 'config', 'general.threshold_alerts_config')
        # TODO remove for production
        self.rabbitmq.queue_purge('system_alerters_manager_configs_queue')
        self.logger.info('Declaring consuming intentions')
        self.rabbitmq.basic_consume('system_alerters_manager_configs_queue',
                                    self._process_configs, False, False, None)

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)
        del sent_configs['DEFAULT']

        self.logger.info('Received configs {}'.format(sent_configs))
        if method.routing_key == 'general.threshold_alerts_config':
            if 'general' in self.systems_configs:
                current_configs = self.systems_configs['general']
            else:
                current_configs = {}
            system_parent = 'general'
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            if chain in self.systems_configs:
                current_configs = self.systems_configs[chain]
            else:
                current_configs = {}
            system_parent = chain

        new_configs = get_newly_added_configs(sent_configs, current_configs)
        if new_configs:
            filtered = {}
            for i in new_configs:
                filtered[new_configs[i]['name']] = new_configs[i]

            system_alerts_config = SystemAlertsConfig(
                parent=system_parent,
                open_file_descriptors=filtered['open_file_descriptors'],
                system_cpu_usage=filtered['system_cpu_usage'],
                system_storage_usage=filtered['system_storage_usage'],
                system_ram_usage=filtered['system_ram_usage'],
                system_is_down=filtered['system_is_down'],
            )

            process = multiprocessing.Process(target=start_system_alerter,
                                              args=[system_alerts_config])
            process.daemon = True
            log_and_print('Creating a new process for the system alerter of {}'
                          .format(system_alerts_config.parent),
                          self.logger)
            process.start()
            self._config_process_dict[system_parent] = process

        modified_configs = get_modified_configs(sent_configs, current_configs)
        if modified_configs:
            filtered = {}
            for i in modified_configs:
                filtered[modified_configs[i]['name']] = modified_configs[i]

            system_alerts_config = SystemAlertsConfig(
                parent=system_parent,
                open_file_descriptors=filtered['open_file_descriptors'],
                system_cpu_usage=filtered['system_cpu_usage'],
                system_storage_usage=filtered['system_storage_usage'],
                system_ram_usage=filtered['system_ram_usage'],
                system_is_down=filtered['system_is_down'],
            )

            previous_process = self.config_process_dict[system_parent]
            previous_process.terminate()
            previous_process.join()

            log_and_print('Restarting the system alerter of {} with latest '
                          'configuration'.format(system_parent), self.logger)

            process = multiprocessing.Process(target=start_system_alerter,
                                              args=[system_alerts_config])
            # Kill children if parent is killed
            process.daemon = True
            process.start()
            self._config_process_dict[config_id] = process

            process = multiprocessing.Process(target=start_system_alerter,
                                              args=[system_alerts_config])
            process.daemon = True
            log_and_print('Creating a new process for the system alerter of {}'
                          .format(system_alerts_config.parent),
                          self.logger)
            process.start()
            self._config_process_dict[system_parent] = process

        removed_configs = get_removed_configs(sent_configs, current_configs)
        if removed_configs:
            previous_process = self.config_process_dict[system_parent]
            previous_process.terminate()
            previous_process.join()
            del self.config_process_dict[system_parent]
            log_and_print('Killed the monitor of {} '
                          .format(system_parent), self.logger)

        # Must be done at the end in case of errors while processing
        if method.routing_key == 'general.threshold_alerts_config':
            # To avoid non-moniterable systems
            self._systems_configs['general'] = {
                'general':  sent_configs}
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            # To avoid non-moniterable systems
            self._systems_configs[chain] = {
                config_id:
                    sent_configs[config_id] for config_id in sent_configs
                if sent_configs[config_id]['monitor_system']}

        self.rabbitmq.basic_ack(method.delivery_tag, False)