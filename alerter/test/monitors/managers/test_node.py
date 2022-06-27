import copy
import json
import logging
import multiprocessing
import unittest
from datetime import timedelta, datetime
from multiprocessing import Process
from unittest import mock
from unittest.mock import call

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.configs.nodes.chainlink import ChainlinkNodeConfig
from src.configs.nodes.evm import EVMNodeConfig
from src.configs.nodes.node import NodeConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.monitors.managers.node import NodeMonitorsManager
from src.monitors.monitor import Monitor
from src.monitors.node.chainlink import ChainlinkNodeMonitor
from src.monitors.node.cosmos import CosmosNodeMonitor
from src.monitors.node.evm import EVMNodeMonitor
from src.monitors.node.substrate import SubstrateNodeMonitor
from src.monitors.starters import start_node_monitor
from src.utils import env
from src.utils.constants.names import NODE_MONITOR_NAME_TEMPLATE
from src.utils.constants.rabbitmq import (
    HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE, NODE_MON_MAN_HEARTBEAT_QUEUE_NAME,
    NODE_MON_MAN_CONFIGS_QUEUE_NAME, MONITORABLE_EXCHANGE, PING_ROUTING_KEY,
    HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from src.utils.types import str_to_bool
from test.test_utils.utils import (
    infinite_fn, connect_to_rabbit, delete_queue_if_exists,
    disconnect_from_rabbit, delete_exchange_if_exists)
from test.utils.chainlink.chainlink import ChainlinkTestNodes
from test.utils.cosmos.cosmos import CosmosTestNodes
from test.utils.evm.evm import EVMTestNodes
from test.utils.substrate.substrate import SubstrateTestNodes


class TestNodeMonitorsManager(unittest.TestCase):
    def setUp(self) -> None:
        # Some dummy data
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_node_monitors_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp(),
        }
        self.test_exception = PANICException('test_exception', 1)
        self.empty_configs = {}

        # Some dummy processes
        self.dummy_process1 = Process(target=infinite_fn, args=())
        self.dummy_process1.daemon = True
        self.dummy_process2 = Process(target=infinite_fn, args=())
        self.dummy_process2.daemon = True
        self.dummy_process3 = Process(target=infinite_fn, args=())
        self.dummy_process3.daemon = True
        self.dummy_process4 = Process(target=infinite_fn, args=())
        self.dummy_process4.daemon = True
        self.dummy_process5 = Process(target=infinite_fn, args=())
        self.dummy_process5.daemon = True
        self.dummy_process6 = Process(target=infinite_fn, args=())
        self.dummy_process6.daemon = True
        self.dummy_process7 = Process(target=infinite_fn, args=())
        self.dummy_process7.daemon = True
        self.dummy_process8 = Process(target=infinite_fn, args=())
        self.dummy_process8.daemon = True
        self.dummy_process9 = Process(target=infinite_fn, args=())
        self.dummy_process9.daemon = True
        self.dummy_process10 = Process(target=infinite_fn, args=())
        self.dummy_process10.daemon = True
        self.dummy_process11 = Process(target=infinite_fn, args=())
        self.dummy_process11.daemon = True

        # Some dummy node configs
        self.cl_test_nodes = ChainlinkTestNodes()
        self.evm_test_nodes = EVMTestNodes()
        self.cosmos_test_nodes = CosmosTestNodes()
        self.substrate_test_nodes = SubstrateTestNodes()
        self.node_config_1 = self.cl_test_nodes.node_1
        self.node_config_2 = self.cl_test_nodes.node_2
        self.node_config_3 = NodeConfig('node_id_3', 'parent_id_3',
                                        'node_name_3', True)
        self.node_config_4 = self.evm_test_nodes.create_custom_node(
            'node_id_4', 'parent_id_4', 'node_name_4', True, 'node_http_url_4')
        self.node_config_5 = self.evm_test_nodes.create_custom_node(
            'node_id_5', 'parent_id_5', 'node_name_5', True, 'node_http_url_5')
        self.node_config_6 = self.cosmos_test_nodes.create_custom_node(
            'node_id_6', 'parent_id_6', 'node_name_6', True, True, 'prom_url_6',
            True, 'cosmos_rest_url_6', True, 'tendermint_rpc_url_6', True, True,
            True, 'operator_address_6'
        )
        self.node_config_7 = self.cosmos_test_nodes.create_custom_node(
            'node_id_7', 'parent_id_7', 'node_name_7', True, True, 'prom_url_7',
            True, 'cosmos_rest_url_7', True, 'tendermint_rpc_url_7', False,
            False, True, 'operator_address_7'
        )
        self.node_config_8 = self.cosmos_test_nodes.create_custom_node(
            'node_id_8', 'parent_id_8', 'node_name_8', True, True, 'prom_url_8',
            True, 'cosmos_rest_url_8', True, 'tendermint_rpc_url_8', False,
            False, False, 'operator_address_8'
        )
        self.node_config_9 = self.substrate_test_nodes.create_custom_node(
            'node_id_9', 'parent_id_9', 'node_name_9', True, 'node_ws_url_9',
            True, True, True, 'stash_address_9')
        self.node_config_10 = self.substrate_test_nodes.create_custom_node(
            'node_id_10', 'parent_id_10', 'node_name_10', True,
            'node_ws_url_10', True, False, False, 'stash_address_10')
        self.node_config_11 = self.substrate_test_nodes.create_custom_node(
            'node_id_11', 'parent_id_11', 'node_name_11', True,
            'node_ws_url_11', False, False, False, 'stash_address_11')

        # Some config_process_dict, node_configs and sent_configs examples
        self.config_process_dict_example = {
            self.node_config_1.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_1.node_name),
                'process': self.dummy_process1,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_1,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_1.node_name,
                'parent_id': self.node_config_1.parent_id,
                'args': ()
            },
            self.node_config_2.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_2.node_name),
                'process': self.dummy_process2,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_2,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_2.node_name,
                'parent_id': self.node_config_2.parent_id,
                'args': ()
            },
            self.node_config_3.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_3.node_name),
                'process': self.dummy_process3,
                'monitor_type': Monitor,
                'node_config': self.node_config_3,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_3.node_name,
                'parent_id': self.node_config_3.parent_id,
                'args': ()
            },
            self.node_config_4.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_4.node_name),
                'process': self.dummy_process4,
                'monitor_type': EVMNodeMonitor,
                'node_config': self.node_config_4,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_4.node_name,
                'parent_id': self.node_config_4.parent_id,
                'args': ()
            },
            self.node_config_5.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_5.node_name),
                'process': self.dummy_process5,
                'monitor_type': EVMNodeMonitor,
                'node_config': self.node_config_5,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_5.node_name,
                'parent_id': self.node_config_5.parent_id,
                'args': ()
            },
            self.node_config_6.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_6.node_name),
                'process': self.dummy_process6,
                'monitor_type': CosmosNodeMonitor,
                'node_config': self.node_config_6,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_6.node_name,
                'parent_id': self.node_config_6.parent_id,
                'args': ([self.node_config_7, self.node_config_6],)
            },
            self.node_config_7.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_7.node_name),
                'process': self.dummy_process7,
                'monitor_type': CosmosNodeMonitor,
                'node_config': self.node_config_7,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_7.node_name,
                'parent_id': self.node_config_7.parent_id,
                'args': ([self.node_config_6, self.node_config_7],)
            },
            self.node_config_8.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_8.node_name),
                'process': self.dummy_process8,
                'monitor_type': CosmosNodeMonitor,
                'node_config': self.node_config_8,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_8.node_name,
                'parent_id': self.node_config_8.parent_id,
                'args': ([self.node_config_7, self.node_config_6,
                          self.node_config_8],)
            },
            self.node_config_9.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_9.node_name),
                'process': self.dummy_process9,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': self.node_config_9,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_9.node_name,
                'parent_id': self.node_config_9.parent_id,
                'args': ([self.node_config_10, self.node_config_9],)
            },
            self.node_config_10.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_10.node_name),
                'process': self.dummy_process10,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': self.node_config_10,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_10.node_name,
                'parent_id': self.node_config_10.parent_id,
                'args': ([self.node_config_9, self.node_config_10],)
            },
            self.node_config_11.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_11.node_name),
                'process': self.dummy_process11,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': self.node_config_11,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_11.node_name,
                'parent_id': self.node_config_11.parent_id,
                'args': ([self.node_config_10, self.node_config_9,
                          self.node_config_11],)
            },
        }
        self.nodes_configs_example = {
            'chainlink Binance Smart Chain': {
                'nodes_config': {
                    self.node_config_1.node_id: {
                        'id': self.node_config_1.node_id,
                        'parent_id': self.node_config_1.parent_id,
                        'name': self.node_config_1.node_name,
                        'node_prometheus_urls': ','.join(
                            self.node_config_1.node_prometheus_urls),
                        'monitor_node': str(self.node_config_1.monitor_node),
                        'monitor_prometheus': str(
                            self.node_config_1.monitor_prometheus)
                    },
                    self.node_config_2.node_id: {
                        'id': self.node_config_2.node_id,
                        'parent_id': self.node_config_2.parent_id,
                        'name': self.node_config_2.node_name,
                        'node_prometheus_urls': ','.join(
                            self.node_config_2.node_prometheus_urls),
                        'monitor_node': str(self.node_config_2.monitor_node),
                        'monitor_prometheus': str(
                            self.node_config_2.monitor_prometheus)
                    },
                },
                'evm_nodes_config': {
                    self.node_config_4.node_id: {
                        'id': self.node_config_4.node_id,
                        'parent_id': self.node_config_4.parent_id,
                        'name': self.node_config_4.node_name,
                        'node_http_url': self.node_config_4.node_http_url,
                        'monitor_node': str(self.node_config_4.monitor_node),
                    },
                    self.node_config_5.node_id: {
                        'id': self.node_config_5.node_id,
                        'parent_id': self.node_config_5.parent_id,
                        'name': self.node_config_5.node_name,
                        'node_http_url': self.node_config_5.node_http_url,
                        'monitor_node': str(self.node_config_5.monitor_node),
                    },
                }
            },
            'TestBaseChain TestSubChain': {
                'nodes_config': {
                    self.node_config_3.node_id: {
                        'id': self.node_config_3.node_id,
                        'parent_id': self.node_config_3.parent_id,
                        'name': self.node_config_3.node_name,
                        'monitor_node': str(self.node_config_3.monitor_node),
                    }
                }
            },
            'cosmos cosmos': {
                'nodes_config': {
                    self.node_config_6.node_id: {
                        'id': self.node_config_6.node_id,
                        'parent_id': self.node_config_6.parent_id,
                        'name': self.node_config_6.node_name,
                        'cosmos_rest_url': self.node_config_6.cosmos_rest_url,
                        'monitor_cosmos_rest': str(
                            self.node_config_6.monitor_cosmos_rest),
                        'prometheus_url': self.node_config_6.prometheus_url,
                        'monitor_prometheus': str(
                            self.node_config_6.monitor_prometheus),
                        'is_validator': str(self.node_config_6.is_validator),
                        'monitor_node': str(self.node_config_6.monitor_node),
                        'is_archive_node': str(
                            self.node_config_6.is_archive_node),
                        'use_as_data_source': str(
                            self.node_config_6.use_as_data_source),
                        'operator_address': self.node_config_6.operator_address,
                        'monitor_tendermint_rpc': str(
                            self.node_config_6.monitor_tendermint_rpc),
                        'tendermint_rpc_url':
                            self.node_config_6.tendermint_rpc_url
                    },
                    self.node_config_7.node_id: {
                        'id': self.node_config_7.node_id,
                        'parent_id': self.node_config_7.parent_id,
                        'name': self.node_config_7.node_name,
                        'cosmos_rest_url': self.node_config_7.cosmos_rest_url,
                        'monitor_cosmos_rest': str(
                            self.node_config_7.monitor_cosmos_rest),
                        'prometheus_url': self.node_config_7.prometheus_url,
                        'monitor_prometheus': str(
                            self.node_config_7.monitor_prometheus),
                        'is_validator': str(self.node_config_7.is_validator),
                        'monitor_node': str(self.node_config_7.monitor_node),
                        'is_archive_node': str(
                            self.node_config_7.is_archive_node),
                        'use_as_data_source': str(
                            self.node_config_7.use_as_data_source),
                        'operator_address': self.node_config_7.operator_address,
                        'monitor_tendermint_rpc': str(
                            self.node_config_7.monitor_tendermint_rpc),
                        'tendermint_rpc_url':
                            self.node_config_7.tendermint_rpc_url
                    },
                    self.node_config_8.node_id: {
                        'id': self.node_config_8.node_id,
                        'parent_id': self.node_config_8.parent_id,
                        'name': self.node_config_8.node_name,
                        'cosmos_rest_url': self.node_config_8.cosmos_rest_url,
                        'monitor_cosmos_rest': str(
                            self.node_config_8.monitor_cosmos_rest),
                        'prometheus_url': self.node_config_8.prometheus_url,
                        'monitor_prometheus': str(
                            self.node_config_8.monitor_prometheus),
                        'is_validator': str(self.node_config_8.is_validator),
                        'monitor_node': str(self.node_config_8.monitor_node),
                        'is_archive_node': str(
                            self.node_config_8.is_archive_node),
                        'use_as_data_source': str(
                            self.node_config_8.use_as_data_source),
                        'operator_address': self.node_config_8.operator_address,
                        'monitor_tendermint_rpc': str(
                            self.node_config_8.monitor_tendermint_rpc),
                        'tendermint_rpc_url':
                            self.node_config_8.tendermint_rpc_url
                    }
                }
            },
            'substrate polkadot': {
                'nodes_config': {
                    self.node_config_9.node_id: {
                        'id': self.node_config_9.node_id,
                        'parent_id': self.node_config_9.parent_id,
                        'name': self.node_config_9.node_name,
                        'node_ws_url': self.node_config_9.node_ws_url,
                        'is_validator': str(self.node_config_9.is_validator),
                        'monitor_node': str(self.node_config_9.monitor_node),
                        'is_archive_node': str(
                            self.node_config_9.is_archive_node),
                        'use_as_data_source': str(
                            self.node_config_9.use_as_data_source),
                        'stash_address': self.node_config_9.stash_address,
                    },
                    self.node_config_10.node_id: {
                        'id': self.node_config_10.node_id,
                        'parent_id': self.node_config_10.parent_id,
                        'name': self.node_config_10.node_name,
                        'node_ws_url': self.node_config_10.node_ws_url,
                        'is_validator': str(self.node_config_10.is_validator),
                        'monitor_node': str(self.node_config_10.monitor_node),
                        'is_archive_node': str(
                            self.node_config_10.is_archive_node),
                        'use_as_data_source': str(
                            self.node_config_10.use_as_data_source),
                        'stash_address': self.node_config_10.stash_address,
                    },
                    self.node_config_11.node_id: {
                        'id': self.node_config_11.node_id,
                        'parent_id': self.node_config_11.parent_id,
                        'name': self.node_config_11.node_name,
                        'node_ws_url': self.node_config_11.node_ws_url,
                        'is_validator': str(self.node_config_11.is_validator),
                        'monitor_node': str(self.node_config_11.monitor_node),
                        'is_archive_node': str(
                            self.node_config_11.is_archive_node),
                        'use_as_data_source': str(
                            self.node_config_11.use_as_data_source),
                        'stash_address': self.node_config_11.stash_address,
                    },
                }
            }
        }
        self.sent_configs_example_chainlink = {
            self.node_config_1.node_id: {
                'id': self.node_config_1.node_id,
                'parent_id': self.node_config_1.parent_id,
                'name': self.node_config_1.node_name,
                'node_prometheus_urls': ','.join(
                    self.node_config_1.node_prometheus_urls),
                'monitor_node': str(self.node_config_1.monitor_node),
                'monitor_prometheus': str(self.node_config_1.monitor_prometheus)
            },
            self.node_config_2.node_id: {
                'id': self.node_config_2.node_id,
                'parent_id': self.node_config_2.parent_id,
                'name': self.node_config_2.node_name,
                'node_prometheus_urls': ','.join(
                    self.node_config_2.node_prometheus_urls),
                'monitor_node': str(self.node_config_2.monitor_node),
                'monitor_prometheus': str(self.node_config_2.monitor_prometheus)
            }
        }
        self.sent_configs_example_chainlink_evm = {
            self.node_config_4.node_id: {
                'id': self.node_config_4.node_id,
                'parent_id': self.node_config_4.parent_id,
                'name': self.node_config_4.node_name,
                'node_http_url': self.node_config_4.node_http_url,
                'monitor_node': str(self.node_config_4.monitor_node),
            },
            self.node_config_5.node_id: {
                'id': self.node_config_5.node_id,
                'parent_id': self.node_config_5.parent_id,
                'name': self.node_config_5.node_name,
                'node_http_url': self.node_config_5.node_http_url,
                'monitor_node': str(self.node_config_5.monitor_node),
            }
        }
        self.sent_configs_example_test_chain = {
            self.node_config_3.node_id: {
                'id': self.node_config_3.node_id,
                'parent_id': self.node_config_3.parent_id,
                'name': self.node_config_3.node_name,
                'monitor_node': str(self.node_config_3.monitor_node),
            }
        }
        self.sent_configs_example_cosmos = {
            self.node_config_6.node_id: {
                'id': self.node_config_6.node_id,
                'parent_id': self.node_config_6.parent_id,
                'name': self.node_config_6.node_name,
                'cosmos_rest_url': self.node_config_6.cosmos_rest_url,
                'monitor_cosmos_rest': str(
                    self.node_config_6.monitor_cosmos_rest),
                'prometheus_url': self.node_config_6.prometheus_url,
                'monitor_prometheus': str(
                    self.node_config_6.monitor_prometheus),
                'is_validator': str(self.node_config_6.is_validator),
                'monitor_node': str(self.node_config_6.monitor_node),
                'is_archive_node': str(self.node_config_6.is_archive_node),
                'use_as_data_source': str(
                    self.node_config_6.use_as_data_source),
                'operator_address': self.node_config_6.operator_address,
                'monitor_tendermint_rpc': str(
                    self.node_config_6.monitor_tendermint_rpc),
                'tendermint_rpc_url': self.node_config_6.tendermint_rpc_url
            },
            self.node_config_7.node_id: {
                'id': self.node_config_7.node_id,
                'parent_id': self.node_config_7.parent_id,
                'name': self.node_config_7.node_name,
                'cosmos_rest_url': self.node_config_7.cosmos_rest_url,
                'monitor_cosmos_rest': str(
                    self.node_config_7.monitor_cosmos_rest),
                'prometheus_url': self.node_config_7.prometheus_url,
                'monitor_prometheus': str(
                    self.node_config_7.monitor_prometheus),
                'is_validator': str(self.node_config_7.is_validator),
                'monitor_node': str(self.node_config_7.monitor_node),
                'is_archive_node': str(self.node_config_7.is_archive_node),
                'use_as_data_source': str(
                    self.node_config_7.use_as_data_source),
                'operator_address': self.node_config_7.operator_address,
                'monitor_tendermint_rpc': str(
                    self.node_config_7.monitor_tendermint_rpc),
                'tendermint_rpc_url': self.node_config_7.tendermint_rpc_url
            },
            self.node_config_8.node_id: {
                'id': self.node_config_8.node_id,
                'parent_id': self.node_config_8.parent_id,
                'name': self.node_config_8.node_name,
                'cosmos_rest_url': self.node_config_8.cosmos_rest_url,
                'monitor_cosmos_rest': str(
                    self.node_config_8.monitor_cosmos_rest),
                'prometheus_url': self.node_config_8.prometheus_url,
                'monitor_prometheus': str(
                    self.node_config_8.monitor_prometheus),
                'is_validator': str(self.node_config_8.is_validator),
                'monitor_node': str(self.node_config_8.monitor_node),
                'is_archive_node': str(self.node_config_8.is_archive_node),
                'use_as_data_source': str(
                    self.node_config_8.use_as_data_source),
                'operator_address': self.node_config_8.operator_address,
                'monitor_tendermint_rpc': str(
                    self.node_config_8.monitor_tendermint_rpc),
                'tendermint_rpc_url': self.node_config_8.tendermint_rpc_url
            }
        }
        self.sent_configs_example_polkadot = {
            self.node_config_9.node_id: {
                'id': self.node_config_9.node_id,
                'parent_id': self.node_config_9.parent_id,
                'name': self.node_config_9.node_name,
                'node_ws_url': self.node_config_9.node_ws_url,
                'is_validator': str(self.node_config_9.is_validator),
                'monitor_node': str(self.node_config_9.monitor_node),
                'is_archive_node': str(self.node_config_9.is_archive_node),
                'use_as_data_source': str(
                    self.node_config_9.use_as_data_source),
                'stash_address': self.node_config_9.stash_address,
            },
            self.node_config_10.node_id: {
                'id': self.node_config_10.node_id,
                'parent_id': self.node_config_10.parent_id,
                'name': self.node_config_10.node_name,
                'node_ws_url': self.node_config_10.node_ws_url,
                'is_validator': str(self.node_config_10.is_validator),
                'monitor_node': str(self.node_config_10.monitor_node),
                'is_archive_node': str(self.node_config_10.is_archive_node),
                'use_as_data_source': str(
                    self.node_config_10.use_as_data_source),
                'stash_address': self.node_config_10.stash_address,
            },
            self.node_config_11.node_id: {
                'id': self.node_config_11.node_id,
                'parent_id': self.node_config_11.parent_id,
                'name': self.node_config_11.node_name,
                'node_ws_url': self.node_config_11.node_ws_url,
                'is_validator': str(self.node_config_11.is_validator),
                'monitor_node': str(self.node_config_11.monitor_node),
                'is_archive_node': str(self.node_config_11.is_archive_node),
                'use_as_data_source': str(
                    self.node_config_11.use_as_data_source),
                'stash_address': self.node_config_11.stash_address,
            },
        }

        # Test manager object
        self.test_manager = NodeMonitorsManager(
            self.dummy_logger, self.manager_name, self.rabbitmq)

        # Some test routing keys
        self.chainlink_routing_key = \
            'chains.chainlink.Binance Smart Chain.nodes_config'
        self.chainlink_evm_routing_key = \
            'chains.chainlink.Binance Smart Chain.evm_nodes_config'
        self.test_chain_routing_key = \
            'chains.TestBaseChain.TestSubChain.nodes_config'
        self.cosmos_routing_key = 'chains.cosmos.cosmos.nodes_config'
        self.polkadot_routing_key = 'chains.substrate.polkadot.nodes_config'

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               NODE_MON_MAN_HEARTBEAT_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               NODE_MON_MAN_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq, CONFIG_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  MONITORABLE_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.dummy_process1 = None
        self.dummy_process2 = None
        self.dummy_process3 = None
        self.dummy_process4 = None
        self.dummy_process5 = None
        self.dummy_process6 = None
        self.dummy_process7 = None
        self.dummy_process8 = None
        self.dummy_process9 = None
        self.dummy_process10 = None
        self.dummy_process11 = None
        self.cl_test_nodes.clear_attributes()
        self.evm_test_nodes.clear_attributes()
        self.cosmos_test_nodes.clear_attributes()
        self.substrate_test_nodes.clear_attributes()
        self.cl_test_nodes = None
        self.evm_test_nodes = None
        self.cosmos_test_nodes = None
        self.substrate_test_nodes = None
        self.node_config_1 = None
        self.node_config_2 = None
        self.node_config_3 = None
        self.node_config_4 = None
        self.node_config_5 = None
        self.node_config_6 = None
        self.node_config_7 = None
        self.node_config_8 = None
        self.node_config_9 = None
        self.node_config_10 = None
        self.node_config_11 = None
        self.config_process_dict_example = None
        self.nodes_configs_example = None
        self.sent_configs_example_chainlink = None
        self.sent_configs_example_chainlink_evm = None
        self.sent_configs_example_test_chain = None
        self.sent_configs_example_cosmos = None
        self.sent_configs_example_polkadot = None
        self.test_manager = None
        self.test_exception = None

    def test_str_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, str(self.test_manager))

    def test_config_process_dict_returns_config_process_dict(self) -> None:
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.assertEqual(self.config_process_dict_example,
                         self.test_manager.config_process_dict)

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_nodes_configs_returns_nodes_configs(self) -> None:
        self.test_manager._nodes_configs = self.nodes_configs_example
        self.assertEqual(self.nodes_configs_example,
                         self.test_manager.nodes_configs)

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        mock_start_consuming.assert_called_once()

    @mock.patch.object(RabbitMQApi, 'basic_consume')
    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self, mock_basic_consume) -> None:
        mock_basic_consume.return_value = None

        # To make sure that there is no connection/channel already established
        self.assertIsNone(self.rabbitmq.connection)
        self.assertIsNone(self.rabbitmq.channel)

        # To make sure that the exchanges and queues have not already been
        # declared
        self.rabbitmq.connect()
        self.test_manager.rabbitmq.queue_delete(
            NODE_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.test_manager.rabbitmq.queue_delete(NODE_MON_MAN_CONFIGS_QUEUE_NAME)
        self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
        self.test_manager.rabbitmq.exchange_delete(MONITORABLE_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_manager._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_manager.rabbitmq.is_connected)
        self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_manager.rabbitmq.channel._delivery_confirmation)

        # Check whether the exchanges and queues have been creating by
        # sending messages with the same routing keys as for the queues, and
        # checking what messages have been received if any.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key=PING_ROUTING_KEY,
            body='data_1', is_body_dict=False, properties=pika.BasicProperties(
                delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=self.chainlink_routing_key, body='data_2',
            is_body_dict=False, properties=pika.BasicProperties(
                delivery_mode=2), mandatory=True)
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=self.chainlink_evm_routing_key, body='data_3',
            is_body_dict=False, properties=pika.BasicProperties(
                delivery_mode=2), mandatory=True)

        # Re-declare queues to get the number of messages and the msgs received
        res = self.test_manager.rabbitmq.queue_declare(
            NODE_MON_MAN_HEARTBEAT_QUEUE_NAME, False, True, False, False)
        self.assertEqual(1, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            NODE_MON_MAN_HEARTBEAT_QUEUE_NAME)
        self.assertEqual('data_1', body.decode())

        res = self.test_manager.rabbitmq.queue_declare(
            NODE_MON_MAN_CONFIGS_QUEUE_NAME, False, True, False, False)
        self.assertEqual(2, res.method.message_count)
        _, _, body = self.test_manager.rabbitmq.basic_get(
            NODE_MON_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual('data_2', body.decode())
        _, _, body = self.test_manager.rabbitmq.basic_get(
            NODE_MON_MAN_CONFIGS_QUEUE_NAME)
        self.assertEqual('data_3', body.decode())

        # Check that basic_consume was called twice, once for each consumer
        # queue
        calls = mock_basic_consume.call_args_list
        self.assertEqual(2, len(calls))

        # Check that the publishing exchanges were created by sending messages
        # to them. If this fails an exception is raised hence the test fails.
        self.test_manager.rabbitmq.basic_publish_confirm(
            exchange=MONITORABLE_EXCHANGE, routing_key='test_key',
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        self.test_manager._initialise_rabbitmq()

        # Delete the queue before to avoid messages in the queue on error.
        self.test_manager.rabbitmq.queue_delete(self.test_queue_name)

        res = self.test_manager.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)
        self.test_manager.rabbitmq.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY)
        self.test_manager._send_heartbeat(self.test_heartbeat)

        # By re-declaring the queue again we can get the number of messages
        # in the queue.
        res = self.test_manager.rabbitmq.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        # Check that the message received is actually the HB
        _, _, body = self.test_manager.rabbitmq.basic_get(self.test_queue_name)
        self.assertEqual(self.test_heartbeat, json.loads(body))

    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing, 'Process')
    def test_create_and_start_monitor_process_stores_the_correct_process_info(
            self, mock_init, mock_start) -> None:
        mock_start.return_value = None
        mock_init.return_value = self.dummy_process1
        expected_output = {
            self.node_config_1.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_1.node_name),
                'process': self.dummy_process1,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_1,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_1.node_name,
                'parent_id': self.node_config_1.parent_id,
                'args': ('extra_arg1', 'extra_arg2')
            },
        }

        self.test_manager._create_and_start_monitor_process(
            self.node_config_1, self.node_config_1.node_id,
            ChainlinkNodeMonitor, '', '', 'extra_arg1', 'extra_arg2')
        self.assertEqual(expected_output, self.test_manager.config_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_monitor_process_creates_and_starts_correct_proc(
            self, mock_start) -> None:
        mock_start.return_value = None

        self.test_manager._create_and_start_monitor_process(
            self.node_config_1, self.node_config_1.node_id,
            ChainlinkNodeMonitor, '', '', 'extra_arg1', 'extra_arg2')
        new_entry = self.test_manager.config_process_dict[
            self.node_config_1.node_id]
        new_entry_process = new_entry['process']
        self.assertTrue(new_entry_process.daemon)
        self.assertEqual(4, len(new_entry_process._args))
        self.assertEqual(self.node_config_1, new_entry_process._args[0])
        self.assertEqual(ChainlinkNodeMonitor, new_entry_process._args[1])
        self.assertEqual('extra_arg1', new_entry_process._args[2])
        self.assertEqual('extra_arg2', new_entry_process._args[3])
        self.assertEqual(start_node_monitor, new_entry_process._target)
        mock_start.assert_called_once()

    @parameterized.expand([
        ("self.node_config_6", "self.sent_configs_example_cosmos",
         ["self.node_config_7", "self.node_config_6"]),
        ("self.node_config_7", "self.sent_configs_example_cosmos",
         ["self.node_config_6", "self.node_config_7"]),
        ("self.node_config_8", "self.sent_configs_example_cosmos",
         ["self.node_config_7", "self.node_config_6", "self.node_config_8"]),
        ("self.node_config_8", "self.empty_configs", ["self.node_config_8"]),
    ])
    def test_determine_data_sources_for_cosmos_monitor_returns_correctly(
            self, node_config, sent_configs, expected_return_vars) -> None:
        # eval creates a new scope, therefore we need to pass the scope from the
        # outside
        scope = locals()
        expected_return = [
            eval(variable, scope) for variable in expected_return_vars
        ]
        actual_return = \
            self.test_manager._determine_data_sources_for_cosmos_monitor(
                eval(node_config), eval(sent_configs))
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ("self.node_config_9", "self.sent_configs_example_polkadot",
         ["self.node_config_10", "self.node_config_9"]),
        ("self.node_config_10", "self.sent_configs_example_polkadot",
         ["self.node_config_9", "self.node_config_10"]),
        ("self.node_config_11", "self.sent_configs_example_polkadot",
         ["self.node_config_10", "self.node_config_9", "self.node_config_11"]),
        ("self.node_config_11", "self.empty_configs", ["self.node_config_11"]),
    ])
    def test_determine_data_sources_for_substrate_monitor_returns_correctly(
            self, node_config, sent_configs, expected_return_vars) -> None:
        # eval creates a new scope, therefore we need to pass the scope from the
        # outside
        scope = locals()
        expected_return = [
            eval(variable, scope) for variable in expected_return_vars
        ]
        actual_return = \
            self.test_manager._determine_data_sources_for_substrate_monitor(
                eval(node_config), eval(sent_configs))
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ("True", "False", "False", "False"),
        ("False", "True", "False", "False"),
        ("False", "False", "True", "False"),
        ("False", "False", "False", "True"),
        ("False", "True", "True", "True"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_cosmos_node_configs_starts_monitors_for_new_configs(
            self, monitor_node, monitor_prometheus, monitor_tendermint,
            monitor_rest, startup_mock, mock_process_send_mon_data) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if
        # `monitor_node and monitor_<any_source> = True`. We will be also
        # testing that if `monitor_node or monitor_<all_sources> = False` no new
        # monitor is created. We will perform this test for both when the state
        # is empty and non-empty
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_cosmos)
        sent_configs[self.node_config_8.node_id]['monitor_node'] = monitor_node
        sent_configs[self.node_config_8.node_id][
            'monitor_prometheus'] = monitor_prometheus
        sent_configs[self.node_config_8.node_id][
            'monitor_cosmos_rest'] = monitor_rest
        sent_configs[self.node_config_8.node_id][
            'monitor_tendermint_rpc'] = monitor_tendermint
        self.test_manager._process_cosmos_node_configs(sent_configs, {}, '', '')
        expected_calls = [
            call(self.node_config_6, self.node_config_6.node_id,
                 CosmosNodeMonitor, '', '', [self.node_config_7,
                                             self.node_config_6]),
            call(self.node_config_7, self.node_config_7.node_id,
                 CosmosNodeMonitor, '', '', [self.node_config_6,
                                             self.node_config_7]),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(2, startup_mock.call_count)

        # Test when current_configs is non-empty
        startup_mock.reset_mock()
        current_configs = copy.deepcopy(self.sent_configs_example_cosmos)
        del current_configs[self.node_config_7.node_id]
        del current_configs[self.node_config_8.node_id]
        self.test_manager._process_cosmos_node_configs(sent_configs,
                                                       current_configs, '', '')
        expected_calls = [
            call(self.node_config_7, self.node_config_7.node_id,
                 CosmosNodeMonitor, '', '', [self.node_config_6,
                                             self.node_config_7]),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(1, startup_mock.call_count)

    @parameterized.expand([
        ("True", "False", "False", "False"),
        ("False", "True", "False", "False"),
        ("False", "False", "True", "False"),
        ("False", "False", "False", "True"),
        ("False", "True", "True", "True"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_cosmos_node_configs_return_if_valid_new_configurations(
            self, monitor_node, monitor_prometheus, monitor_tendermint,
            monitor_rest, startup_mock, mock_process_send_mon_data) -> None:
        # In this test we will assume that all added configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        # We will perform this test for both when the state is empty and
        # non-empty.
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_cosmos)
        sent_configs[self.node_config_8.node_id]['monitor_node'] = monitor_node
        sent_configs[self.node_config_8.node_id][
            'monitor_prometheus'] = monitor_prometheus
        sent_configs[self.node_config_8.node_id][
            'monitor_cosmos_rest'] = monitor_rest
        sent_configs[self.node_config_8.node_id][
            'monitor_tendermint_rpc'] = monitor_tendermint
        actual_return = self.test_manager._process_cosmos_node_configs(
            sent_configs, {}, '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_8.node_id]
        self.assertEqual(expected_return, actual_return)

        # Test when current_configs is non-empty
        current_configs = copy.deepcopy(self.sent_configs_example_cosmos)
        del current_configs[self.node_config_7.node_id]
        del current_configs[self.node_config_8.node_id]
        actual_return = self.test_manager._process_cosmos_node_configs(
            sent_configs, current_configs, '', '')
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ("True", "False", "False", "False"),
        ("False", "True", "False", "False"),
        ("False", "False", "True", "False"),
        ("False", "False", "False", "True"),
        ("False", "True", "True", "True"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing, 'Process')
    def test_process_cosmos_node_configs_restarts_monitors_for_edited_confs(
            self, monitor_node, monitor_prometheus, monitor_tendermint,
            monitor_rest, mock_init, mock_terminate, mock_join,
            mock_start, mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed and started with the latest configuration as long
        # as `monitor_node and monitor_<any_source>=True`.
        mock_start.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_process_send_mon_data.return_value = None
        mock_init.side_effect = [self.dummy_process7, self.dummy_process8]
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_cosmos)

        # Assume that config_6, will be the configuration whose monitors will
        # be killed but not started.
        sent_configs[self.node_config_6.node_id]['monitor_node'] = monitor_node
        sent_configs[self.node_config_6.node_id][
            'monitor_prometheus'] = monitor_prometheus
        sent_configs[self.node_config_6.node_id][
            'monitor_cosmos_rest'] = monitor_rest
        sent_configs[self.node_config_6.node_id][
            'monitor_tendermint_rpc'] = monitor_tendermint

        # Assume that for config_7 the name of the node was changed. Node 8
        # will be restarted because there was a change in data sources.
        sent_configs[self.node_config_7.node_id]['name'] = 'changed_node_name'

        self.test_manager._process_cosmos_node_configs(
            sent_configs,
            self.nodes_configs_example['cosmos cosmos']['nodes_config'], '', '')

        # Called once for terminating node 6 and twice for restarting nodes 7
        # and 8 with the latest configuration
        self.assertEqual(3, mock_terminate.call_count)
        self.assertEqual(3, mock_join.call_count)
        self.assertTrue(
            self.node_config_8.node_id in self.test_manager.config_process_dict)
        self.assertTrue(
            self.node_config_7.node_id in self.test_manager.config_process_dict)
        self.assertFalse(
            self.node_config_6.node_id in self.test_manager.config_process_dict)

        # Check that monitors for node 7 and 8 were restarted
        modified_node_7_config = self.cosmos_test_nodes.create_custom_node(
            'node_id_7', 'parent_id_7', 'changed_node_name', True, True,
            'prom_url_7', True, 'cosmos_rest_url_7', True,
            'tendermint_rpc_url_7', False, False, True, 'operator_address_7'
        )
        expected_node_6_config = self.cosmos_test_nodes.create_custom_node(
            'node_id_6', 'parent_id_6', 'node_name_6',
            str_to_bool(monitor_node), str_to_bool(monitor_prometheus),
            'prom_url_6', str_to_bool(monitor_rest), 'cosmos_rest_url_6',
            str_to_bool(monitor_tendermint), 'tendermint_rpc_url_6', True, True,
            True, 'operator_address_6'
        )

        expected_config_process_dict = {
            self.node_config_1.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_1.node_name),
                'process': self.dummy_process1,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_1,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_1.node_name,
                'parent_id': self.node_config_1.parent_id,
                'args': ()
            },
            self.node_config_2.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_2.node_name),
                'process': self.dummy_process2,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_2,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_2.node_name,
                'parent_id': self.node_config_2.parent_id,
                'args': ()
            },
            self.node_config_3.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_3.node_name),
                'process': self.dummy_process3,
                'monitor_type': Monitor,
                'node_config': self.node_config_3,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_3.node_name,
                'parent_id': self.node_config_3.parent_id,
                'args': ()
            },
            self.node_config_4.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_4.node_name),
                'process': self.dummy_process4,
                'monitor_type': EVMNodeMonitor,
                'node_config': self.node_config_4,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_4.node_name,
                'parent_id': self.node_config_4.parent_id,
                'args': ()
            },
            self.node_config_5.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_5.node_name),
                'process': self.dummy_process5,
                'monitor_type': EVMNodeMonitor,
                'node_config': self.node_config_5,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_5.node_name,
                'parent_id': self.node_config_5.parent_id,
                'args': ()
            },
            modified_node_7_config.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    modified_node_7_config.node_name),
                'process': self.dummy_process7,
                'monitor_type': CosmosNodeMonitor,
                'node_config': modified_node_7_config,
                'base_chain': '',
                'sub_chain': '',
                'source_name': 'changed_node_name',
                'parent_id': self.node_config_7.parent_id,
                'args': ([expected_node_6_config, modified_node_7_config],)
            },
            self.node_config_8.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_8.node_name),
                'process': self.dummy_process8,
                'monitor_type': CosmosNodeMonitor,
                'node_config': self.node_config_8,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_8.node_name,
                'parent_id': self.node_config_8.parent_id,
                'args': ([modified_node_7_config, expected_node_6_config,
                          self.node_config_8],)
            },
            self.node_config_9.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_9.node_name),
                'process': self.dummy_process9,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': self.node_config_9,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_9.node_name,
                'parent_id': self.node_config_9.parent_id,
                'args': ([self.node_config_10, self.node_config_9],)
            },
            self.node_config_10.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_10.node_name),
                'process': self.dummy_process10,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': self.node_config_10,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_10.node_name,
                'parent_id': self.node_config_10.parent_id,
                'args': ([self.node_config_9, self.node_config_10],)
            },
            self.node_config_11.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_11.node_name),
                'process': self.dummy_process11,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': self.node_config_11,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_11.node_name,
                'parent_id': self.node_config_11.parent_id,
                'args': ([self.node_config_10, self.node_config_9,
                          self.node_config_11],)
            },
        }
        self.assertEqual(expected_config_process_dict,
                         self.test_manager.config_process_dict)

    @parameterized.expand([
        ("True", "False", "False", "False"),
        ("False", "True", "False", "False"),
        ("False", "False", "True", "False"),
        ("False", "False", "False", "True"),
        ("False", "True", "True", "True"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_cosmos_node_configs_return_if_valid_edited_confs(
            self, monitor_node, monitor_prometheus, monitor_tendermint,
            monitor_rest, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # In this test we will assume that all edited configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_cosmos)

        # Assume that config_6, will be the configuration whose monitors will
        # be killed but not started.
        sent_configs[self.node_config_6.node_id]['monitor_node'] = monitor_node
        sent_configs[self.node_config_6.node_id][
            'monitor_prometheus'] = monitor_prometheus
        sent_configs[self.node_config_6.node_id][
            'monitor_cosmos_rest'] = monitor_rest
        sent_configs[self.node_config_6.node_id][
            'monitor_tendermint_rpc'] = monitor_tendermint

        # Assume that for config_7 the name of the node was changed. Node 8
        # will be restarted because there was a change in data sources.
        sent_configs[self.node_config_7.node_id]['name'] = 'changed_node_name'

        actual_return = self.test_manager._process_cosmos_node_configs(
            sent_configs,
            self.nodes_configs_example['cosmos cosmos']['nodes_config'], '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_6.node_id]
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_cosmos_node_configs_deletes_monitors_for_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed. Note that we also need to check that if the
        # deleted node was a data source, the monitors using that data source
        # are also restarted
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_cosmos)
        del sent_configs[self.node_config_6.node_id]

        self.test_manager._process_cosmos_node_configs(
            sent_configs,
            self.nodes_configs_example['cosmos cosmos']['nodes_config'], '', '')

        # Terminate and join were called once when deleting node 6 and twice for
        # restarting the monitors of node 7 and 8
        self.assertEqual(3, mock_terminate.call_count)
        self.assertEqual(3, mock_join.call_count)
        self.assertTrue(
            self.node_config_8.node_id in self.test_manager.config_process_dict)
        self.assertTrue(
            self.node_config_7.node_id in self.test_manager.config_process_dict)
        self.assertFalse(
            self.node_config_6.node_id in self.test_manager.config_process_dict)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_cosmos_node_configs_return_if_valid_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # In this test we will assume that all sent configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_cosmos)
        del sent_configs[self.node_config_6.node_id]

        actual_return = self.test_manager._process_cosmos_node_configs(
            sent_configs,
            self.nodes_configs_example['cosmos cosmos']['nodes_config'], '', '')
        self.assertEqual(sent_configs, actual_return)

    @mock.patch.object(NodeMonitorsManager, "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_substrate_node_configs_starts_monitors_for_new_configs(
            self, startup_mock, mock_process_send_mon_data) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if `monitor_node = True`.
        # We will be also testing that if `monitor_node = False` no new monitor
        # is created. We will perform this test for both when the state is empty
        # and non-empty
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_polkadot)
        sent_configs[self.node_config_11.node_id]['monitor_node'] = 'False'
        self.test_manager._process_substrate_node_configs(
            sent_configs, {}, '', '')
        expected_calls = [
            call(self.node_config_9, self.node_config_9.node_id,
                 SubstrateNodeMonitor, '', '', [self.node_config_10,
                                                self.node_config_9]),
            call(self.node_config_10, self.node_config_10.node_id,
                 SubstrateNodeMonitor, '', '', [self.node_config_9,
                                                self.node_config_10]),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(2, startup_mock.call_count)

        # Test when current_configs is non-empty
        startup_mock.reset_mock()
        current_configs = copy.deepcopy(self.sent_configs_example_polkadot)
        del current_configs[self.node_config_10.node_id]
        del current_configs[self.node_config_11.node_id]
        self.test_manager._process_substrate_node_configs(
            sent_configs, current_configs, '', '')
        expected_calls = [
            call(self.node_config_10, self.node_config_10.node_id,
                 SubstrateNodeMonitor, '', '', [self.node_config_9,
                                                self.node_config_10]),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(1, startup_mock.call_count)

    @mock.patch.object(NodeMonitorsManager, "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_substrate_node_configs_return_if_valid_new_configurations(
            self, startup_mock, mock_process_send_mon_data) -> None:
        # In this test we will assume that all added configurations are valid.
        # Thus, we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        # We will perform this test for both when the state is empty and
        # non-empty.
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_polkadot)
        sent_configs[self.node_config_11.node_id]['monitor_node'] = 'False'
        actual_return = self.test_manager._process_substrate_node_configs(
            sent_configs, {}, '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_11.node_id]
        self.assertEqual(expected_return, actual_return)

        # Test when current_configs is non-empty
        current_configs = copy.deepcopy(self.sent_configs_example_polkadot)
        del current_configs[self.node_config_10.node_id]
        del current_configs[self.node_config_11.node_id]
        actual_return = self.test_manager._process_substrate_node_configs(
            sent_configs, current_configs, '', '')
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(NodeMonitorsManager, "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "start")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing, 'Process')
    def test_process_substrate_node_configs_restarts_monitors_for_edited_confs(
            self, mock_init, mock_terminate, mock_join, mock_start,
            mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed and started with the latest configuration as long
        # as `monitor_node=True`.
        mock_start.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_process_send_mon_data.return_value = None
        mock_init.side_effect = [self.dummy_process10, self.dummy_process11]
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_polkadot)

        # Assume that config_9, will be the configuration whose monitors will
        # be killed but not started.
        sent_configs[self.node_config_9.node_id]['monitor_node'] = 'False'

        # Assume that for config_10 the name of the node was changed. Node 11
        # will be restarted because there was a change in data sources.
        sent_configs[self.node_config_10.node_id]['name'] = 'changed_node_name'

        self.test_manager._process_substrate_node_configs(
            sent_configs,
            self.nodes_configs_example['substrate polkadot']['nodes_config'],
            '', '')

        # Called once for terminating node 9 and twice for restarting nodes 10
        # and 11 with the latest configuration
        self.assertEqual(3, mock_terminate.call_count)
        self.assertEqual(3, mock_join.call_count)
        self.assertTrue(self.node_config_11.node_id in
                        self.test_manager.config_process_dict)
        self.assertTrue(self.node_config_10.node_id in
                        self.test_manager.config_process_dict)
        self.assertFalse(self.node_config_9.node_id in
                         self.test_manager.config_process_dict)

        # Check that monitors for node 10 and 11 were restarted
        modified_node_10_config = self.substrate_test_nodes.create_custom_node(
            'node_id_10', 'parent_id_10', 'changed_node_name', True,
            'node_ws_url_10', True, False, False, 'stash_address_10'
        )
        expected_node_9_config = self.substrate_test_nodes.create_custom_node(
            'node_id_9', 'parent_id_9', 'node_name_9', False, 'node_ws_url_9',
            True, True, True, 'stash_address_9'
        )

        expected_config_process_dict = {
            self.node_config_1.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_1.node_name),
                'process': self.dummy_process1,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_1,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_1.node_name,
                'parent_id': self.node_config_1.parent_id,
                'args': ()
            },
            self.node_config_2.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_2.node_name),
                'process': self.dummy_process2,
                'monitor_type': ChainlinkNodeMonitor,
                'node_config': self.node_config_2,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_2.node_name,
                'parent_id': self.node_config_2.parent_id,
                'args': ()
            },
            self.node_config_3.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_3.node_name),
                'process': self.dummy_process3,
                'monitor_type': Monitor,
                'node_config': self.node_config_3,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_3.node_name,
                'parent_id': self.node_config_3.parent_id,
                'args': ()
            },
            self.node_config_4.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_4.node_name),
                'process': self.dummy_process4,
                'monitor_type': EVMNodeMonitor,
                'node_config': self.node_config_4,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_4.node_name,
                'parent_id': self.node_config_4.parent_id,
                'args': ()
            },
            self.node_config_5.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_5.node_name),
                'process': self.dummy_process5,
                'monitor_type': EVMNodeMonitor,
                'node_config': self.node_config_5,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_5.node_name,
                'parent_id': self.node_config_5.parent_id,
                'args': ()
            },
            self.node_config_6.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_6.node_name),
                'process': self.dummy_process6,
                'monitor_type': CosmosNodeMonitor,
                'node_config': self.node_config_6,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_6.node_name,
                'parent_id': self.node_config_6.parent_id,
                'args': ([self.node_config_7, self.node_config_6],)
            },
            self.node_config_7.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_7.node_name),
                'process': self.dummy_process7,
                'monitor_type': CosmosNodeMonitor,
                'node_config': self.node_config_7,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_7.node_name,
                'parent_id': self.node_config_7.parent_id,
                'args': ([self.node_config_6, self.node_config_7],)
            },
            self.node_config_8.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_8.node_name),
                'process': self.dummy_process8,
                'monitor_type': CosmosNodeMonitor,
                'node_config': self.node_config_8,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_8.node_name,
                'parent_id': self.node_config_8.parent_id,
                'args': ([self.node_config_7, self.node_config_6,
                          self.node_config_8],)
            },
            modified_node_10_config.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    modified_node_10_config),
                'process': self.dummy_process10,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': modified_node_10_config,
                'base_chain': '',
                'sub_chain': '',
                'source_name': modified_node_10_config.node_name,
                'parent_id': modified_node_10_config.parent_id,
                'args': ([expected_node_9_config, modified_node_10_config],)
            },
            self.node_config_11.node_id: {
                'component_name': NODE_MONITOR_NAME_TEMPLATE.format(
                    self.node_config_11.node_name),
                'process': self.dummy_process11,
                'monitor_type': SubstrateNodeMonitor,
                'node_config': self.node_config_11,
                'base_chain': '',
                'sub_chain': '',
                'source_name': self.node_config_11.node_name,
                'parent_id': self.node_config_11.parent_id,
                'args': ([modified_node_10_config, expected_node_9_config,
                          self.node_config_11],)
            },
        }
        self.assertEqual(expected_config_process_dict,
                         self.test_manager.config_process_dict)

    @mock.patch.object(NodeMonitorsManager, "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_substrate_node_configs_return_if_valid_edited_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # In this test we will assume that all edited configurations are valid.
        # Thus, we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_polkadot)

        # Assume that config_9, will be the configuration whose monitors will
        # be killed but not started.
        sent_configs[self.node_config_9.node_id]['monitor_node'] = 'False'

        # Assume that for config_10 the name of the node was changed. Node 11
        # will be restarted because there was a change in data sources.
        sent_configs[self.node_config_10.node_id]['name'] = 'changed_node_name'

        actual_return = self.test_manager._process_substrate_node_configs(
            sent_configs,
            self.nodes_configs_example['substrate polkadot']['nodes_config'],
            '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_9.node_id]
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(NodeMonitorsManager, "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_substrate_node_configs_deletes_monitors_for_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed. Note that we also need to check that if the
        # deleted node was a data source, the monitors using that data source
        # are also restarted
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_polkadot)
        del sent_configs[self.node_config_9.node_id]

        self.test_manager._process_substrate_node_configs(
            sent_configs,
            self.nodes_configs_example['substrate polkadot']['nodes_config'],
            '', '')

        # Terminate and join were called once when deleting node 9 and twice for
        # restarting the monitors of node 10 and 11
        self.assertEqual(3, mock_terminate.call_count)
        self.assertEqual(3, mock_join.call_count)
        self.assertTrue(self.node_config_11.node_id in
                        self.test_manager.config_process_dict)
        self.assertTrue(self.node_config_10.node_id in
                        self.test_manager.config_process_dict)
        self.assertFalse(
            self.node_config_9.node_id in self.test_manager.config_process_dict)

    @mock.patch.object(NodeMonitorsManager, "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_substrate_node_configs_return_if_valid_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # In this test we will assume that all sent configurations are valid.
        # Thus, we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_polkadot)
        del sent_configs[self.node_config_9.node_id]

        actual_return = self.test_manager._process_substrate_node_configs(
            sent_configs,
            self.nodes_configs_example['substrate polkadot']['nodes_config'],
            '', '')
        self.assertEqual(sent_configs, actual_return)

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_starts_monitors_for_new_configs(
            self, third_conf_monitor_node, third_conf_monitor_prometheus,
            startup_mock, mock_process_send_mon_data) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if
        # `monitor_node and monitor_<any_source> = True`.
        # We will be also testing that if
        # `monitor_node or monitor_<all_sources> = False` no new monitor
        # is created. We will perform this test for both when the state is empty
        # and non-empty
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        sent_configs[self.node_config_3.node_id] = {
            'id': self.node_config_3.node_id,
            'parent_id': self.node_config_3.parent_id,
            'name': self.node_config_3.node_name,
            'node_prometheus_urls': 'url7,url8,url9',
            'monitor_node': third_conf_monitor_node,
            'monitor_prometheus': third_conf_monitor_prometheus
        }
        self.test_manager._process_chainlink_node_configs(
            sent_configs, {}, '', '')
        expected_calls = [
            call(self.node_config_1, self.node_config_1.node_id,
                 ChainlinkNodeMonitor, '', ''),
            call(self.node_config_2, self.node_config_2.node_id,
                 ChainlinkNodeMonitor, '', ''),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(2, startup_mock.call_count)

        # Test when current_configs is non-empty
        startup_mock.reset_mock()
        current_configs = {
            self.node_config_1.node_id: {
                'id': self.node_config_1.node_id,
                'parent_id': self.node_config_1.parent_id,
                'name': self.node_config_1.node_name,
                'node_prometheus_urls':
                    ','.join(self.node_config_1.node_prometheus_urls),
                'monitor_node': str(self.node_config_1.monitor_node),
                'monitor_prometheus': str(self.node_config_1.monitor_prometheus)
            }
        }
        self.test_manager._process_chainlink_node_configs(sent_configs,
                                                          current_configs,
                                                          '', '')
        expected_calls = [
            call(self.node_config_2, self.node_config_2.node_id,
                 ChainlinkNodeMonitor, '', ''),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(1, startup_mock.call_count)

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_return_if_valid_new_configurations(
            self, third_conf_monitor_node, third_conf_monitor_prometheus,
            startup_mock, mock_process_send_mon_data) -> None:
        # In this test we will assume that all added configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        # We will perform this test for both when the state is empty and
        # non-empty.
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        sent_configs[self.node_config_3.node_id] = {
            'id': self.node_config_3.node_id,
            'parent_id': self.node_config_3.parent_id,
            'name': self.node_config_3.node_name,
            'node_prometheus_urls': 'url7,url8,url9',
            'monitor_node': third_conf_monitor_node,
            'monitor_prometheus': third_conf_monitor_prometheus
        }
        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs, {}, '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_3.node_id]
        self.assertEqual(expected_return, actual_return)

        # Test when current_configs is non-empty
        current_configs = {
            self.node_config_1.node_id: {
                'id': self.node_config_1.node_id,
                'parent_id': self.node_config_1.parent_id,
                'name': self.node_config_1.node_name,
                'node_prometheus_urls':
                    ','.join(self.node_config_1.node_prometheus_urls),
                'monitor_node': str(self.node_config_1.monitor_node),
                'monitor_prometheus': str(self.node_config_1.monitor_prometheus)
            }
        }
        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs, current_configs, '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_3.node_id]
        self.assertEqual(expected_return, actual_return)

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_restarts_monitors_for_edited_confs(
            self, deleted_conf_monitor_node, deleted_conf_monitor_prometheus,
            startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed and started with the latest configuration as long
        # as `monitor_node and monitor_<any_source>=True`.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)

        # Assume that config_1, will be the configuration whose monitors will
        # be killed but not started.
        sent_configs[self.node_config_1.node_id] = {
            'id': self.node_config_1.node_id,
            'parent_id': self.node_config_1.parent_id,
            'name': self.node_config_1.node_name,
            'node_prometheus_urls':
                ','.join(self.node_config_1.node_prometheus_urls),
            'monitor_node': deleted_conf_monitor_node,
            'monitor_prometheus': deleted_conf_monitor_prometheus
        }
        # Assume that for config_2 the name of the node was changed
        sent_configs[self.node_config_2.node_id] = {
            'id': self.node_config_2.node_id,
            'parent_id': self.node_config_2.parent_id,
            'name': 'changed_node_name',
            'node_prometheus_urls':
                ','.join(self.node_config_2.node_prometheus_urls),
            'monitor_node': str(self.node_config_2.monitor_node),
            'monitor_prometheus': str(self.node_config_2.monitor_prometheus)
        }

        self.test_manager._process_chainlink_node_configs(
            sent_configs, self.nodes_configs_example[
                'chainlink Binance Smart Chain']['nodes_config'],
            '', '')
        modified_node_2_config = ChainlinkNodeConfig(
            self.node_config_2.node_id, self.node_config_2.parent_id,
            'changed_node_name', self.node_config_2.monitor_node,
            self.node_config_2.monitor_prometheus,
            self.node_config_2.node_prometheus_urls)
        startup_mock.assert_called_once_with(modified_node_2_config,
                                             self.node_config_2.node_id,
                                             ChainlinkNodeMonitor,
                                             '',
                                             '')
        self.assertEqual(2, mock_terminate.call_count)
        self.assertEqual(2, mock_join.call_count)
        self.assertTrue(
            self.node_config_2.node_id in self.test_manager.config_process_dict)
        self.assertFalse(
            self.node_config_1.node_id in self.test_manager.config_process_dict)

    @parameterized.expand([
        ("True", "False"),
        ("False", "True"),
        ("False", "False"),
    ])
    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_return_if_valid_edited_confs(
            self, deleted_conf_monitor_node, deleted_conf_monitor_prometheus,
            startup_mock, mock_terminate, mock_join, mock_process_send_mon_data
    ) -> None:
        # In this test we will assume that all edited configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)

        # Assume config_1 will be the config whose monitor will be killed and
        # not restarted.
        sent_configs[self.node_config_1.node_id] = {
            'id': self.node_config_1.node_id,
            'parent_id': self.node_config_1.parent_id,
            'name': self.node_config_1.node_name,
            'node_prometheus_urls':
                ','.join(self.node_config_1.node_prometheus_urls),
            'monitor_node': deleted_conf_monitor_node,
            'monitor_prometheus': deleted_conf_monitor_prometheus
        }
        # Assume that for config_2 the name of the node was changed
        sent_configs[self.node_config_2.node_id] = {
            'id': self.node_config_2.node_id,
            'parent_id': self.node_config_2.parent_id,
            'name': 'changed_node_name',
            'node_prometheus_urls':
                ','.join(self.node_config_2.node_prometheus_urls),
            'monitor_node': str(self.node_config_2.monitor_node),
            'monitor_prometheus': str(self.node_config_2.monitor_prometheus)
        }

        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['chainlink Binance Smart Chain'][
                'nodes_config'], '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_1.node_id]
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_deletes_monitors_for_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        del sent_configs[self.node_config_1.node_id]

        self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['chainlink Binance Smart Chain'][
                'nodes_config'], '', '')
        startup_mock.assert_not_called()
        self.assertEqual(1, mock_terminate.call_count)
        self.assertEqual(1, mock_join.call_count)
        self.assertTrue(
            self.node_config_2.node_id in self.test_manager.config_process_dict)
        self.assertFalse(
            self.node_config_1.node_id in self.test_manager.config_process_dict)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_chainlink_node_configs_return_if_valid_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # In this test we will assume that all sent configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        del sent_configs[self.node_config_1.node_id]

        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['chainlink Binance Smart Chain'][
                'nodes_config'], '', '')
        self.assertEqual(sent_configs, actual_return)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_evm_node_configs_starts_monitors_for_new_configs(
            self, startup_mock, mock_process_send_mon_data) -> None:
        # We will check whether _create_and_start_monitor_process is called
        # correctly on each newly added configuration if `monitor_node = True`.
        # We will be also testing that if `monitor_node = False` no new monitor
        # is created. We will perform this test for both when the state is empty
        # and non-empty
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink_evm)
        sent_configs[self.node_config_3.node_id] = {
            'id': self.node_config_3.node_id,
            'parent_id': self.node_config_3.parent_id,
            'name': self.node_config_3.node_name,
            'node_http_url': 'url3',
            'monitor_node': "False",
        }
        self.test_manager._process_evm_node_configs(sent_configs, {},
                                                    '',
                                                    '')
        expected_calls = [
            call(self.node_config_4, self.node_config_4.node_id,
                 EVMNodeMonitor, '', ''),
            call(self.node_config_5, self.node_config_5.node_id,
                 EVMNodeMonitor, '', ''),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(2, startup_mock.call_count)

        # Test when current_configs is non-empty
        startup_mock.reset_mock()
        current_configs = {
            self.node_config_4.node_id: {
                'id': self.node_config_4.node_id,
                'parent_id': self.node_config_4.parent_id,
                'name': self.node_config_4.node_name,
                'node_http_url': self.node_config_4.node_http_url,
                'monitor_node': str(self.node_config_4.monitor_node),
            }
        }
        self.test_manager._process_evm_node_configs(sent_configs,
                                                    current_configs,
                                                    '',
                                                    '')
        expected_calls = [
            call(self.node_config_5, self.node_config_5.node_id,
                 EVMNodeMonitor, '', ''),
        ]
        startup_mock.assert_has_calls(expected_calls, True)
        self.assertEqual(1, startup_mock.call_count)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_evm_node_configs_return_if_valid_new_configurations(
            self, startup_mock, mock_process_send_mon_data) -> None:
        # In this test we will assume that all added configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        # We will perform this test for both when the state is empty and
        # non-empty.
        startup_mock.return_value = None
        mock_process_send_mon_data.return_value = None

        # First test for when current_configs is empty
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink_evm)
        sent_configs[self.node_config_3.node_id] = {
            'id': self.node_config_3.node_id,
            'parent_id': self.node_config_3.parent_id,
            'name': self.node_config_3.node_name,
            'node_http_url': 'url3',
            'monitor_node': 'False',
        }
        actual_return = self.test_manager._process_evm_node_configs(
            sent_configs, {}, '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_3.node_id]
        self.assertEqual(expected_return, actual_return)

        # Test when current_configs is non-empty
        current_configs = {
            self.node_config_4.node_id: {
                'id': self.node_config_4.node_id,
                'parent_id': self.node_config_4.parent_id,
                'name': self.node_config_4.node_name,
                'node_http_url': self.node_config_4.node_http_url,
                'monitor_node': str(self.node_config_4.monitor_node),
            }
        }
        actual_return = self.test_manager._process_evm_node_configs(
            sent_configs, current_configs, '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_3.node_id]
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_evm_node_configs_restarts_monitors_for_edited_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed and started with the latest configuration as long
        # as `monitor_node=True`.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink_evm)

        # Assume that config_4, will be the configuration whose monitors will
        # be killed but not started.
        sent_configs[self.node_config_4.node_id] = {
            'id': self.node_config_4.node_id,
            'parent_id': self.node_config_4.parent_id,
            'name': self.node_config_4.node_name,
            'node_http_url': self.node_config_4.node_http_url,
            'monitor_node': 'False'
        }
        # Assume that for config_5 the name of the node was changed
        sent_configs[self.node_config_5.node_id] = {
            'id': self.node_config_5.node_id,
            'parent_id': self.node_config_5.parent_id,
            'name': 'changed_node_name',
            'node_http_url': self.node_config_5.node_http_url,
            'monitor_node': str(self.node_config_5.monitor_node),
        }

        self.test_manager._process_evm_node_configs(
            sent_configs,
            self.nodes_configs_example['chainlink Binance Smart Chain'][
                'evm_nodes_config'], '', '')
        modified_node_5_config = EVMNodeConfig(
            self.node_config_5.node_id, self.node_config_5.parent_id,
            'changed_node_name', self.node_config_5.monitor_node,
            self.node_config_5.node_http_url)
        startup_mock.assert_called_once_with(
            modified_node_5_config, self.node_config_5.node_id, EVMNodeMonitor,
            '', '')
        self.assertEqual(2, mock_terminate.call_count)
        self.assertEqual(2, mock_join.call_count)
        self.assertTrue(
            self.node_config_5.node_id in self.test_manager.config_process_dict)
        self.assertFalse(
            self.node_config_4.node_id in self.test_manager.config_process_dict)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_evm_node_configs_return_if_valid_edited_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # In this test we will assume that all edited configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example

        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink_evm)

        # Assume config_4 will be the config whose monitor will be killed and
        # not restarted.
        sent_configs[self.node_config_4.node_id] = {
            'id': self.node_config_4.node_id,
            'parent_id': self.node_config_4.parent_id,
            'name': self.node_config_4.node_name,
            'node_http_url': self.node_config_4.node_http_url,
            'monitor_node': 'False',
        }
        # Assume that for config_5 the name of the node was changed
        sent_configs[self.node_config_5.node_id] = {
            'id': self.node_config_5.node_id,
            'parent_id': self.node_config_5.parent_id,
            'name': 'changed_node_name',
            'node_http_url': self.node_config_5.node_http_url,
            'monitor_node': str(self.node_config_5.monitor_node),
        }

        actual_return = self.test_manager._process_evm_node_configs(
            sent_configs,
            self.nodes_configs_example['chainlink Binance Smart Chain'][
                'evm_nodes_config'], '', '')
        expected_return = copy.deepcopy(sent_configs)
        del expected_return[self.node_config_4.node_id]
        self.assertEqual(expected_return, actual_return)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_evm_node_configs_deletes_monitors_for_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # We will check that the running monitors associated with the modified
        # configs are killed.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink_evm)
        del sent_configs[self.node_config_4.node_id]

        self.test_manager._process_evm_node_configs(
            sent_configs,
            self.nodes_configs_example['chainlink Binance Smart Chain'][
                'evm_nodes_config'], '', '')
        startup_mock.assert_not_called()
        self.assertEqual(1, mock_terminate.call_count)
        self.assertEqual(1, mock_join.call_count)
        self.assertTrue(
            self.node_config_5.node_id in self.test_manager.config_process_dict)
        self.assertFalse(
            self.node_config_4.node_id in self.test_manager.config_process_dict)

    @mock.patch.object(NodeMonitorsManager,
                       "process_and_send_monitorable_data")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    def test_process_evm_node_configs_return_if_valid_deleted_confs(
            self, startup_mock, mock_terminate, mock_join,
            mock_process_send_mon_data) -> None:
        # In this test we will assume that all sent configurations are valid.
        # Thus we need to check that the function returns a dict containing all
        # the configurations which have an associated running monitor process.
        startup_mock.return_value = None
        mock_terminate.return_value = None
        mock_join.return_value = None
        mock_process_send_mon_data.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example
        self.test_manager._nodes_configs = self.nodes_configs_example
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink_evm)
        del sent_configs[self.node_config_4.node_id]

        actual_return = self.test_manager._process_chainlink_node_configs(
            sent_configs,
            self.nodes_configs_example['chainlink Binance Smart Chain'][
                'evm_nodes_config'], '', '')
        self.assertEqual(sent_configs, actual_return)

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_ignores_default_key(self, mock_ack) -> None:
        # This test will pass if the stored nodes' config does not change.
        # This would mean that the DEFAULT key was ignored, otherwise, it would
        # have been included as a new config.
        mock_ack.return_value = None
        old_nodes_configs = copy.deepcopy(self.nodes_configs_example)
        self.test_manager._nodes_configs = self.nodes_configs_example

        # We will pass the acceptable schema as a value to make sure that the
        # default key will never be added. By passing the schema we will also
        # prevent processing errors from happening.
        sent_configs = copy.deepcopy(self.sent_configs_example_chainlink)
        sent_configs['DEFAULT'] = {
            'id': self.node_config_1.node_id,
            'parent_id': self.node_config_1.parent_id,
            'name': self.node_config_1.node_name,
            'node_prometheus_urls':
                ','.join(self.node_config_1.node_prometheus_urls),
            'monitor_node': str(self.node_config_1.monitor_node),
            'monitor_prometheus': str(self.node_config_1.monitor_prometheus)
        }

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=self.chainlink_routing_key)
        body = bytes(json.dumps(sent_configs), 'utf-8')
        properties = pika.spec.BasicProperties()
        self.test_manager._process_configs(blocking_channel, method, properties,
                                           body)

        self.assertEqual(old_nodes_configs, self.test_manager.nodes_configs)
        mock_ack.assert_called_once()

    @parameterized.expand([
        ('self.chainlink_routing_key', 'self.sent_configs_example_chainlink'),
        ('self.chainlink_evm_routing_key',
         'self.sent_configs_example_chainlink_evm',),
        ('self.cosmos_routing_key', 'self.sent_configs_example_cosmos',),
        ('self.polkadot_routing_key', 'self.sent_configs_example_polkadot',),
    ])
    @mock.patch.object(multiprocessing.Process, 'start')
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_stores_updated_confs_correctly_if_recognized(
            self, routing_key, sent_configs, mock_ack, mock_start) -> None:
        mock_ack.return_value = None
        mock_start.return_value = None

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=eval(routing_key))
        body = bytes(json.dumps(eval(sent_configs)), 'utf-8')
        properties = pika.spec.BasicProperties()

        self.assertEqual({}, self.test_manager.nodes_configs)
        self.test_manager._process_configs(blocking_channel, method, properties,
                                           body)
        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        config_type = parsed_routing_key[3]
        expected_nodes_configs = {
            chain: {
                config_type: self.nodes_configs_example[chain][config_type]
            },
        }
        self.assertEqual(expected_nodes_configs,
                         self.test_manager.nodes_configs)
        mock_ack.assert_called_once()

    @mock.patch.object(multiprocessing.Process, 'start')
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_configs_stores_empty_dict_if_unrecognised_configuration(
            self, mock_ack, mock_start) -> None:
        mock_ack.return_value = None
        mock_start.return_value = None

        # Must create a connection so that the blocking channel is passed
        self.test_manager.rabbitmq.connect()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(
            routing_key=self.test_chain_routing_key)
        body = bytes(json.dumps(self.sent_configs_example_test_chain), 'utf-8')
        properties = pika.spec.BasicProperties()

        self.assertEqual({}, self.test_manager.nodes_configs)
        self.test_manager._process_configs(blocking_channel, method, properties,
                                           body)
        parsed_routing_key = method.routing_key.split('.')
        chain = parsed_routing_key[1] + ' ' + parsed_routing_key[2]
        config_type = parsed_routing_key[3]
        expected_nodes_configs = {
            chain: {
                config_type: {}
            }
        }
        self.assertEqual(expected_nodes_configs,
                         self.test_manager.nodes_configs)
        mock_ack.assert_called_once()

    @parameterized.expand([
        ([True, True, True, True, True, True, True, True, True, True, True],
         [],),
        ([True, False, True, True, True, True, True, True, True, True, True],
         ['node_id_2'],),
        ([False, False, False, True, True, True, False, True, True, True,
          False],
         ['node_id_1', 'node_id_2', 'node_id_3', 'node_id_7', 'node_id_11'],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb(
            self, is_alive_side_effect, dead_configs, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method,
                                        properties, body)

        expected_hb = {
            'component_name': self.manager_name,
            'running_processes': [
                self.config_process_dict_example[config_id]['component_name']
                for config_id in self.config_process_dict_example
                if config_id not in dead_configs
            ],
            'dead_processes': [
                self.config_process_dict_example[config_id]['component_name']
                for config_id in self.config_process_dict_example
                if config_id in dead_configs
            ],
            'timestamp': datetime.now().timestamp()
        }
        mock_send_hb.assert_called_once_with(expected_hb)

    @parameterized.expand([
        ([True, True, True, True, True, True, True, True, True, True, True],
         [],),
        ([True, False, True, True, True, True, True, True, True, True, True],
         ['node_id_2'],),
        ([False, False, False, True, True, True, False, True, True, True,
          False],
         ['node_id_1', 'node_id_2', 'node_id_3', 'node_id_7', 'node_id_11'],),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(NodeMonitorsManager, "_create_and_start_monitor_process")
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_restarts_dead_processes_correctly(
            self, is_alive_side_effect, dead_configs, mock_send_hb,
            mock_create_and_start, mock_is_alive, mock_join) -> None:
        mock_send_hb.return_value = None
        mock_join.return_value = None
        mock_create_and_start.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method,
                                        properties, body)

        expected_calls = [
            call(self.config_process_dict_example[config_id]['node_config'],
                 config_id,
                 self.config_process_dict_example[config_id]['monitor_type'],
                 self.config_process_dict_example[config_id]['base_chain'],
                 self.config_process_dict_example[config_id]['sub_chain'],
                 *self.config_process_dict_example[config_id]['args'])
            for config_id in self.config_process_dict_example
            if config_id in dead_configs
        ]
        actual_calls = mock_create_and_start.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_does_not_send_hb_if_processing_fails(
            self, mock_send_hb, mock_is_alive) -> None:
        mock_is_alive.side_effect = self.test_exception
        mock_send_hb.return_value = None
        self.test_manager._config_process_dict = \
            self.config_process_dict_example

        # Some of the variables below are needed as parameters for the
        # process_ping function
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        self.test_manager._process_ping(blocking_channel, method,
                                        properties, body)

        mock_send_hb.assert_not_called()

    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self) -> None:
        # In this test we are assuming that no configs have been set, this is
        # done to keep the test as simple as possible. We are also assuming that
        # a MsgWasNotDeliveredException will be raised automatically because
        # we are deleting the HealthExchange after every test, and thus there
        # are no consumers of the heartbeat.
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = b'ping'
        properties = pika.spec.BasicProperties()

        try:
            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except MessageWasNotDeliveredException:
            self.fail('A MessageWasNotDeliveredException should not have been '
                      'raised')

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(NodeMonitorsManager, "_send_heartbeat")
    def test_process_ping_raises_unrecognised_error_if_raised_by_send_heartbeat(
            self, exception_class, exception_instance, mock_send_hb) -> None:
        mock_send_hb.side_effect = exception_instance
        self.test_manager._initialise_rabbitmq()
        blocking_channel = self.test_manager.rabbitmq.channel
        method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
        body = 'ping'
        properties = pika.spec.BasicProperties()

        self.assertRaises(exception_class, self.test_manager._process_ping,
                          blocking_channel, method, properties, body)
