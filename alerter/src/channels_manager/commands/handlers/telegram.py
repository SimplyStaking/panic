from pymongo.errors import PyMongoError
from redis import RedisError
from telegram import Update

from src.channels_manager.commands.handlers.handler import CommandHandler \
    as CmdHandler
import logging

from src.data_store.mongo import MongoApi
from src.data_store.redis import RedisApi
from src.message_broker.rabbitmq import RabbitMQApi

# TODO: Tomorrow start by fixing circular import in Update and implement
#     : ping for rabbit. Start by testing whether a meaningful exception is
#     : raised if rabbit is down and we try to connect.

class TelegramCommandHandlers(CmdHandler):
    def __init__(self, handler_name: str, logger: logging.Logger,
                 rabbit: RabbitMQApi, redis: RedisApi, mongo: MongoApi) -> None:
        super().__init__(handler_name, logger)

        self._rabbit = rabbit
        self._redis = redis
        self._mongo = mongo

    @property
    def rabbit(self) -> RabbitMQApi:
        return self._rabbit

    @property
    def redis(self) -> RedisApi:
        return self._redis

    @property
    def mongo(self) -> MongoApi:
        return self._mongo

    def redis_running(self) -> bool:
        try:
            self._redis.ping_unsafe()
            return True
        except (RedisError, ConnectionResetError):
            pass
        except Exception as e:
            self._logger.error('Unrecognized error when accessing Redis: %s', e)
        return False

    def mongo_running(self) -> bool:
        try:
            self._mongo.ping_unsafe()
            return True
        except PyMongoError:
            pass
        except Exception as e:
            self._logger.error('Unrecognized error when accessing Mongo: %s', e)
        return False

    def rabbit_running(self) -> bool:
        pass

    @staticmethod
    def formatted_reply(update: Update, reply: str):
        # Adds Markdown formatting
        update.message.reply_text(reply, parse_mode='MarkdownV2')

    def unknown_callback(self) -> None:
        pass

    def ping_callback(self) -> None:
        pass

    def health_callback(self) -> None:
        pass

    def unsnooze_callback(self) -> None:
        pass

    def snooze_callback(self) -> None:
        pass

    def unmute_callback(self) -> None:
        pass

    def mute_callback(self) -> None:
        pass

    def help_callback(self) -> None:
        pass

    def start_callback(self) -> None:
        pass