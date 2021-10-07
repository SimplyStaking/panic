export interface Alert {
    readonly severity: Severity;
    readonly message: string;
    readonly timestamp: number;
}

export enum Severity {
    CRITICAL = 'Critical',
    WARNING = 'Warning',
    ERROR = 'Error',
    INFO = 'Info'
}