import copy
import json
import logging
import multiprocessing
import unittest
from datetime import timedelta, datetime
from unittest import mock
from unittest.mock import call

import pika
from freezegun import freeze_time
from parameterized import parameterized
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from src.channels_manager.handlers.starters import (
    start_telegram_alerts_handler, start_telegram_commands_handler,
    start_twilio_alerts_handler, start_email_alerts_handler,
    start_pagerduty_alerts_handler, start_opsgenie_alerts_handler,
    start_console_alerts_handler, start_log_alerts_handler)
from src.channels_manager.manager import ChannelsManager
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants.names import (TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE,
                                       TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE,
                                       TWILIO_ALERTS_HANDLER_NAME_TEMPLATE,
                                       EMAIL_ALERTS_HANDLER_NAME_TEMPLATE,
                                       PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE,
                                       OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE,
                                       CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE,
                                       LOG_ALERTS_HANDLER_NAME_TEMPLATE,
                                       CONSOLE_CHANNEL_ID,
                                       CONSOLE_CHANNEL_NAME,
                                       LOG_CHANNEL_ID, LOG_CHANNEL_NAME)
from src.utils.constants.rabbitmq import (HEALTH_CHECK_EXCHANGE,
                                          CONFIG_EXCHANGE,
                                          HEARTBEAT_OUTPUT_MANAGER_ROUTING_KEY,
                                          PING_ROUTING_KEY,
                                          CHANNELS_MANAGER_HEARTBEAT_QUEUE_NAME,
                                          CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                          CHANNELS_MANAGER_CONFIGS_ROUTING_KEY)
from src.utils.exceptions import PANICException, MessageWasNotDeliveredException
from src.utils.types import ChannelHandlerTypes, ChannelTypes
from test.utils.utils import (infinite_fn, connect_to_rabbit,
                              delete_queue_if_exists, delete_exchange_if_exists,
                              disconnect_from_rabbit)


