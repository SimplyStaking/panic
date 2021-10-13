import { Alert, Severity } from "../interfaces/alerts";
import { Chain } from "../interfaces/chains";
import { SelectOptionObjType, SelectOptionType } from "../lib/types/types/select";
import { apiURL, criticalIcon, errorIcon, infoIcon, maxNumberOfAlerts, warningIcon } from "./constants";
import { UnknownAlertSeverityError } from "./errors";

export const AlertsAPI = {
    parseRedisAlerts: parseRedisAlerts,
    getAllSeverityValues: getAllSeverityValues,
    getSeverityFilterOptions: getSeverityFilterOptions,
    getSeverityFilterValue: getSeverityFilterValue,
    getSeverityIcon: getSeverityIcon,
    getAlertsFromMongo: getAlertsFromMongo
}

/**
 * Parses the problems JSON object from Redis to a list of alerts.
 * @param problems JSON object.
 * @returns list of alerts.
 */
function parseRedisAlerts(problems: any): Alert[] {
    const alerts: Alert[] = []

    for (const source in problems) {
        for (const alert of problems[source]) {
            if (alert.severity in Severity) {
                alerts.push({
                    severity: alert.severity as Severity,
                    message: alert.message,
                    timestamp: alert.timestamp,
                    origin: null
                });
            } else {
                throw new UnknownAlertSeverityError(alert.severity);
            }
        }
    }

    return alerts;
}

/**
 * Returns all severity keys in a list.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns list of all severity keys.
 */
function getAllSeverityValues(skipInfoSeverity: boolean = false): Severity[] {
    let filtered: string[] = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    return filtered.map(severity => severity as Severity);
}

/**
 * Formats Severity enum to SelectOptionType type.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns populated SelectOptionType object.
 */
function getSeverityFilterOptions(skipInfoSeverity: boolean = false): SelectOptionType {
    let filtered: string[] = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    return filtered.map(severity => parseSeverity(Severity[severity], severity))
}

/**
 * Returns the value for the severity filter. If not all severities are chosen, it
 * returns the name of the chosen severities while if all severities are chosen, it
 * returns an empty list. This is the case since no severity should be
 * selected if all severities are active.
 * @returns list of name of all selected severities.
 */
function getSeverityFilterValue(severities: Severity[], skipInfoSeverity: boolean = false): string[] {
    let filtered: string[] = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    // If all severities are chosen, set filter to empty.
    if (filtered.length === severities.length) {
        return [];
    }

    // Else return name of chosen severities.
    return severities;
}

/**
 * Parses label and value strings into SelectOptionObjType.
 * @param label label to be parsed.
 * @param value value to be parsed.
 * @returns populated SelectOptionObjType object.
 */
function parseSeverity(label: string, value: string): SelectOptionObjType {
    return { label: label, value: value }
}

/**
 * Returns icon markup as object according to the severity passed.
 * @param severity the alert severity.
 * @returns icon markup as object which corresponds to the severity.
 */
function getSeverityIcon(severity: Severity): Object {
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

/**
 * ALERTS OVERVIEW - Mongo.
 */

/**
 * Gets the alerts of chains from Mongo.
 * @param chains chains to be checked.
 * @param activeSeverities only alerts with these severities are required.
 * @param minTimestamp only alerts which occurred after this timestamp are required.
 * @param maxTimestamp only alerts which occurred before this timestamp are required.
 * @returns alerts extracted from API.
 */
async function getAlertsFromMongo(chains: Chain[], activeSeverities: Severity[], minTimestamp: number, maxTimestamp: number): Promise<Alert[]> {
    const data: any = await getAlerts(chains, activeSeverities, minTimestamp, maxTimestamp);
    let alerts: Alert[] = [];

    if (data.result['alerts']) {
        alerts = parseMongoAlerts(data.result['alerts']);
    }

    return alerts;
}

/**
 * Gets the alerts of chains.
 * @param chains chains to be checked.
 * @param activeSeverities only alerts with these severities are required.
 * @param minTimestamp only alerts which occurred after this timestamp are required.
 * @param maxTimestamp only alerts which occurred before this timestamp are required.
 * @returns alerts data as a JSON object.
 */
async function getAlerts(chains: Chain[], activeSeverities: Severity[], minTimestamp: number, maxTimestamp: number): Promise<any> {
    let mongoAlertsInput = {
        chains: [],
        severities: activeSeverities,
        sources: [],
        minTimestamp: minTimestamp,
        maxTimestamp: maxTimestamp,
        noOfAlerts: maxNumberOfAlerts
    };

    for (const chain of chains) {
        if (chain.active) {
            mongoAlertsInput.chains.push(chain.id);
            mongoAlertsInput.sources.push.apply(mongoAlertsInput.sources, chain.systems);
            mongoAlertsInput.sources.push.apply(mongoAlertsInput.sources, chain.repos);
        }
    }

    try {
        const alerts = await fetch(`${apiURL}mongo/alerts`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(mongoAlertsInput)
            });

        return await alerts.json();
    } catch (error: any) {
        console.log('Error getting Chain Alerts from Mongo -', error);
        return { result: {} };
    }
}

/**
 * Parses the alerts JSON object from Mongo to a list of alerts.
 * @param alertsList list of JSON objects.
 * @returns list of alerts.
 */
function parseMongoAlerts(alertsList: any): Alert[] {
    const alerts: Alert[] = []

    for (const alert of alertsList) {
        if (alert.severity in Severity) {
            alerts.push({
                severity: alert.severity as Severity,
                message: alert.message,
                timestamp: alert.timestamp,
                origin: alert.origin
            });
        } else {
            throw new UnknownAlertSeverityError(alert.severity);
        }
    }

    return alerts;
}
