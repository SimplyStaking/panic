import { Alert, Severity } from "../interfaces/alerts";
import { BaseChain } from "../interfaces/chains";
import { SelectOptionObjType, SelectOptionType } from "../lib/types/types/select";
import { apiURL, criticalIcon, errorIcon, infoIcon, maxNumberOfAlerts, warningIcon } from "./constants";
import { UnknownAlertSeverityError } from "./errors";

export const AlertsAPI = {
    parseRedisAlerts: parseRedisAlerts,
    getAllSeverityValues: getAllSeverityValues,
    getSeverityFilterOptions: getSeverityFilterOptions,
    getSeverityIcon: getSeverityIcon,
    getAlertsFromMongoDB: getAlertsFromMongoDB
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
 * @returns list of all severity keys.
 */
function getAllSeverityValues(): Severity[] {
    return Object.keys(Severity).map(severity => severity as Severity);
}

/**
 * Formats Severity enum to SelectOptionType type.
 * @param skipInfoSeverity whether to skip info severity (false by default).
 * @returns populated SelectOptionType object.
 */
function getSeverityFilterOptions(skipInfoSeverity: boolean = false): SelectOptionType {
    let filtered = Object.keys(Severity).filter((severity) => {
        return severity !== 'INFO' || (!skipInfoSeverity)
    });

    return filtered.map(severity => parseSeverity(Severity[severity], severity))
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
 * ALERTS OVERVIEW - MongoDB.
 */

/**
 * Gets the alerts of global base chain from MongoDB.
 * @param globalBaseChain base chain to be checked.
 * @returns alerts extracted from API.
 */
async function getAlertsFromMongoDB(globalBaseChain: BaseChain, minTimestamp: number, maxTimestamp: number): Promise<Alert[]> {
    const data: any = await getAlerts(globalBaseChain, minTimestamp, maxTimestamp);
    let alerts: Alert[] = [];

    if (data.result['alerts']) {
        alerts = parseMongoAlerts(data.result['alerts']);
    }

    return alerts;
}

/**
 * Gets the alerts of global base chain.
 * @param globalBaseChain global base chain to be checked.
 * @returns alerts data as a JSON object.
 */
async function getAlerts(globalBaseChain: BaseChain, minTimestamp: number, maxTimestamp: number): Promise<any> {
    let mongoAlertsInput = {
        chains: [],
        severities: globalBaseChain.activeSeverities,
        sources: [],
        minTimestamp: minTimestamp,
        maxTimestamp: maxTimestamp,
        noOfAlerts: maxNumberOfAlerts
    };

    for (const chain of globalBaseChain.chains) {
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
        console.log('Error getting Chain Alerts from MongoDB -', error);
        return { result: {} };
    }
}

/**
 * Parses the alerts JSON object from MongoDB to a list of alerts.
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
