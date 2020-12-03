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
            raise e
        return False

    def mongo_running(self) -> bool:
        try:
            self.mongo.ping_unsafe()
            return True
        except PyMongoError:
            pass
        except Exception as e:
            self.logger.error('Unrecognized error when accessing Mongo: %s', e)
            raise e
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
            raise e
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

    @staticmethod
    def _get_running_icon(running: bool) -> str:
        if running:
            return '\xE2\x9C\x85'
        else:
            return '\xE2\x9D\x97'

    def _get_mongo_based_status(self) -> str:
        status = ""
        try:
            if self.mongo_running():
                status += '- *Mongo*: {} \n'.format(self._get_running_icon(
                    True))
            else:
                status += '- *Mongo*: {} \n'.format(self._get_running_icon(
                    False))
        except Exception:
            status += '- Could not get Mongo status due to an unrecognized ' \
                      'error. Check the logs to debug the issue.'

        return status

    def _get_rabbit_based_status(self) -> str:
        status = ""
        try:
            if self.rabbit_running():
                status += '- *RabbitMQ*: {} \n'.format(
                    self._get_running_icon(True))
            else:
                status += '- *RabbitMQ*: {} \n'.format(self._get_running_icon(
                    False))
        except Exception:
            status += '- Could not get RabbitMQ status due to an ' \
                      'unrecognized error. Check the logs to debug the issue.'

        return status

    def _get_muted_status(self) -> str:
        # TODO: Use unsafe only to trigger exceptions. Do not catch exceptions.
        #     : as this is solved in the calling function
        status = ''

        mute_alerter_key = Keys.get_alerter_mute()
        all_chains_muted_severities = []
        if self.redis.exists_unsafe(mute_alerter_key):
            muted_severities = json.loads(self.redis.get_unsafe(
                mute_alerter_key).decode())
            for severity, severity_muted in muted_severities.items():
                if severity_muted:
                    all_chains_muted_severities.append(severity)
            status += '- All chains have {} alerts ' \
                      'muted.\n '.format(','.join(all_chains_muted_severities))

        associated_chains = self.telegram_commands_handler.associated_chains
        chain_names = \
            [chain_name for _, chain_name in associated_chains.items()]

        # TODO: write a line for each chain .. do union of all_chain_muted_severities

        # TODO: Say no muted alert severities for associated chains if nothing
        #     : muted for associated chains. And say nothing on the other one
        return status

    def _get_panic_components_status(self) -> str:
        # TODO: Use unsafe only to trigger exceptions. Do not catch exceptions.
        pass

    def _get_redis_based_status(self) -> str:
        associated_chains = self.telegram_commands_handler.associated_chains
        chain_names = \
            [chain_name for _, chain_name in associated_chains.items()]

        redis_accessible_status = ""
        redis_error_status = \
            "- *Redis*: {} \n".format(self._get_running_icon(False)) + \
            "- No {} alert is consider muted as Redis is inaccessible.".format(
                ', '.join(chain_names)) + \
            "- Cannot get PANIC components' status as Redis is inaccessible."
        unrecognized_error_status = \
            "- Could not get Redis status due to an unrecognized error. " \
            "Check the logs to debug the issue." + \
            "- Cannot get PANIC components' status due to an unrecognized " \
            "error. "
        try:
            redis_accessible_status += '- *Redis*: {} \n'.format(
                self._get_running_icon(True))
            redis_accessible_status += self._get_muted_status()
            redis_accessible_status += self._get_panic_components_status()
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error('Error in redis when getting redis based '
                              'status: ', e)
            return redis_error_status
        except Exception as e:
            self.logger.exception(e)
            self.logger.error('Could not get redis based status: ', e)
            return unrecognized_error_status

        return redis_accessible_status

    def status_callback(self, update: Update, context: CallbackContext) -> None:
        self._logger.info('/status: update=%s, context=%s', update, context)

        # Check that authorised
        if not self.telegram_commands_handler.authorise(update, context):
            return

        # Start forming the status message
        update.message.reply_text('Generating status...')

        mongo_based_status = self._get_mongo_based_status()
        rabbit_based_status = self._get_rabbit_based_status()
        redis_based_status = self._get_redis_based_status()

        status = mongo_based_status + rabbit_based_status + redis_based_status

        # TODO: If overflow message split in two messages. See if you can.
        # Send status
        self.formatted_reply(
            update, status[:-1] if status.endswith('\n') else status)

    def unmute_callback(self, update: Update, context: CallbackContext) -> None:
        self.logger.info('/unmute: update=%s, context=%s', update, context)

        # Check that authorised
        if not self.telegram_commands_handler.authorise(update, context):
            return

        update.message.reply_text('Performing unmute...')

        associated_chains = self.telegram_commands_handler.associated_chains

        redis_error_chains = []
        unrecognized_error_chains = []
        successfully_unmuted_chains = []
        already_unmuted_chains = []
        for chain_id, chain_name in associated_chains.items():
            chain_hash = Keys.get_hash_parent(chain_id)
            mute_alerts_key = Keys.get_chain_mute_alerts()
            try:
                if self.redis.hexists_unsafe(chain_hash, mute_alerts_key):
                    self.redis.hremove_unsafe(chain_hash, mute_alerts_key)
                    self.logger.info("%s alerts have been unmuted.",
                                     chain_name)
                    successfully_unmuted_chains.append(chain_name)
                else:
                    already_unmuted_chains.append(chain_name)
                    self.logger.info("%s has no muted severities.", chain_name)
            except (RedisError, ConnectionResetError) as e:
                self.logger.exception(e)
                self.logger.error('Could not unmute %s alerts due to a'
                                  'redis error: %s', chain_name, e)
                redis_error_chains.append(chain_name)
            except Exception as e:
                self.logger.exception(e)
                self.logger.error('Could not unmute %s alerts due to an '
                                  'unrecognized error: %s', chain_name, e)
                unrecognized_error_chains.append(chain_name)

        res = "Unmute result:\n\n"
        if len(successfully_unmuted_chains) != 0:
            res += "- Successfully unmuted all {} alerts.\n".format(', '.join(
                successfully_unmuted_chains))

        if len(redis_error_chains) != 0:
            res += "- Could not unmute {} alerts due to a redis error. Check " \
                   "/status or the logs to see if Redis is online and/or " \
                   "re-try again \n".format(', '.join(redis_error_chains))

        if len(unrecognized_error_chains) != 0:
            res += "- Could not unmute {} alerts due to an unrecognized " \
                   "error. Check the logs to debug the issue. " \
                   "\n".format(', '.join(unrecognized_error_chains))

        if len(already_unmuted_chains) != 0:
            res += "- No {} alert severity was muted.\n".format(
                ', '.join(already_unmuted_chains))

        update.message.reply_text(res)

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
        unrecognized_error_chains = []
        for chain_id, chain_name in associated_chains.items():
            chain_hash = Keys.get_hash_parent(chain_id)
            mute_alerts_key = Keys.get_chain_mute_alerts()

            severities_muted = {}
            for severity in panic_severities:
                severities_muted[severity] = severity in recognized_severities

            try:
                self.redis.hset_unsafe(chain_hash, mute_alerts_key,
                                       json.dumps(severities_muted))
                muted_chains.append(chain_name)
            except (RedisError, ConnectionResetError) as e:
                self.logger.exception(e)
                self.logger.error('Could not unmute %s alerts due to a'
                                  'redis error: %s', chain_name, e)
                redis_error_chains.append(chain_name)
            except Exception as e:
                self.logger.exception(e)
                self.logger.error('Could not unmute %s alerts due to an '
                                  'unrecognized error: %s', chain_name, e)
                unrecognized_error_chains.append(chain_name)

        res = "Mute result:\n\n"
        if len(muted_chains) != 0:
            res += "- Successfully muted all {} alerts for chain(s). Give a " \
                   "few seconds until the alerter picks this up. " \
                   "\n".format(', '.join(recognized_severities),
                               ', '.join(muted_chains))

        if len(redis_error_chains) != 0:
            res += "- Could not mute {} alerts for chain(s) {} due to a " \
                   "redis error. Check /status or the logs to see if Redis " \
                   "is online and/or re-try again " \
                   "\n".format(', '.join(recognized_severities),
                               ', '.join(redis_error_chains))

        if len(unrecognized_error_chains) != 0:
            res += "- Could not mute {} alerts for chain(s) {} due to an " \
                   "unrecognized error. Check /status or the logs to see if " \
                   "Redis is online and/or re-try again " \
                   "\n".format(', '.join(recognized_severities),
                               ', '.join(unrecognized_error_chains))

        update.message.reply_text(res)

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

        try:
            self.redis.set_unsafe(mute_alerter_key,
                                  json.dumps(severities_muted))
            self.logger.info('Successfully muted all {} alerts for every '
                             'chain.'.format(', '.join(recognized_severities)))
            update.message.reply_text(
                'Successfully muted all {} alerts for every chain. Give a few '
                'seconds until the alerter picks this up.'.format(
                    ', '.join(recognized_severities)))
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error(
                'I could not mute all {} alerts due to a Redis error.'
                ''.format(', '.join(recognized_severities)))
            update.message.reply_text(
                'I could not mute all {} alerts due to a Redis error. Please '
                'check /status or the logs to see if Redis is online and/or '
                're-try again.'.format(', '.join(recognized_severities)))
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(
                'I could not mute all {} alerts due to an unrecognized error.'
                ''.format(', '.join(recognized_severities)))
            update.message.reply_text(
                'I could not mute all {} alerts due to an unrecognized error. '
                'Please check /status or the logs to see if Redis is online '
                'and/or re-try again.'.format(', '.join(recognized_severities)))

    def unmute_all_callback(self, update: Update, context: CallbackContext) \
            -> None:
        self.logger.info('/unmute_all: update=%s, context=%s', update, context)

        # Check that authorised
        if not self.telegram_commands_handler.authorise(update, context):
            return

        update.message.reply_text('Performing unmute_all ...')

        mute_alerter_key = Keys.get_alerter_mute()
        at_least_one_chain_was_muted = False

        try:
            if self.redis.exists_unsafe(mute_alerter_key):
                self.redis.remove_unsafe(mute_alerter_key)
                self.logger.info("Successfully deleted %s from redis",
                                 mute_alerter_key)
                at_least_one_chain_was_muted = True
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error('Unmuting unsuccessful due to an issue with '
                              'redis %s', e)
            update.message.reply_text(
                'Unmuting unsuccessful due to an issue with Redis. Check '
                '/status or the logs to see if Redis is online and/or re-try '
                'again.')
            return
        except Exception as e:
            self.logger.exception(e)
            self.logger.error('Unmuting unsuccessful due to an unrecognized '
                              'issue: %s', e)
            update.message.reply_text(
                'Unmuting unsuccessful due to an unrecognized issue. Check '
                'the logs to debug the issue and/or re-try again.')
            return

        try:
            parent_hash = Keys.get_hash_parent_raw()
            chain_hashes_list = self.redis.get_keys_unsafe(
                '*' + parent_hash + '*')
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error("It may be that not all chains were unmuted "
                              "due to an issue with redis: %s", e)
            update.message.reply_text(
                'It may be that not all chains were unmuted due to a Redis '
                'error. Check /status or the logs to see if redis is online '
                'and/or re-try again.')
            return
        except Exception as e:
            self.logger.exception(e)
            self.logger.error("It may be that not all chains were unmuted "
                              "due to an unrecognized issue: %s", e)
            update.message.reply_text(
                'It may be that not all chains were unmuted due to an '
                'unrecognized error. Check /status or the logs to see if '
                'redis is online and/or re-try again.')
            return

        for chain_hash in chain_hashes_list:
            mute_alerts_key = Keys.get_chain_mute_alerts()
            try:
                if self.redis.hexists_unsafe(chain_hash, mute_alerts_key):
                    self.redis.hremove_unsafe(chain_hash, mute_alerts_key)
                    self.logger.info("All alert severities have been unmuted "
                                     "for chain with hash %s.", chain_hash)
                    at_least_one_chain_was_muted = True
            except (RedisError, ConnectionResetError) as e:
                self.logger.exception(e)
                self.logger.error('Could not unmute all alerts of chain with '
                                  'hash %s due to a redis error: %s.',
                                  chain_hash, e)
                update.message.reply_text(
                    'Not all chains were unmuted due to an issue with Redis. '
                    'Check /status or the logs to see if redis is online '
                    'and/or re-try again.')
                return
            except Exception as e:
                self.logger.exception(e)
                self.logger.error(
                    'Unmuting unsuccessful due to an unrecognized issue: '
                    '%s', e)
                update.message.reply_text(
                    'Not all chains were unmuted due to an unrecognized issue. '
                    'Check the logs to debug the issue and/or re-try again.')
                return

        if at_least_one_chain_was_muted:
            update.message.reply_text(
                'Successfully unmuted all alert severities of all chains '
                'being monitored in panic (including general repositories and '
                'general systems as they belong to the chain GENERAL).')
        else:
            update.message.reply_text(
                'No alert severity was muted for any chain.')

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
