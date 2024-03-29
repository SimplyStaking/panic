import copy
import logging
import unittest
from datetime import timedelta
from unittest import mock

from src.alerter.alerter_starters import (
    _initialise_alerter_logger, _initialise_system_alerter,
    _initialise_github_alerter, _initialise_dockerhub_alerter,
    _initialise_chainlink_node_alerter, _initialise_chainlink_contract_alerter,
    _initialise_evm_node_alerter, start_github_alerter, start_system_alerter,
    start_chainlink_node_alerter, start_evm_node_alerter,
    start_chainlink_contract_alerter, _initialise_cosmos_node_alerter,
    start_cosmos_node_alerter, _initialise_cosmos_network_alerter,
    start_cosmos_network_alerter, start_dockerhub_alerter,
    _initialise_substrate_node_alerter, start_substrate_node_alerter,
    _initialise_substrate_network_alerter, start_substrate_network_alerter)
from src.alerter.alerters.contract.chainlink import ChainlinkContractAlerter
from src.alerter.alerters.dockerhub import DockerhubAlerter
from src.alerter.alerters.github import GithubAlerter
from src.alerter.alerters.network.cosmos import CosmosNetworkAlerter
from src.alerter.alerters.network.substrate import SubstrateNetworkAlerter
from src.alerter.alerters.node.chainlink import ChainlinkNodeAlerter
from src.alerter.alerters.node.cosmos import CosmosNodeAlerter
from src.alerter.alerters.node.evm import EVMNodeAlerter
from src.alerter.alerters.node.substrate import SubstrateNodeAlerter
from src.alerter.alerters.system import SystemAlerter
from src.configs.factory.alerts.chainlink_alerts import (
    ChainlinkNodeAlertsConfigsFactory, ChainlinkContractAlertsConfigsFactory)
from src.configs.factory.alerts.cosmos_alerts import (
    CosmosNodeAlertsConfigsFactory, CosmosNetworkAlertsConfigsFactory)
from src.configs.factory.alerts.evm_alerts import EVMNodeAlertsConfigsFactory
from src.configs.factory.alerts.substrate_alerts import (
    SubstrateNodeAlertsConfigsFactory, SubstrateNetworkAlertsConfigsFactory)
from src.configs.factory.alerts.system_alerts import SystemAlertsConfigsFactory
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (
    SYSTEM_ALERTER_NAME, CHAINLINK_NODE_ALERTER_NAME,
    CHAINLINK_CONTRACT_ALERTER_NAME, EVM_NODE_ALERTER_NAME,
    COSMOS_NODE_ALERTER_NAME, COSMOS_NETWORK_ALERTER_NAME,
    SUBSTRATE_NODE_ALERTER_NAME, SUBSTRATE_NETWORK_ALERTER_NAME)


