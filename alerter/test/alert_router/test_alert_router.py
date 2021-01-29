import copy
import json
import logging
import unittest
from datetime import timedelta
from typing import Dict, Callable, Any
from unittest import mock
from unittest.mock import MagicMock

import configparser
import pika.exceptions
from parameterized import parameterized

from src.alert_router.alert_router import (AlertRouter,
                                           _ALERT_ROUTER_INPUT_QUEUE_NAME)
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (CONFIG_EXCHANGE, ALERT_EXCHANGE,
                                 STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 ALERT_ROUTER_CONFIGS_QUEUE_NAME)
from src.utils.exceptions import MissingKeyInConfigException


class TestAlertRouter(unittest.TestCase):
    def setUp(self) -> None:
        self._alert_router_logger = logging.getLogger('test_alert_router')
        self._rabbit_logger = logging.getLogger('test_rabbit')
        self._redis_logger = logging.getLogger('test_reids')
        self._connection_check_time_interval = timedelta(seconds=0)

        self._rabbit_ip = 'localhost'
        self._config_exchange = CONFIG_EXCHANGE
        self._alert_input_exchange = ALERT_EXCHANGE

        self._redis_ip = 'localhost'
        self._redis_db = 1
        self._redis_port = 6379

        self._rabbitmq = RabbitMQApi(
            self._rabbit_logger, self._rabbit_ip,
            connection_check_time_interval=self._connection_check_time_interval)

        self._redis = RedisApi(self._redis_logger, self._redis_db,
                               self._redis_ip, self._redis_port)

        self.CONFIG_ROUTING_KEY = "channels.test"
        self.TEST_CHANNEL_CONFIG_FILE = {
            'test_123': {
                'id': "test_123",
                'channel_name': "test_channel",
                'info': "false",
                'warning': "false",
                'critical': "false",
                'error': "false",
                'parent_ids': "GENERAL,",
                'parent_names': ""
            }
        }

        self.TEST_CHANNEL_CONFIG = {
            'test_123': {
                'id': "test_123",
                'info': False,
                'warning': False,
                'critical': False,
                'error': False,
                'parent_ids': ["GENERAL"],
            }
        }

        self._test_alert_router = AlertRouter(
            "Alert Router", self._alert_router_logger, self._rabbit_ip,
            self._redis_ip,
            self._redis_db, self._redis_port, "test_alerter", True, True
        )

    def tearDown(self) -> None:
        # flush and consume all from rabbit queues and exchanges
        self._rabbitmq.connect_till_successful()

        try:
            self._rabbitmq.queue_declare(ALERT_ROUTER_CONFIGS_QUEUE_NAME,
                                         passive=True)
            self._rabbitmq.queue_purge(ALERT_ROUTER_CONFIGS_QUEUE_NAME)
            self._rabbitmq.queue_delete(ALERT_ROUTER_CONFIGS_QUEUE_NAME)
        except pika.exceptions.ChannelClosedByBroker:
            print("Queue {} does not exist - don't need to close".format(
                ALERT_ROUTER_CONFIGS_QUEUE_NAME
            ))

        exchanges = [
            ALERT_EXCHANGE, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
            STORE_EXCHANGE
        ]

        for exchange in exchanges:
            try:
                self._rabbitmq.exchange_declare(exchange, passive=True)
                self._rabbitmq.channel.exchange_delete(exchange)
            except pika.exceptions.ChannelClosedByBroker:
                print("Exchange {} does not exist - don't need to close".format(
                    exchange))

        self._rabbitmq.disconnect_till_successful()

    def test_alert_router_initialised(self):
        self.assertIsNotNone(self._test_alert_router)

    def test_name(self):
        self.assertEqual("Alert Router", self._test_alert_router.name)

    @parameterized.expand([
        (ALERT_ROUTER_CONFIGS_QUEUE_NAME,),
        (_ALERT_ROUTER_INPUT_QUEUE_NAME,)
    ])
    def test__initialise_rabbit_initialises_queues(self, queue_to_check: str):
        # Testing this separately since this is a critical function
        self._test_alert_router._initialise_rabbit()

        try:
            self._rabbitmq.connect_till_successful()
            self._rabbitmq.queue_declare(queue_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Queue {} was not declared".format(queue_to_check))

    @parameterized.expand([
        (CONFIG_EXCHANGE,),
        (ALERT_EXCHANGE,),
        (HEALTH_CHECK_EXCHANGE,),
        (STORE_EXCHANGE,),
    ])
    def test__initialise_rabbit_initialises_exchanges(self,
                                                      exchange_to_check: str):
        # Testing this separately since this is a critical function
        self._test_alert_router._initialise_rabbit()

        try:
            self._rabbitmq.connect_till_successful()
            self._rabbitmq.exchange_declare(exchange_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Exchange {} was not declared".format(exchange_to_check))

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_first_consumed_and_processed(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        mock_ack.return_value = None
        mock_extract_config.return_value = self.TEST_CHANNEL_CONFIG['test_123']
        # Must create a connection so that the blocking channel is passed
        self._test_alert_router._initialise_rabbit()
        blocking_channel = self._test_alert_router._rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains = pika.spec.Basic.Deliver(
            routing_key=self.CONFIG_ROUTING_KEY)
        config_json = json.dumps(
            self.TEST_CHANNEL_CONFIG_FILE)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 config_json)

        expected_output = {
            self.CONFIG_ROUTING_KEY: copy.deepcopy(self.TEST_CHANNEL_CONFIG)
        }
        self.assertEqual(expected_output, self._test_alert_router._config)

        # Clean before test finishes
        self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_correct_update(self, mock_ack, mock_extract_config):
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        updated_config_file = {
            'test_123': {
                'id': "test_123",
                'channel_name': "test_channel",
                'info': "true",
                'warning': "true",
                'critical': "false",
                'error': "true",
                'parent_ids': "GENERAL,",
                'parent_names': ""
            }
        }

        updated_config = {
            'test_123': {
                'id': "test_123",
                'info': True,
                'warning': True,
                'critical': False,
                'error': True,
                'parent_ids': ["GENERAL"],
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'], updated_config['test_123']
        ]

        # Must create a connection so that the blocking channel is passed
        self._test_alert_router._initialise_rabbit()
        blocking_channel = self._test_alert_router._rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains = pika.spec.Basic.Deliver(
            routing_key=self.CONFIG_ROUTING_KEY)
        config_json = json.dumps(
            self.TEST_CHANNEL_CONFIG_FILE)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 config_json)

        updated_config_json = json.dumps(updated_config_file)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 updated_config_json)

        expected_output = {
            self.CONFIG_ROUTING_KEY: copy.deepcopy(updated_config)
        }

        self.assertEqual(expected_output, self._test_alert_router._config)

        # Clean before test finishes
        self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_incorrect_update_reverted(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        # Incorrect config file has missing fields - it doesn't matter what
        # this is for the purpose of this test as the extraction is being
        # mocked
        updated_incorrect_config_file = {
            'test_123': {
                'id': "test_123",
                'channel_name': "test_channel",
                'critical': "false",
                'error': "true",
                'parent_ids': "GENERAL,",
                'parent_names': ""
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'],
            MissingKeyInConfigException("critical", "channel.test_123")
        ]

        # Must create a connection so that the blocking channel is passed
        self._test_alert_router._initialise_rabbit()
        blocking_channel = self._test_alert_router._rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains = pika.spec.Basic.Deliver(
            routing_key=self.CONFIG_ROUTING_KEY)
        config_json = json.dumps(
            self.TEST_CHANNEL_CONFIG_FILE)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 config_json)

        updated_config_json = json.dumps(updated_incorrect_config_file)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 updated_config_json)

        expected_output = {
            self.CONFIG_ROUTING_KEY: copy.deepcopy(self.TEST_CHANNEL_CONFIG)
        }

        self.assertEqual(expected_output, self._test_alert_router._config)

        # Clean before test finishes
        self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_exception_reverted(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        # Incorrect config file has missing fields - it doesn't matter what
        # this is for the purpose of this test as the extraction is being
        # mocked
        updated_incorrect_config_file = {
            'test_123': {
                'id': "test_123",
                'channel_name': "test_channel",
                'critical': "false",
                'error': "true",
                'parent_ids': "GENERAL,",
                'parent_names': ""
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'],
            Exception("This is a random exception")
        ]

        # Must create a connection so that the blocking channel is passed
        self._test_alert_router._initialise_rabbit()
        blocking_channel = self._test_alert_router._rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains = pika.spec.Basic.Deliver(
            routing_key=self.CONFIG_ROUTING_KEY)
        config_json = json.dumps(
            self.TEST_CHANNEL_CONFIG_FILE)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 config_json)

        updated_config_json = json.dumps(updated_incorrect_config_file)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 updated_config_json)

        expected_output = {
            self.CONFIG_ROUTING_KEY: copy.deepcopy(self.TEST_CHANNEL_CONFIG)
        }

        self.assertEqual(expected_output, self._test_alert_router._config)

        # Clean before test finishes
        self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_multiple_channel_configs_correct(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        # Incorrect config file has missing fields
        second_correct_config_file = {
            'test_234': {
                'id': "test_234",
                'channel_name': "test_channel",
                'info': "true",
                'warning': "false",
                'critical': "true",
                'error': "true",
                'parent_ids': "GENERAL,",
                'parent_names': ""
            }
        }

        second_correct_config = {
            'test_234': {
                'id': "test_234",
                'info': True,
                'warning': False,
                'critical': True,
                'error': True,
                'parent_ids': "GENERAL,",
            }
        }

        second_routing_key = "channel.test2"

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'],
            second_correct_config['test_234']
        ]

        # Must create a connection so that the blocking channel is passed
        self._test_alert_router._initialise_rabbit()
        blocking_channel = self._test_alert_router._rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains1 = pika.spec.Basic.Deliver(
            routing_key=self.CONFIG_ROUTING_KEY)

        method_chains2 = pika.spec.Basic.Deliver(routing_key=second_routing_key)

        config_json = json.dumps(
            self.TEST_CHANNEL_CONFIG_FILE)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains1,
                                                 properties,
                                                 config_json)

        second_config_json = json.dumps(second_correct_config_file)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains2,
                                                 properties,
                                                 second_config_json)

        expected_output = {
            self.CONFIG_ROUTING_KEY: copy.deepcopy(self.TEST_CHANNEL_CONFIG),
            second_routing_key: copy.deepcopy(second_correct_config)
        }

        self.assertEqual(expected_output, self._test_alert_router._config)

        # Clean before test finishes
        self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config", autospec=True)
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_multiple_channel_single_config_correct(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        def generate_extract_config_mocker(config: Dict[str, Dict[str, Any]]
                                           ) -> Callable[..., Dict[str, Any]]:
            def extract_config_mocker(
                    section, config_filename: str
            ) -> Dict[str, str]:
                return config[section['id']]

            return extract_config_mocker

        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        # Incorrect config file has missing fields
        config_file = {
            **self.TEST_CHANNEL_CONFIG_FILE,
            'test_234': {
                'id': "test_234",
                'channel_name': "test_channel",
                'info': "true",
                'warning': "false",
                'critical': "true",
                'error': "true",
                'parent_ids': "GENERAL,",
                'parent_names': ""
            }
        }

        config = {
            **self.TEST_CHANNEL_CONFIG,
            'test_234': {
                'id': "test_234",
                'info': True,
                'warning': False,
                'critical': True,
                'error': True,
                'parent_ids': "GENERAL,",
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = generate_extract_config_mocker(config)
        # Must create a connection so that the blocking channel is passed
        self._test_alert_router._initialise_rabbit()
        blocking_channel = self._test_alert_router._rabbitmq.channel

        # We will send new configs through both the existing and
        # non-existing chain and general paths to make sure that all routes
        # work as expected.
        method_chains = pika.spec.Basic.Deliver(
            routing_key=self.CONFIG_ROUTING_KEY)

        config_json = json.dumps(config_file)
        properties = pika.spec.BasicProperties()

        self._test_alert_router._process_configs(blocking_channel,
                                                 method_chains,
                                                 properties,
                                                 config_json)

        expected_output = {
            self.CONFIG_ROUTING_KEY: copy.deepcopy(config)
        }

        self.assertEqual(expected_output, self._test_alert_router._config)

        # Clean before test finishes
        self._test_alert_router.disconnect_from_rabbit()

    @parameterized.expand([
        (
                {'id': "test_123", 'channel_name': "test_channel",
                 'info': "false", 'warning': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,",
                 'parent_names': ""},
                "channel.test_123",
                {'id': "test_123", 'info': False, 'warning': False,
                 'critical': False, 'error': False, 'parent_ids': ["GENERAL"],
                 }
        ), (
                {'id': "test_123", 'channel_name': "test_channel",
                 'info': "on", 'warning': "off", 'critical': "yes",
                 'error': "no", 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.test_123",
                {'id': "test_123", 'info': True, 'warning': False,
                 'critical': True, 'error': False, 'parent_ids': ["GENERAL"],
                 }
        ), (
                {'id': "twilio_123", 'channel_name': "test_channel",
                 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.twilio_123",
                {'id': "twilio_123", 'info': False, 'warning': False,
                 'critical': True, 'error': False, 'parent_ids': ["GENERAL"],
                 }
        ), (
                {'id': "twilio_123", 'channel_name': "test_channel",
                 'info': "on", 'warning': "off", 'critical': "yes",
                 'error': "no",
                 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.twilio_123",
                {'id': "twilio_123", 'info': False, 'warning': False,
                 'critical': True, 'error': False, 'parent_ids': ["GENERAL"],
                 }
        )
    ])
    @mock.patch.object(AlertRouter, "validate_config_fields_existence")
    def test_extract_config_correct(
            self, config_file: Dict[str, str], config_filename: str,
            expected_config: Dict[str, Any],
            mock_validate_config_fields_existence: MagicMock):
        mock_validate_config_fields_existence.return_value = None
        config_to_test = configparser.ConfigParser()
        config_to_test.read_dict({'conf': config_file})
        self.assertEqual(
            expected_config,
            self._test_alert_router.extract_config(
                config_to_test['conf'], config_filename
            )
        )

    @mock.patch.object(AlertRouter, "validate_config_fields_existence")
    def test_extract_config_propagates_exception(
            self, mock_validate_config_fields_existence: MagicMock
    ):
        mock_validate_config_fields_existence.side_effect = \
            MissingKeyInConfigException("x", "y")
        config_to_test = configparser.ConfigParser()
        config_to_test.read_dict({})  # Config does not matter here
        self.assertRaises(MissingKeyInConfigException,
                          self._test_alert_router.extract_config,
                          config_to_test['DEFAULT'],
                          '')

    @parameterized.expand([
        (
                {'id': "test_123", 'channel_name': "test_channel",
                 'info': "false", 'warning': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,",
                 'parent_names': ""},
                "channel.test_123"
        ), (
                {'id': "test_123", 'channel_name': "test_channel",
                 'info': "on", 'warning': "off", 'critical': "yes",
                 'error': "no", 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.test_123"
        ), (
                {'id': "twilio_123", 'channel_name': "test_channel",
                 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.twilio_123"
        ), (
                {'id': "twilio_123", 'channel_name': "test_channel",
                 'info': "on", 'warning': "off", 'critical': "yes",
                 'error': "no",
                 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.twilio_123"
        )
    ])
    def test_validate_config_fields_existence_valid(
            self, config_dict: Dict[str, str], config_file_name: str
    ):
        config = configparser.ConfigParser()
        config.read_dict({'conf': config_dict})

        self.assertIsNone(
            self._test_alert_router.validate_config_fields_existence(
                config["conf"], config_file_name
            )
        )

    @parameterized.expand([
        (
                {'info': "false", 'warning': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id': "test_123", 'warning': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id': "test_123", 'info': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id': "test_123", 'info': "false", 'warning': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id': "test_123", 'info': "false", 'warning': "false",
                 'critical': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id': "test_123", 'info': "false", 'warning': "false",
                 'critical': "false", 'error': "false", },
                "channel.test_123"
        ), (
                {'channel_name': "test_channel", 'parent_ids': "GENERAL,"},
                "channel.twilio_123"
        ), (
                {'id': "twilio_123", 'channel_name': "test_channel"},
                "channel.twilio_123"
        )
    ])
    def test_validate_config_fields_existance_fail(
            self, config_dict: Dict[str, str], config_file_name: str
    ):
        config = configparser.ConfigParser()
        config.read_dict({'conf': config_dict})
        print(config_dict)

        self.assertRaises(
            MissingKeyInConfigException,
            self._test_alert_router.validate_config_fields_existence,
            config['conf'], config_file_name
        )

    @unittest.skip
    def test__process_alert(self):
        self.fail()

    @unittest.skip
    def test__process_ping(self):
        self.fail()

    @unittest.skip
    def test_start(self):
        self.fail()

    @unittest.skip
    def test_disconnect_from_rabbit(self):
        self.fail()

    @unittest.skip
    def test_on_terminate(self):
        self.fail()

    @unittest.skip
    def test_is_all_muted(self):
        self.fail()

    @unittest.skip
    def test_is_chain_severity_muted(self):
        self.fail()
