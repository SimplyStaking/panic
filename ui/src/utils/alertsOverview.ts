import { Alert } from "../interfaces/alerts";
import { Chain } from "../interfaces/chains";
import { Severity } from "../interfaces/severity";
import { apiURL } from "./constants";
import { UnknownAlertSeverityError } from "./errors";

export const AlertsOverviewAPI = {
    updateAlerts: updateAlerts
}

/**
 * Updates the alerts of a given chain.
 * @param chain chain to be checked.
 * @returns updated chain.
 */
async function updateAlerts(chain: Chain): Promise<Chain> {
    const data: any = await getAlertsOverview(chain);

    if (data.result[chain.id]) {
        chain.alerts = parseAlertsOverview(data.result[chain.id].problems);
    }

    return chain;
}

/**
 * Gets the alerts overview of a given chain.
 * @param chain chain to be checked.
 * @returns chain data as a JSON object.
 */
async function getAlertsOverview(chain: Chain): Promise<any> {
    let chainSources = { parentIds: {} };
    chainSources.parentIds[chain.id] = { systems: [], repos: [] };
    chainSources.parentIds[chain.id].systems = chain.systems;
    chainSources.parentIds[chain.id].repos = chain.repos;

    try {
        const alertsOverview = await fetch(`${apiURL}redis/alertsOverview`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chainSources)
            });

        return await alertsOverview.json();
    } catch (error: any) {
        console.log(`Error getting Alerts Overview for chain ID: ${chain.id} -`, error);
        return { result: {} };
    }
}

/**
 * Parses the problems JSON object from alerts overview API call to a list of alerts.
 * @param problems JSON object.
 * @returns list of alerts.
 */
function parseAlertsOverview(problems: any): Alert[] {
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
