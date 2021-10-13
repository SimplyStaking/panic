import { Severity } from "./severity";

export interface FilterState {
    readonly chainName: string;
    activeSeverities: Severity[];
    lastClickedColumnIndex: number;
    ordering: 'ascending' | 'descending';
}
