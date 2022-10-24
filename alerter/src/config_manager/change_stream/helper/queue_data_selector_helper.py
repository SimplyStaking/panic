import logging
from time import sleep, time
from typing import Dict, Union

from bson import ObjectId

from src.config_manager.change_stream.helper.dict_helper import DictHelper
from src.config_manager.change_stream.helper.selector_helper \
    import SelectorHelper
from src.config_manager.change_stream.model.base_chain_model \
    import BaseChainModel
from src.config_manager.change_stream.model.channels.base_channel_model \
    import BaseChannelModel
from src.config_manager.change_stream.model.channels.email_channel_model \
    import EmailChannelModel
from src.config_manager.change_stream.model.channels.ops_genie_channel_model \
    import OpsGenieChannelModel
from src.config_manager.change_stream.model.channels.pager_duty_channel_model \
    import PagerDutyChannelModel
from src.config_manager.change_stream.model.channels.slack_channel_model \
    import SlackChannelModel
from src.config_manager.change_stream.model.channels.telegram_channel_model \
    import TelegramChannelModel
from src.config_manager.change_stream.model.channels.twillio_channel_model \
    import TwillioChannelModel
from src.config_manager.change_stream.model.config_model import ConfigModel
from src.config_manager.change_stream.model.evm_nodes_model import EVMNodesModel
from src.config_manager.change_stream.model.generic_model import GenericModel
from src.config_manager.change_stream.model.node_subconfig_model \
    import NodeSubconfigModel
from src.config_manager.change_stream.model.repository_subconfig_model \
    import RepositorySubconfigModel
from src.config_manager.change_stream.model.severity_alert_subconfig_model \
    import SeverityAlertSubconfigModel
from src.config_manager.change_stream.model.sub_chain_model import SubChainModel
from src.config_manager.change_stream.model.system_subconfig_model \
    import SystemSubconfigModel
from src.config_manager.change_stream.model.threshold_alert_subconfig_model \
    import ThresholdAlertSubconfigModel
from src.config_manager.change_stream.model.time_window_alert_subconfig_model \
    import TimeWindowAlertSubconfigModel
from src.data_store.mongo.mongo_api import MongoApi
from src.utils import env
from src.utils.constants.mongo import (
    BASE_CHAIN_COLL, CONFIGS_COLL, CONFIGS_OLD_COLL, GENERICS_COLL
)
from src.utils.constants.names import CONFIGS_MANAGER_NAME
from src.utils.constants.starters import RE_INITIALISE_SLEEPING_PERIOD
from src.utils.logging import create_logger, log_and_print
from src.utils.starters import get_initialisation_error_message, \
    get_reattempting_message


