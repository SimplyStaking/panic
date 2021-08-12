import copy
import json
import logging
from datetime import datetime
from typing import Tuple, Dict, Optional, Any

import pika
import pika.exceptions
from pymongo.errors import PyMongoError
from redis import RedisError
from slack_bolt import App, Ack, Say

from src.alerter.alert_severities import Severity
from src.channels_manager.channels.slack import SlackChannel
from src.channels_manager.commands.handlers.handler import CommandHandler
from src.data_store.mongo import MongoApi
from src.data_store.redis import RedisApi, Keys
from src.message_broker.rabbitmq import RabbitMQApi
from src.utils.constants.names import (SYSTEM_MONITORS_MANAGER_NAME,
                                       GITHUB_MONITORS_MANAGER_NAME,
                                       DATA_TRANSFORMERS_MANAGER_NAME,
                                       SYSTEM_ALERTERS_MANAGER_NAME,
                                       GITHUB_ALERTER_MANAGER_NAME,
                                       CHAINLINK_ALERTER_MANAGER_NAME,
                                       DATA_STORE_MANAGER_NAME,
                                       ALERT_ROUTER_NAME,
                                       CONFIGS_MANAGER_NAME,
                                       CHANNELS_MANAGER_NAME,
                                       HEARTBEAT_HANDLER_NAME,
                                       PING_PUBLISHER_NAME,
                                       NODE_MONITORS_MANAGER_NAME)


