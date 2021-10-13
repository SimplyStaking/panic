import { Severity } from "./severity";

export interface Alert {
    readonly severity: Severity;
    readonly message: string;
    readonly timestamp: number;
    readonly origin: string;
}
