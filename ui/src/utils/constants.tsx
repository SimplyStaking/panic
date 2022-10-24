import {Env} from '@stencil/core';
import {
  DataTableHeaderType
} from "@simply-vc/uikit/dist/types/types/datatable";
import {ServiceNames, ServicesFullNameType, ServicesType} from "./types";

/**
 * The URL of the UI's home page.
 */
export const HOME_URL: string = '/';

/**
 * A string representing the key where the config id is stored in the local storage (browser).
 */
export const CONFIG_ID_LOCAL_STORAGE_KEY: string = "configId";

/**
 * All base chains currently supported by the PANIC API as an enum.
 */
export enum BaseChains {
  CHAINLINK = 'chainlink',
  COSMOS = 'cosmos',
  SUBSTRATE = 'substrate',
  GENERAL = 'general'
}

/**
 * All base chains currently supported by the PANIC API as array of strings.
 */
export const BASE_CHAINS: string[] = Object.values(BaseChains);

/**
 * All base chains in short-full name pairs
 */
export const BASE_CHAIN_FULL_NAMES = {
  cosmos: 'Cosmos',
  substrate: 'Substrate',
  chainlink: 'Chainlink',
  general: 'General'
};

/**
 * PANIC API URL based on host name and API PORT environmental variable.
 */
export const API_URL: string = `https://${window.location.hostname}:${Env.API_PORT}/`;

/**
 * Polling frequency (data refresh rate) in milliseconds.
 */
export const POLLING_FREQUENCY: number = 5000;

/**
 * Maximum number of alerts retrieved from alerts API call.
 */
export const MAX_ALERTS: number = 1000;

/**
 * Represents the different alert severity values.
 */
export enum Severity {
  CRITICAL = 'Critical',
  WARNING = 'Warning',
  ERROR = 'Error',
  INFO = 'Info'
}

/**
 * Represents the different repository types available within PANIC.
 */
export enum RepoType {
  GITHUB = 'GitHub',
  DOCKERHUB = 'DockerHub'
}

/**
 * Represents the keys for all the system metrics.
 */
export enum SystemMetricKeys {
  PROCESS_CPU_SECONDS_TOTAL = 's1',
  PROCESS_MEMORY_USAGE = 's2',
  VIRTUAL_MEMORY_USAGE = 's3',
  OPEN_FILE_DESCRIPTORS = 's4',
  SYSTEM_CPU_USAGE = 's5',
  SYSTEM_RAM_USAGE = 's6',
  SYSTEM_STORAGE_USAGE = 's7',
  NETWORK_TRANSMIT_BYTES_PER_SECOND = 's8',
  NETWORK_RECEIVE_BYTES_PER_SECOND = 's9',
  NETWORK_RECEIVE_BYTES_TOTAL = 's10',
  NETWORK_TRANSMIT_BYTES_TOTAL = 's11',
  DISK_IO_TIME_SECONDS_TOTAL = 's12',
  DISK_IO_TIME_SECONDS_IN_INTERVAL = 's13',
  LAST_MONITORED = 's14',
  WENT_DOWN_AT = 's15',
}

/**
 * The data table header for alerts. Every column is sortable.
 */
export const ALERTS_DATA_TABLE_HEADER: DataTableHeaderType[] = [
  {title: 'Severity', sortable: true},
  {title: 'Date Time', sortable: true},
  {title: 'Message', sortable: true}
];

/**
 * The data table header for system metrics. Every column is sortable.
 */
export const SYSTEM_METRICS_DATA_TABLE_HEADER: DataTableHeaderType[] = [
  {title: 'System', sortable: true},
  {title: 'CPU', sortable: true},
  {title: 'RAM', sortable: true},
  {title: 'Storage', sortable: true},
  {title: 'Process Memory', sortable: true},
  {title: 'Process Virtual Memory', sortable: true},
  {title: 'Open File Descriptors', sortable: true}
];

