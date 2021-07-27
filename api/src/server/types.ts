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
  no_of_active_jobs: string,
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

export interface AlertKeysGitHubRepo {
    github_release: string,
    cannot_access_github: string,

    [key: string]: string
}

export interface AlertKeysChainlinkNode {
  head_tacker_current_head: string,
  head_tracker_heads_received_total: string,
  max_unconfirmed_blocks: string,
  process_start_time_seconds: string,
  tx_manager_gas_bump_exceeds_limit_total: string,
  unconfirmed_transactions: string,
  run_status_update_total: string,
  eth_balance_amount: string,
  eth_balance_amount_increase: string,
  invalid_url: string,
  metric_not_found: string,
  node_is_down: string,
  prometheus_is_down: string,

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
    | ConfigKeys
    | AlertKeysSystem
    | AlertKeysGitHubRepo
    | AlertKeysChainlinkNode
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

interface ParentSourceChainInput {
  systems: string[],
  repos: string[],
}

export interface ParentSourceInput {
  [key: string]: ParentSourceChainInput
}

export function isParentSourceInput(object: any): boolean {
  let isParentSourceInput: boolean = true;
  if (!object || object.constructor !== Object) {
      return false;
  }
  Object.keys(object).forEach(
      (key: string, _: number): void => {
          if (!(object[key] && object[key].constructor === Object)) {
              isParentSourceInput = false;
          } else if (!('systems' in object[key] && 'repos' in object[key])) {
              isParentSourceInput = false;
          } else if (!(Array.isArray(object[key].systems)
              && Array.isArray(object[key].repos))) {
              isParentSourceInput = false;
          } else if (!(allElementsInListHaveTypeString(object[key].systems)
              && allElementsInListHaveTypeString(object[key].repos))) {
              isParentSourceInput = false;
          }
      });
  return isParentSourceInput;
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