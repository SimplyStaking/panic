import { Alert } from "../interfaces/alerts"
import { Severity } from "./severity";

export interface BaseChain {
    readonly name: string;
    chains: Chain[];
    activeSeverities: Severity[];
    lastClickedColumnIndex: number;
    ordering: string;
}

export interface Chain {
    readonly name: string;
    readonly id: string;
    repos: string[];
    systems: string[];
    alerts: Alert[];
    active: boolean;
}
