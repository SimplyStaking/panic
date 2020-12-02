import copy
import json
import logging
import os

import pika
import pika.exceptions
from pymongo.errors import PyMongoError
from redis import RedisError
from telegram import Update
from telegram.ext import CallbackContext

from src.channels_manager.commands.handlers.handler import CommandHandler \
    as CmdHandler
from src.channels_manager.handlers.telegram.commands import \
    TelegramCommandsHandler
from src.data_store.mongo import MongoApi
from src.data_store.redis import RedisApi, Keys
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.alert import Severity


class TelegramCommandHandlers(CmdHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 redis: RedisApi, mongo: MongoApi,
                 telegram_commands_handler: TelegramCommandsHandler) -> None:
        super().__init__(handler_name, logger.getChild(handler_name))

        rabbit_ip = os.environ['RABBIT_IP']
        self._rabbitmq = RabbitMQApi(logger=self.logger.getChild('rabbitmq'),
                                     host=rabbit_ip)
        self._redis = redis
        self._mongo = mongo
        self._telegram_commands_handler = telegram_commands_handler

    @property
    def rabbitmq(self) -> RabbitMQApi:
        return self._rabbitmq

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def mongo(self) -> MongoApi:
        return self._mongo

    @property
    def telegram_commands_handler(self) -> TelegramCommandsHandler:
        return self._telegram_commands_handler

    def redis_running(self) -> bool:
        try:
            self.redis.ping_unsafe()
            return True
        except (RedisError, ConnectionResetError):
            pass
        except Exception as e:
            self.logger.error('Unrecognized error when accessing Redis: %s', e)
        return False

    def mongo_running(self) -> bool:
        try:
            self.mongo.ping_unsafe()
            return True
        except PyMongoError:
            pass
        except Exception as e:
            self.logger.error('Unrecognized error when accessing Mongo: %s', e)
        return False

    def rabbit_running(self) -> bool:
        # Check that the rabbit server is running by trying to connect with it.
        # Disconnect afterwards to avoid connection errors due to heartbeats,
        # since commands are not continuously sent.
        try:
            self.rabbitmq.connect_unsafe()
            self.rabbitmq.disconnect_unsafe()
            return True
        except pika.exceptions.AMQPConnectionError:
            pass
        except Exception as e:
            self.logger.error('Unrecognized error when accessing RabbitMQ: %s',
                              e)
        return False

    @staticmethod
    def formatted_reply(update: Update, reply: str):
        # Adds Markdown formatting
        update.message.reply_text(reply, parse_mode='MarkdownV2')

    def unknown_callback(self, update: Update,
                         context: CallbackContext) -> None:
        self.logger.info('Received unrecognized command: update=%s, '
                         'context=%s', update, context)

        # Check that authorised
        if not self.telegram_commands_handler.authorise(update, context):
            return

        # Send a default message for unrecognized commands
        update.message.reply_text('I did not understand (Type /help)')

    def ping_callback(self, update: Update, context: CallbackContext) -> None:
        if self.telegram_commands_handler.authorise(update, context):
            update.message.reply_text('PONG!')

    def status_callback(self) -> None:
        pass

    def unmute_callback(self) -> None:
        # TODO: Both unmute all and unmute can take severities (or not)
        pass

    def mute_callback(self, update: Update, context: CallbackContext) -> None:
        self._logger.info('/mute: update=%s, context=%s', update, context)

        # Check that authorised
        if not self.telegram_commands_handler.authorise(update, context):
            return

        update.message.reply_text('Performing mute...')

        # Expected: /mute or /mute List[<severity>]
        inputted_severities = update.message.text.split(' ')[1:]
        unrecognized_severities = []
        recognized_severities = []

        associated_chains = self.telegram_commands_handler.associated_chains
        chain_names = \
            [chain_name for _, chain_name in associated_chains.items()]

        panic_severities = [severity.value for severity in Severity]
        if not inputted_severities:
            # If no severities were passed as arguments, the user wants to mute
            # all severities.
            recognized_severities = copy.deepcopy(panic_severities)
        else:
            for severity in inputted_severities:
                if severity.upper() in panic_severities:
                    recognized_severities.append(severity.upper())
                else:
                    unrecognized_severities.append(severity)

        if len(unrecognized_severities) != 0:
            self.logger.error('Unrecognized severities {}'.format(
                ', '.join(unrecognized_severities)))
            update.message.reply_text(
                'Muting Failed: Invalid severity/severities {}. Please enter '
                'a combination of CRITICAL, WARNING, INFO or ERROR separated '
                'by spaces after the /mute command. You can enter no '
                'severities and PANIC will automatically mute all alerts for '
                '{}'.format(', '.join(unrecognized_severities),
                            ', '.join(chain_names)))
            return

        redis_error_chains = []
        muted_chains = []
        for chain_id, chain_name in associated_chains.items():
            chain_hash = Keys.get_hash_parent(chain_id)
            mute_alerts_key = Keys.get_chain_mute_alerts()

            severities_muted = {}
            for severity in panic_severities:
                severities_muted[severity] = severity in recognized_severities

            set_ret = self.redis.hset(chain_hash, mute_alerts_key, json.dumps(
                severities_muted))
            if set_ret is None:
                redis_error_chains.append(chain_name)
            else:
                muted_chains.append(chain_name)

        if len(redis_error_chains) == 0:
            self.logger.info('Successfully muted all alerts with '
                             'severity/severities {} for chain(s) '
                             '{}.'.format(', '.join(recognized_severities),
                                          ', '.join(muted_chains)))
            update.message.reply_text(
                'Successfully muted all alerts with severity/severities {} for '
                'chain(s) {}. Give a few seconds until the alerter picks '
                'this up.'.format(', '.join(recognized_severities),
                                  ', '.join(muted_chains)))
        else:
            if len(muted_chains) == 0:
                self.logger.error(
                    'I could not mute {} alerts for {} due to a Redis error.'
                    ''.format(', '.join(recognized_severities),
                              ', '.join(redis_error_chains)))
                update.message.reply_text(
                    'I could not mute {} alerts for {} due to a Redis error. '
                    'Please check /status or the logs to see if Redis is '
                    'online and/or re-try again.'.format(
                        ', '.join(recognized_severities),
                        ', '.join(redis_error_chains)))
            else:
                self.logger.error(
                    'Successfully muted all alerts with severity/severities '
                    '{} for chain(s) {}. However, I could not mute {} alerts '
                    'for {} due to a Redis error.'.format(
                        ', '.join(recognized_severities),
                        ', '.join(muted_chains),
                        ', '.join(recognized_severities),
                        ', '.join(redis_error_chains)))
                update.message.reply_text(
                    'Successfully muted all alerts with severity/severities '
                    '{} for chain(s) {}. Give a few seconds until the alerter '
                    'picks this up. However, I could not mute {} alerts for {} '
                    'due to a Redis error. Please check /status to see if '
                    'Redis is online and/or re-try again.'.format(
                        ', '.join(recognized_severities),
                        ', '.join(muted_chains),
                        ', '.join(recognized_severities),
                        ', '.join(redis_error_chains)))

    def mute_all_callback(self, update: Update, context: CallbackContext) \
            -> None:
        self._logger.info('/mute_all: update=%s, context=%s', update, context)

        # Check that authorised
        if not self.telegram_commands_handler.authorise(update, context):
            return

        update.message.reply_text('Performing mute_all...')

        # Expected: /mute_all or /mute_all List[<severity>]
        inputted_severities = update.message.text.split(' ')[1:]
        unrecognized_severities = []
        recognized_severities = []

        panic_severities = [severity.value for severity in Severity]
        if not inputted_severities:
            # If no severities were passed as arguments, the user wants to mute
            # all severities for all chains.
            recognized_severities = copy.deepcopy(panic_severities)
        else:
            for severity in inputted_severities:
                if severity.upper() in panic_severities:
                    recognized_severities.append(severity.upper())
                else:
                    unrecognized_severities.append(severity)

        if len(unrecognized_severities) != 0:
            self.logger.error('Unrecognized severities {}'.format(
                ', '.join(unrecognized_severities)))
            update.message.reply_text(
                'Muting Failed: Invalid severity/severities {}. Please enter '
                'a combination of CRITICAL, WARNING, INFO or ERROR separated '
                'by spaces after the /mute_all command. You can enter no '
                'severities and PANIC will automatically mute all alerts for '
                'all chains'.format(', '.join(unrecognized_severities)))
            return

        mute_alerter_key = Keys.get_alerter_mute()

        severities_muted = {}
        for severity in panic_severities:
            severities_muted[severity] = severity in recognized_severities

        set_ret = self.redis.set(mute_alerter_key, json.dumps(severities_muted))
        if set_ret is None:
            self.logger.error(
                'I could not mute all {} alerts due to a Redis error.'
                ''.format(', '.join(recognized_severities)))
            update.message.reply_text(
                'I could not mute all {} alerts due to a Redis error. Please '
                'check /status or the logs to see if Redis is online and/or '
                're-try again.'.format(', '.join(recognized_severities)))
        else:
            self.logger.info('Successfully muted all {} alerts for every '
                             'chain.'.format(', '.join(recognized_severities)))
            update.message.reply_text(
                'Successfully muted all {} alerts for every chain. Give a few '
                'seconds until the alerter picks this up.'.format(
                    ', '.join(recognized_severities)))

    def unmute_all_callback(self) -> None:
        # TODO: Must check for pattern an unmute for every chain, apart from
        #     : unsetting the mute all variable in redis
        pass

    def help_callback(self) -> None:
        pass

    def start_callback(self, update: Update, context: CallbackContext):
        self.logger.info('/start: update=%s, context=%s', update, context)

        # Check that authorised
        if not self.telegram_commands_handler.authorise(update, context):
            return

        # Send welcome message
        update.message.reply_text("Welcome to PANIC's Telegram commands!\n"
                                  "Type /help for more information.")

# TODO: Need to update alerter router to cater for these commands. First check
#     : if alert all variable is set, then check for the specific parent id
