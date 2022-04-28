import logging
import unittest
from abc import ABC
from datetime import timedelta, datetime
from unittest import mock
from unittest.mock import call

import pika
from parameterized import parameterized
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.publisher_subscriber import (
    QueuingPublisherSubscriberComponent)
from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.manager import MonitorsManager
from src.monitors.node.chainlink import ChainlinkNodeMonitor
from src.monitors.node.evm import EVMNodeMonitor
from src.utils import env
from src.utils.constants.monitorables import MonitorableType
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY,
    MONITORABLE_EXCHANGE)
from src.utils.exceptions import PANICException
from test.test_utils.utils import (
    connect_to_rabbit, delete_queue_if_exists, delete_exchange_if_exists,
    disconnect_from_rabbit)


class MonitorManagerInstance(MonitorsManager, ABC):
    def __init__(
            self, logger: logging.Logger, name: str,
            rabbitmq: RabbitMQApi) -> None:
        super().__init__(logger, name, rabbitmq)

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        pass

    def process_and_send_monitorable_data(
            self, base_chain: str, monitorable_type: MonitorableType) -> None:
        pass

    def _initialise_rabbitmq(self) -> None:
        pass


class TestMonitorsManager(unittest.TestCase):

    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_monitors_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.test_exception = PANICException('test_exception', 1)

        # dummy variables
        self.chain_id_1 = 'chain_id_1'
        self.chain_1 = 'base_chain_1 sub_chain_1'
        self.base_chain_1 = 'base_chain_1'
        self.sub_chain_1 = 'sub_chain_1'
        self.chain_id_2 = 'chain_id_2'
        self.chain_2 = 'base_chain_2 sub_chain_2'
        self.base_chain_2 = 'base_chain_2'
        self.sub_chain_2 = 'sub_chain_2'

        # github
        self.github_component_name_1 = 'GitHub monitor (source_name_1)'
        self.github_source_id_1 = 'repo_1'
        self.github_source_name_1 = 'source_name_1'
        self.github_component_name_2 = 'GitHub monitor (source_name_2)'
        self.github_source_id_2 = 'repo_2'
        self.github_source_name_2 = 'source_name_2'

        # github none
        self.test_github_config_process_dict_none = {}
        self.test_github_config_process_dict_none_expected = {
            'manager_name': self.manager_name,
            'sources': []
        }

        # github single
        self.test_github_config_process_dict_single = {
            self.github_source_id_1: {
                'component_name': self.github_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.github_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
            }
        }
        self.test_github_config_process_dict_single_expected = {
            'manager_name': self.manager_name,
            'sources': [
                {
                    'chain_id': self.chain_id_1,
                    'chain_name': self.sub_chain_1,
                    'source_id': self.github_source_id_1,
                    'source_name': self.github_source_name_1,
                }
            ]
        }

        # github multiple
        self.test_github_config_process_dict_multiple = {
            self.github_source_id_1: {
                'component_name': self.github_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.github_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
            },
            self.github_source_id_2: {
                'component_name': self.github_component_name_2,
                'chain': self.chain_2,
                'parent_id': self.chain_id_2,
                'source_name': self.github_source_name_2,
                'base_chain': self.base_chain_2,
                'sub_chain': self.sub_chain_2,
            }
        }
        self.test_github_config_process_dict_multiple_expected = [
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_1,
                        'chain_name': self.sub_chain_1,
                        'source_id': self.github_source_id_1,
                        'source_name': self.github_source_name_1,
                    },
                ]
            },
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_2,
                        'chain_name': self.sub_chain_2,
                        'source_id': self.github_source_id_2,
                        'source_name': self.github_source_name_2,
                    },
                ]
            },
        ]

        # dockerhub
        self.dockerhub_component_name_1 = 'DockerHub monitor (source_name_1)'
        self.dockerhub_source_id_1 = 'repo_1'
        self.dockerhub_source_name_1 = 'source_name_1'
        self.dockerhub_component_name_2 = 'DockerHub monitor (source_name_2)'
        self.dockerhub_source_id_2 = 'repo_2'
        self.dockerhub_source_name_2 = 'source_name_2'

        # dockerhub none
        self.test_dockerhub_config_process_dict_none = {}
        self.test_dockerhub_config_process_dict_none_expected = {
            'manager_name': self.manager_name,
            'sources': []
        }

        # dockerhub single
        self.test_dockerhub_config_process_dict_single = {
            self.github_source_id_1: {
                'component_name': self.dockerhub_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.dockerhub_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
            }
        }
        self.test_dockerhub_config_process_dict_single_expected = {
            'manager_name': self.manager_name,
            'sources': [
                {
                    'chain_id': self.chain_id_1,
                    'chain_name': self.sub_chain_1,
                    'source_id': self.dockerhub_source_id_1,
                    'source_name': self.dockerhub_source_name_1,
                }
            ]
        }

        # dockerhub multiple
        self.test_dockerhub_config_process_dict_multiple = {
            self.dockerhub_source_id_1: {
                'component_name': self.dockerhub_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.dockerhub_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
            },
            self.dockerhub_source_id_2: {
                'component_name': self.dockerhub_component_name_2,
                'chain': self.chain_2,
                'parent_id': self.chain_id_2,
                'source_name': self.dockerhub_source_name_2,
                'base_chain': self.base_chain_2,
                'sub_chain': self.sub_chain_2,
            }
        }
        self.test_dockerhub_config_process_dict_multiple_expected = [
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_1,
                        'chain_name': self.sub_chain_1,
                        'source_id': self.dockerhub_source_id_1,
                        'source_name': self.dockerhub_source_name_1,
                    },
                ]
            },
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_2,
                        'chain_name': self.sub_chain_2,
                        'source_id': self.dockerhub_source_id_2,
                        'source_name': self.dockerhub_source_name_2,
                    },
                ]
            },
        ]

        # system
        self.system_component_name_1 = 'Systems monitor (source_name_1)'
        self.system_source_id_1 = 'repo_1'
        self.system_source_name_1 = 'source_name_1'
        self.system_component_name_2 = 'Systems monitor (source_name_2)'
        self.system_source_id_2 = 'repo_2'
        self.system_source_name_2 = 'source_name_2'

        # system none
        self.test_system_config_process_dict_none = {}
        self.test_system_config_process_dict_none_expected = {
            'manager_name': self.manager_name,
            'sources': []
        }

        # system single
        self.test_system_config_process_dict_single = {
            self.github_source_id_1: {
                'component_name': self.system_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.system_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
            }
        }
        self.test_system_config_process_dict_single_expected = {
            'manager_name': self.manager_name,
            'sources': [
                {
                    'chain_id': self.chain_id_1,
                    'chain_name': self.sub_chain_1,
                    'source_id': self.system_source_id_1,
                    'source_name': self.system_source_name_1,
                }
            ]
        }

        # system multiple
        self.test_system_config_process_dict_multiple = {
            self.system_source_id_1: {
                'component_name': self.system_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.system_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
            },
            self.system_source_id_2: {
                'component_name': self.system_component_name_2,
                'chain': self.chain_2,
                'parent_id': self.chain_id_2,
                'source_name': self.system_source_name_2,
                'base_chain': self.base_chain_2,
                'sub_chain': self.sub_chain_2,
            }
        }
        self.test_system_config_process_dict_multiple_expected = [
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_1,
                        'chain_name': self.sub_chain_1,
                        'source_id': self.system_source_id_1,
                        'source_name': self.system_source_name_1,
                    },
                ]
            },
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_2,
                        'chain_name': self.sub_chain_2,
                        'source_id': self.system_source_id_2,
                        'source_name': self.system_source_name_2,
                    },
                ]
            },
        ]

        # node
        self.node_component_name_1 = 'Node monitor (source_name_1)'
        self.node_source_id_1 = 'repo_1'
        self.node_source_name_1 = 'source_name_1'
        self.node_component_name_2 = 'Node monitor (source_name_2)'
        self.node_source_id_2 = 'repo_2'
        self.node_source_name_2 = 'source_name_2'

        # node none
        self.test_node_config_process_dict_none = {}
        self.test_node_config_process_dict_none_expected = {
            'manager_name': self.manager_name,
            'sources': []
        }

        # node single ChainlinkNodeMonitor
        self.test_node_chainlink_config_process_dict_single = {
            self.node_source_id_1: {
                'component_name': self.node_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.node_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
                'monitor_type': ChainlinkNodeMonitor
            }
        }
        self.test_node_chainlink_config_process_dict_single_expected = {
            'manager_name': self.manager_name,
            'sources': [
                {
                    'chain_id': self.chain_id_1,
                    'chain_name': self.sub_chain_1,
                    'source_id': self.node_source_id_1,
                    'source_name': self.node_source_name_1,
                }
            ]
        }

        # node single EVMNodeMonitor
        self.test_node_evm_config_process_dict_single = {
            self.node_source_id_1: {
                'component_name': self.node_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.node_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
                'monitor_type': EVMNodeMonitor
            }
        }
        self.test_node_evm_config_process_dict_single_expected = {
            'manager_name': self.manager_name,
            'sources': [
                {
                    'chain_id': self.chain_id_1,
                    'chain_name': self.sub_chain_1,
                    'source_id': self.node_source_id_1,
                    'source_name': self.node_source_name_1,
                }
            ]
        }

        # node multiple
        self.test_node_config_process_dict_multiple = {
            self.node_source_id_1: {
                'component_name': self.node_component_name_1,
                'chain': self.chain_1,
                'parent_id': self.chain_id_1,
                'source_name': self.node_source_name_1,
                'base_chain': self.base_chain_1,
                'sub_chain': self.sub_chain_1,
                'monitor_type': ChainlinkNodeMonitor
            },
            self.node_source_id_2: {
                'component_name': self.node_component_name_2,
                'chain': self.chain_2,
                'parent_id': self.chain_id_2,
                'source_name': self.node_source_name_2,
                'base_chain': self.base_chain_2,
                'sub_chain': self.sub_chain_2,
                'monitor_type': ChainlinkNodeMonitor
            }
        }
        self.test_node_config_process_dict_multiple_expected = [
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_1,
                        'chain_name': self.sub_chain_1,
                        'source_id': self.node_source_id_1,
                        'source_name': self.node_source_name_1,
                    },
                ]
            },
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_2,
                        'chain_name': self.sub_chain_2,
                        'source_id': self.node_source_id_2,
                        'source_name': self.node_source_name_2,
                    },
                ]
            },
        ]

        self.node_id_1 = 'node_1'
        self.parent_id_1 = 'parent_node_1'
        self.node_name_1 = 'node_name_1'
        self.monitor_node_1 = True
        self.monitor_prometheus_1 = True
        self.node_prometheus_urls_1 = ['url1', 'url2']
        self.node_id_2 = 'node_2'
        self.parent_id_2 = 'parent_node_2'
        self.node_name_2 = 'node_name_2'
        self.monitor_node_2 = True
        self.monitor_prometheus_2 = True
        self.node_prometheus_urls_2 = ['url1', 'url2']
        self.chainlink_node_config_1 = ChainlinkNodeConfig(
            self.node_id_1, self.parent_id_1, self.node_name_1,
            self.monitor_node_1, self.monitor_prometheus_1,
            self.node_prometheus_urls_1)
        self.chainlink_node_config_2 = ChainlinkNodeConfig(
            self.node_id_2, self.parent_id_1, self.node_name_2,
            self.monitor_node_2, self.monitor_prometheus_2,
            self.node_prometheus_urls_2)
        self.chainlink_node_configs_1 = [self.chainlink_node_config_1,
                                         self.chainlink_node_config_2]
        # contracts
        self.test_node_contracts_config_process_dict_expected = [
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'chain_id': self.chain_id_1,
                        'chain_name': self.sub_chain_1,
                        'source_id':
                            self.chainlink_node_configs_1[0].node_id,
                        'source_name':
                            self.chainlink_node_configs_1[0].node_name
                    },
                    {
                        'chain_id': self.chain_id_1,
                        'chain_name': self.sub_chain_1,
                        'source_id':
                            self.chainlink_node_configs_1[1].node_id,
                        'source_name':
                            self.chainlink_node_configs_1[1].node_name
                    }
                ]
            },
            {
                'manager_name': self.manager_name,
                'sources': [
                    {
                        'parent_id': self.chain_id_1,
                        'chain_name': self.sub_chain_1,
                        'source_id': self.chain_id_1,
                        'source_name': self.chain_1
                    },
                ]
            }
        ]

        self.test_manager = \
            MonitorManagerInstance(self.dummy_logger,
                                   self.manager_name,
                                   self.rabbitmq)

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               self.test_queue_name)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  MONITORABLE_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.rabbitmq = None
        self.connection_check_time_interval = None
        self.test_exception = None
        self.test_github_config_process_dict = None
        self.test_manager = None

    @parameterized.expand([
        ('self.test_github_config_process_dict_none',
         'self.test_github_config_process_dict_none_expected',
         MonitorableType.GITHUB_REPOS,),
        ('self.test_github_config_process_dict_single',
         'self.test_github_config_process_dict_single_expected',
         MonitorableType.GITHUB_REPOS,),
        ('self.test_github_config_process_dict_multiple',
         'self.test_github_config_process_dict_multiple_expected',
         MonitorableType.GITHUB_REPOS,),

        ('self.test_dockerhub_config_process_dict_none',
         'self.test_dockerhub_config_process_dict_none_expected',
         MonitorableType.DOCKERHUB_REPOS,),
        ('self.test_dockerhub_config_process_dict_single',
         'self.test_dockerhub_config_process_dict_single_expected',
         MonitorableType.DOCKERHUB_REPOS,),
        ('self.test_dockerhub_config_process_dict_multiple',
         'self.test_dockerhub_config_process_dict_multiple_expected',
         MonitorableType.DOCKERHUB_REPOS,),

        ('self.test_system_config_process_dict_none',
         'self.test_system_config_process_dict_none_expected',
         MonitorableType.SYSTEMS,),
        ('self.test_system_config_process_dict_single',
         'self.test_system_config_process_dict_single_expected',
         MonitorableType.SYSTEMS,),
        ('self.test_system_config_process_dict_multiple',
         'self.test_system_config_process_dict_multiple_expected',
         MonitorableType.SYSTEMS,),

        ('self.test_node_config_process_dict_none',
         'self.test_node_config_process_dict_none_expected',
         MonitorableType.NODES,),
        ('self.test_node_chainlink_config_process_dict_single',
         'self.test_node_chainlink_config_process_dict_single_expected',
         MonitorableType.NODES,),
        ('self.test_node_evm_config_process_dict_single',
         'self.test_node_evm_config_process_dict_single_expected',
         MonitorableType.NODES,),
        ('self.test_node_config_process_dict_multiple',
         'self.test_node_config_process_dict_multiple_expected',
         MonitorableType.NODES,),
    ])
    @mock.patch.object(MonitorsManager, "send_monitorable_data")
    def test_process_and_send_monitorable_data_processes_data_correctly(
            self, config_process_dict, expected_monitorable_data,
            monitorable_type, mock_send_mon_data) -> None:
        mock_send_mon_data.return_value = None

        self.test_manager._config_process_dict = eval(config_process_dict)
        num_sources = len(self.test_manager._config_process_dict.keys())

        if num_sources <= 1:
            self.test_manager.process_and_send_monitorable_data_generic(
                self.base_chain_1, monitorable_type)

            expected_routing_key = '{}.{}' \
                .format(self.base_chain_1, monitorable_type.value)

            mock_send_mon_data.assert_called_once_with(
                expected_routing_key, eval(expected_monitorable_data))

        elif num_sources > 1:

            expected_routing_keys = []
            for source, source_data \
                    in self.test_manager._config_process_dict.items():
                self.test_manager.process_and_send_monitorable_data_generic(
                    source_data['base_chain'], monitorable_type)
                expected_routing_keys.append('{}.{}'
                                             .format(source_data['base_chain'],
                                                     monitorable_type.value))

            expected_dict = eval(expected_monitorable_data)
            calls = [
                call(expected_routing_keys[c], expected_dict[c])
                for c in range(0, num_sources)
            ]

            mock_send_mon_data.assert_has_calls(calls)

        self.assertEqual(max(num_sources, 1), mock_send_mon_data.call_count)

    @parameterized.expand([
        ('self.test_github_config_process_dict_single_expected',
         MonitorableType.GITHUB_REPOS,),

        ('self.test_dockerhub_config_process_dict_single_expected',
         MonitorableType.DOCKERHUB_REPOS,),

        ('self.test_system_config_process_dict_single_expected',
         MonitorableType.SYSTEMS,),

        ('self.test_node_chainlink_config_process_dict_single_expected',
         MonitorableType.NODES,),
        ('self.test_node_evm_config_process_dict_single_expected',
         MonitorableType.NODES,),
    ])
    @mock.patch.object(QueuingPublisherSubscriberComponent, "_push_to_queue")
    @mock.patch.object(MonitorsManager, "_send_data")
    def test_send_monitorable_data(self, data, monitorable_type, mock_send_data,
                                   mock_push) -> None:
        mock_send_data.return_value = None
        mock_push.return_value = None

        data = eval(data)
        routing_key = '{}.{}'.format(self.base_chain_1, monitorable_type.value)
        self.test_manager.send_monitorable_data(routing_key, data)

        mock_push.assert_called_once_with(
            data, MONITORABLE_EXCHANGE, routing_key,
            pika.BasicProperties(delivery_mode=2)
        )
        mock_send_data.assert_called_once()

    @parameterized.expand([
        ('self.test_node_contracts_config_process_dict_expected',),
    ])
    @mock.patch.object(QueuingPublisherSubscriberComponent, "_push_to_queue")
    @mock.patch.object(MonitorsManager, "_send_data")
    def test_send_monitorable_data_contracts(self, data, mock_send_data,
                                             mock_push) -> None:
        mock_send_data.return_value = None
        mock_push.return_value = None

        data = eval(data)
        routing_key_nodes = '{}.{}'.format(self.base_chain_1,
                                           MonitorableType.NODES.value)
        routing_key_chains = '{}.{}'.format(self.base_chain_1,
                                            MonitorableType.CHAINS.value)

        self.test_manager.send_monitorable_data(routing_key_nodes,
                                                data[0])
        self.test_manager.send_monitorable_data(routing_key_chains,
                                                data[1])

        calls = [
            call(data[0], MONITORABLE_EXCHANGE, routing_key_nodes,
                 pika.BasicProperties(delivery_mode=2)),
            call(data[1], MONITORABLE_EXCHANGE, routing_key_chains,
                 pika.BasicProperties(delivery_mode=2)),
        ]

        mock_push.assert_has_calls(calls)
        self.assertEqual(2, mock_send_data.call_count)