class QueueDataSelectorHelper:
    """
    Helps the Stream Watcher select the right data and routing key before
    pushing to the queue
    
    TODO: Rename helper to iterable and improve architecture
    """

    _items: list[SelectorHelper] = []
    _mongo: MongoApi = None
    _logger: logging.Logger = None

    def __init__(self, change: Dict, mongo: MongoApi):
        """
        Handles the Change Stream when insert, update, startup

        Args:
            change (Dict): The MongoDB Change Stream
            mongo (MongoApi)            
        """
        # clear selectors of iterator
        self._items = []

        self._mongo = mongo

        self._logger = self._initialise_logger(CONFIGS_MANAGER_NAME,
                                               QueueDataSelectorHelper.__name__,
                                               env.CONFIG_MANAGER_LOG_FILE)
        
        # remove deleted sub_chains or channels
        if self._remove_configs(change):
            return None
        
        config, channel = self._get_valid_config(change)
        

        if config != None:
            is_renamed = self._is_sub_chain_renamed(change)
            new_conf = self._is_new_config(change)
            startup = change.get('operationType') == 'startup'

            # free flow helps to send all sub configs
            free_flow = new_conf or startup or is_renamed

            self._add_alerts(change, config, free_flow)
            self._add_repositories(change, config, free_flow)
            self._add_systems(change, config, free_flow)
            self._add_evms(change, config, free_flow)
            self._add_nodes(change, config, free_flow)

            # when finish a new config send all channels
            if new_conf and not startup:
                self._add_all_channels_by_sub_chain_id(config._id)

            return None

        if channel != None:
            self._add_email(channel)
            self._add_slack(channel)
            self._add_ops_genie(channel)
            self._add_pager_duty(channel)
            self._add_telegram(channel)
            self._add_twillio(channel)

    @staticmethod
    def get_all_configs_available(mongo: MongoApi) -> list[SelectorHelper]:
        """
        Helps to get all available configurations and extract the right routing
        key and data and put it on a list of SelectorHelper

        Args:
            mongo (MongoApi): The MongoApi connection instance

        Returns:
            list[SelectorHelper]: List of selectors with data and routing key
            information
        """
        items = []

        configs = mongo.get_all(CONFIGS_COLL)
        
        #sorting configs: 1st sub chains, 2nd channels
        sub_chains = []
        channels = []
        for config in configs:
            if QueueDataSelectorHelper.is_valid_sub_chain(config):
                sub_chains.append(config)
                continue                
            
            if QueueDataSelectorHelper.is_valid_channel(config):                
                distinct = True
                
                for channel in channels:
                    if str(channel.get('type')) == str(config.get('type')):
                        distinct = False
                
                if distinct:
                    channels.append(config)
        
        #run sorted configs
        for config in sub_chains + channels:
                
            #simulating an insert behavior
            change = dict({
                'operationType': 'startup',
                'fullDocument': config
            })

            iterables = iter(QueueDataSelectorHelper(change, mongo))

            for item in iterables:
                items.append(item)

        return items

    @ staticmethod
    def is_valid_channel(doc: Dict) -> bool:
        availables = [BaseChannelModel.EMAIL, BaseChannelModel.OPS_GENIE,
                      BaseChannelModel.PAGER_DUTY, BaseChannelModel.SLACK,
                      BaseChannelModel.TELEGRAM, BaseChannelModel.TWILLIO]
        
        is_valid_type = str(doc.get('type', '')) in availables
        total_configs = len(doc.get('configs', []))

        return  total_configs > 0 and is_valid_type

    @ staticmethod
    def is_valid_sub_chain(doc: Dict) -> bool:
        is_sub_chain = str(doc.get('config_type')) == GenericModel.SUB_CHAIN
        return doc.get('ready') and is_sub_chain

    # iterator
 
    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        if self._i < len(self._items):
            selector = self._items[self._i]
            self._i += 1
            return selector
        else:
            raise StopIteration

    # validators

    def _is_valid_alert(self, change: Dict) -> bool:
        """
        Checks if the alerts are eligible to send alerts
        Args:
            change (Dict): The MongoDB Chage Stream
                @link https://www.mongodb.com/docs/manual/changeStreams/

        Returns:
            bool: Eligible or not?
        """
        needles = ['threshold_alerts', 'severity_alerts', 'time_window_alerts']

        match: bool = False
        for needle in needles:
            match = match or self._search_in_updated_fields(
                needle, change)
        return match

    def _is_new_config(self, change: Dict) -> bool:
        """
        Checks if the config is ready or just simple update. If an old doc is
        false and the new status update is true, so we consider a new
        configuration born

        Args:
            change (Dict): The MongoDB Chage Stream
                @link https://www.mongodb.com/docs/manual/changeStreams/

        Returns:
            bool: Is new config or just simple update?
        """

        # insert case
        if change.get('operationType') == 'insert':
            return change.get('fullDocument').get('ready', False)

        # update case
        is_ready = change.get('updateDescription', {}).get(
            'updatedFields', {}).get('ready', False)

        if is_ready:
            id = change.get('documentKey').get('_id')
            old_doc: Dict = self._mongo.get_one(CONFIGS_OLD_COLL, {'_id': id})
            return not old_doc.get('ready', False)

        return False
    
    def _is_sub_chain_renamed(self, change: Dict) -> bool:
        """
        Checks if the sub chain was renamed

        Args:
            change (Dict): The MongoDB Chage Stream
                @link https://www.mongodb.com/docs/manual/changeStreams/

        Returns:
            bool: Is new config or just simple update?
        """

        if change.get('operationType') != 'update':
            return False

        updateFields = change.get('updateDescription', {}).get(
            'updatedFields', {})
        sub_chain = updateFields.get('sub_chain.name', False)
        
        return sub_chain and len(updateFields) == 1

    def _search_in_updated_fields(self, needle: str, change: Dict) -> bool:
        """
        Search a substring inside the updated fields of Stream Change dict

        Args:
            needle (str): What you want search
            change (Dict): The MongoDB Change Stream

        Returns:
            bool: find or not find?
        """
        haystack = change.get('updateDescription', {}).get(
            'updatedFields', {}).keys()

        matchCount = len([t for t in haystack if needle in t])
        return matchCount > 0

    # appenders chains and general

    def _add_alerts(self, change: Dict, config: ConfigModel,
                    free_flow: bool = False) -> None:
        """
        Validates and add alerts: THRESHOLD, SEVERITY AND TIME WINDOW data and
        detect the right routing key for rabbitMQ and put this information to a
        SelectorHelper class and append it to a list of items for future
        iteration. Each item can be iterate  using an iter() function.

        Args:
            change (Dict): The MongoDB Change Stream
            config (ConfigModel): The subchain populated in ConfigModel class
            free_flow (bool): Use free flow to disable stricts validations

        Returns: None
        """
        # validations
        if not free_flow:
            if not self._is_valid_alert(change):
                return None

        alerts: Dict = dict({})
        index: int = 1

        # treshold_alert
        for item in config.threshold_alerts:

            threshold: ThresholdAlertSubconfigModel = DictHelper.dict2obj(
                ThresholdAlertSubconfigModel, item)
            str(config._id)
            alerts[index] = dict({
                'name': str(threshold.value or ''),
                'parent_id': str(config._id),
                'enabled': 'true' if threshold.enabled else 'false',
                'warning_threshold': str(threshold.warning.threshold or '0'),
                'warning_enabled':
                    'true' if threshold.warning.enabled else 'false',
                'critical_repeat': str(threshold.critical.repeat or '0'),
                'critical_enabled':
                    'true' if threshold.critical.enabled else 'false',
                'critical_threshold': str(threshold.critical.threshold or '0'),
                'critical_repeat_enabled':
                    'true' if threshold.critical.repeat_enabled else 'false'
            })

            index += 1

        # severity_alerts
        for item in config.severity_alerts:

            severity: SeverityAlertSubconfigModel = DictHelper.dict2obj(
                SeverityAlertSubconfigModel, item)

            type: GenericModel = self._mongo.get_one(
                GENERICS_COLL, {'_id': severity.type})
            type = DictHelper.dict2obj(GenericModel, type)

            severity.type = type

            alerts[index] = dict({
                'name': str(severity.value or ''),
                'parent_id': str(config._id),
                'enabled': 'true' if severity.enabled else 'false',
                'severity': str(severity.type.value or '')
            })

            index += 1

        # time_window_alerts
        for item in config.time_window_alerts:

            time_window: TimeWindowAlertSubconfigModel = DictHelper.dict2obj(
                TimeWindowAlertSubconfigModel, item)

            alerts[index] = dict({
                'parent_id': str(config._id),
                'name': str(time_window.value or ''),                
                'enabled': 
                    'true' if time_window.enabled else 'false',
                'warning_threshold': 
                    str(time_window.warning.threshold or '0'),
                'warning_time_window': 
                    str(time_window.warning.time_window or '0'),
                'warning_enabled':
                    'true' if time_window.warning.enabled else 'false',
                'critical_threshold': 
                    str(time_window.critical.threshold or '0'),
                'critical_time_window': 
                    str(time_window.critical.time_window or '0'),
                'critical_repeat': 
                    str(time_window.critical.repeat or '0'),
                'critical_repeat_enabled':
                    'true' if time_window.critical.repeat_enabled else 'false',
                'critical_enabled':
                    'true' if time_window.critical.enabled else 'false'
            })

            index += 1

        rkey = 'chains.{}.{}.alerts_config'.format(
            config.base_chain.value, config.sub_chain.name).lower()

        if str(config.base_chain._id) == BaseChainModel.GENERAL_ID:
            rkey = '{}.alerts_config'.format(config.base_chain.value).lower()

        self._logger.info('Send {} alert(s) to {} routing key'
                    .format(len(alerts), rkey))
                    
        self._items.append(SelectorHelper(rkey, alerts))

    def _add_repositories(self, change: Dict, config: ConfigModel,
                          free_flow: bool = False) -> None:
        """
        Validates and add GIT and DOCKER repositories data and detect the right
        routing key for rabbitMQ and put this information to a SelectorHelper
        class and append it to a  list of items for future iteration.
        Each item can be iterate using an iter() function.

        Args:
            change (Dict): The MongoDB Change Stream
            config (ConfigModel): The subchain populated in ConfigModel class
            free_flow (bool): Use free flow to disable stricts validations

        Returns: None
        """

        # validations
        if not free_flow:
            if not self._search_in_updated_fields('repositories', change):
                return None

        git_repos: Dict = dict({})
        docker_repos: Dict = dict({})

        # repositories
        for item in config.repositories:

            repository: RepositorySubconfigModel = DictHelper.dict2obj(
                RepositorySubconfigModel, item)

            id = str(repository._id)
            repo = dict({
                'id': id,
                'parent_id': str(config._id),
                'repo_name': str(repository.name or ''),
                'repo_namespace': str(repository.namespace or ''),
                'monitor_repo': 'true' if repository.monitor else 'false'
            })

            if (str(repository.type) == GenericModel.REPO_GIT):
                git_repos[id] = repo
            elif (str(repository.type) == GenericModel.REPO_DOCKER):
                docker_repos[id] = repo

        pre_key = 'chains.{}.{}'.format(config.base_chain.value,
                                        config.sub_chain.name).lower()        

        if str(config.base_chain._id) == BaseChainModel.GENERAL_ID:
            pre_key = config.base_chain.value.lower()

        # append Git Repos
        rkey = pre_key + '.github_repos_config'
        self._logger.info('Send {} git repo(s) to {} routing key'
                    .format(len(git_repos), rkey))
        
        self._items.append(SelectorHelper(rkey, git_repos))

        # append Docker Repos        
        rkey = pre_key + '.dockerhub_repos_config'.lower()
        self._logger.info('Send {} docker repo(s) to {} routing key'
                    .format(len(docker_repos), rkey))
                
        self._items.append(SelectorHelper(rkey, docker_repos))

    def _add_evms(self, change: Dict, config: ConfigModel,
                  free_flow: bool = False) -> None:
        """
        Validates and add EVM NODES data and detect the right routing key for
        rabbitMQ and put this information to a SelectorHelper class and append
        it to a  list of items for future iteration. Each item can be iterate
        using an iter() function.

        Args:
            change (Dict): The MongoDB Change Stream
            config (ConfigModel): The subchain populated in ConfigModel class
            free_flow (bool): Use free flow to disable stricts validations

        Returns: None
        """

        if str(config.base_chain._id) == BaseChainModel.GENERAL_ID:
            return None

        if not free_flow:
            if not self._search_in_updated_fields('evm_nodes.', change):
                return None

        evms: Dict = dict({})

        # evm_nodes select
        for item in config.evm_nodes:

            evm: EVMNodesModel = DictHelper.dict2obj(EVMNodesModel, item)

            id = str(evm._id)
            evms[id] = dict({
                'id': id,
                'parent_id': str(config._id),
                'name': str(evm.name or ''),                
                'node_http_url': str(evm.node_http_url or ''),
                'monitor_node': 'true' if evm.monitor else 'false'
            })
        
        rkey = 'chains.{}.{}.evm_nodes_config'.format(
            config.base_chain.value, config.sub_chain.name).lower()

        self._logger.info('Send {} evm node(s) to {} routing key'
                    .format(len(evms), rkey))

        self._items.append(SelectorHelper(rkey, evms))

    def _add_systems(self, change: Dict, config: ConfigModel,
                     free_flow: bool = False) -> None:
        """
        Validates and add SYSTEMS data and detect the right routing key for
        rabbitMQ and put this information to a SelectorHelper class and append
        it to a  list of items for future iteration. Each item can be iterate
        using an iter() function.

        Args:
            change (Dict): The MongoDB Change Stream
            config (ConfigModel): The subchain populated in ConfigModel class
            free_flow (bool): Use free flow to disable stricts validations

        Returns: None
        """

        if not free_flow:
            if not self._search_in_updated_fields('systems', change):
                return None

        systems: Dict = dict({})

        # evm_nodes select
        for item in config.systems:

            system: SystemSubconfigModel = DictHelper.dict2obj(
                SystemSubconfigModel, item)

            id = str(system._id)
            systems[id] = dict({
                'id': id,
                'parent_id': str(config._id),
                'name': str(system.name or ''),                
                'exporter_url': str(system.exporter_url or ''),
                'monitor_system': 'true' if system.monitor else 'false'
            })

        rkey = 'chains.{}.{}.systems_config'.format(
            config.base_chain.value, config.sub_chain.name).lower()

        if str(config.base_chain._id) == BaseChainModel.GENERAL_ID:
            rkey = '{}.systems_config'.format(config.base_chain.value).lower()

        self._logger.info('Send {} system(s) to {} routing key'
                    .format(len(systems), rkey))

        self._items.append(SelectorHelper(rkey, systems))

    def _add_nodes(self, change: Dict, config: ConfigModel,
                   free_flow: bool = False) -> None:
        """
        Validates and add NODES repositories data and detect the right routing
        key for rabbitMQ and put this information to a SelectorHelper class and
        append it to a  list of items for future iteration. Each item can be
        iterate using an iter() function.

        Args:
            change (Dict): The MongoDB Change Stream
            config (ConfigModel): The subchain populated in ConfigModel class
            free_flow (bool): Use free flow to disable stricts validations

        Returns: None
        """
        if str(config.base_chain._id) == BaseChainModel.GENERAL_ID:
            return None

        if not free_flow:
            is_nodes =  self._search_in_updated_fields('nodes', change)
            is_evm = self._search_in_updated_fields('evm_nodes.', change)
            if not is_nodes or is_evm:
                return None

        nodes: Dict = dict({})

        # evm_nodes select
        for item in config.nodes:

            node: NodeSubconfigModel = DictHelper.dict2obj(
                NodeSubconfigModel, item)

            id = str(node._id)
            nodes[id] = dict({
                'id': id,
                'parent_id': str(config._id),
                'name': str(node.name or ''),                
                'node_ws_url': str(node.node_ws_url or ''),
                'exporter_url': str(node.exporter_url or ''),
                'monitor_system': 'true' if node.monitor_system else 'false',
                'monitor_node': 'true' if node.monitor_node else 'false',
                'is_validator': 'true' if node.is_validator else 'false',
                'is_archive_node': 'true' if node.is_archive_node else 'false',
                'use_as_data_source':
                    'true' if node.use_as_data_source else 'false',
                'stash_address': str(node.stash_address or ''),
                'governance_addresses': str(node.governance_addresses or ''),
                'monitor_network': 'true' if node.monitor_network else 'false',
                'cosmos_rest_url': str(node.cosmos_rest_url or ''),
                'monitor_cosmos_rest':
                    'true' if node.monitor_cosmos_rest else 'false',
                'tendermint_rpc_url': str(node.tendermint_rpc_url or ''),
                'monitor_tendermint_rpc':
                    'true' if node.monitor_tendermint_rpc else 'false',
                'operator_address': str(node.operator_address or ''),
                'monitor_prometheus':
                    'true' if node.monitor_prometheus else 'false',
                'prometheus_url': str(node.prometheus_url  or ''),
                'node_prometheus_urls': str(node.node_prometheus_urls or ''),
                'evm_nodes_urls': str(node.evm_nodes_urls or ''),
                'weiwatchers_url': str(node.weiwatchers_url or ''),
                'monitor_contracts':
                    'true' if node.monitor_contracts else 'false'
            })

        rkey = 'chains.{}.{}.nodes_config'.format(config.base_chain.value, 
                                                  config.sub_chain.name).lower()

        self._logger.info('Send {} node(s) to {} routing key'
                    .format(len(nodes), rkey))
            
        self._items.append(SelectorHelper(rkey, nodes))

    # appenders channels
    def _add_email(self, email: EmailChannelModel) -> None:
        """        
        Validates and add EMAIL CHANNEL data and detect the right routing key 
        for rabbitMQ and put this information to a SelectorHelper class and 
        append it to a  list of items for future iteration. Each item can be 
        iterate using an iter() function.

        Args:
            email (EmailChannelModel): The Email object

        Returns: None
        """
        if str(email.type._id) != BaseChannelModel.EMAIL:
            return None
        
        rkey = 'channels.' + email.type.value + '_config'.lower()

        docs: Dict = self._mongo.get_by(CONFIGS_COLL, {'type': email.type._id})
        
        channels = dict()
        
        for doc in docs:
            email = self._dict_to_channel(doc)
            if len(email.configs) == 0:
                continue

            if not email:
                self._logger.debug("Can't convert dict to Email model")
                continue
            
            ids = ','.join(map(lambda x: str(x._id), email.configs))
            names = ','.join(map(lambda x: x.sub_chain.name, email.configs))            

            id = str(email._id)
            channels[id] = dict({
                'id': id,
                'channel_name': str(email.name or ''),
                'port': str(email.port  or ''),
                'smtp': str(email.smtp  or ''), 
                'email_from': str(email.email_from  or ''),
                'emails_to': ','.join(email.emails_to),
                'username': str(email.username  or ''),
                'password': str(email.password or ''),
                'info': 'true' if email.info else 'false',
                'warning': 'true' if email.warning else 'false',
                'critical': 'true' if email.critical else 'false',
                'error': 'true' if email.error else 'false',
                'parent_ids': ids,
                'parent_names': names
            })        
                        
        self._logger.info('Send {} email(s) to {} routing key'
                    .format(len(channels), rkey))
        
        self._items.append(SelectorHelper(rkey, channels))

    def _add_slack(self, slack: SlackChannelModel) -> None:
        """
        Validates and add SLACK CHANNEL data and detect the right routing key 
        for rabbitMQ and put this information to a SelectorHelper class and 
        append it to a  list of items for future iteration. Each item can be 
        iterate using an iter() function.

        Args:
            slack (SlackChannelModel): The Slack object

        Returns: None
        """
        if str(slack.type._id) != BaseChannelModel.SLACK:
            return None
        
        rkey = 'channels.' + slack.type.value + '_config'.lower()
    
        docs: Dict = self._mongo.get_by(CONFIGS_COLL, {'type': slack.type._id})
        
        channels = dict()
        
        for doc in docs:
            slack = self._dict_to_channel(doc)
            if len(slack.configs) == 0:
                continue

            if not slack:
                self._logger.debug("Can't convert dict to Slack model")
                continue

            ids = ','.join(map(lambda x: str(x._id), slack.configs))
            names = ','.join(map(lambda x: x.sub_chain.name, slack.configs))            

            id = str(slack._id)
            channels[id] = dict({
                'id': id,
                'channel_name': str(slack.name or ''),
                'bot_token': str(slack.bot_token or ''),
                'app_token': str(slack.app_token  or ''),
                'bot_channel_id': str(slack.bot_channel_id  or ''),
                'info': 'true' if slack.info else 'false',
                'warning': 'true' if slack.warning else 'false',
                'critical': 'true' if slack.critical else 'false',
                'error': 'true' if slack.error else 'false',
                'alerts': 'true' if slack.alerts else 'false',
                'commands': 'true' if slack.commands else 'false',
                'parent_ids': ids,
                'parent_names': names
            })        

        self._logger.info('Send {} Slack(s) to {} routing key'        
                    .format(len(channels), rkey))

        self._items.append(SelectorHelper(rkey, channels))

    def _add_ops_genie(self, ops: OpsGenieChannelModel) -> None:
        """
        Validates and add OPSGENIE CHANNEL data and detect the right routing key 
        for rabbitMQ and put this information to a SelectorHelper class and 
        append it to a  list of items for future iteration. Each item can be 
        iterate using an iter() function.

        Args:
            ops (OpsGenieChannelModel): The Opsgenie object

        Returns: None
        """
        if str(ops.type._id) != OpsGenieChannelModel.OPS_GENIE:
            return None
        
        rkey = 'channels.' + ops.type.value + '_config'.lower()
        
        docs: Dict = self._mongo.get_by(CONFIGS_COLL, {'type': ops.type._id})
        
        channels = dict()
        
        for doc in docs:
            ops = self._dict_to_channel(doc)
            if len(ops.configs) == 0:
                continue

            if not ops:
                self._logger.debug("Can't convert dict to Opsgenie model")
                continue

            ids = ','.join(map(lambda x: str(x._id), ops.configs))
            names = ','.join(map(lambda x: x.sub_chain.name, ops.configs))

            id = str(ops._id)
            channels[id] = dict({
                'id': id,
                'channel_name': str(ops.name or ''),
                'api_token': str(ops.api_token or ''),
                'eu': 'true' if ops.eu else 'false',
                'info': 'true' if ops.info else 'false',
                'warning': 'true' if ops.warning else 'false',
                'critical': 'true' if ops.critical else 'false',
                'error': 'true' if ops.error else 'false',
                'parent_ids': ids,
                'parent_names': names
            })              

        self._logger.info('Send {} Opsgenie(s) to {} routing key'
                    .format(len(channels), rkey))

        self._items.append(SelectorHelper(rkey, channels))

    def _add_pager_duty(self, pager: PagerDutyChannelModel) -> None:
        """
        Validates and add PAGERDUTY CHANNEL data and detect the right routing 
        key for rabbitMQ and put this information to a SelectorHelper class and 
        append it to a  list of items for future iteration. Each item can be 
        iterate using an iter() function.

        Args:
            pager (PagerDutyChannelModel): The PagerDuty object

        Returns: None            
        """
        if str(pager.type._id) != OpsGenieChannelModel.PAGER_DUTY:
            return None
        
        rkey = 'channels.' + pager.type.value + '_config'.lower()

        docs: Dict = self._mongo.get_by(CONFIGS_COLL, {'type': pager.type._id})
        
        channels = dict()
        
        for doc in docs:
            pager = self._dict_to_channel(doc)
            if len(pager.configs) == 0:
                continue

            if not pager:
                self._logger.debug("Can't convert dict to Pager Duty model")
                continue
            
            ids = ','.join(map(lambda x: str(x._id), pager.configs))
            names = ','.join(map(lambda x: x.sub_chain.name, pager.configs))

            id = str(pager._id)
            channels[id] = dict({
                'id': id,
                'channel_name': str(pager.name or ''),
                'integration_key': str(pager.integration_key or ''),
                'info': 'true' if pager.info else 'false',
                'warning': 'true' if pager.warning else 'false',
                'critical': 'true' if pager.critical else 'false',
                'error': 'true' if pager.error else 'false',
                'parent_ids': ids,
                'parent_names': names
            })

        self._logger.info('Send {} Pager(s) to {} routing key'                        
                    .format(len(channels), rkey))

        self._items.append(SelectorHelper(rkey, channels))

    def _add_telegram(self, telegram: TelegramChannelModel):
        """
        Validates and add TELEGRAM CHANNEL data and detect the right routing key 
        for rabbitMQ and put this information to a SelectorHelper class and 
        append it to a  list of items for future iteration. Each item can be 
        iterate using an iter() function.

        Args:
            telegram (TelegramChannelModel): The Telegram object

        Returns:
            _type_: _description_
        """
        if str(telegram.type._id) != OpsGenieChannelModel.TELEGRAM:
            return None
        
        rkey = 'channels.' + telegram.type.value + '_config'.lower()

        docs: Dict = self._mongo.get_by(CONFIGS_COLL,
                                        {'type': telegram.type._id})
        
        channels = dict()
        
        for doc in docs:
            telegram = self._dict_to_channel(doc)
            if len(telegram.configs) == 0:
                continue

            if not telegram:
                self._logger.debug("Can't convert dict to Telegram model")
                continue
                            
            ids = ','.join(map(lambda x: str(x._id), telegram.configs))
            names = ','.join(map(lambda x: x.sub_chain.name, telegram.configs))

            id = str(telegram._id)
            channels[id] = dict({
                'id': id,
                'channel_name': str(telegram.name or ''),
                'bot_token': str(telegram.bot_token or ''),
                'chat_id': str(telegram.chat_id or ''),
                'info': 'true' if telegram.info else 'false',
                'warning': 'true' if telegram.warning else 'false',
                'critical': 'true' if telegram.critical else 'false',
                'error': 'true' if telegram.error else 'false',
                'alerts': 'true' if telegram.alerts else 'false',
                'commands': 'true' if telegram.commands else 'false',
                'parent_ids': ids,
                'parent_names': names
            })        
                        
        self._logger.info('Send {} telegram(s) to {} routing key'
                    .format(len(channels), rkey))
        
        self._items.append(SelectorHelper(rkey, channels))

    def _add_twillio(self, twillio: TwillioChannelModel) -> None:
        """
        Validates and add TWILLIO CHANNEL data and detect the right routing key 
        for rabbitMQ and put this information to a SelectorHelper class and 
        append it to a  list of items for future iteration. Each item can be 
        iterate using an iter() function.

        Args:
            twillio (TwillioChannelModel): The Twillio object

        Returns: None
        """
        if str(twillio.type._id) != OpsGenieChannelModel.TWILLIO:
            return None

        rkey = 'channels.' + twillio.type.value + '_config'.lower()
        
        docs: Dict = self._mongo.get_by(CONFIGS_COLL,
                                        {'type': twillio.type._id})
        
        channels = dict()
        
        for doc in docs:
            twillio = self._dict_to_channel(doc)
            if len(twillio.configs) == 0:
                continue

            if not twillio:
                self._logger.debug("Can't convert dict to Twillio model")
                continue
            
            ids = ','.join(map(lambda x: str(x._id), twillio.configs))
            names = ','.join(map(lambda x: x.sub_chain.name, twillio.configs))

            numbers: Dict = twillio.twilio_phone_numbers_to_dial
            channels = dict()
            id = str(twillio._id)
            channels[id] = dict({
                'id': id,
                'channel_name': str(twillio.name or ''),
                'account_sid': str(twillio.account_sid or ''),
                'auth_token': str(twillio.auth_token  or ''),
                'twilio_phone_no': str(twillio.twilio_phone_number or ''),
                'twilio_phone_numbers_to_dial_valid': ','.join(numbers),
                'parent_ids': ids,
                'parent_names': names
            })                

        self._logger.info('Send {} twillio(s) to {} routing key'
                    .format(len(channels), rkey))

        self._items.append(SelectorHelper(rkey, channels))

    def _add_all_channels_by_sub_chain_id(self, id: ObjectId) -> None:
        """
        Send all availables channels by sub_chain associated

        Args:
            id (ObjectId): The Sub Chain Id
        Returns: None
        """

        docs: Dict = self._mongo.get_by(CONFIGS_COLL, {'configs': id})

        if docs is None:
            return None

        for doc in docs:
            channel : BaseChannelModel = self._dict_to_channel(doc)

            if channel != None and len(channel.configs) == 0:
                continue

            self._add_email(channel)
            self._add_slack(channel)
            self._add_ops_genie(channel)
            self._add_pager_duty(channel)
            self._add_telegram(channel)
            self._add_twillio(channel)

    # logger

    def _initialise_logger(self, component_display_name: str,
                           component_module_name: str,
                           log_file_template: str) -> logging.Logger:
        """
        Starts Logger to Config Manager

        Args:
            component_display_name (str): The Component name
            component_module_name (str): The Module name
            log_file_template (str): The Template

        Returns:
            logging.Logger: Instance of Logger
        """

        # Try initialising the logger until successful. This had to be done
        # separately to avoid instances when the logger creation failed and we
        # attempt to use it.
        while True:
            try:
                new_logger = create_logger(log_file_template.format(
                    component_display_name), component_module_name,
                    env.LOGGING_LEVEL, rotating=True)
                break
            except Exception as e:
                # Use a dummy logger in this case because we cannot create the
                # manager's logger.
                dummy_logger = logging.getLogger('DUMMY_LOGGER')
                log_and_print(get_initialisation_error_message(
                    component_display_name, e), dummy_logger)
                log_and_print(get_reattempting_message(component_display_name),
                              dummy_logger)
                # sleep before trying again
                time.sleep(RE_INITIALISE_SLEEPING_PERIOD)

        return new_logger

    # auxiliaries

    def _get_valid_config(self, change: Dict) -> Union[ConfigModel,
                                                         BaseChannelModel]:
        """
        Gets valid channel or valid sub chain configured

        Args:
            change (Dict): The Change Stream MongoDB

        Returns:
            Union[ConfigModel, BaseChannelModel]: The union of config/channel
        """
        # just accept insert and update operationTypes
        is_valid = change.get('operationType') in [
            'insert', 'update', 'startup']
        if not is_valid:
            return [None, None]

        if change.get('operationType') in ['insert', 'startup']:
            doc = change.get('fullDocument')
        elif (change.get('operationType') == 'update'):
            id = change.get('documentKey').get('_id')
            doc: Dict = self._mongo.get_one(CONFIGS_COLL, {'_id': id})

        if QueueDataSelectorHelper.is_valid_sub_chain(doc):
            config = self._get_valid_sub_chain(doc)
            return [config, None]
        #disconsider insert channels            
        elif change.get('operationType') != 'insert': 
            channel : BaseChannelModel = self._dict_to_channel(doc)
            if channel != None:
                return [None, channel]

        return [None, None]

    def _dict_to_channel(self, doc: Dict) -> BaseChainModel:
        """
        Converts channel document to Email, OpsGenie, PagerDuty, Slack, Telegram
            or Twillio object.

        Args:
            doc (Dict): _description_

        Returns:
            BaseChainModel: The Email, OpsGenie, PagerDuty, Slack, Telegram or
                Twillio object
        """
        type = str(doc.get('type', ''))

        channel: BaseChannelModel = None
        if type == BaseChannelModel.EMAIL:
            channel = DictHelper.dict2obj(EmailChannelModel, doc)
        elif type == BaseChannelModel.OPS_GENIE:
            channel = DictHelper.dict2obj(OpsGenieChannelModel, doc)
        elif type == BaseChannelModel.PAGER_DUTY:
            channel = DictHelper.dict2obj(PagerDutyChannelModel, doc)
        elif type == BaseChannelModel.SLACK:
            channel = DictHelper.dict2obj(SlackChannelModel, doc)
        elif type == BaseChannelModel.TELEGRAM:
            channel = DictHelper.dict2obj(TelegramChannelModel, doc)
        elif type == BaseChannelModel.TWILLIO:
            channel = DictHelper.dict2obj(TwillioChannelModel, doc)
        else:
            return None

        type = self._mongo.get_one(GENERICS_COLL, {'_id': channel.type})

        configs = []
        for id in channel.configs:
            sub_doc: Dict = self._mongo.get_one(CONFIGS_COLL, {'_id': id})
            
            if sub_doc is None:
                continue

            config: ConfigModel = DictHelper.dict2obj(ConfigModel, sub_doc)

            if config.sub_chain != None:
                config.sub_chain = DictHelper.dict2obj(
                    SubChainModel, config.sub_chain)

            if (config and config.ready):
                configs.append(config)

        channel.configs = configs
        channel.type = DictHelper.dict2obj(GenericModel, type)

        return channel

    def _get_valid_sub_chain(self, doc: Dict) -> ConfigModel:
        """
        Returns a valid sub chain object

        Args:
            doc (Dict): The MongoDB Document

        Returns:
            ConfigModel: The sub chain object
        """
        
        # convert dict to object
        config: ConfigModel = DictHelper.dict2obj(ConfigModel, doc)

        if config.base_chain != None:
            base_chain = self._mongo.get_one(BASE_CHAIN_COLL,
                                             {'_id': config.base_chain})
            config.base_chain = DictHelper.dict2obj(
                BaseChainModel, base_chain)

        if config.sub_chain != None:
            config.sub_chain = DictHelper.dict2obj(
                SubChainModel, config.sub_chain)

        return config

    def _remove_configs(self, change: Dict, retry = 0) -> bool:
        """
        Detect if the SubChain or Channel was removed and Put a empty dict on 
        each routing key for: Alerter, Repositories, EVMS, NODES, email,
        telegram, twillio, pagerduty, opsgenie and slack. Get all routing keys
        and append for iterator.
        
        TODO : Needs to remove retry approach and investigate deeply the issue 
        of sync

        Args:
            change (Dict): The MongoDB Change Stream

        Returns:
            bool: True if detect and append any removes was succesfull 
        """
        is_delete = change.get('operationType') == 'delete'
        is_update = change.get('operationType') == 'update'
        
        if not is_delete and not is_update:
            return False                
        
        criteria = {'_id': change.get('documentKey',{}).get('_id','')}
        
        if retry == 3:
            raise Exception("Failed removing after {} attempts".format(retry))                
        
        old_doc = self._mongo.get_one(CONFIGS_OLD_COLL, criteria)
        
        if not old_doc:
            self._logger.debug("Failed to search in backup collection" +
                " sleeping 2s and try again")
            
            sleep(2)
            return self._remove_configs(change, retry+1)            
                                
        if is_update:
            updated_doc = self._mongo.get_one(CONFIGS_COLL, criteria)

            #sub chain case
            if self._is_sub_chain_renamed(change) and updated_doc.get('ready'):
                self._remove_all_sub_configs(old_doc)                    
        
        if is_delete:
            if QueueDataSelectorHelper.is_valid_channel(old_doc):
                channel : BaseChannelModel = self._dict_to_channel(old_doc)                
                
                if not channel:
                    False
                
                self._add_email(channel)
                self._add_slack(channel)
                self._add_ops_genie(channel)
                self._add_pager_duty(channel)
                self._add_telegram(channel)
                self._add_twillio(channel)
                                                                
            return self._remove_all_sub_configs(old_doc)
                
        return False

    def _remove_all_sub_configs(self, doc : Dict)-> bool:
        """
        Removes every routing key associated to sub config of specific document

        Args:
            doc (Dict): The MongoDB document

        Returns:
            bool: True if everything removed, False if invalid sub chain or doc
        """
        
        if not QueueDataSelectorHelper.is_valid_sub_chain(doc):
            return False
                
        config = self._get_valid_sub_chain(doc)

        if config is None:
            return False
            
        pre_key = 'chains.{}.{}'.format(config.base_chain.value, 
                                                config.sub_chain.name)

        if str(config.base_chain._id) == BaseChainModel.GENERAL_ID:
            pre_key = config.base_chain.value
            
        self._remove_routing_keys([
            'alerts_config',
            'github_repos_config',
            'dockerhub_repos_config',
            'systems_config'], pre_key)
                
        if str(config.base_chain._id) != BaseChainModel.GENERAL_ID:
            self._remove_routing_keys([
                'nodes_config',
                'evm_nodes_config'], pre_key)            
        
        return True

    def _remove_channel(self, doc: Dict) -> bool:
        """
        Remove channel and put empty dict to channel

        Args:
            doc (Dict): The Mongo DB document

        Returns:
            bool: True if channel removed, False if invalid channel
        """
        channel: BaseChannelModel = self._dict_to_channel(doc)

        if channel is None:
            return False

        rkey = 'channels.' + channel.type.value + '_config'
        self._remove_routing_keys([rkey])        

        return True
    
    def _remove_routing_keys(self, keys : list[str], pre_key : str = '') -> None:
        """
        Appends empty dict to given list of routing keys

        Args:
            keys (list[str]): _description_
            pre_key (str, optional): Preposition name of keys. Defaults to ''.
            
        Returns : None
        """
        for key in keys:
            rkey = (pre_key + key).lower()
            if len(pre_key) > 0:
                rkey = (pre_key + '.' + key).lower()
                            
            self._logger.info('Removing {}'.format(rkey))
            self._items.append(SelectorHelper(rkey, dict({})))