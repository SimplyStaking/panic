import {Alert, AlertsCount} from "../interfaces/alerts";
import {SubChain} from "../interfaces/chains";
import {FilterStateV2} from "../interfaces/filterState";
import {ChainsAPI} from "./chains";
import {API_URL, MAX_ALERTS, Severity} from "./constants";
import {UnknownAlertSeverityError} from "./errors";
import {HelperAPI} from "./helpers";
import {SeverityAPI} from "./severity";

export const AlertsAPI = {
    getAlerts: getAlerts,
    getAlertsCount: getAlertsCount
}

/**
 * Gets and parses the alerts of chains. Wrapper around
 * {@link getChainAlerts} and {@link parseAlerts} functions.
 * @param chains array of chains to be checked.
 * @param filterState only alerts which fall under these filters are required.
 * @returns alerts extracted from API.
 */
async function getAlerts(chains: SubChain[], filterState: FilterStateV2): Promise<Alert[]> {
    const data: any = await getChainAlerts(chains, filterState);
    let alerts: Alert[] = [];

    if (data.result['alerts']) {
        alerts = parseAlerts(data.result['alerts']);
    }

    return alerts;
}

/**
 * Gets the alerts of chains given a filter state.
 * @param chains array of chains to be checked.
 * @param filterState only chains and alerts which fall under these filters are
 * required.
 * @returns alerts data as a JSON object.
 */
async function getChainAlerts(chains: SubChain[], filterState: FilterStateV2): Promise<any> {
    let alertsBody = {
        chains: [],
        severities: filterState.selectedSeverities.length > 0 ? filterState.selectedSeverities : SeverityAPI.getAllSeverityValues(),
        sources: filterState.selectedSources.length > 0 ? filterState.selectedSources : ChainsAPI.activeChainsSourcesIDs(chains, filterState.selectedSubChains),
        minTimestamp: filterState.fromDateTime !== '' ? HelperAPI.dateTimeStringToTimestamp(filterState.fromDateTime) : 0,
        maxTimestamp: filterState.toDateTime !== '' ? HelperAPI.dateTimeStringToTimestamp(filterState.toDateTime) : HelperAPI.getCurrentTimestamp(),
        noOfAlerts: MAX_ALERTS
    };

    const noFilter: boolean = filterState.selectedSubChains.length === 0;

    for (const chain of chains) {
        if (noFilter || filterState.selectedSubChains.includes(chain.name)) {
            alertsBody.chains.push(chain.id);
        }
    }

    try {
        const alerts = await fetch(`${API_URL}server/mongo/alerts`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(alertsBody)
            });

        if (!alerts.ok) {
            const result = await alerts.json();
            HelperAPI.logFetchError(result, 'Chain Alerts from Mongo');
            return {result: {}};
        }

        return alerts.json();
    } catch (error: any) {
        console.log(`Error getting Chain Alerts from Mongo - ${error}`);
        return {result: {}};
    }
}

/**
 * Parses the alerts JSON object from alerts API call to an array of alerts.
 * @param alertsArray array of JSON objects.
 * @returns array of alerts.
 */
function parseAlerts(alertsArray: any[]): Alert[] {
    const alerts: Alert[] = []

    for (const alert of alertsArray) {
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

/**
 * Gets the number of alerts within chains.
 * @param chains array of chains to be checked.
 * @returns {@link AlertsCount} object with updated alert counts.
 */
function getAlertsCount(chains: SubChain[]): AlertsCount {
    const alertsCount: AlertsCount = {
        critical: 0,
        warning: 0,
        error: 0,
        info: 0
    };

    for (const chain of chains) {
        for (const alert of chain.alerts) {
            switch (Severity[alert.severity]) {
                case Severity.CRITICAL: {
                    alertsCount.critical++;
                    break;
                }
                case Severity.WARNING: {
                    alertsCount.warning++;
                    break;
                }
                case Severity.ERROR: {
                    alertsCount.error++;
                    break;
                }
                case Severity.INFO: {
                    alertsCount.info++;
                    break;
                }
            }
        }
    }

    return alertsCount;
}
