import redis, {RetryStrategyOptions} from "redis"
import {MaxRetryTimeExceeded, RedisConnectionRefused} from "./errors"
import {MSG_REDIS_CONNECTED, MSG_REDIS_RECONNECTING} from "./msgs";

export class RedisAPI {
    host: string;
    port: number;
    password?: string;
    client?: redis.RedisClient;

    constructor(host = "localhost", port = 6379, password?: string) {
        this.host = host;
        this.port = port;
        this.password = password;
        this.client = undefined;
    }

    connect() {
        this.client = redis.createClient({
            host: this.host,
            port: this.port,
            password: this.password,
            no_ready_check: true,
            retry_strategy: (options: RetryStrategyOptions) => {
                if (options.error && options.error.code === 'ECONNREFUSED') {
                    // End reconnecting on a specific error and flush all
                    // commands with an individual error.
                    return new RedisConnectionRefused();
                }
                if (options.total_retry_time > 1000 * 60 * 60) {
                    // End reconnecting after a specific timeout and flush all
                    // commands with an individual error
                    return new MaxRetryTimeExceeded();
                }
                if (options.attempt > 10) {
                    // End reconnecting with built in error
                    return undefined;
                }
                // reconnect after
                return Math.min(options.attempt * 100, 3000);
            },
            connect_timeout: 10000, // 10 * 1000 ms
        });
        this.client.on('error', (error) => {
            console.error(error);
        });
        this.client.on('reconnecting', () => {
            console.log(MSG_REDIS_RECONNECTING);
        });
        this.client.on('ready', () => {
            console.debug(MSG_REDIS_CONNECTED);
        });
        return;
    }

    disconnect() {
        if (this.client) {
            this.client.quit()
        }
    }

}

// TODO: Disconnect, hset, set, get, hget, multiple gets and sets for both h and
//     : with no h.

// TODO: In the future we might persist a redis connection, thus the retry
//     : strategy may never terminate. Tomorrow check if this is possible.
