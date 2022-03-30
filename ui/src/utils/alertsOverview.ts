import {Alert} from "../interfaces/alerts";
import {SubChain} from "../interfaces/chains";
import {API_URL, RepoType, Severity} from "./constants";
import {UnknownAlertSeverityError} from "./errors";
import {ChainsAPI} from "./chains";
import {HelperAPI} from "./helpers";

export const AlertsOverviewAPI = {
    updateAlerts: updateAlerts
}

/**
 * Gets and parses the alerts of given chains. Wrapper around
 * {@link getAlertsOverview} and {@link parseAlertsOverview} functions.
 * @param chains array of chains to be checked.
 * @returns updated array of chains.
 */
async function updateAlerts(chains: SubChain[]): Promise<SubChain[]> {
    const data: any = await getAlertsOverview(chains);

    for (const chain of chains) {
        if (data.result[chain.id]) {
            chain.alerts = parseAlertsOverview(data.result[chain.id].problems);
        }
    }

    return chains;
}

/**
 * Gets the alerts overview of given chains.
 * @param chains array of chains to be checked.
 * @returns chains data as a JSON object.
 */
async function getAlertsOverview(chains: SubChain[]): Promise<any> {
    let chainSources = {parentIds: {}};
    for (const chain of chains) {
        chainSources.parentIds[chain.id] = {
            include_chain_sourced_alerts: chain.isSource,
            systems: chain.systems.map((source) => {return source.id}),
            nodes: chain.nodes.map((source) => {return source.id}),
            github_repos: ChainsAPI.getRepoIDsOfRepoType(chain.repos, RepoType.GITHUB),
            dockerhub_repos: ChainsAPI.getRepoIDsOfRepoType(chain.repos, RepoType.DOCKERHUB)
        };
    }

    try {
        const alertsOverview = await fetch(`${API_URL}redis/alertsOverview`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chainSources)
            });

        if (!alertsOverview.ok) {
            const result = await alertsOverview.json();
            HelperAPI.logFetchError(result, 'Alerts Overview');
            return {result: {}};
        }

        return await alertsOverview.json();
    } catch (error: any) {
        console.log(`Error getting Alerts Overview - ${error}`);
        return {result: {}};
    }
}

/**
 * Parses the problems JSON object from alerts overview API call to an array
 * of alerts.
 * @param problems JSON object.
 * @returns array of alerts.
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
