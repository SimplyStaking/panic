"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RedisInterface = exports.addPostfixToKeys = exports.addPrefixToKeys = exports.getBaseChainKeys = exports.getAlertKeysRepo = exports.getAlertKeysSystem = exports.getConfigKeys = exports.getChainKeys = exports.getComponentKeys = exports.getGitHubKeys = exports.getSystemKeys = exports.getUniqueKeys = exports.getRedisHashes = exports.baseChainsRedis = void 0;
var redis_1 = __importDefault(require("redis"));
var msgs_1 = require("./msgs");
var errors_1 = require("./errors");
exports.baseChainsRedis = ['Cosmos', 'Substrate', 'General'];
var getRedisHashes = function () { return ({
    parent: 'hash_p1'
}); };
exports.getRedisHashes = getRedisHashes;
var getUniqueKeys = function () { return ({
    mute: 'a1',
}); };
exports.getUniqueKeys = getUniqueKeys;
var getSystemKeys = function () { return ({
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
}); };
exports.getSystemKeys = getSystemKeys;
var getGitHubKeys = function () { return ({
    no_of_releases: 'gh1',
    last_monitored: 'gh2',
}); };
exports.getGitHubKeys = getGitHubKeys;
var getComponentKeys = function () { return ({
    heartbeat: 'c1'
}); };
exports.getComponentKeys = getComponentKeys;
var getChainKeys = function () { return ({
    mute_alerts: 'ch1'
}); };
exports.getChainKeys = getChainKeys;
var getConfigKeys = function () { return ({
    config: 'conf1'
}); };
exports.getConfigKeys = getConfigKeys;
var getAlertKeysSystem = function () { return ({
    open_file_descriptors: 'alert1',
    system_cpu_usage: 'alert2',
    system_storage_usage: 'alert3',
    system_ram_usage: 'alert4',
    system_is_down: 'alert5',
    metric_not_found: 'alert6',
    invalid_url: 'alert7',
}); };
exports.getAlertKeysSystem = getAlertKeysSystem;
var getAlertKeysRepo = function () { return ({
    github_release: 'alert8',
    cannot_access_github: 'alert9',
}); };
exports.getAlertKeysRepo = getAlertKeysRepo;
var getBaseChainKeys = function () { return ({
    monitorables_info: 'bc1'
}); };
exports.getBaseChainKeys = getBaseChainKeys;
var addPrefixToKeys = function (keysObject, prefix) {
    var newObject = __assign({}, keysObject);
    Object.keys(keysObject)
        .forEach(function (key) {
        newObject[key] = "" + prefix + keysObject[key];
    });
    return newObject;
};
exports.addPrefixToKeys = addPrefixToKeys;
var addPostfixToKeys = function (keysObject, postfix) {
    var newObject = __assign({}, keysObject);
    Object.keys(keysObject)
        .forEach(function (key) {
        newObject[key] = "" + keysObject[key] + postfix;
    });
    return newObject;
};
exports.addPostfixToKeys = addPostfixToKeys;
var RedisInterface = /** @class */ (function () {
    function RedisInterface(host, port, db, password) {
        if (host === void 0) { host = "localhost"; }
        if (port === void 0) { port = 6379; }
        if (db === void 0) { db = 10; }
        this.host = host;
        this.port = port;
        this.db = db;
        this.password = password;
        this._client = undefined;
    }
    Object.defineProperty(RedisInterface.prototype, "client", {
        get: function () {
            return this._client;
        },
        enumerable: false,
        configurable: true
    });
    RedisInterface.prototype.connect = function () {
        if (this._client && this._client.connected) {
            return;
        }
        this._client = redis_1.default.createClient({
            host: this.host,
            port: this.port,
            db: this.db,
            password: this.password,
            no_ready_check: true,
            retry_strategy: function (_) {
                return undefined;
            }
        });
        this._client.on('error', function (error) {
            console.error(error);
        });
        this._client.on('ready', function () {
            console.log(msgs_1.MSG_REDIS_CONNECTION_ESTABLISHED);
        });
        this._client.on('end', function () {
            console.error(msgs_1.MSG_REDIS_DISCONNECTED);
        });
        return;
    };
    RedisInterface.prototype.disconnect = function () {
        if (this._client) {
            this._client.quit();
        }
        else {
            throw new errors_1.RedisClientNotInitialised();
        }
    };
    return RedisInterface;
}());
exports.RedisInterface = RedisInterface;
