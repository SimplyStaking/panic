import copy
import json
import logging
import multiprocessing
import sys
from datetime import datetime
from types import FrameType
from typing import Dict, List, Optional

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.abstract.publisher_subscriber import PublisherSubscriberComponent
from src.channels_manager.handlers.starters import (
    start_telegram_alerts_handler, start_telegram_commands_handler,
    start_twilio_alerts_handler, start_console_alerts_handler,
    start_log_alerts_handler, start_email_alerts_handler,
    start_pagerduty_alerts_handler, start_opsgenie_alerts_handler)
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.configs import (get_newly_added_configs, get_modified_configs,
                               get_removed_configs)
from src.utils.constants import (HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE,
                                 CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                 TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE,
                                 TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE,
                                 TWILIO_ALERTS_HANDLER_NAME_TEMPLATE,
                                 EMAIL_ALERTS_HANDLER_NAME_TEMPLATE,
                                 PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE,
                                 OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE,
                                 CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE,
                                 LOG_ALERTS_HANDLER_NAME_TEMPLATE,
                                 CONSOLE_CHANNEL_ID, CONSOLE_CHANNEL_NAME,
                                 LOG_CHANNEL_ID, LOG_CHANNEL_NAME)
from src.utils.exceptions import MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import (str_to_bool, ChannelTypes, ChannelHandlerTypes,
                             convert_to_int_if_not_none_and_not_empty_str)

_CHANNELS_MANAGER_INPUT_QUEUE = 'channels_manager_ping_queue'
_CHANNELS_MANAGER_HB_ROUTING_KEY = 'ping'
_CHANNELS_MANAGER_CONFIG_ROUTING_KEY = 'channels.*'


