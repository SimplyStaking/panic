import { Alert, Severity } from "../interfaces/alerts";
import { SelectOptionType } from "../lib/types/types/select";
import { criticalIcon, errorIcon, infoIcon, warningIcon } from "./constants";

/**
 * Parses the problems JSON object from Redis to a list of alerts.
 * @param problems JSON object.
 * @returns list of alerts.
 */
export function parseRedisAlerts(problems: any): Alert[] {
    const alerts: Alert[] = []

    for (const source in problems) {
        for (const alert of problems[source]) {
            if (alert.severity in Severity) {
                alerts.push({ severity: alert.severity as Severity, message: alert.message, timestamp: alert.timestamp });
            } else {
                console.log('Info - Found severity value which is not in Severity enum.');
            }
        }
    }

    return alerts;
}

/**
 * Returns all severity keys in a list.
 * @returns list of all severity keys.
 */
export function getAllSeverityValues(): Severity[] {
    return Object.keys(Severity).map(severity => severity as Severity);
}

/**
 * Formats Severity enum to SelectOptionType type.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns populated list of required object type.
 */
export const getSeverityFilterOptions = (skipInfoSeverity: boolean = false): SelectOptionType => {
    return skipInfoSeverity ?
        Object.keys(Severity).reduce(function (filtered, severity) {
            if (severity !== 'INFO') {
                filtered.push({ label: Severity[severity], value: severity });
            }
            return filtered;
        }, []) :
        Object.keys(Severity).map(severity => ({ label: Severity[severity], value: severity }));
}

/**
 * Returns icon markup as object according to the severity passed.
 * @param severity the alert severity.
 * @returns icon markup as object which corresponds to the severity.
 */
export const getSeverityIcon = (severity: Severity): Object => {
    switch (Severity[severity]) {
        case Severity.CRITICAL: {
            return criticalIcon;
        }
        case Severity.WARNING: {
            return warningIcon;
        }
        case Severity.ERROR: {
            return errorIcon;
        }
        case Severity.INFO: {
            return infoIcon;
        }
        default: {
            return {};
        }
    }
}
