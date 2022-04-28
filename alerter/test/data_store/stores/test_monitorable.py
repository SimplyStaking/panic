import json
import logging
import unittest
from datetime import datetime
from datetime import timedelta
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.data_store.mongo import MongoApi
from src.data_store.stores.monitorable import MonitorableStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.monitorables import (
    MonitorableType, MONITORABLES_MONGO_COLLECTION)
from src.utils.constants.rabbitmq import (
    MONITORABLE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    MONITORABLE_STORE_INPUT_QUEUE_NAME, HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
    MONITORABLE_STORE_INPUT_ROUTING_KEY, TOPIC)
from src.utils.exceptions import (PANICException)
from test.test_utils.utils import (
    connect_to_rabbit, disconnect_from_rabbit, delete_exchange_if_exists,
    delete_queue_if_exists, process_monitorable_data)


class TestMonitorableStore(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        self.test_rabbit_manager = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)

        self.mongo_ip = env.DB_IP
        self.mongo_db = env.DB_NAME
        self.mongo_port = env.DB_PORT
        self.mongo = MongoApi(logger=self.dummy_logger.getChild(
            MongoApi.__name__), db_name=self.mongo_db, host=self.mongo_ip,
            port=self.mongo_port)

        self.redis = None

        self.test_store_name = 'store name'
        self.test_store = MonitorableStore(self.test_store_name,
                                           self.dummy_logger, self.rabbitmq)

        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.test_queue_name = 'test queue'

        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.rabbitmq.exchange_declare(MONITORABLE_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.rabbitmq.queue_declare(MONITORABLE_STORE_INPUT_QUEUE_NAME,
                                    False, True, False, False)
        self.rabbitmq.queue_bind(MONITORABLE_STORE_INPUT_QUEUE_NAME,
                                 MONITORABLE_EXCHANGE,
                                 MONITORABLE_STORE_INPUT_ROUTING_KEY)

        connect_to_rabbit(self.test_rabbit_manager)
        self.test_rabbit_manager.queue_declare(self.test_queue_name, False,
                                               True, False, False)
        self.test_rabbit_manager.queue_bind(self.test_queue_name,
                                            HEALTH_CHECK_EXCHANGE,
                                            self.heartbeat_routing_key)

        self.test_parent_id = 'parent_id'

        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)

        self.last_monitored = datetime(2012, 1, 1).timestamp()

        self.routing_key_1 = 'cosmos.{}'.format(MonitorableType.SYSTEMS.value)
        self.routing_key_2 = 'cosmos.{}'.format(MonitorableType.NODES.value)
        self.routing_key_3 = 'cosmos.{}'.format(
            MonitorableType.GITHUB_REPOS.value)
        self.routing_key_4 = 'cosmos.{}'.format(
            MonitorableType.DOCKERHUB_REPOS.value)

        self.routing_key_5 = 'general.{}'.format(MonitorableType.SYSTEMS.value)
        self.routing_key_6 = 'general.{}'.format(
            MonitorableType.GITHUB_REPOS.value)

        self.routing_key_7 = 'chainlink.{}'.format(
            MonitorableType.SYSTEMS.value)
        self.routing_key_8 = 'chainlink.{}'.format(
            MonitorableType.NODES.value)
        self.routing_key_9 = 'chainlink.{}'.format(
            MonitorableType.GITHUB_REPOS.value)
        self.routing_key_10 = 'chainlink.{}'.format(
            MonitorableType.CHAINS.value)
        self.routing_key_11 = 'chainlink.{}'.format(
            MonitorableType.NODES.value)

        self.routing_key_12 = 'substrate.{}'.format(
            MonitorableType.NODES.value)

        self.routing_key_13 = 'newbasechain.invalid'
        self.routing_key_14 = '.{}'.format(
            MonitorableType.NODES.value)
        self.routing_key_15 = 'cosmos.'

        self.monitorable_data_1 = {
            'manager_name': 'System Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_1',
                    'chain_name': 'Cosmos Hub',
                    'source_id': 'cosmoshub_system_1',
                    'source_name': 'CosmosHub System 1'
                },
                {
                    'chain_id': 'chain_1',
                    'chain_name': 'Cosmos Hub',
                    'source_id': 'cosmoshub_system_2',
                    'source_name': 'CosmosHub System 2'
                },
                {
                    'chain_id': 'chain_2',
                    'chain_name': 'Akash',
                    'source_id': 'akash_system_1',
                    'source_name': 'Akash System 1'
                }
            ]
        }

        self.monitorable_data_2 = {
            'manager_name': 'Node Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_1',
                    'chain_name': 'Cosmos Hub',
                    'source_id': 'cosmoshub_node_1',
                    'source_name': 'CosmosHub Node 1'
                },
                {
                    'chain_id': 'chain_2',
                    'chain_name': 'Akash',
                    'source_id': 'akash_node_1',
                    'source_name': 'Akash Node 1'
                },
                {
                    'chain_id': 'chain_2',
                    'chain_name': 'Akash',
                    'source_id': 'akash_node_2',
                    'source_name': 'Akash Node 2'
                }
            ]
        }

        self.monitorable_data_3 = {
            'manager_name': 'GitHub Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_1',
                    'chain_name': 'Cosmos Hub',
                    'source_id': 'cosmoshub_github_repo_1',
                    'source_name': 'CosmosHub GitHub Repo 1'
                },
                {
                    'chain_id': 'chain_2',
                    'chain_name': 'Akash',
                    'source_id': 'akash_github_repo_1',
                    'source_name': 'Akash GitHub Repo 1'
                }
            ]
        }

        self.monitorable_data_4 = {
            'manager_name': 'DockerHub Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_1',
                    'chain_name': 'Cosmos Hub',
                    'source_id': 'cosmoshub_dockerhub_repo_1',
                    'source_name': 'CosmosHub DockerHub Repo 1'
                },
                {
                    'chain_id': 'chain_2',
                    'chain_name': 'Akash',
                    'source_id': 'akash_dockerhub_repo_1',
                    'source_name': 'Akash DockerHub Repo 1'
                }
            ]
        }

        self.monitorable_data_5 = {
            'manager_name': 'System Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_3',
                    'chain_name': 'General Chain',
                    'source_id': 'general_system_1',
                    'source_name': 'General System 1'
                },
                {
                    'chain_id': 'chain_3',
                    'chain_name': 'General Chain',
                    'source_id': 'general_system_2',
                    'source_name': 'General System 2'
                }
            ]
        }

        self.monitorable_data_6 = {
            'manager_name': 'GitHub Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_3',
                    'chain_name': 'General Chain',
                    'source_id': 'general_github_repo_1',
                    'source_name': 'General GitHub Repo 1'
                }
            ]
        }

        self.monitorable_data_7 = {
            'manager_name': 'System Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_4',
                    'chain_name': 'Chainlink',
                    'source_id': 'chainlink_system_1',
                    'source_name': 'Chainlink System 1'
                },
                {
                    'chain_id': 'chain_5',
                    'chain_name': 'Binance Smart Chain',
                    'source_id': 'bsc_system_1',
                    'source_name': 'Binance Smart Chain System 1'
                }
            ]
        }

        self.monitorable_data_8 = {
            'manager_name': 'Node Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_4',
                    'chain_name': 'Chainlink',
                    'source_id': 'chainlink_node_1',
                    'source_name': 'Chainlink Node 1'
                },
                {
                    'chain_id': 'chain_5',
                    'chain_name': 'Binance Smart Chain',
                    'source_id': 'bsc_node_1',
                    'source_name': 'Binance Smart Chain Node 1'
                },
                {
                    'chain_id': 'chain_4',
                    'chain_name': 'Chainlink',
                    'source_id': 'chainlink_evm_node_1',
                    'source_name': 'Chainlink EVM Node 1'
                },
                {
                    'chain_id': 'chain_5',
                    'chain_name': 'Binance Smart Chain',
                    'source_id': 'bsc_evm_node_1',
                    'source_name': 'Binance Smart Chain EVM Node 1'
                }
            ]
        }

        self.monitorable_data_9 = {
            'manager_name': 'GitHub Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_4',
                    'chain_name': 'Chainlink',
                    'source_id': 'chainlink_github_repo_1',
                    'source_name': 'Chainlink GitHub Repo 1'
                },
                {
                    'chain_id': 'chain_5',
                    'chain_name': 'Binance Smart Chain',
                    'source_id': 'bsc_github_repo_1',
                    'source_name': 'Binance Smart Chain GitHub Repo 1'
                }
            ]
        }

        self.monitorable_data_10 = {
            'manager_name': 'Contract Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_4',
                    'chain_name': 'Chainlink',
                    'source_id': 'chainlink_chain_1',
                    'source_name': 'Chainlink Chain 1'
                }
            ]
        }

        self.monitorable_data_11 = {
            'manager_name': 'Contract Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_4',
                    'chain_name': 'Chainlink',
                    'source_id': 'chainlink_node_1',
                    'source_name': 'Chainlink Node 1'
                }
            ]
        }

        self.monitorable_data_12 = {
            'manager_name': 'Node Monitors Manager',
            'sources': [
                {
                    'chain_id': 'chain_6',
                    'chain_name': 'Kusama',
                    'source_id': 'kusama_node_1',
                    'source_name': 'Kusama Node 1'
                },
                {
                    'chain_id': 'chain_6',
                    'chain_name': 'Kusama',
                    'source_id': 'kusama_node_2',
                    'source_name': 'Kusama Node 2'
                },
                {
                    'chain_id': 'chain_7',
                    'chain_name': 'Moonbeam',
                    'source_id': 'moonbeam_node_1',
                    'source_name': 'Moonbeam Node 1'
                },
                {
                    'chain_id': 'chain_7',
                    'chain_name': 'Moonbeam',
                    'source_id': 'moonbeam_node_2',
                    'source_name': 'Moonbeam Node 2'
                }
            ]
        }

        self.expected_monitorables_1 = {
            'chain_1': {
                'chain_name': 'Cosmos Hub',
                MonitorableType.SYSTEMS.value: {
                    'cosmoshub_system_1': {
                        'name': 'CosmosHub System 1',
                        'manager_names': ['System Monitors Manager']
                    },
                    'cosmoshub_system_2': {
                        'name': 'CosmosHub System 2',
                        'manager_names': ['System Monitors Manager']
                    }
                },
                MonitorableType.NODES.value: {
                    'cosmoshub_node_1': {
                        'name': 'CosmosHub Node 1',
                        'manager_names': ['Node Monitors Manager']
                    }
                },
                MonitorableType.GITHUB_REPOS.value: {
                    'cosmoshub_github_repo_1': {
                        'name': 'CosmosHub GitHub Repo 1',
                        'manager_names': ['GitHub Monitors Manager']
                    }
                },
                MonitorableType.DOCKERHUB_REPOS.value: {
                    'cosmoshub_dockerhub_repo_1': {
                        'name': 'CosmosHub DockerHub Repo 1',
                        'manager_names': ['DockerHub Monitors Manager']
                    }
                },
                MonitorableType.CHAINS.value: {}
            },
            'chain_2': {
                'chain_name': 'Akash',
                MonitorableType.SYSTEMS.value: {
                    'akash_system_1': {
                        'name': 'Akash System 1',
                        'manager_names': ['System Monitors Manager']
                    }
                },
                MonitorableType.NODES.value: {
                    'akash_node_1': {
                        'name': 'Akash Node 1',
                        'manager_names': ['Node Monitors Manager']
                    },
                    'akash_node_2': {
                        'name': 'Akash Node 2',
                        'manager_names': ['Node Monitors Manager']
                    }
                },
                MonitorableType.GITHUB_REPOS.value: {
                    'akash_github_repo_1': {
                        'name': 'Akash GitHub Repo 1',
                        'manager_names': ['GitHub Monitors Manager']
                    }
                },
                MonitorableType.DOCKERHUB_REPOS.value: {
                    'akash_dockerhub_repo_1': {
                        'name': 'Akash DockerHub Repo 1',
                        'manager_names': ['DockerHub Monitors Manager']
                    }
                },
                MonitorableType.CHAINS.value: {}
            }
        }

        self.expected_monitorables_2 = {
            'chain_3': {
                'chain_name': 'General Chain',
                MonitorableType.SYSTEMS.value: {
                    'general_system_1': {
                        'name': 'General System 1',
                        'manager_names': ['System Monitors Manager']
                    },
                    'general_system_2': {
                        'name': 'General System 2',
                        'manager_names': ['System Monitors Manager']
                    }
                },
                MonitorableType.NODES.value: {},
                MonitorableType.GITHUB_REPOS.value: {
                    'general_github_repo_1': {
                        'name': 'General GitHub Repo 1',
                        'manager_names': ['GitHub Monitors Manager']
                    }
                },
                MonitorableType.DOCKERHUB_REPOS.value: {},
                MonitorableType.CHAINS.value: {}
            }
        }

        self.expected_monitorables_3 = {
            'chain_4': {
                'chain_name': 'Chainlink',
                MonitorableType.SYSTEMS.value: {
                    'chainlink_system_1': {
                        'name': 'Chainlink System 1',
                        'manager_names': ['System Monitors Manager']
                    }
                },
                MonitorableType.NODES.value: {
                    'chainlink_node_1': {
                        'name': 'Chainlink Node 1',
                        'manager_names': ['Node Monitors Manager',
                                          'Contract Monitors Manager']
                    },
                    'chainlink_evm_node_1': {
                        'name': 'Chainlink EVM Node 1',
                        'manager_names': ['Node Monitors Manager']
                    }
                },
                MonitorableType.GITHUB_REPOS.value: {
                    'chainlink_github_repo_1': {
                        'name': 'Chainlink GitHub Repo 1',
                        'manager_names': ['GitHub Monitors Manager']
                    }
                },
                MonitorableType.DOCKERHUB_REPOS.value: {},
                MonitorableType.CHAINS.value: {
                    'chainlink_chain_1': {
                        'name': 'Chainlink Chain 1',
                        'manager_names': ['Contract Monitors Manager']
                    }
                }
            },
            'chain_5': {
                'chain_name': 'Binance Smart Chain',
                MonitorableType.SYSTEMS.value: {
                    'bsc_system_1': {
                        'name': 'Binance Smart Chain System 1',
                        'manager_names': ['System Monitors Manager']
                    }
                },
                MonitorableType.NODES.value: {
                    'bsc_node_1': {
                        'name': 'Binance Smart Chain Node 1',
                        'manager_names': ['Node Monitors Manager']
                    },
                    'bsc_evm_node_1': {
                        'name': 'Binance Smart Chain EVM Node 1',
                        'manager_names': ['Node Monitors Manager']
                    }
                },
                MonitorableType.GITHUB_REPOS.value: {
                    'bsc_github_repo_1': {
                        'name': 'Binance Smart Chain GitHub Repo 1',
                        'manager_names': ['GitHub Monitors Manager']
                    }
                },
                MonitorableType.DOCKERHUB_REPOS.value: {},
                MonitorableType.CHAINS.value: {}
            }
        }

        self.expected_monitorables_4 = {
            'chain_6': {
                'chain_name': 'Kusama',
                MonitorableType.SYSTEMS.value: {},
                MonitorableType.NODES.value: {
                    'kusama_node_1': {
                        'name': 'Kusama Node 1',
                        'manager_names': ['Node Monitors Manager']
                    },
                    'kusama_node_2': {
                        'name': 'Kusama Node 2',
                        'manager_names': ['Node Monitors Manager']
                    }
                },
                MonitorableType.GITHUB_REPOS.value: {},
                MonitorableType.DOCKERHUB_REPOS.value: {},
                MonitorableType.CHAINS.value: {}
            },
            'chain_7': {
                'chain_name': 'Moonbeam',
                MonitorableType.SYSTEMS.value: {},
                MonitorableType.NODES.value: {
                    'moonbeam_node_1': {
                        'name': 'Moonbeam Node 1',
                        'manager_names': ['Node Monitors Manager']
                    },
                    'moonbeam_node_2': {
                        'name': 'Moonbeam Node 2',
                        'manager_names': ['Node Monitors Manager']
                    }
                },
                MonitorableType.GITHUB_REPOS.value: {},
                MonitorableType.DOCKERHUB_REPOS.value: {},
                MonitorableType.CHAINS.value: {}
            }
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq,
                               MONITORABLE_STORE_INPUT_QUEUE_NAME)
        delete_exchange_if_exists(self.rabbitmq, MONITORABLE_EXCHANGE)
        delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        connect_to_rabbit(self.test_rabbit_manager)
        delete_queue_if_exists(self.test_rabbit_manager, self.test_queue_name)
        disconnect_from_rabbit(self.test_rabbit_manager)

        self.mongo.drop_collection(MONITORABLES_MONGO_COLLECTION)
        self.mongo = None
        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
        self.test_store._mongo = None
        self.test_store._redis = None
        self.test_rabbit_manager = None
        self.test_store = None

    def test__str__returns_name_correctly(self) -> None:
        self.assertEqual(self.test_store_name, str(self.test_store))

    def test_name_property_returns_name_correctly(self) -> None:
        self.assertEqual(self.test_store_name, self.test_store.name)

    def test_mongo_ip_property_returns_mongo_ip_correctly(self) -> None:
        self.assertEqual(self.mongo_ip, self.test_store.mongo_ip)

    def test_mongo_db_property_returns_mongo_db_correctly(self) -> None:
        self.assertEqual(self.mongo_db, self.test_store.mongo_db)

    def test_mongo_port_property_returns_mongo_port_correctly(self) -> None:
        self.assertEqual(self.mongo_port, self.test_store.mongo_port)

    def test_mongo_property_returns_mongo_correctly(self) -> None:
        self.assertEqual(type(self.mongo), type(self.test_store.mongo))

    def test_redis_property_returns_none_when_redis_not_init(self) -> None:
        self.assertEqual(None, self.test_store.redis)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that the exchanges have not already been declared
        self.rabbitmq.connect()
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_delete(MONITORABLE_EXCHANGE)
        self.rabbitmq.disconnect()

        self.test_store._initialise_rabbitmq()

        # Perform checks that the connection has been opened, marked as open
        # and that the delivery confirmation variable is set.
        self.assertTrue(self.test_store.rabbitmq.is_connected)
        self.assertTrue(self.test_store.rabbitmq.connection.is_open)
        self.assertTrue(
            self.test_store.rabbitmq.channel._delivery_confirmation)

        # Check whether the producing exchanges have been created by using
        # passive=True. If this check fails an exception is raised
        # automatically.
        self.test_store.rabbitmq.exchange_declare(
            MONITORABLE_EXCHANGE, passive=True)
        self.test_store.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE,
                                                  passive=True)

        # Check whether the queue has been creating by sending messages with the
        # same routing key. If this fails an exception is raised, hence the test
        # fails.
        self.test_store.rabbitmq.basic_publish_confirm(
            exchange=MONITORABLE_EXCHANGE,
            routing_key=MONITORABLE_STORE_INPUT_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            MONITORABLE_STORE_INPUT_QUEUE_NAME, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

    @freeze_time("2012-01-01")
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.monitorable.MonitorableStore"
                "._process_mongo_store",
                autospec=True)
    def test_process_data_sends_heartbeat_correctly(
            self, mock_process_mongo_store, mock_basic_ack
    ) -> None:
        mock_basic_ack.return_value = None
        self.test_rabbit_manager.connect()
        self.test_store._initialise_rabbitmq()

        self.test_rabbit_manager.queue_delete(self.test_queue_name)
        res = self.test_rabbit_manager.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)

        self.test_rabbit_manager.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=self.heartbeat_routing_key)

        blocking_channel = self.test_store.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(routing_key=self.routing_key_1)

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(blocking_channel, method_chains,
                                      properties,
                                      json.dumps(self.monitorable_data_1))

        res = self.test_rabbit_manager.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(1, res.method.message_count)

        heartbeat_test = {
            'component_name': self.test_store_name,
            'is_alive': True,
            'timestamp': datetime(2012, 1, 1).timestamp()
        }

        _, _, body = self.test_rabbit_manager.basic_get(self.test_queue_name)
        self.assertEqual(heartbeat_test, json.loads(body))
        mock_process_mongo_store.assert_called_once()

    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    def test_process_data_doesnt_send_heartbeat_on_processing_error(
            self, mock_basic_ack) -> None:
        mock_basic_ack.return_value = None
        self.test_rabbit_manager.connect()
        self.test_store._initialise_rabbitmq()

        self.test_rabbit_manager.queue_delete(self.test_queue_name)
        res = self.test_rabbit_manager.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=False
        )
        self.assertEqual(0, res.method.message_count)

        self.test_rabbit_manager.queue_bind(
            queue=self.test_queue_name, exchange=HEALTH_CHECK_EXCHANGE,
            routing_key=self.heartbeat_routing_key)

        blocking_channel = self.test_store.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(routing_key=None)

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(blocking_channel, method_chains,
                                      properties,
                                      json.dumps(self.monitorable_data_1))

        res = self.test_rabbit_manager.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(0, res.method.message_count)

    @parameterized.expand([
        ("self.monitorable_data_1", "self.routing_key_1"),
        ("self.monitorable_data_2", "self.routing_key_2"),
        ("self.monitorable_data_3", "self.routing_key_3"),
        ("self.monitorable_data_4", "self.routing_key_4"),
        ("self.monitorable_data_5", "self.routing_key_5"),
        ("self.monitorable_data_6", "self.routing_key_6"),
        ("self.monitorable_data_7", "self.routing_key_7"),
        ("self.monitorable_data_8", "self.routing_key_8"),
        ("self.monitorable_data_9", "self.routing_key_9"),
        ("self.monitorable_data_10", "self.routing_key_10"),
        ("self.monitorable_data_11", "self.routing_key_11"),
        ("self.monitorable_data_12", "self.routing_key_12"),
    ])
    @mock.patch.object(MongoApi, "replace_one")
    @mock.patch.object(MongoApi, "get_one")
    def test_process_mongo_store(
            self, mock_monitorable_data, mock_routing_key, mock_get_one,
            mock_replace_one) -> None:
        mock_get_one.return_value = None

        self.test_store._process_mongo_store(
            eval(mock_routing_key), eval(mock_monitorable_data))

        base_chain, base_chain_data = process_monitorable_data(
            self.test_store, eval(mock_routing_key),
            eval(mock_monitorable_data))

        args, _ = mock_replace_one.call_args
        self.assertEqual(args[0], MONITORABLES_MONGO_COLLECTION)
        self.assertEqual(args[1], {'_id': base_chain})
        self.assertEqual(args[2], base_chain_data)

    @parameterized.expand([
        ("self.monitorable_data_1", "self.routing_key_1"),
        ("self.monitorable_data_2", "self.routing_key_2"),
        ("self.monitorable_data_3", "self.routing_key_3"),
        ("self.monitorable_data_4", "self.routing_key_4"),
        ("self.monitorable_data_5", "self.routing_key_5"),
        ("self.monitorable_data_6", "self.routing_key_6"),
        ("self.monitorable_data_7", "self.routing_key_7"),
        ("self.monitorable_data_8", "self.routing_key_8"),
        ("self.monitorable_data_9", "self.routing_key_9"),
        ("self.monitorable_data_10", "self.routing_key_10"),
        ("self.monitorable_data_11", "self.routing_key_11"),
        ("self.monitorable_data_12", "self.routing_key_12"),
    ])
    def test_process_mongo_store_stores_in_mongo_correctly(
            self, mock_monitorable_data, mock_routing_key) -> None:
        self.test_store._process_mongo_store(
            eval(mock_routing_key), eval(mock_monitorable_data))

        base_chain, base_chain_data = process_monitorable_data(
            self.test_store, eval(mock_routing_key),
            eval(mock_monitorable_data))

        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain, **base_chain_data})

    @parameterized.expand([
        ([("self.monitorable_data_1", "self.routing_key_1"),
          ("self.monitorable_data_2", "self.routing_key_2"),
          ("self.monitorable_data_3", "self.routing_key_3"),
          ("self.monitorable_data_4", "self.routing_key_4")],
         "self.expected_monitorables_1"),
        ([("self.monitorable_data_5", "self.routing_key_5"),
          ("self.monitorable_data_6", "self.routing_key_6")],
         "self.expected_monitorables_2"),
        ([("self.monitorable_data_7", "self.routing_key_7"),
          ("self.monitorable_data_8", "self.routing_key_8"),
          ("self.monitorable_data_9", "self.routing_key_9"),
          ("self.monitorable_data_10", "self.routing_key_10"),
          ("self.monitorable_data_11", "self.routing_key_11")],
         "self.expected_monitorables_3"),
        ([("self.monitorable_data_12", "self.routing_key_12")],
         "self.expected_monitorables_4")
    ])
    def test_process_mongo_store_stores_sources_in_mongo_correctly(
            self, mock_monitorable_data_and_routing_keys,
            mock_expected_monitorables) -> None:
        # Extract base chain from the first routing key since we need to
        # check the database for the value of this entry.
        base_chain, _ = \
            self.test_store._process_routing_key(eval(
                mock_monitorable_data_and_routing_keys[0][1]))

        for mock_monitorable_data, mock_routing_key in \
                mock_monitorable_data_and_routing_keys:
            self.test_store._process_mongo_store(
                eval(mock_routing_key), eval(mock_monitorable_data))

        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain, **eval(mock_expected_monitorables)})

    @parameterized.expand([
        ("self.monitorable_data_1", "self.routing_key_1"),
        ("self.monitorable_data_2", "self.routing_key_2"),
        ("self.monitorable_data_3", "self.routing_key_3"),
        ("self.monitorable_data_4", "self.routing_key_4"),
        ("self.monitorable_data_5", "self.routing_key_5"),
        ("self.monitorable_data_6", "self.routing_key_6"),
        ("self.monitorable_data_7", "self.routing_key_7"),
        ("self.monitorable_data_8", "self.routing_key_8"),
        ("self.monitorable_data_9", "self.routing_key_9"),
        ("self.monitorable_data_10", "self.routing_key_10"),
        ("self.monitorable_data_11", "self.routing_key_11"),
        ("self.monitorable_data_12", "self.routing_key_12"),
    ])
    def test_process_mongo_store_stores_in_mongo_correctly_then_deletes(
            self, mock_monitorable_data, mock_routing_key) -> None:
        self.test_store._process_mongo_store(
            eval(mock_routing_key), eval(mock_monitorable_data))

        base_chain, base_chain_data = process_monitorable_data(
            self.test_store, eval(mock_routing_key),
            eval(mock_monitorable_data))

        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain, **base_chain_data})

        self.test_store._process_mongo_store(
            eval(mock_routing_key), {
                'manager_name': eval(mock_monitorable_data)['manager_name'],
                'sources': []
            }
        )

        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain})

    @parameterized.expand([
        ("self.monitorable_data_1", "self.routing_key_1",
         "self.monitorable_data_5", "self.routing_key_5"),
        ("self.monitorable_data_1", "self.routing_key_1",
         "self.monitorable_data_8", "self.routing_key_8"),
        ("self.monitorable_data_1", "self.routing_key_1",
         "self.monitorable_data_12", "self.routing_key_12"),
        ("self.monitorable_data_5", "self.routing_key_5",
         "self.monitorable_data_3", "self.routing_key_3"),
        ("self.monitorable_data_5", "self.routing_key_5",
         "self.monitorable_data_9", "self.routing_key_9"),
        ("self.monitorable_data_5", "self.routing_key_5",
         "self.monitorable_data_12", "self.routing_key_12"),
        ("self.monitorable_data_8", "self.routing_key_8",
         "self.monitorable_data_4", "self.routing_key_4"),
        ("self.monitorable_data_8", "self.routing_key_8",
         "self.monitorable_data_12", "self.routing_key_12"),
    ])
    def test_process_mongo_store_stores_in_mongo_correctly_does_not_modify_other_monitorables(
            self, mock_monitorable_data, mock_routing_key,
            mock_monitorable_data_2, mock_routing_key_2) -> None:
        # Store two things after each other and then verify that they are
        # stored correctly
        self.test_store._process_mongo_store(
            eval(mock_routing_key), eval(mock_monitorable_data))
        self.test_store._process_mongo_store(
            eval(mock_routing_key_2), eval(mock_monitorable_data_2))

        base_chain, base_chain_data = process_monitorable_data(
            self.test_store, eval(mock_routing_key),
            eval(mock_monitorable_data))

        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain, **base_chain_data})

        # Repeat the process with the second monitorable data to ensure data
        # was saved correctly
        base_chain, base_chain_data = process_monitorable_data(
            self.test_store, eval(mock_routing_key),
            eval(mock_monitorable_data))

        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain, **base_chain_data})

    @parameterized.expand([
        ("self.monitorable_data_1", "self.routing_key_1",
         "self.monitorable_data_2", "self.routing_key_2"),
        ("self.monitorable_data_5", "self.routing_key_5",
         "self.monitorable_data_6", "self.routing_key_6"),
        ("self.monitorable_data_7", "self.routing_key_7",
         "self.monitorable_data_8", "self.routing_key_8"),
        ("self.monitorable_data_7", "self.routing_key_7",
         "self.monitorable_data_9", "self.routing_key_9"),
        ("self.monitorable_data_10", "self.routing_key_10",
         "self.monitorable_data_9", "self.routing_key_9"),
        ("self.monitorable_data_10", "self.routing_key_10",
         "self.monitorable_data_11", "self.routing_key_11"),
    ])
    def test_process_mongo_store_stores_in_mongo_correctly_removes_correct_data(
            self, mock_monitorable_data, mock_routing_key,
            mock_monitorable_data_2, mock_routing_key_2) -> None:
        base_chain_data = {}

        # Store two things after each other.
        self.test_store._process_mongo_store(
            eval(mock_routing_key), eval(mock_monitorable_data))
        self.test_store._process_mongo_store(
            eval(mock_routing_key_2), eval(mock_monitorable_data_2))

        # Remove first set of data.
        self.test_store._process_mongo_store(
            eval(mock_routing_key), {
                'manager_name': eval(mock_monitorable_data)['manager_name'],
                'sources': []
            })

        # Only add data from the second set since the first set should be
        # removed from Mongo.
        base_chain, base_chain_data = process_monitorable_data(
            self.test_store, eval(mock_routing_key_2),
            eval(mock_monitorable_data_2))

        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain, **base_chain_data})

    @parameterized.expand([
        ("self.routing_key_1"),
        ("self.routing_key_2"),
        ("self.routing_key_3"),
        ("self.routing_key_4"),
        ("self.routing_key_5"),
        ("self.routing_key_6"),
        ("self.routing_key_7"),
        ("self.routing_key_8"),
        ("self.routing_key_9"),
        ("self.routing_key_10"),
        ("self.routing_key_11"),
    ])
    def test_process_mongo_store_if_only_empty_data_sent(
            self, mock_routing_key) -> None:
        # In this test we will send only empty data to check the data stored
        # in mongo if no monitorable data is stored.
        self.test_store._process_mongo_store(
            eval(mock_routing_key), {
                'manager_name': 'Test Monitors Manager',
                'sources': []
            }
        )

        # Check that all data has been stored before performing the test
        base_chain, _ = \
            self.test_store._process_routing_key(eval(mock_routing_key))
        self.assertEqual(self.test_store.mongo.get_one(
            MONITORABLES_MONGO_COLLECTION, {'_id': base_chain}),
            {'_id': base_chain})

    @parameterized.expand([
        ("self.routing_key_1", "cosmos", MonitorableType.SYSTEMS),
        ("self.routing_key_2", "cosmos", MonitorableType.NODES),
        ("self.routing_key_3", "cosmos", MonitorableType.GITHUB_REPOS),
        ("self.routing_key_4", "cosmos", MonitorableType.DOCKERHUB_REPOS),
        ("self.routing_key_5", "general", MonitorableType.SYSTEMS),
        ("self.routing_key_6", "general", MonitorableType.GITHUB_REPOS),
        ("self.routing_key_7", "chainlink", MonitorableType.SYSTEMS),
        ("self.routing_key_8", "chainlink", MonitorableType.NODES),
        ("self.routing_key_9", "chainlink", MonitorableType.GITHUB_REPOS),
        ("self.routing_key_10", "chainlink", MonitorableType.CHAINS),
        ("self.routing_key_11", "chainlink", MonitorableType.NODES),
        ("self.routing_key_12", "substrate", MonitorableType.NODES),
        ("self.routing_key_13", "newbasechain", ""),
        ("self.routing_key_14", "", MonitorableType.NODES),
        ("self.routing_key_15", "cosmos", ""),
    ])
    def test_process_routing_key_processes_routing_key_correctly(
            self, mock_routing_key, mock_base_chain,
            mock_monitorable_type) -> None:
        base_chain, monitorable_type = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        self.assertEqual(base_chain, mock_base_chain)
        self.assertEqual(monitorable_type, mock_monitorable_type)
