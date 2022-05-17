import {SubChain} from "../interfaces/chains";
import {MetricAlert, Metrics, SystemMetrics} from "../interfaces/metrics";
import {API_URL, SystemMetricKeys, Severity} from "./constants";
import {UnknownAlertSeverityError} from "./errors";
import {HelperAPI} from "./helpers";

export const MetricsAPI = {
    getMetrics: getMetrics
}

/**
 * Gets an array of metrics from the API and formats it with system metrics and
 * metric alerts.
 * @param chains array of chains to be checked.
 * @returns populated metrics which includes system metrics and metric alerts.
 */
async function getMetrics(chains: SubChain[]): Promise<Metrics[]> {
    const systemMetrics: Metrics[] = [];
    const metrics: SystemMetrics[] = await getSystemsMetrics(chains);
    const alertMetrics: MetricAlert[] = await getMetricsAlerts(chains);

    for (const chain of chains) {
        for (const system of chain.systems) {
            const currentMetric: SystemMetrics = metrics.find(metric => metric.origin === system.id);
            const currentAlertMetrics: MetricAlert[] = alertMetrics.filter((metricAlert) => {
                return metricAlert.origin === system.id
            });
            systemMetrics.push({
                id: system.id,
                name: system.name,
                metrics: currentMetric,
                metricAlerts: currentAlertMetrics
            });
        }
    }

    return systemMetrics;
}

/**
 * Returns an array of system metrics for given chains.
 * @param chains array of chains to be checked.
 * @returns array of system metrics.
 */
async function getSystemsMetrics(chains: SubChain[]): Promise<SystemMetrics[]> {
    const data: any = await getSystemMetrics(chains);

    return parseSystemMetrics(data.result);
}

/**
 * Gets the system metrics for given chains.
 * @param chains chains to be checked.
 * @returns system metrics data as a JSON object.
 */
async function getSystemMetrics(chains: SubChain[]): Promise<any> {
    let chainSources = {parentIds: {}};
    for (const chain of chains) {
        chainSources.parentIds[chain.id] = {
            systems: chain.systems.map((source) => {return source.id}),
            repos: []
        };
    }

    try {
        const metrics = await fetch(`${API_URL}redis/metrics`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chainSources)
            });

        if (!metrics.ok) {
            const result = await metrics.json();
            HelperAPI.logFetchError(result, 'Metrics');
            return {result: {}};
        }

        return await metrics.json();
    } catch (error: any) {
        console.log(`Error getting Metrics - ${error}`);
        return {result: {}};
    }
}

/**
 * Parses the result JSON object from metrics API call to an array of system
 * metrics.
 * @param result JSON object.
 * @returns array of systems metrics.
 */
function parseSystemMetrics(result: any): SystemMetrics[] {
    const systemMetrics: SystemMetrics[] = []

    for (const chainID in result) {
        const system = result[chainID]['system'];
        for (const source in system) {
            systemMetrics.push({
                origin: source,
                CPU: parseFloat(system[source][SystemMetricKeys.SYSTEM_CPU_USAGE]),
                RAM: parseFloat(system[source][SystemMetricKeys.SYSTEM_RAM_USAGE]),
                Storage: parseFloat(system[source][SystemMetricKeys.SYSTEM_STORAGE_USAGE]),
                ProcessMemory: parseFloat(system[source][SystemMetricKeys.PROCESS_MEMORY_USAGE]),
                ProcessVirtualMemory: HelperAPI.formatBytes(system[source][SystemMetricKeys.VIRTUAL_MEMORY_USAGE],),
                OpenFileDescriptors: parseFloat(parseFloat(system[source][SystemMetricKeys.OPEN_FILE_DESCRIPTORS]).toFixed(2)),
            });
        }
    }

    return systemMetrics;
}

/**
 * Returns the metric alerts of given chains.
 * @param chains an array of chains to be checked.
 * @returns array of metric alerts.
 */
async function getMetricsAlerts(chains: SubChain[]): Promise<MetricAlert[]> {
    let metricAlerts: MetricAlert[] = []
    const data: any = await getMetricAlerts(chains);

    for (const chain of chains) {
        if (data.result[chain.id]) {
            metricAlerts = metricAlerts.concat(parseMetricAlerts(data.result[chain.id].problems));
        }
    }

    return metricAlerts;
}

/**
 * Gets the metric alerts of given chains.
 * @param chains chains to be checked.
 * @returns metric alerts data as a JSON object.
 */
async function getMetricAlerts(chains: SubChain[]): Promise<any> {
    let chainSources = {parentIds: {}};
    for (const chain of chains) {
        chainSources.parentIds[chain.id] = {
            include_chain_sourced_alerts: false,
            systems: chain.systems.map((source) => {return source.id}),
            nodes: [],
            github_repos: [],
            dockerhub_repos: []
        };
    }

    try {
        const metricAlerts = await fetch(`${API_URL}redis/alertsOverview`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chainSources)
            });

        if (!metricAlerts.ok) {
            const result = await metricAlerts.json();
            HelperAPI.logFetchError(result, 'Alerts Overview');
            return {result: {}};
        }

        return await metricAlerts.json();
    } catch (error: any) {
        console.log(`Error getting Alerts Overview - ${error}`);
        return {result: {}};
    }
}

/**
 * Parses the problems JSON object from alerts overview API call to an array of
 * metric alerts.
 * @param problems JSON object.
 * @returns array of metric alerts.
 */
function parseMetricAlerts(problems: any): MetricAlert[] {
    const metricAlerts: MetricAlert[] = []

    for (const source in problems) {
        for (const alert of problems[source]) {
            if (alert.severity in Severity) {
                if (alert.metric.toUpperCase() in SystemMetricKeys) {
                    metricAlerts.push({
                        origin: source,
                        severity: alert.severity as Severity,
                        metric: alert.metric.toUpperCase() as SystemMetricKeys
                    });
                }
            } else {
                throw new UnknownAlertSeverityError(alert.severity);
            }
        }
    }

    return metricAlerts;
}
