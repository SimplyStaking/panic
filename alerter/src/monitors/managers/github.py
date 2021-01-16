import copy
import json
import logging
import multiprocessing
from datetime import datetime
from typing import Dict

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.configs.repo import RepoConfig
from src.monitors.managers.manager import MonitorsManager
from src.monitors.starters import start_github_monitor
from src.utils import env
from src.utils.configs import get_newly_added_configs, get_modified_configs, \
    get_removed_configs
from src.utils.constants import CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE, \
    GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME, GITHUB_MONITOR_NAME_TEMPLATE
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import str_to_bool

_GH_MON_MAN_INPUT_QUEUE = 'github_monitors_manager_ping_queue'
_GH_MON_MAN_INPUT_ROUTING_KEY = 'ping'
_GH_MON_MAN_ROUTING_KEY_CHAINS = 'chains.*.*.repos_config'
_GH_MON_MAN_ROUTING_KEY_GEN = 'general.repos_config'


class GitHubMonitorsManager(MonitorsManager):

    def __init__(self, logger: logging.Logger, manager_name: str) -> None:
        super().__init__(logger, manager_name)

        self._repos_configs = {}

    @property
    def repos_configs(self) -> Dict:
        return self._repos_configs

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'", _GH_MON_MAN_INPUT_QUEUE)
        self.rabbitmq.queue_declare(_GH_MON_MAN_INPUT_QUEUE, False, True, False,
                                    False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", _GH_MON_MAN_INPUT_QUEUE,
                         HEALTH_CHECK_EXCHANGE, _GH_MON_MAN_INPUT_ROUTING_KEY)
        self.rabbitmq.queue_bind(_GH_MON_MAN_INPUT_QUEUE, HEALTH_CHECK_EXCHANGE,
                                 _GH_MON_MAN_INPUT_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          _GH_MON_MAN_INPUT_QUEUE)
        self.rabbitmq.basic_consume(_GH_MON_MAN_INPUT_QUEUE, self._process_ping,
                                    True, False, None)

        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, _GH_MON_MAN_ROUTING_KEY_CHAINS)
        self.rabbitmq.queue_bind(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 _GH_MON_MAN_ROUTING_KEY_CHAINS)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing "
                         "key '%s'", GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, _GH_MON_MAN_ROUTING_KEY_GEN)
        self.rabbitmq.queue_bind(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE, _GH_MON_MAN_ROUTING_KEY_GEN)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(GITHUB_MONITORS_MANAGER_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _create_and_start_monitor_process(self, repo_config: RepoConfig,
                                          config_id: str, chain: str) -> None:
        process = multiprocessing.Process(target=start_github_monitor,
                                          args=(repo_config,))
        # Kill children if parent is killed
        process.daemon = True
        log_and_print("Creating a new process for the monitor of {}"
                      .format(repo_config.repo_name), self.logger)
        process.start()
        self._config_process_dict[config_id] = {}
        self._config_process_dict[config_id]['component_name'] = \
            GITHUB_MONITOR_NAME_TEMPLATE.format(
                repo_config.repo_name.replace('/', ' ')[:-1])
        self._config_process_dict[config_id]['process'] = process
        self._config_process_dict[config_id]['chain'] = chain

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)
        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        self.logger.info("Received configs %s", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        if method.routing_key == _GH_MON_MAN_ROUTING_KEY_GEN:
            if 'general' in self.repos_configs:
                current_configs = self.repos_configs['general']
            else:
                current_configs = {}
            chain = 'general'
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            if chain in self.repos_configs:
                current_configs = self.repos_configs[chain]
            else:
                current_configs = {}

        # This contains all the correct latest repo configs. All current
        # configs are correct configs, therefore start from the current and
        # modify as we go along according to the updates. This is done just in
        # case an error occurs.
        correct_repos_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs,
                                                  current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                repo_id = config['id']
                parent_id = config['parent_id']

                repo_name = config['repo_name']
                if not repo_name.endswith('/'):
                    repo_name = repo_name + '/'

                monitor_repo = str_to_bool(config['monitor_repo'])
                releases_page = env.GITHUB_RELEASES_TEMPLATE.format(repo_name)

                # If we should not monitor the repo, move to the next config
                if not monitor_repo:
                    continue

                repo_config = RepoConfig(repo_id, parent_id, repo_name,
                                         monitor_repo, releases_page)
                self._create_and_start_monitor_process(repo_config, config_id,
                                                       chain)
                correct_repos_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                repo_id = config['id']
                parent_id = config['parent_id']

                repo_name = config['repo_name']
                if not repo_name.endswith('/'):
                    repo_name = repo_name + '/'

                monitor_repo = str_to_bool(config['monitor_repo'])
                releases_page = env.GITHUB_RELEASES_TEMPLATE.format(repo_name)
                repo_config = RepoConfig(repo_id, parent_id, repo_name,
                                         monitor_repo, releases_page)
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()

                # If we should not monitor the repo, delete the previous
                # process from the repo and move to the next config
                if not monitor_repo:
                    del self.config_process_dict[config_id]
                    del correct_repos_configs[config_id]
                    log_and_print("Killed the monitor of {} "
                                  .format(config_id), self.logger)
                    continue

                log_and_print("Restarting the monitor of {} with latest "
                              "configuration".format(config_id), self.logger)
                self._create_and_start_monitor_process(repo_config, config_id,
                                                       chain)
                correct_repos_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs,
                                                  current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                repo_name = config['repo_name']
                previous_process = self.config_process_dict[config_id][
                    'process']
                previous_process.terminate()
                previous_process.join()
                del self.config_process_dict[config_id]
                del correct_repos_configs[config_id]
                log_and_print("Killed the monitor of {} "
                              .format(repo_name), self.logger)
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        # Must be done at the end in case of errors while processing
        if method.routing_key == _GH_MON_MAN_ROUTING_KEY_GEN:
            self._repos_configs['general'] = correct_repos_configs
        else:
            parsed_routing_key = method.routing_key.split('.')
            chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
            self._repos_configs[chain] = correct_repos_configs

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.debug("Received %s", data)

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.name
            heartbeat['running_processes'] = []
            heartbeat['dead_processes'] = []
            for config_id, process_details in self.config_process_dict.items():
                process = process_details['process']
                component_name = process_details['component_name']
                if process.is_alive():
                    heartbeat['running_processes'].append(component_name)
                else:
                    heartbeat['dead_processes'].append(component_name)
                    process.join()  # Just in case, to release resources

                    # Restart dead process
                    chain = process_details['chain']
                    config = self.repos_configs[chain][config_id]
                    repo_id = config['id']
                    parent_id = config['parent_id']

                    repo_name = config['repo_name']
                    if not repo_name.endswith('/'):
                        repo_name = repo_name + '/'

                    monitor_repo = str_to_bool(config['monitor_repo'])
                    releases_page = env.GITHUB_RELEASES_TEMPLATE.format(
                        repo_name)
                    repo_config = RepoConfig(repo_id, parent_id, repo_name,
                                             monitor_repo, releases_page)
                    self._create_and_start_monitor_process(repo_config,
                                                           config_id, chain)
            heartbeat['timestamp'] = datetime.now().timestamp()
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing %s", data)
            self.logger.exception(e)
            return

        # Send heartbeat if processing was successful
        try:
            self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as there is no use in
            # re-trying to send a heartbeat
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it.
            raise e
