export enum Timeout {
    MAX = 30000,
    MIN = 3000
}

export enum Status {
    SUCCESS = 200,
    NO_CONTENT = 204,
    ERROR = 400,
    NOT_FOUND = 404,
    TIMEOUT = 408,
    CONFLICT = 409,
    E_500 = 500,
    E_530 = 530,
    E_531 = 531,
    E_532 = 532,
    E_533 = 533,
    E_534 = 534,
    E_535 = 535,
    E_536 = 536,
    E_537 = 537,
    E_538 = 538,
    E_539 = 539,
    E_540 = 540,
    E_541 = 541,
}

export enum PingStatus {
    SUCCESS = "PING_SUCCESS",
    ERROR = "PING_ERROR",
    TIMEOUT = "PING_TIMEOUT",
}

export enum Severities {
    INFO = "INFO",
    WARNING = "WARNING",
    CRITICAL = "CRITICAL",
    ERROR = "ERROR",
}

export const baseChains = ['cosmos', 'substrate', 'chainlink', 'general'];

export const testAlertMessage = 'Test alert from PANIC';
