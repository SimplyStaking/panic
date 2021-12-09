import { OrderingType } from "../lib/types/types/ordering";
import { Severity } from "./severity";

export interface FilterState {
    readonly chainName: string;
    selectedSeverities: Severity[];
    lastClickedColumnIndex: number;
    ordering: OrderingType;
}
