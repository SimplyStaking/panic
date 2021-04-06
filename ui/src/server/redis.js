"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RedisInterface = exports.addPostfixToKeys = exports.addPrefixToKeys = exports.getBaseChainKeys = exports.getAlertKeysRepo = exports.getAlertKeysSystem = exports.getConfigKeys = exports.getChainKeys = exports.getComponentKeys = exports.getGitHubKeys = exports.getSystemKeys = exports.getUniqueKeys = exports.getRedisHashes = exports.baseChainsRedis = void 0;
const redis_1 = __importDefault(require("redis"));
const msgs_1 = require("./msgs");
const errors_1 = require("./errors");
exports.baseChainsRedis = ['Cosmos', 'Substrate', 'General'];
const getRedisHashes = () => ({
    parent: 'hash_p1'
});
exports.getRedisHashes = getRedisHashes;
const getUniqueKeys = () => ({
    mute: 'a1',
});
exports.getUniqueKeys = getUniqueKeys;
const getSystemKeys = () => ({
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
exports.getSystemKeys = getSystemKeys;
const getGitHubKeys = () => ({
    no_of_releases: 'gh1',
    last_monitored: 'gh2',
});
exports.getGitHubKeys = getGitHubKeys;
const getComponentKeys = () => ({
    heartbeat: 'c1'
});
exports.getComponentKeys = getComponentKeys;
const getChainKeys = () => ({
    mute_alerts: 'ch1'
});
exports.getChainKeys = getChainKeys;
const getConfigKeys = () => ({
    config: 'conf1'
});
exports.getConfigKeys = getConfigKeys;
const getAlertKeysSystem = () => ({
    open_file_descriptors: 'alert1',
    system_cpu_usage: 'alert2',
    system_storage_usage: 'alert3',
    system_ram_usage: 'alert4',
    system_is_down: 'alert5',
    metric_not_found: 'alert6',
    invalid_url: 'alert7',
});
exports.getAlertKeysSystem = getAlertKeysSystem;
const getAlertKeysRepo = () => ({
    github_release: 'alert8',
    cannot_access_github: 'alert9',
});
exports.getAlertKeysRepo = getAlertKeysRepo;
const getBaseChainKeys = () => ({
    monitorables_info: 'bc1'
});
exports.getBaseChainKeys = getBaseChainKeys;
const addPrefixToKeys = (keysObject, prefix) => {
    const newObject = Object.assign({}, keysObject);
    Object.keys(keysObject)
        .forEach((key) => {
        newObject[key] = `${prefix}${keysObject[key]}`;
    });
    return newObject;
};
exports.addPrefixToKeys = addPrefixToKeys;
const addPostfixToKeys = (keysObject, postfix) => {
    const newObject = Object.assign({}, keysObject);
    Object.keys(keysObject)
        .forEach((key) => {
        newObject[key] = `${keysObject[key]}${postfix}`;
    });
    return newObject;
};
exports.addPostfixToKeys = addPostfixToKeys;
class RedisInterface {
    constructor(host = "localhost", port = 6379, db = 10, password) {
        this.host = host;
        this.port = port;
        this.db = db;
        this.password = password;
        this._client = undefined;
    }
    get client() {
        return this._client;
    }
    connect() {
        if (this._client && this._client.connected) {
            return;
        }
        this._client = redis_1.default.createClient({
            host: this.host,
            port: this.port,
            db: this.db,
            password: this.password,
            no_ready_check: true,
            retry_strategy: (_) => {
                return undefined;
            }
        });
        this._client.on('error', (error) => {
            console.error(error);
        });
        this._client.on('ready', () => {
            console.log(msgs_1.MSG_REDIS_CONNECTION_ESTABLISHED);
        });
        this._client.on('end', () => {
            console.error(msgs_1.MSG_REDIS_DISCONNECTED);
        });
        return;
    }
    disconnect() {
        if (this._client) {
            this._client.quit();
        }
        else {
            throw new errors_1.RedisClientNotInitialised();
        }
    }
}
exports.RedisInterface = RedisInterface;