class ChannelsManager(PublisherSubscriberComponent):
    def __init__(self, logger: logging.Logger, name: str,
                 rabbitmq: RabbitMQApi) -> None:
        self._name = name
        self._channel_configs = {}
        self._channel_process_dict = {}

        super().__init__(logger, rabbitmq)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    @property
    def channel_configs(self) -> Dict:
        return self._channel_configs

    @property
    def channel_process_dict(self) -> Dict:
        return self._channel_process_dict

    def _initialise_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '%s' exchange", HEALTH_CHECK_EXCHANGE)
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue '%s'", _CHANNELS_MANAGER_INPUT_QUEUE)
        self.rabbitmq.queue_declare(_CHANNELS_MANAGER_INPUT_QUEUE, False, True,
                                    False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", _CHANNELS_MANAGER_INPUT_QUEUE,
                         HEALTH_CHECK_EXCHANGE,
                         _CHANNELS_MANAGER_HB_ROUTING_KEY)
        self.rabbitmq.queue_bind(_CHANNELS_MANAGER_INPUT_QUEUE,
                                 HEALTH_CHECK_EXCHANGE,
                                 _CHANNELS_MANAGER_HB_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on '%s'",
                          _CHANNELS_MANAGER_INPUT_QUEUE)
        self.rabbitmq.basic_consume(_CHANNELS_MANAGER_INPUT_QUEUE,
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '%s'", CONFIG_EXCHANGE)
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue '%s'",
                         CHANNELS_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.queue_declare(CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                    False, True, False, False)
        self.logger.info("Binding queue '%s' to exchange '%s' with routing key "
                         "'%s'", CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                         CONFIG_EXCHANGE, _CHANNELS_MANAGER_CONFIG_ROUTING_KEY)
        self.rabbitmq.queue_bind(CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                 CONFIG_EXCHANGE,
                                 _CHANNELS_MANAGER_CONFIG_ROUTING_KEY)
        self.logger.debug("Declaring consuming intentions on %s",
                          CHANNELS_MANAGER_CONFIGS_QUEUE_NAME)
        self.rabbitmq.basic_consume(CHANNELS_MANAGER_CONFIGS_QUEUE_NAME,
                                    self._process_configs, False, False, None)

        # Declare publishing intentions
        self.logger.info("Setting delivery confirmation on RabbitMQ channel")
        self.rabbitmq.confirm_delivery()

    def _listen_for_data(self) -> None:
        self.rabbitmq.start_consuming()

    def _send_heartbeat(self, data_to_send: Dict) -> None:
        self.rabbitmq.basic_publish_confirm(
            exchange=HEALTH_CHECK_EXCHANGE, routing_key='heartbeat.manager',
            body=data_to_send, is_body_dict=True,
            properties=pika.BasicProperties(delivery_mode=2), mandatory=True)
        self.logger.debug("Sent heartbeat to '%s' exchange",
                          HEALTH_CHECK_EXCHANGE)

    def _create_and_start_telegram_alerts_handler(
            self, bot_token: str, bot_chat_id: str, channel_id: str,
            channel_name: str) -> None:
        process = multiprocessing.Process(target=start_telegram_alerts_handler,
                                          args=(bot_token, bot_chat_id,
                                                channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "Telegram channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        handler_type = ChannelHandlerTypes.ALERTS.value
        self._channel_process_dict[channel_id][handler_type] = {}
        process_details = self._channel_process_dict[channel_id][handler_type]
        process_details['component_name'] = \
            TELEGRAM_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['bot_token'] = bot_token
        process_details['bot_chat_id'] = bot_chat_id
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['channel_type'] = ChannelTypes.TELEGRAM.value

    def _create_and_start_telegram_cmds_handler(
            self, bot_token: str, bot_chat_id: str, channel_id: str,
            channel_name: str, associated_chains: Dict) -> None:
        process = multiprocessing.Process(
            target=start_telegram_commands_handler,
            args=(bot_token, bot_chat_id, channel_id, channel_name,
                  associated_chains))
        process.daemon = True
        log_and_print("Creating a new process for the commands handler of "
                      "Telegram channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        commands_handler_type = ChannelHandlerTypes.COMMANDS.value
        self._channel_process_dict[channel_id][commands_handler_type] = {}
        process_details = self._channel_process_dict[channel_id][
            commands_handler_type]
        process_details['component_name'] = \
            TELEGRAM_COMMANDS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['bot_token'] = bot_token
        process_details['bot_chat_id'] = bot_chat_id
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['associated_chains'] = associated_chains
        process_details['channel_type'] = ChannelTypes.TELEGRAM.value

    def _create_and_start_twilio_alerts_handler(
            self, account_sid: str, auth_token: str, channel_id: str,
            channel_name: str, call_from: str, call_to: List[str], twiml: str,
            twiml_is_url: bool) -> None:
        process = multiprocessing.Process(
            target=start_twilio_alerts_handler,
            args=(account_sid, auth_token, channel_id, channel_name, call_from,
                  call_to, twiml, twiml_is_url))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "Twilio channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        handler_type = ChannelHandlerTypes.ALERTS.value
        self._channel_process_dict[channel_id][handler_type] = {}
        process_details = self._channel_process_dict[channel_id][handler_type]
        process_details['component_name'] = \
            TWILIO_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['account_sid'] = account_sid
        process_details['auth_token'] = auth_token
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['call_from'] = call_from
        process_details['call_to'] = call_to
        process_details['twiml'] = twiml
        process_details['twiml_is_url'] = twiml_is_url
        process_details['channel_type'] = ChannelTypes.TWILIO.value

    def _create_and_start_email_alerts_handler(
            self, smtp: str, email_from: str, emails_to: List[str],
            channel_id: str, channel_name: str, username: Optional[str],
            password: Optional[str], port: int = 0) -> None:
        process = multiprocessing.Process(
            target=start_email_alerts_handler,
            args=(smtp, email_from, emails_to, channel_id, channel_name,
                  username, password, port))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "e-mail channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        handler_type = ChannelHandlerTypes.ALERTS.value
        self._channel_process_dict[channel_id][handler_type] = {}
        process_details = self._channel_process_dict[channel_id][handler_type]
        process_details['component_name'] = \
            EMAIL_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['smtp'] = smtp
        process_details['email_from'] = email_from
        process_details['emails_to'] = emails_to
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['username'] = username
        process_details['password'] = password
        process_details['channel_type'] = ChannelTypes.EMAIL.value
        process_details['port'] = port

    def _create_and_start_pagerduty_alerts_handler(
            self, integration_key: str, channel_id: str, channel_name: str) \
            -> None:
        process = multiprocessing.Process(
            target=start_pagerduty_alerts_handler,
            args=(integration_key, channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "PagerDuty channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        handler_type = ChannelHandlerTypes.ALERTS.value
        self._channel_process_dict[channel_id][handler_type] = {}
        process_details = self._channel_process_dict[channel_id][handler_type]
        process_details['component_name'] = \
            PAGERDUTY_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['integration_key'] = integration_key
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['channel_type'] = ChannelTypes.PAGERDUTY.value

    def _create_and_start_opsgenie_alerts_handler(
            self, api_key: str, eu_host: bool, channel_id: str,
            channel_name: str) -> None:
        process = multiprocessing.Process(
            target=start_opsgenie_alerts_handler,
            args=(api_key, eu_host, channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "Opsgenie channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        handler_type = ChannelHandlerTypes.ALERTS.value
        self._channel_process_dict[channel_id][handler_type] = {}
        process_details = self._channel_process_dict[channel_id][handler_type]
        process_details['component_name'] = \
            OPSGENIE_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['api_key'] = api_key
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['eu_host'] = eu_host
        process_details['channel_type'] = ChannelTypes.OPSGENIE.value

    def _create_and_start_console_alerts_handler(
            self, channel_id: str, channel_name: str) -> None:
        process = multiprocessing.Process(target=start_console_alerts_handler,
                                          args=(channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "console channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        handler_type = ChannelHandlerTypes.ALERTS.value
        self._channel_process_dict[channel_id][handler_type] = {}
        process_details = self._channel_process_dict[channel_id][handler_type]
        process_details['component_name'] = \
            CONSOLE_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['channel_type'] = ChannelTypes.CONSOLE.value

    def _create_and_start_log_alerts_handler(self, channel_id: str,
                                             channel_name: str) -> None:
        process = multiprocessing.Process(target=start_log_alerts_handler,
                                          args=(channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "log channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        handler_type = ChannelHandlerTypes.ALERTS.value
        self._channel_process_dict[channel_id][handler_type] = {}
        process_details = self._channel_process_dict[channel_id][handler_type]
        process_details['component_name'] = \
            LOG_ALERTS_HANDLER_NAME_TEMPLATE.format(channel_name)
        process_details['process'] = process
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['channel_type'] = ChannelTypes.LOG.value

    def _start_persistent_channels(self) -> None:
        # Start the console channel in a separate process if it is not yet
        # started or it is not alive. This must be done in case of a restart of
        # the manager.
        alerts_handler_type = ChannelHandlerTypes.ALERTS.value
        if CONSOLE_CHANNEL_ID not in self._channel_process_dict or \
                not self.channel_process_dict[CONSOLE_CHANNEL_ID][
                    alerts_handler_type]['process'].is_alive():
            self._create_and_start_console_alerts_handler(CONSOLE_CHANNEL_ID,
                                                          CONSOLE_CHANNEL_NAME)

        # Start the LOG channel in a separate process if it is not yet started
        # or it is not alive. This must be done in case of a restart of the
        # manager.
        if LOG_CHANNEL_ID not in self._channel_process_dict or \
                not self.channel_process_dict[LOG_CHANNEL_ID][
                    alerts_handler_type]['process'].is_alive():
            self._create_and_start_log_alerts_handler(LOG_CHANNEL_ID,
                                                      LOG_CHANNEL_NAME)

    def _process_telegram_configs(self, sent_configs: Dict) -> Dict:
        if ChannelTypes.TELEGRAM.value in self.channel_configs:
            current_configs = self.channel_configs[ChannelTypes.TELEGRAM.value]
        else:
            current_configs = {}

        # This contains all the correct latest channel configs. All current
        # configs are correct configs, therefore start from the current and
        # modify as we go along according to the updates. This is done just in
        # case an error occurs.
        correct_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                bot_token = config['bot_token']
                chat_id = config['chat_id']
                alerts = str_to_bool(config['alerts'])
                commands = str_to_bool(config['commands'])
                parent_ids = config['parent_ids'].split(',')
                chain_names = config['parent_names'].split(',')
                associated_chains = dict(zip(parent_ids, chain_names))

                # If Telegram Alerts are enabled on this channel, start an
                # alerts handler for this channel
                if alerts:
                    self._create_and_start_telegram_alerts_handler(
                        bot_token, chat_id, channel_id, channel_name)
                    correct_configs[config_id] = config

                # If Telegram Commands are enabled on this channel, start a
                # commands handler for this channel
                if commands:
                    self._create_and_start_telegram_cmds_handler(
                        bot_token, chat_id, channel_id, channel_name,
                        associated_chains)
                    correct_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                bot_token = config['bot_token']
                chat_id = config['chat_id']
                alerts = str_to_bool(config['alerts'])
                commands = str_to_bool(config['commands'])
                parent_ids = config['parent_ids'].split(',')
                chain_names = config['parent_names'].split(',')
                associated_chains = dict(zip(parent_ids, chain_names))

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()

                    if not alerts:
                        del self.channel_process_dict[channel_id][
                            alerts_handler_type]
                        log_and_print("Killed the alerts handler of {} "
                                      .format(channel_name), self.logger)
                    else:
                        log_and_print(
                            "Restarting the alerts handler of {} with latest "
                            "configuration".format(channel_name), self.logger)
                        self._create_and_start_telegram_alerts_handler(
                            bot_token, chat_id, channel_id, channel_name)
                else:
                    if alerts:
                        log_and_print(
                            "Starting a new alerts handler for {}.".format(
                                channel_name), self.logger)
                        self._create_and_start_telegram_alerts_handler(
                            bot_token, chat_id, channel_id, channel_name)

                commands_handler_type = ChannelHandlerTypes.COMMANDS.value
                if commands_handler_type in \
                        self.channel_process_dict[channel_id]:
                    previous_commands_process = self.channel_process_dict[
                        channel_id][commands_handler_type]['process']
                    previous_commands_process.terminate()
                    previous_commands_process.join()

                    if not commands:
                        del self.channel_process_dict[channel_id][
                            commands_handler_type]
                        log_and_print("Killed the commands handler of {} "
                                      .format(channel_name), self.logger)
                    else:
                        log_and_print(
                            "Restarting the commands handler of {} with latest "
                            "configuration".format(channel_name), self.logger)
                        self._create_and_start_telegram_cmds_handler(
                            bot_token, chat_id, channel_id, channel_name,
                            associated_chains)
                else:
                    if commands:
                        log_and_print(
                            "Starting a new commands handler for {}.".format(
                                channel_name), self.logger)
                        self._create_and_start_telegram_cmds_handler(
                            bot_token, chat_id, channel_id, channel_name,
                            associated_chains)

                # Delete the state entries if both commands and alerts are
                # disabled on the Telegram channel. Otherwise, save the config
                # as a process must be running
                if not commands and not alerts:
                    del self.channel_process_dict[channel_id]
                    del correct_configs[config_id]
                else:
                    correct_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()
                    log_and_print("Killed the alerts handler of {} ".format(
                        channel_name), self.logger)

                commands_handler_type = ChannelHandlerTypes.COMMANDS.value
                if commands_handler_type in \
                        self.channel_process_dict[channel_id]:
                    previous_commands_process = self.channel_process_dict[
                        channel_id][commands_handler_type]['process']
                    previous_commands_process.terminate()
                    previous_commands_process.join()
                    log_and_print("Killed the commands handler of {} ".format(
                        channel_name), self.logger)

                del self.channel_process_dict[channel_id]
                del correct_configs[config_id]
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing {}".format(sent_configs))
            self.logger.exception(e)

        return correct_configs

    def _process_twilio_configs(self, sent_configs: Dict) -> Dict:
        if ChannelTypes.TWILIO.value in self.channel_configs:
            current_configs = self.channel_configs[ChannelTypes.TWILIO.value]
        else:
            current_configs = {}

        # This contains all the correct latest channel configs. All current
        # configs are correct configs, therefore start from the current and
        # modify as we go along according to the updates. This is done just in
        # case an error occurs.
        correct_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                account_sid = config['account_sid']
                auth_token = config['auth_token']
                twilio_phone_number = config['twilio_phone_no']
                numbers_to_dial = config['twilio_phone_numbers_to_dial_valid'] \
                    .split(',')
                twiml = env.TWIML
                twiml_is_url = env.TWIML_IS_URL

                self._create_and_start_twilio_alerts_handler(
                    account_sid, auth_token, channel_id, channel_name,
                    twilio_phone_number, numbers_to_dial, twiml, twiml_is_url)
                correct_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                account_sid = config['account_sid']
                auth_token = config['auth_token']
                twilio_phone_number = config['twilio_phone_no']
                numbers_to_dial = config['twilio_phone_numbers_to_dial_valid'] \
                    .split(',')
                twiml = env.TWIML
                twiml_is_url = env.TWIML_IS_URL

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()

                log_and_print("Restarting the alerts handler of {} with "
                              "latest configuration".format(channel_name),
                              self.logger)
                self._create_and_start_twilio_alerts_handler(
                    account_sid, auth_token, channel_id, channel_name,
                    twilio_phone_number, numbers_to_dial, twiml,
                    twiml_is_url)
                correct_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()
                    log_and_print("Killed the alerts handler of {} ".format(
                        channel_name), self.logger)

                del self.channel_process_dict[channel_id]
                del correct_configs[config_id]
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        return correct_configs

    def _process_email_configs(self, sent_configs: Dict) -> Dict:
        if ChannelTypes.EMAIL.value in self.channel_configs:
            current_configs = self.channel_configs[ChannelTypes.EMAIL.value]
        else:
            current_configs = {}

        # This contains all the correct latest channel configs. All current
        # configs are correct configs, therefore start from the current and
        # modify as we go along according to the updates. This is done just in
        # case an error occurs.
        correct_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                smtp = config['smtp']
                email_from = config['email_from']
                emails_to = config['emails_to'].split(',')
                username = config['username']
                password = config['password']
                port = convert_to_int_if_not_none_and_not_empty_str(
                    config['port'], 0)

                self._create_and_start_email_alerts_handler(
                    smtp, email_from, emails_to, channel_id, channel_name,
                    username, password, port)
                correct_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                smtp = config['smtp']
                email_from = config['email_from']
                emails_to = config['emails_to'].split(',')
                username = config['username']
                password = config['password']
                port = convert_to_int_if_not_none_and_not_empty_str(
                    config['port'], 0)

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()

                log_and_print("Restarting the alerts handler of {} with "
                              "latest configuration".format(channel_name),
                              self.logger)
                self._create_and_start_email_alerts_handler(
                    smtp, email_from, emails_to, channel_id, channel_name,
                    username, password, port)
                correct_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()
                    log_and_print("Killed the alerts handler of {} ".format(
                        channel_name), self.logger)

                del self.channel_process_dict[channel_id]
                del correct_configs[config_id]
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        return correct_configs

    def _process_pagerduty_configs(self, sent_configs: Dict) -> Dict:
        if ChannelTypes.PAGERDUTY.value in self.channel_configs:
            current_configs = self.channel_configs[ChannelTypes.PAGERDUTY.value]
        else:
            current_configs = {}

        # This contains all the correct latest channel configs. All current
        # configs are correct configs, therefore start from the current and
        # modify as we go along according to the updates. This is done just in
        # case an error occurs.
        correct_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                integration_key = config['integration_key']

                self._create_and_start_pagerduty_alerts_handler(
                    integration_key, channel_id, channel_name)
                correct_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                integration_key = config['integration_key']

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()

                log_and_print("Restarting the alerts handler of {} with "
                              "latest configuration".format(channel_name),
                              self.logger)
                self._create_and_start_pagerduty_alerts_handler(
                    integration_key, channel_id, channel_name)
                correct_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()
                    log_and_print("Killed the alerts handler of {} ".format(
                        channel_name), self.logger)

                del self.channel_process_dict[channel_id]
                del correct_configs[config_id]
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        return correct_configs

    def _process_opsgenie_configs(self, sent_configs: Dict) -> Dict:
        if ChannelTypes.OPSGENIE.value in self.channel_configs:
            current_configs = self.channel_configs[ChannelTypes.OPSGENIE.value]
        else:
            current_configs = {}

        # This contains all the correct latest channel configs. All current
        # configs are correct configs, therefore start from the current and
        # modify as we go along according to the updates. This is done just in
        # case an error occurs.
        correct_configs = copy.deepcopy(current_configs)
        try:
            new_configs = get_newly_added_configs(sent_configs, current_configs)
            for config_id in new_configs:
                config = new_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                api_key = config['api_token']
                eu_host = str_to_bool(config['eu'])

                self._create_and_start_opsgenie_alerts_handler(
                    api_key, eu_host, channel_id, channel_name)
                correct_configs[config_id] = config

            modified_configs = get_modified_configs(sent_configs,
                                                    current_configs)
            for config_id in modified_configs:
                # Get the latest updates
                config = sent_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']
                api_key = config['api_token']
                eu_host = str_to_bool(config['eu'])

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()

                log_and_print("Restarting the alerts handler of {} with "
                              "latest configuration".format(channel_name),
                              self.logger)
                self._create_and_start_opsgenie_alerts_handler(
                    api_key, eu_host, channel_id, channel_name)
                correct_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']

                alerts_handler_type = ChannelHandlerTypes.ALERTS.value
                if alerts_handler_type in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id][alerts_handler_type]['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()
                    log_and_print("Killed the alerts handler of {} ".format(
                        channel_name), self.logger)

                del self.channel_process_dict[channel_id]
                del correct_configs[config_id]
        except Exception as e:
            # If we encounter an error during processing, this error must be
            # logged and the message must be acknowledged so that it is removed
            # from the queue
            self.logger.error("Error when processing %s", sent_configs)
            self.logger.exception(e)

        return correct_configs

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info("Received configs %s. Now processing.", sent_configs)

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        if method.routing_key == 'channels.telegram_config':
            updated_configs = self._process_telegram_configs(sent_configs)
            self._channel_configs[ChannelTypes.TELEGRAM.value] = updated_configs
        elif method.routing_key == 'channels.twilio_config':
            updated_configs = self._process_twilio_configs(sent_configs)
            self._channel_configs[ChannelTypes.TWILIO.value] = updated_configs
        elif method.routing_key == 'channels.email_config':
            updated_configs = self._process_email_configs(sent_configs)
            self._channel_configs[ChannelTypes.EMAIL.value] = updated_configs
        elif method.routing_key == 'channels.pagerduty_config':
            updated_configs = self._process_pagerduty_configs(sent_configs)
            self._channel_configs[ChannelTypes.PAGERDUTY.value] = \
                updated_configs
        elif method.routing_key == 'channels.opsgenie_config':
            updated_configs = self._process_opsgenie_configs(sent_configs)
            self._channel_configs[ChannelTypes.OPSGENIE.value] = \
                updated_configs

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.debug("Received %s", data)

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.name
            heartbeat['running_processes'] = []
            heartbeat['dead_processes'] = []
            for channel_id, handlers in self.channel_process_dict.items():
                for handler, process_details in handlers.items():
                    process = process_details['process']
                    component_name = process_details['component_name']
                    if process.is_alive():
                        heartbeat['running_processes'].append(component_name)
                    else:
                        heartbeat['dead_processes'].append(component_name)
                        process.join()  # Just in case, to release resources

                        # Restart dead process
                        channel_type = process_details['channel_type']
                        if channel_type == ChannelTypes.TELEGRAM.value:
                            if handler == ChannelHandlerTypes.ALERTS.value:
                                self._create_and_start_telegram_alerts_handler(
                                    process_details['bot_token'],
                                    process_details['bot_chat_id'],
                                    process_details['channel_id'],
                                    process_details['channel_name'])
                            elif handler == ChannelHandlerTypes.COMMANDS.value:
                                self._create_and_start_telegram_cmds_handler(
                                    process_details['bot_token'],
                                    process_details['bot_chat_id'],
                                    process_details['channel_id'],
                                    process_details['channel_name'],
                                    process_details['associated_chains'])
                        elif channel_type == ChannelTypes.TWILIO.value:
                            self._create_and_start_twilio_alerts_handler(
                                process_details['account_sid'],
                                process_details['auth_token'],
                                process_details['channel_id'],
                                process_details['channel_name'],
                                process_details['call_from'],
                                process_details['call_to'],
                                process_details['twiml'],
                                process_details['twiml_is_url'])
                        elif channel_type == ChannelTypes.EMAIL.value:
                            self._create_and_start_email_alerts_handler(
                                process_details['smtp'],
                                process_details['email_from'],
                                process_details['emails_to'],
                                process_details['channel_id'],
                                process_details['channel_name'],
                                process_details['username'],
                                process_details['password'],
                                process_details['port']
                            )
                        elif channel_type == ChannelTypes.PAGERDUTY.value:
                            self._create_and_start_pagerduty_alerts_handler(
                                process_details['integration_key'],
                                process_details['channel_id'],
                                process_details['channel_name'],
                            )
                        elif channel_type == ChannelTypes.OPSGENIE.value:
                            self._create_and_start_opsgenie_alerts_handler(
                                process_details['api_key'],
                                process_details['eu_host'],
                                process_details['channel_id'],
                                process_details['channel_name'],
                            )
                        elif channel_type == ChannelTypes.CONSOLE.value:
                            self._create_and_start_console_alerts_handler(
                                process_details['channel_id'],
                                process_details['channel_name'])
                        elif channel_type == ChannelTypes.LOG.value:
                            self._create_and_start_log_alerts_handler(
                                process_details['channel_id'],
                                process_details['channel_name'])
            heartbeat['timestamp'] = datetime.now().timestamp()
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing %s", data)
            self.logger.exception(e)
            return

        # Send heartbeat if processing was successful
        try:
            self._send_heartbeat(heartbeat)
        except MessageWasNotDeliveredException as e:
            # Log the message and do not raise it as there is no use in
            # re-trying to send a heartbeat
            self.logger.exception(e)
        except Exception as e:
            # For any other exception raise it.
            raise e

    def start(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialise_rabbitmq()
        while True:
            try:
                self._start_persistent_channels()
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialise the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    # If termination signals are received, terminate all child process and
    # close the connection with rabbit mq before exiting
    def _on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print(
            "{} is terminating. Connections with RabbitMQ will be closed, and "
            "any running channel handlers will be stopped gracefully. "
            "Afterwards the {} process will exit.".format(self, self),
            self.logger)
        self.disconnect_from_rabbit()

        for _, handlers in self.channel_process_dict.items():
            for handler, process_details in handlers.items():
                log_and_print("Terminating {}".format(
                    process_details['component_name']), self.logger)
                process = process_details['process']
                process.terminate()
                process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()

    def _send_data(self, *args) -> None:
        """
        We are not implementing the _send_data function because wrt to rabbit,
        the channels manager only sends heartbeats.
        """
        pass
