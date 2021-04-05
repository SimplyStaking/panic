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

export interface AlertKeys {
    open_file_descriptors: string,
    system_cpu_usage: string,
    system_storage_usage: string,
    system_ram_usage: string,
    system_is_down: string,
    metric_not_found: string,
    invalid_url: string,
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
    | AlertKeys
    | BaseChainKeys;

interface monitorablesInfoResultData {
    Cosmos?: Object,
    Substrate?: Object,
    General?: Object,

    [key: string]: Object | undefined
}

export interface monitorablesInfoResult {
    result: monitorablesInfoResultData

    [key: string]: Object
}
