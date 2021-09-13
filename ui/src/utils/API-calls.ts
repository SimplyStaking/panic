import { BaseChain, Chain } from "../interfaces/chains";
import { apiURL, baseChainsNames } from "./constants";

export async function MonitorablesInfo(): Promise<BaseChain[]> {
    const monitorablesInfo: Response = await fetch(apiURL + 'redis/monitorablesInfo',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "baseChains": baseChainsNames
            })
        }
    );

    const data: any = await monitorablesInfo.json();
    var baseChains: BaseChain[] = [];

    for (const baseChain in data.result) {
        if (data.result[baseChain]) {
            var currentChains: Chain[] = [];
            var index: number = 0;
            for (const currentChain in data.result[baseChain]) {
                // Systems case.
                var currentSystems: string[] = [];
                for (const system of data.result[baseChain][currentChain].monitored.systems) {
                    currentSystems.push(Object.keys(system)[0]);
                }

                // Repos case.
                var currentRepos: string[] = [];
                for (const type of Object.keys(data.result[baseChain][currentChain].monitored)) {
                    if (type.includes('repo')) {
                        for (const repo of data.result[baseChain][currentChain].monitored[type]) {
                            currentRepos.push(Object.keys(repo)[0]);
                        }
                    }
                }

                currentChains.push({
                    name: currentChain,
                    id: data.result[baseChain][currentChain].parent_id,
                    repos: currentRepos,
                    systems: currentSystems,
                    criticalAlerts: 0,
                    warningAlerts: 0,
                    errorAlerts: 0,
                    totalAlerts: 0,
                    active: index == 0
                });

                index++;
            }

            baseChains.push({
                name: baseChain,
                chains: currentChains
            });
        }
    }

    return baseChains;
}

export async function UpdateAllAlertsOverview(initialCall: Boolean, baseChains: BaseChain[]): Promise<void> {
    var changed: Boolean = false;
    var result: {} = {};
    for (var baseChain of baseChains) {
        for (var chain of baseChain.chains) {
            if (chain.active) {
                result = await GetAlertsOverview(chain, initialCall);
                chain = result['chain'];

                if (!initialCall && !changed && result['changed']) {
                    changed = true;
                }
            }
        }
    }

    if (changed) {
        this.alertsChanged = !this.alertsChanged;
    }
}

export async function GetAlertsOverview(chain: Chain, initialCall: Boolean): Promise<{ chain: Chain, changed: Boolean }> {
    var changed: Boolean = false;
    var chainSources = { parentIds: {} };
    chainSources.parentIds[chain.id] = { systems: [], repos: [] };
    chainSources.parentIds[chain.id].systems = chain.systems;
    chainSources.parentIds[chain.id].repos = chain.repos;

    try {
        const alertsOverview = await fetch(apiURL + 'redis/alertsOverview',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chainSources)
            });

        const data: any = await alertsOverview.json();

        if (!initialCall && ((data.result[chain.id].critical != chain.criticalAlerts) ||
            (data.result[chain.id].warning != chain.warningAlerts) ||
            (data.result[chain.id].error != chain.errorAlerts))) {
            changed = true;
        }

        chain.criticalAlerts = data.result[chain.id].critical;
        chain.warningAlerts = data.result[chain.id].warning;
        chain.errorAlerts = data.result[chain.id].error;
        chain.totalAlerts = chain.criticalAlerts + chain.warningAlerts + chain.errorAlerts;

    } catch (error: any) {
        console.error(error);
    }

    return { chain: chain, changed: changed };
}
