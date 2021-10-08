// @ts-nocheck
import { Severity } from "../interfaces/alerts";

/**
 * {@link UnknownAlertSeverityError} class represents the error which is thrown
 * when an alert severity value which is not in {@link Severity} is encountered.
 */
export class UnknownAlertSeverityError extends Error {
    name = "UnknownAlertSeverityError";

    constructor(severity: Severity) {
        super(`An unknown alert severity (${severity}) was encountered.`);
    }
}