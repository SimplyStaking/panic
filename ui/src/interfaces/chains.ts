import { Severity } from "../utils/constants";

export interface BaseChain {
    readonly name: string;
    chains: Chain[];
    chainFilter: string;
    severityFilter: Severity[];
}

export interface Chain {
    readonly name: string;
    readonly id: string;
    repos: string[];
    systems: string[];
    criticalAlerts: number;
    warningAlerts: number;
    errorAlerts: number;
    alerts: Alert[];
    active: Boolean;
}

export interface Alert {
    readonly severity: Severity;
    readonly message: string;
    readonly timestamp: number;
}
