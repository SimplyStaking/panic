import distutils.util
import logging
from datetime import timedelta
from typing import Dict, Optional, List, Any

import redis

from src.utils.timing import TimedTaskLimiter
from src.utils.types import RedisType


class RedisApi:

    def __init__(self, logger: logging.Logger, db: int,
                 host: str = 'localhost', port: int = 6379,
                 password: str = '', namespace: str = '',
                 live_check_time_interval: timedelta = timedelta(seconds=60)) \
            -> None:
        self._logger = logger
        if password == '':
            self._redis = redis.Redis(host=host, port=port, db=db)
        else:
            self._redis = redis.Redis(host=host, port=port, db=db,
                                      password=password)
        self._namespace = namespace

        # The live check limiter means that we don't wait for connection
        # errors to occur to be able to continue, thus speeding everything up
        self._live_check_limiter = TimedTaskLimiter(live_check_time_interval)
        self._is_live = True  # This is necessary to initialise the variable
        self._set_as_live()

        self._logger.info("Redis initialised.")

    @property
    def is_live(self) -> bool:
        return self._is_live

    def _add_namespace(self, key: str) -> str:
        if not key.startswith(self._namespace + ':'):
            return self._namespace + ':' + key
        else:
            return key  # prevent adding namespace twice

    def _remove_namespace(self, key: str) -> str:
        if not key.startswith(self._namespace + ':'):
            return key  # prevent removing namespace twice
        else:
            return key.replace(self._namespace + ':', '', 1)

    def _set_as_live(self) -> None:
        if not self._is_live:
            self._logger.info("Redis is now accessible again.")
        self._is_live = True

    def _set_as_down(self) -> None:
        # If Redis is live or if we can check whether it is live (because the
        # live check time interval has passed), reset the live check limiter
        # so that usage of Redis is skipped for as long as the time interval
        if self._is_live or self._live_check_limiter.can_do_task():
            self._live_check_limiter.did_task()
            self._logger.warning("Redis is unusable for some reason. Stopping "
                                 "usage temporarily to improve performance.")
        self._is_live = False

    def _do_not_use_if_recently_went_down(self) -> bool:
        # If Redis is not live and cannot check if it is live return true
        return not self._is_live and not self._live_check_limiter.can_do_task()

    def _safe(self, function, args: List[Any], default_return: Any):
        # Given an "unsafe" function from below and its arguments, safe calls
        # the function with the provided arguments and performs exception
        # handling as well as returns a specified default upon failure
        try:
            if self._do_not_use_if_recently_went_down():
                return default_return
            ret = function(*args)
            self._set_as_live()
            return ret
        except Exception as e:
            self._logger.error("Redis error in %s: %s", function.__name__, e)
            self._set_as_down()
            return default_return

    def set_unsafe(self, key: str, value: RedisType):
        key = self._add_namespace(key)

        set_ret = self._redis.set(key, value)
        return set_ret

    def hset_unsafe(self, name: str, key: str, value: RedisType):
        name = self._add_namespace(name)

        set_ret = self._redis.hset(name, key, value)
        return set_ret

    def set_multiple_unsafe(self, key_values: Dict[str, RedisType]):
        # Add namespace to keys
        keys = list(key_values.keys())
        namespaced_keys = [self._add_namespace(k) for k in keys]
        for k, uk in zip(keys, namespaced_keys):
            key_values[uk] = key_values.pop(k)

        # Set multiple
        pipe = self._redis.pipeline()
        for key, value in key_values.items():
            pipe.set(key, value if value is not None else 'None')
        exec_ret = pipe.execute()
        return exec_ret

    def hset_multiple_unsafe(self, name: str, key_values: Dict[str, RedisType]):
        # Add namespace to hash name
        name = self._add_namespace(name)

        # Set multiple
        pipe = self._redis.pipeline()
        for key, value in key_values.items():
            pipe.hset(name, key, value if value is not None else 'None')
        exec_ret = pipe.execute()
        return exec_ret

    def set_for_unsafe(self, key: str, value: RedisType, time: timedelta):
        key = self._add_namespace(key)

        pipe = self._redis.pipeline()
        pipe.set(key, value)
        pipe.expire(key, time)
        exec_ret = pipe.execute()
        return exec_ret

    def time_to_live_unsafe(self, key: str):
        key = self._add_namespace(key)
        time_to_live = self._redis.ttl(key)

        # -1: Key exists but has no associated timeout
        # -2: Key does not exist
        if time_to_live == -1 or time_to_live == -2:
            return None
        else:
            return time_to_live

    def get_unsafe(self, key: str, default: Optional[bytes] = None) \
            -> Optional[bytes]:
        key = self._add_namespace(key)

        if self.exists_unsafe(key):
            get_ret = self._redis.get(key)
            if get_ret.decode('UTF-8') == 'None':
                return None
            else:
                return get_ret
        else:
            return default

    def hget_unsafe(self, name: str, key: str,
                    default: Optional[bytes] = None) -> Optional[bytes]:
        name = self._add_namespace(name)

        if self.hexists_unsafe(name, key):
            get_ret = self._redis.hget(name, key)
            if get_ret.decode('UTF-8') == 'None':
                return None
            else:
                return get_ret
        else:
            return default

    def get_int_unsafe(self, key: str, default: Optional[int] = None) \
            -> Optional[int]:
        key = self._add_namespace(key)

        get_ret = self.get_unsafe(key, None)
        try:
            return int(get_ret) if get_ret is not None else default
        except ValueError:
            self._logger.error("Could not convert value %s of key %s to an "
                               "integer. Defaulting to value %s.", get_ret, key,
                               default)
            return default

    def hget_int_unsafe(self, name: str, key: str,
                        default: Optional[int] = None) -> Optional[int]:
        name = self._add_namespace(name)

        get_ret = self.hget_unsafe(name, key, None)
        try:
            return int(get_ret) if get_ret is not None else default
        except ValueError:
            self._logger.error("Could not convert value %s of key %s to an "
                               "integer. Defaulting to value %s.", get_ret, key,
                               default)
            return default

    def get_bool_unsafe(self, key: str, default: Optional[bool] = None) \
            -> Optional[bool]:
        key = self._add_namespace(key)
        get_ret = self.get_unsafe(key, None)

        if get_ret is not None and get_ret.decode() in ['True', 'False']:
            return bool(distutils.util.strtobool(get_ret.decode()))

        return default

    def hget_bool_unsafe(self, name: str, key: str,
                         default: Optional[bool] = None) -> Optional[bool]:
        name = self._add_namespace(name)
        get_ret = self.hget_unsafe(name, key, None)

        if get_ret is not None and get_ret.decode() in ['True', 'False']:
            return bool(distutils.util.strtobool(get_ret.decode()))

        return default

    def exists_unsafe(self, key: str) -> bool:
        key = self._add_namespace(key)
        return bool(self._redis.exists(key))

    def hexists_unsafe(self, name: str, key: str) -> bool:
        name = self._add_namespace(name)
        return bool(self._redis.hexists(name, key))

    def get_keys_unsafe(self, pattern: str = "*") -> List[str]:
        pattern = self._add_namespace(pattern)

        # Decode and remove namespace
        keys_list = self._redis.keys(pattern)
        keys_list = [k.decode('utf8') for k in keys_list]
        keys_list = [self._remove_namespace(k) for k in keys_list]

        return keys_list

    def remove_unsafe(self, *keys):
        keys = [self._add_namespace(k) for k in keys]
        return self._redis.delete(*keys)

    def hremove_unsafe(self, name: str, *keys):
        name = self._add_namespace(name)
        return self._redis.hdel(name, *keys)

    def hremove(self, name: str, *keys):
        return self._safe(self.hremove_unsafe, [name, *keys], None)

    # TODO add unit tests for this function
    def hkeys_unsafe(self, name: str):
        name = self._add_namespace(name)

        keys_list = self._redis.hkeys(name)
        keys_list = [k.decode('utf8') for k in keys_list]
        keys_list = [self._remove_namespace(k) for k in keys_list]

        return keys_list

    def hkeys(self, name: str):
        return self._safe(self.hkeys_unsafe, [name], None)

    def delete_all_unsafe(self):
        return self._redis.flushdb()

    def set(self, key: str, value: RedisType):
        return self._safe(self.set_unsafe, [key, value], None)

    def hset(self, name: str, key: str, value: RedisType):
        return self._safe(self.hset_unsafe, [name, key, value], None)

    def set_multiple(self, key_values: Dict[str, RedisType]):
        return self._safe(self.set_multiple_unsafe, [key_values], None)

    def hset_multiple(self, name: str, key_values: Dict[str, RedisType]):
        return self._safe(self.hset_multiple_unsafe, [name, key_values], None)

    def set_for(self, key: str, value: RedisType, time: timedelta):
        return self._safe(self.set_for_unsafe, [key, value, time], None)

    def time_to_live(self, key: str):
        return self._safe(self.time_to_live_unsafe, [key], None)

    def get(self, key: str, default: Optional[bytes] = None) -> Optional[bytes]:
        return self._safe(self.get_unsafe, [key, default], default)

    def hget(self, name: str, key: str, default: Optional[bytes] = None) \
            -> Optional[bytes]:
        return self._safe(self.hget_unsafe, [name, key, default], default)

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        return self._safe(self.get_int_unsafe, [key, default], default)

    def hget_int(self, name: str, key: str, default: Optional[int] = None) \
            -> Optional[int]:
        return self._safe(self.hget_int_unsafe, [name, key, default], default)

    def get_bool(self, key: str, default: Optional[bool] = None) \
            -> Optional[bool]:
        return self._safe(self.get_bool_unsafe, [key, default], default)

    def hget_bool(self, name: str, key: str, default: Optional[bool] = None) \
            -> Optional[bool]:
        return self._safe(self.hget_bool_unsafe, [name, key, default], default)

    def exists(self, key: str) -> bool:
        return self._safe(self.exists_unsafe, [key], False)

    def hexists(self, name: str, key: str) -> bool:
        return self._safe(self.hexists_unsafe, [name, key], False)

    def get_keys(self, pattern: str = "*") -> List[str]:
        return self._safe(self.get_keys_unsafe, [pattern], [])

    def remove(self, *keys):
        return self._safe(self.remove_unsafe, [*keys], None)

    def delete_all(self):
        return self._safe(self.delete_all_unsafe, [], None)

    def ping_unsafe(self) -> bool:
        return self._redis.ping()
