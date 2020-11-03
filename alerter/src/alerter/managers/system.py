import json
import logging
import multiprocessing
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel
from src.alerter.alerter_starters import start_system_alerter
from src.alerter.managers.manager import AlertersManager
from src.configs.system import SystemConfig
from src.utils.configs import (get_modified_configs, get_newly_added_configs,
                               get_removed_configs)
from src.utils.logging import log_and_print


class SystemAlertersManager(AlertersManager):

    def __init__(self, logger: logging.Logger, manager_name: str) -> None:
        super().__init__(logger, manager_name)
        self._systems_configs = {}
        self._systems_alerts_configs = {}

    @property
    def systems_configs(self) -> Dict:
        return self._systems_configs

    @property
    def systems_alerts_configs(self) -> Dict:
        return self._systems_alerts_configs

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
            '\'chains.*.*.systems_config\'')
        self.rabbitmq.queue_bind('system_alerters_manager_configs_queue',
                                 'config', 'chains.*.*.systems_config')
        self.logger.info(
            'Binding queue \'system_alerters_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'general.systems_config\'')
        self.rabbitmq.queue_bind('system_alerters_manager_configs_queue',
                                 'config', 'general.systems_config')
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

    def _attempt_to_strat_alerters(self) -> None:
        print("Attempte to start alerters if you have both configs")

    def _process_systems_alerts_config(self, sent_configs,
                                       current_alert_configs) -> None:
        print("Process the system alerts config and save it")
        print(sent_configs)
        print(current_alert_configs)

    def _process_systems_config(self, sent_configs,
                                current_configs) -> None:
        print("Process the systems configuration and save")
        print(sent_configs)
        print(current_configs)

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        del sent_configs['DEFAULT']

        self.logger.info('Received configs {}'.format(sent_configs))

        parsed_routing_key = method.routing_key.split('.')
        if parsed_routing_key[0] == 'general' and parsed_routing_key[1] == \
                'threshold_alerts_config':
            if 'general' in self.systems_alerts_configs:
                current_alert_configs = \
                    self.systems_alerts_configs['general']
            else:
                current_alert_configs = {}
            self._process_systems_alerts_config(sent_configs,
                                                current_alert_configs)
        elif parsed_routing_key[0] == 'general' and parsed_routing_key[1] == \
                'systems_config':
            if 'general' in self.systems_configs:
                current_configs = self.systems_configs['general']
            else:
                current_configs = {}
            self._process_systems_config(sent_configs, current_configs)
        elif parsed_routing_key[0] == 'chain' and parsed_routing_key[3] == \
                'threshold_alerts_config':
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            if chain in self.systems_alerts_configs:
                current_alert_configs = self.systems_alerts_configs[chain]
            else:
                current_alert_configs = {}
            self._process_systems_alerts_config(sent_configs,
                                                current_alert_configs)
        elif parsed_routing_key[0] == 'chain' and parsed_routing_key[3] == \
                'systems_config':
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            if chain in self.systems_configs:
                current_configs = self.systems_configs[chain]
            else:
                current_configs = {}
            self._process_systems_config(sent_configs, current_configs)

        # At the end of saving each process we should attempt to start
        # an alerter

        # if method.routing_key == 'general.threshold_alerts_config':
        #     if 'general' in self.systems_alerts_configs:
        #         current_alert_configs = self.systems_alerts_configs
        # # ['general']
        #     else:
        #         current_alert_configs = {}
        # else:
        #     parsed_routing_key = method.routing_key.split('.')
        #     print(parsed_routing_key)
        #     chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        #     if chain in self.systems_alerts_configs:
        #         current_alert_configs = self.systems_alerts_configs[chain]
        #     else:
        #         current_alert_configs = {}

        # if method.routing_key == 'general.systems_config':
        #     if 'general' in self.systems_configs:
        #         current_configs = self.systems_configs['general']
        #     else:
        #         current_configs = {}
        # else:
        #     parsed_routing_key = method.routing_key.split('.')
        #     chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        #     if chain in self.systems_configs:
        #         current_configs = self.systems_configs[chain]
        #     else:
        #         current_configs = {}

        # new_alert_configs = get_newly_added_configs(sent_configs,
        #                                             current_alert_configs)
        # for alert_id in new_alert_configs:
        #     config = new_alert_configs[alert_id]
        #     print(alert_id)

        # new_configs = get_newly_added_configs(sent_configs, current_configs)
        # for config_id in new_configs:
        #     config = new_configs[config_id]
        #     system_id = config['id']
        #     parent_id = config['parent_id']
        #     system_name = config['name']
        #     node_exporter_url = config['exporter_url']
        #     monitor_system = config['monitor_system']

        #     # If we should not monitor the system, move to the next config
        #     if not monitor_system:
        #         continue

        #     system_config = SystemConfig(system_id, parent_id, system_name,
        #                                  monitor_system, node_exporter_url)
        #     process = multiprocessing.Process(target=start_system_alerter,
        #                                       args=[system_config])
        #     # Kill children if parent is killed
        #     process.daemon = True
        #     log_and_print('Creating a new process for the alerter of {}'
        #                   .format(system_config.system_name), self.logger)
        #     process.start()
        #     self._config_process_dict[config_id] = process

        # modified_configs = get_modified_configs(sent_configs,
        #                                         current_configs)
        # for config_id in modified_configs:
        #     # Get the latest updates
        #     config = sent_configs[config_id]
        #     system_id = config['id']
        #     parent_id = config['parent_id']
        #     system_name = config['name']
        #     node_exporter_url = config['exporter_url']
        #     monitor_system = config['monitor_system']
        #     system_config = SystemConfig(system_id, parent_id, system_name,
        #                                  monitor_system, node_exporter_url)
        #     previous_process = self.config_process_dict[config_id]
        #     previous_process.terminate()
        #     previous_process.join()

        #     # If we should not monitor the system, delete the previous
        #     # process
        #     # from the system and move to the next config
        #     if not monitor_system:
        #         del self.config_process_dict[config_id]
        #         log_and_print('Killed the monitor of {} '
        #                       .format(config_id), self.logger)
        #         continue

        #     log_and_print('Restarting the monitor of {} with latest '
        #                   'configuration'.format(config_id), self.logger)

        #     process = multiprocessing.Process(target=start_system_alerter,
        #                                       args=[system_config])
        #     # Kill children if parent is killed
        #     process.daemon = True
        #     process.start()
        #     self._config_process_dict[config_id] = process

        # removed_configs = get_removed_configs(sent_configs, current_configs)
        # for config_id in removed_configs:
        #     config = removed_configs[config_id]
        #     system_name = config['name']
        #     previous_process = self.config_process_dict[config_id]
        #     previous_process.terminate()
        #     previous_process.join()
        #     del self.config_process_dict[config_id]
        #     log_and_print('Killed the monitor of {} '
        #                   .format(system_name), self.logger)

        # # Must be done at the end in case of errors while processing
        # if method.routing_key == 'general.systems_config':
        #     # To avoid non-moniterable systems
        #     self._systems_configs['general'] = {
        #         config_id:
        #             sent_configs[config_id] for config_id in sent_configs
        #         if sent_configs[config_id]['monitor_system']}
        # else:
        #     parsed_routing_key = method.routing_key.split('.')
        #     chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        #     # To avoid non-moniterable systems
        #     self._systems_configs[chain] = {
        #         config_id:
        #             sent_configs[config_id] for config_id in sent_configs
        #         if sent_configs[config_id]['monitor_system']}

        self.rabbitmq.basic_ack(method.delivery_tag, False)
