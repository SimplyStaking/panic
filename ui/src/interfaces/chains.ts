export interface BaseChain {
    readonly name: string;
    chains: Chain[];
}

export interface Chain {
    readonly name: string;
    readonly id: string;
    repos: string[];
    systems: string[];
    criticalAlerts: number;
    warningAlerts: number;
    errorAlerts: number;
    totalAlerts: number;
    active: Boolean;
}