class TestChannelsManager(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_logger = logging.getLogger('Dummy')
        self.dummy_logger.disabled = True
        self.connection_check_time_interval = timedelta(seconds=0)
        self.rabbit_ip = env.RABBIT_IP
        self.rabbitmq = RabbitMQApi(
            self.dummy_logger, self.rabbit_ip,
            connection_check_time_interval=self.connection_check_time_interval)
        self.manager_name = 'test_channels_manager'
        self.test_queue_name = 'Test Queue'
        self.test_data_str = 'test data'
        self.test_timestamp = datetime(2012, 1, 1).timestamp()
        self.test_heartbeat = {
            'component_name': 'Test Component',
            'timestamp': self.test_timestamp,
        }
        self.test_dict = {'test_key': 'test_val'}
        self.dummy_process1 = multiprocessing.Process(target=infinite_fn,
                                                      args=())
        self.dummy_process1.daemon = True
        self.test_manager = ChannelsManager(self.dummy_logger,
                                            self.manager_name, self.rabbitmq)
        self.test_exception = PANICException('test_exception', 1)
        self.telegram_channel_name = 'test_telegram_channel'
        self.telegram_channel_id = 'test_telegram_id12345'
        self.bot_token = '1234567891:ABC-67ABCrfZFdddqRT5Gh837T2rtUFHgTY'
        self.bot_chat_id = 'test_bot_chat_id'
        self.test_chain_1 = 'Kusama'
        self.test_chain_2 = 'Cosmos'
        self.test_chain_3 = 'Test_Chain'
        self.test_chain1_id = 'kusama1234'
        self.test_chain2_id = 'cosmos1234'
        self.test_chain3_id = 'test_chain11123'
        self.test_associated_chains = {
            self.test_chain1_id: self.test_chain_1,
            self.test_chain2_id: self.test_chain_2,
            self.test_chain3_id: self.test_chain_3
        }
        self.twilio_channel_name = 'test_twilio_channel'
        self.twilio_channel_id = 'test_twilio_id12345'
        self.account_sid = 'test_account_sid'
        self.auth_token = 'test_auth_token'
        self.call_from = '+35699999999'
        self.call_to = ['+35611111111', '+35644545454', '+35634343434']
        self.twiml = env.TWIML
        self.twiml_is_url = env.TWIML_IS_URL
        self.email_channel_name = 'test_email_channel'
        self.email_channel_id = 'test_email1234'
        self.emails_to = ['test1@example.com', 'test2@example.com',
                          'test3@example.com']
        self.smtp = 'test smtp server'
        self.sender = 'test sender'
        self.username = 'test username'
        self.password = 'test password'
        self.port = 10
        self.integration_key = 'test_integration_key'
        self.pagerduty_channel_name = 'test_pagerduty_channel'
        self.pagerduty_channel_id = 'test_pagerduty_id12345'
        self.api_key = 'test api key'
        self.opsgenie_channel_name = 'test_opsgenie_channel'
        self.opsgenie_channel_id = 'test_opsgenie_id12345'
        self.eu_host = True
        self.console_channel_name = CONSOLE_CHANNEL_NAME
        self.console_channel_id = CONSOLE_CHANNEL_ID
        self.log_channel_name = LOG_CHANNEL_NAME
        self.log_channel_id = LOG_CHANNEL_ID
        self.test_channel_process_dict = {
            self.telegram_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.telegram_channel_name),
                    'process': self.dummy_process1,
                    'bot_token': self.bot_token,
                    'bot_chat_id': self.bot_chat_id,
                    'channel_id': self.telegram_channel_id,
                    'channel_name': self.telegram_channel_name,
                    'channel_type': ChannelTypes.TELEGRAM.value,
                },
                ChannelHandlerTypes.COMMANDS.value: {
                    'component_name':
                        TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE.format(
                            self.telegram_channel_name),
                    'process': self.dummy_process1,
                    'bot_token': self.bot_token,
                    'bot_chat_id': self.bot_chat_id,
                    'channel_id': self.telegram_channel_id,
                    'channel_name': self.telegram_channel_name,
                    'channel_type': ChannelTypes.TELEGRAM.value,
                    'associated_chains': self.test_associated_chains,
                },
            },
            self.twilio_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        TWILIO_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.twilio_channel_name),
                    'process': self.dummy_process1,
                    'account_sid': self.account_sid,
                    'auth_token': self.auth_token,
                    'channel_id': self.twilio_channel_id,
                    'channel_name': self.twilio_channel_name,
                    'channel_type': ChannelTypes.TWILIO.value,
                    'call_from': self.call_from,
                    'call_to': self.call_to,
                    'twiml': self.twiml,
                    'twiml_is_url': self.twiml_is_url,
                },
            },
            self.email_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        EMAIL_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.email_channel_name),
                    'process': self.dummy_process1,
                    'smtp': self.smtp,
                    'email_from': self.sender,
                    'emails_to': self.emails_to,
                    'channel_id': self.email_channel_id,
                    'channel_name': self.email_channel_name,
                    'channel_type': ChannelTypes.EMAIL.value,
                    'username': self.username,
                    'password': self.password,
                    'port': self.port,
                },
            },
            self.pagerduty_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.pagerduty_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.pagerduty_channel_id,
                    'channel_name': self.pagerduty_channel_name,
                    'channel_type': ChannelTypes.PAGERDUTY.value,
                    'integration_key': self.integration_key,
                },
            },
            self.opsgenie_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.opsgenie_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.opsgenie_channel_id,
                    'channel_name': self.opsgenie_channel_name,
                    'channel_type': ChannelTypes.OPSGENIE.value,
                    'api_key': self.api_key,
                    'eu_host': self.eu_host
                },
            },
            self.console_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.console_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.console_channel_id,
                    'channel_name': self.console_channel_name,
                    'channel_type': ChannelTypes.CONSOLE.value,
                },
            },
            self.log_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        LOG_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.log_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.log_channel_id,
                    'channel_name': self.log_channel_name,
                    'channel_type': ChannelTypes.LOG.value,
                },
            }
        }
        self.test_channel_process_dict_copy = {
            self.telegram_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.telegram_channel_name),
                    'process': self.dummy_process1,
                    'bot_token': self.bot_token,
                    'bot_chat_id': self.bot_chat_id,
                    'channel_id': self.telegram_channel_id,
                    'channel_name': self.telegram_channel_name,
                    'channel_type': ChannelTypes.TELEGRAM.value,
                },
                ChannelHandlerTypes.COMMANDS.value: {
                    'component_name':
                        TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE.format(
                            self.telegram_channel_name),
                    'process': self.dummy_process1,
                    'bot_token': self.bot_token,
                    'bot_chat_id': self.bot_chat_id,
                    'channel_id': self.telegram_channel_id,
                    'channel_name': self.telegram_channel_name,
                    'channel_type': ChannelTypes.TELEGRAM.value,
                    'associated_chains': self.test_associated_chains,
                },
            },
            self.twilio_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        TWILIO_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.twilio_channel_name),
                    'process': self.dummy_process1,
                    'account_sid': self.account_sid,
                    'auth_token': self.auth_token,
                    'channel_id': self.twilio_channel_id,
                    'channel_name': self.twilio_channel_name,
                    'channel_type': ChannelTypes.TWILIO.value,
                    'call_from': self.call_from,
                    'call_to': self.call_to,
                    'twiml': self.twiml,
                    'twiml_is_url': self.twiml_is_url,
                },
            },
            self.email_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        EMAIL_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.email_channel_name),
                    'process': self.dummy_process1,
                    'smtp': self.smtp,
                    'email_from': self.sender,
                    'emails_to': self.emails_to,
                    'channel_id': self.email_channel_id,
                    'channel_name': self.email_channel_name,
                    'channel_type': ChannelTypes.EMAIL.value,
                    'username': self.username,
                    'password': self.password,
                    'port': self.port,
                },
            },
            self.pagerduty_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.pagerduty_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.pagerduty_channel_id,
                    'channel_name': self.pagerduty_channel_name,
                    'channel_type': ChannelTypes.PAGERDUTY.value,
                    'integration_key': self.integration_key,
                },
            },
            self.opsgenie_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.opsgenie_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.opsgenie_channel_id,
                    'channel_name': self.opsgenie_channel_name,
                    'channel_type': ChannelTypes.OPSGENIE.value,
                    'api_key': self.api_key,
                    'eu_host': self.eu_host
                },
            },
            self.console_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.console_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.console_channel_id,
                    'channel_name': self.console_channel_name,
                    'channel_type': ChannelTypes.CONSOLE.value,
                },
            },
            self.log_channel_id: {
                ChannelHandlerTypes.ALERTS.value: {
                    'component_name':
                        LOG_ALERTS_HANDLER_NAME_TEMPLATE.format(
                            self.log_channel_name),
                    'process': self.dummy_process1,
                    'channel_id': self.log_channel_id,
                    'channel_name': self.log_channel_name,
                    'channel_type': ChannelTypes.LOG.value,
                },
            }
        }
        self.test_channel_configs = {
            ChannelTypes.TELEGRAM.value: {
                self.telegram_channel_id: {
                    'id': self.telegram_channel_id,
                    'channel_name': self.telegram_channel_name,
                    'bot_token': self.bot_token,
                    'chat_id': self.bot_chat_id,
                    'info': 'True',
                    'warning': 'True',
                    'critical': 'True',
                    'error': 'True',
                    'alerts': 'True',
                    'commands': 'True',
                    'parent_ids': "{},{},{}".format(self.test_chain1_id,
                                                    self.test_chain2_id,
                                                    self.test_chain3_id),
                    'parent_names': "{},{},{}".format(self.test_chain_1,
                                                      self.test_chain_2,
                                                      self.test_chain_3),
                }
            },
            ChannelTypes.TWILIO.value: {
                self.twilio_channel_id: {
                    'id': self.twilio_channel_id,
                    'channel_name': self.twilio_channel_name,
                    'account_sid': self.account_sid,
                    'auth_token': self.auth_token,
                    'twilio_phone_no': self.call_from,
                    'twilio_phone_numbers_to_dial_valid':
                        "{}".format(','.join(self.call_to)),
                    'parent_ids': "{},{},{}".format(self.test_chain1_id,
                                                    self.test_chain2_id,
                                                    self.test_chain3_id),
                    'parent_names': "{},{},{}".format(self.test_chain_1,
                                                      self.test_chain_2,
                                                      self.test_chain_3),
                }
            },
            ChannelTypes.EMAIL.value: {
                self.email_channel_id: {
                    'id': self.email_channel_id,
                    'channel_name': self.email_channel_name,
                    'smtp': self.smtp,
                    'port': self.port,
                    'email_from': self.sender,
                    'emails_to': "{}".format(','.join(self.emails_to)),
                    'username': self.username,
                    'password': self.password,
                    'info': 'True',
                    'warning': 'True',
                    'critical': 'True',
                    'error': 'True',
                    'parent_ids': "{},{},{}".format(self.test_chain1_id,
                                                    self.test_chain2_id,
                                                    self.test_chain3_id),
                    'parent_names': "{},{},{}".format(self.test_chain_1,
                                                      self.test_chain_2,
                                                      self.test_chain_3),
                }
            },
            ChannelTypes.PAGERDUTY.value: {
                self.pagerduty_channel_id: {
                    'id': self.pagerduty_channel_id,
                    'channel_name': self.pagerduty_channel_name,
                    'api_token': self.api_key,
                    'integration_key': self.integration_key,
                    'info': 'True',
                    'warning': 'True',
                    'critical': 'True',
                    'error': 'True',
                    'parent_ids': "{},{},{}".format(self.test_chain1_id,
                                                    self.test_chain2_id,
                                                    self.test_chain3_id),
                    'parent_names': "{},{},{}".format(self.test_chain_1,
                                                      self.test_chain_2,
                                                      self.test_chain_3),
                }
            },
            ChannelTypes.OPSGENIE.value: {
                self.opsgenie_channel_id: {
                    'id': self.opsgenie_channel_id,
                    'channel_name': self.opsgenie_channel_name,
                    'api_token': self.api_key,
                    'eu': 'True',
                    'info': 'True',
                    'warning': 'True',
                    'critical': 'True',
                    'error': 'True',
                    'parent_ids': "{},{},{}".format(self.test_chain1_id,
                                                    self.test_chain2_id,
                                                    self.test_chain3_id),
                    'parent_names': "{},{},{}".format(self.test_chain_1,
                                                      self.test_chain_2,
                                                      self.test_chain_3),
                }
            },
        }

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        connect_to_rabbit(self.test_manager.rabbitmq)
        delete_queue_if_exists(self.test_manager.rabbitmq, self.test_queue_name)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               CHANNELS_MANAGER_HEARTBEAT_QUEUE_NAME)
        delete_queue_if_exists(self.test_manager.rabbitmq,
                               CHANNELS_MANAGER_CONFIGS_QUEUE_NAME)
        delete_exchange_if_exists(self.test_manager.rabbitmq,
                                  HEALTH_CHECK_EXCHANGE)
        delete_exchange_if_exists(self.test_manager.rabbitmq, CONFIG_EXCHANGE)
        disconnect_from_rabbit(self.test_manager.rabbitmq)

        self.dummy_logger = None
        self.rabbitmq = None
        self.test_manager = None
        self.test_exception = None
        self.connection_check_time_interval = None
        self.dummy_process1 = None

    def test__str__returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, str(self.test_manager))

    def test_name_returns_manager_name(self) -> None:
        self.assertEqual(self.manager_name, self.test_manager.name)

    def test_channel_configs_returns_the_channel_configurations(self) -> None:
        self.test_manager._channel_configs = self.test_dict
        self.assertEqual(self.test_dict, self.test_manager.channel_configs)

    def test_channel_process_dict_returns_channel_process_dict(self) -> None:
        self.test_manager._channel_process_dict = self.test_dict
        self.assertEqual(self.test_dict, self.test_manager.channel_process_dict)

    def test_initialise_rabbitmq_initializes_everything_as_expected(
            self) -> None:
        try:
            # To make sure that there is no connection/channel already
            # established
            self.assertIsNone(self.rabbitmq.connection)
            self.assertIsNone(self.rabbitmq.channel)

            # To make sure that the exchanges and queues have not already been
            # declared
            connect_to_rabbit(self.rabbitmq)
            self.test_manager.rabbitmq.queue_delete(
                CHANNELS_MANAGER_HEARTBEAT_QUEUE_NAME)
            self.test_manager.rabbitmq.queue_delete(
                CHANNELS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            disconnect_from_rabbit(self.rabbitmq)

            self.test_manager._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_manager.rabbitmq.is_connected)
            self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_manager.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchanges and queues have been creating by
            # sending messages with the same routing keys as for the queues. We
            # will also check if the size of the queues is 0 to confirm that
            # basic_consume was called (it will store the msg in the component
            # memory immediately). If one of the exchanges or queues is not
            # created, then an exception will be thrown. Note when deleting the
            # exchanges in the beginning we also released every binding, hence
            # there is no other queue binded with the same routing key to any
            # exchange at this point.
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=PING_ROUTING_KEY, body=self.test_data_str,
                is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=CONFIG_EXCHANGE,
                routing_key=CHANNELS_MANAGER_CONFIGS_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queues to get the number of messages
            input_queue_res = self.test_manager.rabbitmq.queue_declare(
                CHANNELS_MANAGER_HEARTBEAT_QUEUE_NAME, False, True, False,
                False)
            configs_queue_res = self.test_manager.rabbitmq.queue_declare(
                CHANNELS_MANAGER_CONFIGS_QUEUE_NAME, False, True, False, False)
            self.assertEqual(0, input_queue_res.method.message_count)
            self.assertEqual(0, configs_queue_res.method.message_count)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(RabbitMQApi, "start_consuming")
    def test_listen_for_data_calls_start_consuming(
            self, mock_start_consuming) -> None:
        mock_start_consuming.return_value = None
        self.test_manager._listen_for_data()
        mock_start_consuming.assert_called_once()

    def test_send_heartbeat_sends_a_heartbeat_correctly(self) -> None:
        # This test creates a queue which receives messages with the same
        # routing key as the ones sent by send_heartbeat, and checks that the
        # heartbeat is received
        try:
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
            _, _, body = self.test_manager.rabbitmq.basic_get(
                self.test_queue_name)
            self.assertEqual(self.test_heartbeat, json.loads(body))
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_telegram_alerts_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.ALERTS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_telegram_alerts_handler(
            self.bot_token, self.bot_chat_id, self.telegram_channel_id,
            self.telegram_channel_name)

        process_details = self.test_manager.channel_process_dict[
            self.telegram_channel_id][handler_type]
        self.assertEqual(TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.telegram_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.bot_token, process_details['bot_token'])
        self.assertEqual(self.bot_chat_id, process_details['bot_chat_id'])
        self.assertEqual(self.telegram_channel_id,
                         process_details['channel_id'])
        self.assertEqual(self.telegram_channel_name,
                         process_details['channel_name'])
        self.assertEqual(ChannelTypes.TELEGRAM.value,
                         process_details['channel_type'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.telegram_channel_id] = {}
        expected_channel_process_dict[self.telegram_channel_id][
            ChannelHandlerTypes.ALERTS.value] = \
            self.test_channel_process_dict[self.telegram_channel_id][
                ChannelHandlerTypes.ALERTS.value]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_telegram_alerts_handler_creates_correct_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.ALERTS.value

        self.test_manager._create_and_start_telegram_alerts_handler(
            self.bot_token, self.bot_chat_id, self.telegram_channel_id,
            self.telegram_channel_name)

        process = self.test_manager.channel_process_dict[
            self.telegram_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(4, len(process._args))
        self.assertEqual((self.bot_token, self.bot_chat_id,
                          self.telegram_channel_id, self.telegram_channel_name),
                         process._args)
        self.assertEqual(start_telegram_alerts_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_telegram_cmds_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.COMMANDS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_telegram_cmds_handler(
            self.bot_token, self.bot_chat_id, self.telegram_channel_id,
            self.telegram_channel_name, self.test_associated_chains)

        process_details = self.test_manager.channel_process_dict[
            self.telegram_channel_id][handler_type]
        self.assertEqual(TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE.format(
            self.telegram_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.bot_token, process_details['bot_token'])
        self.assertEqual(self.bot_chat_id, process_details['bot_chat_id'])
        self.assertEqual(self.telegram_channel_id,
                         process_details['channel_id'])
        self.assertEqual(self.telegram_channel_name,
                         process_details['channel_name'])
        self.assertEqual(ChannelTypes.TELEGRAM.value,
                         process_details['channel_type'])
        self.assertEqual(self.test_associated_chains,
                         process_details['associated_chains'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.telegram_channel_id] = {}
        expected_channel_process_dict[self.telegram_channel_id][
            ChannelHandlerTypes.COMMANDS.value] = \
            self.test_channel_process_dict[self.telegram_channel_id][
                ChannelHandlerTypes.COMMANDS.value]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_telegram_cmds_handler_creates_correct_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.COMMANDS.value

        self.test_manager._create_and_start_telegram_cmds_handler(
            self.bot_token, self.bot_chat_id, self.telegram_channel_id,
            self.telegram_channel_name, self.test_associated_chains)

        process = self.test_manager.channel_process_dict[
            self.telegram_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(5, len(process._args))
        self.assertEqual((self.bot_token, self.bot_chat_id,
                          self.telegram_channel_id, self.telegram_channel_name,
                          self.test_associated_chains), process._args)
        self.assertEqual(start_telegram_commands_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_twilio_alerts_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.ALERTS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_twilio_alerts_handler(
            self.account_sid, self.auth_token, self.twilio_channel_id,
            self.twilio_channel_name, self.call_from, self.call_to, self.twiml,
            self.twiml_is_url)

        process_details = self.test_manager.channel_process_dict[
            self.twilio_channel_id][handler_type]
        self.assertEqual(TWILIO_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.twilio_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.account_sid, process_details['account_sid'])
        self.assertEqual(self.auth_token, process_details['auth_token'])
        self.assertEqual(self.twilio_channel_id, process_details['channel_id'])
        self.assertEqual(self.twilio_channel_name,
                         process_details['channel_name'])
        self.assertEqual(self.call_from, process_details['call_from'])
        self.assertEqual(self.call_to, process_details['call_to'])
        self.assertEqual(self.twiml, process_details['twiml'])
        self.assertEqual(self.twiml_is_url, process_details['twiml_is_url'])
        self.assertEqual(ChannelTypes.TWILIO.value,
                         process_details['channel_type'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.twilio_channel_id] = \
            self.test_channel_process_dict[self.twilio_channel_id]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_twilio_alerts_handler_creates_correct_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.ALERTS.value

        self.test_manager._create_and_start_twilio_alerts_handler(
            self.account_sid, self.auth_token, self.twilio_channel_id,
            self.twilio_channel_name, self.call_from, self.call_to, self.twiml,
            self.twiml_is_url)

        process = self.test_manager.channel_process_dict[
            self.twilio_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(8, len(process._args))
        self.assertEqual((self.account_sid, self.auth_token,
                          self.twilio_channel_id, self.twilio_channel_name,
                          self.call_from, self.call_to, self.twiml,
                          self.twiml_is_url), process._args)
        self.assertEqual(start_twilio_alerts_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_email_alerts_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.ALERTS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_email_alerts_handler(
            self.smtp, self.sender, self.emails_to, self.email_channel_id,
            self.email_channel_name, self.username, self.password, self.port)

        process_details = self.test_manager.channel_process_dict[
            self.email_channel_id][handler_type]
        self.assertEqual(EMAIL_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.email_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.smtp, process_details['smtp'])
        self.assertEqual(self.sender, process_details['email_from'])
        self.assertEqual(self.emails_to, process_details['emails_to'])
        self.assertEqual(self.email_channel_id, process_details['channel_id'])
        self.assertEqual(self.email_channel_name,
                         process_details['channel_name'])
        self.assertEqual(self.username, process_details['username'])
        self.assertEqual(self.password, process_details['password'])
        self.assertEqual(ChannelTypes.EMAIL.value,
                         process_details['channel_type'])
        self.assertEqual(self.port, process_details['port'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.email_channel_id] = \
            self.test_channel_process_dict[self.email_channel_id]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_email_alerts_handler_creates_correct_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.ALERTS.value

        self.test_manager._create_and_start_email_alerts_handler(
            self.smtp, self.sender, self.emails_to, self.email_channel_id,
            self.email_channel_name, self.username, self.password, self.port)

        process = self.test_manager.channel_process_dict[
            self.email_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(8, len(process._args))
        self.assertEqual((self.smtp, self.sender, self.emails_to,
                          self.email_channel_id, self.email_channel_name,
                          self.username, self.password, self.port),
                         process._args)
        self.assertEqual(start_email_alerts_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_pagerduty_alerts_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.ALERTS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_pagerduty_alerts_handler(
            self.integration_key, self.pagerduty_channel_id,
            self.pagerduty_channel_name)

        process_details = self.test_manager.channel_process_dict[
            self.pagerduty_channel_id][handler_type]
        self.assertEqual(PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.pagerduty_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.integration_key,
                         process_details['integration_key'])
        self.assertEqual(self.pagerduty_channel_id,
                         process_details['channel_id'])
        self.assertEqual(self.pagerduty_channel_name,
                         process_details['channel_name'])
        self.assertEqual(ChannelTypes.PAGERDUTY.value,
                         process_details['channel_type'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.pagerduty_channel_id] = \
            self.test_channel_process_dict[self.pagerduty_channel_id]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_pagerduty_alerts_handler_creates_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.ALERTS.value

        self.test_manager._create_and_start_pagerduty_alerts_handler(
            self.integration_key, self.pagerduty_channel_id,
            self.pagerduty_channel_name)

        process = self.test_manager.channel_process_dict[
            self.pagerduty_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(3, len(process._args))
        self.assertEqual((self.integration_key, self.pagerduty_channel_id,
                          self.pagerduty_channel_name), process._args)
        self.assertEqual(start_pagerduty_alerts_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_opsgenie_alerts_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.ALERTS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_opsgenie_alerts_handler(
            self.api_key, self.eu_host, self.opsgenie_channel_id,
            self.opsgenie_channel_name)

        process_details = self.test_manager.channel_process_dict[
            self.opsgenie_channel_id][handler_type]
        self.assertEqual(OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.opsgenie_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.api_key, process_details['api_key'])
        self.assertEqual(self.opsgenie_channel_id,
                         process_details['channel_id'])
        self.assertEqual(self.opsgenie_channel_name,
                         process_details['channel_name'])
        self.assertEqual(self.eu_host, process_details['eu_host'])
        self.assertEqual(ChannelTypes.OPSGENIE.value,
                         process_details['channel_type'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.opsgenie_channel_id] = \
            self.test_channel_process_dict[self.opsgenie_channel_id]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_opsgenie_alerts_handler_creates_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.ALERTS.value

        self.test_manager._create_and_start_opsgenie_alerts_handler(
            self.api_key, self.eu_host, self.opsgenie_channel_id,
            self.opsgenie_channel_name)

        process = self.test_manager.channel_process_dict[
            self.opsgenie_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(4, len(process._args))
        self.assertEqual((self.api_key, self.eu_host, self.opsgenie_channel_id,
                          self.opsgenie_channel_name), process._args)
        self.assertEqual(start_opsgenie_alerts_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_console_alerts_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.ALERTS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_console_alerts_handler(
            self.console_channel_id, self.console_channel_name)

        process_details = self.test_manager.channel_process_dict[
            self.console_channel_id][handler_type]
        self.assertEqual(CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.console_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.console_channel_id, process_details['channel_id'])
        self.assertEqual(self.console_channel_name,
                         process_details['channel_name'])
        self.assertEqual(ChannelTypes.CONSOLE.value,
                         process_details['channel_type'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.console_channel_id] = \
            self.test_channel_process_dict[self.console_channel_id]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_console_alerts_handler_creates_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.ALERTS.value

        self.test_manager._create_and_start_console_alerts_handler(
            self.console_channel_id, self.console_channel_name)

        process = self.test_manager.channel_process_dict[
            self.console_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(2, len(process._args))
        self.assertEqual((self.console_channel_id, self.console_channel_name),
                         process._args)
        self.assertEqual(start_console_alerts_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(multiprocessing, "Process")
    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_log_alerts_handler_stores_process_correctly(
            self, mock_start, mock_process_init) -> None:
        mock_start.return_value = None
        mock_process_init.return_value = self.dummy_process1
        handler_type = ChannelHandlerTypes.ALERTS.value
        self.test_manager._channel_process_dict = copy.deepcopy(self.test_dict)

        self.test_manager._create_and_start_log_alerts_handler(
            self.log_channel_id, self.log_channel_name)

        process_details = self.test_manager.channel_process_dict[
            self.log_channel_id][handler_type]
        self.assertEqual(LOG_ALERTS_HANDLER_NAME_TEMPLATE.format(
            self.log_channel_name), process_details['component_name'])
        self.assertEqual(self.dummy_process1, process_details['process'])
        self.assertEqual(self.log_channel_id, process_details['channel_id'])
        self.assertEqual(self.log_channel_name, process_details['channel_name'])
        self.assertEqual(ChannelTypes.LOG.value,
                         process_details['channel_type'])
        expected_channel_process_dict = self.test_dict
        expected_channel_process_dict[self.log_channel_id] = \
            self.test_channel_process_dict[self.log_channel_id]
        self.assertEqual(expected_channel_process_dict,
                         self.test_manager.channel_process_dict)

    @mock.patch.object(multiprocessing.Process, "start")
    def test_create_and_start_log_alerts_handler_creates_and_start(
            self, mock_start) -> None:
        mock_start.return_value = None
        handler_type = ChannelHandlerTypes.ALERTS.value

        self.test_manager._create_and_start_log_alerts_handler(
            self.log_channel_id, self.log_channel_name)

        process = self.test_manager.channel_process_dict[
            self.log_channel_id][handler_type]['process']
        self.assertTrue(process.daemon)
        self.assertEqual(2, len(process._args))
        self.assertEqual((self.log_channel_id, self.log_channel_name),
                         process._args)
        self.assertEqual(start_log_alerts_handler, process._target)
        mock_start.assert_called_once_with()

    @mock.patch.object(ChannelsManager, "_create_and_start_log_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    def test_start_persistent_channels_creates_and_starts_CAH_if_first_time(
            self, mock_start_cah, mock_start_lah) -> None:
        mock_start_cah.return_value = None
        mock_start_lah.return_value = None
        self.test_manager._start_persistent_channels()
        mock_start_cah.assert_called_once_with(CONSOLE_CHANNEL_ID,
                                               CONSOLE_CHANNEL_NAME)

    @mock.patch.object(multiprocessing.Process, 'is_alive')
    @mock.patch.object(ChannelsManager, "_create_and_start_log_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    def test_start_persistent_channels_starts_CAH_if_not_alive(
            self, mock_start_cah, mock_start_lah, mock_is_alive) -> None:
        mock_start_cah.return_value = None
        mock_start_lah.return_value = None
        mock_is_alive.return_value = False
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        self.test_manager._start_persistent_channels()
        mock_start_cah.assert_called_once_with(CONSOLE_CHANNEL_ID,
                                               CONSOLE_CHANNEL_NAME)

    @mock.patch.object(multiprocessing.Process, 'is_alive')
    @mock.patch.object(ChannelsManager, "_create_and_start_log_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    def test_start_persistent_channels_does_not_start_CAH_if_already_running(
            self, mock_start_cah, mock_start_lah, mock_is_alive) -> None:
        mock_start_cah.return_value = None
        mock_start_lah.return_value = None
        mock_is_alive.return_value = True
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        self.test_manager._start_persistent_channels()
        mock_start_cah.assert_not_called()

    @mock.patch.object(ChannelsManager, "_create_and_start_log_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    def test_start_persistent_channels_creates_and_starts_LAH_if_first_time(
            self, mock_start_cah, mock_start_lah) -> None:
        mock_start_cah.return_value = None
        mock_start_lah.return_value = None
        self.test_manager._start_persistent_channels()
        mock_start_lah.assert_called_once_with(LOG_CHANNEL_ID, LOG_CHANNEL_NAME)

    @mock.patch.object(multiprocessing.Process, 'is_alive')
    @mock.patch.object(ChannelsManager, "_create_and_start_log_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    def test_start_persistent_channels_starts_LAH_if_not_alive(
            self, mock_start_cah, mock_start_lah, mock_is_alive) -> None:
        mock_start_cah.return_value = None
        mock_start_lah.return_value = None
        mock_is_alive.return_value = False
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        self.test_manager._start_persistent_channels()
        mock_start_lah.assert_called_once_with(LOG_CHANNEL_ID,
                                               LOG_CHANNEL_NAME)

    @mock.patch.object(multiprocessing.Process, 'is_alive')
    @mock.patch.object(ChannelsManager, "_create_and_start_log_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    def test_start_persistent_channels_does_not_start_LAH_if_already_running(
            self, mock_start_cah, mock_start_lah, mock_is_alive) -> None:
        mock_start_cah.return_value = None
        mock_start_lah.return_value = None
        mock_is_alive.return_value = True
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        self.test_manager._start_persistent_channels()
        mock_start_lah.assert_not_called()

    @parameterized.expand([('True',), ('False',), ])
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    def test_process_telegram_configs_if_new_configs_and_alerts_true(
            self, commands, mock_start_tah, mock_start_tch) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected. Note that we
        # test this for both when the telegram channel state is empty and when
        # it is not.
        mock_start_tah.return_value = None
        mock_start_tch.return_value = None

        # Test with no telegram configs in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['alerts'] = 'True'
        sent_configs[self.telegram_channel_id]['commands'] = commands
        del current_configs[ChannelTypes.TELEGRAM.value]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_telegram_configs(
            sent_configs)
        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TELEGRAM.value])
        expected_configs[self.telegram_channel_id]['commands'] = commands

        self.assertEqual(expected_configs, actual_configs)

        # Test with telegram configs already in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['alerts'] = 'True'
        sent_configs[self.telegram_channel_id]['commands'] = commands
        del current_configs[ChannelTypes.TELEGRAM.value][
            self.telegram_channel_id]
        current_configs[ChannelTypes.TELEGRAM.value][
            'Another_Telegram_Config'] = self.test_dict
        sent_configs['Another_Telegram_Config'] = self.test_dict
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_telegram_configs(
            sent_configs)
        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TELEGRAM.value])
        expected_configs['Another_Telegram_Config'] = self.test_dict
        expected_configs[self.telegram_channel_id]['commands'] = commands

        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to start the processes were done correctly.
        expected_calls = [
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 self.telegram_channel_name),
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 self.telegram_channel_name),
        ]
        actual_calls = mock_start_tah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @parameterized.expand([('True',), ('False',), ])
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    def test_process_telegram_configs_if_new_configs_and_commands_true(
            self, alerts, mock_start_tah, mock_start_tch) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected. Note that we
        # will test this for both when the telegram channel state is empty and
        # when it is not.
        mock_start_tah.return_value = None
        mock_start_tch.return_value = None

        # Test with no telegram configs in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['alerts'] = alerts
        sent_configs[self.telegram_channel_id]['commands'] = 'True'
        del current_configs[ChannelTypes.TELEGRAM.value]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_telegram_configs(
            sent_configs)
        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TELEGRAM.value])
        expected_configs[self.telegram_channel_id]['alerts'] = alerts

        self.assertEqual(expected_configs, actual_configs)

        # Test with telegram configs already in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['alerts'] = alerts
        sent_configs[self.telegram_channel_id]['commands'] = 'True'
        del current_configs[ChannelTypes.TELEGRAM.value][
            self.telegram_channel_id]
        current_configs[ChannelTypes.TELEGRAM.value][
            'Another_Telegram_Config'] = self.test_dict
        sent_configs['Another_Telegram_Config'] = self.test_dict
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_telegram_configs(
            sent_configs)
        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TELEGRAM.value])
        expected_configs['Another_Telegram_Config'] = self.test_dict
        expected_configs[self.telegram_channel_id]['alerts'] = alerts

        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to start the processes were done correctly.
        expected_calls = [
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 self.telegram_channel_name, self.test_associated_chains),
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 self.telegram_channel_name, self.test_associated_chains),
        ]
        actual_calls = mock_start_tch.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    def test_process_telegram_configs_if_new_configs_and_commands_alerts_false(
            self, mock_start_tah, mock_start_tch) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective processes were not called since both alerts and
        # commands are disabled. Note that we will test this for both when the
        # telegram channel state is empty and when it is not.
        mock_start_tah.return_value = None
        mock_start_tch.return_value = None

        # Test with no telegram configs in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['alerts'] = 'False'
        sent_configs[self.telegram_channel_id]['commands'] = 'False'
        del current_configs[ChannelTypes.TELEGRAM.value]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_telegram_configs(
            sent_configs)
        expected_configs = {}

        self.assertEqual(expected_configs, actual_configs)

        # Test with telegram configs already in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['alerts'] = 'False'
        sent_configs[self.telegram_channel_id]['commands'] = 'False'
        del current_configs[ChannelTypes.TELEGRAM.value][
            self.telegram_channel_id]
        current_configs[ChannelTypes.TELEGRAM.value][
            'Another_Telegram_Config'] = self.test_dict
        sent_configs['Another_Telegram_Config'] = self.test_dict
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_telegram_configs(
            sent_configs)
        expected_configs = {'Another_Telegram_Config': self.test_dict}

        self.assertEqual(expected_configs, actual_configs)

        # Check that no process was started.
        mock_start_tch.assert_not_called()
        mock_start_tah.assert_not_called()

    @parameterized.expand([('True',), ('False',), ])
    @mock.patch.object(multiprocessing.Process, 'terminate')
    @mock.patch.object(multiprocessing.Process, 'join')
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    def test_process_telegram_configs_if_modified_configs_and_alerts_true(
            self, commands_enabled, mock_start_tah, mock_start_tch, mock_join,
            mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # the respective process calls were done successfully. Note that we will
        # test this for both when alerts were already enabled and when they were
        # disabled
        mock_start_tah.return_value = None
        mock_start_tch.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        new_channel_name = "new_name"

        # Test with alerts currently enabled
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        sent_configs[self.telegram_channel_id]['commands'] = commands_enabled
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_confs = self.test_manager._process_telegram_configs(sent_configs)

        expected_confs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        expected_confs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        expected_confs[self.telegram_channel_id]['commands'] = commands_enabled
        self.assertEqual(expected_confs, actual_confs)
        self.assertEqual(2, len(mock_terminate.call_args_list))
        self.assertEqual(2, len(mock_join.call_args_list))
        if not commands_enabled:
            self.assertTrue(ChannelHandlerTypes.COMMANDS.value not in
                            self.test_manager.channel_process_dict[
                                self.telegram_channel_id])

        # Test with alerts not currently enabled
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        sent_configs[self.telegram_channel_id]['commands'] = commands_enabled
        current_configs[ChannelTypes.TELEGRAM.value][
            self.telegram_channel_id]['alerts'] = 'False'
        del self.test_channel_process_dict_copy[self.telegram_channel_id][
            ChannelHandlerTypes.ALERTS.value]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = \
            self.test_channel_process_dict_copy

        actual_confs = self.test_manager._process_telegram_configs(sent_configs)

        expected_confs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TELEGRAM.value])
        expected_confs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        expected_confs[self.telegram_channel_id]['commands'] = commands_enabled
        self.assertEqual(expected_confs, actual_confs)
        self.assertEqual(3, len(mock_terminate.call_args_list))
        self.assertEqual(3, len(mock_join.call_args_list))
        if not commands_enabled:
            self.assertTrue(ChannelHandlerTypes.COMMANDS.value not in
                            self.test_manager.channel_process_dict[
                                self.telegram_channel_id])

        expected_calls = [
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 new_channel_name),
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 new_channel_name),
        ]
        actual_calls = mock_start_tah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @parameterized.expand([('True',), ('False',), ])
    @mock.patch.object(multiprocessing.Process, 'terminate')
    @mock.patch.object(multiprocessing.Process, 'join')
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    def test_process_telegram_configs_if_modified_configs_and_commands_true(
            self, alerts_enabled, mock_start_tah, mock_start_tch, mock_join,
            mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # the respective process calls were done successfully. Note that we will
        # test this for both when commands were already enabled and when they
        # were disabled
        mock_start_tah.return_value = None
        mock_start_tch.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        new_channel_name = "new_name"

        # Test with commands currently enabled
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        sent_configs[self.telegram_channel_id]['alerts'] = alerts_enabled
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_confs = self.test_manager._process_telegram_configs(sent_configs)

        expected_confs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        expected_confs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        expected_confs[self.telegram_channel_id]['alerts'] = alerts_enabled
        self.assertEqual(expected_confs, actual_confs)
        self.assertEqual(2, len(mock_terminate.call_args_list))
        self.assertEqual(2, len(mock_join.call_args_list))
        if not alerts_enabled:
            self.assertTrue(ChannelHandlerTypes.ALERTS.value not in
                            self.test_manager.channel_process_dict[
                                self.telegram_channel_id])

        # Test with commands not currently enabled
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        sent_configs[self.telegram_channel_id]['alerts'] = alerts_enabled
        current_configs[ChannelTypes.TELEGRAM.value][
            self.telegram_channel_id]['commands'] = 'False'
        del self.test_channel_process_dict_copy[self.telegram_channel_id][
            ChannelHandlerTypes.COMMANDS.value]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = \
            self.test_channel_process_dict_copy

        actual_confs = self.test_manager._process_telegram_configs(sent_configs)

        expected_confs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TELEGRAM.value])
        expected_confs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        expected_confs[self.telegram_channel_id]['alerts'] = alerts_enabled
        self.assertEqual(expected_confs, actual_confs)
        self.assertEqual(3, len(mock_terminate.call_args_list))
        self.assertEqual(3, len(mock_join.call_args_list))
        if not alerts_enabled:
            self.assertTrue(ChannelHandlerTypes.ALERTS.value not in
                            self.test_manager.channel_process_dict[
                                self.telegram_channel_id])

        expected_calls = [
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 new_channel_name, self.test_associated_chains),
            call(self.bot_token, self.bot_chat_id, self.telegram_channel_id,
                 new_channel_name, self.test_associated_chains),
        ]
        actual_calls = mock_start_tch.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, 'terminate')
    @mock.patch.object(multiprocessing.Process, 'join')
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    def test_process_telegram_configs_if_modified_configs_and_cmds_alerts_false(
            self, mock_start_tah, mock_start_tch, mock_join,
            mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # the respective process calls were done successfully. Note that we will
        # test this for both when commands and alerts were already enabled and
        # when they were both disabled
        mock_start_tah.return_value = None
        mock_start_tch.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        new_channel_name = "new_name"

        # Test with alerts and commands currently enabled
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        sent_configs[self.telegram_channel_id]['alerts'] = 'False'
        sent_configs[self.telegram_channel_id]['commands'] = 'False'
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_confs = self.test_manager._process_telegram_configs(sent_configs)

        self.assertEqual({}, actual_confs)
        self.assertEqual(2, len(mock_terminate.call_args_list))
        self.assertEqual(2, len(mock_join.call_args_list))
        self.assertTrue(self.telegram_channel_id
                        not in self.test_manager._channel_process_dict)

        # Test with commands and alerts not currently enabled
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        sent_configs[self.telegram_channel_id]['channel_name'] = \
            new_channel_name
        sent_configs[self.telegram_channel_id]['alerts'] = 'False'
        sent_configs[self.telegram_channel_id]['commands'] = 'False'
        current_configs[ChannelTypes.TELEGRAM.value][
            self.telegram_channel_id]['commands'] = 'False'
        del self.test_channel_process_dict_copy[self.telegram_channel_id][
            ChannelHandlerTypes.COMMANDS.value]
        current_configs[ChannelTypes.TELEGRAM.value][
            self.telegram_channel_id]['alerts'] = 'False'
        del self.test_channel_process_dict_copy[self.telegram_channel_id][
            ChannelHandlerTypes.ALERTS.value]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = \
            self.test_channel_process_dict_copy

        actual_confs = self.test_manager._process_telegram_configs(sent_configs)

        self.assertEqual({}, actual_confs)
        self.assertEqual(2, len(mock_terminate.call_args_list))
        self.assertEqual(2, len(mock_join.call_args_list))
        self.assertTrue(self.telegram_channel_id
                        not in self.test_manager._channel_process_dict)
        mock_start_tch.assert_not_called()
        mock_start_tah.assert_not_called()

    @parameterized.expand([
        ('True', 'False'), ('False', 'True'), ('True', 'True',)
    ])
    @mock.patch.object(multiprocessing.Process, 'terminate')
    @mock.patch.object(multiprocessing.Process, 'join')
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    def test_process_telegram_configs_if_removed_configs(
            self, cmds_running, alerts_running, mock_tah, mock_tch, mock_join,
            mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # the respective process calls were done successfully. We will perform
        # this test for when both cmds and alert handlers are running and when
        # one of them is running. For the configs to be removed at least one of
        # the handlers must be running.
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_tah.return_value = None
        mock_tch.return_value = None

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.TELEGRAM.value][
            'Another_Telegram_Config'] = self.test_dict
        if not cmds_running:
            current_configs[ChannelTypes.TELEGRAM.value][
                self.telegram_channel_id]['commands'] = 'False'
            del self.test_channel_process_dict[self.telegram_channel_id][
                ChannelHandlerTypes.COMMANDS.value]
        if not alerts_running:
            current_configs[ChannelTypes.TELEGRAM.value][
                self.telegram_channel_id]['alerts'] = 'False'
            del self.test_channel_process_dict[self.telegram_channel_id][
                ChannelHandlerTypes.ALERTS.value]
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.TELEGRAM.value])
        del sent_configs[self.telegram_channel_id]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_confs = self.test_manager._process_telegram_configs(sent_configs)

        expected_confs = {'Another_Telegram_Config': self.test_dict}
        self.assertEqual(expected_confs, actual_confs)
        self.assertTrue(self.telegram_channel_id not in
                        self.test_manager._channel_process_dict)
        if alerts_running and cmds_running:
            self.assertEqual(2, len(mock_join.call_args_list))
            self.assertEqual(2, len(mock_terminate.call_args_list))
        else:
            mock_join.assert_called_once()
            mock_terminate.assert_called_once()
        mock_tah.assert_not_called()
        mock_tch.assert_not_called()

    @mock.patch.object(ChannelsManager,
                       "_create_and_start_twilio_alerts_handler")
    def test_process_twilio_configs_if_new_configs(self,
                                                   mock_start_tah) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected. Note that we
        # test this for both when the twilio channel state is empty and when
        # it is not.
        mock_start_tah.return_value = None

        # Test with no twilio configs in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.TWILIO.value])
        del current_configs[ChannelTypes.TWILIO.value]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_twilio_configs(sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TWILIO.value])
        self.assertEqual(expected_configs, actual_configs)

        # Test with twilio configs already in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.TWILIO.value][
            'Another_Twilio_Config'] = self.test_dict
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.TWILIO.value])
        del current_configs[ChannelTypes.TWILIO.value][self.twilio_channel_id]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_twilio_configs(sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TWILIO.value])
        expected_configs['Another_Twilio_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to start the processes were done correctly.
        expected_calls = [
            call(self.account_sid, self.auth_token, self.twilio_channel_id,
                 self.twilio_channel_name, self.call_from, self.call_to,
                 self.twiml, self.twiml_is_url),
            call(self.account_sid, self.auth_token, self.twilio_channel_id,
                 self.twilio_channel_name, self.call_from, self.call_to,
                 self.twiml, self.twiml_is_url),
        ]
        actual_calls = mock_start_tah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_twilio_alerts_handler")
    def test_process_twilio_configs_if_modified_configs(
            self, mock_start_tah, mock_join, mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_start_tah.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        new_channel_name = "new_name"

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.TWILIO.value][
            'Another_Twilio_Config'] = self.test_dict
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.TWILIO.value])
        sent_configs[self.twilio_channel_id]['channel_name'] = new_channel_name
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_twilio_configs(sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.TWILIO.value])
        expected_configs[self.twilio_channel_id][
            'channel_name'] = new_channel_name
        expected_configs['Another_Twilio_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to restart the process was done correctly.
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        expected_calls = [
            call(self.account_sid, self.auth_token, self.twilio_channel_id,
                 new_channel_name, self.call_from, self.call_to, self.twiml,
                 self.twiml_is_url),
        ]
        actual_calls = mock_start_tah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_twilio_alerts_handler")
    def test_process_twilio_configs_if_removed_configs(
            self, mock_tah, mock_join, mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_tah.return_value = None

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.TWILIO.value][
            'Another_Twilio_Config'] = self.test_dict
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.TWILIO.value])
        del sent_configs[self.twilio_channel_id]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_twilio_configs(sent_configs)

        expected_configs = {'Another_Twilio_Config': self.test_dict}
        self.assertEqual(expected_configs, actual_configs)
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        mock_tah.assert_not_called()

    @mock.patch.object(ChannelsManager,
                       "_create_and_start_pagerduty_alerts_handler")
    def test_process_pagerduty_configs_if_new_configs(self,
                                                      mock_start_pah) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected. Note that we
        # test this for both when the pagerduty channel state is empty and when
        # it is not.
        mock_start_pah.return_value = None

        # Test with no pagerduty configs in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.PAGERDUTY.value])
        del current_configs[ChannelTypes.PAGERDUTY.value]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_pagerduty_configs(
            sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.PAGERDUTY.value])
        self.assertEqual(expected_configs, actual_configs)

        # Test with pagerduty configs already in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.PAGERDUTY.value][
            'Another_PagerDuty_Config'] = self.test_dict
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.PAGERDUTY.value])
        del current_configs[ChannelTypes.PAGERDUTY.value][
            self.pagerduty_channel_id]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_pagerduty_configs(
            sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.PAGERDUTY.value])
        expected_configs['Another_PagerDuty_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to start the processes were done correctly.
        expected_calls = [
            call(self.integration_key, self.pagerduty_channel_id,
                 self.pagerduty_channel_name),
            call(self.integration_key, self.pagerduty_channel_id,
                 self.pagerduty_channel_name),
        ]
        actual_calls = mock_start_pah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_pagerduty_alerts_handler")
    def test_process_pagerduty_configs_if_modified_configs(
            self, mock_start_pah, mock_join, mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_start_pah.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        new_channel_name = "new_name"

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.PAGERDUTY.value][
            'Another_PagerDuty_Config'] = self.test_dict
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.PAGERDUTY.value])
        sent_configs[self.pagerduty_channel_id][
            'channel_name'] = new_channel_name
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_pagerduty_configs(
            sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.PAGERDUTY.value])
        expected_configs[self.pagerduty_channel_id][
            'channel_name'] = new_channel_name
        expected_configs['Another_PagerDuty_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to restart the process was done correctly.
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        expected_calls = [
            call(self.integration_key, self.pagerduty_channel_id,
                 new_channel_name),
        ]
        actual_calls = mock_start_pah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_pagerduty_alerts_handler")
    def test_process_pagerduty_configs_if_removed_configs(
            self, mock_pah, mock_join, mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_pah.return_value = None

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.PAGERDUTY.value][
            'Another_PagerDuty_Config'] = self.test_dict
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.PAGERDUTY.value])
        del sent_configs[self.pagerduty_channel_id]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_pagerduty_configs(
            sent_configs)

        expected_configs = {'Another_PagerDuty_Config': self.test_dict}
        self.assertEqual(expected_configs, actual_configs)
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        mock_pah.assert_not_called()

    @mock.patch.object(ChannelsManager,
                       "_create_and_start_email_alerts_handler")
    def test_process_email_configs_if_new_configs(self, mock_start_eah) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected. Note that we
        # test this for both when the email channel state is empty and when it
        # is not.
        mock_start_eah.return_value = None

        # Test with no email configs in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.EMAIL.value])
        del current_configs[ChannelTypes.EMAIL.value]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_email_configs(sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.EMAIL.value])
        self.assertEqual(expected_configs, actual_configs)

        # Test with email configs already in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.EMAIL.value][
            'Another_Email_Config'] = self.test_dict
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.EMAIL.value])
        del current_configs[ChannelTypes.EMAIL.value][self.email_channel_id]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_email_configs(sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.EMAIL.value])
        expected_configs['Another_Email_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to start the processes were done correctly.
        expected_calls = [
            call(self.smtp, self.sender, self.emails_to, self.email_channel_id,
                 self.email_channel_name, self.username, self.password,
                 self.port),
            call(self.smtp, self.sender, self.emails_to, self.email_channel_id,
                 self.email_channel_name, self.username, self.password,
                 self.port),
        ]
        actual_calls = mock_start_eah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_email_alerts_handler")
    def test_process_email_configs_if_modified_configs(
            self, mock_start_eah, mock_join, mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_start_eah.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        new_channel_name = "new_name"

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.EMAIL.value][
            'Another_Email_Config'] = self.test_dict
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.EMAIL.value])
        sent_configs[self.email_channel_id]['channel_name'] = new_channel_name
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_email_configs(sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.EMAIL.value])
        expected_configs[self.email_channel_id][
            'channel_name'] = new_channel_name
        expected_configs['Another_Email_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to restart the process was done correctly.
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        expected_calls = [
            call(self.smtp, self.sender, self.emails_to, self.email_channel_id,
                 new_channel_name, self.username, self.password, self.port),
        ]
        actual_calls = mock_start_eah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_email_alerts_handler")
    def test_process_email_configs_if_removed_configs(self, mock_eah, mock_join,
                                                      mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_eah.return_value = None

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.EMAIL.value][
            'Another_Email_Config'] = self.test_dict
        sent_configs = copy.deepcopy(current_configs[ChannelTypes.EMAIL.value])
        del sent_configs[self.email_channel_id]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_email_configs(sent_configs)

        expected_configs = {'Another_Email_Config': self.test_dict}
        self.assertEqual(expected_configs, actual_configs)
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        mock_eah.assert_not_called()

    @mock.patch.object(ChannelsManager,
                       "_create_and_start_opsgenie_alerts_handler")
    def test_process_opsgenie_configs_if_new_configs(self,
                                                     mock_start_oah) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected. Note that we
        # test this for both when the opsgenie channel state is empty and when
        # it is not.
        mock_start_oah.return_value = None

        # Test with no opsgenie configs in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.OPSGENIE.value])
        del current_configs[ChannelTypes.OPSGENIE.value]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_opsgenie_configs(
            sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.OPSGENIE.value])
        self.assertEqual(expected_configs, actual_configs)

        # Test with opsgenie configs already in the state
        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.OPSGENIE.value][
            'Another_Opsgenie_Config'] = self.test_dict
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.OPSGENIE.value])
        del current_configs[ChannelTypes.OPSGENIE.value][
            self.opsgenie_channel_id]
        self.test_manager._channel_configs = current_configs

        actual_configs = self.test_manager._process_opsgenie_configs(
            sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.OPSGENIE.value])
        expected_configs['Another_Opsgenie_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to start the processes were done correctly.
        expected_calls = [
            call(self.api_key, self.eu_host, self.opsgenie_channel_id,
                 self.opsgenie_channel_name),
            call(self.api_key, self.eu_host, self.opsgenie_channel_id,
                 self.opsgenie_channel_name),
        ]
        actual_calls = mock_start_oah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_opsgenie_alerts_handler")
    def test_process_opsgenie_configs_if_modified_configs(
            self, mock_start_oah, mock_join, mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_start_oah.return_value = None
        mock_join.return_value = None
        mock_terminate.return_value = None
        new_channel_name = "new_name"

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.OPSGENIE.value][
            'Another_Opsgenie_Config'] = self.test_dict
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.OPSGENIE.value])
        sent_configs[self.opsgenie_channel_id][
            'channel_name'] = new_channel_name
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_opsgenie_configs(
            sent_configs)

        expected_configs = copy.deepcopy(
            self.test_channel_configs[ChannelTypes.OPSGENIE.value])
        expected_configs[self.opsgenie_channel_id][
            'channel_name'] = new_channel_name
        expected_configs['Another_Opsgenie_Config'] = self.test_dict
        self.assertEqual(expected_configs, actual_configs)

        # Check that the calls to restart the process was done correctly.
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        expected_calls = [
            call(self.api_key, self.eu_host, self.opsgenie_channel_id,
                 new_channel_name),
        ]
        actual_calls = mock_start_oah.call_args_list
        self.assertEqual(expected_calls, actual_calls)

    @mock.patch.object(multiprocessing.Process, "terminate")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_opsgenie_alerts_handler")
    def test_process_opsgenie_configs_if_removed_configs(
            self, mock_oah, mock_join, mock_terminate) -> None:
        # In this test we will check that the configs are correctly returned and
        # that the respective process calls were done as expected.
        mock_join.return_value = None
        mock_terminate.return_value = None
        mock_oah.return_value = None

        current_configs = copy.deepcopy(self.test_channel_configs)
        current_configs[ChannelTypes.OPSGENIE.value][
            'Another_Opsgenie_Config'] = self.test_dict
        sent_configs = copy.deepcopy(
            current_configs[ChannelTypes.OPSGENIE.value])
        del sent_configs[self.opsgenie_channel_id]
        self.test_manager._channel_configs = current_configs
        self.test_manager._channel_process_dict = self.test_channel_process_dict

        actual_configs = self.test_manager._process_opsgenie_configs(
            sent_configs)

        expected_configs = {'Another_Opsgenie_Config': self.test_dict}
        self.assertEqual(expected_configs, actual_configs)
        mock_terminate.assert_called_once()
        mock_join.assert_called_once()
        mock_oah.assert_not_called()

    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(ChannelsManager, "_process_telegram_configs")
    @mock.patch.object(ChannelsManager, "_process_twilio_configs")
    @mock.patch.object(ChannelsManager, "_process_email_configs")
    @mock.patch.object(ChannelsManager, "_process_pagerduty_configs")
    @mock.patch.object(ChannelsManager, "_process_opsgenie_configs")
    def test_process_configs_does_not_process_if_bad_routing_key(
            self, mock_opsgenie, mock_pagerduty, mock_email, mock_twilio,
            mock_telegram, mock_ack) -> None:
        mock_ack.return_value = None
        mock_pagerduty.return_value = None
        mock_opsgenie.return_value = None
        mock_telegram.return_value = None
        mock_twilio.return_value = None
        mock_email.return_value = None
        try:
            # Must create a connection so that the blocking channel is passed
            connect_to_rabbit(self.test_manager.rabbitmq)
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key='invalid_routing_key')
            body = json.dumps(self.test_dict)
            properties = pika.spec.BasicProperties()

            self.test_manager._process_configs(blocking_channel, method,
                                               properties, body)

            mock_opsgenie.assert_not_called()
            mock_pagerduty.assert_not_called()
            mock_email.assert_not_called()
            mock_twilio.assert_not_called()
            mock_telegram.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_ack.assert_called_once()

    @parameterized.expand([
        ('channels.telegram_config',),
        ('channels.twilio_config',),
        ('channels.email_config',),
        ('channels.opsgenie_config',),
        ('channels.pagerduty_config',),
    ])
    @mock.patch.object(RabbitMQApi, "basic_ack")
    @mock.patch.object(ChannelsManager, "_process_telegram_configs")
    @mock.patch.object(ChannelsManager, "_process_twilio_configs")
    @mock.patch.object(ChannelsManager, "_process_email_configs")
    @mock.patch.object(ChannelsManager, "_process_pagerduty_configs")
    @mock.patch.object(ChannelsManager, "_process_opsgenie_configs")
    def test_process_configs_stores_configs_in_state_correctly(
            self, routing_key, mock_opsgenie, mock_pagerduty, mock_email,
            mock_twilio, mock_telegram, mock_ack) -> None:
        mock_ack.return_value = None
        mock_pagerduty.return_value = self.test_dict \
            if routing_key == 'channels.pagerduty_config' else None
        mock_opsgenie.return_value = self.test_dict \
            if routing_key == 'channels.opsgenie_config' else None
        mock_telegram.return_value = self.test_dict \
            if routing_key == 'channels.telegram_config' else None
        mock_twilio.return_value = self.test_dict \
            if routing_key == 'channels.twilio_config' else None
        mock_email.return_value = self.test_dict \
            if routing_key == 'channels.email_config' else None
        try:
            # Must create a connection so that the blocking channel is passed
            connect_to_rabbit(self.test_manager.rabbitmq)
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=routing_key)
            body = json.dumps(self.test_dict)
            properties = pika.spec.BasicProperties()
            self.test_manager._channel_configs = self.test_channel_configs

            self.test_manager._process_configs(blocking_channel, method,
                                               properties, body)

            expected_configs = copy.deepcopy(self.test_channel_configs)
            if routing_key == 'channels.telegram_config':
                expected_configs[ChannelTypes.TELEGRAM.value] = self.test_dict
                self.assertEqual(expected_configs,
                                 self.test_manager.channel_configs)
                mock_opsgenie.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_email.assert_not_called()
                mock_twilio.assert_not_called()
            elif routing_key == 'channels.twilio_config':
                expected_configs[ChannelTypes.TWILIO.value] = self.test_dict
                self.assertEqual(expected_configs,
                                 self.test_manager.channel_configs)
                mock_opsgenie.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_email.assert_not_called()
                mock_telegram.assert_not_called()
            elif routing_key == 'channels.email_config':
                expected_configs[ChannelTypes.EMAIL.value] = self.test_dict
                self.assertEqual(expected_configs,
                                 self.test_manager.channel_configs)
                mock_opsgenie.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_telegram.assert_not_called()
                mock_twilio.assert_not_called()
            elif routing_key == 'channels.pagerduty_config':
                expected_configs[ChannelTypes.PAGERDUTY.value] = self.test_dict
                self.assertEqual(expected_configs,
                                 self.test_manager.channel_configs)
                mock_opsgenie.assert_not_called()
                mock_telegram.assert_not_called()
                mock_email.assert_not_called()
                mock_twilio.assert_not_called()
            elif routing_key == 'channels.opsgenie_config':
                expected_configs[ChannelTypes.OPSGENIE.value] = self.test_dict
                self.assertEqual(expected_configs,
                                 self.test_manager.channel_configs)
                mock_telegram.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_email.assert_not_called()
                mock_twilio.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

        mock_ack.assert_called_once()

    @freeze_time("2012-01-01")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(ChannelsManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb_if_all_handler_processes_are_alive(
            self, mock_send_hb, mock_is_alive) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat. The actual sending was already tested above.
        mock_send_hb.return_value = None
        mock_is_alive.return_value = True
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            expected_hb = {
                'component_name': self.manager_name,
                'running_processes': [
                    self.test_channel_process_dict[channel_id][handler][
                        'component_name']
                    for channel_id in self.test_channel_process_dict
                    for handler in self.test_channel_process_dict[channel_id]
                ],
                'dead_processes': [],
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @freeze_time("2012-01-01")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_twilio_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_email_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_pagerduty_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_opsgenie_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_log_alerts_handler")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(ChannelsManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb_if_all_handler_processes_are_dead(
            self, mock_send_hb, mock_is_alive, mock_join, mock_log,
            mock_console, mock_opsgenie, mock_pagerduty, mock_email,
            mock_twilio, mock_telegram_cmds, mock_telegram_alerts) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat. The actual sending was already tested above.
        mock_send_hb.return_value = None
        mock_is_alive.return_value = False
        mock_join.return_value = None
        mock_log.return_value = None
        mock_console.return_value = None
        mock_opsgenie.return_value = None
        mock_pagerduty.return_value = None
        mock_email.return_value = None
        mock_twilio.return_value = None
        mock_telegram_cmds.return_value = None
        mock_telegram_alerts.return_value = None
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            expected_hb = {
                'component_name': self.manager_name,
                'dead_processes': [
                    self.test_channel_process_dict[channel_id][handler][
                        'component_name']
                    for channel_id in self.test_channel_process_dict
                    for handler in self.test_channel_process_dict[channel_id]
                ],
                'running_processes': [],
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ([False, True, True, True, True, True, True, True],
         'Telegram Alerts Handler (test_telegram_channel)'),
        ([True, False, True, True, True, True, True, True],
         'Telegram Commands Handler (test_telegram_channel)'),
        ([True, True, False, True, True, True, True, True],
         'Twilio Alerts Handler (test_twilio_channel)'),
        ([True, True, True, False, True, True, True, True],
         'Email Alerts Handler (test_email_channel)'),
        ([True, True, True, True, False, True, True, True],
         'PagerDuty Alerts Handler (test_pagerduty_channel)'),
        ([True, True, True, True, True, False, True, True],
         'Opsgenie Alerts Handler (test_opsgenie_channel)'),
        ([True, True, True, True, True, True, False, True],
         'Console Alerts Handler (CONSOLE)'),
        ([True, True, True, True, True, True, True, False],
         'Log Alerts Handler (LOG)'),
    ])
    @freeze_time("2012-01-01")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_twilio_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_email_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_pagerduty_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_opsgenie_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_log_alerts_handler")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(ChannelsManager, "_send_heartbeat")
    def test_process_ping_sends_a_valid_hb_if_an_alerts_handler_is_dead(
            self, is_alive_side_effect, dead_process, mock_send_hb,
            mock_is_alive, mock_join, mock_log, mock_console, mock_opsgenie,
            mock_pagerduty, mock_email, mock_twilio, mock_telegram_cmds,
            mock_telegram_alerts) -> None:
        # We will perform this test by checking that send_hb is called with the
        # correct heartbeat. The actual sending was already tested above.
        mock_send_hb.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        mock_join.return_value = None
        mock_log.return_value = None
        mock_console.return_value = None
        mock_opsgenie.return_value = None
        mock_pagerduty.return_value = None
        mock_email.return_value = None
        mock_twilio.return_value = None
        mock_telegram_cmds.return_value = None
        mock_telegram_alerts.return_value = None
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
            expected_hb = {
                'component_name': self.manager_name,
                'running_processes': [
                    self.test_channel_process_dict[channel_id][handler][
                        'component_name']
                    for channel_id in self.test_channel_process_dict
                    for handler in self.test_channel_process_dict[channel_id]
                    if self.test_channel_process_dict[channel_id][handler][
                           'component_name'] != dead_process
                ],
                'dead_processes': [dead_process],
                'timestamp': datetime.now().timestamp()
            }
            mock_send_hb.assert_called_once_with(expected_hb)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        ([False, True, True, True, True, True, True, True],
         'mock_telegram_alerts',),
        ([True, False, True, True, True, True, True, True],
         'mock_telegram_cmds',),
        ([True, True, False, True, True, True, True, True], 'mock_twilio',),
        ([True, True, True, False, True, True, True, True], 'mock_email',),
        ([True, True, True, True, False, True, True, True], 'mock_pagerduty',),
        ([True, True, True, True, True, False, True, True], 'mock_opsgenie',),
        ([True, True, True, True, True, True, False, True], 'mock_console',),
        ([True, True, True, True, True, True, True, False], 'mock_log',),
    ])
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_telegram_cmds_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_twilio_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_email_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_pagerduty_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_opsgenie_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_console_alerts_handler")
    @mock.patch.object(ChannelsManager,
                       "_create_and_start_log_alerts_handler")
    @mock.patch.object(multiprocessing.Process, "join")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    @mock.patch.object(ChannelsManager, "_send_heartbeat")
    def test_process_ping_restarts_a_dead_handler(
            self, is_alive_side_effect, dead_handler_start_mock, mock_send_hb,
            mock_is_alive, mock_join, mock_log, mock_console, mock_opsgenie,
            mock_pagerduty, mock_email, mock_twilio, mock_telegram_cmds,
            mock_telegram_alerts) -> None:
        # We will perform this test by checking that the dead handler's create
        # function was called correctly, and the other handler's create
        # functions were not called
        mock_send_hb.return_value = None
        mock_is_alive.side_effect = is_alive_side_effect
        mock_join.return_value = None
        mock_log.return_value = None
        mock_console.return_value = None
        mock_opsgenie.return_value = None
        mock_pagerduty.return_value = None
        mock_email.return_value = None
        mock_twilio.return_value = None
        mock_telegram_cmds.return_value = None
        mock_telegram_alerts.return_value = None
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            if dead_handler_start_mock == 'mock_telegram_alerts':
                process_details = self.test_channel_process_dict[
                    self.telegram_channel_id][ChannelHandlerTypes.ALERTS.value]
                mock_telegram_alerts.assert_called_once_with(
                    process_details['bot_token'],
                    process_details['bot_chat_id'],
                    process_details['channel_id'],
                    process_details['channel_name'])
                mock_telegram_cmds.assert_not_called()
                mock_twilio.assert_not_called()
                mock_email.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_opsgenie.assert_not_called()
                mock_console.assert_not_called()
                mock_log.assert_not_called()
            elif dead_handler_start_mock == 'mock_telegram_cmds':
                process_details = self.test_channel_process_dict[
                    self.telegram_channel_id][
                    ChannelHandlerTypes.COMMANDS.value]
                mock_telegram_cmds.assert_called_once_with(
                    process_details['bot_token'],
                    process_details['bot_chat_id'],
                    process_details['channel_id'],
                    process_details['channel_name'],
                    process_details['associated_chains'])
                mock_telegram_alerts.assert_not_called()
                mock_twilio.assert_not_called()
                mock_email.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_opsgenie.assert_not_called()
                mock_console.assert_not_called()
                mock_log.assert_not_called()
            elif dead_handler_start_mock == 'mock_twilio':
                process_details = self.test_channel_process_dict[
                    self.twilio_channel_id][ChannelHandlerTypes.ALERTS.value]
                mock_twilio.assert_called_once_with(
                    process_details['account_sid'],
                    process_details['auth_token'],
                    process_details['channel_id'],
                    process_details['channel_name'],
                    process_details['call_from'], process_details['call_to'],
                    process_details['twiml'], process_details['twiml_is_url'])
                mock_telegram_cmds.assert_not_called()
                mock_telegram_alerts.assert_not_called()
                mock_email.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_opsgenie.assert_not_called()
                mock_console.assert_not_called()
                mock_log.assert_not_called()
            elif dead_handler_start_mock == 'mock_email':
                process_details = self.test_channel_process_dict[
                    self.email_channel_id][ChannelHandlerTypes.ALERTS.value]
                mock_email.assert_called_once_with(
                    process_details['smtp'], process_details['email_from'],
                    process_details['emails_to'], process_details['channel_id'],
                    process_details['channel_name'],
                    process_details['username'], process_details['password'],
                    process_details['port'])
                mock_telegram_cmds.assert_not_called()
                mock_twilio.assert_not_called()
                mock_telegram_alerts.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_opsgenie.assert_not_called()
                mock_console.assert_not_called()
                mock_log.assert_not_called()
            elif dead_handler_start_mock == 'mock_pagerduty':
                process_details = self.test_channel_process_dict[
                    self.pagerduty_channel_id][ChannelHandlerTypes.ALERTS.value]
                mock_pagerduty.assert_called_once_with(
                    process_details['integration_key'],
                    process_details['channel_id'],
                    process_details['channel_name'])
                mock_telegram_cmds.assert_not_called()
                mock_twilio.assert_not_called()
                mock_email.assert_not_called()
                mock_telegram_alerts.assert_not_called()
                mock_opsgenie.assert_not_called()
                mock_console.assert_not_called()
                mock_log.assert_not_called()
            elif dead_handler_start_mock == 'mock_opsgenie':
                process_details = self.test_channel_process_dict[
                    self.opsgenie_channel_id][ChannelHandlerTypes.ALERTS.value]
                mock_opsgenie.assert_called_once_with(
                    process_details['api_key'], process_details['eu_host'],
                    process_details['channel_id'],
                    process_details['channel_name'], )
                mock_telegram_cmds.assert_not_called()
                mock_twilio.assert_not_called()
                mock_email.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_telegram_alerts.assert_not_called()
                mock_console.assert_not_called()
                mock_log.assert_not_called()
            elif dead_handler_start_mock == 'mock_console':
                process_details = self.test_channel_process_dict[
                    self.console_channel_id][ChannelHandlerTypes.ALERTS.value]
                mock_console.assert_called_once_with(
                    process_details['channel_id'],
                    process_details['channel_name'])
                mock_telegram_cmds.assert_not_called()
                mock_twilio.assert_not_called()
                mock_email.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_opsgenie.assert_not_called()
                mock_telegram_alerts.assert_not_called()
                mock_log.assert_not_called()
            elif dead_handler_start_mock == 'mock_log':
                process_details = self.test_channel_process_dict[
                    self.log_channel_id][ChannelHandlerTypes.ALERTS.value]
                mock_log.assert_called_once_with(
                    process_details['channel_id'],
                    process_details['channel_name'])
                mock_telegram_cmds.assert_not_called()
                mock_twilio.assert_not_called()
                mock_email.assert_not_called()
                mock_pagerduty.assert_not_called()
                mock_opsgenie.assert_not_called()
                mock_console.assert_not_called()
                mock_telegram_alerts.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(ChannelsManager, "_send_heartbeat")
    @mock.patch.object(multiprocessing.Process, "is_alive")
    def test_process_ping_does_not_send_hb_if_hb_processing_fails(
            self, mock_is_alive, mock_send_hb) -> None:
        # We will perform this test by checking that _send_heartbeat is not
        # called. Note we will generate an exception from is_alive
        mock_is_alive.side_effect = self.test_exception
        mock_send_hb.return_value = None
        self.test_manager._channel_process_dict = self.test_channel_process_dict
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)

            mock_send_hb.assert_not_called()
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @mock.patch.object(ChannelsManager, "_send_heartbeat")
    def test_proc_ping_send_hb_does_not_raise_msg_not_del_exce_if_hb_not_routed(
            self, mock_send_hb) -> None:
        # This test would fail if a msg not del excep is raised, as it is not
        # caught in the test.
        mock_send_hb.side_effect = MessageWasNotDeliveredException('test')
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.test_manager._process_ping(blocking_channel, method,
                                            properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))

    @parameterized.expand([
        (AMQPConnectionError, AMQPConnectionError('test'),),
        (AMQPChannelError, AMQPChannelError('test'),),
        (Exception, Exception('test'),),
    ])
    @mock.patch.object(ChannelsManager, "_send_heartbeat")
    def test_process_ping_raises_error_if_raised_by_send_heartbeat(
            self, exception_class, exception_instance,
            mock_send_heartbeat) -> None:
        # For this test we will check for channel, connection and unexpected
        # errors.
        mock_send_heartbeat.side_effect = exception_instance
        try:
            # Some of the variables below are needed as parameters for the
            # process_ping function
            self.test_manager._initialise_rabbitmq()
            blocking_channel = self.test_manager.rabbitmq.channel
            method = pika.spec.Basic.Deliver(routing_key=PING_ROUTING_KEY)
            body = 'ping'
            properties = pika.spec.BasicProperties()

            self.assertRaises(
                exception_class, self.test_manager._process_ping,
                blocking_channel, method, properties, body)
        except Exception as e:
            self.fail("Test failed: {}".format(e))
