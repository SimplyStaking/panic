import copy
import json
import logging
import time
import unittest
from datetime import timedelta
from unittest import mock

import configparser
import pika.exceptions
from parameterized import parameterized
from pika import BasicProperties

from src.alert_router.alert_router import (AlertRouter, _HEARTBEAT_QUEUE_NAME,
                                           _ROUTED_ALERT_QUEUED_LOG_MESSAGE,
                                           _ALERT_ROUTER_INPUT_QUEUE_NAME)
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants import (CONFIG_EXCHANGE, ALERT_EXCHANGE,
                                 STORE_EXCHANGE, HEALTH_CHECK_EXCHANGE,
                                 ALERT_ROUTER_CONFIGS_QUEUE_NAME)


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

        self._test_channel_config_file = {
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

        self._test_channel_config = {
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

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_first_config_consumed_and_processed(self, mock_ack):
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        mock_ack.return_value = None
        routing_key = "channels.test"
        try:
            # Must create a connection so that the blocking channel is passed
            self._test_alert_router._initialise_rabbit()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=routing_key)
            config_json = json.dumps(
                self._test_channel_config_file)
            properties = pika.spec.BasicProperties()

            self._test_alert_router._process_configs(blocking_channel,
                                                     method_chains,
                                                     properties,
                                                     config_json)

            expected_output = {
                routing_key: copy.deepcopy(self._test_channel_config)
            }

            self.assertEqual(expected_output, self._test_alert_router._config)

            # Clean before test finishes
            self._test_alert_router.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "basic_ack")
    def test_correct_config_update_consumed_and_processed(self, mock_ack):
        self._rabbitmq.connect_till_successful()
        self._rabbitmq.exchange_declare(CONFIG_EXCHANGE, "topic", False, True,
                                        False, False)

        mock_ack.return_value = None
        routing_key = "channels.test"
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

        try:
            # Must create a connection so that the blocking channel is passed
            self._test_alert_router._initialise_rabbit()
            blocking_channel = self._test_alert_router._rabbitmq.channel

            # We will send new configs through both the existing and
            # non-existing chain and general paths to make sure that all routes
            # work as expected.
            method_chains = pika.spec.Basic.Deliver(
                routing_key=routing_key)
            config_json = json.dumps(
                self._test_channel_config_file)
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
                routing_key: copy.deepcopy(updated_config)
            }

            self.assertEqual(expected_output, self._test_alert_router._config)

            # Clean before test finishes
            self._test_alert_router.disconnect_from_rabbit()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @unittest.skip
    def test_incorrect_config_update_consumed_and_reverted(self):
        pass

    @unittest.skip
    def test_multiple_channel_config_correct(self):
        self.fail()

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
    def test__extract_config(self):
        self.fail()

    @unittest.skip
    def test_is_all_muted(self):
        self.fail()

    @unittest.skip
    def test_is_chain_severity_muted(self):
        self.fail()
