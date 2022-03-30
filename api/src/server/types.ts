import {allElementsInListHaveTypeString} from "./utils";

export interface HttpsOptions {
    key: Buffer,
    cert: Buffer,

    [key: string]: Buffer
}

export interface RedisHashes {
    parent: string,

    [key: string]: string
}

export interface UniqueKeys {
    mute: string,

    [key: string]: string
}

export interface SystemKeys {
    process_cpu_seconds_total: string,
    process_memory_usage: string,
    virtual_memory_usage: string,
    open_file_descriptors: string,
    system_cpu_usage: string,
    system_ram_usage: string,
    system_storage_usage: string,
    network_transmit_bytes_per_second: string,
    network_receive_bytes_per_second: string,
    network_receive_bytes_total: string,
    network_transmit_bytes_total: string,
    disk_io_time_seconds_total: string,
    disk_io_time_seconds_in_interval: string,
    last_monitored: string,
    system_went_down_at: string,

    [key: string]: string
}

export interface ChainlinkNodeKeys {
    current_height: string,
    total_block_headers_received: string,
    max_pending_tx_delay: string,
    process_start_time_seconds: string,
    total_gas_bumps: string,
    total_gas_bumps_exceeds_limit: string,
    no_of_unconfirmed_txs: string,
    total_errored_job_runs: string,
    current_gas_price_info: string,
    eth_balance_info: string,
    went_down_at_prometheus: string,
    last_prometheus_source_used: string,
    last_monitored_prometheus: string,

    [key: string]: string
}

export interface GitHubKeys {
    no_of_releases: string,
    last_monitored: string,

    [key: string]: string
}

export interface ComponentKeys {
    heartbeat: string,

    [key: string]: string
}

export interface ChainKeys {
    mute_alerts: string,

    [key: string]: string
}

export interface AlertKeysSystem {
    open_file_descriptors: string,
    system_cpu_usage: string,
    system_storage_usage: string,
    system_ram_usage: string,
    system_is_down: string,
    metric_not_found: string,
    invalid_url: string,

    [key: string]: string
}

export interface AlertKeysNode {
    // Chainlink Nodes
    cl_head_tracker_current_head: string,
    cl_head_tracker_heads_received_total: string,
    cl_max_unconfirmed_blocks: string,
    cl_process_start_time_seconds: string,
    cl_tx_manager_gas_bump_exceeds_limit_total: string,
    cl_unconfirmed_transactions: string,
    cl_run_status_update_total: string,
    cl_eth_balance_amount: string,
    cl_eth_balance_amount_increase: string,
    cl_invalid_url: string,
    cl_metric_not_found: string,
    cl_node_is_down: string,
    cl_prometheus_is_down: string,
    // EVM Nodes
    evm_node_is_down: string,
    evm_block_syncing_block_height_difference: string,
    evm_block_syncing_no_change_in_block_height: string,
    evm_invalid_url: string,

    [key: string]: string
}

export interface AlertKeysGitHubRepo {
    github_release: string,
    github_cannot_access: string,
    github_api_call_error: string,

    [key: string]: string
}

export interface AlertKeysDockerHubRepo {
    dockerhub_new_tag: string,
    dockerhub_updated_tag: string,
    dockerhub_deleted_tag: string,
    dockerhub_cannot_access: string,
    dockerhub_tags_api_call_error: string,

    [key: string]: string
}

export interface BaseChainKeys {
    monitorables_info: string,

    [key: string]: string
}

export type RedisKeys =
    RedisHashes
    | UniqueKeys
    | SystemKeys
    | GitHubKeys
    | ChainlinkNodeKeys
    | ComponentKeys
    | ChainKeys
    | AlertKeysSystem
    | AlertKeysNode
    | AlertKeysGitHubRepo
    | AlertKeysDockerHubRepo
    | BaseChainKeys;

interface MonitorablesInfoResultData {
    cosmos?: Object,
    substrate?: Object,
    general?: Object,
    chainlink?: Object,

    [key: string]: Object | undefined
}

export interface MonitorablesInfoResult {
    result: MonitorablesInfoResultData

    [key: string]: Object
}

interface AlertsOverviewChainInput {
    include_chain_sourced_alerts: boolean,
    systems: string[],
    nodes: string[],
    github_repos: string[],
    dockerhub_repos: string[],
}

export interface AlertsOverviewInput {
    [key: string]: AlertsOverviewChainInput
}

interface AlertsOverviewResultData {
    [key: string]: {
        info: number,
        warning: number,
        critical: number,
        error: number
        problems: {
            [key: string]: {
                msg: string
                severity: string
            }[]
        }
        releases: {
            [key: string]: {}
        },
        tags: {
            [key: string]: {
                new: {},
                updated: {},
                deleted: {}
            }
        }
    }
}

export interface AlertsOverviewResult {
    result: AlertsOverviewResultData

    [key: string]: AlertsOverviewResultData
}

export interface AlertsOverviewAlertData {
    parentId: string,
    monitorableId: string,
    key: string,
    value: any
}

interface RedisMetricsChainsInput {
    systems: string[],
    repos: string[],
}

export interface RedisMetricsInput {
    [key: string]: RedisMetricsChainsInput
}

export function isAlertsOverviewInputValid(object: any): boolean {
    let isAlertsOverviewInputValid: boolean = true;
    if (!object || object.constructor !== Object) {
        return false;
    }
    Object.keys(object).forEach(
        (key: string, _: number): void => {
            if (!(object[key] && object[key].constructor === Object)) {
                isAlertsOverviewInputValid = false;
            } else if (!('include_chain_sourced_alerts' in object[key] &&
                'systems' in object[key] && 'nodes' in object[key] &&
                'github_repos' in object[key] &&
                'dockerhub_repos' in object[key])) {
                isAlertsOverviewInputValid = false;
            } else if (!(
                typeof object[key].include_chain_sourced_alerts == 'boolean' &&
                Array.isArray(object[key].systems) &&
                Array.isArray(object[key].nodes) &&
                Array.isArray(object[key].github_repos) &&
                Array.isArray(object[key].dockerhub_repos))) {
                isAlertsOverviewInputValid = false;
            } else if (!(allElementsInListHaveTypeString(object[key].systems)
                && allElementsInListHaveTypeString(object[key].nodes) &&
                allElementsInListHaveTypeString(object[key].github_repos) &&
                allElementsInListHaveTypeString(object[key].dockerhub_repos))) {
                isAlertsOverviewInputValid = false;
            }
        });
    return isAlertsOverviewInputValid;
}

export function isRedisMetricsInputValid(object: any): boolean {
    let isParentSourceInputValid: boolean = true;
    if (!object || object.constructor !== Object) {
        return false;
    }
    Object.keys(object).forEach(
        (key: string, _: number): void => {
            if (!(object[key] && object[key].constructor === Object)) {
                isParentSourceInputValid = false;
            } else if (!('systems' in object[key] && 'repos' in object[key])) {
                isParentSourceInputValid = false;
            } else if (!(Array.isArray(object[key].systems)
                && Array.isArray(object[key].repos))) {
                isParentSourceInputValid = false;
            } else if (!(allElementsInListHaveTypeString(object[key].systems)
                && allElementsInListHaveTypeString(object[key].repos))) {
                isParentSourceInputValid = false;
            }
        });
    return isParentSourceInputValid;
}

interface MetricsResultData {
    [key: string]: {
        system: {
            [key: string]: SystemKeys
        }
        github: {
            [key: string]: GitHubKeys
        },
    }
}

export interface MetricsResult {
    result: MetricsResultData,

    [key: string]: MetricsResultData
}
