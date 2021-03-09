import json
import logging
import multiprocessing
import unittest
from datetime import timedelta, datetime
from unittest import mock

import pika

from src.channels_manager.handlers.starters import (
    start_telegram_alerts_handler, start_telegram_commands_handler,
    start_twilio_alerts_handler, start_email_alerts_handler,
    start_pagerduty_alerts_handler, start_opsgenie_alerts_handler,
    start_console_alerts_handler, start_log_alerts_handler)
from src.channels_manager.manager import (ChannelsManager,
                                          CHANNELS_MANAGER_INPUT_QUEUE,
                                          CHANNELS_MANAGER_HB_ROUTING_KEY,
                                          CHANNELS_MANAGER_CONFIG_ROUTING_KEY)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.constants import (HEALTH_CHECK_EXCHANGE,
                                 CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE,
                                 TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE,
                                 TWILIO_ALERTS_HANDLER_NAME_TEMPLATE,
                                 EMAIL_ALERTS_HANDLER_NAME_TEMPLATE,
                                 PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE,
                                 OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE,
                                 CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE,
                                 LOG_ALERTS_HANDLER_NAME_TEMPLATE)
from src.utils.exceptions import PANICException
from src.utils.types import ChannelHandlerTypes, ChannelTypes
from test.utils.utils import infinite_fn


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
        self.twiml = '<Response><Reject/></Response>'
        self.twiml_is_url = False
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
        self.opsgenie_channel_name = 'test_opgenie_channel'
        self.opsgenie_channel_id = 'test_opsgenie_id12345'
        self.eu_host = True
        self.console_channel_name = 'test_console_channel'
        self.console_channel_id = 'test_console1234'
        self.log_channel_name = 'test_logger_channel'
        self.log_channel_id = 'test_logger1234'

    def tearDown(self) -> None:
        # Delete any queues and exchanges which are common across many tests
        try:
            self.test_manager.rabbitmq.connect()

            # Declare them before just in case there are tests which do not
            # use these queues and exchanges
            self.test_manager.rabbitmq.queue_declare(
                queue=self.test_queue_name, durable=True, exclusive=False,
                auto_delete=False, passive=False
            )
            self.test_manager.rabbitmq.queue_declare(
                CHANNELS_MANAGER_INPUT_QUEUE, False, True, False, False)
            self.test_manager.rabbitmq.queue_declare(
                CHANNELS_MANAGER_CONFIGS_QUEUE_NAME, False, True, False, False)
            self.test_manager.rabbitmq.exchange_declare(
                HEALTH_CHECK_EXCHANGE, 'topic', False, True, False, False)
            self.test_manager.rabbitmq.exchange_declare(
                CONFIG_EXCHANGE, 'topic', False, True, False, False)

            self.test_manager.rabbitmq.queue_purge(self.test_queue_name)
            self.test_manager.rabbitmq.queue_purge(CHANNELS_MANAGER_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_purge(
                CHANNELS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.queue_delete(self.test_queue_name)
            self.test_manager.rabbitmq.queue_delete(
                CHANNELS_MANAGER_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                CHANNELS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.test_manager.rabbitmq.disconnect()
        except Exception as e:
            print("Deletion of queues and exchanges failed: {}".format(e))

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
            self.rabbitmq.connect()
            self.test_manager.rabbitmq.queue_delete(
                CHANNELS_MANAGER_INPUT_QUEUE)
            self.test_manager.rabbitmq.queue_delete(
                CHANNELS_MANAGER_CONFIGS_QUEUE_NAME)
            self.test_manager.rabbitmq.exchange_delete(HEALTH_CHECK_EXCHANGE)
            self.test_manager.rabbitmq.exchange_delete(CONFIG_EXCHANGE)
            self.rabbitmq.disconnect()

            self.test_manager._initialise_rabbitmq()

            # Perform checks that the connection has been opened, marked as open
            # and that the delivery confirmation variable is set.
            self.assertTrue(self.test_manager.rabbitmq.is_connected)
            self.assertTrue(self.test_manager.rabbitmq.connection.is_open)
            self.assertTrue(
                self.test_manager.rabbitmq.channel._delivery_confirmation)

            # Check whether the exchanges and queues have been creating by
            # sending messages with the same routing keys as for the queues. We
            # will also check if the size of the queues are 0 to confirm that
            # basic_consume was called (it will store the msg in the component
            # memory immediately). If one of the exchanges or queues is not
            # created, then either an exception will be thrown or the queue size
            # would be 1. Note when deleting the exchanges in the beginning we
            # also released every binding, hence there is no other queue binded
            # with the same routing key to any exchange at this point.
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=HEALTH_CHECK_EXCHANGE,
                routing_key=CHANNELS_MANAGER_HB_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)
            self.test_manager.rabbitmq.basic_publish_confirm(
                exchange=CONFIG_EXCHANGE,
                routing_key=CHANNELS_MANAGER_CONFIG_ROUTING_KEY,
                body=self.test_data_str, is_body_dict=False,
                properties=pika.BasicProperties(delivery_mode=2),
                mandatory=True)

            # Re-declare queues to get the number of messages
            input_queue_res = self.test_manager.rabbitmq.queue_declare(
                CHANNELS_MANAGER_INPUT_QUEUE, False, True, False, False)
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
                routing_key='heartbeat.manager')
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
