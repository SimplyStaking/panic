import logging
import unittest
from datetime import timedelta
from unittest import mock

from parameterized import parameterized

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.configs.nodes.evm import EVMNodeConfig
from src.configs.repo import RepoConfig
from src.configs.system import SystemConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.contracts.chainlink import ChainlinkContractsMonitor
from src.monitors.github import GitHubMonitor
from src.monitors.node.chainlink import ChainlinkNodeMonitor
from src.monitors.node.evm import EVMNodeMonitor
from src.monitors.starters import (_initialise_monitor_logger,
                                   _initialise_monitor, start_system_monitor,
                                   start_github_monitor, start_node_monitor,
                                   _initialise_chainlink_contracts_monitor,
                                   start_chainlink_contracts_monitor)
from src.monitors.system import SystemMonitor
from src.utils import env
from src.utils.constants.names import (SYSTEM_MONITOR_NAME_TEMPLATE,
                                       GITHUB_MONITOR_NAME_TEMPLATE,
                                       NODE_MONITOR_NAME_TEMPLATE,
                                       CL_CONTRACTS_MONITOR_NAME_TEMPLATE)


class TestMonitorStarters(unittest.TestCase):
    def setUp(self) -> None:
        # Dummy objects
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.monitor_display_name = 'Test Monitor'
        self.monitor_module_name = 'TestMonitor'
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        # Github monitor
        self.github_monitor_name = 'test_github_monitor'
        self.github_monitoring_period = env.GITHUB_MONITOR_PERIOD_SECONDS
        self.github_repo_id = 'test_repo_id'
        self.github_parent_id = 'test_github_parent_id'
        self.github_repo_name = 'test_repo'
        self.monitor_repo = True
        self.releases_page = 'test_url'
        self.repo_config = RepoConfig(self.github_repo_id,
                                      self.github_parent_id,
                                      self.github_repo_name, self.monitor_repo,
                                      self.releases_page)
        self.test_github_monitor = GitHubMonitor(self.github_monitor_name,
                                                 self.repo_config,
                                                 self.dummy_logger,
                                                 self.github_monitoring_period,
                                                 self.rabbitmq)

        # System Monitor
        self.system_monitor_name = 'test_system_monitor'
        self.system_monitoring_period = env.SYSTEM_MONITOR_PERIOD_SECONDS
        self.system_id = 'test_system_id'
        self.system_parent_id = 'test_system_parent_id'
        self.system_name = 'test_system'
        self.monitor_system = True
        self.node_exporter_url = 'test_url'
        self.system_config = SystemConfig(self.system_id, self.system_parent_id,
                                          self.system_name, self.monitor_system,
                                          self.node_exporter_url)
        self.test_system_monitor = SystemMonitor(self.system_monitor_name,
                                                 self.system_config,
                                                 self.dummy_logger,
                                                 self.system_monitoring_period,
                                                 self.rabbitmq)

        # Node Monitors
        self.node_monitor_name = 'test_node_monitor'
        self.node_monitoring_period = env.NODE_MONITOR_PERIOD_SECONDS
        self.node_id = 'test_node_id'
        self.node_parent_id = 'test_node_parent_id'
        self.node_name = 'test_node'
        self.monitor_node = True
        self.monitor_prometheus = True
        self.node_exporter_url = 'test_url'
        self.node_http_url = 'http_url_1'
        self.node_prometheus_urls = ['url1', 'url2', 'url3']
        self.chainlink_node_config = ChainlinkNodeConfig(
            self.node_id, self.node_parent_id, self.node_name,
            self.monitor_node, self.monitor_prometheus,
            self.node_prometheus_urls)
        self.evm_node_config = EVMNodeConfig(
            self.node_id, self.node_parent_id, self.node_name,
            self.monitor_node, self.node_http_url)
        self.test_chainlink_node_monitor = ChainlinkNodeMonitor(
            self.node_monitor_name, self.chainlink_node_config,
            self.dummy_logger, self.node_monitoring_period, self.rabbitmq)
        self.test_evm_node_monitor = EVMNodeMonitor(
            self.node_monitor_name, self.evm_node_config, self.dummy_logger,
            self.node_monitoring_period, self.rabbitmq)

        # Chainlink Contracts Monitor
        self.cl_contracts_monitor_name = 'chainlink_contracts_monitor'
        self.weiwatchers_url = 'weiwatchers_url'
        self.evm_nodes = ['url1', 'url2', 'url3']
        self.node_configs = [self.chainlink_node_config]
        self.chainlink_contracts_monitoring_period = \
            env.CHAINLINK_CONTRACTS_MONITOR_PERIOD_SECONDS
        self.test_chainlink_contracts_monitor = ChainlinkContractsMonitor(
            self.cl_contracts_monitor_name, self.weiwatchers_url,
            self.evm_nodes, self.node_configs, self.dummy_logger,
            self.chainlink_contracts_monitoring_period, self.rabbitmq)

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.repo_config = None
        self.test_github_monitor = None
        self.rabbitmq = None
        self.system_config = None
        self.test_system_monitor = None
        self.chainlink_node_config = None
        self.evm_node_config = None
        self.test_chainlink_node_monitor = None
        self.test_evm_node_monitor = None
        self.test_chainlink_contracts_monitor = None

    @mock.patch("src.monitors.starters.create_logger")
    def test_initialise_monitor_logger_creates_and_returns_logger_correctly(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger

        actual_return = _initialise_monitor_logger(self.monitor_display_name,
                                                   self.monitor_module_name)

        mock_create_logger.assert_called_once_with(
            env.MONITORS_LOG_FILE_TEMPLATE.format(self.monitor_display_name),
            self.monitor_module_name, env.LOGGING_LEVEL, True
        )
        self.assertEqual(self.dummy_logger, actual_return)

    @parameterized.expand([
        (GitHubMonitor, 'self.github_monitor_name',
         'self.github_monitoring_period', 'self.repo_config',),
        (SystemMonitor, 'self.system_monitor_name',
         'self.system_monitoring_period', 'self.system_config',),
        (ChainlinkNodeMonitor, 'self.node_monitor_name',
         'self.node_monitoring_period', 'self.chainlink_node_config',),
        (EVMNodeMonitor, 'self.node_monitor_name',
         'self.node_monitoring_period', 'self.evm_node_config',),
    ])
    @mock.patch("src.monitors.starters._initialise_monitor_logger")
    def test_initialise_monitor_calls_initialise_logger_correctly(
            self, monitor_type, monitor_display_name, monitoring_period, config,
            mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_monitor(monitor_type, eval(monitor_display_name),
                            eval(monitoring_period), eval(config))

        mock_init_logger.assert_called_once_with(
            eval(monitor_display_name), monitor_type.__name__
        )

    @mock.patch("src.monitors.starters._initialise_monitor_logger")
    def test_initialise_cl_contracts_monitor_calls_initialise_logger_correctly(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_chainlink_contracts_monitor(
            self.cl_contracts_monitor_name,
            self.chainlink_contracts_monitoring_period, self.weiwatchers_url,
            self.evm_nodes, self.node_configs)

        mock_init_logger.assert_called_once_with(
            self.cl_contracts_monitor_name, ChainlinkContractsMonitor.__name__
        )

    @parameterized.expand([
        (GitHubMonitor, 'self.github_monitor_name',
         'self.github_monitoring_period', 'self.repo_config',
         'self.test_github_monitor'),
        (SystemMonitor, 'self.system_monitor_name',
         'self.system_monitoring_period', 'self.system_config',
         'self.test_system_monitor'),
        (ChainlinkNodeMonitor, 'self.node_monitor_name',
         'self.node_monitoring_period', 'self.chainlink_node_config',
         'self.test_chainlink_node_monitor'),
        (EVMNodeMonitor, 'self.node_monitor_name',
         'self.node_monitoring_period', 'self.evm_node_config',
         'self.test_evm_node_monitor'),
    ])
    @mock.patch('src.monitors.node.evm.Web3')
    @mock.patch('src.monitors.starters.RabbitMQApi')
    @mock.patch("src.monitors.starters._initialise_monitor_logger")
    def test_initialise_monitor_creates_monitor_correctly(
            self, monitor_type, monitor_display_name, monitoring_period, config,
            monitor, mock_init_logger, mock_rabbit, mock_web3) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_web3.return_value = self.test_evm_node_monitor.w3_interface
        mock_rabbit.return_value = self.rabbitmq
        mock_rabbit.__name__ = RabbitMQApi.__name__

        actual_output = _initialise_monitor(
            monitor_type, eval(monitor_display_name), eval(monitoring_period),
            eval(config))

        self.assertEqual(eval(monitor).__dict__, actual_output.__dict__)

    @mock.patch('src.monitors.starters.ChainlinkContractsMonitor')
    @mock.patch("src.monitors.starters._initialise_monitor_logger")
    def test_initialise_cl_contracts_monitor_creates_and_returns_monitor(
            self, mock_init_logger, mock_cl_contracts_monitor) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_cl_contracts_monitor.return_value = \
            self.test_chainlink_contracts_monitor
        mock_cl_contracts_monitor.__name__ = ChainlinkContractsMonitor.__name__

        actual_output = _initialise_chainlink_contracts_monitor(
            self.cl_contracts_monitor_name,
            self.chainlink_contracts_monitoring_period, self.weiwatchers_url,
            self.evm_nodes, self.node_configs)
        self.assertEqual(self.test_chainlink_contracts_monitor, actual_output)

    @mock.patch("src.monitors.starters._initialise_monitor")
    @mock.patch('src.monitors.starters.start_monitor')
    def test_start_system_monitor_calls_sub_functions_correctly(
            self, mock_start_monitor, mock_initialise_monitor) -> None:
        mock_start_monitor.return_value = None
        mock_initialise_monitor.return_value = self.test_system_monitor

        start_system_monitor(self.system_config)

        mock_start_monitor.assert_called_once_with(self.test_system_monitor)
        mock_initialise_monitor.assert_called_once_with(
            SystemMonitor,
            SYSTEM_MONITOR_NAME_TEMPLATE.format(self.system_config.system_name),
            env.SYSTEM_MONITOR_PERIOD_SECONDS, self.system_config
        )

    @mock.patch("src.monitors.starters._initialise_monitor")
    @mock.patch('src.monitors.starters.start_monitor')
    def test_start_github_monitor_calls_sub_functions_correctly(
            self, mock_start_monitor, mock_initialise_monitor) -> None:
        mock_start_monitor.return_value = None
        mock_initialise_monitor.return_value = self.test_github_monitor

        start_github_monitor(self.repo_config)

        mock_start_monitor.assert_called_once_with(self.test_github_monitor)
        mock_initialise_monitor.assert_called_once_with(
            GitHubMonitor,
            GITHUB_MONITOR_NAME_TEMPLATE.format(
                self.repo_config.repo_name.replace('/', ' ')[:-1]),
            env.GITHUB_MONITOR_PERIOD_SECONDS, self.repo_config
        )

    @parameterized.expand([
        ('self.test_chainlink_node_monitor', 'self.chainlink_node_config',
         ChainlinkNodeMonitor,),
        ('self.test_evm_node_monitor', 'self.evm_node_config',
         EVMNodeMonitor,),
    ])
    @mock.patch("src.monitors.starters._initialise_monitor")
    @mock.patch('src.monitors.starters.start_monitor')
    def test_start_node_monitor_calls_sub_functions_correctly(
            self, monitor, node_config, monitor_type, mock_start_monitor,
            mock_initialise_monitor) -> None:
        mock_start_monitor.return_value = None
        mock_initialise_monitor.return_value = eval(monitor)

        start_node_monitor(eval(node_config), monitor_type)

        mock_start_monitor.assert_called_once_with(eval(monitor))
        mock_initialise_monitor.assert_called_once_with(
            monitor_type, NODE_MONITOR_NAME_TEMPLATE.format(
                eval(node_config).node_name), env.NODE_MONITOR_PERIOD_SECONDS,
            eval(node_config)
        )

    @mock.patch("src.monitors.starters._initialise_chainlink_contracts_monitor")
    @mock.patch('src.monitors.starters.start_monitor')
    def test_start_chainlink_contracts_monitor_calls_sub_functions_correctly(
            self, mock_start_monitor,
            mock_initialise_cl_contracts_monitor) -> None:
        mock_start_monitor.return_value = None
        mock_initialise_cl_contracts_monitor.return_value = \
            self.test_chainlink_contracts_monitor
        test_parent_id = 'test_parent_id'
        monitor_display_name = CL_CONTRACTS_MONITOR_NAME_TEMPLATE.format(
            test_parent_id)

        start_chainlink_contracts_monitor(self.weiwatchers_url, self.evm_nodes,
                                          self.node_configs, test_parent_id)

        mock_start_monitor.assert_called_once_with(
            self.test_chainlink_contracts_monitor)
        mock_initialise_cl_contracts_monitor.assert_called_once_with(
            monitor_display_name,
            env.CHAINLINK_CONTRACTS_MONITOR_PERIOD_SECONDS,
            self.weiwatchers_url, self.evm_nodes, self.node_configs
        )
