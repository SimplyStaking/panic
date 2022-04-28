import redis, {RetryStrategyOptions} from "redis"
import {MSG_REDIS_CONNECTION_ESTABLISHED, MSG_REDIS_DISCONNECTED} from "./msgs";
import {
    AlertKeysDockerHubRepo,
    AlertKeysGitHubRepo,
    AlertKeysNode,
    AlertKeysSystem,
    ChainKeys,
    ChainlinkNodeKeys,
    ComponentKeys,
    GitHubKeys,
    RedisHashes,
    RedisKeys,
    SystemKeys,
    UniqueKeys
} from "./types";
import {RedisClientNotInitialised} from "./errors";

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

export const getChainlinkNodeKeys = (): ChainlinkNodeKeys => ({
    current_height: 'cl1',
    total_block_headers_received: 'cl2',
    max_pending_tx_delay: 'cl3',
    process_start_time_seconds: 'cl4',
    total_gas_bumps: 'cl5',
    total_gas_bumps_exceeds_limit: 'cl6',
    no_of_unconfirmed_txs: 'cl7',
    total_errored_job_runs: 'cl8',
    current_gas_price_info: 'cl9',
    eth_balance_info: 'cl10',
    went_down_at_prometheus: 'cl11',
    last_prometheus_source_used: 'cl12',
    last_monitored_prometheus: 'cl13',
});

export const getComponentKeys = (): ComponentKeys => ({
    heartbeat: 'c1'
});

export const getChainKeys = (): ChainKeys => ({
    mute_alerts: 'ch1'
});

export const alertKeysSystemPrefix: string = 'alert_system';
export const alertKeysClNodePrefix: string = 'alert_cl_node';
export const alertKeysEvmNodePrefix: string = 'alert_evm_node';
export const alertKeysCosmosNodePrefix: string = 'alert_cosmos_node';
export const alertKeysClContractPrefix: string = 'alert_cl_contract';
export const alertKeysGitHubPrefix: string = 'alert_github';
export const alertKeysDockerHubPrefix: string = 'alert_dockerhub';
export const alertKeysChainSourced: string[] = [
    'alert_cl_contract4',
    'alert_cl_contract5',
    'alert_cosmos_network1',
    'alert_cosmos_network2',
    'alert_cosmos_network3',
    'alert_cosmos_network4'
]

export const getAlertKeysSystem = (): AlertKeysSystem => ({
    open_file_descriptors: `${alertKeysSystemPrefix}1`,
    system_cpu_usage: `${alertKeysSystemPrefix}2`,
    system_storage_usage: `${alertKeysSystemPrefix}3`,
    system_ram_usage: `${alertKeysSystemPrefix}4`,
    system_is_down: `${alertKeysSystemPrefix}5`,
    metric_not_found: `${alertKeysSystemPrefix}6`,
    invalid_url: `${alertKeysSystemPrefix}7`,
});

export const getAlertKeysNode = (): AlertKeysNode => ({
    // Chainlink Nodes
    cl_head_tracker_current_head: `${alertKeysClNodePrefix}1`,
    cl_head_tracker_heads_received_total: `${alertKeysClNodePrefix}2`,
    cl_max_unconfirmed_blocks: `${alertKeysClNodePrefix}3`,
    cl_process_start_time_seconds: `${alertKeysClNodePrefix}4`,
    cl_tx_manager_gas_bump_exceeds_limit_total: `${alertKeysClNodePrefix}5`,
    cl_unconfirmed_transactions: `${alertKeysClNodePrefix}6`,
    cl_run_status_update_total: `${alertKeysClNodePrefix}7`,
    cl_eth_balance_amount: `${alertKeysClNodePrefix}8`,
    cl_eth_balance_amount_increase: `${alertKeysClNodePrefix}9`,
    cl_invalid_url: `${alertKeysClNodePrefix}10`,
    cl_metric_not_found: `${alertKeysClNodePrefix}11`,
    cl_node_is_down: `${alertKeysClNodePrefix}12`,
    cl_prometheus_is_down: `${alertKeysClNodePrefix}13`,
    // EVM Nodes
    evm_node_is_down: `${alertKeysEvmNodePrefix}1`,
    evm_block_syncing_block_height_difference: `${alertKeysEvmNodePrefix}2`,
    evm_block_syncing_no_change_in_block_height: `${alertKeysEvmNodePrefix}3`,
    evm_invalid_url: `${alertKeysEvmNodePrefix}4`,
    // Cosmos Nodes
    cosmos_node_is_down: `${alertKeysCosmosNodePrefix}1`,
    cosmos_node_slashed: `${alertKeysCosmosNodePrefix}2`,
    cosmos_node_syncing: `${alertKeysCosmosNodePrefix}3`,
    cosmos_node_active: `${alertKeysCosmosNodePrefix}4`,
    cosmos_node_jailed: `${alertKeysCosmosNodePrefix}5`,
    cosmos_node_blocks_missed: `${alertKeysCosmosNodePrefix}6`,
    cosmos_node_change_in_height: `${alertKeysCosmosNodePrefix}7`,
    cosmos_node_height_difference: `${alertKeysCosmosNodePrefix}8`,
    cosmos_node_prometheus_url_invalid: `${alertKeysCosmosNodePrefix}9`,
    cosmos_node_cosmos_rest_url_invalid: `${alertKeysCosmosNodePrefix}10`,
    cosmos_node_tendermint_rpc_url_invalid: `${alertKeysCosmosNodePrefix}11`,
    cosmos_node_prometheus_is_down: `${alertKeysCosmosNodePrefix}12`,
    cosmos_node_cosmos_rest_is_down: `${alertKeysCosmosNodePrefix}13`,
    cosmos_node_tendermint_rpc_is_down: `${alertKeysCosmosNodePrefix}14`,
    cosmos_node_no_synced_cosmos_rest_source: `${alertKeysCosmosNodePrefix}15`,
    cosmos_node_no_synced_tendermint_rpc_source: `${alertKeysCosmosNodePrefix}16`,
    cosmos_node_cosmos_rest_data_not_obtained: `${alertKeysCosmosNodePrefix}17`,
    cosmos_node_tendermint_rpc_data_not_obtained: `${alertKeysCosmosNodePrefix}18`,
    cosmos_node_metric_not_found: `${alertKeysCosmosNodePrefix}19`,
});

export const getAlertKeysGitHubRepo = (): AlertKeysGitHubRepo => ({
    github_release: `${alertKeysGitHubPrefix}1`,
    github_cannot_access: `${alertKeysGitHubPrefix}2`,
    github_api_call_error: `${alertKeysGitHubPrefix}3`,
});

export const getAlertKeysDockerHubRepo = (): AlertKeysDockerHubRepo => ({
    dockerhub_new_tag: `${alertKeysDockerHubPrefix}1`,
    dockerhub_updated_tag: `${alertKeysDockerHubPrefix}2`,
    dockerhub_deleted_tag: `${alertKeysDockerHubPrefix}3`,
    dockerhub_cannot_access: `${alertKeysDockerHubPrefix}4`,
    dockerhub_tags_api_call_error: `${alertKeysDockerHubPrefix}5`,
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
