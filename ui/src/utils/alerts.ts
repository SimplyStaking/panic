import { Alert } from "../interfaces/alerts";
import { Chain } from "../interfaces/chains";
import { Severity } from "../interfaces/severity";
import { apiURL, maxNumberOfAlerts } from "./constants";
import { UnknownAlertSeverityError } from "./errors";

export const AlertsAPI = {
    parseRedisAlerts: parseRedisAlerts,
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
