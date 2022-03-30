import {Severity} from "../utils/constants";

/**
 * Represents an alert within PANIC.
 */
export interface Alert {
    /**
     * Severity of alert.
     */
    readonly severity: Severity;
    /**
     * Message of alert as a string.
     */
    readonly message: string;
    /**
     * Unix timestamp of alert as a number.
     */
    readonly timestamp: number;
    /**
     * Origin of alert as a string.
     */
    readonly origin: string;
}

/**
 * Represents the number of alerts of a given chain.
 */
export interface AlertsCount {
    /**
     * Number of critical alerts.
     */
    critical: number;
    /**
     * Number of warning alerts.
     */
    warning: number;
    /**
     * Number of error alerts.
     */
    error: number;
    /**
     * Number of info alerts.
     */
    info: number;
}
