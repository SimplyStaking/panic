import { Alert } from "../interfaces/alerts"

export interface BaseChain {
    readonly name: string;
    chains: Chain[];
}

export interface Chain {
    readonly name: string;
    readonly id: string;
    repos: string[];
    systems: string[];
    alerts: Alert[];
    active: boolean;
}
