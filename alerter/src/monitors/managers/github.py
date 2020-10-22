import json
import logging
import multiprocessing
import os
from typing import Dict

import pika.exceptions

from alerter.src.configs.repo import RepoConfig
from alerter.src.monitors.managers.manager import MonitorsManager
from alerter.src.monitors.monitor_starters import start_github_monitor
from alerter.src.utils.configs import get_newly_added_configs, \
    get_modified_configs, get_removed_configs
from alerter.src.utils.logging import log_and_print


class GitHubMonitorsManager(MonitorsManager):

    def __init__(self, logger: logging.Logger, manager_name: str) -> None:
        super().__init__(logger, manager_name)
        self._repos_configs = {}

    @property
    def repos_configs(self) -> Dict:
        return self._repos_configs

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()
        self.logger.info('Creating exchange \'config\'')
        self.rabbitmq.exchange_declare('config', 'topic', False, True,
                                       False, False)
        self.logger.info(
            'Creating queue \'github_monitors_manager_configs_queue\'')
        self.rabbitmq.queue_declare('github_monitors_manager_configs_queue',
                                    False, True, False, False)
        self.logger.info(
            'Binding queue \'github_monitors_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'chains.*.*.repos_config.ini\'')
        self.rabbitmq.queue_bind('github_monitors_manager_configs_queue',
                                 'config', 'chains.*.*.repos_config.ini')
        self.logger.info(
            'Binding queue \'github_monitors_manager_configs_queue\' to '
            'exchange \'config\' with routing key '
            '\'general.repos_config.ini\'')
        self.rabbitmq.queue_bind('github_monitors_manager_configs_queue',
                                 'config', 'general.repos_config.ini')
        self.logger.info('Declaring consuming intentions')
        self.rabbitmq.basic_consume('github_monitors_manager_configs_queue',
                                    self._process_configs, False, False, None)

    def _process_configs(
            self, ch, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info('Received configs {}'.format(sent_configs))

        if method.routing_key == 'general.repos_config.ini':
            if 'general' in self.repos_configs:
                current_configs = self.repos_configs['general']
            else:
                current_configs = {}
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            if chain in self.repos_configs:
                current_configs = self.repos_configs[chain]
            else:
                current_configs = {}

        new_configs = get_newly_added_configs(sent_configs, current_configs)
        for config_id in new_configs:
            config = new_configs[config_id]
            repo_id = config['id']
            parent_id = config['parent_id']

            repo_name = config['repo_name']
            if not repo_name.endswith('/'):
                repo_name = repo_name + '/'

            monitor_repo = config['monitor_repo']
            # releases_page = os.environ["GITHUB_RELEASES_TEMPLATE"] \
            #     .format(repo_name)
            releases_page = "https://api.github.com/repos/{}releases".format(repo_name)

            # If we should not monitor the repo, move to the next config
            if not monitor_repo:
                continue

            repo_config = RepoConfig(repo_id, parent_id, repo_name,
                                     monitor_repo, releases_page)
            process = multiprocessing.Process(target=start_github_monitor,
                                              args=[repo_config])
            # Kill children if parent is killed
            process.daemon = True
            log_and_print('Creating a new process for the monitor of {}'
                          .format(repo_config.repo_name), self.logger)
            process.start()
            self._config_process_dict[config_id] = process

        modified_configs = get_modified_configs(sent_configs, current_configs)
        for config_id in modified_configs:
            # Get the latest updates
            config = sent_configs[config_id]
            repo_id = config['id']
            parent_id = config['parent_id']

            repo_name = config['repo_name']
            if not repo_name.endswith('/'):
                repo_name = repo_name + '/'

            monitor_repo = config['monitor_repo']
            # releases_page = os.environ["GITHUB_RELEASES_TEMPLATE"] \
            #     .format(repo_name)
            releases_page = "https://api.github.com/repos/{}releases".format(
                repo_name)
            repo_config = RepoConfig(repo_id, parent_id, repo_name,
                                     monitor_repo, releases_page)
            previous_process = self.config_process_dict[config_id]
            previous_process.terminate()
            previous_process.join()

            # If we should not monitor the system, delete the previous process
            # from the system and move to the next config
            if not monitor_repo:
                del self.config_process_dict[config_id]
                log_and_print('Killed the monitor of {} '
                              .format(config_id), self.logger)
                continue

            log_and_print('Restarting the monitor of {} with latest '
                          'configuration'.format(config_id), self.logger)

            process = multiprocessing.Process(target=start_github_monitor,
                                              args=[repo_config])
            # Kill children if parent is killed
            process.daemon = True
            process.start()
            self._config_process_dict[config_id] = process

        removed_configs = get_removed_configs(sent_configs, current_configs)
        for config_id in removed_configs:
            config = removed_configs[config_id]
            repo_name = config['repo_name']
            previous_process = self.config_process_dict[config_id]
            previous_process.terminate()
            previous_process.join()
            del self.config_process_dict[config_id]
            log_and_print('Killed the monitor of {} '
                          .format(repo_name), self.logger)

        # Must be done at the end in case of errors while processing
        if method.routing_key == 'general.repos_config.ini':
            # To avoid non-moniterable repos
            self._repos_configs['general'] = {
                config_id: sent_configs[config_id] for config_id in sent_configs
                if sent_configs[config_id]['monitor_repo']}
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            # To avoid non-moniterable repos
            self._repos_configs[chain] = {
                config_id: sent_configs[config_id] for config_id in sent_configs
                if sent_configs[config_id]['monitor_repo']}

        self.rabbitmq.basic_ack(method.delivery_tag, False)

# TODO: Test manager exceptions
# TODO: Test deleted (Start from here tomorrow, then below)
# TODO: Test chains repos as well