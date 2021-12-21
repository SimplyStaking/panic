import copy
import json
import logging
import unittest
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from unittest import mock

import pika
import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.data_store.redis import RedisApi
from src.data_store.redis.store_keys import Keys
from src.data_store.stores.config import ConfigStore
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.rabbitmq import (CONFIG_EXCHANGE,
                                          HEALTH_CHECK_EXCHANGE,
                                          CONFIGS_STORE_INPUT_QUEUE_NAME,
                                          HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY,
                                          CONFIGS_STORE_INPUT_ROUTING_KEY,
                                          TOPIC)
from src.utils.exceptions import (PANICException)
from test.utils.utils import (connect_to_rabbit,
                              disconnect_from_rabbit,
                              delete_exchange_if_exists,
                              delete_queue_if_exists)


class TestConfigStore(unittest.TestCase):
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

        self.redis_db = env.REDIS_DB
        self.redis_host = env.REDIS_IP
        self.redis_port = env.REDIS_PORT
        self.redis_namespace = env.UNIQUE_ALERTER_IDENTIFIER
        self.redis = RedisApi(self.dummy_logger, self.redis_db,
                              self.redis_host, self.redis_port, '',
                              self.redis_namespace,
                              self.connection_check_time_interval)

        self.mongo_ip = env.DB_IP
        self.mongo_db = env.DB_NAME
        self.mongo_port = env.DB_PORT

        self.test_store_name = 'store name'
        self.test_store = ConfigStore(self.test_store_name,
                                      self.dummy_logger,
                                      self.rabbitmq)

        self.heartbeat_routing_key = HEARTBEAT_OUTPUT_WORKER_ROUTING_KEY
        self.test_queue_name = 'test queue'

        connect_to_rabbit(self.rabbitmq)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, TOPIC, False,
                                       True, False, False)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, TOPIC, False, True,
                                       False, False)
        self.rabbitmq.queue_declare(CONFIGS_STORE_INPUT_QUEUE_NAME, False, True,
                                    False, False)
        self.rabbitmq.queue_bind(CONFIGS_STORE_INPUT_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 CONFIGS_STORE_INPUT_ROUTING_KEY)

        connect_to_rabbit(self.test_rabbit_manager)
        self.test_rabbit_manager.queue_declare(self.test_queue_name, False,
                                               True, False, False)
        self.test_rabbit_manager.queue_bind(self.test_queue_name,
                                            HEALTH_CHECK_EXCHANGE,
                                            self.heartbeat_routing_key)

        self.test_parent_id = 'parent_id'
        self.test_config_type = 'config_type'

        self.test_data_str = 'test data'
        self.test_exception = PANICException('test_exception', 1)

        self.last_monitored = datetime(2012, 1, 1).timestamp()

        self.routing_key_1 = 'chains.cosmos.cosmos.nodes_config'
        self.routing_key_2 = 'chains.cosmos.cosmos.alerts_config'
        self.routing_key_3 = 'chains.cosmos.cosmos.github_repos_config'

        self.routing_key_4 = 'general.github_repos_config'
        self.routing_key_5 = 'general.alerts_config'
        self.routing_key_6 = 'general.systems_config'

        self.routing_key_7 = 'channels.email_config'
        self.routing_key_8 = 'channels.pagerduty_config'
        self.routing_key_9 = 'channels.opsgenie_config'
        self.routing_key_10 = 'channels.telegram_config'
        self.routing_key_11 = 'channels.twilio_config'

        self.routing_key_12 = 'chains.chainlink.bsc.nodes_config'
        self.routing_key_13 = 'chains.chainlink.bsc.alerts_config'
        self.routing_key_14 = 'chains.chainlink.bsc.github_repos_config'
        self.routing_key_15 = 'chains.chainlink.bsc.systems_config'
        self.routing_key_16 = 'chains.chainlink.bsc.evm_nodes_config'

        self.nodes_config_1 = {
            "node_3e0a5189-f474-4120-a0a4-d5ab817c0504": {
                "id": "node_3e0a5189-f474-4120-a0a4-d5ab817c0504",
                "parent_id": "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548",
                "name": "cosmos_sentry_1",
                "monitor_tendermint": "false",
                "monitor_rpc": "false",
                "monitor_prometheus": "false",
                "exporter_url": "test_url",
                "monitor_system": "true",
                "is_validator": "false",
                "monitor_node": "true",
                "is_archive_node": "true",
                "use_as_data_source": "true"
            },
            "node_f8ebf267-9b53-4aa1-9c45-e84a9cba5fbc": {
                "id": "node_f8ebf267-9b53-4aa1-9c45-e84a9cba5fbc",
                "parent_id": "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548",
                "name": "cosmos_sentry_2",
                "monitor_tendermint": "false",
                "monitor_rpc": "false",
                "monitor_prometheus": "false",
                "exporter_url": "test_url",
                "monitor_system": "true",
                "is_validator": "false",
                "monitor_node": "true",
                "is_archive_node": "true",
                "use_as_data_source": "true"
            }
        }

        self.nodes_config_2 = {
            "node_sgdfh4y5u56u56j": {
                "id": "node_sgdfh4y5u56u56j",
                "parent_id": "chain_name_okjhfghuhsiduiusdh",
                "name": "bsc_sentry_1",
                "node_prometheus_urls": "test_url1,test_url2",
                "monitor_prometheus": "true",
                "monitor_node": "true",
                "monitor_contracts": "true",
                "ethereum_addresses":
                    "0xC7040bEeC1A3794C3e7CC9bA5C68070DAD0b4c29"
            },
            "node_dfouihgdfuoghdfuudfh": {
                "id": "node_dfouihgdfuoghdfuudfh",
                "parent_id": "chain_name_okjhfghuhsiduiusdh",
                "name": "bsc_sentry_2",
                "node_prometheus_urls": "test_url1,test_url2",
                "monitor_prometheus": "true",
                "monitor_contracts": "true",
                "monitor_node": "false",
                "ethereum_addresses":
                    "0xC7040bEeC1A3794C3e7CC9bA5C68070MUM0b4c29"
            },
            "node_mkdfkghhnusd": {
                "id": "node_mkdfkghhnusd",
                "parent_id": "chain_name_okjhfghuhsiduiusdh",
                "name": "bsc_sentry_3",
                "node_prometheus_urls": "test_url1,test_url2",
                "monitor_prometheus": "false",
                "monitor_contracts": "false",
                "monitor_node": "true",
                "ethereum_addresses":
                    "0xC7040bEeC1A3794C3e7CC9bA5C68070SIS0b4c29"
            },
            "node_difuhbguidf": {
                "id": "node_difuhbguidf",
                "parent_id": "chain_name_okjhfghuhsiduiusdh",
                "name": "bsc_sentry_4",
                "node_prometheus_urls": "test_url1,test_url2",
                "monitor_prometheus": "false",
                "monitor_contracts": "false",
                "monitor_node": "false",
                "ethereum_addresses":
                    "0xC7040bEeC1A3794C3e7CC9bA5C68070BRO0b4c29"
            },
        }

        self.evm_nodes_config = {
            "node_4e0a5189-f474-4120-a0a4-d5ab817c0504": {
                "id": "node_4e9eeacf-c98f-4207-81ec-7d5cb7a1ff7a",
                "parent_id": "chain_name_2be935b4-1072-469c-a5ff-1495f032fefa",
                "name": "evm_node_1",
                "node_http_url": "test_url",
                "monitor_node": "true"
            },
            "node_48ebf267-9b53-4aa1-9c45-e84a9cba5fbc": {
                "id": "node_48ebf267-9b53-4aa1-9c45-e84a9cba5fbc",
                "parent_id": "chain_name_2be935b4-1072-469c-a5ff-1495f032fefa",
                "name": "evm_node_2",
                "node_http_url": "test_url",
                "monitor_node": "false"
            }
        }

        self.github_repos_config_1 = {
            "repo_4ea76d87-d291-4b68-88af-da2bd1e16e2e": {
                "id": "repo_4ea76d87-d291-4b68-88af-da2bd1e16e2e",
                "parent_id": "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548",
                "repo_name": "tendermint/tendermint/",
                "monitor_repo": "true"
            },
            "repo_83713022-4155-420b-ada1-73a863f58282": {
                "id": "repo_83713022-4155-420b-ada1-73a863f58282",
                "parent_id": "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548",
                "repo_name": "SimplyVC/panic_cosmos/",
                "monitor_repo": "false"
            }
        }

        self.github_repos_config_2 = {
            "repo_sd978fgt789sdfg78g334th87fg": {
                "id": "repo_sd978fgt789sdfg78g334th87fg",
                "parent_id": "GENERAL",
                "repo_name": "SimplyVC/panic_polkadot/",
                "monitor_repo": "true"
            },
            "repo_S789G7S9DGS97G": {
                "id": "repo_S789G7S9DGS97G",
                "parent_id": "GENERAL",
                "repo_name": "SimplyVC/panic_cosmos/",
                "monitor_repo": "false"
            }
        }

        self.alerts_config_1 = {
            "1": {
                "name": "open_file_descriptors",
                "enabled": "true",
                "parent_id": "GENERAL",
                "critical_threshold": "95",
                "critical_repeat": "300",
                "critical_enabled": "true",
                "warning_threshold": "85",
                "warning_enabled": "true"
            },
            "2": {
                "name": "system_cpu_usage",
                "enabled": "true",
                "parent_id": "GENERAL",
                "critical_threshold": "95",
                "critical_repeat": "300",
                "critical_enabled": "true",
                "warning_threshold": "85",
                "warning_enabled": "true"
            },
            "3": {
                "name": "system_storage_usage",
                "enabled": "true",
                "parent_id": "GENERAL",
                "critical_threshold": "95",
                "critical_repeat": "300",
                "critical_enabled": "true",
                "warning_threshold": "85",
                "warning_enabled": "true"
            },
            "4": {
                "name": "system_ram_usage",
                "enabled": "true",
                "parent_id": "GENERAL",
                "critical_threshold": "95",
                "critical_repeat": "300",
                "critical_enabled": "true",
                "warning_threshold": "85",
                "warning_enabled": "true"
            },
            "5": {
                "name": "system_is_down",
                "enabled": "true",
                "parent_id": "GENERAL",
                "critical_threshold": "200",
                "critical_repeat": "300",
                "critical_enabled": "true",
                "warning_threshold": "0",
                "warning_enabled": "true"
            }
        }

        self.systems_config_1 = {
            "system_1d026af1-6cab-403d-8256-c8faa462930a": {
                "id": "system_1d026af1-6cab-403d-8256-c8faa462930a",
                "parent_id": "GENERAL",
                "name": "panic_system_1",
                "exporter_url": "test_url",
                "monitor_system": "true"
            },
            "system_a51b3a33-cb3f-4f53-a657-8a5a0efe0822": {
                "id": "system_a51b3a33-cb3f-4f53-a657-8a5a0efe0822",
                "parent_id": "GENERAL",
                "name": "panic_system_2",
                "exporter_url": "test_url",
                "monitor_system": "false"
            }
        }

        self.systems_config_2 = {
            "system_098hfd90ghbsd98fgbs98rgf9": {
                "id": "system_098hfd90ghbsd98fgbs98rgf9",
                "parent_id": "chain_name_okjhfghuhsiduiusdh",
                "name": "matic_full_node_nl",
                "exporter_url": "test_url",
                "monitor_system": "true"
            },
            "system_9sd8gh927gtb94gb99e": {
                "id": "system_9sd8gh927gtb94gb99e",
                "parent_id": "chain_name_okjhfghuhsiduiusdh",
                "name": "matic_full_node_mt",
                "exporter_url": "test_url",
                "monitor_system": "false"
            }
        }

        self.telegram_config_1 = {
            "telegram_8431a28e-a2ce-4e9b-839c-299b62e3d5b9": {
                "id": "telegram_8431a28e-a2ce-4e9b-839c-299b62e3d5b9",
                "channel_name": "telegram_chat_1",
                "bot_token": "test_bot_token",
                "chat_id": "test_chat_id",
                "info": "true",
                "warning": "true",
                "critical": "true",
                "error": "true",
                "alerts": "false",
                "commands": "false",
                "parent_ids":
                    "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548,"
                    "chain_name_94aafe04-8287-463a-8416-0401852b3ca2,GENERAL",
                "parent_names": "cosmos,kusama,GENERAL"
            }
        }

        self.twilio_config_1 = {
            "twilio_a7016a6b-9394-4584-abe3-5a5c434b6b7c": {
                "id": "twilio_a7016a6b-9394-4584-abe3-5a5c434b6b7c",
                "channel_name": "twilio_caller_main",
                "account_sid": "test_account_sid",
                "auth_token": "test_auth_token",
                "twilio_phone_no": "test_phone_number",
                "twilio_phone_numbers_to_dial_valid":
                "test_phone_numbers_to_dial_valid",
                "parent_ids":
                    "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548,"
                    "chain_name_94aafe04-8287-463a-8416-0401852b3ca2,GENERAL",
                "parent_names": "cosmos,kusama,GENERAL"
            }
        }

        self.pagerduty_config_1 = {
            "pagerduty_4092d0ed-ac45-462b-b62a-89cffd4833cc": {
                "id": "pagerduty_4092d0ed-ac45-462b-b62a-89cffd4833cc",
                "channel_name": "pager_duty_1",
                "api_token": "test_api_token",
                "integration_key": "test_integration_key",
                "info": "true",
                "warning": "true",
                "critical": "true",
                "error": "true",
                "parent_ids":
                    "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548,"
                    "chain_name_94aafe04-8287-463a-8416-0401852b3ca2,GENERAL",
                "parent_names": "cosmos,kusama,GENERAL"
            }
        }

        self.opsgenie_config_1 = {
            "opsgenie_9550bee1-5880-41f6-bdcf-a289472d7c35": {
                "id": "opsgenie_9550bee1-5880-41f6-bdcf-a289472d7c35",
                "channel_name": "ops_genie_main",
                "api_token": "test_api_token",
                "eu": "true",
                "info": "true",
                "warning": "true",
                "critical": "true",
                "error": "true",
                "parent_ids":
                    "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548,"
                    "chain_name_94aafe04-8287-463a-8416-0401852b3ca2,GENERAL",
                "parent_names": "cosmos,kusama,GENERAL"
            }
        }

        self.email_config_1 = {
            "email_01b23d79-10f5-4815-a11f-034f53974b23": {
                "id": "email_01b23d79-10f5-4815-a11f-034f53974b23",
                "channel_name": "main_email_channel",
                "port": "test_port",
                "smtp": "test_smtp",
                "email_from": "test_email_from",
                "emails_to": "test_email_to",
                "info": "true",
                "warning": "true",
                "critical": "true",
                "error": "true",
                "parent_ids":
                    "chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548,"
                    "chain_name_94aafe04-8287-463a-8416-0401852b3ca2,GENERAL",
                "parent_names": "cosmos,kusama,GENERAL"
            }
        }

        self.expected_data_nodes_1 = {
            'cosmos': {
                'monitored': {
                    'systems': [
                        {
                            'node_3e0a5189-f474-4120-a0a4-d5ab817c0504':
                                'cosmos_sentry_1'
                        },
                        {
                            'node_f8ebf267-9b53-4aa1-9c45-e84a9cba5fbc':
                                'cosmos_sentry_2'
                        }
                    ]
                },
                'not_monitored': {
                    'systems': []
                },
                'parent_id': 'chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548'
            }
        }

        self.expected_data_nodes_2 = {
            'bsc': {
                'monitored': {
                    'nodes': [
                        {
                            "node_sgdfh4y5u56u56j": "bsc_sentry_1"
                        },
                    ]
                },
                'not_monitored': {
                    'nodes': [
                        {
                            "node_dfouihgdfuoghdfuudfh": "bsc_sentry_2",
                        },
                        {
                            "node_mkdfkghhnusd": "bsc_sentry_3",
                        },
                        {
                            "node_difuhbguidf": "bsc_sentry_4",
                        },
                    ]
                },
                "parent_id": "chain_name_okjhfghuhsiduiusdh"
            }
        }

        self.expected_data_evm_nodes = {
            'bsc': {
                'monitored': {
                    'evm_nodes': [
                        {
                            "node_4e9eeacf-c98f-4207-81ec-7d5cb7a1ff7a":
                                "evm_node_1"
                        },
                    ]
                },
                'not_monitored': {
                    'evm_nodes': [
                        {
                            "node_48ebf267-9b53-4aa1-9c45-e84a9cba5fbc":
                                "evm_node_2",
                        },
                    ]
                },
                "parent_id": "chain_name_2be935b4-1072-469c-a5ff-1495f032fefa"
            }
        }

        self.expected_data_repos_1 = {
            'cosmos': {
                'monitored': {
                    'github_repos': [
                        {
                            'repo_4ea76d87-d291-4b68-88af-da2bd1e16e2e':
                                'tendermint/tendermint/'
                        },
                    ]
                },
                'not_monitored': {
                    'github_repos': [
                        {
                            'repo_83713022-4155-420b-ada1-73a863f58282':
                                'SimplyVC/panic_cosmos/'
                        }
                    ]
                },
                'parent_id': 'chain_name_7f4bc842-21b1-4bcb-8ab9-d86e08149548'
            }
        }

        self.expected_data_repos_2 = {
            'general': {
                'monitored': {
                    'github_repos': [
                        {
                            "repo_sd978fgt789sdfg78g334th87fg":
                                'SimplyVC/panic_polkadot/'
                        },
                    ]
                },
                'not_monitored': {
                    'github_repos': [
                        {
                            'repo_S789G7S9DGS97G': 'SimplyVC/panic_cosmos/'
                        }
                    ]
                },
                "parent_id": "GENERAL"
            }
        }

        self.expected_data_systems_1 = {
            'general': {
                'monitored': {
                    'systems': [
                        {
                            'system_1d026af1-6cab-403d-8256-c8faa462930a':
                                'panic_system_1'
                        },
                    ]
                },
                'not_monitored': {
                    'systems': [
                        {
                            'system_a51b3a33-cb3f-4f53-a657-8a5a0efe0822':
                                'panic_system_2'
                        },
                    ]
                },
                "parent_id": "GENERAL"
            }
        }

        self.expected_data_systems_2 = {
            'bsc': {
                'monitored': {
                    'systems': [
                        {
                            'system_098hfd90ghbsd98fgbs98rgf9':
                                'matic_full_node_nl'
                        },
                    ]
                },
                'not_monitored': {
                    'systems': [
                        {
                            'system_9sd8gh927gtb94gb99e':
                                'matic_full_node_mt'
                        },
                    ]
                },
                "parent_id": "chain_name_okjhfghuhsiduiusdh"
            }
        }

        self.config_data_unexpected = {
            "unexpected": {}
        }

    def tearDown(self) -> None:
        connect_to_rabbit(self.rabbitmq)
        delete_queue_if_exists(self.rabbitmq, CONFIGS_STORE_INPUT_QUEUE_NAME)
        delete_exchange_if_exists(self.rabbitmq, CONFIG_EXCHANGE)
        delete_exchange_if_exists(self.rabbitmq, HEALTH_CHECK_EXCHANGE)
        disconnect_from_rabbit(self.rabbitmq)

        connect_to_rabbit(self.test_rabbit_manager)
        delete_queue_if_exists(self.test_rabbit_manager, self.test_queue_name)
        disconnect_from_rabbit(self.test_rabbit_manager)

        self.redis.delete_all_unsafe()
        self.redis = None
        self.dummy_logger = None
        self.connection_check_time_interval = None
        self.rabbitmq = None
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

    def test_redis_property_returns_redis_correctly(self) -> None:
        self.assertEqual(type(self.redis), type(self.test_store.redis))

    def test_mongo_property_returns_none_when_mongo_not_init(self) -> None:
        self.assertEqual(None, self.test_store.mongo)

    def test_initialise_rabbitmq_initialises_everything_as_expected(
            self) -> None:
        # To make sure that the exchanges have not already been declared
        self.rabbitmq.connect()
        self.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
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
            CONFIG_EXCHANGE, passive=True)
        self.test_store.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE,
                                                  passive=True)

        # Check whether the queue has been creating by sending messages with the
        # same routing key. If this fails an exception is raised, hence the test
        # fails.
        self.test_store.rabbitmq.basic_publish_confirm(
            exchange=CONFIG_EXCHANGE,
            routing_key=CONFIGS_STORE_INPUT_ROUTING_KEY,
            body=self.test_data_str, is_body_dict=False,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=False)

        # Re-declare queue to get the number of messages
        res = self.test_store.rabbitmq.queue_declare(
            CONFIGS_STORE_INPUT_QUEUE_NAME, False, True, False, False)

        self.assertEqual(1, res.method.message_count)

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1"),
        ("self.nodes_config_2", "self.routing_key_12",),
        ("self.alerts_config_1", "self.routing_key_2"),
        ("self.alerts_config_1", "self.routing_key_5"),
        ("self.alerts_config_1", "self.routing_key_13"),
        ("self.evm_nodes_config", "self.routing_key_16"),
        ("self.github_repos_config_1", "self.routing_key_3"),
        ("self.github_repos_config_2", "self.routing_key_4"),
        ("self.systems_config_1", "self.routing_key_6"),
        ("self.systems_config_2", "self.routing_key_15",),
        ("self.email_config_1", "self.routing_key_7"),
        ("self.pagerduty_config_1", "self.routing_key_8"),
        ("self.opsgenie_config_1", "self.routing_key_9"),
        ("self.telegram_config_1", "self.routing_key_10"),
        ("self.twilio_config_1", "self.routing_key_11"),
    ])
    @mock.patch(
        "src.data_store.stores.config.ConfigStore"
        "._process_redis_store_chain_monitorables",
        autospec=True)
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_saves_in_redis(
            self, mock_config_data, mock_routing_key, mock_send_hb, mock_ack,
            mock_store_chain) -> None:
        self.rabbitmq.connect()
        mock_ack.return_value = None
        data = eval(mock_config_data)
        routing_key = eval(mock_routing_key)

        self.test_store._initialise_rabbitmq()

        blocking_channel = self.test_store.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(
            routing_key=eval(mock_routing_key))

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(blocking_channel, method_chains,
                                      properties, json.dumps(data))
        mock_ack.assert_called_once()
        mock_send_hb.assert_called_once()

        self.assertEqual(data, json.loads(
            self.redis.get(Keys.get_config(routing_key)).decode("utf-8")))
        mock_store_chain.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch(
        "src.data_store.stores.config.ConfigStore"
        "._process_redis_store_chain_monitorables",
        autospec=True)
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.config.ConfigStore._process_redis_store",
                autospec=True)
    def test_process_data_sends_heartbeat_correctly(
            self, mock_process_redis_store, mock_basic_ack, mock_store_chains
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
                                      json.dumps(self.nodes_config_1))

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
        mock_process_redis_store.assert_called_once()
        mock_store_chains.assert_called_once()

    @mock.patch(
        "src.data_store.stores.config.ConfigStore"
        "._process_redis_store_chain_monitorables",
        autospec=True)
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    def test_process_data_doesnt_send_heartbeat_on_processing_error(
            self, mock_basic_ack, mock_store_chain) -> None:
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
                                      json.dumps(self.nodes_config_1))

        res = self.test_rabbit_manager.queue_declare(
            queue=self.test_queue_name, durable=True, exclusive=False,
            auto_delete=False, passive=True
        )
        self.assertEqual(0, res.method.message_count)
        # This isn't called as processing error occurs before this call
        mock_store_chain.assert_not_called()

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1"),
        ("self.nodes_config_2", "self.routing_key_12",),
        ("self.alerts_config_1", "self.routing_key_2"),
        ("self.alerts_config_1", "self.routing_key_5"),
        ("self.alerts_config_1", "self.routing_key_13"),
        ("self.evm_nodes_config", "self.routing_key_16"),
        ("self.github_repos_config_1", "self.routing_key_3"),
        ("self.github_repos_config_2", "self.routing_key_4"),
        ("self.systems_config_1", "self.routing_key_6"),
        ("self.systems_config_2", "self.routing_key_15",),
        ("self.email_config_1", "self.routing_key_7"),
        ("self.pagerduty_config_1", "self.routing_key_8"),
        ("self.opsgenie_config_1", "self.routing_key_9"),
        ("self.telegram_config_1", "self.routing_key_10"),
        ("self.twilio_config_1", "self.routing_key_11"),
    ])
    @mock.patch(
        "src.data_store.stores.config.ConfigStore"
        "._process_redis_store_chain_monitorables",
        autospec=True)
    @mock.patch("src.data_store.stores.store.RabbitMQApi.basic_ack",
                autospec=True)
    @mock.patch("src.data_store.stores.store.Store._send_heartbeat",
                autospec=True)
    def test_process_data_saves_in_redis_then_removes_it_on_empty_config(
            self, mock_config_data, mock_routing_key, mock_send_hb,
            mock_ack, mock_store_chain) -> None:
        self.rabbitmq.connect()
        mock_ack.return_value = None
        data = eval(mock_config_data)
        routing_key = eval(mock_routing_key)

        self.test_store._initialise_rabbitmq()

        blocking_channel = self.test_store.rabbitmq.channel
        method_chains = pika.spec.Basic.Deliver(routing_key=routing_key)

        properties = pika.spec.BasicProperties()
        self.test_store._process_data(blocking_channel, method_chains,
                                      properties, json.dumps(data))
        mock_ack.assert_called_once()
        mock_send_hb.assert_called_once()

        self.assertEqual(data, json.loads(
            self.redis.get(Keys.get_config(routing_key)).decode("utf-8")))

        self.test_store._process_data(blocking_channel, method_chains,
                                      properties, json.dumps({}))

        self.assertEqual(None, self.redis.get(Keys.get_config(routing_key)))
        self.assertEqual(2, mock_store_chain.call_count)

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1"),
        ("self.nodes_config_2", "self.routing_key_12",),
        ("self.evm_nodes_config", "self.routing_key_16"),
        ("self.github_repos_config_1", "self.routing_key_3"),
        ("self.github_repos_config_2", "self.routing_key_4"),
        ("self.systems_config_1", "self.routing_key_6"),
        ("self.systems_config_2", "self.routing_key_15",),
    ])
    @mock.patch("src.data_store.stores.store.RedisApi.set",
                autospec=True)
    @mock.patch("src.data_store.stores.store.RedisApi.exists",
                autospec=True)
    def test_process_redis_store_chain_monitorables(
            self, mock_config_data, mock_routing_key, mock_exists, mock_set
    ) -> None:
        data_for_store = {}
        mock_exists.return_value = False

        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key), eval(mock_config_data))

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        # Process the data according to the config type
        data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_config_data), config_type_key, data_for_store,
            source_name)

        args, _ = mock_set.call_args
        self.assertEqual(args[1], Keys.get_base_chain_monitorables_info(
            redis_store_key))
        self.assertEqual(args[2], json.dumps(dict(data_for_store)))

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1"),
        ("self.nodes_config_2", "self.routing_key_12",),
        ("self.evm_nodes_config", "self.routing_key_16"),
        ("self.github_repos_config_1", "self.routing_key_3"),
        ("self.github_repos_config_2", "self.routing_key_4"),
        ("self.systems_config_1", "self.routing_key_6"),
        ("self.systems_config_2", "self.routing_key_15",),
    ])
    def test_process_redis_store_chain_monitorables_stores_in_redis_correctly(
            self, mock_config_data, mock_routing_key) -> None:
        data_for_store = {}

        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key), eval(mock_config_data))

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        # Process the data according to the config type
        data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_config_data), config_type_key, data_for_store,
            source_name)

        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(self.test_store.redis.get(
            Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
            'utf-8'), json.dumps(data_for_store))

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1"),
        ("self.nodes_config_2", "self.routing_key_12",),
        ("self.evm_nodes_config", "self.routing_key_16"),
        ("self.github_repos_config_1", "self.routing_key_3"),
        ("self.github_repos_config_2", "self.routing_key_4"),
        ("self.systems_config_1", "self.routing_key_6"),
        ("self.systems_config_2", "self.routing_key_15",),
    ])
    def test_process_redis_store_chain_monitorables_stores_in_redis_correctly_then_deletes(
            self, mock_config_data, mock_routing_key) -> None:
        data_for_store = {}
        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key), eval(mock_config_data))

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        # Process the data according to the config type
        data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_config_data), config_type_key, data_for_store,
            source_name)

        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(self.test_store.redis.get(
            Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
            'utf-8'),
            json.dumps(data_for_store))

        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key), {})

        self.assertFalse(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))

    @parameterized.expand([
        ("self.alerts_config_1", "self.routing_key_2"),
        ("self.alerts_config_1", "self.routing_key_5"),
        ("self.telegram_config_1", "self.routing_key_7"),
        ("self.twilio_config_1", "self.routing_key_8"),
        ("self.pagerduty_config_1", "self.routing_key_9"),
        ("self.opsgenie_config_1", "self.routing_key_10"),
        ("self.email_config_1", "self.routing_key_11"),
    ])
    @mock.patch("src.data_store.stores.store.RedisApi.set",
                autospec=True)
    @mock.patch("src.data_store.stores.store.RedisApi.exists",
                autospec=True)
    def test_process_redis_store_chain_monitorables_ignores_data_correctly(
            self, mock_config_data, mock_routing_key, mock_exists, mock_set
    ) -> None:
        mock_exists.return_value = False

        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key), eval(mock_config_data))

        mock_set.assert_not_called()

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1",
         "self.github_repos_config_2", "self.routing_key_4"),
        ("self.nodes_config_1", "self.routing_key_1",
         "self.systems_config_1", "self.routing_key_6"),
    ])
    def test_process_redis_store_chain_monitorables_stores_in_redis_correctly_does_not_modify_other_configs(
            self, mock_config_data, mock_routing_key, mock_config_data_2,
            mock_routing_key_2) -> None:
        data_for_store = {}

        # Store two things after each other and then verify that they are
        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key), eval(mock_config_data))
        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key_2), eval(mock_config_data_2))

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        # Process the data according to the config type
        data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_config_data), config_type_key, data_for_store,
            source_name)

        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(self.test_store.redis.get(
            Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
            'utf-8'),
            json.dumps(data_for_store))

        # Repeat the process with the second config to ensure data was saved
        # correctly
        data_for_store = {}

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key_2))

        # Process the data according to the config type
        data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_config_data_2), config_type_key, data_for_store,
            source_name)

        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(self.test_store.redis.get(
            Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
            'utf-8'),
            json.dumps(data_for_store))

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1",
         "self.github_repos_config_2", "self.routing_key_4"),
        ("self.nodes_config_1", "self.routing_key_1",
         "self.systems_config_1", "self.routing_key_6"),
    ])
    def test_process_redis_store_chain_monitorables_stores_in_redis_correctly_does_not_modify_other_configs(
            self, mock_config_data, mock_routing_key, mock_config_data_2,
            mock_routing_key_2) -> None:
        data_for_store = {}

        # Store two things after each other and then verify that they are
        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key), eval(mock_config_data))
        self.test_store._process_redis_store_chain_monitorables(
            eval(mock_routing_key_2), eval(mock_config_data_2))

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        # Process the data according to the config type
        data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_config_data), config_type_key, data_for_store,
            source_name)

        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(self.test_store.redis.get(
            Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
            'utf-8'),
            json.dumps(data_for_store))

        # Repeat the process with the second config to ensure data was saved
        # correctly
        data_for_store = {}

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key_2))

        # Process the data according to the config type
        data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_config_data_2), config_type_key, data_for_store,
            source_name)

        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(self.test_store.redis.get(
            Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
            'utf-8'),
            json.dumps(data_for_store))

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1",
         "self.expected_data_nodes_1", "chains.cosmos.dummy.nodes_config"),
        ("self.nodes_config_2", "self.routing_key_12",
         "self.expected_data_nodes_2", "chains.chainlink.dummy.nodes_config"),
        ("self.evm_nodes_config", "self.routing_key_16",
         "self.expected_data_evm_nodes",
         "chains.chainlink.dummy.evm_nodes_config"),
        ("self.github_repos_config_1", "self.routing_key_3",
         "self.expected_data_repos_1",
         "chains.cosmos.dummy.github_repos_config"),
        ("self.systems_config_2", "self.routing_key_15",
         "self.expected_data_systems_2",
         "chains.chainlink.dummy.systems_config")
    ])
    def test_process_redis_store_chain_monitorables_removes_correct_data_from_redis(
            self, config, config_routing_key, expected_config_data,
            dummy_chain_routing_key) -> None:
        # In this test we will assume that there are multiple chain data for the
        # same base chain. The other case for a single base chain is covered by
        # other tests
        self.test_store._process_redis_store_chain_monitorables(
            eval(config_routing_key), eval(config))
        self.test_store._process_redis_store_chain_monitorables(
            dummy_chain_routing_key, eval(config))

        # Check that all data has been stored before performing the test
        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(config_routing_key))
        expected_stored_data = copy.deepcopy(eval(expected_config_data))
        expected_stored_data['dummy'] = expected_stored_data[source_name]
        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(expected_stored_data, json.loads(
            self.test_store.redis.get(
                Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
                'utf-8')))

        # Remove the dummy data
        self.test_store._process_redis_store_chain_monitorables(
            dummy_chain_routing_key, {})
        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(eval(expected_config_data), json.loads(
            self.test_store.redis.get(
                Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
                'utf-8')))

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1",
         "self.expected_data_nodes_1", "chains.cosmos.dummy.nodes_config"),
        ("self.nodes_config_2", "self.routing_key_12",
         "self.expected_data_nodes_2", "chains.chainlink.dummy.nodes_config"),
        ("self.evm_nodes_config", "self.routing_key_16",
         "self.expected_data_evm_nodes",
         "chains.chainlink.dummy.evm_nodes_config"),
        ("self.github_repos_config_1", "self.routing_key_3",
         "self.expected_data_repos_1",
         "chains.cosmos.dummy.github_repos_config"),
        ("self.systems_config_2", "self.routing_key_15",
         "self.expected_data_systems_2",
         "chains.chainlink.dummy.systems_config")
    ])
    def test_process_redis_store_chain_monitorables_if_no_data_for_routing_key(
            self, config, config_routing_key, expected_config_data,
            dummy_chain_routing_key) -> None:
        # In this test we will send an empty config for a routing key whose data
        # is not yet saved in redis.
        self.test_store._process_redis_store_chain_monitorables(
            eval(config_routing_key), eval(config))

        # Check that all data has been stored before performing the test
        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(config_routing_key))
        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(eval(expected_config_data), json.loads(
            self.test_store.redis.get(
                Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
                'utf-8')))

        # Send empty config
        self.test_store._process_redis_store_chain_monitorables(
            dummy_chain_routing_key, {})
        self.assertTrue(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))
        self.assertEqual(eval(expected_config_data), json.loads(
            self.test_store.redis.get(
                Keys.get_base_chain_monitorables_info(redis_store_key)).decode(
                'utf-8')))

    @parameterized.expand([
        ("self.routing_key_1",),
        ("self.routing_key_12",),
        ("self.routing_key_3",),
        ("self.routing_key_15",)
    ])
    def test_process_redis_store_chain_monitorables_if_only_empty_confs_sent(
            self, config_routing_key, ) -> None:
        # In this test we will send only empty configs to check the data stored
        # in redis if no configs are stored.
        self.test_store._process_redis_store_chain_monitorables(
            eval(config_routing_key), {})

        # Check that all data has been stored before performing the test
        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(config_routing_key))
        self.assertFalse(self.test_store.redis.exists(
            Keys.get_base_chain_monitorables_info(redis_store_key)))

    @parameterized.expand([
        ("self.routing_key_1", "cosmos", "cosmos", "cosmos_nodes_config"),
        ("self.routing_key_2", "cosmos", "cosmos", ""),
        ("self.routing_key_3", "cosmos", "cosmos", "github_repos_config"),
        ("self.routing_key_4", "general", "general", "github_repos_config"),
        ("self.routing_key_5", "general", "general", ""),
        ("self.routing_key_6", "general", "general", "systems_config"),
        ("self.routing_key_7", "", "", ""),
        ("self.routing_key_8", "", "", ""),
        ("self.routing_key_9", "", "", ""),
        ("self.routing_key_10", "", "", ""),
        ("self.routing_key_11", "", "", ""),
        ("self.routing_key_12", "chainlink", "bsc", "chainlink_nodes_config"),
        ("self.routing_key_13", "chainlink", "bsc", ""),
        ("self.routing_key_14", "chainlink", "bsc", "github_repos_config"),
        ("self.routing_key_15", "chainlink", "bsc", "systems_config"),
    ])
    def test_process_routing_key_processes_routing_key_correctly(
            self, mock_routing_key, mock_redis_store_key,
            mock_source_name, mock_config_type_key) -> None:
        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        self.assertEqual(redis_store_key, mock_redis_store_key)
        self.assertEqual(source_name, mock_source_name)
        self.assertEqual(config_type_key, mock_config_type_key)

    @parameterized.expand([
        ("self.nodes_config_1", "self.routing_key_1",
         "self.expected_data_nodes_1"),
        ("self.nodes_config_2", "self.routing_key_12",
         "self.expected_data_nodes_2"),
        ("self.evm_nodes_config", "self.routing_key_16",
         "self.expected_data_evm_nodes"),
        ("self.github_repos_config_1", "self.routing_key_3",
         "self.expected_data_repos_1"),
        ("self.github_repos_config_2", "self.routing_key_4",
         "self.expected_data_repos_2"),
        ("self.systems_config_1", "self.routing_key_6",
         "self.expected_data_systems_1"),
        ("self.systems_config_2", "self.routing_key_15",
         "self.expected_data_systems_2")
    ])
    def test_sort_monitorable_configs_sorts_data_correctly(
            self, mock_data, mock_routing_key, mock_expected_data) -> None:
        actual_data_for_store = defaultdict(dict)

        redis_store_key, source_name, config_type_key = \
            self.test_store._process_routing_key(eval(mock_routing_key))

        actual_data_for_store = self.test_store._sort_monitorable_configs(
            eval(mock_data), config_type_key, actual_data_for_store,
            source_name)
        self.assertEqual(actual_data_for_store, eval(mock_expected_data))
