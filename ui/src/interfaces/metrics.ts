import {SystemMetricKeys, Severity} from "../utils/constants";

// Represents the metrics of a given chain.
export interface Metrics {
    readonly id: string;
    readonly name: string;
    metrics: SystemMetrics;
    metricAlerts: MetricAlert[];
}

// Represents a single metric alert.
export interface MetricAlert {
    readonly origin: string;
    readonly severity: Severity;
    readonly metric: SystemMetricKeys;
}

// Represents the system metrics alert of a given chain.
export interface SystemMetrics {
    readonly origin: string;
    CPU: number;
    RAM: number;
    Storage: number;
    ProcessMemory: number;
    ProcessVirtualMemory: string;
    OpenFileDescriptors: number;
}
