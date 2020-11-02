import json
import logging
import multiprocessing
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.configs.system import SystemConfig
from src.monitors.managers.manager import MonitorsManager
from src.monitors.starters import start_system_monitor
from src.utils.configs import get_newly_added_configs, get_modified_configs, \
    get_removed_configs
from src.utils.logging import log_and_print


class SystemMonitorsManager(MonitorsManager):

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
            'Creating queue \'system_monitors_manager_configs_queue\'')
        self.rabbitmq.queue_declare(
            'system_monitors_manager_configs_queue', False, True, False, False)
        self.logger.info(
            'Binding queue \'system_monitors_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'chains.*.*.systems_config\'')
        self.rabbitmq.queue_bind('system_monitors_manager_configs_queue',
                                 'config', 'chains.*.*.systems_config')
        self.logger.info(
            'Binding queue \'system_monitors_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'general.systems_config\'')
        self.rabbitmq.queue_bind('system_monitors_manager_configs_queue',
                                 'config', 'general.systems_config')
        self.logger.info('Declaring consuming intentions')
        self.rabbitmq.basic_consume('system_monitors_manager_configs_queue',
                                    self._process_configs, False, False, None)

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info('Received configs {}'.format(sent_configs))

        if method.routing_key == 'general.systems_config':
            if 'general' in self.systems_configs:
                current_configs = self.systems_configs['general']
            else:
                current_configs = {}
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            if chain in self.systems_configs:
                current_configs = self.systems_configs[chain]
            else:
                current_configs = {}

        new_configs = get_newly_added_configs(sent_configs, current_configs)
        for config_id in new_configs:
            config = new_configs[config_id]
            system_id = config['id']
            parent_id = config['parent_id']
            system_name = config['name']
            node_exporter_url = config['exporter_url']
            monitor_system = config['monitor_system']

            # If we should not monitor the system, move to the next config
            if not monitor_system:
                continue

            system_config = SystemConfig(system_id, parent_id, system_name,
                                         monitor_system, node_exporter_url)
            process = multiprocessing.Process(target=start_system_monitor,
                                              args=[system_config])
            # Kill children if parent is killed
            process.daemon = True
            log_and_print('Creating a new process for the monitor of {}'
                          .format(system_config.system_name), self.logger)
            process.start()
            self._config_process_dict[config_id] = process

        modified_configs = get_modified_configs(sent_configs, current_configs)
        for config_id in modified_configs:
            # Get the latest updates
            config = sent_configs[config_id]
            system_id = config['id']
            parent_id = config['parent_id']
            system_name = config['name']
            node_exporter_url = config['exporter_url']
            monitor_system = config['monitor_system']
            system_config = SystemConfig(system_id, parent_id, system_name,
                                         monitor_system, node_exporter_url)
            previous_process = self.config_process_dict[config_id]
            previous_process.terminate()
            previous_process.join()

            # If we should not monitor the system, delete the previous process
            # from the system and move to the next config
            if not monitor_system:
                del self.config_process_dict[config_id]
                log_and_print('Killed the monitor of {} '
                              .format(config_id), self.logger)
                continue

            log_and_print('Restarting the monitor of {} with latest '
                          'configuration'.format(config_id), self.logger)

            process = multiprocessing.Process(target=start_system_monitor,
                                              args=[system_config])
            # Kill children if parent is killed
            process.daemon = True
            process.start()
            self._config_process_dict[config_id] = process

        removed_configs = get_removed_configs(sent_configs, current_configs)
        for config_id in removed_configs:
            config = removed_configs[config_id]
            system_name = config['name']
            previous_process = self.config_process_dict[config_id]
            previous_process.terminate()
            previous_process.join()
            del self.config_process_dict[config_id]
            log_and_print('Killed the monitor of {} '
                          .format(system_name), self.logger)

        # Must be done at the end in case of errors while processing
        if method.routing_key == 'general.systems_config':
            # To avoid non-moniterable systems
            self._systems_configs['general'] = {
                config_id: sent_configs[config_id] for config_id in sent_configs
                if sent_configs[config_id]['monitor_system']}
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            # To avoid non-moniterable systems
            self._systems_configs[chain] = {
                config_id: sent_configs[config_id] for config_id in sent_configs
                if sent_configs[config_id]['monitor_system']}

        self.rabbitmq.basic_ack(method.delivery_tag, False)

# TODO: In case bad config is sent by the config manager, what should happen is
#     : that the message is acknowledged so that it is released from the queue,
#     : but the message should not be processed. The config manager must also
#     : send the configs periodically, say every 60 seconds for us to avoid
#     : errors