export const SUBCHAIN_TABLE_HEADERS = [
  {
    title: "Name",
    sortable: true
  },
  {
    title: "Base Chain",
    sortable: true
  }
];

export const CHANNEL_TABLE_HEADERS = [
  {
    title: "Channel Type",
    sortable: true
  },
  {
    title: "Name",
    sortable: true
  },
];

export const SUBCHAIN_CHANNEL_MAP_TABLE_HEADERS = [
  {
    title: "Sub-Chain",
    sortable: true
  },
  {
    title: "Enabled",
    sortable: true
  },
];

export const CHANNEL_FILTERS = [
  {
    label: "All",
    value: "all"
  },
  {
    label: "Telegram",
    value: "telegram"
  },
  {
    label: "Slack",
    value: "slack"
  },
  {
    label: "E-mail",
    value: "email"
  },
  {
    label: "Opsgenie",
    value: "opsgenie"
  },
  {
    label: "PagerDuty",
    value: "pagerduty"
  },
  {
    label: "Twilio",
    value: "twilio"
  },
];

/**
 * Installer related constants.
 */

/**
 * Endpoint to be used to get weiwatchers network/URL mappings.
 */
export const WEIWATCHERS_MAPPING_URL = 'https://raw.githubusercontent.com/SimplyVC/weiwatchers_mapping/main/mapping.json';

/**
 * Represents the different source types available within PANIC (excluding Repos).
 */
export enum SourceType {
  NODES = 'Nodes',
  EVM_NODES = 'EVMNodes',
  CONTRACT = 'Contract',
  SYSTEMS = 'Systems',
  NETWORK = 'Network'
}

/**
 * Test-buttons related constants.
 */

/**
 * Array defining a list of channels services.
 */
export const ChannelsServices: ServiceNames[] = [
  'opsgenie', 'telegram', 'slack', 'pagerduty', 'twilio', 'email'];

/**
 * Full names of services referenced by their shorthand.
 */
export const ServiceFullNames: ServicesFullNameType = {
  'node-exporter': 'Node Exporter',
  'prometheus': 'Prometheus Endpoint',
  'cosmos-rest': 'Cosmos REST',
  'tendermint-rpc': 'Tendermint RPC',
  'substrate-websocket': 'Substrate Websocket',
  'ethereum-rpc': 'Ethereum RPC',
  'opsgenie': 'Opsgenie',
  'telegram': 'Telegram',
  'slack': 'Slack',
  'pagerduty': 'PagerDuty',
  'twilio': 'Twilio',
  'email': 'Email',
  'github': 'GitHub',
  'dockerhub': 'Dockerhub'
}

/**
 * Services which are used to ping various endpoints.
 */
export const Services: ServicesType = {
  'node-exporter': {'endpoint_url': 'common/node-exporter/'},
  'prometheus': {'endpoint_url': 'common/prometheus/'},
  'cosmos-rest': {'endpoint_url': 'cosmos/rest/'},
  'tendermint-rpc': {'endpoint_url': 'cosmos/tendermint-rpc/'},
  'substrate-websocket': {'endpoint_url': 'substrate/websocket/'},
  'ethereum-rpc': {'endpoint_url': 'ethereum/rpc/'},
  'opsgenie': {'endpoint_url': 'channels/opsgenie/'},
  'telegram': {'endpoint_url': 'channels/telegram/'},
  'slack': {'endpoint_url': 'channels/slack/'},
  'pagerduty': {'endpoint_url': 'channels/pagerduty/'},
  'twilio': {'endpoint_url': 'channels/twilio/'},
  'email': {'endpoint_url': 'channels/email/'},
  'github': {'endpoint_url': 'repositories/github'},
  'dockerhub': {'endpoint_url': 'repositories/dockerhub'}
}

/**
 * Enum defining the 3 status ping types returned by the API calls.
 */
export const enum PingStatus {
  SUCCESS = "PING_SUCCESS",
  ERROR = "PING_ERROR",
  TIMEOUT = "PING_TIMEOUT",
}
