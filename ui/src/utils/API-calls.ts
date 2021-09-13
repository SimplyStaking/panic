import { BaseChain, Chain } from "../interfaces/chains";
import { apiURL, baseChainsNames } from "./constants";

/**
 * Gets the base chains from the API and populates them with chain information.
 * @returns list of populated base chains.
 */
export async function getMonitorablesInfo(): Promise<BaseChain[]> {
    const monitorablesInfo: Response = await fetch(`${apiURL}redis/monitorablesInfo`,
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
    const baseChains: BaseChain[] = [];

    for (const baseChain in data.result) {
        if (data.result[baseChain]) {
            const currentChains: Chain[] = [];
            let index: number = 0;
            for (const currentChain in data.result[baseChain]) {
                // Systems case.
                const currentSystems: string[] = [];
                for (const system of data.result[baseChain][currentChain].monitored.systems) {
                    currentSystems.push(Object.keys(system)[0]);
                }

                // Repos case.
                const currentRepos: string[] = [];
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

/**
 * Updates the alerts of all of the chains within each base chain.
 * @param initialCall whether this is the first call.
 * @param baseChains base chains to be updated.
 * @returns whether any chain was changed.
 */
export async function updateAllBaseChains(initialCall: Boolean, baseChains: BaseChain[]): Promise<Boolean> {
    let changed: Boolean = false;
    let result: {} = {};
    for (let baseChain of baseChains) {
        for (let chain of baseChain.chains) {
            if (chain.active) {
                result = await updateChainAlerts(chain, initialCall);
                chain = result['chain'];

                if (!initialCall && !changed && result['changed']) {
                    changed = true;
                }
            }
        }
    }

    return changed;
}

/**
 * Updates the alerts of a given chain while noting whether it changed.
 * @param chain chain to be updated.
 * @param initialCall whether this is the first call.
 * @returns updated chain and whether it was changed.
 */
async function updateChainAlerts(chain: Chain, initialCall: Boolean): Promise<{ chain: Chain, changed: Boolean }> {
    let changed: Boolean = false;

    try {
        const data: any = await getAlertsOverview(chain);

        if (!initialCall && ((data.result[chain.id].critical !== chain.criticalAlerts) ||
            (data.result[chain.id].warning !== chain.warningAlerts) ||
            (data.result[chain.id].error !== chain.errorAlerts))) {
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

/**
 * Gets the alerts overview of a given chain.
 * @param chain chain to be checked.
 * @returns chain data as JSON.
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
        console.error(error);
    }
}
