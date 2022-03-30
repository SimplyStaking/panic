import logging
import unittest
from datetime import timedelta
from unittest import mock

from parameterized import parameterized

from src.data_store.starters import (
    _initialise_store_logger, _initialise_store, start_system_store,
    start_github_store, start_dockerhub_store, start_alert_store,
    start_chainlink_node_store, start_monitorable_store)
from src.data_store.stores.alert import AlertStore
from src.data_store.stores.dockerhub import DockerhubStore
from src.data_store.stores.github import GithubStore
from src.data_store.stores.monitorable import MonitorableStore
from src.data_store.stores.node.chainlink import ChainlinkNodeStore
from src.data_store.stores.system import SystemStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (SYSTEM_STORE_NAME, GITHUB_STORE_NAME,
                                       DOCKERHUB_STORE_NAME, ALERT_STORE_NAME,
                                       CL_NODE_STORE_NAME,
                                       MONITORABLE_STORE_NAME)


class TestAlertersStarters(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True

        self.github_store_name = 'test_github_store'
        self.dockerhub_store_name = 'test_dockerhub_store'
        self.system_store_name = 'test_system_store'
        self.alerter_store_name = 'alerter_store_name'
        self.cl_node_store_name = 'cl_node_store_name'
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.test_github_store = GithubStore(GITHUB_STORE_NAME,
                                             self.dummy_logger,
                                             self.rabbitmq)
        self.test_dockerhub_store = DockerhubStore(DOCKERHUB_STORE_NAME,
                                                   self.dummy_logger,
                                                   self.rabbitmq)
        self.test_system_store = SystemStore(SYSTEM_STORE_NAME,
                                             self.dummy_logger,
                                             self.rabbitmq)
        self.test_alert_store = AlertStore(ALERT_STORE_NAME,
                                           self.dummy_logger,
                                           self.rabbitmq)
        self.test_monitorable_store = MonitorableStore(MONITORABLE_STORE_NAME,
                                                       self.dummy_logger,
                                                       self.rabbitmq)
        self.test_cl_node_store = ChainlinkNodeStore(CL_NODE_STORE_NAME,
                                                     self.dummy_logger,
                                                     self.rabbitmq)

    def tearDown(self) -> None:
        self.rabbitmq = None
        self.dummy_logger = None
        self.test_github_store = None
        self.test_dockerhub_store = None
        self.test_system_store = None
        self.test_alert_store = None
        self.test_monitorable_store = None
        self.test_cl_node_store = None

    @parameterized.expand([
        (GITHUB_STORE_NAME, GithubStore.__name__,),
        (DOCKERHUB_STORE_NAME, DockerhubStore.__name__),
        (SYSTEM_STORE_NAME, SystemStore.__name__,),
        (CL_NODE_STORE_NAME, ChainlinkNodeStore.__name__,),
        (ALERT_STORE_NAME, AlertStore.__name__,),
        (MONITORABLE_STORE_NAME, MonitorableStore.__name__,),
    ])
    @mock.patch("src.data_store.starters.create_logger")
    def test_initialise_store_logger_initialises_logger_correctly(
            self, store_display_name, store_module_name,
            mock_create_logger) -> None:
        mock_create_logger.return_value = None

        _initialise_store_logger(store_display_name, store_module_name)

        mock_create_logger.assert_called_once_with(
            env.DATA_STORE_LOG_FILE_TEMPLATE.format(store_display_name),
            store_module_name, env.LOGGING_LEVEL, rotating=True)

    @parameterized.expand([
        (GITHUB_STORE_NAME, GithubStore.__name__, 'mock_github_store',),
        (DOCKERHUB_STORE_NAME, DockerhubStore.__name__, 'mock_dockerhub_store'),
        (SYSTEM_STORE_NAME, SystemStore.__name__, 'mock_system_store',),
        (CL_NODE_STORE_NAME, ChainlinkNodeStore.__name__,
         'mock_cl_node_store',),
        (ALERT_STORE_NAME, AlertStore.__name__, 'mock_alert_store',),
        (MONITORABLE_STORE_NAME, MonitorableStore.__name__,
         'mock_monitorable_store',),
    ])
    @mock.patch("src.data_store.starters.RabbitMQApi")
    @mock.patch("src.data_store.starters.ChainlinkNodeStore")
    @mock.patch("src.data_store.starters.SystemStore")
    @mock.patch("src.data_store.starters.MonitorableStore")
    @mock.patch("src.data_store.starters.AlertStore")
    @mock.patch("src.data_store.starters.DockerhubStore")
    @mock.patch("src.data_store.starters.GithubStore")
    @mock.patch("src.data_store.starters._initialise_store_logger")
    def test_initialise_store_initialises_store_correctly(
            self, store_display_name, store_module_name, enabled_mock_variable,
            mock_init_logger, mock_github_store, mock_dockerhub_store,
            mock_alert_store, mock_monitorable_store, mock_system_store,
            mock_cl_node_store, mock_rabbit) -> None:
        mock_init_logger.return_value = self.dummy_logger
        mock_var = eval(enabled_mock_variable)
        mock_var.__name__ = store_module_name
        mock_rabbit.__name__ = 'RabbitMQApi'
        mock_rabbit.return_value = self.rabbitmq

        _initialise_store(mock_var, store_display_name)

        mock_init_logger.assert_called_once_with(store_display_name,
                                                 store_module_name)
        mock_var.assert_called_once_with(store_display_name, self.dummy_logger,
                                         self.rabbitmq)

    @parameterized.expand([
        ('self.test_github_store', start_github_store, GithubStore,
         GITHUB_STORE_NAME,),
        ('self.test_dockerhub_store', start_dockerhub_store, DockerhubStore,
         DOCKERHUB_STORE_NAME),
        ('self.test_system_store', start_system_store, SystemStore,
         SYSTEM_STORE_NAME,),
        ('self.test_cl_node_store', start_chainlink_node_store,
         ChainlinkNodeStore, CL_NODE_STORE_NAME,),
        ('self.test_alert_store', start_alert_store, AlertStore,
         ALERT_STORE_NAME,),
        ('self.test_monitorable_store', start_monitorable_store,
         MonitorableStore, MONITORABLE_STORE_NAME,),
    ])
    @mock.patch("src.data_store.starters._initialise_store")
    @mock.patch("src.data_store.starters.start_store")
    def test_start_store_functions_call_sub_functions_correctly(
            self, initialised_store, start_function, store_type,
            store_display_name, mock_start_store, mock_init_store) -> None:
        mock_init_store.return_value = eval(initialised_store)
        start_function()
        mock_start_store.assert_called_once_with(eval(initialised_store))
        mock_init_store.assert_called_once_with(store_type, store_display_name)
