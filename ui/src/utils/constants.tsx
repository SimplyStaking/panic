import {Env} from '@stencil/core';
import {
  DataTableHeaderType
} from "@simply-vc/uikit/dist/types/types/datatable";

/**
 * The URL of the UI's home page.
 */
export const HOME_URL: string = '/';

/**
 * All base chains currently supported by the PANIC API as array of strings.
 */
export const BASE_CHAINS: string[] = ["cosmos", "general", "chainlink", "substrate"];

/**
 * PANIC API URL based on host name and API PORT environmental variable.
 */
export const API_URL: string = `https://${window.location.hostname}:${Env.API_PORT}/server/`;

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
