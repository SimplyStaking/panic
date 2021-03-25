export interface HttpsOptions {
    key: Buffer,
    cert: Buffer,
}

export interface RedisHashes {
    parent: string,
}

export interface UniqueKeys {
    mute: string,
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
}

export interface GitHubKeys {
    no_of_releases: string,
    last_monitored: string,
}

export interface ComponentKeys {
    heartbeat: string,
}

export interface ChainKeys {
    mute_alerts: string,
}

export interface ConfigKeys {
    config: string,
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
}

export interface BaseChainKeys {
    monitorables_info: string,
}
