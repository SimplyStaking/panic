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

export interface ConfigKeys {
    config: string,

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

export interface AlertKeysRepo {
    github_release: string,
    cannot_access_github: string,

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
    | ComponentKeys
    | ChainKeys
    | ConfigKeys
    | AlertKeysSystem
    | AlertKeysRepo
    | BaseChainKeys;

interface MonitorablesInfoResultData {
    Cosmos?: Object,
    Substrate?: Object,
    General?: Object,

    [key: string]: Object | undefined
}

export interface MonitorablesInfoResult {
    result: MonitorablesInfoResultData

    [key: string]: Object
}

interface AlertsOverviewChainInput {
    systems: string[],
    repos: string[],
}

export interface AlertsOverviewInput {
    [key: string]: AlertsOverviewChainInput
}

export function isAlertsOverviewInput(object: any): boolean {
    let isAlertsOverviewInput: boolean = true;
    if (!object || object.constructor !== Object) {
        return false;
    }
    Object.keys(object).forEach(
        (key: string, _: number): void => {
            if (!(object[key] && object[key].constructor === Object)) {
                isAlertsOverviewInput = false;
            } else if (!('systems' in object[key] && 'repos' in object[key])) {
                isAlertsOverviewInput = false;
            } else if (!(Array.isArray(object[key].systems)
                && Array.isArray(object[key].repos))) {
                isAlertsOverviewInput = false;
            } else if (!(allElementsInListHaveTypeString(object[key].systems)
                && allElementsInListHaveTypeString(object[key].repos))) {
                isAlertsOverviewInput = false;
            }
        });
    return isAlertsOverviewInput;
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
            [key: string]: string
        }
    }
}

export interface AlertsOverviewResult {
    result: AlertsOverviewResultData

    [key: string]: AlertsOverviewResultData
}
