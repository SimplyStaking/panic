import configparser
import copy
import json
import logging
import unittest
from datetime import timedelta, datetime
from typing import Dict, Callable, Any
from unittest import mock
from unittest.mock import MagicMock

import pika.exceptions
from freezegun import freeze_time
from parameterized import parameterized

from src.alert_router.alert_router import (
    AlertRouter, _ALERT_ROUTER_INPUT_QUEUE_NAME, _HEARTBEAT_QUEUE_NAME
)
from src.alerter.alerts.alert import Alert
from src.data_store.redis import RedisApi, Keys
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (
    CONFIG_EXCHANGE, ALERT_EXCHANGE, STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
    ALERT_ROUTER_CONFIGS_QUEUE_NAME
)
from src.utils.exceptions import MissingKeyInConfigException
from test.test_utils import DummyAlertCode


class TestAlertRouter(unittest.TestCase):
    def setUp(self) -> None:
        self._alert_router_logger = logging.getLogger('test_alert_router')
        self._rabbit_logger = logging.getLogger('test_rabbit')
        self._redis_logger = logging.getLogger('test_redis')
        self._connection_check_time_interval = timedelta(seconds=0)

        self._rabbit_ip = env.RABBIT_IP
        self._config_exchange = CONFIG_EXCHANGE
        self._alert_input_exchange = ALERT_EXCHANGE

        self._redis_ip = env.REDIS_IP
        self._redis_db = 1
        self._redis_port = 6379

        self._rabbitmq = RabbitMQApi(
            self._rabbit_logger, self._rabbit_ip,
            connection_check_time_interval=self._connection_check_time_interval)

        self._redis = RedisApi(self._redis_logger, self._redis_db,
                               self._redis_ip, self._redis_port)

        self.CONFIG_ROUTING_KEY = "channels.test"
        self.ALERT_ROUTER_ROUTING_KEY = "alert_router.test"
        self.TEST_CHANNEL_CONFIG_FILE = {
            'test_123': {
                'id':           "test_123",
                'channel_name': "test_channel",
                'info':         "false",
                'warning':      "false",
                'critical':     "false",
                'error':        "false",
                'parent_ids':   "GENERAL,",
                'parent_names': ""
            }
        }

        self.TEST_CHANNEL_CONFIG = {
            'test_123': {
                'id':         "test_123",
                'info':       False,
                'warning':    False,
                'critical':   False,
                'error':      False,
                'parent_ids': ["GENERAL"],
            }
        }
        self.ALERT_ROUTER_NAME = "Alert Router"
        self._test_alert_router = AlertRouter(
            self.ALERT_ROUTER_NAME, self._alert_router_logger, self._rabbit_ip,
            self._redis_ip, self._redis_db, self._redis_port, "test_alerter",
            True, True
        )

    def connect_to_rabbit(self, attempts: int = 3) -> None:
        tries = 0

        while tries < attempts:
            try:
                self._rabbitmq.connect()
                return
            except Exception as e:
                tries += 1
                print("Could not connect to rabbit. Attempts so far: {}".format(
                    tries))
                print(e)
                if tries >= attempts:
                    raise e

    def disconnect_from_rabbit(self, attempts: int = 3) -> None:
        tries = 0

        while tries < attempts:
            try:
                self._rabbitmq.disconnect()
                return
            except Exception as e:
                tries += 1
                print("Could not connect to rabbit. Attempts so far: {}".format(
                    tries))
                print(e)
                if tries >= attempts:
                    raise e

    def delete_queue_if_exists(self, queue_name: str) -> None:
        try:
            self._rabbitmq.queue_declare(queue_name, passive=True)
            self._rabbitmq.queue_purge(queue_name)
            self._rabbitmq.queue_delete(queue_name)
        except pika.exceptions.ChannelClosedByBroker:
            print("Queue {} does not exist - don't need to close".format(
                queue_name
            ))

    def delete_exchange_if_exists(self, exchange_name: str) -> None:
        try:
            self._rabbitmq.exchange_declare(exchange_name, passive=True)
            self._rabbitmq.exchange_delete(exchange_name)
        except pika.exceptions.ChannelClosedByBroker:
            print("Exchange {} does not exist - don't need to close".format(
                exchange_name))

    def tearDown(self) -> None:
        # flush and consume all from rabbit queues and exchanges
        queues = [ALERT_ROUTER_CONFIGS_QUEUE_NAME,
                  _ALERT_ROUTER_INPUT_QUEUE_NAME, _HEARTBEAT_QUEUE_NAME]
        for queue in queues:
            self.connect_to_rabbit()
            self.delete_queue_if_exists(queue)

        exchanges = [
            ALERT_EXCHANGE, CONFIG_EXCHANGE, HEALTH_CHECK_EXCHANGE,
            STORE_EXCHANGE
        ]

        for exchange in exchanges:
            self.delete_exchange_if_exists(exchange)

        self.disconnect_from_rabbit()

    def test_alert_router_initialised(self):
        self.assertIsNotNone(self._test_alert_router)

    def test_str(self):
        self.assertEqual(self.ALERT_ROUTER_NAME, str(self._test_alert_router))

    def test_name(self):
        self.assertEqual(self.ALERT_ROUTER_NAME, self._test_alert_router.name)

    @parameterized.expand([
        (ALERT_ROUTER_CONFIGS_QUEUE_NAME,),
        (_ALERT_ROUTER_INPUT_QUEUE_NAME,),
        (_HEARTBEAT_QUEUE_NAME,)
    ])
    @mock.patch.object(RabbitMQApi, "confirm_delivery")
    @mock.patch.object(RabbitMQApi, "basic_consume")
    def test__initialise_rabbit_initialises_queues(
            self, queue_to_check: str, mock_basic_consume: MagicMock,
            mock_confirm_delivery: MagicMock
    ):
        mock_basic_consume.return_value = None
        mock_confirm_delivery.return_value = None
        try:
            self.connect_to_rabbit()

            # Testing this separately since this is a critical function
            self._test_alert_router._initialise_rabbitmq()

            mock_basic_consume.assert_called()
            mock_confirm_delivery.assert_called()

            self._rabbitmq.queue_declare(queue_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Queue {} was not declared".format(queue_to_check))
        finally:
            self.disconnect_from_rabbit()

    @parameterized.expand([
        (CONFIG_EXCHANGE,),
        (ALERT_EXCHANGE,),
        (HEALTH_CHECK_EXCHANGE,),
        (STORE_EXCHANGE,),
    ])
    @mock.patch.object(RabbitMQApi, "confirm_delivery")
    @mock.patch.object(RabbitMQApi, "basic_consume")
    def test__initialise_rabbit_initialises_exchanges(
            self, exchange_to_check: str, mock_basic_consume: MagicMock,
            mock_confirm_delivery: MagicMock
    ):
        mock_basic_consume.return_value = None
        mock_confirm_delivery.return_value = None

        try:
            self.connect_to_rabbit()

            # Testing this separately since this is a critical function
            self._test_alert_router._initialise_rabbitmq()

            mock_basic_consume.assert_called()
            mock_confirm_delivery.assert_called()

            self._rabbitmq.exchange_declare(exchange_to_check, passive=True)
        except pika.exceptions.ConnectionClosedByBroker:
            self.fail("Exchange {} was not declared".format(exchange_to_check))
        finally:
            self.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_first_consumed_and_processed(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        try:
            self.connect_to_rabbit()
            self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False,
                                            True, False, False)

            mock_ack.return_value = None
            mock_extract_config.return_value = self.TEST_CHANNEL_CONFIG[
                'test_123']
            # Must create a connection so that the blocking channel is passed
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.CONFIG_ROUTING_KEY)
            config_json = json.dumps(
                self.TEST_CHANNEL_CONFIG_FILE)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties, config_json
            )

            expected_output = {
                self.CONFIG_ROUTING_KEY: copy.deepcopy(self.TEST_CHANNEL_CONFIG)
            }
            self.assertDictEqual(
                expected_output, self._test_alert_router._config
            )
        finally:
            # Clean before test finishes
            self.delete_exchange_if_exists(CONFIG_EXCHANGE)
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_correct_update(self, mock_ack, mock_extract_config):
        updated_config_file = {
            'test_123': {
                'id':           "test_123",
                'channel_name': "test_channel",
                'info':         "true",
                'warning':      "true",
                'critical':     "false",
                'error':        "true",
                'parent_ids':   "GENERAL,",
                'parent_names': ""
            }
        }

        updated_config = {
            'test_123': {
                'id':         "test_123",
                'info':       True,
                'warning':    True,
                'critical':   False,
                'error':      True,
                'parent_ids': ["GENERAL"],
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'], updated_config['test_123']
        ]

        try:
            self.connect_to_rabbit()
            self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False,
                                            True, False, False)
            # Must create a connection so that the blocking channel is passed
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.CONFIG_ROUTING_KEY)
            config_json = json.dumps(
                self.TEST_CHANNEL_CONFIG_FILE)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties, config_json
            )

            updated_config_json = json.dumps(updated_config_file)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties,
                updated_config_json
            )

            expected_output = {
                self.CONFIG_ROUTING_KEY: copy.deepcopy(updated_config)
            }

            self.assertDictEqual(
                expected_output, self._test_alert_router._config
            )
        finally:
            # Clean before test finishes
            self.delete_exchange_if_exists(CONFIG_EXCHANGE)
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_incorrect_update_reverted(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        # Incorrect config file has missing fields - it doesn't matter what
        # this is for the purpose of this test as the extraction is being
        # mocked
        updated_incorrect_config_file = {
            'test_123': {
                'id':           "test_123",
                'channel_name': "test_channel",
                'critical':     "false",
                'error':        "true",
                'parent_ids':   "GENERAL,",
                'parent_names': ""
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'],
            MissingKeyInConfigException("critical", "channel.test_123")
        ]

        try:
            self.connect_to_rabbit()
            self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False,
                                            True, False, False)

            # Must create a connection so that the blocking channel is passed
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.CONFIG_ROUTING_KEY)
            config_json = json.dumps(
                self.TEST_CHANNEL_CONFIG_FILE)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties, config_json
            )

            updated_config_json = json.dumps(updated_incorrect_config_file)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties,
                updated_config_json
            )

            expected_output = {
                self.CONFIG_ROUTING_KEY: copy.deepcopy(self.TEST_CHANNEL_CONFIG)
            }

            self.assertDictEqual(
                expected_output, self._test_alert_router._config
            )
        finally:
            # Clean before test finishes
            self.delete_exchange_if_exists(CONFIG_EXCHANGE)
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_exception_reverted(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        # Incorrect config file has missing fields - it doesn't matter what
        # this is for the purpose of this test as the extraction is being
        # mocked
        updated_incorrect_config_file = {
            'test_123': {
                'id':           "test_123",
                'channel_name': "test_channel",
                'critical':     "false",
                'error':        "true",
                'parent_ids':   "GENERAL,",
                'parent_names': ""
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'],
            Exception("This is a random exception")
        ]

        try:
            self.connect_to_rabbit()
            self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False,
                                            True, False, False)

            # Must create a connection so that the blocking channel is passed
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.CONFIG_ROUTING_KEY
            )
            config_json = json.dumps(self.TEST_CHANNEL_CONFIG_FILE)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties, config_json
            )

            updated_config_json = json.dumps(updated_incorrect_config_file)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties,
                updated_config_json
            )

            expected_output = {
                self.CONFIG_ROUTING_KEY: copy.deepcopy(self.TEST_CHANNEL_CONFIG)
            }

            self.assertDictEqual(
                expected_output, self._test_alert_router._config
            )
        finally:
            # Clean before test finishes
            self.delete_exchange_if_exists(CONFIG_EXCHANGE)
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config")
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_multiple_channel_configs_correct(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        second_correct_config_file = {
            'test_234': {
                'id':           "test_234",
                'channel_name': "test_channel",
                'info':         "true",
                'warning':      "false",
                'critical':     "true",
                'error':        "true",
                'parent_ids':   "GENERAL,",
                'parent_names': ""
            }
        }

        second_correct_config = {
            'test_234': {
                'id':         "test_234",
                'info':       True,
                'warning':    False,
                'critical':   True,
                'error':      True,
                'parent_ids': ["GENERAL"],
            }
        }

        second_routing_key = "channel.test2"

        mock_ack.return_value = None
        mock_extract_config.side_effect = [
            self.TEST_CHANNEL_CONFIG['test_123'],
            second_correct_config['test_234']
        ]

        try:
            self.connect_to_rabbit()
            self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False,
                                            True, False, False)
            # Must create a connection so that the blocking channel is passed
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains1 = pika.spec.Basic.Deliver(
                routing_key=self.CONFIG_ROUTING_KEY
            )

            method_chains2 = pika.spec.Basic.Deliver(
                routing_key=second_routing_key
            )

            config_json = json.dumps(self.TEST_CHANNEL_CONFIG_FILE)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains1, properties, config_json
            )

            second_config_json = json.dumps(second_correct_config_file)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains2, properties,
                second_config_json
            )

            expected_output = {
                second_routing_key:      copy.deepcopy(second_correct_config),
                self.CONFIG_ROUTING_KEY: copy.deepcopy(
                    self.TEST_CHANNEL_CONFIG
                ),
            }

            self.assertDictEqual(
                expected_output, self._test_alert_router._config
            )
        finally:
            # Clean before test finishes
            self.delete_exchange_if_exists(CONFIG_EXCHANGE)
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "extract_config", autospec=True)
    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_process_config_multiple_channel_single_config_correct(
            self, mock_ack: MagicMock, mock_extract_config: MagicMock
    ):
        def generate_extract_config_mocker(config: Dict[str, Dict[str, Any]]
                                           ) -> Callable[..., Dict[str, Any]]:
            def extract_config_mocker(section, _) -> Dict[str, str]:
                return config[section['id']]

            return extract_config_mocker

        # Incorrect config file has missing fields
        config_file = {
            **self.TEST_CHANNEL_CONFIG_FILE,
            'test_234': {
                'id':           "test_234",
                'channel_name': "test_channel",
                'info':         "true",
                'warning':      "false",
                'critical':     "true",
                'error':        "true",
                'parent_ids':   "GENERAL,",
                'parent_names': ""
            }
        }

        config = {
            **self.TEST_CHANNEL_CONFIG,
            'test_234': {
                'id':         "test_234",
                'info':       True,
                'warning':    False,
                'critical':   True,
                'error':      True,
                'parent_ids': "GENERAL,",
            }
        }

        mock_ack.return_value = None
        mock_extract_config.side_effect = generate_extract_config_mocker(config)
        try:
            # Must create a connection so that the blocking channel is passed
            self.connect_to_rabbit()
            self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False,
                                            True, False, False)

            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.CONFIG_ROUTING_KEY)

            config_json = json.dumps(config_file)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(
                blocking_channel, method_chains, properties, config_json
            )

            expected_output = {
                self.CONFIG_ROUTING_KEY: copy.deepcopy(config)
            }

            self.assertDictEqual(
                expected_output, self._test_alert_router._config
            )
        finally:
            # Clean before test finishes
            self.delete_exchange_if_exists(CONFIG_EXCHANGE)
            self._test_alert_router.disconnect_from_rabbit()

    @parameterized.expand([
        (
                {'id':           "test_123", 'channel_name': "test_channel",
                 'info':         "false", 'warning': "false",
                 'critical':     "false",
                 'error':        "false", 'parent_ids': "GENERAL,",
                 'parent_names': ""},
                "channel.test_123",
                {'id':       "test_123", 'info': False, 'warning': False,
                 'critical': False, 'error': False, 'parent_ids': ["GENERAL"],
                 }
        ), (
                {'id':    "test_123", 'channel_name': "test_channel",
                 'info':  "on", 'warning': "off", 'critical': "yes",
                 'error': "no", 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.test_123",
                {'id':       "test_123", 'info': True, 'warning': False,
                 'critical': True, 'error': False, 'parent_ids': ["GENERAL"],
                 }
        ), (
                {'id':         "twilio_123", 'channel_name': "test_channel",
                 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.twilio_123",
                {'id':       "twilio_123", 'info': False, 'warning': False,
                 'critical': True, 'error': False, 'parent_ids': ["GENERAL"],
                 }
        ), (
                {'id':         "twilio_123", 'channel_name': "test_channel",
                 'info':       "on", 'warning': "off", 'critical': "yes",
                 'error':      "no",
                 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.twilio_123",
                {'id':       "twilio_123", 'info': False, 'warning': False,
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
        self.assertDictEqual(
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
                {'id':           "test_123", 'channel_name': "test_channel",
                 'info':         "false", 'warning': "false",
                 'critical':     "false",
                 'error':        "false", 'parent_ids': "GENERAL,",
                 'parent_names': ""},
                "channel.test_123"
        ), (
                {'id':    "test_123", 'channel_name': "test_channel",
                 'info':  "on", 'warning': "off", 'critical': "yes",
                 'error': "no", 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.test_123"
        ), (
                {'id':         "twilio_123", 'channel_name': "test_channel",
                 'parent_ids': "GENERAL,", 'parent_names': ""},
                "channel.twilio_123"
        ), (
                {'id':         "twilio_123", 'channel_name': "test_channel",
                 'info':       "on", 'warning': "off", 'critical': "yes",
                 'error':      "no",
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
                {'info':  "false", 'warning': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id':    "test_123", 'warning': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id':    "test_123", 'info': "false", 'critical': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id':    "test_123", 'info': "false", 'warning': "false",
                 'error': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id':       "test_123", 'info': "false", 'warning': "false",
                 'critical': "false", 'parent_ids': "GENERAL,"},
                "channel.test_123"
        ), (
                {'id':       "test_123", 'info': "false", 'warning': "false",
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

    def test_disconnect_from_rabbit_disconnects(self):
        self._test_alert_router.disconnect_from_rabbit()

        self.assertIsNone(self._test_alert_router._rabbitmq.channel)

    def test_disconnect_from_rabbit_remains_disconnected(self):
        self._test_alert_router.disconnect_from_rabbit()
        self._test_alert_router.disconnect_from_rabbit()

        self.assertIsNone(self._test_alert_router._rabbitmq.channel)

    @parameterized.expand([
        ("error",), ("ERroR",), ("warning",), ("WArNIng",), ("critical",),
        ("CRitICAl",), ("info",), ("InFo",),
    ])
    @mock.patch.object(AlertRouter, "_send_data", autospec=True)
    @mock.patch.object(AlertRouter, "_push_to_queue", autospec=True)
    @mock.patch.object(AlertRouter, "is_all_muted", autospec=True)
    @mock.patch.object(AlertRouter, "is_chain_severity_muted", autospec=True)
    @mock.patch.object(RabbitMQApi, "basic_ack", autospec=True)
    def test__process_alert_no_mute(self, severity: str,
                                    mock_basic_ack: MagicMock,
                                    mock_is_chain_severity_muted: MagicMock,
                                    mock_is_all_muted: MagicMock,
                                    mock_push_to_queue: MagicMock,
                                    mock_send_data: MagicMock):

        mock_basic_ack.return_value = None
        mock_is_all_muted.return_value = False
        mock_is_chain_severity_muted.return_value = False
        mock_push_to_queue.return_value = None
        mock_send_data.return_value = None

        config = {
            'test_234': {
                'id':         "test_234",
                'info':       True,
                'warning':    True,
                'critical':   True,
                'error':      True,
                'parent_ids': "GENERAL,",
            }
        }

        self._test_alert_router._config = {'channel.test': config}
        try:

            # Must create a connection so that the blocking channel is passed
            self.connect_to_rabbit()
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.ALERT_ROUTER_ROUTING_KEY
            )

            properties = pika.spec.BasicProperties()
            alert_timestamp = datetime(
                year=1997, month=8, day=15, hour=10, minute=21, second=33,
                microsecond=30
            )
            alert = Alert(
                DummyAlertCode.TEST_ALERT_CODE, "This is a test alert",
                severity, alert_timestamp.timestamp(), "GENERAL", "origin_123"
            )

            alert_json = json.dumps(alert.alert_data)

            expected_output_channel = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'test_234'
            }

            expected_output_console = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'console'
            }

            expected_output_log = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'log'
            }

            self._test_alert_router._process_alert(
                blocking_channel, method_chains, properties, alert_json
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_channel,
                ALERT_EXCHANGE, "channel.test_234", mandatory=False
            )
            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_console,
                ALERT_EXCHANGE, "channel.console", mandatory=True
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_log, ALERT_EXCHANGE,
                "channel.log", mandatory=True
            )
            mock_push_to_queue.assert_any_call(
                self._test_alert_router, copy.deepcopy(alert.alert_data),
                STORE_EXCHANGE, "alert", mandatory=True
            )

            self.assertEqual(4, mock_push_to_queue.call_count)

            mock_send_data.assert_called_once_with(self._test_alert_router)
            self.assertEqual(1, mock_send_data.call_count)
        finally:
            self._test_alert_router.disconnect_from_rabbit()

    @parameterized.expand([
        ("error",), ("warning",), ("critical",), ("info",),
    ])
    @mock.patch.object(AlertRouter, "_send_data", autospec=True)
    @mock.patch.object(AlertRouter, "_push_to_queue", autospec=True)
    @mock.patch.object(AlertRouter, "is_all_muted", autospec=True)
    @mock.patch.object(AlertRouter, "is_chain_severity_muted", autospec=True)
    @mock.patch.object(RabbitMQApi, "basic_ack", autospec=True)
    def test__process_alert_false_no_mute(
            self, severity: str, mock_basic_ack: MagicMock,
            mock_is_chain_severity_muted: MagicMock,
            mock_is_all_muted: MagicMock, mock_push_to_queue: MagicMock,
            mock_send_data: MagicMock
    ):

        mock_basic_ack.return_value = None
        mock_is_all_muted.return_value = False
        mock_is_chain_severity_muted.return_value = False
        mock_push_to_queue.return_value = None
        mock_send_data.return_value = None

        config = {
            'test_234': {
                'id':         "test_234",
                'info':       True,
                'warning':    True,
                'critical':   True,
                'error':      True,
                'parent_ids': "GENERAL,",
            }
        }

        config['test_234'][severity] = False

        self._test_alert_router._config = {'channel.test': config}

        try:
            # Must create a connection so that the blocking channel is passed
            self.connect_to_rabbit()

            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.ALERT_ROUTER_ROUTING_KEY
            )

            properties = pika.spec.BasicProperties()
            alert_timestamp = datetime(
                year=1997, month=8, day=15, hour=10, minute=21, second=33,
                microsecond=30
            )
            alert = Alert(
                DummyAlertCode.TEST_ALERT_CODE, "This is a test alert",
                severity, alert_timestamp.timestamp(), "GENERAL", "origin_123"
            )

            alert_json = json.dumps(alert.alert_data)

            expected_output_console = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'console'
            }

            expected_output_log = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'log'
            }

            self._test_alert_router._process_alert(
                blocking_channel, method_chains, properties, alert_json
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_console,
                ALERT_EXCHANGE, "channel.console", mandatory=True
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_log, ALERT_EXCHANGE,
                "channel.log", mandatory=True
            )
            mock_push_to_queue.assert_any_call(
                self._test_alert_router, copy.deepcopy(alert.alert_data),
                STORE_EXCHANGE, "alert", mandatory=True
            )

            self.assertEqual(3, mock_push_to_queue.call_count)

            mock_send_data.assert_called_once_with(self._test_alert_router)
            self.assertEqual(1, mock_send_data.call_count)
        finally:
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "_send_data", autospec=True)
    @mock.patch.object(AlertRouter, "_push_to_queue", autospec=True)
    @mock.patch.object(AlertRouter, "is_all_muted", autospec=True)
    @mock.patch.object(AlertRouter, "is_chain_severity_muted", autospec=True)
    @mock.patch.object(RabbitMQApi, "basic_ack", autospec=True)
    def test__process_alert_mute_all(self, mock_basic_ack: MagicMock,
                                     mock_is_chain_severity_muted: MagicMock,
                                     mock_is_all_muted: MagicMock,
                                     mock_push_to_queue: MagicMock,
                                     mock_send_data: MagicMock):

        mock_basic_ack.return_value = None
        mock_is_all_muted.return_value = True
        mock_is_chain_severity_muted.return_value = False
        mock_push_to_queue.return_value = None
        mock_send_data.return_value = None

        config = {
            'test_234': {
                'id':         "test_234",
                'info':       True,
                'warning':    True,
                'critical':   True,
                'error':      True,
                'parent_ids': "GENERAL,",
            }
        }

        self._test_alert_router._config = {'channel.test': config}

        try:
            # Must create a connection so that the blocking channel is passed
            self.connect_to_rabbit()
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.ALERT_ROUTER_ROUTING_KEY
            )

            properties = pika.spec.BasicProperties()
            alert_timestamp = datetime(
                year=1997, month=8, day=15, hour=10, minute=21, second=33,
                microsecond=30
            )
            alert = Alert(
                DummyAlertCode.TEST_ALERT_CODE, "This is a test alert", 'error',
                alert_timestamp.timestamp(), "GENERAL", "origin_123"
            )

            alert_json = json.dumps(alert.alert_data)

            expected_output_console = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'console'
            }

            expected_output_log = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'log'
            }

            self._test_alert_router._process_alert(
                blocking_channel, method_chains, properties, alert_json
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_console,
                ALERT_EXCHANGE, "channel.console", mandatory=True
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_log, ALERT_EXCHANGE,
                "channel.log", mandatory=True
            )
            mock_push_to_queue.assert_any_call(
                self._test_alert_router, copy.deepcopy(alert.alert_data),
                STORE_EXCHANGE, "alert", mandatory=True
            )

            self.assertEqual(3, mock_push_to_queue.call_count)

            mock_send_data.assert_called_once_with(self._test_alert_router)
            self.assertEqual(1, mock_send_data.call_count)
        finally:
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "_send_data", autospec=True)
    @mock.patch.object(AlertRouter, "_push_to_queue", autospec=True)
    @mock.patch.object(AlertRouter, "is_all_muted", autospec=True)
    @mock.patch.object(AlertRouter, "is_chain_severity_muted", autospec=True)
    @mock.patch.object(RabbitMQApi, "basic_ack", autospec=True)
    def test__process_alert_severity_muted(
            self, mock_basic_ack: MagicMock,
            mock_is_chain_severity_muted: MagicMock,
            mock_is_all_muted: MagicMock, mock_push_to_queue: MagicMock,
            mock_send_data: MagicMock
    ):

        mock_basic_ack.return_value = None
        mock_is_all_muted.return_value = False
        mock_is_chain_severity_muted.return_value = True
        mock_push_to_queue.return_value = None
        mock_send_data.return_value = None

        config = {
            'test_234': {
                'id':         "test_234",
                'info':       True,
                'warning':    True,
                'critical':   True,
                'error':      True,
                'parent_ids': "GENERAL,",
            }
        }

        self._test_alert_router._config = {'channel.test': config}

        try:
            # Must create a connection so that the blocking channel is passed
            self.connect_to_rabbit()
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.ALERT_ROUTER_ROUTING_KEY
            )

            properties = pika.spec.BasicProperties()
            alert_timestamp = datetime(
                year=1997, month=8, day=15, hour=10, minute=21, second=33,
                microsecond=30
            )
            alert = Alert(
                DummyAlertCode.TEST_ALERT_CODE, "This is a test alert", 'error',
                alert_timestamp.timestamp(), "GENERAL", "origin_123"
            )

            alert_json = json.dumps(alert.alert_data)

            expected_output_console = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'console'
            }

            expected_output_log = {
                **copy.deepcopy(alert.alert_data),
                'destination_id': 'log'
            }

            self._test_alert_router._process_alert(
                blocking_channel, method_chains, properties, alert_json
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_console,
                ALERT_EXCHANGE, "channel.console", mandatory=True
            )

            mock_push_to_queue.assert_any_call(
                self._test_alert_router, expected_output_log, ALERT_EXCHANGE,
                "channel.log", mandatory=True
            )
            mock_push_to_queue.assert_any_call(
                self._test_alert_router, copy.deepcopy(alert.alert_data),
                STORE_EXCHANGE, "alert", mandatory=True
            )

            self.assertEqual(3, mock_push_to_queue.call_count)

            mock_send_data.assert_called_once_with(self._test_alert_router)
            self.assertEqual(1, mock_send_data.call_count)
        finally:
            self._test_alert_router.disconnect_from_rabbit()

    @mock.patch.object(AlertRouter, "_send_data", autospec=True)
    @mock.patch.object(AlertRouter, "_push_to_queue", autospec=True)
    @mock.patch.object(AlertRouter, "is_all_muted", autospec=True)
    @mock.patch.object(AlertRouter, "is_chain_severity_muted", autospec=True)
    @mock.patch.object(RabbitMQApi, "basic_ack", autospec=True)
    def test__process_alert_error_processing(
            self, mock_basic_ack: MagicMock,
            mock_is_chain_severity_muted: MagicMock,
            mock_is_all_muted: MagicMock, mock_push_to_queue: MagicMock,
            mock_send_data: MagicMock
    ):

        mock_basic_ack.return_value = None
        # trigger an exception when processing - we don't care where from as
        # long as it's in the processing try-except
        mock_is_all_muted.side_effect = Exception("Test Exception")
        mock_is_chain_severity_muted.return_value = False
        mock_push_to_queue.return_value = None
        mock_send_data.return_value = None

        try:
            # Must create a connection so that the blocking channel is passed
            self.connect_to_rabbit()
            self._test_alert_router._initialise_rabbitmq()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            method_chains = pika.spec.Basic.Deliver(
                routing_key=self.ALERT_ROUTER_ROUTING_KEY
            )

            properties = pika.spec.BasicProperties()
            alert_timestamp = datetime(
                year=1997, month=8, day=15, hour=10, minute=21, second=33,
                microsecond=30
            )
            alert = Alert(
                DummyAlertCode.TEST_ALERT_CODE, "This is a test alert", 'error',
                alert_timestamp.timestamp(), "GENERAL", "origin_123"
            )

            alert_json = json.dumps(alert.alert_data)

            self._test_alert_router._process_alert(
                blocking_channel, method_chains, properties, alert_json
            )

            mock_push_to_queue.assert_not_called()

            mock_send_data.assert_called_once_with(self._test_alert_router)
            self.assertEqual(1, mock_send_data.call_count)
        finally:
            self._test_alert_router.disconnect_from_rabbit()

    @freeze_time("1997-08-15T10:21:33.000030")
    @mock.patch.object(RabbitMQApi, "basic_ack", autospec=True)
    def test__process_ping_sends_valid_hb(self, mock_ack: MagicMock):
        mock_ack.return_value = None

        expected_output = {
            'component_name': self.ALERT_ROUTER_NAME,
            'is_alive':       True,
            'timestamp':      datetime(
                year=1997, month=8, day=15, hour=10, minute=21, second=33,
                microsecond=30
            ).timestamp()
        }
        HEARTBEAT_QUEUE = "hb_test"
        try:
            self.connect_to_rabbit()
            self._rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, "topic",
                                            False,
                                            True, False, False)

            queue_res = self._rabbitmq.queue_declare(
                queue=HEARTBEAT_QUEUE, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.assertEqual(0, queue_res.method.message_count)

            self._rabbitmq.queue_bind(HEARTBEAT_QUEUE, HEALTH_CHECK_EXCHANGE,
                                      "heartbeat.*")

            self._test_alert_router._initialise_rabbitmq()

            blocking_channel = self._test_alert_router._rabbitmq.channel
            method_chains = pika.spec.Basic.Deliver(
                routing_key="ping"
            )
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_ping(blocking_channel,
                                                  method_chains,
                                                  properties, b"ping")

            # By re-declaring the queue again we can get the number of messages
            # in the queue.
            queue_res = self._rabbitmq.queue_declare(
                queue=HEARTBEAT_QUEUE, durable=True, exclusive=False,
                auto_delete=False, passive=True
            )
            self.assertEqual(1, queue_res.method.message_count)

            # Check that the message received is a valid HB
            _, _, body = self._rabbitmq.basic_get(HEARTBEAT_QUEUE)
            self.assertDictEqual(expected_output, json.loads(body))
        finally:
            self.delete_queue_if_exists(HEARTBEAT_QUEUE)
            self.delete_exchange_if_exists(HEALTH_CHECK_EXCHANGE)
            self.disconnect_from_rabbit()

    @parameterized.expand([
        ("PARENT_1", "x", "{}", False),
        ("PARENT_1", "x", '{"x": true}', True),
        ("PARENT_1", "x", '{"x": false}', False),
        ("PARENT_1", "x", '{"x": null}', False),
        ("PARENT_1", "x", '{"x": "Anything"}', True)
    ])
    @mock.patch.object(Keys, "get_hash_parent", autospec=True)
    @mock.patch.object(Keys, "get_chain_mute_alerts", autospec=True)
    @mock.patch.object(RedisApi, "hget", autospec=True)
    def test_is_chain_severity_muted(
            self, parent_id_in: str, severity_in: str, redis_memory: str,
            expected_output: bool, mock_redis_hget: MagicMock,
            mock_alerter_mute: MagicMock, mock_get_hash_parent: MagicMock
    ):
        test_redis_key = "random_key"
        test_redis_hash_key = "h_random_key"
        mock_get_hash_parent.return_value = test_redis_hash_key
        mock_alerter_mute.return_value = test_redis_key
        mock_redis_hget.return_value = redis_memory

        self.assertEqual(expected_output,
                         self._test_alert_router.is_chain_severity_muted(
                             parent_id_in, severity_in))

        mock_get_hash_parent.assert_called_once_with(parent_id_in)
        mock_redis_hget.assert_called_once_with(
            self._test_alert_router._redis, test_redis_hash_key, test_redis_key,
            default=b"{}"
        )

    @parameterized.expand([
        ("x", "{}", False),
        ("x", '{"x": true}', True),
        ("x", '{"x": false}', False),
        ("x", '{"x": null}', False),
        ("x", '{"x": "Anything"}', True)
    ])
    @mock.patch.object(Keys, "get_alerter_mute", autospec=True)
    @mock.patch.object(RedisApi, "get", autospec=True)
    def test_is_all_muted_returns_correct(self, severity_in: str,
                                          redis_memory: str,
                                          expected_output: bool,
                                          mock_redis_get: MagicMock,
                                          mock_alerter_mute: MagicMock):

        test_redis_key = "random_key"
        mock_alerter_mute.return_value = test_redis_key
        mock_redis_get.return_value = redis_memory

        self.assertEqual(expected_output,
                         self._test_alert_router.is_all_muted(severity_in))
        mock_redis_get.assert_called_once_with(self._test_alert_router._redis,
                                               test_redis_key, default=b"{}")
