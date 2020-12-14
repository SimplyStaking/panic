import copy
import json
import logging
import multiprocessing
import signal
import sys
from datetime import datetime
from types import FrameType
from typing import Dict, List

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from src.alerter.alerter_starters import start_system_alerter
from src.alerter.managers.manager import AlertersManager
from src.channels_manager.handlers.starters import \
    start_telegram_alerts_handler, start_telegram_commands_handler, \
    start_twilio_alerts_handler, start_console_alerts_handler, \
    start_log_alerts_handler
from src.configs.system_alerts import SystemAlertsConfig
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils import env
from src.utils.configs import get_newly_added_configs, get_modified_configs, \
    get_removed_configs
from src.utils.constants import HEALTH_CHECK_EXCHANGE, CONFIG_EXCHANGE
from src.utils.exceptions import ParentIdsMissMatchInAlertsConfiguration, \
    MessageWasNotDeliveredException
from src.utils.logging import log_and_print
from src.utils.types import str_to_bool, ChannelTypes


class ChannelsManager:

    def __init__(self, logger: logging.Logger, name: str) -> None:
        self._logger = logger
        self._name = name
        self._channel_configs = {}
        self._channel_process_dict = {}

        rabbit_ip = env.RABBIT_IP
        self._rabbitmq = RabbitMQApi(logger=self.logger, host=rabbit_ip)

        # Handle termination signals by stopping the manager gracefully
        signal.signal(signal.SIGTERM, self.on_terminate)
        signal.signal(signal.SIGINT, self.on_terminate)
        signal.signal(signal.SIGHUP, self.on_terminate)

    def __str__(self) -> str:
        return self.name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def name(self) -> str:
        return self._name

    @property
    def channel_configs(self) -> Dict:
        return self._channel_configs

    @property
    def channel_process_dict(self) -> Dict:
        return self._channel_process_dict

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    def _initialize_rabbitmq(self) -> None:
        self.rabbitmq.connect_till_successful()

        # Declare consuming intentions
        self.logger.info("Creating '{}' exchange".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.exchange_declare(HEALTH_CHECK_EXCHANGE, 'topic', False,
                                       True, False, False)
        self.logger.info("Creating queue 'system_alerters_manager_ping_queue'")
        self.rabbitmq.queue_declare('channels_manager_ping_queue', False, True,
                                    False, False)
        self.logger.info("Binding queue 'channels_manager_ping_queue' to "
                         "exchange '{}' with routing key "
                         "'ping'".format(HEALTH_CHECK_EXCHANGE))
        self.rabbitmq.queue_bind('channels_manager_ping_queue',
                                 HEALTH_CHECK_EXCHANGE, 'ping')
        self.logger.info("Declaring consuming intentions on "
                         "'channels_manager_ping_queue'")
        self.rabbitmq.basic_consume('channels_manager_ping_queue',
                                    self._process_ping, True, False, None)

        self.logger.info("Creating exchange '{}'".format(CONFIG_EXCHANGE))
        self.rabbitmq.exchange_declare(CONFIG_EXCHANGE, 'topic', False, True,
                                       False, False)
        self.logger.info("Creating queue 'channels_manager_configs_queue'")
        self.rabbitmq.queue_declare('channels_manager_configs_queue',
                                    False, True, False, False)
        self.logger.info(
            "Binding queue 'channels_manager_configs_queue' to exchange '{}' "
            "with routing key 'channels.*'".format(CONFIG_EXCHANGE))
        self.rabbitmq.queue_bind('channels_manager_configs_queue',
                                 CONFIG_EXCHANGE, 'channels.*')
        self.logger.info("Declaring consuming intentions on "
                         "channels_manager_configs_queue")
        self.rabbitmq.basic_consume('channels_manager_configs_queue',
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
        self.logger.info("Sent heartbeat to '{}' exchange".format(
            HEALTH_CHECK_EXCHANGE))

    def _create_and_start_telegram_alerts_handler_process(
            self, bot_token: str, bot_chat_id: str, channel_id: str,
            channel_name: str) -> None:
        process = multiprocessing.Process(target=start_telegram_alerts_handler,
                                          args=(bot_token, bot_chat_id,
                                                channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "telegram channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        self._channel_process_dict[channel_id]['alerts'] = {}
        process_details = self._channel_process_dict[channel_id]['alerts']
        process_details['component_name'] = \
            "Telegram Alerts Handler ({})".format(channel_name)
        process_details['process'] = process
        process_details['bot_token'] = bot_token
        process_details['bot_chat_id'] = bot_chat_id
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['channel_type'] = ChannelTypes.TELEGRAM.value

    def _create_and_start_telegram_cmds_handler_process(
            self, bot_token: str, bot_chat_id: str, channel_id: str,
            channel_name: str, associated_chains: Dict) -> None:
        process = multiprocessing.Process(
            target=start_telegram_commands_handler,
            args=(bot_token, bot_chat_id, channel_id, channel_name,
                  associated_chains))
        process.daemon = True
        log_and_print("Creating a new process for the commands handler of "
                      "telegram channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        self._channel_process_dict[channel_id]['commands'] = {}
        process_details = self._channel_process_dict[channel_id]['commands']
        process_details['component_name'] = \
            "Telegram Commands Handler ({})".format(channel_name)
        process_details['process'] = process
        process_details['bot_token'] = bot_token
        process_details['bot_chat_id'] = bot_chat_id
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['associated_chains'] = associated_chains
        process_details['channel_type'] = ChannelTypes.TELEGRAM.value

    def _create_and_start_twilio_alerts_handler_process(
            self, account_sid: str, auth_token: str, channel_id: str,
            channel_name: str, call_from: str, call_to: List[str], twiml: str,
            twiml_is_url: bool) -> None:
        process = multiprocessing.Process(
            target=start_twilio_alerts_handler,
            args=(account_sid, auth_token, channel_id, channel_name, call_from,
                  call_to, twiml, twiml_is_url))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "twilio channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        self._channel_process_dict[channel_id]['alerts'] = {}
        process_details = self._channel_process_dict[channel_id]['alerts']
        process_details['component_name'] = \
            "Twilio Alerts Handler ({})".format(channel_name)
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

    def _create_and_start_console_alerts_handler_process(
            self, channel_id: str, channel_name: str) -> None:
        process = multiprocessing.Process(target=start_console_alerts_handler,
                                          args=(channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "console channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        self._channel_process_dict[channel_id]['alerts'] = {}
        process_details = self._channel_process_dict[channel_id]['alerts']
        process_details['component_name'] = \
            "Console Alerts Handler ({})".format(channel_name)
        process_details['process'] = process
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['channel_type'] = ChannelTypes.CONSOLE.value

    def _create_and_start_log_alerts_handler_process(self, channel_id: str,
                                                     channel_name: str) -> None:
        process = multiprocessing.Process(target=start_log_alerts_handler,
                                          args=(channel_id, channel_name))
        process.daemon = True
        log_and_print("Creating a new process for the alerts handler of "
                      "log channel {}".format(channel_name), self.logger)
        process.start()

        if channel_id not in self._channel_process_dict:
            self._channel_process_dict[channel_id] = {}

        self._channel_process_dict[channel_id]['alerts'] = {}
        process_details = self._channel_process_dict[channel_id]['alerts']
        process_details['component_name'] = \
            "Log Alerts Handler ({})".format(channel_name)
        process_details['process'] = process
        process_details['channel_id'] = channel_id
        process_details['channel_name'] = channel_name
        process_details['channel_type'] = ChannelTypes.LOG.value

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
                chain_names = config['chain_names'].split(',')
                associated_chains = dict(zip(parent_ids, chain_names))

                # If Telegram Alerts are enabled on this channel, start an
                # alerts handler for this channel
                if alerts:
                    self._create_and_start_telegram_alerts_handler_process(
                        bot_token, chat_id, channel_id, channel_name)
                    correct_configs[config_id] = config

                # If Telegram Commands are enabled on this channel, start a
                # commands handler for this channel
                if commands:
                    self._create_and_start_telegram_cmds_handler_process(
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
                chain_names = config['chain_names'].split(',')
                associated_chains = dict(zip(parent_ids, chain_names))

                if 'alerts' in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id]['alerts']['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()

                    if not alerts:
                        del self.channel_process_dict[channel_id]['alerts']
                        log_and_print("Killed the alerts handler of {} "
                                      .format(channel_name), self.logger)
                    else:
                        log_and_print(
                            "Restarting the alerts handler of {} with latest "
                            "configuration".format(channel_name), self.logger)
                        self._create_and_start_telegram_alerts_handler_process(
                            bot_token, chat_id, channel_id, channel_name)

                if 'commands' in self.channel_process_dict[channel_id]:
                    previous_commands_process = self.channel_process_dict[
                        channel_id]['commands']['process']
                    previous_commands_process.terminate()
                    previous_commands_process.join()

                    if not commands:
                        del self.channel_process_dict[channel_id]['commands']
                        log_and_print("Killed the commands handler of {} "
                                      .format(channel_name), self.logger)
                    else:
                        log_and_print(
                            "Restarting the commands handler of {} with latest "
                            "configuration".format(channel_name), self.logger)
                        self._create_and_start_telegram_cmds_handler_process(
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

                if 'alerts' in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id]['alerts']['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()
                    log_and_print("Killed the alerts handler of {} ".format(
                        channel_name), self.logger)

                if 'commands' in self.channel_process_dict[channel_id]:
                    previous_commands_process = self.channel_process_dict[
                        channel_id]['commands']['process']
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
                numbers_to_dial = config['twilio_phone_numbers_to_dial_valid']\
                    .split(',')
                twiml = env.TWIML
                twiml_is_url = env.TWIML_IS_URL

                self._create_and_start_twilio_alerts_handler_process(
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

                if 'alerts' in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id]['alerts']['process']
                    previous_alerts_process.terminate()
                    previous_alerts_process.join()

                log_and_print("Restarting the alerts handler of {} with "
                              "latest configuration".format(channel_name),
                              self.logger)
                self._create_and_start_twilio_alerts_handler_process(
                    account_sid, auth_token, channel_id, channel_name,
                    twilio_phone_number, numbers_to_dial, twiml,
                    twiml_is_url)
                correct_configs[config_id] = config

            removed_configs = get_removed_configs(sent_configs, current_configs)
            for config_id in removed_configs:
                config = removed_configs[config_id]
                channel_id = config['id']
                channel_name = config['channel_name']

                if 'alerts' in self.channel_process_dict[channel_id]:
                    previous_alerts_process = self.channel_process_dict[
                        channel_id]['alerts']['process']
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
            self.logger.error("Error when processing {}".format(sent_configs))
            self.logger.exception(e)

        return correct_configs

    def _process_configs(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        sent_configs = json.loads(body)

        self.logger.info("Received configs {}. Now processing.".format(
            sent_configs))

        if 'DEFAULT' in sent_configs:
            del sent_configs['DEFAULT']

        if method.routing_key == 'channels.telegram_config':
            updated_configs = self._process_telegram_configs(sent_configs)
            self._channel_configs[ChannelTypes.TELEGRAM.value] = updated_configs
        elif method.routing_key == 'channels.twilio_config':
            updated_configs = self._process_twilio_configs(sent_configs)
            self._channel_configs[ChannelTypes.TWILIO.value] = updated_configs

        # TODO: Must do for e-mail, pagerduty and opsgenie

        self.rabbitmq.basic_ack(method.delivery_tag, False)

    def _process_ping(
            self, ch: BlockingChannel, method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties, body: bytes) -> None:
        data = body
        self.logger.info("Received {}".format(data))

        heartbeat = {}
        try:
            heartbeat['component_name'] = self.name
            heartbeat['running_processes'] = []
            heartbeat['dead_processes'] = []
            for channel_id, handlers in self.channel_process_dict.items():
                for handler, process_details in handlers:
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
                            # TODO: Tomorrow continue from these. Start by
                            #     : doing if handler == commands, or handler=alerts.
                            #     : maybe do handler type enum
                            pass
                        elif channel_type == ChannelTypes.TWILIO.value:
                            pass
                        elif channel_type == ChannelTypes.CONSOLE.value:
                            pass
                        elif channel_type == ChannelTypes.LOG.value:
                            pass

                        # TODO: Must add e-mail, pager and opsgenie here.
            heartbeat['timestamp'] = datetime.now().timestamp()
        except Exception as e:
            # If we encounter an error during processing log the error and
            # return so that no heartbeat is sent
            self.logger.error("Error when processing {}".format(data))
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

    def manage(self) -> None:
        log_and_print("{} started.".format(self), self.logger)
        self._initialize_rabbitmq()
        while True:
            try:
                # TODO: Must start console and logs before listening for data,
                #     : and this must happen if they are not alive etc.
                self._listen_for_data()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.AMQPChannelError) as e:
                # If we have either a channel error or connection error, the
                # channel is reset, therefore we need to re-initialize the
                # connection or channel settings
                raise e
            except Exception as e:
                self.logger.exception(e)
                raise e

    # If termination signals are received, terminate all child process and
    # close the connection with rabbit mq before exiting
    def on_terminate(self, signum: int, stack: FrameType) -> None:
        log_and_print(
            "{} is terminating. Connections with RabbitMQ will be closed, and "
            "any running system alerters will be stopped gracefully. "
            "Afterwards the {} process will exit.".format(self, self),
            self.logger)
        self.rabbitmq.disconnect_till_successful()

        for _, process_details in self.parent_id_process_dict.items():
            log_and_print("Terminating the alerter process of {}".format(
                process_details['chain']), self.logger)
            process = process_details['process']
            process.terminate()
            process.join()

        log_and_print("{} terminated.".format(self), self.logger)
        sys.exit()
