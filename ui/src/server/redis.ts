import redis, {RetryStrategyOptions} from "redis"
import {MSG_REDIS_CONNECTION_ESTABLISHED, MSG_REDIS_DISCONNECTED} from "./msgs";
import {
    AlertKeysRepo,
    AlertKeysSystem,
    BaseChainKeys,
    ChainKeys,
    ComponentKeys,
    ConfigKeys,
    GitHubKeys,
    RedisHashes,
    RedisKeys,
    SystemKeys,
    UniqueKeys
} from "./types";
import {RedisClientNotInitialised} from "./errors";

export const baseChainsRedis = ['Cosmos', 'Substrate', 'General'];

export const getRedisHashes = (): RedisHashes => ({
    parent: 'hash_p1'
});

export const getUniqueKeys = (): UniqueKeys => ({
    mute: 'a1',
});

export const getSystemKeys = (): SystemKeys => ({
    process_cpu_seconds_total: 's1',
    process_memory_usage: 's2',
    virtual_memory_usage: 's3',
    open_file_descriptors: 's4',
    system_cpu_usage: 's5',
    system_ram_usage: 's6',
    system_storage_usage: 's7',
    network_transmit_bytes_per_second: 's8',
    network_receive_bytes_per_second: 's9',
    network_receive_bytes_total: 's10',
    network_transmit_bytes_total: 's11',
    disk_io_time_seconds_total: 's12',
    disk_io_time_seconds_in_interval: 's13',
    last_monitored: 's14',
    system_went_down_at: 's15',
});

export const getGitHubKeys = (): GitHubKeys => ({
    no_of_releases: 'gh1',
    last_monitored: 'gh2',
});

export const getComponentKeys = (): ComponentKeys => ({
    heartbeat: 'c1'
});

export const getChainKeys = (): ChainKeys => ({
    mute_alerts: 'ch1'
});

export const getConfigKeys = (): ConfigKeys => ({
    config: 'conf1'
});

export const getAlertKeysSystem = (): AlertKeysSystem => ({
    open_file_descriptors: 'alert1',
    system_cpu_usage: 'alert2',
    system_storage_usage: 'alert3',
    system_ram_usage: 'alert4',
    system_is_down: 'alert5',
    metric_not_found: 'alert6',
    invalid_url: 'alert7',
});

export const getAlertKeysRepo = (): AlertKeysRepo => ({
    github_release: 'alert8',
    cannot_access_github: 'alert9',
});

export const getBaseChainKeys = (): BaseChainKeys => ({
    monitorables_info: 'bc1'
});

export const addPrefixToKeys =
    (keysObject: RedisKeys, prefix: string): RedisKeys => {
        const newObject: RedisKeys = {...keysObject};
        Object.keys(keysObject)
            .forEach((key) => {
                newObject[key] = `${prefix}${keysObject[key]}`;
            });
        return newObject;
    };

export const addPostfixToKeys =
    (keysObject: RedisKeys, postfix: string): RedisKeys => {
        const newObject: RedisKeys = {...keysObject};
        Object.keys(keysObject)
            .forEach((key) => {
                newObject[key] = `${keysObject[key]}${postfix}`;
            });
        return newObject;
    };

export class RedisInterface {
    private readonly host: string;
    private readonly port: number;
    private readonly db: number;
    private readonly password?: string;
    private _client?: redis.RedisClient;

    constructor(host: string = "localhost", port: number = 6379,
                db: number = 10, password?: string) {
        this.host = host;
        this.port = port;
        this.db = db;
        this.password = password;
        this._client = undefined;
    }

    get client() {
        return this._client
    }

    connect() {
        if (this._client && this._client.connected) {
            return;
        }
        this._client = redis.createClient({
            host: this.host,
            port: this.port,
            db: this.db,
            password: this.password,
            no_ready_check: true,
            retry_strategy: (_: RetryStrategyOptions) => {
                return undefined
            }
        });
        this._client.on('error', (error) => {
            console.error(error);
        });
        this._client.on('ready', () => {
            console.log(MSG_REDIS_CONNECTION_ESTABLISHED);
        });
        this._client.on('end', () => {
            console.error(MSG_REDIS_DISCONNECTED);
        });
        return;
    }

    disconnect() {
        if (this._client) {
            this._client.quit();
        } else {
            throw new RedisClientNotInitialised()
        }
    }

}