class SlackCommandHandlers(CommandHandler):

    def __init__(self, handler_name: str, logger: logging.Logger,
                 associated_chains: Dict, slack_channel: SlackChannel,
                 rabbitmq: RabbitMQApi, redis: RedisApi,
                 mongo: MongoApi) -> None:
        super().__init__(handler_name, logger)

        self._rabbitmq = rabbitmq
        self._redis = redis
        self._mongo = mongo
        self._associated_chains = associated_chains
        self._slack_channel = slack_channel
        self._app = App(token=self.slack_channel.slack_bot.bot_token)

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
    def associated_chains(self) -> Dict:
        return self._associated_chains

    @property
    def slack_channel(self) -> SlackChannel:
        return self._slack_channel

    @property
    def app(self) -> App:
        return self._app

    def _execute_safely(function):
        def execute_callback_safely(self, ack: Ack, say: Say,
                                    command: Optional[Dict[str, Any]]) -> None:
            try:
                function(self, ack, say, command)
            except Exception as e:
                self.logger.exception(e)
                self.logger.error("Error while executing %s: %s",
                                  function.__name__, e)

        return execute_callback_safely

    def redis_running(self) -> bool:
        try:
            self.redis.ping_unsafe()
            return True
        except (RedisError, ConnectionResetError):
            pass
        except Exception as e:
            self.logger.error("Unrecognized error when accessing Redis: %r", e)
            raise e
        return False

    def mongo_running(self) -> bool:
        try:
            self.mongo.ping_unsafe()
            return True
        except PyMongoError as e:
            self.logger.error("Mongo error when accessing Mongo: %r", e)
        except Exception as e:
            self.logger.error("Unrecognized error when accessing Mongo: %r", e)
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
        except pika.exceptions.AMQPConnectionError as e:
            self.logger.error("Error when accessing RabbitMQ: %r", e)
        except Exception as e:
            self.logger.error("Unrecognized error when accessing RabbitMQ: %r",
                              e)
            raise e
        return False

    @_execute_safely
    def ping_callback(self, ack: Ack, say: Say,
                      command: Optional[Dict[str, Any]]) -> None:
        self.logger.info("/ping: command=%s", command)

        # Acknowledge command request
        ack()
        say("PONG!")

    @staticmethod
    def _get_running_icon(running: bool) -> str:
        if running:
            return u'\U00002705'
        else:
            return u'\U0000274C'

    def _get_mongo_based_status(self) -> str:
        status = ""
        try:
            if self.mongo_running():
                status += "- *Mongo*: {} \n".format(self._get_running_icon(
                    True))
            else:
                status += "- *Mongo*: {} \n".format(self._get_running_icon(
                    False))
        except Exception:
            status += "- Could not get Mongo status due to an unrecognized " \
                      "error. Check the logs to debug the issue.\n"

        return status

    def _get_rabbit_based_status(self) -> str:
        status = ""
        try:
            if self.rabbit_running():
                status += "- *RabbitMQ*: {} \n".format(
                    self._get_running_icon(True))
            else:
                status += "- *RabbitMQ*: {} \n".format(self._get_running_icon(
                    False))
        except Exception:
            status += "- Could not get RabbitMQ status due to an " \
                      "unrecognized error. Check the logs to debug the issue.\n"

        return status

    def _get_muted_status(self) -> str:
        status = ''

        mute_alerter_key = Keys.get_alerter_mute()
        all_chains_muted_severities = []
        if self.redis.exists_unsafe(mute_alerter_key):
            muted_severities = json.loads(self.redis.get_unsafe(
                mute_alerter_key).decode())
            for severity, severity_muted in muted_severities.items():
                if severity_muted:
                    all_chains_muted_severities.append(severity)
            status += "- All chains have {} alerts " \
                      "muted.\n".format(', '.join(all_chains_muted_severities))
        else:
            status += "- There is no severity which was muted using " \
                      "/muteall \n"

        associated_chains = self.associated_chains

        for chain_id, chain_name in associated_chains.items():
            chain_hash = Keys.get_hash_parent(chain_id)
            mute_alerts_key = Keys.get_chain_mute_alerts()
            if self.redis.hexists_unsafe(chain_hash, mute_alerts_key):
                muted_severities = json.loads(self.redis.hget_unsafe(
                    chain_hash, mute_alerts_key).decode())
                chain_muted_severities = []
                for severity, severity_muted in muted_severities.items():
                    if severity_muted:
                        chain_muted_severities.append(severity)
                chain_muted_severities = list(set().union(
                    chain_muted_severities, all_chains_muted_severities))
                status += "- {} has {} alerts muted.\n".format(
                    chain_name, ', '.join(chain_muted_severities))
            elif not all_chains_muted_severities:
                status += "- {} has no alerts muted.\n".format(chain_name)

        return status

    def _get_manager_component_hb_status(self, heartbeat) -> str:
        # If all sub-processes are running and the component's heartbeat is
        # recent, this function will return an empty string as nothing is to
        # be reported

        status = ''
        dead_processes = heartbeat['dead_processes']
        hb_timestamp = heartbeat['timestamp']
        component = heartbeat['component_name']

        current_timestamp = datetime.now().timestamp()
        time_elapsed_since_hb = current_timestamp - hb_timestamp
        hb_interval = 30
        hb_grace_buffer = 10
        hb_cut_off_time = hb_interval + hb_grace_buffer

        if time_elapsed_since_hb > hb_cut_off_time:
            missed_hbs = int((current_timestamp - hb_timestamp) // hb_interval)
            status = "- *{}*: {} - Missed {} heartbeats, either the " \
                     "health-checker found problems when saving the " \
                     "heartbeat or the {} is running into problems. " \
                     "Please check the " \
                     "logs.\n".format(component, self._get_running_icon(False),
                                      missed_hbs, component)
        else:
            if len(dead_processes) != 0:
                for sub_process in dead_processes:
                    status += "- *{}*: {} - Not running. \n".format(
                        sub_process, self._get_running_icon(False))

        return status

    def _get_worker_component_hb_status(self, heartbeat) -> str:
        # If the worker component is running and the component's heartbeat is
        # recent, this function will return an empty string as nothing is to
        # be reported

        status = ''
        alive = heartbeat['is_alive']
        hb_timestamp = heartbeat['timestamp']
        component = heartbeat['component_name']

        current_timestamp = datetime.now().timestamp()
        time_elapsed_since_hb = current_timestamp - hb_timestamp
        hb_interval = 30
        hb_grace_buffer = 10
        hb_cut_off_time = hb_interval + hb_grace_buffer

        if time_elapsed_since_hb > hb_cut_off_time:
            missed_hbs = int((current_timestamp - hb_timestamp) // hb_interval)
            status = "- *{}*: {} - Missed {} heartbeats, either the " \
                     "health-checker found problems when saving the " \
                     "heartbeat or the {} is running into problems. " \
                     "Please check the " \
                     "logs.\n".format(component, self._get_running_icon(False),
                                      missed_hbs, component)
        else:
            if not alive:
                status += "- *{}*: {} - Not running. \n".format(
                    component, self._get_running_icon(False))

        return status

    def _get_panic_components_status(self, problems_in_health_checker: bool) \
            -> str:
        if problems_in_health_checker:
            return "- *PANIC Components*: {} - Cannot get live status as " \
                   "there seems to be an issue with the Health " \
                   "Checker.\n".format(self._get_running_icon(False))

        status = ''

        configs = [
            (SYSTEM_MONITORS_MANAGER_NAME,
             "self._get_manager_component_hb_status"),
            (GITHUB_MONITORS_MANAGER_NAME,
             "self._get_manager_component_hb_status"),
            (NODE_MONITORS_MANAGER_NAME,
             "self._get_manager_component_hb_status"),
            (DATA_TRANSFORMERS_MANAGER_NAME,
             "self._get_manager_component_hb_status"),
            (SYSTEM_ALERTERS_MANAGER_NAME,
             "self._get_manager_component_hb_status"),
            (GITHUB_ALERTER_MANAGER_NAME,
             "self._get_manager_component_hb_status"),
            (CHAINLINK_ALERTER_MANAGER_NAME,
             "self._get_manager_component_hb_status"),
            (DATA_STORE_MANAGER_NAME, "self._get_manager_component_hb_status"),
            (ALERT_ROUTER_NAME, "self._get_worker_component_hb_status"),
            (CONFIGS_MANAGER_NAME, "self._get_worker_component_hb_status"),
            (CHANNELS_MANAGER_NAME, "self._get_manager_component_hb_status"),
        ]

        for config in configs:
            component_hb_key = Keys.get_component_heartbeat(
                config[0])
            if self.redis.exists_unsafe(component_hb_key):
                component_hb = json.loads(
                    self.redis.get_unsafe(component_hb_key).decode())
                status += eval(config[1])(component_hb)
            else:
                status += "- *{}*: {} - No heartbeats yet.\n" \
                    .format(config[0],
                            self._get_running_icon(False))

        # Just say that PANIC's components are ok if there are no issues.
        if status == '':
            status += "- *PANIC Components*: {}\n".format(
                self._get_running_icon(True))

        return status

    def _get_health_checker_status(self) -> Tuple[str, bool]:
        status = ''
        problems_in_checker = False

        key_heartbeat_handler_hb = Keys.get_component_heartbeat(
            HEARTBEAT_HANDLER_NAME)
        key_ping_publisher_hb = Keys.get_component_heartbeat(
            PING_PUBLISHER_NAME)

        if self.redis.exists_unsafe(key_heartbeat_handler_hb):
            heartbeat_handler_hb = json.loads(
                self.redis.get_unsafe(key_heartbeat_handler_hb).decode())
            hb_timestamp = heartbeat_handler_hb['timestamp']

            current_timestamp = datetime.now().timestamp()
            time_elapsed_since_hb = current_timestamp - hb_timestamp
            hb_interval = 30
            hb_grace_buffer = 10
            hb_cut_off_time = hb_interval + hb_grace_buffer

            if time_elapsed_since_hb > hb_cut_off_time:
                missed_hbs = \
                    int((current_timestamp - hb_timestamp) // hb_interval)
                status += \
                    "- *Health Checker ({})*: {} - Missed {} " \
                    "heartbeats.\n".format(
                        HEARTBEAT_HANDLER_NAME,
                        self._get_running_icon(False), missed_hbs)
                problems_in_checker = True
        else:
            status += "- *Health Checker ({})*: {} - No heartbeat " \
                      "yet.\n".format(HEARTBEAT_HANDLER_NAME,
                                      self._get_running_icon(False))
            problems_in_checker = True

        if self.redis.exists_unsafe(key_ping_publisher_hb):
            ping_publisher_hb = json.loads(
                self.redis.get_unsafe(key_ping_publisher_hb).decode())
            hb_timestamp = ping_publisher_hb['timestamp']

            current_timestamp = datetime.now().timestamp()
            time_elapsed_since_hb = current_timestamp - hb_timestamp
            hb_interval = 30
            hb_grace_buffer = 10
            hb_cut_off_time = hb_interval + hb_grace_buffer

            if time_elapsed_since_hb > hb_cut_off_time:
                missed_hbs = \
                    int((current_timestamp - hb_timestamp) // hb_interval)
                status += \
                    "- *Health Checker ({})*: {} - Missed {} " \
                    "heartbeats.\n".format(PING_PUBLISHER_NAME,
                                           self._get_running_icon(False),
                                           missed_hbs)
                problems_in_checker = True
        else:
            status += "- *Health Checker ({})*: {} - No heartbeat " \
                      "yet.\n".format(PING_PUBLISHER_NAME,
                                      self._get_running_icon(False))
            problems_in_checker = True

        # Just say that Health Checkers's components are ok if there are no
        # issues.
        if status == '':
            status += "- *Health Checker*: {}\n".format(
                self._get_running_icon(True))

        return status, problems_in_checker

    def _get_redis_based_status(self) -> str:
        associated_chains = self.associated_chains

        chain_names = [chain_name for _, chain_name in
                       associated_chains.items()]

        redis_accessible_status = ""
        redis_error_status = \
            "- *Redis*: {} \n".format(self._get_running_icon(False)) + \
            "- No {} alert is consider muted as Redis is " \
            "inaccessible.\n".format(', '.join(chain_names)) + \
            "- Cannot get Health Checker status as Redis is inaccessible.\n" + \
            "- Cannot get PANIC components' status as Redis is inaccessible.\n"
        unrecognized_error_status = \
            "- Could not get Redis status due to an unrecognized error. " \
            "Check the logs to debug the issue.\n" + \
            "- Cannot get mute status due to an unrecognized error.\n" + \
            "- Cannot get Health Checker status due to an unrecognized " \
            "error.\n" + \
            "- Cannot get PANIC components' status due to an unrecognized " \
            "error. \n"
        try:
            redis_accessible_status += "- *Redis*: {} \n".format(
                self._get_running_icon(True))
            redis_accessible_status += self._get_muted_status()
            health_checker_status, problems_in_health_checker = \
                self._get_health_checker_status()
            redis_accessible_status += health_checker_status
            redis_accessible_status += \
                self._get_panic_components_status(problems_in_health_checker)
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error("Error in redis when getting redis based "
                              "status: %s", e)
            return redis_error_status
        except Exception as e:
            self.logger.exception(e)
            self.logger.error("Could not get redis based status: %s", e)
            return unrecognized_error_status

        return redis_accessible_status

    @_execute_safely
    def status_callback(self, ack: Ack, say: Say,
                        command: Optional[Dict[str, Any]]) -> None:
        self._logger.info("/panicstatus: command=%s", command)

        # Acknowledge command request
        ack()
        # Start forming the status message
        say("Generating status...")

        mongo_based_status = self._get_mongo_based_status()
        rabbit_based_status = self._get_rabbit_based_status()
        redis_based_status = self._get_redis_based_status()

        status = mongo_based_status + rabbit_based_status + redis_based_status

        # Send status
        say(status[:-1] if status.endswith('\n') else status)

    @_execute_safely
    def unmute_callback(self, ack: Ack, say: Say,
                        command: Optional[Dict[str, Any]]) -> None:
        self._logger.info("/unmute: command=%s", command)

        # Acknowledge command request
        ack()

        say("Performing unmute...")

        associated_chains = self.associated_chains

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
                    successfully_unmuted_chains.append(
                        chain_name)
                else:
                    already_unmuted_chains.append(chain_name)
                    self.logger.info("%s has no muted severities.", chain_name)
            except (RedisError, ConnectionResetError) as e:
                self.logger.exception(e)
                self.logger.error("Could not unmute %s alerts due to a redis "
                                  "error: %s", chain_name, e)
                say(
                    "Redis error. Unmuting may not have been successful for "
                    "all chains. Please check /panicstatus or the logs to see "
                    "which chains were unmuted (if any) and that Redis is "
                    "online. Re-try again when the issue is solved.")
                return
            except Exception as e:
                self.logger.exception(e)
                self.logger.error("Could not unmute %s alerts due to an "
                                  "unrecognized error: %s", chain_name, e)
                say(
                    "Unrecognized error. Please debug the issue by looking at "
                    "the logs. Unmuting may not have been successful for all "
                    "chains. Please check /panicstatus or the logs to see "
                    "which "
                    "chains were unmuted (if any) and that Redis is online. "
                    "Re-try again when the issue is solved.")
                return

        res = "*Unmute result*:\n\n"
        if len(successfully_unmuted_chains) != 0:
            res += "- Successfully unmuted all {} alerts.\n".format(', '.join(
                successfully_unmuted_chains))

        if len(already_unmuted_chains) != 0:
            res += "- No {} alert severity was muted.\n".format(
                ', '.join(already_unmuted_chains))

        say(res[:-1] if res.endswith('\n') else res)

    @_execute_safely
    def mute_callback(self, ack: Ack, say: Say,
                      command: Optional[Dict[str, Any]]) -> None:
        self._logger.info("/panicmute: command=%s", command)

        # Acknowledge command request
        ack()

        say("Performing mute...")

        # Expected: /panicmute or /panicmute List[<severity>]
        inputted_severities = command.get('text', '').split(' ')[1:]
        unrecognized_severities = []
        recognized_severities = []

        associated_chains = self.associated_chains
        chain_names = \
            [chain_name for _, chain_name in associated_chains.items()]

        # The Internal Severity isn't something the user should care about.
        panic_severities = [severity.value for severity in Severity
                            if Severity.INTERNAL.value != severity.value]
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
            self.logger.error("Unrecognized severity/severities %s",
                              ', '.join(unrecognized_severities))
            say(
                "Muting Failed: Invalid severity/severities {}. Please enter "
                "a combination of CRITICAL, WARNING, INFO or ERROR separated "
                "by spaces after the /panicmute command. You can enter no "
                "severities and PANIC will automatically mute all alerts for "
                "{}".format(', '.join(unrecognized_severities),
                            ', '.join(chain_names)))
            return

        for chain_id, chain_name in associated_chains.items():
            try:
                chain_hash = Keys.get_hash_parent(chain_id)
                mute_alerts_key = Keys.get_chain_mute_alerts()

                if self.redis.hexists_unsafe(chain_hash, mute_alerts_key):
                    severities_muted = json.loads(self.redis.hget_unsafe(
                        chain_hash, mute_alerts_key).decode())
                    for severity in panic_severities:
                        if severity in recognized_severities:
                            severities_muted[severity] = True
                else:
                    severities_muted = {}
                    for severity in panic_severities:
                        severities_muted[severity] = \
                            severity in recognized_severities

                self.redis.hset_unsafe(chain_hash, mute_alerts_key,
                                       json.dumps(severities_muted))
                self.logger.info("Successfully muted %s alerts.", chain_name)
            except (RedisError, ConnectionResetError) as e:
                self.logger.exception(e)
                self.logger.error("Could not mute %s alerts due to a redis "
                                  "error: %s", chain_name, e)
                say(
                    "Redis error. Muting may not have been successful for all "
                    "chains. Please check /panicstatus or the logs to see "
                    "which "
                    "chains were muted (if any) and that Redis is online. "
                    "Re-try again when the issue is solved.")
                return
            except Exception as e:
                self.logger.exception(e)
                self.logger.error("Could not mute %s alerts due to an "
                                  "unrecognized error: %s", chain_name, e)
                say(
                    "Unrecognized error. Please debug the issue by looking at "
                    "the logs. Muting may not have been successful for all "
                    "chains. Please check /panicstatus or the logs to see "
                    "which "
                    "chains were muted (if any) and that Redis is online. "
                    "Re-try again when the issue is solved.")
                return

        say(
            "Successfully muted all {} alerts for chain(s) {}. Give a few "
            "seconds until the alerter picks this up.".format(
                ', '.join(recognized_severities), ', '.join(chain_names)))

    @_execute_safely
    def muteall_callback(self, ack: Ack, say: Say,
                         command: Optional[Dict[str, Any]]) \
            -> None:
        self._logger.info("/muteall: command=%s", command)

        # Acknowledge command request
        ack()

        say("Performing muteall...")

        # Expected: /muteall or /muteall List[<severity>]
        inputted_severities = command.get('text', '').split(' ')[1:]
        unrecognized_severities = []
        recognized_severities = []

        # The Internal Severity isn't something the user should care about.
        panic_severities = [severity.value for severity in Severity
                            if Severity.INTERNAL.value != severity.value]

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
            self.logger.error("Unrecognized severity/severities %s",
                              ', '.join(unrecognized_severities))
            escaped_unrecognized_severities = \
                [unrecognized_severity for
                 unrecognized_severity in unrecognized_severities]
            msg = "Muting Failed: Invalid severity/severities {}. Please " \
                  "enter a combination of CRITICAL, WARNING, INFO or ERROR " \
                  "separated by spaces after the /muteall command. " \
                  "*Example*: /muteall WARNING CRITICAL. You can enter no " \
                  "severities and PANIC will automatically mute all alerts " \
                  "for all " \
                  "chains".format(', '.join(escaped_unrecognized_severities))
            say(msg[:-1] if msg.endswith('\n') else msg)
            return

        try:
            mute_alerter_key = Keys.get_alerter_mute()

            # Load existing muted severities if they exist. This has to be done
            # so that we do not unmute already muted severities
            if self.redis.exists_unsafe(mute_alerter_key):
                severities_muted = json.loads(self.redis.get_unsafe(
                    mute_alerter_key).decode())
                for severity in panic_severities:
                    if severity in recognized_severities:
                        severities_muted[severity] = True
            else:
                severities_muted = {}
                for severity in panic_severities:
                    severities_muted[severity] = \
                        severity in recognized_severities

            self.redis.set_unsafe(mute_alerter_key,
                                  json.dumps(severities_muted))
            self.logger.info("Successfully muted all %s alerts for every "
                             "chain.", ', '.join(recognized_severities))
            say(
                "Successfully muted all {} alerts for every chain. Give a few "
                "seconds until the alerter picks this up.".format(
                    ', '.join(recognized_severities)))
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error("I could not mute all %s alerts due to a Redis "
                              "error.", ', '.join(recognized_severities))
            say(
                "I could not mute all {} alerts due to a Redis error. Please "
                "check /panicstatus or the logs to see if Redis is online "
                "and/or "
                "re-try again.".format(', '.join(recognized_severities)))
        except Exception as e:
            self.logger.exception(e)
            self.logger.error("I could not mute all %s alerts due to an "
                              "unrecognized error.",
                              ', '.join(recognized_severities))
            say(
                "Unrecognized error, please check the logs to debug the "
                "issue. Please also check /panicstatus to see if the muting "
                "was "
                "successful and that Redis is online. Re-try again when the "
                "issue is solved.")

    @_execute_safely
    def unmuteall_callback(self, ack: Ack, say: Say,
                           command: Optional[Dict[str, Any]]) \
            -> None:
        self.logger.info("/unmuteall: command=%s", command)

        # Acknowledge command request
        ack()

        say("Performing unmuteall...")

        at_least_one_chain_was_muted = False
        try:
            mute_alerter_key = Keys.get_alerter_mute()

            # We must first unmute severities which are muted for all chains
            if self.redis.exists_unsafe(mute_alerter_key):
                self.redis.remove_unsafe(mute_alerter_key)
                self.logger.info("Successfully deleted %s from redis",
                                 mute_alerter_key)
                at_least_one_chain_was_muted = True
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error("Unmuting unsuccessful due to an issue with "
                              "redis %s", e)
            say(
                "Unmuting unsuccessful due to an issue with Redis. Check "
                "/panicstatus or the logs to see if Redis is online and/or "
                "re-try "
                "again.")
            return
        except Exception as e:
            self.logger.exception(e)
            self.logger.error("It may be that not all chains were unmuted "
                              "due to an unrecognized issue: %s", e)
            say(
                "Unrecognized error, please check the logs to debug the "
                "issue. Please also check /panicstatus to see if the unmuting "
                "was "
                "successful and that Redis is online. Re-try again when the "
                "issue is solved.")
            return

        try:
            # We must unmute severities which are muted for specific chains
            parent_hash = Keys.get_hash_parent_raw()
            chain_hashes_list = self.redis.get_keys_unsafe(
                '*' + parent_hash + '*')

            for chain_hash in chain_hashes_list:
                mute_alerts_key = Keys.get_chain_mute_alerts()
                if self.redis.hexists_unsafe(chain_hash, mute_alerts_key):
                    self.redis.hremove_unsafe(chain_hash, mute_alerts_key)
                    self.logger.info("All alert severities have been unmuted "
                                     "for chain with hash %s.", chain_hash)
                    at_least_one_chain_was_muted = True
        except (RedisError, ConnectionResetError) as e:
            self.logger.exception(e)
            self.logger.error("It may be that not all chains were unmuted "
                              "due to an issue with redis: %s", e)
            say(
                "It may be that not all chains were unmuted due to a Redis "
                "error. Check /panicstatus or the logs to see if unmuting was "
                "successful and that redis is online. Re-try again when the "
                "issue is solved.")
            return
        except Exception as e:
            self.logger.exception(e)
            self.logger.error("It may be that not all chains were unmuted "
                              "due to an unrecognized issue: %s", e)
            say(
                "It may be that not all chains were unmuted due to an "
                "unrecognized error. Check /panicstatus or the logs to see if "
                "the "
                "unmuting was successful and that redis is online. Re-try "
                "again when the issue is solved.")
            return

        if at_least_one_chain_was_muted:
            say(
                "Successfully unmuted all alert severities of all chains "
                "being monitored in panic (including general repositories and "
                "general systems, as they belong to the chain GENERAL).")
        else:
            say("No alert severity was muted for any "
                "chain.")

    @_execute_safely
    def help_callback(self, ack: Ack, say: Say,
                      command: Optional[Dict[str, Any]]) -> None:
        self._logger.info("/help: command=%s", command)

        # Acknowledge command request
        ack()

        associated_chains = self.associated_chains
        chain_names = \
            [chain_name for _, chain_name in
             associated_chains.items()]

        # Send help message with available commands
        msg = "Hey! These are the available commands:\n" \
              "  /start: Welcome message\n" \
              "  /ping: Ping the Slack Commands Handler\n" \
              "  /panicmute List(<severity>) (*Example*: /panicmute INFO " \
              "CRITICAL): " \
              "Mutes List(<severity>) on all channels for chains {}. If the " \
              "list of severities is not given, all alerts for chains {} are " \
              "muted on all channels.\n" \
              "  /unmute: Unmutes all alert severities on all channels for " \
              "chains {}.\n" \
              "  /muteall List(<severity>) (*Example*: /muteall INFO " \
              "CRITICAL): Mutes List(<severity>) on all channels for every " \
              "chain being monitored. If the list of severities is not " \
              "given, all alerts for all chains are muted on all channels.\n" \
              "  /unmuteall: Unmutes all alert severities on all channels " \
              "for all chains being monitored.\n" \
              "  /panicstatus: Gives a live status of PANIC's components\n" \
              "  /help: Shows this message".format(', '.join(chain_names),
                                                   ', '.join(chain_names),
                                                   ', '.join(chain_names),
                                                   ', '.join(chain_names))
        say(msg[:-1] if msg.endswith('\n') else msg)

    @_execute_safely
    def start_callback(self, ack: Ack, say: Say,
                       command: Optional[Dict[str, Any]]) -> None:
        self.logger.info("/start: command=%s", command)

        # Acknowledge command request
        ack()
        # Send welcome message
        say("Welcome to PANIC's Slack commands!\n"
            "Type /help for more information.")

    def unknown_callback(self, *args) -> None:
        """
        We are not implementing the unknown_callback function since
        Slack handles unknown/invalid commands automatically.
        """
        pass

    _execute_safely = staticmethod(_execute_safely)