# Tests adapted from monitor starters
class TestAlertersStarters(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.alerter_name = 'Test Alerter'
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        self.parent_id = 'test_parent_id'
        self.enabled_alert = "True"
        self.critical_threshold_percentage = 95
        self.critical_threshold_seconds = 300
        self.critical_repeat_seconds = 300
        self.critical_enabled = "True"
        self.warning_threshold_percentage = 85
        self.warning_threshold_seconds = 200
        self.warning_enabled = "True"
        self.base_config = {
            "name": "base_percent_config",
            "enabled": self.enabled_alert,
            "parent_id": self.parent_id,
            "critical_threshold": self.critical_threshold_percentage,
            "critical_repeat": self.critical_repeat_seconds,
            "critical_enabled": self.critical_enabled,
            "warning_threshold": self.warning_threshold_percentage,
            "warning_enabled": self.warning_enabled
        }

        self.open_file_descriptors = copy.deepcopy(self.base_config)
        self.open_file_descriptors['name'] = "open_file_descriptors"

        self.system_cpu_usage = copy.deepcopy(self.base_config)
        self.system_cpu_usage['name'] = "system_cpu_usage"

        self.system_storage_usage = copy.deepcopy(self.base_config)
        self.system_storage_usage['name'] = "system_storage_usage"

        self.system_ram_usage = copy.deepcopy(self.base_config)
        self.system_ram_usage['name'] = "system_ram_usage"

        self.system_is_down = copy.deepcopy(self.base_config)
        self.system_is_down['name'] = "system_is_down"
        self.system_is_down['critical_threshold'] = \
            self.critical_threshold_seconds
        self.system_is_down['warning_threshold'] = \
            self.warning_threshold_seconds

        # Note github_alerter_name is the same as in the alerter_starters file
        self.github_alerter_name = "GitHub Alerter"

        # Similarly for Dockerhub
        self.dockerhub_alerter_name = "DockerHub Alerter"

        self.system_alerts_configs_factory = SystemAlertsConfigsFactory()

        self.test_system_alerter = SystemAlerter(
            self.alerter_name,
            self.dummy_logger,
            self.system_alerts_configs_factory,
            self.rabbitmq,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_github_alerter = GithubAlerter(
            self.github_alerter_name,
            self.dummy_logger,
            self.rabbitmq,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_dockerhub_alerter = DockerhubAlerter(
            self.dockerhub_alerter_name,
            self.dummy_logger,
            self.rabbitmq,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.evm_node_alerts_configs_factory = EVMNodeAlertsConfigsFactory()
        self.chainlink_node_alerts_configs_factory = \
            ChainlinkNodeAlertsConfigsFactory()
        self.chainlink_contract_alerts_configs_factory = \
            ChainlinkContractAlertsConfigsFactory()
        self.cosmos_node_alerts_configs_factory = \
            CosmosNodeAlertsConfigsFactory()
        self.cosmos_network_alerts_configs_factory = \
            CosmosNetworkAlertsConfigsFactory()
        self.substrate_node_alerts_configs_factory = \
            SubstrateNodeAlertsConfigsFactory()
        self.substrate_network_alerts_configs_factory = \
            SubstrateNetworkAlertsConfigsFactory()

        self.test_chainlink_node_alerter = ChainlinkNodeAlerter(
            CHAINLINK_NODE_ALERTER_NAME, self.dummy_logger,
            self.rabbitmq, self.chainlink_node_alerts_configs_factory,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_chainlink_contract_alerter = ChainlinkContractAlerter(
            CHAINLINK_CONTRACT_ALERTER_NAME, self.dummy_logger,
            self.rabbitmq, self.chainlink_contract_alerts_configs_factory,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_evm_node_alerter = EVMNodeAlerter(
            EVM_NODE_ALERTER_NAME, self.dummy_logger,
            self.evm_node_alerts_configs_factory, self.rabbitmq,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_cosmos_node_alerter = CosmosNodeAlerter(
            COSMOS_NODE_ALERTER_NAME, self.dummy_logger, self.rabbitmq,
            self.cosmos_node_alerts_configs_factory,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_cosmos_network_alerter = CosmosNetworkAlerter(
            COSMOS_NETWORK_ALERTER_NAME, self.dummy_logger, self.rabbitmq,
            self.cosmos_network_alerts_configs_factory,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_substrate_node_alerter = SubstrateNodeAlerter(
            SUBSTRATE_NODE_ALERTER_NAME, self.dummy_logger, self.rabbitmq,
            self.substrate_node_alerts_configs_factory,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.test_substrate_network_alerter = SubstrateNetworkAlerter(
            SUBSTRATE_NETWORK_ALERTER_NAME, self.dummy_logger, self.rabbitmq,
            self.substrate_network_alerts_configs_factory,
            env.ALERTER_PUBLISHING_QUEUE_SIZE
        )

        self.system_id = 'test_system_id'
        self.system_parent_id = 'test_system_parent_id'
        self.system_name = 'test_system'
        self.chain_name = 'chain'

    def tearDown(self) -> None:
        self.dummy_logger = None
        self.test_github_alerter = None
        self.test_dockerhub_alerter = None
        self.rabbitmq = None
        self.system_alerts_configs_factory = None
        self.test_system_alerter = None
        self.evm_node_alerts_configs_factory = None
        self.chainlink_node_alerts_configs_factory = None
        self.chainlink_contract_alerts_configs_factory = None
        self.cosmos_node_alerts_configs_factory = None
        self.cosmos_network_alerts_configs_factory = None
        self.substrate_node_alerts_configs_factory = None
        self.substrate_network_alerts_configs_factory = None
        self.test_chainlink_node_alerter = None
        self.test_chainlink_contract_alerter = None
        self.test_evm_node_alerter = None
        self.test_cosmos_node_alerter = None
        self.test_cosmos_network_alerter = None
        self.test_substrate_node_alerter = None
        self.test_substrate_network_alerter = None

    @mock.patch("src.alerter.alerter_starters.create_logger")
    def test_initialise_alerter_logger_calls_create_logger_correctly(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = None

        _initialise_alerter_logger(SYSTEM_ALERTER_NAME, self.alerter_name)

        mock_create_logger.assert_called_once_with(
            env.ALERTERS_LOG_FILE_TEMPLATE.format(SYSTEM_ALERTER_NAME),
            self.alerter_name, env.LOGGING_LEVEL, rotating=True
        )

    @mock.patch("src.alerter.alerter_starters.create_logger")
    def test_initialise_alerter_logger_returns_created_logger_if_init_correct(
            self, mock_create_logger) -> None:
        mock_create_logger.return_value = self.dummy_logger

        actual_output = _initialise_alerter_logger(SYSTEM_ALERTER_NAME,
                                                   self.alerter_name)

        self.assertEqual(self.dummy_logger, actual_output)

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_system_alerter_calls_initialise_logger_correctly(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_system_alerter(self.system_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(SYSTEM_ALERTER_NAME,
                                                 SystemAlerter.__name__)

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_github_alerter_calls_initialise_logger_correctly(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_github_alerter()

        mock_init_logger.assert_called_once_with(
            self.github_alerter_name,
            GithubAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_dockerhub_alerter_calls_initialise_logger_correctly(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_dockerhub_alerter()

        mock_init_logger.assert_called_once_with(
            self.dockerhub_alerter_name,
            DockerhubAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_chainlink_node_alerter_calls_initialise_logger_correct(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_chainlink_node_alerter(
            self.chainlink_node_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(
            CHAINLINK_NODE_ALERTER_NAME,
            ChainlinkNodeAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_chainlink_contract_alerter_calls_init_logger_correct(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_chainlink_contract_alerter(
            self.chainlink_contract_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(
            CHAINLINK_CONTRACT_ALERTER_NAME,
            ChainlinkContractAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_evm_node_alerter_calls_initialise_logger_correctly(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_evm_node_alerter(
            self.evm_node_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(
            EVM_NODE_ALERTER_NAME,
            EVMNodeAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_cosmos_node_alerter_calls_initialise_logger_correctly(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_cosmos_node_alerter(self.cosmos_node_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(
            COSMOS_NODE_ALERTER_NAME, CosmosNodeAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_cosmos_network_alerter_calls_initialise_logger_correct(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_cosmos_network_alerter(
            self.cosmos_network_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(
            COSMOS_NETWORK_ALERTER_NAME, CosmosNetworkAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_substrate_node_alerter_calls_initialise_logger_correct(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_substrate_node_alerter(
            self.substrate_node_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(
            SUBSTRATE_NODE_ALERTER_NAME, SubstrateNodeAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    def test_initialise_substrate_network_alerter_calls_initialise_logger_correct(
            self, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger

        _initialise_substrate_network_alerter(
            self.substrate_network_alerts_configs_factory)

        mock_init_logger.assert_called_once_with(
            SUBSTRATE_NETWORK_ALERTER_NAME, SubstrateNetworkAlerter.__name__
        )

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.SystemAlerter')
    def test_initialise_system_alerter_creates_system_alerter_correctly(
            self, mock_system_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_system_alerter.__name__ = "system_alerter_name"

        _initialise_system_alerter(self.system_alerts_configs_factory)

        args, _ = mock_system_alerter.call_args
        self.assertEqual(SYSTEM_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(self.system_alerts_configs_factory, args[2])
        self.assertEqual(type(self.rabbitmq), type(args[3]))
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.GithubAlerter')
    def test_initialise_github_alerter_creates_github_alerter_correctly(
            self, mock_github_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_github_alerter.__name__ = 'github_alerter_name'

        _initialise_github_alerter()

        args, _ = mock_github_alerter.call_args
        self.assertEqual(self.github_alerter_name, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[3])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.DockerhubAlerter')
    def test_initialise_dockerhub_alerter_creates_dockerhub_alerter_correctly(
            self, mock_dockerhub_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_dockerhub_alerter.__name__ = 'dockerhub_alerter_name'

        _initialise_dockerhub_alerter()

        args, _ = mock_dockerhub_alerter.call_args
        self.assertEqual(self.dockerhub_alerter_name, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[3])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.ChainlinkNodeAlerter')
    def test_initialise_chainlink_node_alerter_creates_cl_node_alerter_correct(
            self, mock_chainlink_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_chainlink_alerter.__name__ = 'chainlink_alerter_name'

        _initialise_chainlink_node_alerter(
            self.chainlink_node_alerts_configs_factory)

        args, _ = mock_chainlink_alerter.call_args
        self.assertEqual(CHAINLINK_NODE_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(self.chainlink_node_alerts_configs_factory, args[3])
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.ChainlinkContractAlerter')
    def test_initialise_chainlink_contract_alerter_creates_alerter_correctly(
            self, mock_chainlink_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_chainlink_alerter.__name__ = 'chainlink_alerter_name'

        _initialise_chainlink_contract_alerter(
            self.chainlink_contract_alerts_configs_factory)

        args, _ = mock_chainlink_alerter.call_args
        self.assertEqual(CHAINLINK_CONTRACT_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(self.chainlink_contract_alerts_configs_factory,
                         args[3])
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.EVMNodeAlerter')
    def test_initialise_evm_node_alerter_creates_evm_node_alerter_correctly(
            self, mock_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_alerter.__name__ = 'evm_alerter_name'

        _initialise_evm_node_alerter(
            self.evm_node_alerts_configs_factory)

        args, _ = mock_alerter.call_args
        self.assertEqual(EVM_NODE_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(self.evm_node_alerts_configs_factory, args[2])
        self.assertEqual(type(self.rabbitmq), type(args[3]))
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.CosmosNodeAlerter')
    def test_initialise_cosmos_node_alerter_creates_cosmos_node_alerter_correct(
            self, mock_cosmos_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_cosmos_alerter.__name__ = 'cosmos_alerter_name'

        _initialise_cosmos_node_alerter(self.cosmos_node_alerts_configs_factory)

        args, _ = mock_cosmos_alerter.call_args
        self.assertEqual(COSMOS_NODE_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(self.cosmos_node_alerts_configs_factory, args[3])
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.CosmosNetworkAlerter')
    def test_initialise_cosmos_network_alerter_creates_alerter_correctly(
            self, mock_cosmos_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_cosmos_alerter.__name__ = 'cosmos_alerter_name'

        _initialise_cosmos_network_alerter(
            self.cosmos_network_alerts_configs_factory)

        args, _ = mock_cosmos_alerter.call_args
        self.assertEqual(COSMOS_NETWORK_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(self.cosmos_network_alerts_configs_factory, args[3])
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.SubstrateNodeAlerter')
    def test_initialise_substrate_node_alerter_creates_alerter_correctly(
            self, mock_substrate_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_substrate_alerter.__name__ = 'substrate_alerter_name'

        _initialise_substrate_node_alerter(
            self.substrate_node_alerts_configs_factory)

        args, _ = mock_substrate_alerter.call_args
        self.assertEqual(SUBSTRATE_NODE_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(self.substrate_node_alerts_configs_factory, args[3])
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_alerter_logger")
    @mock.patch('src.alerter.alerter_starters.SubstrateNetworkAlerter')
    def test_initialise_substrate_network_alerter_creates_alerter_correctly(
            self, mock_substrate_alerter, mock_init_logger) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_substrate_alerter.__name__ = 'substrate_alerter_name'

        _initialise_substrate_network_alerter(
            self.substrate_network_alerts_configs_factory)

        args, _ = mock_substrate_alerter.call_args
        self.assertEqual(SUBSTRATE_NETWORK_ALERTER_NAME, args[0])
        self.assertEqual(self.dummy_logger, args[1])
        self.assertEqual(type(self.rabbitmq), type(args[2]))
        self.assertEqual(self.substrate_network_alerts_configs_factory, args[3])
        self.assertEqual(env.ALERTER_PUBLISHING_QUEUE_SIZE, args[4])

    @mock.patch("src.alerter.alerter_starters._initialise_system_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_system_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_system_alerter

        start_system_alerter(self.system_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_system_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.system_alerts_configs_factory
        )

    @mock.patch("src.alerter.alerter_starters._initialise_github_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_github_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_github_alerter

        start_github_alerter()

        mock_start_alerter.assert_called_once_with(
            self.test_github_alerter
        )
        mock_initialise_alerter.assert_called_once()

    @mock.patch("src.alerter.alerter_starters._initialise_dockerhub_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_dockerhub_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_dockerhub_alerter

        start_dockerhub_alerter()

        mock_start_alerter.assert_called_once_with(self.test_dockerhub_alerter)
        mock_initialise_alerter.assert_called_once()

    @mock.patch(
        "src.alerter.alerter_starters._initialise_chainlink_node_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_chainlink_node_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_chainlink_node_alerter

        start_chainlink_node_alerter(
            self.chainlink_node_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_chainlink_node_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.chainlink_node_alerts_configs_factory)

    @mock.patch(
        "src.alerter.alerter_starters._initialise_evm_node_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_evm_node_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_evm_node_alerter

        start_evm_node_alerter(self.evm_node_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_evm_node_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.evm_node_alerts_configs_factory)

    @mock.patch(
        "src.alerter.alerter_starters._initialise_chainlink_contract_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_chainlink_contract_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = \
            self.test_chainlink_contract_alerter

        start_chainlink_contract_alerter(
            self.chainlink_contract_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_chainlink_contract_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.chainlink_contract_alerts_configs_factory)

    @mock.patch("src.alerter.alerter_starters._initialise_cosmos_node_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_cosmos_node_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_cosmos_node_alerter

        start_cosmos_node_alerter(self.cosmos_node_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_cosmos_node_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.cosmos_node_alerts_configs_factory)

    @mock.patch(
        "src.alerter.alerter_starters._initialise_cosmos_network_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_cosmos_network_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_cosmos_network_alerter

        start_cosmos_network_alerter(self.cosmos_network_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_cosmos_network_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.cosmos_network_alerts_configs_factory)

    @mock.patch(
        "src.alerter.alerter_starters._initialise_substrate_node_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_substrate_node_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = self.test_substrate_node_alerter

        start_substrate_node_alerter(
            self.substrate_node_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_substrate_node_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.substrate_node_alerts_configs_factory)

    @mock.patch(
        "src.alerter.alerter_starters._initialise_substrate_network_alerter")
    @mock.patch('src.alerter.alerter_starters.start_alerter')
    def test_start_substrate_network_alerter_calls_sub_functions_correctly(
            self, mock_start_alerter, mock_initialise_alerter) -> None:
        mock_start_alerter.return_value = None
        mock_initialise_alerter.return_value = (
            self.test_substrate_network_alerter)

        start_substrate_network_alerter(
            self.substrate_network_alerts_configs_factory)

        mock_start_alerter.assert_called_once_with(
            self.test_substrate_network_alerter
        )
        mock_initialise_alerter.assert_called_once_with(
            self.substrate_network_alerts_configs_factory)
